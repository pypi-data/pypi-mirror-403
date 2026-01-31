"""
Simple HTTP API Server
======================
A lightweight, reusable API server built on Python's built-in http.server module.
Supports GET and POST requests with JSON data handling.
Python http.server doc: https://docs.python.org/3/library/http.server.html

Features:
    - Zero external dependencies (uses only stdlib)
    - JSON request/response handling
    - Simple route registration
    - Error handling for invalid JSON and server errors
"""

import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler


class APIRequestHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP request handler for API endpoints.
    
    Handles GET and POST requests with automatic JSON parsing and error handling.
    Routes are registered dynamically via the APIServer class.
    
    Attributes:
        routes (dict): Dictionary mapping (method, path) to handler functions
    """
    
    routes = {}  # Will be set by APIServer
    
    def log_message(self, format, *args):
        """Override to customize logging format."""
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def do_GET(self):
        """
        Handle GET requests.
        
        Routes requests to appropriate handler functions based on path.
        Sends 404 if no matching route is found.
        """
        sys.stdout.write(f"Received GET request: {self.path}\n")
        
        handler = self.routes.get(('GET', self.path))
        if handler:
            try:
                result = handler(self)
                self._send_json_response(200, result)
            except Exception as exc:
                self._send_error_response(500, str(exc))
        else:
            self._send_error_response(404, "Endpoint not found")

    def do_POST(self):
        """
        Handle POST requests.
        
        Automatically parses JSON from request body and passes to handler.
        Handles JSON parsing errors and other exceptions gracefully.
        Sends 404 if no matching route is found.
        """
        sys.stdout.write(f"Received POST request: {self.path}\n")
        
        handler = self.routes.get(('POST', self.path))
        if not handler:
            self._send_error_response(404, "Endpoint not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8")) if post_data else {}
            
            result = handler(self, data)
            self._send_json_response(200, result)
            
        except json.JSONDecodeError as exc:
            self._send_error_response(400, f"Invalid JSON: {str(exc)}")
            
        except Exception as exc:
            self._send_error_response(500, str(exc))

    def _send_json_response(self, status, data):
        """
        Send JSON response.
        
        Args:
            status (int): HTTP status code
            data: Data to serialize to JSON (dict, list, str, etc.)
        """
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        
        if isinstance(data, (dict, list)):
            response = json.dumps(data, indent=2)
        elif isinstance(data, str):
            response = json.dumps({"message": data})
        else:
            response = json.dumps({"result": str(data)})
            
        self.wfile.write(response.encode())

    def _send_error_response(self, status, message):
        """
        Send error response.
        
        Args:
            status (int): HTTP status code
            message (str): Error message
        """
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {"error": message}
        self.wfile.write(json.dumps(response).encode())


class APIServer:
    """
    Simple API Server with route registration.
    
    Example:
        >>> server = APIServer(port=8000)
        >>> server.add_route('GET', '/hello', lambda req: "Hello!")
        >>> server.run()
    
    Attributes:
        host (str): Server host address
        port (int): Server port number
        routes (dict): Registered routes
    """
    
    def __init__(self, host="0.0.0.0", port=8000):
        """
        Initialize API Server.
        
        Args:
            host (str): Host address to bind to. Default is '0.0.0.0'
            port (int): Port number to listen on. Default is 8000
        """
        self.host = host
        self.port = port
        self.routes = {}
    
    def add_route(self, method, path, handler):
        """
        Register a route handler.
        
        Args:
            method (str): HTTP method ('GET' or 'POST')
            path (str): URL path (e.g., '/api/hello')
            handler (callable): Function to handle the request
                - For GET: handler(request) -> response_data
                - For POST: handler(request, data) -> response_data
        
        Example:
            >>> def hello_handler(req):
            ...     return {"message": "Hello World"}
            >>> server.add_route('GET', '/hello', hello_handler)
        """
        self.routes[(method.upper(), path)] = handler
        sys.stdout.write(f"Registered {method.upper()} {path}\n")
    
    def run(self):
        """
        Start the HTTP server.
        
        Runs indefinitely until interrupted with Ctrl+C.
        """
        # Create handler class with routes
        handler_class = type(
            'CustomHandler',
            (APIRequestHandler,),
            {'routes': self.routes}
        )
        
        server_address = (self.host, self.port)
        httpd = HTTPServer(server_address, handler_class)
        
        sys.stdout.write(f"\n{'='*50}\n")
        sys.stdout.write(f"Server running at http://{self.host}:{self.port}\n")
        sys.stdout.write(f"Registered routes:\n")
        for (method, path) in self.routes.keys():
            sys.stdout.write(f"  {method:6} {path}\n")
        sys.stdout.write(f"{'='*50}\n")
        sys.stdout.write(f"Press Ctrl+C to stop\n\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            sys.stdout.write("\n\nShutting down server...\n")
            httpd.shutdown()
