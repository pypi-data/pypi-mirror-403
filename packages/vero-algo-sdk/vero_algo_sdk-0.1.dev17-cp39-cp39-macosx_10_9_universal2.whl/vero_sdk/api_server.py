import threading
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, cast

logger = logging.getLogger("vero_sdk.api_server")

class APIHandler(BaseHTTPRequestHandler):
    """
    Handles API requests for the Vero SDK Control Server.
    Has access to the Vero instance via server.app_instance.
    """

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def _send_error(self, message: str, status: int = 400):
        """Send error response."""
        self._send_json({"error": message}, status)

    def _send_html(self, content: str, status: int = 200):
        """Send HTML response."""
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _get_openapi_schema(self) -> Dict[str, Any]:
        """Generate openapi.json schema."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Vero Algo SDK Control API",
                "version": "1.0.0",
                "description": "Control and monitor your running trading strategy."
            },
            "servers": [{"url": "/"}],
            "paths": {
                "/status": {
                    "get": {
                        "summary": "Get Strategy Status",
                        "responses": {
                            "200": {
                                "description": "Current status",
                                "content": {"application/json": {"example": {"status": "RUNNING"}}}
                            }
                        }
                    }
                },
                "/progress": {
                    "get": {
                        "summary": "Get Backtest Progress",
                        "responses": {
                            "200": {
                                "description": "Current progress percentage",
                                "content": {"application/json": {"example": {"progress": 45.5}}}
                            }
                        }
                    }
                },
                "/report": {
                    "get": {
                        "summary": "Get Performance Report",
                        "responses": {
                            "200": {
                                "description": "Full backtest result",
                                "content": {"application/json": {"example": {"metrics": {}, "equity_curve": []}}}
                            }
                        }
                    }
                },
                "/stop": {
                    "post": {
                        "summary": "Stop Strategy",
                        "responses": {
                            "200": {
                                "description": "Stop signal sent",
                                "content": {"application/json": {"example": {"message": "Stop signal sent"}}}
                            }
                        }
                    }
                }
            }
        }

    def do_GET(self):
        """Handle GET requests."""
        server = cast(Any, self.server)
        if self.path == "/status":
            status = server.app_instance.get_status()
            self._send_json({"status": status})
        
        elif self.path == "/progress":
            progress = server.app_instance.get_progress()
            self._send_json({"progress": progress})
            
        elif self.path == "/report":
            report = server.app_instance.get_algo_stat_report()
            if report:
                self._send_json(report)
            else:
                self._send_json({}, 200) # Empty valid JSON if no report yet
        
        elif self.path == "/openapi.json":
            self._send_json(self._get_openapi_schema())
            
        elif self.path == "/docs":
            html = """<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="utf-8" />
                <title>Vero Control API - Swagger UI</title>
                <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
            </head>
            <body>
                <div id="swagger-ui"></div>
                <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js" crossorigin></script>
                <script>
                    window.onload = () => {
                        window.ui = SwaggerUIBundle({
                            url: '/openapi.json',
                            dom_id: '#swagger-ui',
                        });
                    };
                </script>
            </body>
            </html>"""
            self._send_html(html)
                
        else:
            self._send_error("Endpoint not found", 404)

    def do_POST(self):
        """Handle POST requests."""
        server = cast(Any, self.server)
        if self.path == "/stop":
            # Fire and forget stop
            import asyncio
            
            app = server.app_instance
            if app._loop and app._loop.is_running():
                app._loop.call_soon_threadsafe(lambda: asyncio.create_task(app.stop()))
            else:
                # Fallback for backtest loop
                app._stop_event.set()
                app._status = "STOPPING" # Enum handling needed ideally
                
            self._send_json({"message": "Stop signal sent"})
            
        else:
            self._send_error("Endpoint not found", 404)
            
    def log_message(self, format, *args):
        # Override to silence default stderr logging or route to logger
        pass


class APIServer(threading.Thread):
    """
    Background Thread running the HTTP Server.
    """
    
    def __init__(self, app_instance, port: int = 8000):
        super().__init__(daemon=True)
        self.app_instance = app_instance
        self.port = port
        self.server = None
        self._is_running = False

    def run(self):
        try:
            self.server = HTTPServer(("0.0.0.0", self.port), APIHandler)
            # Inject app instance so handler can access it
            server = cast(Any, self.server)
            server.app_instance = self.app_instance
            
            self._is_running = True
            logger.info(f"Control API Server started on port {self.port}")
            self.server.serve_forever()
        except OSError as e:
            logger.error(f"Failed to start API Server on port {self.port}: {e}")
            self._is_running = False
        except Exception as e:
            logger.error(f"API Server crashed: {e}")
            self._is_running = False

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Control API Server stopped")
