#!/usr/bin/env python3
"""
HTTP Client for File Server
Lab 1 - Protocols and Programming (PR)

A simple HTTP client that can download files from the HTTP file server.
Usage: client.py server_host server_port url_path directory
"""

import socket
import sys
import os
import urllib.parse

class HTTPClient:
    def __init__(self):
        pass
    
    def parse_http_response(self, response_data):
        """Parse HTTP response and return headers and body"""
        try:
            # Split headers and body
            parts = response_data.split(b'\r\n\r\n', 1)
            if len(parts) != 2:
                raise ValueError("Invalid HTTP response format")
            
            headers_data, body = parts
            headers_text = headers_data.decode('utf-8')
            
            # Parse headers
            header_lines = headers_text.split('\r\n')
            status_line = header_lines[0]
            
            # Parse status line
            status_parts = status_line.split(' ', 2)
            if len(status_parts) < 2:
                raise ValueError("Invalid status line")
            
            status_code = int(status_parts[1])
            status_message = status_parts[2] if len(status_parts) > 2 else ""
            
            # Parse header fields
            headers = {}
            for line in header_lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            return {
                'status_code': status_code,
                'status_message': status_message,
                'headers': headers,
                'body': body
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing HTTP response: {e}")
    
    def create_http_request(self, method, path, host, port):
        """Create HTTP request"""
        request = f"{method} {path} HTTP/1.1\r\n"
        request += f"Host: {host}:{port}\r\n"
        request += "User-Agent: HTTPClient/1.0\r\n"
        request += "Connection: close\r\n"
        request += "\r\n"
        return request.encode('utf-8')
    
    def download_file(self, host, port, url_path, save_directory):
        """Download a file from the server"""
        
        # Create socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            print(f"Connecting to {host}:{port}")
            client_socket.connect((host, port))
            
            # Create and send HTTP request
            request = self.create_http_request('GET', url_path, host, port)
            print(f"Sending request: GET {url_path}")
            client_socket.sendall(request)
            
            # Receive response
            response_data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            # Parse response
            response = self.parse_http_response(response_data)
            
            print(f"Response status: {response['status_code']} {response['status_message']}")
            
            if response['status_code'] != 200:
                print(f"Error: Server returned status {response['status_code']}")
                if response['body']:
                    print("Response body:")
                    try:
                        print(response['body'].decode('utf-8'))
                    except UnicodeDecodeError:
                        print("[Binary content]")
                return False
            
            # Get content type
            content_type = response['headers'].get('content-type', 'application/octet-stream')
            print(f"Content-Type: {content_type}")
            
            # Handle different content types
            if content_type.startswith('text/html'):
                # HTML content - print to console
                print("\\n--- HTML Content ---")
                try:
                    html_content = response['body'].decode('utf-8')
                    print(html_content)
                except UnicodeDecodeError:
                    print("[Unable to decode HTML content]")
                print("--- End HTML Content ---\\n")
                
            elif content_type in ['image/png', 'application/pdf'] or url_path.endswith(('.png', '.pdf')):
                # Binary file - save to directory
                filename = os.path.basename(url_path) or 'downloaded_file'
                
                # Ensure save directory exists
                if not os.path.exists(save_directory):
                    os.makedirs(save_directory)
                    print(f"Created directory: {save_directory}")
                
                filepath = os.path.join(save_directory, filename)
                
                # Save file
                with open(filepath, 'wb') as f:
                    f.write(response['body'])
                
                file_size = len(response['body'])
                print(f"Saved {filename} ({file_size} bytes) to {filepath}")
                
            else:
                # Unknown content type - try to display as text, otherwise save as binary
                try:
                    text_content = response['body'].decode('utf-8')
                    print("\\n--- Text Content ---")
                    print(text_content)
                    print("--- End Text Content ---\\n")
                except UnicodeDecodeError:
                    # Save as binary file
                    filename = os.path.basename(url_path) or 'downloaded_file'
                    
                    if not os.path.exists(save_directory):
                        os.makedirs(save_directory)
                    
                    filepath = os.path.join(save_directory, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response['body'])
                    
                    print(f"Saved binary file {filename} to {filepath}")
            
            return True
            
        except socket.error as e:
            print(f"Socket error: {e}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            client_socket.close()

def main():
    """Main function"""
    if len(sys.argv) != 5:
        print("Usage: python client.py server_host server_port url_path directory")
        print("Examples:")
        print("  python client.py localhost 8000 / ./downloads")
        print("  python client.py localhost 8000 /index.html ./downloads")
        print("  python client.py localhost 8000 /networking-basics.pdf ./downloads")
        print("  python client.py 192.168.1.100 8000 /books/ ./downloads")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    url_path = sys.argv[3]
    directory = sys.argv[4]
    
    # Ensure URL path starts with /
    if not url_path.startswith('/'):
        url_path = '/' + url_path
    
    print(f"HTTP Client")
    print(f"Server: {server_host}:{server_port}")
    print(f"Path: {url_path}")
    print(f"Save directory: {directory}")
    print("-" * 40)
    
    client = HTTPClient()
    success = client.download_file(server_host, server_port, url_path, directory)
    
    if success:
        print("\\n✓ Request completed successfully")
    else:
        print("\\n✗ Request failed")
        sys.exit(1)

if __name__ == '__main__':
    main()