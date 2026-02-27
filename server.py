import http.server
import socketserver
import urllib.parse
import os
import json

PORT = int(os.environ.get("PORT", 8000))

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/subscribe':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                if 'application/json' in self.headers.get('Content-Type', ''):
                    data = json.loads(post_data.decode('utf-8'))
                else:
                    data = dict(urllib.parse.parse_qsl(post_data.decode('utf-8')))

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'status': 'success', 
                    'message': f'Successfully subscribed {data.get("email", "to the pelleton")}!'
                }
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())
        else:
            self.send_error(404, "Endpoint not found")

if __name__ == '__main__':
    # Change into the directory containing this script so simple server serves the frontend files
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Server running on port {PORT}. Connect to http://localhost:{PORT}")
        httpd.serve_forever()
