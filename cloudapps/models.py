from cloudapps.app import db, login_manager
from sqlalchemy import text, ForeignKey
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'

    id = db.Column(db.INT, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mobile = db.Column(db.String(14), nullable=False)
    avatar = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    show_password = db.Column(db.String(150), nullable=False)
    status = db.Column(mysql.TINYINT(1), nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

@login_manager.user_loader
def load_user(user_id):
    manager = Manager.query.get(int(user_id))
    if manager:
        return manager
    
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin
    
    return None
    

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.INT, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    status = db.Column(mysql.TINYINT(1), nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    users = relationship('User', backref='project')
    managers = relationship('Manager', backref='project')
    trainings = relationship('Training', backref='project')
    rules = relationship('Rule', backref='project')

class Manager(db.Model, UserMixin):
    __tablename__ = 'manager'

    id = db.Column(db.INT, primary_key=True)
    project_id = db.Column(db.INT, ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mobile = db.Column(db.String(14), nullable=False)
    role = db.Column(db.Enum('supermanager','manager'), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    show_password = db.Column(db.String(150), nullable=False)
    status = db.Column(mysql.TINYINT(1), nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.INT, primary_key=True)
    project_id = db.Column(db.INT, ForeignKey('projects.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    mobile = db.Column(db.String(14), nullable=True)
    position = db.Column(db.String(100), nullable=False)
    start_duty = db.Column(db.Time, nullable=True)
    end_duty = db.Column(db.Time, nullable=True)
    total_salary = db.Column(mysql.DECIMAL(10,2), nullable=True)
    salary_per_hour = db.Column(mysql.DECIMAL(10,2), nullable=True)
    total_work_hours = db.Column(db.INT, nullable=True)
    per_day_work_hours = db.Column(db.INT, nullable=True)
    break_hours = db.Column(db.INT, nullable=True)
    break_from = db.Column(db.Time, nullable=True)
    break_to = db.Column(db.Time, nullable=True)
    work_schedule = db.Column(db.String(255), nullable=True)
    avatar = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    show_password = db.Column(db.String(150), nullable=False)
    status = db.Column(mysql.TINYINT(1), nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    sections = relationship('Section', backref='user')

class Section(db.Model):
    __tablename__='sections'

    id = db.Column(db.INT, primary_key=True)
    user_id = db.Column(db.INT, ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.Enum('daily','weekly','monthly','urgent'), nullable=False)
    status = db.Column(mysql.TINYINT(1), nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    tasks = relationship('Task', backref='section')



class Task(db.Model):
    __tablename__='tasks'

    id = db.Column(db.INT, primary_key=True)
    section_id = db.Column(db.INT, ForeignKey('sections.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    sub_description = db.Column(db.Text, nullable=True)
    type = db.Column(db.Enum('daily','weekly','monthly','urgent'), nullable=False)
    schedule = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    image_server = db.Column(db.Text, nullable=True)
    video_server = db.Column(db.Text, nullable=True)
    voice_server = db.Column(db.Text, nullable=True)
    file_server = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    video = db.Column(db.String(255), nullable=True)
    voice = db.Column(db.String(255), nullable=True)
    note = db.Column(db.Text, nullable=True)
    complaint = db.Column(db.Text, nullable=True)
    fulfillment = db.Column(db.Enum('awaiting','pending','notcompleted','completed'), nullable=False)
    status = db.Column(mysql.TINYINT(1), nullable=False, default=1)
    priority = db.Column(db.INT, nullable=False)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

class Reminder(db.Model):
    __tablename__='reminder'

    id = db.Column(db.INT, primary_key=True)
    user_id = db.Column(db.INT, nullable=True)
    to_user_id = db.Column(db.INT, nullable=True)
    deadline = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    notifications = relationship('Notification', backref='reminder')

class Training(db.Model):
    __tablename__='trainings'

    id = db.Column(db.INT, primary_key=True)
    project_id = db.Column(db.INT, ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    video = db.Column(db.String(255), nullable=True)
    voice = db.Column(db.String(255), nullable=True)
    status = db.Column(mysql.TINYINT(1), nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
class Rule(db.Model):
    __tablename__='rules'

    id = db.Column(db.INT, primary_key=True)
    project_id = db.Column(db.INT, ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    video = db.Column(db.String(255), nullable=True)
    voice = db.Column(db.String(255), nullable=True)
    status = db.Column(mysql.TINYINT(1), nullable=False, default=1)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

class Notification(db.Model):
    __tablename__='notifications'

    id = db.Column(db.INT, primary_key=True)
    reminder_id = db.Column(db.INT, ForeignKey('reminder.id'), nullable=False)
    user_id = db.Column(db.INT, nullable=False)
    to_user_id = db.Column(db.INT, nullable=True)
    task_id = db.Column(db.INT, nullable=True)
    time = db.Column(mysql.TIME, nullable=True)
    is_last = db.Column(db.INT, nullable=True)
    title = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

class Investigation(db.Model):
    __tablename__='investigations'

    id = db.Column(db.INT, primary_key=True)
    user_id = db.Column(db.INT, nullable=False)
    task_id = db.Column(db.INT, nullable=True)
    status = db.Column(mysql.TINYINT, nullable=True)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

class SalaryMetrics(db.Model):
    __tablename__='salary_metrics'

    id = db.Column(db.INT, primary_key=True)
    user_id = db.Column(db.INT, nullable=False)
    worked_time = db.Column(mysql.TIME, nullable=True)
    salary = db.Column(mysql.DECIMAL(10,2), nullable=True)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

class fcm(db.Model):
    __tablename__='fcm'

    id = db.Column(db.INT, primary_key=True)
    user_id = db.Column(db.INT, nullable=False)
    fcm_token = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP(), server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))