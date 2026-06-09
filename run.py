import os
import socket

from app import create_app
from app.config import DevelopmentConfig

app = create_app(DevelopmentConfig)


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
    except OSError:
        return "YOUR_LOCAL_IP"


def print_server_urls(port=5000):
    print("Server Running:")
    print(f"Local: http://127.0.0.1:{port}")
    print(f"Network: http://{get_local_ip()}:{port}")


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", "5000"))
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print_server_urls(port=port)
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=debug)
