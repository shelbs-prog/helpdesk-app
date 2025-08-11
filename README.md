🛠 Helpdesk Ticketing System
A web-based support ticket system built with Flask, SQLAlchemy, and SQLite. This app lets users submit, search, and manage IT helpdesk tickets with priority, status tracking, and timestamps.

🚀 Features
- ✅ User login/logout with secure session management
- 🎟 Create, view, and filter helpdesk tickets
- 🔍 Search by ticket title, description, and ID
- 📂 View Open and Closed ticket queues separately
- 🕒 Track ticket creation time (date_created)
- 📊 Dynamic search with case-insensitive filtering
- 🧮 Calculate ticket durations using Python

🧰 Technologies Used
| Tool | Purpose | 
| Flask | Web framework | 
| SQLAlchemy | ORM for database interactions | 
| SQLite | Lightweight database | 
| Jinja2 | Templating engine | 
| Bootstrap | (Optional) For UI styling | 



📦 Setup Instructions
git clone https://github.com/your-username/helpdesk-app.git
cd helpdesk-app
python -m venv venv
source venv/bin/activate   # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

# Initialize the database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run the app
flask run



🔐 Authentication
This app uses login-required decorators to restrict access to ticket views. Only authenticated users can create or manage tickets.

💡 Future Enhancements
- 📨 Email notifications for ticket updates
- 📋 Admin dashboard for tracking all users
- 📎 File uploads for attachments
- 🌐 PostgreSQL or MySQL support for production use

🙌 Contributions
Pull requests are welcome! If you find a bug or have a feature idea, feel free to open an issue.


