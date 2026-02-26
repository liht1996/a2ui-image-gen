/**
 * A2UI Client
 * Handles communication with the backend server
 */

class A2UIClient {
    constructor(baseUrl = 'http://localhost:10002') {
        this.baseUrl = baseUrl;
        this.messageCounter = 0;
        this.connectionStatus = 'disconnected';
    }

    /**
     * Send a message to the agent (handles SSE streaming)
     */
    async sendMessage(text, widgetData = null) {
        this.messageCounter++;
        
        // Build message parts
        const parts = [{ text }];
        
        // Add widget data if provided
        if (widgetData) {
            // Support old format (backward compatibility)
            if (widgetData.color_tone) {
                parts.push({
                    a2ui: {
                        type: 'color-tone-control',
                        id: 'color-tone-widget',
                        properties: widgetData.color_tone
                    }
                });
            }
            if (widgetData.sketch) {
                parts.push({
                    a2ui: {
                        type: 'sketch-board',
                        id: 'sketch-board-widget',
                        properties: { sketch: widgetData.sketch }
                    }
                });
            }
            
            // Support new dynamic widget format (A2UI protocol compliant)
            if (widgetData.widget_parts) {
                for (const widgetPart of widgetData.widget_parts) {
                    parts.push({
                        a2ui: widgetPart
                    });
                }
            }
        }
        
        // Build A2A request
        const request = {
            jsonrpc: '2.0',
            method: 'message/stream',
            params: {
                message: {
                    messageId: `msg-${this.messageCounter}`,
                    role: 'user',
                    parts: parts
                }
            },
            id: this.messageCounter
        };
        
        try {
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-A2A-Extensions': 'https://a2ui.org/a2a-extension/a2ui/v0.8'
                },
                body: JSON.stringify(request)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Handle SSE (Server-Sent Events) response
            const responseText = await response.text();
            console.log('Raw SSE response (first 500 chars):', responseText.substring(0, 500));
            
            // Parse SSE format: data: {json}\n\ndata: {json}\n\n
            const events = this.parseSSE(responseText);
            console.log('Parsed', events.length, 'events from SSE');
            
            this.updateConnectionStatus('connected');
            
            // Process events and return the final message
            let finalMessage = null;
            let latestStatusUpdate = null;
            
            console.log('Processing', events.length, 'SSE events');
            
            for (const event of events) {
                console.log('Event:', event);
                
                if (event.error) {
                    throw new Error(event.error.message || 'Unknown error');
                }
                
                if (event.result) {
                    console.log('Event result kind:', event.result.kind);
                    
                    // Check if this is a direct message event
                    if (event.result.kind === 'message') {
                        console.log('Found direct message event');
                        finalMessage = event.result;
                    } 
                    // Check for status-update events (most common in A2A SDK)
                    else if (event.result.kind === 'status-update') {
                        const state = event.result.status?.state;
                        console.log('Found status-update event, state:', state);
                        latestStatusUpdate = event.result;
                        
                        // Message is nested inside status.message
                        if (event.result.status && event.result.status.message) {
                            console.log('Found message in status-update');
                            // Update finalMessage with this message if it's an agent message
                            if (event.result.status.message.role === 'agent' || 
                                event.result.status.message.role === 'assistant') {
                                finalMessage = event.result.status.message;
                            }
                        }
                    }
                    // Check for task events with history
                    else if (event.result.kind === 'task') {
                        console.log('Found task event, status:', event.result.status?.state);
                        // Look for message in history
                        const history = event.result.history || [];
                        console.log('Task history length:', history.length);
                        
                        // Get the last assistant message from history
                        for (let i = history.length - 1; i >= 0; i--) {
                            if (history[i].role === 'assistant' || history[i].role === 'agent') {
                                console.log('Found assistant/agent message in history at index', i);
                                if (!finalMessage) {  // Only use if we don't have a message yet
                                    finalMessage = history[i];
                                }
                                break;
                            }
                        }
                    }
                }
            }
            
            if (!finalMessage) {
                console.error('No message found in events. Event details:');
                console.error('Latest status update:', latestStatusUpdate);
                events.forEach((evt, idx) => {
                    console.error(`Event ${idx}:`, JSON.stringify(evt, null, 2));
                });
                throw new Error('No message received from agent');
            }
            
            console.log('Returning final message with', finalMessage.parts?.length || 0, 'parts');
            return finalMessage;
        } catch (error) {
            this.updateConnectionStatus('error');
            throw error;
        }
    }
    
    /**
     * Parse Server-Sent Events (SSE) format
     */
    parseSSE(text) {
        const events = [];
        const lines = text.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const json = JSON.parse(line.substring(6));
                    events.push(json);
                } catch (e) {
                    console.warn('Failed to parse SSE event:', line, e);
                }
            }
        }
        
        return events;
    }

    /**
     * Check connection to server
     */
    async checkConnection() {
        try {
            // Test the agent card endpoint
            const response = await fetch(`${this.baseUrl}/.well-known/agent-card.json`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            
            if (response.ok) {
                this.updateConnectionStatus('connected');
                return true;
            }
        } catch (error) {
            console.warn('Connection check failed:', error);
        }
        
        this.updateConnectionStatus('disconnected');
        return false;
    }

    /**
     * Update connection status UI
     */
    updateConnectionStatus(status) {
        this.connectionStatus = status;
        const statusElement = document.getElementById('connection-status');
        const statusDot = statusElement.querySelector('.status-dot');
        const statusText = statusElement.querySelector('.status-text');
        
        statusDot.className = 'status-dot';
        
        switch (status) {
            case 'connected':
                statusDot.classList.add('connected');
                statusText.textContent = 'Connected';
                break;
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                break;
            case 'error':
                statusDot.classList.add('error');
                statusText.textContent = 'Connection Error';
                break;
            default:
                statusText.textContent = 'Connecting...';
        }
    }

    /**
     * Get agent card (capabilities) from the well-known endpoint
     */
    async getCapabilities() {
        try {
            const response = await fetch(`${this.baseUrl}/.well-known/agent-card.json`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const agentCard = await response.json();
            // Return in the same format as before for backward compatibility
            return {
                capabilities: agentCard.capabilities,
                ...agentCard
            };
        } catch (error) {
            console.error('Failed to get agent card:', error);
            return null;
        }
    }
}

// Export for use in other scripts
window.A2UIClient = A2UIClient;
