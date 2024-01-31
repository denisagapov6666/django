from flask import Blueprint, request, jsonify, current_app
from .models import Section, Task, User, Investigation, SalaryMetrics, Notification, fcm
from .app import db
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func
import os, json

apis = Blueprint('apis', __name__)

@apis.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    fcm_token = data.get('fcm_token')

    if not fcm_token:
        return jsonify(error='fcm token missing!')
    
    user = User.query.filter_by(email=username).first_or_404()

    if user and check_password_hash(user.password, password):
        newFcm = fcm(user_id=user.id, fcm_token=fcm_token)
        db.session.add(newFcm)

        db.session.commit()

        return jsonify({'message': 'Login successful', 'userId': int(user.id), 'start_duty': str(user.start_duty), 'end_duty': str(user.end_duty)})
    else:
        return jsonify({'message': 'Invalid username or password'})

@apis.route('/sections', methods=['GET'])
def sections():
    userId = request.args.get('userId')
    type = request.args.get('type')

    if type not in ['daily','weekly','monthly','urgent']:
        return jsonify(error='type not valid!')
        
    sections = (
        Section.query
        .with_entities(Section.id, Section.user_id, Section.name, Section.type, func.count(Task.id).label('task_count'))
        .join(Task, Task.section_id == Section.id)
        .filter(Section.user_id == userId, Section.type == type)
        .group_by(Section.id)
        .order_by(Section.id.desc())
        .all()
    )


    section_data = []
    for section in sections:
        section_data.append({
            'id': section.id,
            'user_id': section.user_id,
            'name': section.name,
            'type': section.type,
            'task_count': section.task_count
        })
        
    if sections:
        return jsonify(sections=section_data)
    else:
        return jsonify(error='no data found!')

@apis.route('/tasks', methods=['GET'])
def tasks():
    sectionId = request.args.get('sectionId')

    tasks = Task.query.filter(Task.section_id==sectionId, Task.status==1).order_by(Task.priority.desc()).all()

    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'type': task.type,
            'schedule': task.schedule,
            'start_time': str(task.start_time),
            'end_time': str(task.end_time),
            'image_en': task.image_en,
            'video_en': task.video_en,
            'voice_en': task.voice_en,
            'note': task.note,
            'complaint': task.complaint,
            'fulfillment': task.fulfillment,
            'created_at': task.created_at,
            'updated_at': task.updated_at
        })

    if tasks:
        return jsonify(tasks=tasks_data)
    else:
        return jsonify(error='no data found!')
    
@apis.route('/notifications', methods=['GET'])
def notifications():
    userId = request.args.get('userId')

    notifications = Notification.query.filter(Notification.to_user_id==userId).order_by(Notification.id.desc()).all()

    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'description': notification.description,
            'task_id': notification.task_id,
            'time': str(notification.time),
            'created_at': notification.created_at,
            'updated_at': notification.updated_at
        })

    if notifications:
        return jsonify(notifications=notifications_data)
    else:
        return jsonify(error='no data found!')
    
@apis.route('/not-completed-tasks', methods=['GET'])
def notCompletedTasks():
    sectionId = request.args.get('sectionId')

    investigationId = Investigation.query.join(Section, Section.user_id==Investigation.user_id).filter(Section.id==sectionId).with_entities(Investigation.task_id).subquery()
    notCompletedTasks = Task.query\
        .filter(
            Task.fulfillment == 'notcompleted',
            Task.section_id == sectionId,
            Task.id.in_(investigationId)
        )\
        .order_by(Task.id.desc())\
        .all()
    
    tasks_data = []
    for task in notCompletedTasks:
        tasks_data.append({
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'type': task.type,
            'schedule': task.schedule,
            'start_time': str(task.start_time),
            'end_time': str(task.end_time),
            'image_en': task.image_en,
            'video_en': task.video_en,
            'voice_en': task.voice_en,
            'note': task.note,
            'complaint': task.complaint,
            'fulfillment': task.fulfillment,
            'created_at': task.created_at,
            'updated_at': task.updated_at
        })
    
    if notCompletedTasks:
        return jsonify(notCompletedTasks=tasks_data)
    else:
        return jsonify(error='no data found!')
    
