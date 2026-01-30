Exactly. HTTP + WebSockets gives you everything Redis would, without the dependency.

**What you can pass between UI and agent:**

```
WebSocket /ws
├── User messages (streaming both directions)
├── Tool call events (real-time as they happen)
├── File change notifications
├── Scratchpad state (open files, current contents)
├── Token counts / context usage
└── Agent thinking/status updates

REST endpoints
├── GET /sessions - list all sessions
├── GET /session/{id} - full session with history tiers
├── POST /session/{id}/message - send message
├── GET /scratchpad - current open files
├── PUT /scratchpad/open - open a file
├── DELETE /scratchpad/{file} - close a file
├── GET /config - user preferences
├── PUT /config - update preferences
└── GET /project - current project metadata
```

**The WebSocket is the key** - it's a persistent bidirectional channel. The terminal CLI and web UI both connect to the same socket and see the same stream:

```
┌─────────────┐     WebSocket      ┌─────────────────────┐
│  Terminal   │◄──────────────────►│                     │
│    CLI      │                    │    Mobius Agent     │
└─────────────┘                    │    (FastAPI)        │
                                   │                     │
┌─────────────┐     WebSocket      │  ┌───────────────┐  │
│   Web UI    │◄──────────────────►│  │ Shared State  │  │
│  (Browser)  │                    │  │ - History     │  │
└─────────────┘                    │  │ - Scratchpad  │  │
                                   │  │ - Config      │  │
┌─────────────┐     WebSocket      │  └───────────────┘  │
│   Cursor    │◄──────────────────►│                     │
│  Extension  │                    │                     │
└─────────────┘                    └─────────────────────┘
```

All three see the same state in real-time. Type in terminal, see it appear in web UI. Open file from Cursor, it shows in terminal's scratchpad display.

**Simple example of the shared state:**

```python
class AgentState:
    # These are shared across all connected clients
    scratchpad: dict[str, str]  # {filepath: contents}
    history_t0: list[Message]   # Working memory
    history_t1: list[Summary]   # Medium-term
    history_t2: dict            # Session facts
    
    # Broadcast to all WebSocket clients on change
    async def notify_clients(self, event: str, data: dict):
        for client in self.connected_clients:
            await client.send_json({"event": event, "data": data})
```

Want me to sketch out the FastAPI structure for this?