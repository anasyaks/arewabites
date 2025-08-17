# northern-market-hub/app/tasks.py
import os
from app import celery, db, models
from datetime import datetime, timedelta

@celery.task
def cleanup_old_snacks():
    """Deletes snacks older than 24 hours."""
    with db.app.app_context():
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        old_snacks = models.Snack.query.filter(models.Snack.date_posted < twenty_four_hours_ago).all()

        for snack in old_snacks:
            # Delete the file from the filesystem first
            file_path = os.path.join(db.app.root_path, 'static', snack.media_url)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(snack)

        db.session.commit()
        print(f"Cleaned up {len(old_snacks)} old snacks.")