from flask import Blueprint, render_template, flash, request, redirect, url_for, current_app, session, jsonify
from flask_login import login_user, login_required, logout_user, current_user, user_logged_in
from cloudapps.models import Admin, Project, Manager, Section, Task, User, Reminder, Training, Rule, Investigation, SalaryMetrics, Notification
from cloudapps.forms import LoginFrom, AdminForm, ProjectForm, ManagerForm, UserForm, SectionForm, TaskForm, ReminderForm, TrainingFrom, RuleFrom
from cloudapps.app import db, mail
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from sqlalchemy import func, case, distinct
from datetime import datetime
from flask_mail import Message
from weasyprint import HTML
import os, json, sys

routes = Blueprint('routes', __name__)

def get_projects():
    projects = Project.query.all() if session['role']=='superadmin' else Project.query.join(Manager, Manager.project_id==Project.id).filter(Manager.id==session['_user_id']).all()

    return projects

@routes.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))

    form = LoginFrom()
    if form.validate_on_submit():
        username = form.email.data
        password = form.password.data
        remember = form.remember_me.data
        
        manager = Manager.query.filter(Manager.email==username).first()
        if manager and check_password_hash(manager.password, password):
            login_user(manager, fresh=True, remember=remember)
            session['user_id']=manager.id
            session['project_id']=manager.project_id
            session['name']=manager.name
            session['avatar']=manager.avatar
            session['role']=manager.role
            session['mode']='light'
            return redirect(url_for('routes.dashboard'))
        
        user = Admin.query.filter_by(email=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user, fresh=True, remember=remember)
            session['user_id']=user.id
            session['name']=user.name
            session['avatar']=user.avatar
            session['role']='superadmin'
            session['mode']='light'
            return redirect(url_for('routes.dashboard'))
        
        flash('Invalid Username or password', 'error')

    context = {
        'form' : form,
        'title' : 'Login | ProjectManagerPro'
    }

    return render_template('login.html', **context)

@routes.get('/logout')
@login_required
def logout():
    logout_user()
    flash('logout user successfully!', 'logout')
    return redirect(url_for('routes.index'))

