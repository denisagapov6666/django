from cloudapps.app import scheduler, db
from datetime import datetime, timedelta
from cloudapps.models import Task, Reminder, Notification, Section, Investigation, SalaryMetrics, User, fcm
import json, os
from sqlalchemy import func, text, select
import firebase_admin
from firebase_admin import credentials, messaging
from flask import current_app

@scheduler.task('cron', id='updateTask', minute='*')
def update_task():
    with scheduler.app.app_context():

        keyFile = f"{current_app.root_path}/serviceAccountKey.json"

        fileExists = os.path.exists(keyFile)
        if fileExists:
            cred = credentials.Certificate(keyFile)
            firebase_admin.initialize_app(cred)

        current_time = datetime.now().strftime("%H:%M:%S")

        tasks = Task.query.filter((Task.start_time <= current_time) & (Task.start_time >= func.SUBTIME(current_time, '00:03:00'))).all()

        # Update task fulfillment
        for task in tasks:
            if task.fulfillment == 'awaiting':
                scheduleList = json.loads(task.schedule)
                day = datetime.now().strftime('%A')
                date = datetime.now().strftime('%m/%d/%Y')

                if task.type == 'daily' and day in scheduleList:
                    task.fulfillment = 'pending'
                elif task.type == 'weekly' and day in scheduleList:
                    task.fulfillment = 'pending'
                elif task.type == 'monthly' and date in scheduleList:
                    task.fulfillment = 'pending'
                elif task.type == 'urgent' and date == task.schedule:
                    task.fulfillment = 'pending'

        tasks1 = Task.query.filter(Task.fulfillment == 'pending').all()

        # Mark task as not completed
        for task in tasks1:
            if str(task.end_time) <= current_time:
                task.fulfillment = 'notcompleted'

                user_id = (Section.query.filter(Section.id == task.section_id).first()).user_id

                if fileExists:
                    fcm_token = fcm.query.filter(fcm.user_id==user_id).order_by(fcm.id.desc()).with_entities(fcm.fcm_token).first()

                    if fcm_token:
                        message = messaging.Message(
                                notification=messaging.Notification(
                                    title='Task Incomplete!',
                                    body=f'{task.name} is not completed by you!',
                                ),
                                token=fcm_token,
                            )
                reminder_exists = Reminder.query.join(Section, Section.user_id == Reminder.user_id).filter(Section.id == task.section_id).first()
                if not reminder_exists:
                    
                    investigation = Investigation(user_id=user_id, task_id=task.id, status=1)
                    db.session.add(investigation)

        reminders = db.session.execute(text("""
            SELECT
                r.id AS id,
                r.user_id AS user_id,
                r.to_user_id AS to_user_id,
                t.id AS task_id,
                t.name AS task_name
            FROM `reminder` AS r
            JOIN `sections` AS s ON s.user_id = r.user_id
            JOIN `tasks` AS t ON t.section_id = s.id
            WHERE t.fulfillment = 'notcompleted'
            AND r.id IN (
                SELECT MIN(id)
                FROM `reminder`
                WHERE user_id = r.user_id
            )
            GROUP BY t.id;
        """.format(current_time))).fetchall()

        for reminder in reminders:
            notification = Notification.query.filter(Notification.task_id == reminder.task_id, Notification.reminder_id == reminder.id).first()
            if not notification:
                notification = Notification(
                    reminder_id=reminder.id,
                    user_id=reminder.user_id,
                    to_user_id=reminder.to_user_id,
                    task_id=reminder.task_id,
                    time=current_time,
                    title='New Task Reminder!',
                    description=f'{reminder.task_name} is reminded to you!',
                    is_last=1
                )
                db.session.add(notification)

                if fileExists:
                    fcm_token = fcm.query.filter(fcm.user_id==reminder.to_user_id).order_by(fcm.id.desc()).with_entities(fcm.fcm_token).first()

                    if fcm_token:
                        message = messaging.Message(
                                notification=messaging.Notification(
                                    title='New Task Reminder!',
                                    body=f'{reminder.task_name} is reminded to you!',
                                ),
                                token=fcm_token,
                            )
            else:
                next_r = db.session.execute(text("""
                SELECT id, user_id, to_user_id FROM `reminder` r 
                WHERE r.user_id = {} AND r.id > (SELECT MAX(reminder_id) FROM `notifications` WHERE task_id = {}) 
                AND ADDTIME((SELECT deadline FROM `reminder` WHERE id = (SELECT MAX(reminder_id) FROM `notifications` WHERE task_id = {}) LIMIT 1), (SELECT TIME(updated_at) FROM `notifications` WHERE task_id = {} AND is_last=1)) <= '{}' LIMIT 1
                """.format(reminder.user_id, reminder.task_id, reminder.task_id, reminder.task_id, current_time))).fetchone()

                if next_r:
                    max_reminder_id = Notification.query \
                        .filter(Notification.task_id == reminder.task_id) \
                        .with_entities(func.max(Notification.reminder_id)) \
                        .scalar()

                    prev_noti = Notification.query \
                        .filter(Notification.reminder_id == max_reminder_id) \
                        .first()
                    prev_noti.is_last = 0
                    
                    notification_new = Notification(
                        reminder_id=next_r.id,
                        user_id=next_r.user_id,
                        to_user_id=next_r.to_user_id,
                        task_id=reminder.task_id,
                        time=current_time,
                        title='New Task Reminder!',
                        description=f'{reminder.task_name} is reminded to you!',
                        is_last=1
                    )
                    db.session.add(notification_new)

                    if fileExists:
                        fcm_token = fcm.query.filter(fcm.user_id==next_r.to_user_id).order_by(fcm.id.desc()).with_entities(fcm.fcm_token).first()

                        if fcm_token:
                            message = messaging.Message(
                                    notification=messaging.Notification(
                                        title='New Task Reminder!',
                                        body=f'{reminder.task_name} is reminded to you!',
                                    ),
                                    token=fcm_token,
                                )

                else:
                    notification_exists = (
                        db.session.query(Notification)
                            .filter(Notification.reminder_id.in_(
                                db.session.query(func.max(Reminder.id).label('max_id'))
                                .filter(Reminder.user_id == Notification.user_id)
                                .group_by(Reminder.user_id)
                                .subquery()
                            ))
                            .filter(Notification.task_id == reminder.task_id)
                            .all()
                    )

                    if notification_exists:
                        investigation_exists = Investigation.query.filter(Investigation.task_id == reminder.task_id).first()

                        if not investigation_exists:
                            investigation = Investigation(user_id=reminder.user_id, task_id=reminder.task_id, status=1)
                            db.session.add(investigation)

        users = User.query.all()

        for user in users:
            salary_metrics = SalaryMetrics.query.filter(SalaryMetrics.user_id == user.id, func.DATE(SalaryMetrics.created_at) == datetime.now().strftime('%Y-%m-%d')).first()
            if not salary_metrics:
                salary_metric = SalaryMetrics(user_id=user.id, worked_time='00:00:00', salary=0)
                db.session.add(salary_metric)

        db.session.commit()
