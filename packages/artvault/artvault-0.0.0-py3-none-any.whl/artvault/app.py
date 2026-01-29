from flask import Flask, render_template, request, redirect, url_for
from database import init_db, save_commission, load_commissions
from models import Commission, DigitalCommission, TraditionalCommission

app = Flask(__name__)

init_db()

@app.route('/')
def home():
    commissions = load_commissions()
    return render_template('index.html', commissions=commissions)

@app.route('/add', methods=['GET', 'POST'])
def add_commission():
    if request.method == 'POST':
        client = request.form['client']
        description = request.form['description']
        commission_type = request.form['type']
        status = 'pending'
        software = request.form.get('software')
        medium = request.form.get('medium')
        if commission_type == 'digital' and software:
            commission = DigitalCommission(client, description, software, status)
        elif commission_type == 'traditional' and medium:
            commission = TraditionalCommission(client, description, medium, status)
        else:
            commission = Commission(client, description, status)
        save_commission(commission)
        return redirect(url_for('home'))
    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)
    