@routes.route('/dashboard')
@login_required
def dashboard():
    data = []
    if session['role']=='superadmin':
        projects_count = Project.query.count()
        admins_count = Admin.query.count()
        managers_count = Manager.query.count()
        users_count = User.query.count()
        investigation_count = Investigation.query.count()
        task_count = Task.query.count()
        daily_count = Task.query.filter(Task.type=='daily').count()
        weekly_count = Task.query.filter(Task.type=='weekly').count()
        monthly_count = Task.query.filter(Task.type=='monthly').count()
        urgent_count = Task.query.filter(Task.type=='urgent').count()
        completed_count = Task.query.filter(Task.fulfillment=='completed').count()
        noncompleted_count = Task.query.filter(Task.fulfillment=='notcompleted').count()
        training_count = Training.query.count()
        rules_count = Rule.query.count()

        data.append({'name': 'Total Projects', 'count': projects_count, 'icon': 'uil-briefcase-alt', 'color': 'secondary'})
        data.append({'name': 'Total Admins', 'count': admins_count, 'icon': 'uil-house-user', 'color': 'warning'})
        data.append({'name': 'Total Managers', 'count': managers_count, 'icon': 'uil-house-user', 'color': 'success'})
        data.append({'name': 'Total Users', 'count': users_count, 'icon': 'uil-user-md', 'color': 'info'})
        data.append({'name': 'Total Investigations', 'count': investigation_count, 'icon': 'uil-user-arrows', 'color': 'primary'})
        data.append({'name': 'Total Tasks', 'count': task_count, 'icon': 'uil-schedule', 'color': 'primary'})
        data.append({'name': 'Completed Tasks', 'count': completed_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Not Completed Tasks', 'count': noncompleted_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Daily Tasks', 'count': daily_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Weekly Tasks', 'count': weekly_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Monthly Tasks', 'count': monthly_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Urgent Tasks', 'count': urgent_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Total Training', 'count': training_count, 'icon': 'uil-clock-five', 'color': 'primary'})
        data.append({'name': 'Total Rules', 'count': rules_count, 'icon': 'uil-chart-pie', 'color': 'primary'})

    else : 
        managers_count = Manager.query.filter(Manager.project_id==session['project_id']).count()
        users_count = User.query.filter(User.project_id==session['project_id']).count()
        investigation_count = Investigation.query.join(User, User.id==Investigation.user_id).filter(User.project_id==session['project_id']).count()
        task_count = Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(User.project_id==session['project_id']).count()
        daily_count = Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.type=='daily', User.project_id==session['project_id']).count()
        weekly_count = Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.type=='weekly', User.project_id==session['project_id']).count()
        monthly_count = Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.type=='monthly', User.project_id==session['project_id']).count()
        urgent_count = Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.type=='urgent', User.project_id==session['project_id']).count()
        completed_count = Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.fulfillment=='completed', User.project_id==session['project_id']).count()
        noncompleted_count = Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.type=='notcompleted', User.project_id==session['project_id']).count()
        training_count = Training.query.filter(Training.project_id==session['project_id']).count()
        rules_count = Rule.query.filter(Rule.project_id==session['project_id']).count()

        data.append({'name': 'Total Managers', 'count': managers_count, 'icon': 'uil-house-user', 'color': 'primary'})
        data.append({'name': 'Total Users', 'count': users_count, 'icon': 'uil-user-md', 'color': 'primary'})
        data.append({'name': 'Total Investigations', 'count': investigation_count, 'icon': 'uil-user-arrows', 'color': 'primary'})
        data.append({'name': 'Total Tasks', 'count': task_count, 'icon': 'uil-schedule', 'color': 'primary'})
        data.append({'name': 'Completed Tasks', 'count': completed_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Not Completed Tasks', 'count': noncompleted_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Daily Tasks', 'count': daily_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Weekly Tasks', 'count': weekly_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Monthly Tasks', 'count': monthly_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Urgent Tasks', 'count': urgent_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        data.append({'name': 'Total Training', 'count': training_count, 'icon': 'uil-clock-five', 'color': 'primary'})
        data.append({'name': 'Total Rules', 'count': rules_count, 'icon': 'uil-chart-pie', 'color': 'primary'})
        

    context = {
        'title':'Dashboard | ProjectManagerPro',
        'projects': get_projects(),
        'data': data
    }
    return render_template('index.html', **context)

@routes.route('/admin-list', methods=['GET', 'POST'])
@login_required
def admin_list():
    if (session['role']!='superadmin'):
        return redirect(url_for('routes.dashboard'))

    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    form = AdminForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        mobile = form.mobile.data
        image = form.image.data
        password = form.password.data
        mode = form.mode.data

        dir = ''
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)

        if mode=='add':
            admin = Admin(
                    name=name,
                    email=email,
                    mobile=mobile,
                    avatar=f'uploads/images/{filename}' if image else '',
                    password=generate_password_hash(password, method='pbkdf2'),
                    show_password=password,
                    status=1
                )
            
            db.session.add(admin)
            db.session.commit()
            
            flash('Admin created successfully!', 'success')

        else: 
            id = form.adminId.data
            admin = Admin.query.filter_by(id=id).first_or_404()
            admin.name=name
            admin.mobile=mobile
            if admin.email != email:
                admin.email=email
            admin.password=generate_password_hash(password, method='pbkdf2')
            if image:
                if (admin.avatar!=''):
                    os.remove(os.path.dirname(__file__)+url_for('static', filename=admin.avatar))

                admin.avatar=f'uploads/images/{filename}' if image else '',
                
                if session['user_id']==int(id):
                    session['avatar']=f'uploads/images/{filename}'
            admin.show_password=password

            db.session.commit()

            

    data = Admin.query.order_by(Admin.id.desc()).paginate(page=int(page), per_page=int(per_page), error_out=False)

    context = {'title':'Admin List | ProjectManagerPro',
               'projects': get_projects(),
               'form': form,
               'data': data}
    

    return render_template('admin-list.html', **context)

@routes.get('/admin-details')
@login_required
def admin_detail():
    if (session['role']!='superadmin'):
        return redirect(url_for('routes.dashboard'))
    
    id = request.args.get('id')

    admin = Admin.query.filter_by(id=id).first_or_404()

    if admin:
        data = {'name': admin.name, 
                'mobile': admin.mobile, 
                'email': admin.email, 
                'password': admin.show_password,
                'avatar': admin.avatar}

    return jsonify(data)

@routes.get('/admin-delete')
@login_required
def admin_delete():
    if (session['role']!='superadmin'):
        return redirect(url_for('routes.dashboard'))

    id = request.args.get('id')

    admin=Admin.query.filter_by(id=id).first_or_404()
    if admin:
        db.session.delete(admin)
        db.session.commit()

    return jsonify('success')

@routes.route('/projects-list', methods=['GET', 'POST'])
@login_required
def project_list():
    if (session['role']!='superadmin'):
        return redirect(url_for('routes.dashboard'))

    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    form = ProjectForm()

    if form.validate_on_submit():
        project_name = form.project.data
        name = form.name.data
        email = form.email.data
        mobile = form.mobile.data
        image = form.image.data
        position = form.position.data
        password = form.password.data
        mode = form.mode.data

        dir = ''
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)

        if mode == 'add':
            project = Project(name=project_name, status=1)
            db.session.add(project)
            db.session.flush()

            manager = Manager(
                name=name,
                project_id=project.id,
                email=email,
                role='supermanager',
                position=position,
                mobile=mobile,
                avatar=f'uploads/images/{filename}',
                password=generate_password_hash(password, method='pbkdf2'),
                show_password=password,
                status=1
            )

            db.session.add(manager)
            db.session.commit()

            flash('Project created successfully!', 'success')
            

        else:
            id = form.projectId.data
            project = Project.query.filter_by(id=id).first_or_404()
            project.name = project_name

            manager = Manager.query.filter_by(project_id=id, role='supermanager').first_or_404()
            manager.name = name
            manager.mobile = mobile
            if manager.email!=email:
                manager.email = email
            manager.position = position
            manager.password=generate_password_hash(password, method='pbkdf2')
            if image:
                if (manager.avatar!=''):
                    os.remove(os.path.dirname(__file__)+url_for('static', filename=manager.avatar))

                manager.avatar=f'uploads/images/{filename}'
                
                if session['user_id']==int(id):
                    session['avatar']=f'uploads/images/{filename}'
            manager.show_password=password

            db.session.commit()


    data = (db.session.query(Project, Manager).join(Manager, Project.id==Manager.project_id).filter(Manager.role=='supermanager').order_by(Project.id.desc()).paginate(page=int(page), per_page=int(per_page), error_out=False))

    project_completion = (
        db.session.query(
            Project.id.label('pId'),
            func.sum(case((Task.fulfillment == 'completed', 1), else_=0)).label('completed_tasks'),
            func.sum(case((Task.fulfillment.in_(['pending', 'completed', 'notcompleted']), 1), else_=0)).label('total_tasks'),
            func.count(distinct(Manager.id)).label('managers_count'),
            func.count(distinct(User.id)).label('user_count'),
            func.count(distinct(Investigation.id)).label('investigation_count')
        )
        .join(User, User.project_id == Project.id)
        .join(Section, Section.user_id == User.id)
        .join(Task, Task.section_id == Section.id)
        .join(Manager, Manager.project_id == Project.id)
        .join(Investigation, Investigation.user_id == User.id)
        .group_by(Project.id)
        .all()
    )

    for project in data:
        for progress in project_completion:
            if progress.pId == project.Project.id:
                project.Project.completed_tasks = progress.completed_tasks
                project.Project.total_tasks = progress.total_tasks
                percent_completion=progress.completed_tasks * 100 / progress.total_tasks
                project.Project.percentage = "{:.2f}".format(percent_completion)
                project.Project.manager_count = progress.managers_count
                project.Project.users_count = progress.user_count
                project.Project.investigation_count = progress.investigation_count


    context = {'title':'Project List | ProjectManagerPro',
               'projects': get_projects(),
               'data': data,
               'form': form,
               'records': {'managers': 20, 'users': 10, 'investigations': 30}}
    return render_template('projects-list.html', **context)

