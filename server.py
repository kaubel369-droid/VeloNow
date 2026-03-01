import http.server
import socketserver
import urllib.parse
import os
import json
import psycopg2
from psycopg2 import pool

PORT = int(os.environ.get("PORT", 8000))
DATABASE_URL = os.environ.get("DATABASE_URL")

# Initialize database connection pool
try:
    if DATABASE_URL:
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
        print("Database connection pool initialized.")
        
        # Create table if not exists
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    address TEXT NOT NULL,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    zip TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("Subscribers table verified/created.")
        db_pool.putconn(conn)
    else:
        db_pool = None
        print("DATABASE_URL not set. Running in memory-only mode.")
except Exception as e:
    print(f"Error initializing database: {e}")
    db_pool = None

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

                # Extract all fields
                name = data.get('name')
                email = data.get('email')
                address = data.get('address')
                city = data.get('city')
                state = data.get('state')
                zip_code = data.get('zip')
                plan = data.get('plan', 'digital')

                if db_pool:
                    conn = db_pool.getconn()
                    try:
                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO subscribers (name, email, address, city, state, zip, plan)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (email) DO UPDATE SET
                                name = EXCLUDED.name,
                                address = EXCLUDED.address,
                                city = EXCLUDED.city,
                                state = EXCLUDED.state,
                                zip = EXCLUDED.zip,
                                plan = EXCLUDED.plan;
                            """, (name, email, address, city, state, zip_code, plan))
                            conn.commit()
                    finally:
                        db_pool.putconn(conn)
                    msg = f'Successfully subscribed {email} to the peloton!'
                else:
                    msg = f'Successfully subscribed {email} (Development mode - no database)!'

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'status': 'success', 
                    'message': msg
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
