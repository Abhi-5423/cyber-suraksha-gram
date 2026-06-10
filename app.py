from app import create_app
from app.config import DevelopmentConfig
from server_utils import print_server_urls

app = create_app(DevelopmentConfig)


if __name__ == "__main__":
    print_server_urls(port=5000)
    app.run(host="0.0.0.0", port=5000, debug=True)