@routes.get('/project-details')
@login_required
def project_detail():
    if (session['role']!='superadmin'):
        return redirect(url_for('routes.dashboard'))

    id = request.args.get('id')

    project = (
            Project.query
            .join(Manager, Manager.project_id == Project.id)
            .filter(Project.id == id, Manager.role == 'supermanager')
            .options(joinedload(Project.managers))
            .first_or_404()
        )
    
    manager = project.managers[0]
    
    if project:
        data = {'project': project.name, 
                'name': manager.name, 
                'email': manager.email, 
                'password': manager.show_password,
                'mobile': manager.mobile,
                'position': manager.position,
                'avatar': manager.avatar}

    return jsonify(data)

@routes.get('/project-delete')
@login_required
def project_delete():
    if (session['role']!='superadmin'):
        return redirect(url_for('routes.dashboard'))

    id = request.args.get('id')

    project=Project.query.filter_by(id=id).first_or_404()
    manager=Manager.query.filter_by(project_id=id).all()

    if project:
        db.session.delete(project)
    if manager:
        for item in manager:
            db.session.delete(item)

    db.session.commit()

    return jsonify('success')

@login_required
def checkManager(projectId):
    if session['role'] != 'superadmin':
        manager_id = session['user_id']
        manager_exists = Manager.query.filter(Manager.project_id==projectId, Manager.id==manager_id).first() is not None
        if manager_exists:
            session['current_project_open']=projectId
            return True
        return False
    session['current_project_open']=projectId
        
    return True

@routes.route('/manager-list/<int:projectid>', methods=['GET', 'POST'])
@login_required
def manager_list(projectid):
    if (session['role']=='manager'):
        return redirect(url_for('routes.dashboard'))
    
    if not checkManager(projectid):
        return redirect(url_for('routes.dashboard'))

    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    form = ManagerForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        mobile = form.mobile.data
        image = form.image.data
        position = form.position.data
        password = form.password.data
        mode = form.mode.data

        dir = ''
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)

        if mode == 'add':
            manager = Manager(
                name=name,
                project_id=projectid,
                email=email,
                role='manager',
                position=position,
                mobile=mobile,
                avatar=f'uploads/images/{filename}',
                password=generate_password_hash(password, method='pbkdf2'),
                show_password=password,
                status=1
            )

            db.session.add(manager)
            db.session.commit()

            flash('Manager created successfully!', 'success')
            

        else:
            id = form.managerId.data

            manager = Manager.query.filter_by(id=id, role='manager').first_or_404()
            manager.name = name
            manager.mobile = mobile
            if manager.email!=email:
                manager.email = email
            manager.position = position
            manager.password=generate_password_hash(password, method='pbkdf2')
            if image:
                if (manager.avatar!=''):
                    os.remove(os.path.dirname(__file__)+url_for('static', filename=manager.avatar))

                manager.avatar=f'uploads/images/{filename}'
                
                if session['user_id']==int(id):
                    session['avatar']=f'uploads/images/{filename}'
            manager.show_password=password

            db.session.commit()


    data = Manager.query.filter(Manager.project_id==projectid).order_by(Manager.id.desc()).paginate(page=int(page), per_page=int(per_page), error_out=False)
    
    context = {'title':'Manager List | ProjectManagerPro',
               'projects': get_projects(),
               'data': data,
               'form': form }
    return render_template('manager-list.html', **context)

@routes.get('/manager-details')
@login_required
def manager_detail():
    
    id = request.args.get('id')

    manager = Manager.query.filter_by(id=id).first_or_404()

    if manager:
        data = {'name': manager.name, 
                'mobile': manager.mobile, 
                'email': manager.email, 
                'position': manager.position,
                'password': manager.show_password,
                'avatar': manager.avatar}

    return jsonify(data)

@routes.get('/manager-delete')
@login_required
def manager_delete():

    id = request.args.get('id')

    manager=Manager.query.filter_by(id=id).first_or_404()
    if manager:
        db.session.delete(manager)
        db.session.commit()

    return jsonify('success')


@routes.route('/user-list/<int:projectId>', methods=['GET', 'POST'])
@login_required
def user_list(projectId):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)


    data = User.query.filter(User.project_id==projectId).order_by(User.id.desc()).paginate(page=int(page), per_page=int(per_page), error_out=False)
    
    context = {'title':'Users List | ProjectManagerPro',
               'projects': get_projects(),
               'data': data, 
               'projectId': projectId}
    return render_template('users-list.html', **context)

@routes.route('/add-user/<int:projectId>', methods=['GET', 'POST'])
@login_required
def add_user(projectId):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    
    form = UserForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        mobile = form.mobile.data
        position = form.position.data
        password = form.password.data
        total_work_hours = form.total_work_hours.data
        salary_per_hour = form.salary_per_hour.data
        per_day_work_hours = form.per_day_work_hours.data
        duty_starts = form.duty_starts.data
        duty_ends = form.duty_ends.data
        total_salary = form.total_salary.data
        break_hours = form.break_hours.data
        break_from = form.break_from.data
        break_to = form.break_to.data
        image = form.image.data
        daysJson = form.day_schedule.data

        dir = ''
        
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)
        

        user = User(name=name, 
                    email=email, 
                    mobile=mobile,
                    position=position,
                    password=generate_password_hash(password, method="pbkdf2"),
                    show_password=password,
                    total_work_hours=total_work_hours,
                    salary_per_hour=salary_per_hour,
                    start_duty=duty_starts,
                    end_duty=duty_ends,
                    total_salary=total_salary,
                    per_day_work_hours=per_day_work_hours,
                    break_hours=break_hours,
                    break_from=break_from,
                    break_to=break_to,
                    avatar=f'uploads/images/{filename}' if image else '',
                    project_id=projectId,
                    work_schedule=daysJson)

        db.session.add(user)
        db.session.commit()

        flash('User created successfully!', 'success')

        return redirect(url_for('routes.user_list', projectId=projectId))

    context = {
        'title': 'Add user | ProjectManagerPro',
        'projects': get_projects(),
        'form': form,
        'current_time': datetime.now().strftime('%H:%M')
    }

    return render_template('add-user.html', **context)

