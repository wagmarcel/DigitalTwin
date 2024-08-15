import http.server
import socketserver
import argparse
import os

class SingleFileRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.file_to_serve = kwargs.pop('file_to_serve')
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == f'/{os.path.basename(self.file_to_serve)}':
            self.path = f'/{self.file_to_serve}'
        else:
            self.send_error(404, "File not found")
            return

        return super().do_GET()

def run_server(port, file_to_serve):
    handler = lambda *args, **kwargs: SingleFileRequestHandler(*args, file_to_serve=file_to_serve, **kwargs)
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving {file_to_serve} on port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal web server to serve a single file.")
    parser.add_argument('file', help="The file to be served")
    parser.add_argument('-p', '--port', type=int, default=8000, help="Port number to serve the file on (default: 8000)")
    
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: {args.file} is not a valid file.")
        exit(1)

    run_server(args.port, args.file)
