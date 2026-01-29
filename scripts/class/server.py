import socket
import urllib.request
import urllib.error

class Server:
    def __init__(self, data):
        self.name = data.get("name")
        self.type = data.get("type")
        self.ip = data.get("ip")        
        self.hostname = data.get("hostname")
        self.sql_port = int(data.get("sql_port", 3306))
        self.web_port = int(data.get("web_port", 80))
        self.web_port_2 = int(data.get("web_port_2", 8080))

    def __repr__(self):
        return f"<Server: {self.name} ({self.hostname})>"

    def check_web_status(self, port):
        """
        Checks if the web server at the specific port returns HTTP 200 OK.
        """
        # Assume HTTPS for standard secure ports, HTTP for others
        protocol = "https" if port in [443, 8443] else "http"
        url = f"{protocol}://{self.hostname}:{port}/"

        try:
            response = urllib.request.urlopen(url, timeout=2)
            return response.getcode() == 200
        except:
            return False

    def check_mysql_status(self):
        """Checks if the MySQL TCP port is open."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex((self.hostname, self.sql_port))
            sock.close()
            return result == 0 
        except:
            return False