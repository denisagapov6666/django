from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_util_js import FlaskUtilJs
from flask_apscheduler import APScheduler
from flask_mail import Mail
import json, pytz

app = Flask(__name__)
app.secret_key = 'ffv21mvajd'
app.config['TIMEZONE'] = pytz.timezone('Asia/Dubai')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://taskerdb:k9hqXp91P@localhost/taskerdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'mail.vishaltechsoft.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'test@vishaltechsoft.com'
app.config['MAIL_PASSWORD'] = 'Xsyv],nQT5O0'

mail = Mail(app)

fujs = FlaskUtilJs(app)

def parse_json(value):
    return json.loads(value)

app.jinja_env.filters['parse_json'] = parse_json

@app.context_processor
def inject_fujs():
    return dict(fujs=fujs)

app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'


from cloudapps.routes import routes
app.register_blueprint(routes)

from cloudapps.api import apis
app.register_blueprint(apis, url_prefix='/api')

from cloudapps import models

with app.app_context():
    db.create_all()

scheduler = APScheduler()

app.config['SCHEDULER_API_ENABLED'] = True

scheduler.init_app(app)

from cloudapps import automation

scheduler.start()