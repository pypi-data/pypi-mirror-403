"""FastAPI + WebSocket server for the Animate class."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

if TYPE_CHECKING:
    from animaid.animate import Animate


def create_animate_app(animate: Animate) -> FastAPI:
    """Create a FastAPI application for the Animate instance.

    Args:
        animate: The Animate instance to serve.

    Returns:
        A configured FastAPI application.
    """
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        """Serve the main HTML page."""
        return get_html_page(animate.title)

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """Handle WebSocket connections."""
        await websocket.accept()
        animate.register_connection(websocket)

        try:
            # Send full state on connection
            full_state = animate.get_full_state()
            await websocket.send_text(
                json.dumps({"type": "full_state", "items": full_state})
            )

            # Listen for messages
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "close":
                    # Client requested server shutdown
                    animate.stop()
                    break
                elif message.get("type") == "input":
                    # Handle input event from browser
                    animate.handle_input_event(message)

        except WebSocketDisconnect:
            pass
        finally:
            animate.unregister_connection(websocket)

    return app


def get_html_page(title: str) -> str:
    """Generate the HTML page for the Animate display.

    Args:
        title: The page title.

    Returns:
        Complete HTML page as a string.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                         Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #fafafa;
            min-height: 100vh;
        }}

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }}

        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            color: #333;
        }}

        .close-btn {{
            background: #f44336;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background-color 0.2s;
        }}

        .close-btn:hover {{
            background: #d32f2f;
        }}

        .close-btn:active {{
            background: #b71c1c;
        }}

        .container {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .item {{
            background: white;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            transition: opacity 0.3s, transform 0.3s;
        }}

        .item.adding {{
            animation: fadeIn 0.3s ease-out;
        }}

        .item.removing {{
            animation: fadeOut 0.3s ease-out;
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes fadeOut {{
            from {{
                opacity: 1;
                transform: translateY(0);
            }}
            to {{
                opacity: 0;
                transform: translateY(-10px);
            }}
        }}

        .status {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }}

        .status.connected {{
            background: #e8f5e9;
            color: #2e7d32;
        }}

        .status.disconnected {{
            background: #ffebee;
            color: #c62828;
        }}

        .empty-message {{
            text-align: center;
            color: #757575;
            padding: 40px;
            font-style: italic;
        }}

        /* Input widget styles */
        .anim-button {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            background: #e0e0e0;
            color: #333;
        }}

        .anim-button:hover {{
            filter: brightness(0.95);
        }}

        .anim-button:active {{
            transform: scale(0.98);
        }}

        .anim-button.primary {{
            background: #2196F3;
            color: white;
        }}

        .anim-button.success {{
            background: #4CAF50;
            color: white;
        }}

        .anim-button.danger {{
            background: #f44336;
            color: white;
        }}

        .anim-button.warning {{
            background: #ff9800;
            color: white;
        }}

        .anim-text-input {{
            padding: 10px 14px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.2s;
            width: 100%;
            max-width: 300px;
        }}

        .anim-text-input:focus {{
            outline: none;
            border-color: #2196F3;
        }}

        .anim-checkbox-container {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        }}

        .anim-checkbox {{
            width: 18px;
            height: 18px;
            cursor: pointer;
        }}

        .anim-slider {{
            width: 100%;
            max-width: 300px;
            height: 6px;
            border-radius: 3px;
            cursor: pointer;
        }}

        .anim-select {{
            padding: 10px 14px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            background: white;
            cursor: pointer;
            min-width: 150px;
        }}

        .anim-select:focus {{
            outline: none;
            border-color: #2196F3;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <button class="close-btn" onclick="closeServer()">Close</button>
    </div>
    <div id="container" class="container">
        <div id="empty-message" class="empty-message">
            Waiting for content...
        </div>
    </div>
    <div id="status" class="status disconnected">Disconnected</div>

    <script>
        const container = document.getElementById('container');
        const emptyMessage = document.getElementById('empty-message');
        const statusEl = document.getElementById('status');
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        function connect() {{
            ws = new WebSocket(`ws://${{location.host}}/ws`);

            ws.onopen = function() {{
                statusEl.textContent = 'Connected';
                statusEl.className = 'status connected';
                reconnectAttempts = 0;
            }};

            ws.onclose = function() {{
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'status disconnected';

                // Try to reconnect
                if (reconnectAttempts < maxReconnectAttempts) {{
                    reconnectAttempts++;
                    setTimeout(connect, 1000 * reconnectAttempts);
                }}
            }};

            ws.onerror = function(error) {{
                console.error('WebSocket error:', error);
            }};

            ws.onmessage = function(event) {{
                const message = JSON.parse(event.data);
                handleMessage(message);
            }};
        }}

        function handleMessage(message) {{
            switch (message.type) {{
                case 'full_state':
                    renderFullState(message.items);
                    break;
                case 'add':
                    addItem(message.id, message.html);
                    break;
                case 'update':
                    updateItem(message.id, message.html);
                    break;
                case 'remove':
                    removeItem(message.id);
                    break;
                case 'clear':
                    clearItems();
                    break;
            }}
        }}

        function updateEmptyState() {{
            const items = container.querySelectorAll('.item');
            if (items.length === 0) {{
                emptyMessage.style.display = 'block';
            }} else {{
                emptyMessage.style.display = 'none';
            }}
        }}

        function renderFullState(items) {{
            // Remove all existing items
            container.querySelectorAll('.item').forEach(el => el.remove());

            // Add all items
            items.forEach(item => {{
                addItem(item.id, item.html, false);
            }});

            updateEmptyState();
        }}

        function addItem(id, html, animate = true) {{
            const div = document.createElement('div');
            div.id = `item-${{id}}`;
            div.className = 'item' + (animate ? ' adding' : '');
            div.innerHTML = html;
            container.appendChild(div);

            if (animate) {{
                div.addEventListener('animationend', () => {{
                    div.classList.remove('adding');
                }}, {{ once: true }});
            }}

            updateEmptyState();
        }}

        function updateItem(id, html) {{
            const div = document.getElementById(`item-${{id}}`);
            if (div) {{
                div.innerHTML = html;
            }}
        }}

        function removeItem(id) {{
            const div = document.getElementById(`item-${{id}}`);
            if (div) {{
                div.classList.add('removing');
                div.addEventListener('animationend', () => {{
                    div.remove();
                    updateEmptyState();
                }}, {{ once: true }});
            }}
        }}

        function clearItems() {{
            container.querySelectorAll('.item').forEach(el => {{
                el.classList.add('removing');
                el.addEventListener('animationend', () => {{
                    el.remove();
                    updateEmptyState();
                }}, {{ once: true }});
            }});
        }}

        function closeServer() {{
            if (ws && ws.readyState === WebSocket.OPEN) {{
                ws.send(JSON.stringify({{ type: 'close' }}));
            }}
            // Close the tab after a short delay
            setTimeout(() => {{
                window.close();
            }}, 500);
        }}

        // Input event handlers
        function sendInputEvent(id, eventType, value) {{
            if (ws && ws.readyState === WebSocket.OPEN) {{
                const message = {{
                    type: 'input',
                    id: id,
                    event: eventType
                }};
                if (value !== undefined) {{
                    message.value = value;
                }}
                ws.send(JSON.stringify(message));
            }}
        }}

        // Global event delegation for input widgets
        document.addEventListener('click', function(e) {{
            const button = e.target.closest('.anim-button');
            if (button && button.dataset.animId) {{
                sendInputEvent(button.dataset.animId, 'click');
            }}
        }});

        document.addEventListener('input', function(e) {{
            const t = e.target;
            const id = t.dataset.animId;
            if (t.classList.contains('anim-text-input') && id) {{
                sendInputEvent(id, 'change', t.value);
            }}
            if (t.classList.contains('anim-slider') && id) {{
                sendInputEvent(id, 'change', parseFloat(t.value));
            }}
        }});

        document.addEventListener('change', function(e) {{
            const target = e.target;
            if (target.classList.contains('anim-checkbox') && target.dataset.animId) {{
                sendInputEvent(target.dataset.animId, 'change', target.checked);
            }}
            if (target.classList.contains('anim-select') && target.dataset.animId) {{
                sendInputEvent(target.dataset.animId, 'change', target.value);
            }}
        }});

        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter') {{
                const t = e.target;
                const id = t.dataset.animId;
                if (t.classList.contains('anim-text-input') && id) {{
                    sendInputEvent(id, 'submit', t.value);
                }}
            }}
        }});

        // Start connection
        connect();
    </script>
</body>
</html>"""
