import os
import socket


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
    except OSError:
        return "YOUR_LOCAL_IP"


def get_public_url(port=5000):
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        return render_url.rstrip("/")
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        domain = railway_domain.strip()
        if not domain.startswith(("http://", "https://")):
            domain = f"https://{domain}"
        return domain.rstrip("/")
    custom_url = os.environ.get("APP_PUBLIC_URL") or os.environ.get("PUBLIC_URL")
    if custom_url:
        return custom_url.rstrip("/")
    return f"http://{get_local_ip()}:{port}"


def print_server_urls(port=5000):
    print("Server Running:")
    print(f"Local: http://127.0.0.1:{port}")
    print(f"Public: {get_public_url(port=port)}")
