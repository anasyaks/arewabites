from app import create_app, db
from flask_migrate import upgrade
from app.models import Vendor
import os

app = create_app()

if __name__ == "__main__":
    # Apply migrations and create admin user before starting the server
    with app.app_context():
        # Apply the latest database migrations
        upgrade()
        
        # Create a default admin user if one does not exist
        # This will now run on every startup, ensuring the admin user is always present
        # especially important if the database is reset.
        Vendor.create_admin()

    # Start the server
    # The app.run() method is suitable for local development. For Render,
    # the Procfile will use gunicorn, so this will be ignored in production.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))