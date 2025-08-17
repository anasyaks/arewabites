from app import create_app, db, socketio
from app.models import Vendor
import os

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # This part will only create the database and admin if they don't exist
        # in your local development environment.
        if not os.path.exists('app/site.db'):
            db.create_all()
            Vendor.create_admin()

    socketio.run(app, debug=True)