@routes.route('/edit-user/<int:projectId>/<int:userId>', methods=['GET', 'POST'])
@login_required
def edit_user(projectId, userId):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    
    user = User.query.filter(User.project_id==projectId, User.id==userId).first_or_404()

    form = UserForm()

    if form.validate_on_submit():
        id = form.userId.data
        name = form.name.data
        email = form.email.data
        mobile = form.mobile.data
        position = form.position.data
        password = form.password.data
        total_work_hours = form.total_work_hours.data
        salary_per_hour = form.salary_per_hour.data
        duty_starts = form.duty_starts.data
        duty_ends = form.duty_ends.data
        total_salary = form.total_salary.data
        per_day_work_hours = form.per_day_work_hours.data
        break_hours = form.break_hours.data
        break_from = form.break_from.data
        break_to = form.break_to.data
        image = form.image.data
        daysJson = form.day_schedule.data

        dir = ''
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)

        user = User.query.filter(User.project_id==projectId, User.id==id).first_or_404()

        user.name=name
        user.email=email
        user.mobile=mobile
        user.position=position
        user.password=generate_password_hash(password, method="pbkdf2")
        user.show_password=password
        user.total_work_hours=total_work_hours
        user.salary_per_hour=salary_per_hour
        user.per_day_work_hours=per_day_work_hours
        user.start_duty=duty_starts
        user.end_duty=duty_ends
        user.total_salary=total_salary
        user.break_hours=break_hours
        user.break_from=break_from
        user.break_to=break_to
        user.work_schedule = daysJson

        if image:
            if (user.avatar!=''):
                os.remove(os.path.dirname(__file__)+url_for('static', filename=user.avatar))

            user.avatar=f'uploads/images/{filename}'
                
        db.session.commit()

        flash('User updated successfully!', 'success')

        return redirect(url_for('routes.user_list', projectId=projectId))


    context = {
        'title': 'Edit user | ProjectManagerPro',
        'type': 'daily',
        'projects': get_projects(),
        'form': form,
        'user': user
    }
    return render_template('edit-user.html', **context)

@routes.get('/user-delete')
@login_required
def user_delete():
    id = request.args.get('id')
    projectId = request.args.get('projectId')

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    user=User.query.filter_by(id=id).first_or_404()
    if user:
        db.session.delete(user)
        db.session.commit()

    return jsonify('success')

@routes.route('/<string:type>-checklist/<int:projectId>/<int:userId>', methods=['GET','POST'])
@login_required
def sections_list(type, projectId, userId):
    if type not in ['daily', 'weekly', 'monthly', 'urgent'] or not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    
    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    form = SectionForm()

    if form.validate_on_submit():
        id = form.sectionId.data
        name = form.name.data
        mode = form.mode.data

        if mode == 'add':
            section = Section(name=name,type=type,user_id=userId)
            
            db.session.add(section)
            db.session.commit()

            flash('Section created successfully!', 'success')
        elif mode == 'edit':
            section = Section.query.join(User, User.id==Section.user_id).filter(Section.id==id, Section.user_id==userId, User.project_id==projectId).first_or_404()
            section.name = name
            
            db.session.commit()

            flash('Section updated successfully!', 'success')

    data = (
        db.session.query(
            Section,
            func.count(Task.id).label('task_count')
        )
        .join(User, User.id == Section.user_id)
        .outerjoin(Task, Task.section_id == Section.id)
        .filter(Section.type == type, User.project_id == projectId, Section.user_id==userId)
        .group_by(Section)
        .order_by(Section.id.desc())
        .paginate(page=int(page), per_page=int(per_page), error_out=False)
        )

    context={'title': f'{type.capitalize()} Checklist | ProjectManagerPro',
            'type': type,
             'data': data,
             'projects': get_projects(),
             'projectId': projectId,
             'userId': userId,
             'form': form}
    return render_template('sections-list.html',**context)

@routes.get('/section-detail')
@login_required
def section_detail():
    id = request.args.get('id')

    section = Section.query.filter_by(id=id).first_or_404()

    if section:
        data = {'name': section.name}

    return jsonify(data)

@routes.get('/section-delete')
@login_required
def section_delete():
    id = request.args.get('id')
    projectId = request.args.get('projectId')

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    section=Section.query.filter_by(id=id).first_or_404()
    if section:
        db.session.delete(section)
        db.session.commit()

    return jsonify('success')


@routes.route('/tasks-list/<int:projectId>/<int:sectionId>')
@login_required
def checklist_tasks(projectId, sectionId):
    fulfillment = request.args.get('fulfillment', 'all')

    if fulfillment not in ['all', 'awaiting', 'pending', 'completed', 'notcompleted'] or not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
        
    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    name = (Section.query.filter_by(id=sectionId).first()).name
    type = (Section.query.filter_by(id=sectionId).first()).type
    userId = (Section.query.filter_by(id=sectionId).first()).user_id

    if fulfillment=="all":
        data = (
            db.session.query(
                User,
                Task
            )
            .join(Section, Section.id==Task.section_id)
            .join(User, User.id==Section.user_id)
            .filter(Task.section_id==sectionId)
            .group_by(Task.id)
            .order_by(Task.priority.desc())
            .paginate(page=int(page), per_page=int(per_page), error_out=False)
            )
    elif fulfillment=="pending":
        data = (
            db.session.query(
                User,
                Task
            )
            .join(Section, Section.id==Task.section_id)
            .join(User, User.id==Section.user_id)
            .filter(Task.section_id==sectionId, Task.fulfillment.in_(['awaiting','pending']))
            .group_by(Task.id)
            .order_by(Task.priority.desc())
            .paginate(page=int(page), per_page=int(per_page), error_out=False)
            )
    else:
        data = (
            db.session.query(
                User,
                Task
            )
            .join(Section, Section.id==Task.section_id)
            .join(User, User.id==Section.user_id)
            .filter(Task.section_id==sectionId, Task.fulfillment == fulfillment)
            .group_by(Task.id)
            .order_by(Task.priority.desc())
            .paginate(page=int(page), per_page=int(per_page), error_out=False)
            )
    
    #Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.section_id==sectionId).order_by(Task.id.desc()).paginate(page=int(page), per_page=int(per_page), error_out=False)

    context={'title': 'Tasks list | ProjectManagerPro',
            'type': type,
             'data': data,
             'projects': get_projects(),
             'projectId': projectId,
             'userId': userId,
             'sectionId': sectionId,
             'fulfillment': fulfillment,
             'name': name}
    
    return render_template('checklist-tasks.html',**context)