@apis.route('/check-media-options', methods=['GET'])
def checkMediaOptions():
    taskId = request.args.get('taskId')
    task_media = Task.query.filter_by(id=taskId).with_entities(Task.image_en,Task.video_en,Task.voice_en).first()

    if task_media:

        task_media_dict = {
            'image_en': task_media.image_en,
            'video_en': task_media.video_en,
            'voice_en': task_media.voice_en
        }

        return jsonify(task_media=task_media_dict)
    else:
        return jsonify(error='no data found!')
    
@apis.route('/complete-task', methods=['POST'])
def completeTask():
    taskId = request.args.get('taskId')

    task_media = Task.query.filter_by(id=taskId).with_entities(Task.image_en,Task.video_en,Task.voice_en).first()
    image_en = 'image' in request.files if task_media[0] == 1 else True
    video_en = 'video' in request.files if task_media[1] == 1 else True
    voice_en = 'voice' in request.files if task_media[2] == 1 else True

    if not image_en or not video_en or not voice_en:
        return jsonify(error=f'image or video or voice not provided')
    
    task = Task.query.get_or_404(taskId)

    task.fulfillment = 'completed'

    dir = ''

    if image_en:
        image_file = request.files['image']
        filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image_file.filename)}'
        dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
        image_file.save(dir)
        
        task.image = f'uploads/images/{filename}'
    
    if video_en:
        video_file = request.files['video']
        filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(video_file.filename)}'
        dir = os.path.join(current_app.root_path, 'static', 'uploads', 'videos', filename)
        video_file.save(dir)

        task.video = f'uploads/videos/{filename}'

    if voice_en:
        voice_file = request.files['voice']
        filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(voice_file.filename)}'
        dir = os.path.join(current_app.root_path, 'static', 'uploads', 'voices', filename)
        voice_file.save(dir)

        task.voice = f'uploads/voices/{filename}'

    db.session.commit()

    return jsonify('task completed successfully!')

@apis.route('/update-working-hours', methods=['POST'])
def updateWorkingHours():
    userId = request.args.get('userId')
    workedHours = request.args.get('workedHours')

    if isinstance(workedHours, (int, float)):
        return jsonify(error='Input valid hours!')
    
    salary_metric = SalaryMetrics.query.filter(SalaryMetrics.user_id==userId).order_by(SalaryMetrics.id.desc()).first_or_404()

    salary_metric.worked_time = addTime(salary_metric.worked_time, workedHours)

    db.session.commit()

    return jsonify('working hours updated successfully!')

def addTime(baseTime, workTime):
    if '.' in workTime:
        hours, minutes = map(int, str(workTime).split('.'))
    else:
        hours, minutes = int(workTime), 0

    workTime = timedelta(hours=hours, minutes=minutes)
    baseTime = datetime.strptime(str(baseTime), '%H:%M:%S')
    
    convTime = (baseTime + workTime).time()

    return convTime.strftime('%H:%M:%S')

@apis.route('/update-task-noncompleted', methods=['POST'])
def updateTaskNonCompleted():
    taskId = request.args.get('taskId')
    
    task = Task.query.get_or_404(taskId)

    task.fulfillment='notcompleted'

    db.session.commit()

    return jsonify('task updated successfully!')

@apis.route('/update-task-completed', methods=['POST'])
def updateTaskCompleted():
    taskId = request.args.get('taskId')
    
    task = Task.query.get_or_404(taskId)

    task.fulfillment='completed'

    db.session.commit()

    return jsonify('task updated successfully!')

@apis.route('/update-task-complaint', methods=['POST'])
def updateTaskComplaint():
    taskId = request.args.get('taskId')
    complaint = request.args.get('complaint')
    
    task = Task.query.get_or_404(taskId)

    task.complaint=complaint

    db.session.commit()

    return jsonify('task updated successfully!')
