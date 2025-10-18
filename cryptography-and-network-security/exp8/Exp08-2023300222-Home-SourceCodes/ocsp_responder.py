from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class OCSPResponder(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        request = json.loads(post_data)
        serial = request.get('serial_number')

        # Load database
        with open('cert_db.json', 'r') as f:
            cert_db = json.load(f)

        status = cert_db.get(serial, "unknown")

        # Prepare response
        response = {
            "serial_number": serial,
            "status": status
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=OCSPResponder):
    server_address = ('127.0.0.1', 8000)
    httpd = server_class(server_address, handler_class)
    print("✅ OCSP Responder running on http://127.0.0.1:8000/ocsp")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