@routes.route('/edit-task/<int:projectId>/<int:taskId>', defaults={'root': None}, methods=['GET','POST'])
@routes.route('/edit-task/<int:projectId>/<int:taskId>/<string:root>', methods=['GET','POST'])
@login_required
def edit_task(projectId, taskId, root):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    
    task = Task.query.filter_by(id=taskId).first_or_404()
    type = task.type
    
    if (task.sub_description != None):
    	sub_description = json.loads(task.sub_description)
    else: 
    	sub_description = []

    form = TaskForm()

    if form.validate_on_submit():
        id = form.taskId.data
        name = form.name.data
        description = form.description.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        daysJson = form.schedule.data
        subDescJson = form.sub_description.data
        
        
        image_file = form.image_file.data
        video_file = form.video_file.data
        voice_file = form.voice_file.data
        file_upload = form.file_upload.data
        
        

        task = Task.query.filter_by(id=id).first_or_404()

        task.name=name
        task.description=description
        task.sub_description=subDescJson
        task.start_time=start_time
        task.end_time=end_time
        task.schedule=daysJson
        
        dir = ''
        if image_file:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image_file.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image_file.save(dir)
            
            task.image_server=f'uploads/images/{filename}'

        if video_file:
            filename1 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(video_file.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'videos', filename1)
            video_file.save(dir)
            
            task.video_server=f'uploads/videos/{filename1}'
        
        if voice_file:
            filename2 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(voice_file.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'voices', filename2)
            voice_file.save(dir)
            
            task.voice_server=f'uploads/voices/{filename2}'
            
        if file_upload:
            filename3 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(file_upload.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'files', filename3)
            file_upload.save(dir)
            
            task.file_server=f'uploads/files/{filename3}'
     

        db.session.commit()

        sectionId=(Section.query.join(User, User.id==Section.user_id).filter(User.project_id==projectId, Section.id==task.section_id).first()).id

        flash('Task updated successfully!', 'success')

        if root=="main":
            return redirect(url_for('routes.tasks_list', projectId=projectId, type=type))
        else: 
            return redirect(url_for('routes.checklist_tasks', projectId=projectId, sectionId=sectionId))


    context = {
        'title': 'Edit task | ProjectManagerPro',
        'type': type,
        'projects': get_projects(),
        'form': form,
        'task': task,
        'sub_description':sub_description,
    }
    return render_template('edit-task.html', **context)

@routes.route('/add-task/<int:projectId>/<int:sectionId>', methods=['GET', 'POST'])
@login_required
def add_task(projectId, sectionId):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    
    section = Section.query.filter_by(id=sectionId).first()
    type = section.type
    
    form = TaskForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        daysJson = form.schedule.data
        subDescJson = form.sub_description.data
        
        image_file = form.image_file.data
        video_file = form.video_file.data
        voice_file = form.voice_file.data
        file_upload = form.file_upload.data
        
        dir = ''
        
        filename1 = ''
        filename2 = ''
        filename3 = ''
        filename4 = ''
        
        if image_file:
            filename1 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image_file.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename1)
            image_file.save(dir)

        if video_file:
            filename2 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(video_file.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'videos', filename2)
            video_file.save(dir)
        
        if voice_file:
            filename3 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(voice_file.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'voices', filename3)
            voice_file.save(dir)
            
        if file_upload:
            filename4 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(file_upload.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'files', filename4)
            file_upload.save(dir)

        is_task_exists=Task.query.first() is not None
        if is_task_exists:
            priority = db.session.query(func.max(Task.priority)).scalar() + 1
        else:
            priority = 1

        task = Task(name=name, 
                    description=description,
                    sub_description=subDescJson,
                    start_time=start_time,
                    end_time=end_time,
                    schedule=daysJson,
                    section_id=section.id,
                    type=type,
                    fulfillment='awaiting',
                    status=1,
                    image_server=f'uploads/images/{filename1}' if filename1 else '',
                    video_server=f'uploads/videos/{filename2}' if filename2 else '',
                    voice_server=f'uploads/voices/{filename3}' if filename3 else '',
                    file_server=f'uploads/files/{filename4}' if filename4 else '',
                    priority=priority)

        db.session.add(task)
        db.session.commit()

        flash('Task created successfully!', 'success')

        return redirect(url_for('routes.checklist_tasks', projectId=projectId, sectionId=sectionId))

    context = {
        'title': 'Add task | ProjectManagerPro',
        'projects': get_projects(),
        'form': form,
        'current_time': datetime.now().strftime('%H:%M'),
        'type': type
    }

    return render_template('add-task.html', **context)


@routes.get('/delete-task')
@login_required
def delete_task():
    id = request.args.get('id')
    projectId = request.args.get('projectId')

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    task=Task.query.filter_by(id=id).first_or_404()
    if task:
        db.session.delete(task)
        db.session.commit()

    return jsonify('success')

@routes.get('/task-up')
@login_required
def task_up():
    id = request.args.get('id')

    task=Task.query.filter_by(id=id).first_or_404()
    if task:
        next_task = Task.query.filter(Task.priority > task.priority).first()

        if next_task:
            next_task_priority = next_task.priority

            next_task.priority = task.priority

            task.priority = next_task_priority

            db.session.commit()
        else:
            return jsonify("no need")

    return jsonify('success')

@routes.get('/task-down')
@login_required
def task_down():
    id = request.args.get('id')

    task=Task.query.filter_by(id=id).first_or_404()
    if task:
        previous_task = Task.query.filter(Task.priority < task.priority).first()

        if previous_task:
            previous_task_priority = previous_task.priority

            previous_task.priority = task.priority
            db.session.add(previous_task)

            task.priority = previous_task_priority

            db.session.commit()
        else:
            return jsonify("no need")

    return jsonify('success')

@routes.get('/task-status')
@login_required
def task_status():
    id = request.args.get('id')
    status = request.args.get('status')

    task=Task.query.filter_by(id=id).first_or_404()

    if task:
        task.status = 1 if status=="true" else 0

        db.session.commit()

    return jsonify('success')

