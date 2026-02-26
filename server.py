import http.server
import socketserver
import urllib.parse
import sqlite3
import json
import os

PORT = 8000

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            plan TEXT
        )
    ''')
    conn.commit()
    conn.close()

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

                conn = sqlite3.connect('subscribers.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO subscribers (name, email, address, city, state, zip, plan)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('name'), 
                    data.get('email'), 
                    data.get('address'),
                    data.get('city'), 
                    data.get('state'), 
                    data.get('zip'), 
                    data.get('plan')
                ))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': 'Successfully subscribed!'}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())
        else:
            self.send_error(404, "Endpoint not found")

if __name__ == '__main__':
    init_db()
    
    # Change into the directory containing this script so simple server serves the frontend files
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Server running on port {PORT}. Connect to http://localhost:{PORT}")
        httpd.serve_forever()
