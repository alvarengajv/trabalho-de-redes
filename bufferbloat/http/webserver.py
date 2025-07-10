try:
    # Python 2
    import SimpleHTTPServer
    import SocketServer
    HTTPServer = SocketServer.TCPServer
    HTTPRequestHandler = SimpleHTTPServer.SimpleHTTPRequestHandler
except ImportError:
    # Python 3
    import http.server
    import socketserver
    HTTPServer = socketserver.TCPServer
    HTTPRequestHandler = http.server.SimpleHTTPRequestHandler

PORT = 80

class Handler(HTTPRequestHandler):
    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])

httpd = HTTPServer(("", PORT), Handler)
print("Server1: httpd serving at port", PORT)
httpd.serve_forever()
