from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import EmailField, SubmitField, PasswordField, BooleanField, StringField, IntegerField, HiddenField, DecimalField, TelField, TextAreaField
from wtforms.validators import DataRequired

class LoginFrom(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Submit')

class AdminForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired()] )
    email = EmailField('Email', validators=[DataRequired()])
    mobile = TelField('Mobile', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only Allowed!')])
    password = PasswordField('Password', validators=[DataRequired()])
    mode = HiddenField('Mode', validators=[DataRequired()])
    adminId = HiddenField('Id')
    submit = SubmitField('add admin')

class ProjectForm(FlaskForm):
    project = StringField('Project',validators=[DataRequired()] )
    name = StringField('Name',validators=[DataRequired()] )
    position = StringField('Position',validators=[DataRequired()] )
    email = EmailField('Email', validators=[DataRequired()])
    mobile = TelField('Mobile', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only Allowed!')])
    password = PasswordField('Password', validators=[DataRequired()])
    mode = HiddenField('Mode', validators=[DataRequired()])
    projectId = HiddenField('Id')
    submit = SubmitField('add project')

class ManagerForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired()] )
    position = StringField('Position',validators=[DataRequired()] )
    email = EmailField('Email', validators=[DataRequired()])
    mobile = TelField('Mobile', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only Allowed!')])
    password = PasswordField('Password', validators=[DataRequired()])
    mode = HiddenField('Mode', validators=[DataRequired()])
    managerId = HiddenField('Id')
    submit = SubmitField('add project')

class UserForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired()] )
    position = StringField('Position',validators=[DataRequired()] )
    email = EmailField('Email', validators=[DataRequired()])
    mobile = TelField('Mobile', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only Allowed!')])
    total_work_hours = IntegerField('Total work hours', validators=[DataRequired()])
    salary_per_hour = DecimalField('Salary per hour', validators=[DataRequired()])
    total_salary = DecimalField('Total salary', validators=[DataRequired()])
    break_hours = IntegerField('Break hours', validators=[DataRequired()])
    duty_starts = StringField('Duty starts', validators=[DataRequired()])
    duty_ends = StringField('Duty ends', validators=[DataRequired()])
    per_day_work_hours = IntegerField('Per day work hours', validators=[DataRequired()])
    break_from = StringField('Break starts', validators=[DataRequired()])
    break_to = StringField('Break ends', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    day_schedule = HiddenField('DaySchedule', validators=[DataRequired()])
    userId = HiddenField('Id')
    submit = SubmitField('Submit')

class SectionForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    mode = HiddenField('Mode', validators=[DataRequired()])
    sectionId = HiddenField('Id')
    submit = SubmitField('Submit')

class TaskForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    sub_description = StringField('Sub Description')
    schedule = HiddenField('Schedule', validators=[DataRequired()])
    start_time = StringField('Start time', validators=[DataRequired()])
    end_time = StringField('End time', validators=[DataRequired()])
    image_file = FileField('Image')
    video_file = FileField('Video')
    voice_file = FileField('Voice')
    file_upload = FileField('File')
    taskId = HiddenField('Id')
    submit = SubmitField('Submit')

class ReminderForm(FlaskForm):
    deadline = HiddenField('deadline', validators=[DataRequired()])
    to_user_id = HiddenField('to_user_id', validators=[DataRequired()])
    submit = SubmitField('Submit')

class TrainingFrom(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only Allowed!')])
    video = FileField('Video', validators=[FileAllowed(['mp4'], 'Videos only Allowed!')])
    voice = FileField('Voice', validators=[FileAllowed(['mp3','wav'], 'Voices only Allowed!')])
    trainingId = HiddenField('Id')
    submit = SubmitField('Submit')

class RuleFrom(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only Allowed!')])
    video = FileField('Video', validators=[FileAllowed(['mp4'], 'Videos only Allowed!')])
    voice = FileField('Voice', validators=[FileAllowed(['mp3','wav'], 'Voices only Allowed!')])
    ruleId = HiddenField('Id')
    submit = SubmitField('Submit')
