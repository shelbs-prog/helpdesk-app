from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory database for tickets
tickets = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    title = request.form['title']
    description = request.form['description']
    ticket = {
        'id': len(tickets) + 1,
        'title': title,
        'description': description,
        'status': 'Open'
    }
    tickets.append(ticket)
    return redirect(url_for('index'))

@app.route('/tickets')
def tickets_view():
    return render_template('tickets.html', tickets=tickets)

if __name__ == '__main__':
    app.run(debug=True)
