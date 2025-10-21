#!/usr/bin/env python3
"""
HTTP File Server with TCP Sockets
Lab 1 - Protocols and Programming (PR)

A simple HTTP file server that serves static files from a directory.
Supports HTML, PNG, and PDF files with directory listing functionality.
Built using raw TCP sockets for educational purposes.
"""

import socket
import os
import sys
import urllib.parse
from datetime import datetime

def get_mime_type(file_path):
    """Get MIME type for file"""
    if file_path.endswith('.html'):
        return 'text/html'
    elif file_path.endswith('.png'):
        return 'image/png'
    elif file_path.endswith('.pdf'):
        return 'application/pdf'
    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        return 'image/jpeg'
    else:
        return 'text/plain'

def create_response(status, content_type, body):
    """Create proper HTTP response"""
    if isinstance(body, str):
        body = body.encode('utf-8')
    
    # Simple, working HTTP response format with proper charset
    response = f"HTTP/1.1 {status}\r\n"
    if content_type == "text/html":
        response += f"Content-Type: {content_type}; charset=utf-8\r\n"
    else:
        response += f"Content-Type: {content_type}\r\n"
    response += f"Content-Length: {len(body)}\r\n"
    response += "Connection: close\r\n"
    response += "\r\n"
    
    return response.encode('utf-8') + body

def create_404():
    """Create 404 response"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .error-container {
            background: rgba(255,255,255,0.1);
            padding: 60px 40px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            max-width: 500px;
        }
        h1 {
            font-size: 4em;
            margin-bottom: 20px;
            font-weight: 300;
        }
        p {
            font-size: 1.2em;
            margin-bottom: 30px;
            opacity: 0.8;
        }
        a {
            color: #ffffff;
            text-decoration: none;
            padding: 15px 30px;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 25px;
            transition: all 0.3s ease;
            display: inline-block;
        }
        a:hover {
            background: rgba(255,255,255,0.2);
            border-color: rgba(255,255,255,0.6);
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>404</h1>
        <p>The requested file was not found on this server.</p>
        <a href="/">&larr; Back to Digital Library</a>
    </div>
</body>
</html>"""
    return create_response("404 Not Found", "text/html", html)

