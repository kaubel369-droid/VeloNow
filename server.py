import http.server
import socketserver
import urllib.parse
import os
import json
import psycopg2
from psycopg2 import pool
import signal
import sys

PORT = int(os.environ.get("PORT", 8000))
DATABASE_URL = os.environ.get("DATABASE_URL")

print(f"DEBUG: Starting server. PORT={PORT}. DATABASE_URL set={'Yes' if DATABASE_URL else 'No'}", flush=True)

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
    print(f"CRITICAL ERROR initializing database: {e}", flush=True)
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
                            print(f"INFO: Successfully saved subscription for {email}", flush=True)
                    finally:
                        db_pool.putconn(conn)
                    msg = f'Successfully subscribed {email} to the peloton!'
                else:
                    msg = f'ERROR: Database not configured. Could not save {email}.'
                    print(f"ERROR: Subscription attempt for {email} failed because db_pool is None", flush=True)
                    raise Exception(msg)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {'status': 'success', 'message': msg}
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())
        else:
            self.send_error(404, "Endpoint not found")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    server_address = ("0.0.0.0", PORT)
    httpd = ThreadingHTTPServer(server_address, MyHandler)
    
    def signal_handler(sig, frame):
        print("\nStopping server...", flush=True)
        httpd.server_close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"Server running on port {PORT} (0.0.0.0). Check http://localhost:{PORT}", flush=True)
    httpd.serve_forever()
