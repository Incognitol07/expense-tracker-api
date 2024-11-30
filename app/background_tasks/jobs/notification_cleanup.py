from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Notification
from app.utils import logger

def delete_old_notifications():
    """
    Deletes notifications that are older than 30 days.
    """
    db = SessionLocal()
    try:
        # Calculate the threshold date
        threshold_date = datetime.now() - timedelta(days=30)

        # Query and delete notifications older than the threshold
        deleted_count = (
            db.query(Notification)
            .filter(Notification.created_at < threshold_date)
            .delete()
        )
        db.commit()

        # Log the cleanup process
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} notifications older than 30 days.")
        else:
            logger.info("No notifications older than 30 days to delete.")
    except Exception as e:
        logger.error(f"Error occurred while deleting old notifications: {e}")
    finally:
        db.close()