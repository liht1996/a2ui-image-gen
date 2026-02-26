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
        
        console.log('=== APPLY WIDGETS ===');
        console.log('Widget data:', this.currentWidgetData);
        
        // Send a refinement message
        const text = 'Apply these adjustments';
        this.addMessage('user', text);
        this.showLoading(true);

        try {
            const response = await this.client.sendMessage(text, this.currentWidgetData);
            console.log('Apply widgets response:', response);
            this.processResponse(response);
        } catch (error) {
            console.error('Error applying widgets:', error);
            console.error('Error stack:', error.stack);
            this.addMessage('system', `❌ Error applying widgets: ${error.message}`, true);
        } finally {
            this.showLoading(false);
        }
    }

    processResponse(response) {
        const parts = response.parts || [];
        console.log('=== PROCESSING RESPONSE ===');
        console.log('Response object:', response);
        console.log('Number of parts:', parts.length);
        console.log('Full parts:', JSON.stringify(parts, null, 2));

        // Extract text and image
        let responseText = '';
        let imageData = null;

        parts.forEach((part, index) => {
            console.log(`\n--- Part ${index} ---`);
            console.log('Full part structure:', JSON.stringify(part, null, 2));
            
            // Handle A2A SDK format (with 'kind' field)
            if (part.kind === 'text' && part.text) {
                responseText += part.text;
                console.log('  ✓ Found text (kind=text):', part.text.substring(0, 50));
            } else if (part.kind === 'data' && part.data) {
                console.log('  - Found data part with keys:', Object.keys(part.data));
                
                // Check for inlineData in data
                if (part.data.inlineData) {
                    console.log('  ✓ Found inlineData in data part!');
                    console.log('    - mimeType:', part.data.inlineData.mimeType);
                    console.log('    - data length:', part.data.inlineData.data ? part.data.inlineData.data.length : 'null');
                    imageData = part.data.inlineData.data;
                }
                
                // This is A2UI surface data (beginRendering, surfaceUpdate, dataModelUpdate)
                if (part.data.beginRendering) {
                    console.log('  - A2UI beginRendering:', part.data.beginRendering);
                }
                if (part.data.surfaceUpdate) {
                    console.log('  - A2UI surfaceUpdate with', part.data.surfaceUpdate.components?.length || 0, 'components');
                }
                if (part.data.dataModelUpdate) {
                    console.log('  - A2UI dataModelUpdate');
                    const contents = part.data.dataModelUpdate.contents || [];
                    for (const content of contents) {
                        console.log('    - key:', content.key, 'value type:', Object.keys(content).filter(k => k.startsWith('value')));
                        if (content.key === 'generated_image' && content.valueString) {
                            console.log('  ✓ Found image in dataModelUpdate');
                            // Extract base64 from data URL
                            const match = content.valueString.match(/^data:image\/[^;]+;base64,(.+)$/);
                            if (match) {
                                imageData = match[1];
                                console.log('  ✓ Extracted base64 from dataModelUpdate');
                            }
                        }
                    }
                }
            } else if (part.kind === 'inlineData' && part.inlineData) {
                // InlineData in SDK format: {kind: 'inlineData', inlineData: {mimeType, data}}
                imageData = part.inlineData.data;
                console.log('  ✓ Found image (kind=inlineData):', imageData ? imageData.substring(0, 50) : 'null');
            } else if (part.kind === 'a2ui' && part.a2ui) {
                console.log('  ✓ Found widget (kind=a2ui):', part.a2ui.type);
            }
            // Handle legacy format (without 'kind' field) - for backward compatibility
            else if (part.text) {
                responseText += part.text;
                console.log('  ✓ Found text (legacy):', part.text.substring(0, 50));
            } else if (part.inlineData) {
                imageData = part.inlineData.data;
                console.log('  ✓ Found image (legacy):', imageData ? imageData.substring(0, 50) : 'null');
            } else if (part.a2ui) {
                console.log('  ✓ Found widget (legacy):', part.a2ui.type);
            } else {
                console.log('  ⚠ Unknown part structure');
            }
        });

        console.log('\n=== EXTRACTION RESULTS ===');
        console.log('Response text length:', responseText.length);
        console.log('Image data found:', imageData ? 'YES (' + imageData.length + ' chars)' : 'NO');

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
        console.log('\n=== WIDGET RENDERING ===');
        const hasWidgets = this.widgetRenderer.renderWidgets(parts);
        console.log('Widgets found:', hasWidgets);
        if (hasWidgets) {
            this.widgetRenderer.togglePanel(true);
        } else {
            this.widgetRenderer.togglePanel(false);
        }
        console.log('=== END RESPONSE PROCESSING ===\n');
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
