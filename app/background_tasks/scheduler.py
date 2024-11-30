from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.background_tasks.jobs.notification_cleanup import delete_old_notifications
from app.database import SessionLocal
from app.models import User
from asgiref.sync import async_to_sync
from .jobs import check_and_deactivate_expired_budgets, check_budget, check_category_budget

scheduler = BackgroundScheduler()

def start_scheduler():
    # Add jobs to the scheduler
    scheduler.add_job(delete_old_notifications, IntervalTrigger(days=1))
    scheduler.add_job(check_and_deactivate_expired_budgets, IntervalTrigger(minutes=5))
    scheduler.add_job(async_to_sync(check_all_thresholds), IntervalTrigger(minutes=5))

    # Start the scheduler
    scheduler.start()

async def check_all_thresholds():
    """
    Checks budget and alert thresholds for all users in a single job.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users: # Check thresholds for each user
            await check_budget(user.id)  # Check budget for each user
            await check_category_budget(user.id)
    finally:
        db.close()