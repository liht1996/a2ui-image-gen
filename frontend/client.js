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
     * Send a message to the agent
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
            
            const data = await response.json();
            this.updateConnectionStatus('connected');
            
            if (data.error) {
                throw new Error(data.error.message || 'Unknown error');
            }
            
            return data.result;
        } catch (error) {
            this.updateConnectionStatus('error');
            throw error;
        }
    }

    /**
     * Check connection to server
     */
    async checkConnection() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
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
     * Get agent capabilities
     */
    async getCapabilities() {
        const request = {
            jsonrpc: '2.0',
            method: 'agent/capabilities',
            params: {},
            id: 0
        };
        
        try {
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request)
            });
            
            const data = await response.json();
            return data.result;
        } catch (error) {
            console.error('Failed to get capabilities:', error);
            return null;
        }
    }
}

// Export for use in other scripts
window.A2UIClient = A2UIClient;
