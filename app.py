from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime
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
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_ticket', methods=['POST'])
@login_required
def submit_ticket():
    issue_type = request.form['issue_type']
    description = request.form['description']

    priority_map = {
        "Password Reset": "Low",
        "Software Installation": "Medium",
        "Hardware Problem": "High",
        "Network Connectivity": "High",
        "Email Access": "Medium",
        "Other": "Low"
    }
    priority = priority_map.get(issue_type, "Low")

    ticket = Ticket(title=issue_type, description=description, priority=priority, user_id=current_user.id)
    db.session.add(ticket)
    db.session.commit()
    flash('Ticket submitted!')
    return redirect(url_for('index'))

@app.route('/tickets')
@login_required
def tickets_view():
    search = request.args.get('search', '')
    if search:
        tickets = Ticket.query.filter(
            Ticket.status == 'Open',
            or_(
                Ticket.title.ilike(f'%{search}%'),
                Ticket.description.ilike(f'%{search}%')
            )
        ).order_by(Ticket.date_created.desc()).all()
    else:
        tickets = Ticket.query.filter_by(status='Open').order_by(Ticket.date_created.desc()).all()
    return render_template('tickets.html', tickets=tickets, form_action='tickets_view')

@app.route('/closedtickets')
@login_required
def closed_tickets_view():
    search_query = request.args.get('search', '')
    if search_query:
        tickets = Ticket.query.filter(
            Ticket.status == 'Closed',
            or_(
                Ticket.title.ilike(f'%{search_query}%'),
                Ticket.description.ilike(f'%{search_query}%')
            )
        ).order_by(Ticket.date_created.desc()).all()
    else:
        tickets = Ticket.query.filter_by(status='Closed').order_by(Ticket.date_created.desc()).all()
    return render_template('closedtickets.html', tickets=tickets,  form_action='closed_tickets_view')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
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

if __name__ == '__main__':
    app.run(debug=True)
