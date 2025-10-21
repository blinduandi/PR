#!/usr/bin/env python3
"""
Lab 1 Style Server - Simple Single-threaded HTTP Server
This simulates the "previous lab" single-threaded server for comparison.
"""

import os
import time
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from http import HTTPStatus


class Lab1Handler(SimpleHTTPRequestHandler):
    """Simple handler with delay - always single-threaded"""
    
    def do_GET(self):
        # Add artificial delay to simulate work
        delay = float(os.getenv('HANDLER_DELAY', '1.0'))
        time.sleep(delay)
        
        # Serve the request normally
        super().do_GET()
    
    def log_message(self, format, *args):
        # Simple logging
        print(f"Lab1 Server: {format % args}")


def main():
    parser = argparse.ArgumentParser(description="Lab 1 Style Single-threaded HTTP Server")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on (default: 8001)")
    parser.add_argument("--doc-root", type=str, default="www", help="Document root directory")
    parser.add_argument("--delay", type=float, default=1.0, help="Handler delay in seconds")
    
    args = parser.parse_args()
    
    # Set environment for handler
    os.environ['HANDLER_DELAY'] = str(args.delay)
    
    # Change to document root
    if os.path.exists(args.doc_root):
        os.chdir(args.doc_root)
    
    # Create single-threaded server (NOT ThreadingHTTPServer)
    httpd = HTTPServer(("0.0.0.0", args.port), Lab1Handler)
    
    print(f"Lab 1 Single-threaded Server starting...")
    print(f"   Port: {args.port}")
    print(f"   Document Root: {args.doc_root}")
    print(f"   Handler Delay: {args.delay}s")
    print(f"   URL: http://localhost:{args.port}/")
    print(f"\nWARNING: This server processes requests ONE AT A TIME (no threading)")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nLab 1 Server shutting down...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()