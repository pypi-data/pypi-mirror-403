import sqlite3
import json
from models import Commission, DigitalCommission, TraditionalCommission

DB_FILE = 'commissions.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS commissions
                 (id INTEGER PRIMARY KEY, data TEXT)''')
    conn.commit()
    conn.close()

def save_commission(commission):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    data = json.dumps(commission.to_dict())
    c.execute("INSERT INTO commissions (data) VALUES (?)", (data,))
    conn.commit()
    conn.close()

def load_commissions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT data FROM commissions")
    rows = c.fetchall()
    conn.close()
    commissions = []
    for row in rows:
        data = json.loads(row[0])
        if data['type'] == 'commission':
            commissions.append(Commission.from_dict(data))
        elif data['type'] == 'digital':
            commissions.append(DigitalCommission.from_dict(data))
        elif data['type'] == 'traditional':
            commissions.append(TraditionalCommission.from_dict(data))
    return commissions

def update_commission(commission_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT data FROM commissions WHERE id=?", (commission_id,))
    row = c.fetchone()
    if row:
        data = json.loads(row[0])
        data['status'] = new_status
        new_data = json.dumps(data)
        c.execute("UPDATE commissions SET data=? WHERE id=?", (new_data, commission_id))
        conn.commit()
    conn.close()

def delete_commission(commission_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM commissions WHERE id=?", (commission_id,))
    conn.commit()
    conn.close()