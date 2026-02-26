import { LitElement, html, render } from 'lit';
import { ContextProvider } from '@lit/context';
import { Data } from '@a2ui/lit/0.8';
import * as UI from '@a2ui/lit/ui';

const DEFAULT_A2UI_THEME = {
    additionalStyles: {},
    components: {
        AudioPlayer: {},
        Button: {},
        Card: {},
        CheckBox: { container: {}, element: {}, label: {} },
        Column: {},
        DateTimeInput: { container: {}, element: {}, label: {} },
        Divider: {},
        Icon: {},
        Image: { all: {}, avatar: {}, header: {}, icon: {}, largeFeature: {}, mediumFeature: {}, smallFeature: {} },
        List: {},
        Modal: { backdrop: {}, element: {} },
        MultipleChoice: { container: {}, element: {}, label: {} },
        Row: {},
        Slider: { container: {}, element: {}, label: {} },
        Tabs: { container: {}, controls: { all: {}, selected: {} }, element: {} },
        Text: { all: {}, body: {}, caption: {}, h1: {}, h2: {}, h3: {}, h4: {}, h5: {} },
        TextField: { container: {}, element: {}, label: {} },
        Video: {},
    },
    elements: {},
    markdown: { a: [], em: [], h1: [], h2: [], h3: [], h4: [], h5: [], li: [], ol: [], p: [], strong: [], ul: [] },
};

class A2uiThemedSurface extends LitElement {
    static properties = {
        surface: { attribute: false },
        surfaceId: { type: String },
        processor: { attribute: false },
        enableCustomElements: { type: Boolean },
    };

    constructor() {
        super();
        this.surface = null;
        this.surfaceId = null;
        this.processor = null;
        this.enableCustomElements = false;
        this.theme = DEFAULT_A2UI_THEME;
        this.themeProvider = new ContextProvider(this, {
            context: UI.Context.themeContext,
            initialValue: this.theme,
        });
    }

    render() {
        return html`
            <a2ui-surface
                .surface=${this.surface}
                .surfaceId=${this.surfaceId}
                .processor=${this.processor}
                .enableCustomElements=${this.enableCustomElements}
            ></a2ui-surface>
        `;
    }
}

if (!customElements.get('a2ui-themed-surface')) {
    customElements.define('a2ui-themed-surface', A2uiThemedSurface);
}

// A2A Client Configuration
const BACKEND_URL = 'http://localhost:10002';

class A2uiImageGenApp {
    constructor() {
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.sessionId = this.generateSessionId();
        this.processor = Data.createSignalA2uiMessageProcessor();
        
        this.setupEventListeners();
    }

    generateSessionId() {
        return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        const widgetValues = this.getCurrentWidgetValues();
        const messageWithWidgetContext = this.buildMessageWithWidgetContext(message, widgetValues);

        // Add user message to chat
        this.addUserMessage(message);
        this.messageInput.value = '';
        this.setLoading(true);

        try {
            await this.streamAgentResponse(messageWithWidgetContext);
        } catch (error) {
            console.error('Error sending message:', error);
            this.addErrorMessage(`Error: ${error.message}`);
        } finally {
            this.setLoading(false);
        }
    }

    async streamAgentResponse(message) {
        const requestBody = {
            jsonrpc: '2.0',
            id: Date.now(),
            method: 'message/stream',
            params: {
                message: {
                    messageId: `msg-${Date.now()}`,
                    role: 'user',
                    parts: [{ text: message }]
                }
            }
        };

        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-A2A-Extensions': 'https://a2ui.org/a2a-extension/a2ui/v0.8'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let agentResponse = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const events = this.parseSSE(buffer);
            
            for (const event of events.complete) {
                console.log('SSE Event:', event);
                
                if (event.error) {
                    throw new Error(event.error.message || 'Unknown error');
                }
                
                if (event.result && event.result.status) {
                    console.log('Status:', event.result.status);
                    const message = event.result.status.message;
                    console.log('Message:', message);
                    if (message && (message.role === 'agent' || message.role === 'assistant')) {
                        console.log('Found agent message with', message.parts?.length || 0, 'parts');
                        agentResponse = message;
                    }
                }
            }
            
            buffer = events.remainder;
        }