@routes.route('/<string:type>-tasks/<int:projectId>')
@login_required
def tasks_list(projectId, type):
    fulfillment = request.args.get('fulfillment', 'all')

    if fulfillment not in ['all', 'awaiting', 'pending', 'completed', 'notcompleted'] or type not in ['daily','weekly','monthly','urgent'] or not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
        
    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    if fulfillment=="all":
        data = (
            db.session.query(
                User,
                Task
            )
            .join(Section, Section.id==Task.section_id)
            .join(User, User.id==Section.user_id)
            .filter(User.project_id==projectId, Task.type==type)
            .group_by(Task.id)
            .order_by(Task.priority.desc())
            .paginate(page=int(page), per_page=int(per_page), error_out=False)
            )
    elif fulfillment=="pending":
        data = (
            db.session.query(
                User,
                Task
            )
            .join(Section, Section.id==Task.section_id)
            .join(User, User.id==Section.user_id)
            .filter(User.project_id==projectId, Task.type==type, Task.fulfillment.in_(['awaiting','pending']))
            .group_by(Task.id)
            .order_by(Task.priority.desc())
            .paginate(page=int(page), per_page=int(per_page), error_out=False)
            )
    else:
        data = (
            db.session.query(
                User,
                Task
            )
            .join(Section, Section.id==Task.section_id)
            .join(User, User.id==Section.user_id)
            .filter(User.project_id==projectId, Task.type==type, Task.fulfillment==fulfillment)
            .group_by(Task.id)
            .order_by(Task.priority.desc())
            .paginate(page=int(page), per_page=int(per_page), error_out=False)
            )
    
    #Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.section_id==sectionId).order_by(Task.id.desc()).paginate(page=int(page), per_page=int(per_page), error_out=False)

    context={'title': 'Tasks list | ProjectManagerPro',
            'type': type,
             'data': data,
             'projects': get_projects(),
             'projectId': projectId,
             'fulfillment': fulfillment}
    
    return render_template('tasks-list.html',**context)

@routes.route('/reminders/<int:userId>', methods=['GET', 'POST'])
@login_required
def reminders(userId):

    project_id = (User.query.filter_by(id=userId).first()).project_id

    if not checkManager(project_id):
        return redirect(url_for('routes.dashboard'))

    form = ReminderForm()

    if form.validate_on_submit():
        to_user_id = form.to_user_id.data
        deadline = form.deadline.data

        reminder = Reminder(user_id=userId,to_user_id=to_user_id,deadline=deadline)
            
        db.session.add(reminder)
        db.session.commit()

        flash('Reminder created successfully!', 'success')
        return redirect(url_for('routes.reminders'))

    reminders = (
                db.session.query(User.name.label('to_user_name'), Reminder)
                .join(User, User.id == Reminder.to_user_id)
                .filter(Reminder.user_id==userId)
                .group_by(Reminder.id)
                .order_by(Reminder.id.asc())
                .all()
            )

    reminder_data = json.dumps([{'id': reminder.Reminder.id, 'to_user_name': reminder.to_user_name, 'deadline': reminder.Reminder.deadline} for reminder in reminders])

    users = User.query.filter(User.project_id==project_id, User.id!=userId).all()

    user_data = json.dumps([{'id': user.id, 'name': user.name} for user in users])

    context={'title': 'Reminders | ProjectManagerPro',
             'reminder_data': reminder_data,
             'projects': get_projects(),
             'user_data': user_data,
             'userId': userId,
             'form': form,
             'projectId': project_id}
    return render_template('reminders.html',**context)

@routes.get('/reminder-delete')
@login_required
def reminder_delete():
    id = request.args.get('id')
    projectId = request.args.get('projectId')

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    reminder = Reminder.query.filter_by(id=id).first()
    notifications = Notification.query.filter_by(reminder_id=reminder.id).all()

    if notifications:
        for notification in notifications:
            db.session.delete(notification)

    if reminder:
        db.session.delete(reminder)
        db.session.commit()

    return jsonify('success')


@routes.get('/taskers-list/<int:projectId>')
@login_required
def tasker_list(projectId):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)
    

    data = (
        db.session.query(
            User.id,
            User.name.label('name'),
            User.avatar,
            User.mobile,
            User.work_schedule,
            func.coalesce(
                func.count(
                    case((Task.fulfillment == 'notcompleted', Task.id))
                ),
                0
            ).label('notcompletedCount'),
            func.coalesce(
                func.count(
                    case((Task.fulfillment == 'completed', Task.id))
                ),
                0
            ).label('completedCount')
        )
        .outerjoin(Section, Section.user_id == User.id)
        .outerjoin(Task, Task.section_id == Section.id)
        .filter(User.project_id == projectId)
        .group_by(User.id)
        .order_by(User.id.desc())
        .paginate(page=int(page), per_page=int(per_page), error_out=False)
    )
    
    context = {'title':'Taskers List | ProjectManagerPro',
               'projects': get_projects(),
               'data': data }
    return render_template('taskers-list.html', **context)

@routes.get('/tasker-page/<int:userId>')
@login_required
def tasker_page(userId):
    project_id = (User.query.filter_by(id=userId).first()).project_id

    if not checkManager(project_id):
        return redirect(url_for('routes.dashboard'))
    
    context={'title': 'Reminders | ProjectManagerPro',
             'projects': get_projects(),
             'projectId': project_id,
             'userId': userId}
    return render_template('tasker-page.html',**context)

@routes.route('/training-list/<int:projectId>')
@login_required
def training_list(projectId):

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
        
    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    data = (
        Training.query
        .filter_by(project_id=projectId)
        .paginate(page=int(page), per_page=int(per_page), error_out=False)
        )
        
    context={'title': 'Training list | ProjectManagerPro',
             'data': data,
             'projects': get_projects(),
             'projectId': projectId}
    
    return render_template('training-list.html',**context)

