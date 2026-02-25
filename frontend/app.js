/**
 * Main Application
 * Coordinates the chat interface, widgets, and client communication
 */

class App {
    constructor() {
        this.client = new A2UIClient('http://localhost:10002');
        this.widgetRenderer = new WidgetRenderer();
        this.currentWidgetData = null;
        this.initialize();
    }

    async initialize() {
        this.setupEventListeners();
        await this.client.checkConnection();
        
        // Periodically check connection
        setInterval(() => this.client.checkConnection(), 10000);
    }

    setupEventListeners() {
        // Send button
        const sendBtn = document.getElementById('send-btn');
        sendBtn.addEventListener('click', () => this.handleSendMessage());

        // Enter key to send
        const userInput = document.getElementById('user-input');
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });

        // Close widgets panel
        const closeWidgetsBtn = document.getElementById('close-widgets');
        closeWidgetsBtn.addEventListener('click', () => {
            this.widgetRenderer.togglePanel(false);
        });

        // Apply widgets changes
        const applyBtn = document.getElementById('apply-widgets');
        applyBtn.addEventListener('click', () => this.handleApplyWidgets());
    }

    async handleSendMessage() {
        const userInput = document.getElementById('user-input');
        const text = userInput.value.trim();

        if (!text) return;

        // Clear input
        userInput.value = '';

        // Add user message to chat
        this.addMessage('user', text);

        // Show loading
        this.showLoading(true);

        try {
            // Send to backend
            const response = await this.client.sendMessage(text, this.currentWidgetData);
            
            // Reset widget data after sending
            this.currentWidgetData = null;

            // Process response
            this.processResponse(response);
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('system', `❌ Error: ${error.message}`, true);
        } finally {
            this.showLoading(false);
        }
    }

    async handleApplyWidgets() {
        // Get current widget values
        this.currentWidgetData = this.widgetRenderer.getWidgetData();
        
        // Send a refinement message
        const text = 'Apply these adjustments';
        this.addMessage('user', text);
        this.showLoading(true);

        try {
            const response = await this.client.sendMessage(text, this.currentWidgetData);
            this.processResponse(response);
        } catch (error) {
            console.error('Error applying widgets:', error);
            this.addMessage('system', `❌ Error: ${error.message}`, true);
        } finally {
            this.showLoading(false);
        }
    }

    processResponse(response) {
        const parts = response.parts || [];
        console.log('Processing response with', parts.length, 'parts:', parts);

        // Extract text and image
        let responseText = '';
        let imageData = null;

        parts.forEach((part, index) => {
            console.log(`Part ${index}:`, Object.keys(part));
            if (part.text) {
                responseText += part.text;
                console.log('  - Found text:', part.text.substring(0, 50));
            }
            if (part.inlineData) {
                imageData = part.inlineData.data;
                console.log('  - Found image:', imageData.substring(0, 50), '...');
            }
            if (part.a2ui) {
                console.log('  - Found widget:', part.a2ui.type);
            }
        });

        // Add assistant message
        if (responseText) {
            this.addMessage('assistant', responseText);
        }

        // Add image if present
        if (imageData) {
            console.log('Adding image to chat');
            this.addImage(imageData);
        } else {
            console.warn('No image data found in response');
        }

        // Render widgets if present
        const hasWidgets = this.widgetRenderer.renderWidgets(parts);
        if (hasWidgets) {
            this.widgetRenderer.togglePanel(true);
        } else {
            this.widgetRenderer.togglePanel(false);
        }
    }

    addMessage(role, text, isError = false) {
        const chatMessages = document.getElementById('chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        if (role === 'system') {
            messageDiv.innerHTML = `<div class="system-message ${isError ? 'error' : ''}">${text}</div>`;
        } else {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = text;
            messageDiv.appendChild(contentDiv);
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    addImage(base64Data) {
        const chatMessages = document.getElementById('chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        
        const img = document.createElement('img');
        img.className = 'message-image';
        img.src = `data:image/png;base64,${base64Data}`;
        img.alt = 'Generated image';
        
        // Click to view full size
        img.addEventListener('click', () => {
            window.open(img.src, '_blank');
        });
        
        messageDiv.appendChild(img);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        const sendBtn = document.getElementById('send-btn');
        const userInput = document.getElementById('user-input');

        if (show) {
            overlay.classList.remove('hidden');
            sendBtn.disabled = true;
            userInput.disabled = true;
        } else {
            overlay.classList.add('hidden');
            sendBtn.disabled = false;
            userInput.disabled = false;
            userInput.focus();
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
