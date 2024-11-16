import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'expenses.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category_id INTEGER,
        description TEXT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
                  FOREIGN KEY (category_id) REFERENCES categories (id)  -- Foreign key reference
    )
    ''')
    cur.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
                )''')
    conn.commit()
    conn.close()

def add_user(username, password_hash):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    conn.close()
    return user

def log_expense(user_id, amount, category_id, description, date, expense_type):
    conn = get_db_connection()
    cur = conn.cursor()
    if expense_type == 'expense':
        amount = -abs(amount)  # Store expenses as negative
    else:
        amount = abs(amount)
    cur.execute('INSERT INTO expenses (user_id, amount, category_id, description, date, type) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, amount, category_id, description, date, expense_type))
    conn.commit()
    conn.close()

def get_user_expenses(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,))
    expenses = cur.fetchall()
    conn.close()
    return expenses

def get_total_expenses(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (user_id,))
    total = cur.fetchone()['total']
    conn.close()
    return round(total if total else 0, 2)

def get_total_income(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ? AND type = "income"', (user_id,))
    total = cur.fetchone()['total']
    conn.close()
    return round(total if total else 0, 2)

def get_expenses_by_category(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(''' 
    SELECT category_id, SUM(amount) as total
    FROM expenses
    WHERE user_id = ?
    GROUP BY category_id  -- Change category to category_id
    ''', (user_id,))
    categories = {row['category_id']: round(row['total'], 2) for row in cur.fetchall()}
    conn.close()
    return categories



def delete_expense(user_id, expense_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (expense_id, user_id))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_expense_summary(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(""" 
            SELECT 
                e.id,
                e.date,
                COALESCE(c.name, 'Uncategorized') as category_name,
                e.description,
                e.amount,
                e.type
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.user_id = ?
            ORDER BY e.date DESC
        """, (user_id,))
        
        expenses = []
        for row in cur.fetchall():
            expense = {
                'id': row['id'],
                'date': datetime.strptime(row['date'], '%Y-%m-%d'),
                'category_name': row['category_name'],
                'description': row['description'] if row['description'] else 'No description',
                'amount': round(float(row['amount']), 2),
                'type': row['type']
            }
            expenses.append(expense)
        
        return expenses
    finally:
        cur.close()
        conn.close()


def update_username(user_id, new_username):
    """
    Update the username for a given user.
    
    :param user_id: The ID of the user to update
    :param new_username: The new username to set
    :return: True if successful, False if the username already exists
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM users WHERE username = ?', (new_username,))
        if cur.fetchone():
            return False  # Username already exists
        
        cur.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def update_password(user_id, current_password, new_password):
    """
    Update the password for a given user.
    
    :param user_id: The ID of the user to update
    :param current_password: The current password for verification
    :param new_password: The new password to set
    :return: True if successful, False if the current password is incorrect
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT password FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        if user and check_password_hash(user['password'], current_password):
            new_password_hash = generate_password_hash(new_password)
            cur.execute('UPDATE users SET password = ? WHERE id = ?', (new_password_hash, user_id))
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def update_currency_preference(user_id, currency_sign):
    """
    Update the currency preference for a given user.
    
    :param user_id: The ID of the user to update
    :param currency_sign: The new currency sign preference
    :return: True if successful, False otherwise
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # First, check if the users table has a currency_preference column
        cur.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'currency_preference' not in columns:
            # Add the column if it doesn't exist
            cur.execute('ALTER TABLE users ADD COLUMN currency_preference TEXT')
        
        cur.execute('UPDATE users SET currency_preference = ? WHERE id = ?', (currency_sign, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def get_user_preferences(user_id):
    """
    Get the user's preferences, including currency sign.
    
    :param user_id: The ID of the user
    :return: A dictionary containing the user's preferences
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT username, currency_preference FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        if user:
            return {
                'username': user['username'],
                'currency_preference': user['currency_preference'] or '$'  # Default to $ if not set
            }
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()


# Initialize the database when this module is imported
init_db()