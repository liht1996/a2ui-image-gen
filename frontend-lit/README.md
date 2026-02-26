# A2UI Image Generation Frontend (Lit Renderer)

This is the official Lit-based frontend for the A2UI Image Generation project using the `@a2ui/lit` renderer from Google.

## Setup

The frontend is already set up and running! Here's what was done:

1. **Installed official packages:**
   - `@a2ui/lit@0.8.1` - Official A2UI Lit renderer
   - `lit@3.3.2` - Lit framework for web components
   - `vite@5.4.21` - Modern build tool

2. **Created files:**
   - `index.html` - Main HTML page with styling
   - `main.js` - Application logic using A2uiMessageProcessor
   - `package.json` - NPM configuration

## Running

The frontend is currently running on:
- **Local**: http://localhost:5173/
- **Backend**: http://localhost:10002 (must be running)

### Start Development Server

```bash
cd frontend-lit
npm run dev
```

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## How It Works

### Architecture

1. **A2uiMessageProcessor**: Processes A2UI protocol messages (beginRendering, surfaceUpdate, dataModelUpdate)
2. **`<a2ui-surface>` Component**: Official Lit web component that renders A2UI surfaces
3. **A2A Protocol**: Server-Sent Events (SSE) for streaming responses from backend

### Key Components

- **A2uiMessageProcessor** - Central processor that handles all A2UI protocol messages
- **Official Lit Components** - All A2UI components (slider, textfield, image, etc.) from `@a2ui/lit/ui`
- **SSE Streaming** - Real-time communication with backend

### Message Flow

1. User sends message via input box
2. Frontend makes POST to `/message/stream` with JSON-RPC request
3. Backend streams response via SSE (Server-Sent Events)
4. Frontend parses SSE stream, extracts agent messages
5. A2uiMessageProcessor processes A2UI messages (beginRendering, surfaceUpdate, dataModelUpdate)
6. `<a2ui-surface>` component automatically renders the UI based on processor state
7. User interactions with widgets (sliders, inputs) update the data model
8. Changes trigger new backend requests automatically

## API Integration

The frontend communicates with the backend using the A2A protocol:

```javascript
POST http://localhost:10002/message/stream
{
  "jsonrpc": "2.0",
  "id": 123456789,
  "method": "message/stream",
  "params": {
    "sessionId": "session-...",
    "message": {
      "role": "user",
      "content": [{
        "kind": "text",
        "text": "Create a cat in a hat"
      }]
    }
  }
}
```

Response comes as SSE stream:
```
data: {"jsonrpc":"2.0","method":"status-update","params":{"status":"streaming"}}\n\n
data: {"jsonrpc":"2.0","method":"status-update","result":{"status":{"message":{...}}}}\n\n
```

## Differences from Custom Frontend

**Old Frontend (frontend/)**:
- ❌ Custom hand-built A2UI Surface parser (~1000 lines)
- ❌ Manual widget rendering
- ❌ Manual data model management
- ❌ "Apply Changes" button issues

**New Frontend (frontend-lit/)**:
- ✅ Official `@a2ui/lit` renderer
- ✅ Automatic widget rendering via web components
- ✅ Built-in data model handling by A2uiMessageProcessor
- ✅ Automatic updates and event handling
- ✅ Better maintainability and future-proofing

## Troubleshooting

### No widgets appearing
Check browser console for errors. Make sure backend is sending proper A2UI Surface format with `beginRendering`, `surfaceUpdate`, and `dataModelUpdate` messages.

### Image not showing
Check that backend is sending `DataPart` with `inlineData` containing base64 encoded image.

### Backend connection errors
Make sure backend is running on port 10002:
```bash
cd /Users/haotian.li/Repositories/a2ui-image-gen
./run_new.sh
```

## Dependencies

- **@a2ui/lit**: Official A2UI Lit renderer with web components
- **lit**: Framework for building web components
- **vite**: Fast build tool and dev server

## Development

The frontend uses modern ES modules and Vite for hot module replacement (HMR). Changes to `main.js` or `index.html` will reflect immediately in the browser.

## Learn More

- [A2UI Documentation](https://a2ui.org/)
- [A2UI GitHub Repository](https://github.com/google/A2UI)
- [Lit Documentation](https://lit.dev/)
- [Google ADK](https://github.com/google/adk-python)
