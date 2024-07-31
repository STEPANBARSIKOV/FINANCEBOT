import sqlite3

DATABASE = 'transactions.db'

def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        type TEXT NOT NULL,
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- Добавлено поле для времени
    )
    ''')
    conn.commit()
    conn.close()

def add_transaction(user_id, amount, currency, transaction_type, comment):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO transactions (user_id, amount, currency, type, comment, created_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
    ''', (user_id, amount, currency, transaction_type, comment))
    conn.commit()
    conn.close()

def get_transactions(user_id, period='all'):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    query = 'SELECT * FROM transactions WHERE user_id = ?'
    params = [user_id]

    cursor.execute(query, params)
    transactions = cursor.fetchall()
    conn.close()

    return transactions


def delete_transaction(transaction_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()

def update_transaction(transaction_id, amount, comment):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE transactions
    SET amount = ?, comment = ?
    WHERE id = ?
    ''', (amount, comment, transaction_id))
    conn.commit()
    conn.close()

def register_user(user_id, username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)')
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    cursor.execute('SELECT changes()')
    changes = cursor.fetchone()[0]
    conn.close()
    return changes > 0
