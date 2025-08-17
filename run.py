from app import create_app, db
from flask_migrate import upgrade
import os

app = create_app()

if __name__ == "__main__":
    # Apply migrations before starting the server
    with app.app_context():
        upgrade()

    # Start the server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))