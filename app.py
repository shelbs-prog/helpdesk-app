from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime
from sqlalchemy.orm import joinedload
from flask import abort
import io
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Helpdesk'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ticket model
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')
    priority = db.Column(db.String(10), default='Low')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='sumbitted_tickets')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50))  # or Integer, Enum, etc.

#user model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'

    tickets = db.relationship('Ticket', backref='submitter', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        
    

        # Create the ticket and assign to current user
        new_ticket = Ticket(
            title=title,
            description=description,
            category=category,
            status='Open',
            priority='Low',
            user_id=current_user.id,
            
        )
        db.session.add(new_ticket)
        db.session.commit()

        flash('Ticket submitted successfully!', 'success')
        return redirect(url_for('dashboard_user'))

    return render_template('index.html')

@app.route('/submit_ticket', methods=['POST'])
@login_required
def submit_ticket():
    # Safely retrieve form fields
    issue_type = request.form.get('issue_type', '')
    description = request.form.get('description', '')
    category = request.form.get('category', 'General')

    priority_map = {
        "Password Reset": "Low",
        "Software Installation": "Medium",
        "Hardware Problem": "High",
        "Network Connectivity": "High",
        "Email Access": "Medium",
        "Other": "Low"
    }
    priority = priority_map.get(issue_type, "Low")

    # Create the ticket
    ticket = Ticket(
        title=issue_type,
        description=description,
        priority=priority,
        category=category,
        user_id=current_user.id
    )

    db.session.add(ticket)
    db.session.commit()
    flash('Ticket submitted!')
    return redirect(url_for('index'))


@app.route('/tickets')
@login_required
def tickets_view():
    from datetime import datetime
    from sqlalchemy import or_

    search_query = request.args.get('search', '')

    # Summary stats for current user
    open_count = Ticket.query.filter_by(user_id=current_user.id, status='Open').count()
    closed_count = Ticket.query.filter_by(user_id=current_user.id, status='Closed').count()
    overdue_count = Ticket.query.filter(
        Ticket.user_id == current_user.id,
        Ticket.status != 'Closed',
    ).count()

    # Base query for open tickets
    base_query = Ticket.query.filter_by(user_id=current_user.id, status='Open')

    if search_query:
        filters = [
            Ticket.title.ilike(f'%{search_query}%'),
            Ticket.description.ilike(f'%{search_query}%')
        ]
        if search_query.isdigit():
            filters.append(Ticket.id == int(search_query))
        base_query = base_query.filter(or_(*filters))

    tickets = base_query.order_by(Ticket.date_created.desc()).all()

    return render_template('tickets.html',
                           tickets=tickets,
                           form_action='tickets_view',
                           open_count=open_count,
                           closed_count=closed_count,
                           overdue_count=overdue_count)




@app.route('/closedtickets')
@login_required
def closed_tickets_view():
    search_query = request.args.get('search', '')

    if search_query:
        filters = [
            Ticket.title.ilike(f'%{search_query}%'),
            Ticket.description.ilike(f'%{search_query}%')
        ]
        if search_query.isdigit():
            filters.append(Ticket.id == int(search_query))

        tickets = Ticket.query.filter(
            Ticket.status == 'Closed',
            Ticket.user_id == current_user.id,
            or_(*filters)
        ).order_by(Ticket.date_created.desc()).all()
    else:
        tickets = Ticket.query.filter_by(
            status='Closed',
            user_id=current_user.id
        ).order_by(Ticket.date_created.desc()).all()

    return render_template('closedtickets.html', tickets=tickets, form_action='closed_tickets_view')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'login-success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard_user'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            hashed_password = generate_password_hash(password)
            user = User(username=username, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/update_priority/<int:ticket_id>', methods=['POST'])
@login_required
def update_priority(ticket_id):
    new_priority = request.form['priority']
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.priority = new_priority
    db.session.commit()
    return redirect(url_for('tickets_view'))

@app.route('/update_status/<int:ticket_id>', methods=['POST'])
@login_required
def update_status(ticket_id):
    new_status = request.form['status']
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = new_status
    db.session.commit()
    return redirect(url_for('tickets_view'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)

    ticket_count = Ticket.query.count()
    open_count = Ticket.query.filter_by(status='Open').count()
    closed_count = Ticket.query.filter_by(status='Closed').count()
    overdue_count = Ticket.query.filter(
        Ticket.status != 'Closed'
    ).count()

    category_summary = db.session.query(
        Ticket.category, db.func.count(Ticket.id)
    ).group_by(Ticket.category).all()

    # This line fetches all tickets for display
    tickets = (Ticket.query
               .options(joinedload(Ticket.user))
               .order_by(Ticket.date_created.desc())
               .all())


    return render_template('dashboard_admin.html',
                           ticket_count=ticket_count,
                           open_count=open_count,
                           closed_count=closed_count,
                           overdue_count=overdue_count,
                           category_summary=category_summary,
                           tickets=tickets)  # Pass the ticket list here

@app.route('/dashboard_user')
@login_required
def dashboard_user():
    search_query = request.args.get('search', '')

    # Counts for this user
    from datetime import datetime  # ensure imported at top in your file
    open_count = Ticket.query.filter_by(user_id=current_user.id, status='Open').count()
    closed_count = Ticket.query.filter_by(user_id=current_user.id, status='Closed').count()
    overdue_count = Ticket.query.filter(
        Ticket.user_id == current_user.id,
        Ticket.status != 'Closed'
    ).count()

    # Base query for closed tickets (shown on dashboard)
    closed_q = Ticket.query.filter_by(user_id=current_user.id, status='Closed')

    if search_query:
        from sqlalchemy import or_  # ensure imported at top in your file
        filters = [
            Ticket.title.ilike(f'%{search_query}%'),
            Ticket.description.ilike(f'%{search_query}%')
        ]
        if search_query.isdigit():
            filters.append(Ticket.id == int(search_query))
        closed_q = closed_q.filter(or_(*filters))

    tickets = closed_q.order_by(Ticket.date_created.desc()).all()

    return render_template(
        'dashboard_user.html',
        tickets=tickets,
        open_count=open_count,
        closed_count=closed_count,
        overdue_count=overdue_count,
        form_action='dashboard_user'
    )

if __name__ == '__main__':
    app.run(debug=True)