def create_directory_listing(dir_path, url_path):
    """Create directory listing"""
    items = []
    
    # Add parent directory if not root
    if url_path != '/':
        parent = '/'.join(url_path.rstrip('/').split('/')[:-1]) or '/'
        items.append(f'''<tr>
            <td><a href="{parent}" class="file-link">
                <span class="file-icon icon-dir">DIR</span>
                <span class="file-name">&uarr; Parent Directory</span>
            </a></td>
            <td class="file-size">-</td>
        </tr>''')
    
    # List contents
    try:
        for item in sorted(os.listdir(dir_path)):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                href = f"{url_path.rstrip('/')}/{item}/"
                items.append(f'''<tr>
                    <td><a href="{href}" class="file-link">
                        <span class="file-icon icon-dir">DIR</span>
                        <span class="file-name">&raquo; {item}/</span>
                    </a></td>
                    <td class="file-size">-</td>
                </tr>''')
            else:
                href = f"{url_path.rstrip('/')}/{item}"
                size = os.path.getsize(item_path)
                
                # Get file type icon and prefix
                if item.endswith('.pdf'):
                    icon_class = 'icon-pdf'
                    icon_text = 'PDF'
                    prefix = '&sdot;'
                elif item.endswith(('.png', '.jpg', '.jpeg')):
                    icon_class = 'icon-img'
                    icon_text = 'IMG'
                    prefix = '&hearts;'
                elif item.endswith('.html'):
                    icon_class = 'icon-html'
                    icon_text = 'WEB'
                    prefix = '&clubs;'
                else:
                    icon_class = 'icon-file'
                    icon_text = 'FILE'
                    prefix = '&diams;'
                
                # Format file size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024*1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/(1024*1024):.1f} MB"
                
                items.append(f'''<tr>
                    <td><a href="{href}" class="file-link">
                        <span class="file-icon {icon_class}">{icon_text}</span>
                        <span class="file-name">{prefix} {item}</span>
                    </a></td>
                    <td class="file-size">{size_str}</td>
                </tr>''')
    except:
        items.append('<tr><td>Error listing directory</td><td class="size">-</td></tr>')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index of {url_path}</title>
    <style>
        * {{ 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }}
        
        body {{ 
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
            overflow-x: auto;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.12);
            border-radius: 20px;
            padding: 40px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        h1 {{ 
            font-size: 2.8em;
            margin-bottom: 15px;
            font-weight: 600;
            background: linear-gradient(45deg, #ffffff, #e0e8ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: none;
        }}
        
        .breadcrumb {{
            background: rgba(0, 0, 0, 0.25);
            padding: 16px 24px;
            border-radius: 12px;
            margin-bottom: 35px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 1.1em;
            border-left: 4px solid #4fc3f7;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .breadcrumb::before {{
            content: "⌂";
            font-size: 1.2em;
            font-weight: bold;
            margin-right: 8px;
        }}
        
        .file-table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        }}
        
        .file-table thead {{
            background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.25));
        }}
        
        .file-table th {{
            padding: 20px 24px;
            text-align: left;
            font-weight: 600;
            font-size: 1.1em;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            border: none;
        }}
        
        .file-table td {{
            padding: 16px 24px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            vertical-align: middle;
        }}
        
        .file-table tr:hover {{
            background: rgba(255, 255, 255, 0.12);
            transform: translateY(-1px);
            transition: all 0.2s ease;
        }}
        
        .file-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .file-link {{
            color: #ffffff;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.05em;
            transition: all 0.2s ease;
        }}
        
        .file-link:hover {{
            color: #81d4fa;
            transform: translateX(4px);
        }}
        
        .file-icon {{
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-weight: 600;
            padding: 8px 12px;
            border-radius: 10px;
            font-size: 0.7em;
            letter-spacing: 0.5px;
            min-width: 55px;
            text-align: center;
            border: 2px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            position: relative;
            overflow: hidden;
        }}
        
        .file-icon::before {{
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: inherit;
            border-radius: inherit;
            z-index: -1;
        }}
        
        .icon-dir {{ 
            background: linear-gradient(135deg, #FFD700, #FFA500); 
            color: #333; 
            border-color: #FFB347;
        }}
        .icon-pdf {{ 
            background: linear-gradient(135deg, #FF6B6B, #FF4757); 
            color: #fff; 
            border-color: #FF7979;
        }}
        .icon-img {{ 
            background: linear-gradient(135deg, #4ECDC4, #26D0CE); 
            color: #fff; 
            border-color: #55E6E1;
        }}
        .icon-html {{ 
            background: linear-gradient(135deg, #3742FA, #2F3542); 
            color: #fff; 
            border-color: #5352ED;
        }}
        .icon-file {{ 
            background: linear-gradient(135deg, #A4B0BE, #747D8C); 
            color: #fff; 
            border-color: #9CA4AF;
        }}
        
        .file-name {{
            font-weight: 500;
            flex-grow: 1;
        }}
        
        .file-size {{
            text-align: right;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
            color: rgba(255, 255, 255, 0.7);
            min-width: 80px;
            font-weight: 500;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 20px; margin: 10px; }}
            h1 {{ font-size: 2.2em; }}
            .file-table th, .file-table td {{ padding: 12px 16px; }}
            .breadcrumb {{ font-size: 1em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Directory Browser</h1>
        </div>
        
        <div class="breadcrumb">
            <span>Current Path:</span>
            <strong>{url_path}</strong>
        </div>
        
        <table class="file-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Size</th>
                </tr>
            </thead>
            <tbody>
                {''.join(items)}
            </tbody>
        </table>
    </div>
</body>
</html>"""
    return create_response("200 OK", "text/html", html)



def handle_download(root_dir, download_path):
    """Handle file download with proper headers"""
    file_path = os.path.join(root_dir, download_path.lstrip('/'))
    file_path = os.path.abspath(file_path)
    
    # Security check
    if not file_path.startswith(os.path.abspath(root_dir)):
        return create_404()
    
    if os.path.isfile(file_path):
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            mime_type = get_mime_type(file_path)
            filename = os.path.basename(file_path)
            
            # Create response with download headers
            response = f"HTTP/1.1 200 OK\r\n"
            response += f"Content-Type: {mime_type}\r\n"
            response += f"Content-Length: {len(content)}\r\n"
            response += f"Content-Disposition: attachment; filename=\"{filename}\"\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            
            return response.encode('utf-8') + content
        except:
            return create_404()
    
    return create_404()

def handle_request(request_data, root_dir):
    """Handle HTTP request"""
    try:
        # Parse request
        lines = request_data.decode('utf-8').split('\r\n')
        if not lines:
            return create_404()
        
        # Get method and path
        parts = lines[0].split(' ')
        if len(parts) < 2:
            return create_404()
        
        method, url_path = parts[0], parts[1]
        
        if method != 'GET':
            return create_404()
        
        # Clean path
        url_path = urllib.parse.unquote(url_path.split('?')[0])
        if not url_path.startswith('/'):
            url_path = '/' + url_path
        
        # Convert to file path
        if url_path == '/':
            file_path = os.path.join(root_dir, 'index.html')
        else:
            file_path = os.path.join(root_dir, url_path.lstrip('/'))
        
        file_path = os.path.abspath(file_path)
        
        # Security check
        if not file_path.startswith(os.path.abspath(root_dir)):
            return create_404()
        
        print(f"Request: {url_path} -> {file_path}")
        
        # Handle download requests (keep this simple feature)
        if url_path.startswith('/download/'):
            download_path = url_path[10:]  # Remove /download/ prefix
            return handle_download(root_dir, download_path)
        
        # Handle request
        if os.path.isfile(file_path):
            # Check supported extensions
            if not any(file_path.endswith(ext) for ext in ['.html', '.png', '.pdf', '.jpg', '.jpeg']):
                return create_404()
            
            # Read and serve file
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                mime_type = get_mime_type(file_path)
                return create_response("200 OK", mime_type, content)
            except:
                return create_404()
        
        elif os.path.isdir(file_path):
            # Try index.html first
            index_path = os.path.join(file_path, 'index.html')
            if os.path.exists(index_path):
                try:
                    with open(index_path, 'rb') as f:
                        content = f.read()
                    return create_response("200 OK", "text/html", content)
                except:
                    pass
            
            # Return directory listing
            return create_directory_listing(file_path, url_path)
        
        else:
            return create_404()
            
    except Exception as e:
        print(f"Error: {e}")
        return create_404()

def main():
    if len(sys.argv) != 2:
        print("Usage: python server_simple.py <directory>")
        sys.exit(1)
    
    root_dir = sys.argv[1]
    if not os.path.exists(root_dir):
        print(f"Directory {root_dir} does not exist")
        sys.exit(1)
    
    root_dir = os.path.abspath(root_dir)
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('0.0.0.0', 8000))
        server_socket.listen(5)
        
        print(f"🚀 HTTP File Server started on http://localhost:8000")
        print(f"📁 Serving directory: {root_dir}")
        print("💡 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        while True:
            client_socket, addr = server_socket.accept()
            print(f"🔗 Connection from {addr}")
            
            try:
                request_data = client_socket.recv(4096)
                if request_data:
                    response = handle_request(request_data, root_dir)
                    client_socket.sendall(response)
            except Exception as e:
                print(f"❌ Error handling request: {e}")
            finally:
                client_socket.close()
                
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()