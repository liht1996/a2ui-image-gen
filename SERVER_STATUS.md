# Server Status & Usage

## ✅ CURRENTLY RUNNING

Your system is now using the **ORIGINAL working server** (`server.py`):

```bash
Backend:  http://localhost:10002  (server.py - WORKING)
Frontend: http://localhost:8080   (frontend/)
```

**→ Open http://localhost:8080 in your browser and try generating images!**

---

## Two Server Implementations Available

### 1. **server.py** - Original Working Implementation ✅ 
**USE THIS ONE** - Works with your current frontend

```bash
# Start backend
./run.sh
# OR
python server.py --host localhost --port 10002

# Start frontend (in another terminal)
cd frontend && python -m http.server 8080
```

**Features:**
- ✅ Custom JSON-RPC 2.0 implementation
- ✅ Works perfectly with existing frontend
- ✅ Dynamic AI-generated widgets
- ✅ Full A2UI v0.8 protocol compliance
- ✅ Gemini 2.5 Flash Image generation

---

### 2. **server_new.py** - Official A2UI SDK Implementation 🔧
**Requires frontend changes to work**

```bash
# Start backend
./run_new.sh
# OR  
python server_new.py --host localhost --port 10002
```

**Features:**
- ✅ Uses official `a2a-sdk` package
- ✅ Uses official `google-adk` package  
- ✅ Uses official `a2ui` schema manager
- ⚠️ **Requires frontend changes** - uses different JSON-RPC method names
- 📚 Follows Google's official A2UI pattern

**Why it doesn't work with current frontend:**
- The frontend sends `message/stream` and `agent/capabilities` methods
- The A2A SDK server expects different method names
- Would need frontend updates to match the official A2A protocol

---

## Quick Commands

### Check what's running:
```bash
lsof -i :10002  # Backend
lsof -i :8080   # Frontend
```

### Stop servers:
```bash
lsof -ti:10002 | xargs kill -9  # Stop backend
lsof -ti:8080 | xargs kill -9   # Stop frontend
```

### Restart original server:
```bash
cd /Users/haotian.li/Repositories/a2ui-image-gen
./run.sh
```

---

## Recommendation

**Use `server.py` (original)** - It's working perfectly and the new SDK version would require significant frontend changes with no immediate benefit for your use case.

The SDK implementation in `server_new.py` is kept for reference and future A2A protocol compatibility if needed.