@routes.route('/edit-training/<int:trainingId>', methods=['GET','POST'])
@login_required
def edit_training(trainingId):
    projectId = (Training.query.filter_by(id=trainingId).first_or_404()).project_id

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    

    form = TrainingFrom()

    if form.validate_on_submit():
        id = form.trainingId.data
        name = form.name.data
        description = form.description.data
        image = form.image.data
        video = form.video.data
        voice = form.voice.data

        training = Training.query.filter_by(id=id).first_or_404()

        training.name=name
        training.description=description
        

        dir = ''
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)
            
        if video:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(video.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'videos', filename)
            video.save(dir)

        if voice:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(voice.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'voices', filename)
            voice.save(dir)

        if image:
            if (training.image!=''):
                os.remove(os.path.dirname(__file__)+url_for('static', filename=training.image))

            training.image=f'uploads/images/{filename}'

        if video:
            if (training.video!=''):
                os.remove(os.path.dirname(__file__)+url_for('static', filename=training.video))

            training.video=f'uploads/videos/{filename}'

        if voice:
            if (training.voice!=''):
                os.remove(os.path.dirname(__file__)+url_for('static', filename=training.voice))

            training.voice=f'uploads/voices/{filename}'

        db.session.commit()

        flash('Training updated successfully!', 'success')

        return redirect(url_for('routes.training_list', projectId=projectId))
    
    data = Training.query.filter_by(id=trainingId).first_or_404()

    context = {
        'title': 'Edit training | ProjectManagerPro',
        'projects': get_projects(),
        'form': form,
        'training': data
    }
    return render_template('edit-training.html', **context)

@routes.route('/add-training/<int:projectId>', methods=['GET', 'POST'])
@login_required
def add_training(projectId):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    
    form = TrainingFrom()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        image = form.image.data
        video = form.video.data
        voice = form.voice.data

        dir = ''
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)

        if video:
            filename1 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(video.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'videos', filename1)
            video.save(dir)
        
        if voice:
            filename2 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(voice.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'voices', filename2)
            voice.save(dir)


        training = Training(name=name, 
                    description=description, 
                    image=f'uploads/images/{filename}',
                    video=f'uploads/videos/{filename1}',
                    voice=f'uploads/voices/{filename2}',
                    status=1,
                    project_id=projectId)

        db.session.add(training)
        db.session.commit()

        flash('Training created successfully!', 'success')

        return redirect(url_for('routes.training_list', projectId=projectId))

    context = {
        'title': 'Add training | ProjectManagerPro',
        'projects': get_projects(),
        'form': form,
        'current_time': datetime.now().strftime('%H:%M'),
        'type': type
    }

    return render_template('add-training.html', **context)

@routes.get('/training-status')
@login_required
def training_status():
    id = request.args.get('id')
    status = request.args.get('status')

    training=Training.query.filter_by(id=id).first_or_404()

    if training:
        training.status = 1 if status=="true" else 0

        db.session.commit()

    return jsonify('success')

@routes.get('/delete-training')
@login_required
def delete_training():
    id = request.args.get('id')
    projectId = request.args.get('projectId')

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    training=Training.query.filter_by(id=id).first_or_404()
    if training:
        db.session.delete(training)
        db.session.commit()

    return jsonify('success')

@routes.route('/rules-list/<int:projectId>')
@login_required
def rules_list(projectId):

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
        
    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    data = (
        Rule.query
        .filter_by(project_id=projectId)
        .paginate(page=int(page), per_page=int(per_page), error_out=False)
        )
        
    context={'title': 'Rules list | ProjectManagerPro',
             'data': data,
             'projects': get_projects(),
             'projectId': projectId}
    
    return render_template('rules-list.html',**context)

@routes.route('/edit-rule/<int:ruleId>', methods=['GET','POST'])
@login_required
def edit_rule(ruleId):
    projectId = (Rule.query.filter_by(id=ruleId).first_or_404()).project_id

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    

    form = RuleFrom()

    if form.validate_on_submit():
        id = form.ruleId.data
        name = form.name.data
        description = form.description.data
        image = form.image.data
        video = form.video.data
        voice = form.voice.data

        rule = Rule.query.filter_by(id=id).first_or_404()

        rule.name=name
        rule.description=description
        

        dir = ''
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)
            
        if video:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(video.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'videos', filename)
            video.save(dir)

        if voice:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(voice.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'voices', filename)
            voice.save(dir)

        if image:
            if (rule.image!=''):
                os.remove(os.path.dirname(__file__)+url_for('static', filename=rule.image))

            rule.image=f'uploads/images/{filename}'

        if video:
            if (rule.video!=''):
                os.remove(os.path.dirname(__file__)+url_for('static', filename=rule.video))

            rule.video=f'uploads/videos/{filename}'

        if voice:
            if (rule.voice!=''):
                os.remove(os.path.dirname(__file__)+url_for('static', filename=rule.voice))

            rule.voice=f'uploads/voices/{filename}'

        db.session.commit()

        flash('Rule updated successfully!', 'success')

        return redirect(url_for('routes.rules_list', projectId=projectId))
    
    data = Rule.query.filter_by(id=ruleId).first_or_404()

    context = {
        'title': 'Edit rule | ProjectManagerPro',
        'projects': get_projects(),
        'form': form,
        'rule': data
    }
    return render_template('edit-rule.html', **context)

@routes.route('/add-rule/<int:projectId>', methods=['GET', 'POST'])
@login_required
def add_rule(projectId):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
    
    form = RuleFrom()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        image = form.image.data
        video = form.video.data
        voice = form.voice.data

        dir = ''
        if image:
            filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image.save(dir)

        if video:
            filename1 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(video.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'videos', filename1)
            video.save(dir)
        
        if voice:
            filename2 = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(voice.filename)}'
            dir = os.path.join(current_app.root_path, 'static', 'uploads', 'voices', filename2)
            voice.save(dir)


        rule = Rule(name=name, 
                    description=description, 
                    image=f'uploads/images/{filename}',
                    video=f'uploads/videos/{filename1}',
                    voice=f'uploads/voices/{filename2}',
                    status=1,
                    project_id=projectId)

        db.session.add(rule)
        db.session.commit()

        flash('Rule created successfully!', 'success')

        return redirect(url_for('routes.rules_list', projectId=projectId))

    context = {
        'title': 'Add rule | ProjectManagerPro',
        'projects': get_projects(),
        'form': form,
        'current_time': datetime.now().strftime('%H:%M'),
        'type': type
    }

    return render_template('add-rule.html', **context)

@routes.get('/rule-status')
@login_required
def rule_status():
    id = request.args.get('id')
    status = request.args.get('status')

    rule=Rule.query.filter_by(id=id).first_or_404()

    if rule:
        rule.status = 1 if status=="true" else 0

        db.session.commit()

    return jsonify('success')

@routes.get('/delete-rule')
@login_required
def delete_rule():
    id = request.args.get('id')
    projectId = request.args.get('projectId')

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    rule=Rule.query.filter_by(id=id).first_or_404()
    if rule:
        db.session.delete(rule)
        db.session.commit()

    return jsonify('success')

