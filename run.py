import os

from app import create_app
from app.config import DevelopmentConfig
from server_utils import print_server_urls

app = create_app(DevelopmentConfig)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print_server_urls(port=port)
    app.run(host="0.0.0.0", port=port)