        if (agentResponse) {
            console.log('Displaying agent response:', agentResponse);
            this.displayAgentMessage(agentResponse);
        } else {
            console.error('No agent message found in SSE stream');
            throw new Error('No response received from agent');
        }
    }

    parseSSE(buffer) {
        const complete = [];
        const lines = buffer.split('\n');
        let i = 0;

        while (i < lines.length - 1) {
            if (lines[i].startsWith('data: ')) {
                try {
                    const jsonStr = lines[i].substring(6);
                    const event = JSON.parse(jsonStr);
                    complete.push(event);
                    i++;
                    if (i < lines.length && lines[i] === '') {
                        i++;
                    }
                } catch (e) {
                    i++;
                }
            } else {
                i++;
            }
        }

        const remainder = lines[lines.length - 1];
        return { complete, remainder };
    }

    displayAgentMessage(message) {
        console.log('displayAgentMessage called with:', message);
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message agent';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // First pass: collect all A2UI messages
        const a2uiMessages = [];
        
        // Process message parts
        console.log('Processing', message.parts?.length || 0, 'parts');
        for (const part of message.parts || []) {
            console.log('Processing part:', part);
            if (part.kind === 'text' && part.text) {
                const textP = document.createElement('p');
                textP.textContent = part.text;
                contentDiv.appendChild(textP);
            } else if (part.kind === 'data' && part.data) {
                // Handle inline images immediately
                if (part.data.inlineData) {
                    console.log('Found inline image');
                    const imageContainer = document.createElement('div');
                    imageContainer.className = 'image-container';
                    const img = document.createElement('img');
                    img.src = `data:${part.data.inlineData.mimeType};base64,${part.data.inlineData.data}`;
                    imageContainer.appendChild(img);
                    contentDiv.appendChild(imageContainer);
                }
                // Collect A2UI messages for batch processing
                else if (part.data.beginRendering || part.data.surfaceUpdate || part.data.dataModelUpdate) {
                    console.log('Found A2UI message:', Object.keys(part.data));
                    a2uiMessages.push(part.data);
                }
            }
        }

        // Second pass: process all A2UI messages at once and render
        if (a2uiMessages.length > 0) {
            console.log('Processing', a2uiMessages.length, 'A2UI messages');
            console.log('A2UI messages:', a2uiMessages);

            // Clear old surfaces so each turn renders only current UI state.
            this.processor.clearSurfaces();
            this.processor.processMessages(a2uiMessages);

            const surfaces = this.processor.getSurfaces();
            console.log('Processor surfaces:', surfaces);

            // Native SignalMap handling: iterate directly, do not unwrap internals.
            for (const [surfaceId, surface] of surfaces.entries()) {
                console.log('Found surface with ID:', surfaceId);
                this.renderA2uiSurface(surfaceId, surface, contentDiv);
            }
        }

        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    renderA2uiSurface(surfaceId, surface, container) {
        // Check if a surface container already exists for this surfaceId
        let surfaceContainer = container.querySelector(`[data-surface-id="${surfaceId}"]`);
        
        if (!surfaceContainer) {
            surfaceContainer = document.createElement('div');
            surfaceContainer.className = 'a2ui-surface-container';
            surfaceContainer.setAttribute('data-surface-id', surfaceId);
            container.appendChild(surfaceContainer);
        }
        
        console.log('Rendering A2UI surface:');
        console.log('  surfaceId:', surfaceId);
        console.log('  surface:', surface);
        console.log('  processor:', this.processor);
        
        // Pass the surface directly - it's a reactive Proxy that components access through
        const template = html`
            <a2ui-themed-surface 
                .surface=${surface}
                .surfaceId=${surfaceId}
                .processor=${this.processor}
                .enableCustomElements=${false}>
            </a2ui-themed-surface>
        `;
        
        render(template, surfaceContainer);
    }

    addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = message;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = message;
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }

    setLoading(loading) {
        this.sendButton.disabled = loading;
        this.messageInput.disabled = loading;
        
        if (loading) {
            this.sendButton.innerHTML = 'Sending<span class="loading"></span>';
        } else {
            this.sendButton.textContent = 'Send';
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    getCurrentWidgetValues() {
        const values = {};
        const surfaces = this.processor.getSurfaces();

        for (const [, surface] of surfaces.entries()) {
            const dataModel = surface?.dataModel;
            if (!dataModel || typeof dataModel.entries !== 'function') {
                continue;
            }

            for (const [key, value] of dataModel.entries()) {
                if (key === 'generated_image') {
                    continue;
                }
                if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
                    values[key] = value;
                }
            }
        }

        return values;
    }

    buildMessageWithWidgetContext(message, widgetValues) {
        const entries = Object.entries(widgetValues);
        if (entries.length === 0) {
            return message;
        }

        const widgetText = entries
            .map(([key, value]) => `${key} is ${String(value)}`)
            .join(', ');

        const sizeValue = widgetValues.size;
        const sizeHint = typeof sizeValue === 'number'
            ? ` Keep image size as ${sizeValue}.`
            : '';

        return `${message}\n\nUse these current widget settings: ${widgetText}.${sizeHint}`;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new A2uiImageGenApp();
});