@routes.route('/investigation-list/<int:projectId>')
@login_required
def investigation_list(projectId):

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))
        
    page = request.args.get('page',1)
    per_page = request.args.get('per_page',20)

    data = (
        db.session.query(Investigation, Task, User)
        .join(Task, Task.id==Investigation.task_id)
        .join(User, User.id==Investigation.user_id)
        .filter(User.project_id==projectId)
        .order_by(Investigation.id.desc())
        .paginate(page=int(page), per_page=int(per_page), error_out=False)
        )
    #Task.query.join(Section, Section.id==Task.section_id).join(User, User.id==Section.user_id).filter(Task.section_id==sectionId).order_by(Task.id.desc()).paginate(page=int(page), per_page=int(per_page), error_out=False)

    context={'title': 'Investigation list | ProjectManagerPro',
             'data': data,
             'projects': get_projects(),
             'projectId': projectId}
    
    return render_template('investigation-list.html',**context)


@routes.get('/investigation-status')
@login_required
def investigation_status():
    id = request.args.get('id')
    status = request.args.get('status')

    investigation=Investigation.query.filter_by(id=id).first_or_404()

    if investigation:
        investigation.status = 1 if status=="true" else 0

        db.session.commit()

    return jsonify('success')

@routes.get('/delete-investigation')
@login_required
def delete_investigation():
    id = request.args.get('id')
    projectId = request.args.get('projectId')

    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    investigation=Investigation.query.filter_by(id=id).first_or_404()
    if investigation:
        db.session.delete(investigation)
        db.session.commit()

    return jsonify('success')

@routes.get('/payroll/<int:projectId>')
@login_required
def payroll(projectId):
    if not checkManager(projectId):
        return redirect(url_for('routes.dashboard'))

    data = (
        db.session.query(
            User.name.label('name'),
            func.sum(SalaryMetrics.salary).label('total_salary'),
            (User.total_work_hours - func.sum(func.HOUR(SalaryMetrics.worked_time))).label('remain_hours'),
            func.sum(func.HOUR(SalaryMetrics.worked_time)).label('total_worked_hours')
        )
        .join(User, User.id == SalaryMetrics.user_id)
        .filter(User.project_id==projectId, func.MONTH(SalaryMetrics.created_at)==datetime.now().month)
        .group_by(User.id)
        .all()
    )

    date = (db.session.query(
            func.DATE(SalaryMetrics.created_at).label('date'),
            func.HOUR(SalaryMetrics.worked_time).label('worked_hour'),
            SalaryMetrics.user_id)
        .join(User, User.id==SalaryMetrics.user_id)
        .filter(func.MONTH(SalaryMetrics.created_at)==datetime.now().month, User.project_id==projectId)
        .all())
    
    calender = (db.session.query(
            func.DATE(SalaryMetrics.created_at).distinct().label('date'),
            func.DAYNAME(SalaryMetrics.created_at).label('day')
        )
        .join(User, User.id==SalaryMetrics.user_id)
        .filter(func.MONTH(SalaryMetrics.created_at)==datetime.now().month, User.project_id==projectId)
        .all())
    
    calender_data = {}

    for i in date:
        date_key = i.date
        if date_key not in calender_data:
            calender_data[date_key]=[]
        calender_data[date_key].append((i.user_id, i.worked_hour))


    
    context={'title': 'Payroll | ProjectManagerPro',
             'data': data,
             'projects': get_projects(),
             'projectId': projectId,
             'calender': calender,
             'calender_data': calender_data}
    
    return render_template('payroll.html',**context)

@routes.get('/sendPayrollMail')
@login_required
def sendPayrollMail():
    msg = Message('Payroll Mail | Project Manager', sender='test@vishaltechsoft.com', recipients=['hackertechv21@gmail.com'])
    msg.html = """
    <h1>Payroll attached with this mail!</h1>
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payroll Mail</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
    </style>
</head>
<body>
    <div class="container">
        <div class="row">
            <!-- User Cards -->
            <div class="col-md-3">
                <div class="card">
                    <img src="user1.jpg" class="card-img-top" alt="User 1">
                    <div class="card-body">
                        <h5 class="card-title">User 1</h5>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <!-- Add more user cards here -->
            </div>
            <!-- Add more rows of user cards as needed -->

            <!-- Payroll Table -->
            <div class="col-md-12 mt-4">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Day</th>
                            <th>User 1</th>
                            <th>User 2</th>
                            <th>User 3</th>
                            <th>User 4</th>
                            <th>User 5</th>
                            <th>User 6</th>
                            <th>User 7</th>
                            <th>User 8</th>
                            <th>User 9</th>
                            <th>User 10</th>
                            <!-- Add more user columns here -->
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>2023-10-01</td>
                            <td>Monday</td>
                            <td>2</td>
                            <td>6</td>
                            <td>6</td>
                            <td>4</td>
                            <td>5</td>
                            <td>8</td>
                            <td>12</td>
                            <td>11</td>
                            <td>6</td>
                            <td>4</td>
                            <!-- Add more rows with payroll data here -->
                        </tr>
                        <tr>
                            <td>2023-10-02</td>
                            <td>Tuesday</td>
                            <td>2</td>
                            <td>6</td>
                            <td>6</td>
                            <td>4</td>
                            <td>5</td>
                            <td>8</td>
                            <td>12</td>
                            <td>11</td>
                            <td>6</td>
                            <td>4</td>
                            <!-- Add more rows with payroll data here -->
                        </tr>
                        <tr>
                            <td>2023-10-03</td>
                            <td>Wednesday</td>
                            <td>2</td>
                            <td>6</td>
                            <td>6</td>
                            <td>4</td>
                            <td>5</td>
                            <td>8</td>
                            <td>12</td>
                            <td>11</td>
                            <td>6</td>
                            <td>4</td>
                            <!-- Add more rows with payroll data here -->
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""
    pdf = HTML(string=html_content).write_pdf(size='auto')
    msg.attach('payroll_report.pdf', 'application/pdf', pdf)
    mail.send(msg)
    return 'Email sent successfully!'

@routes.get('/update_mode/<string:mode>')
def update_mode(mode):
    session['mode'] = mode
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    else:
        return redirect(url_for('routes.index'))