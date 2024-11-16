from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import expense_manager
from datetime import datetime
from expense_manager import get_expense_summary, DATABASE
import json 


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    
    if expense_manager.get_user(username):
        flash('Username already exists')
        return redirect(url_for('index'))
    
    password_hash = generate_password_hash(password)
    expense_manager.add_user(username, password_hash)
    flash('Registration successful! Please login.')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    user = expense_manager.get_user(username)
    if not user or not check_password_hash(user['password'], password):
        flash('Invalid username or password')
        return redirect(url_for('index'))
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/log_expense', methods=['GET', 'POST'])
def log_expense():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        amount = float(request.form['amount'])
        category_id = request.form['category_id']
        description = request.form['description']
        date = request.form['date']
        expense_type = request.form['type']
        
        expense_manager.log_expense(user_id, amount, category_id, description, date, expense_type)
        
        flash('Expense logged successfully!')
        return redirect(url_for('home'))
    
    return render_template('log_expense.html')
@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    username = session['username']
    expenses = expense_manager.get_user_expenses(user_id)
    total_expenses = expense_manager.get_total_expenses(user_id)
    total_income = expense_manager.get_total_income(user_id)
    expenses_by_category = expense_manager.get_expenses_by_category(user_id)

    categories = list(expenses_by_category.keys())
    amounts = list(expenses_by_category.values())
 
    
    return render_template('home.html', 
                           username=username,
                           expenses=expenses,
                           total_expenses=total_expenses,
                           total_income=total_income,
                           expenses_by_category=expenses_by_category,
                           chart_categories=json.dumps(categories),
                           chart_amounts=json.dumps(amounts)
                        )



@app.route('/summarize')
def summarize():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    print(f"Fetching expenses for user_id: {user_id}")  # Debug print
    
    expenses = get_expense_summary(user_id)
    print(f"Found {len(expenses)} expenses")  # Debug print
    
    return render_template('summarize.html', expenses=expenses)



@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    if expense_manager.delete_expense(user_id, expense_id):
        flash('Expense deleted successfully!')
    else:
        flash('Failed to delete expense.')
    
    return redirect(url_for('summarize'))






@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user_preferences = expense_manager.get_user_preferences(session['user_id'])
    return render_template('profile.html', user_preferences=user_preferences)

@app.route('/update_username', methods=['POST'])
def update_username():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    new_username = request.form['new_username']
    if expense_manager.update_username(session['user_id'], new_username):
        session['username'] = new_username
        flash('Username updated successfully', 'success')
    else:
        flash('Failed to update username. It may already be taken.', 'error')
    return redirect(url_for('profile'))

@app.route('/update_password', methods=['POST'])
def update_password():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
    elif expense_manager.update_password(session['user_id'], current_password, new_password):
        flash('Password updated successfully', 'success')
    else:
        flash('Failed to update password. Please check your current password.', 'error')
    return redirect(url_for('profile'))

@app.route('/update_currency', methods=['POST'])
def update_currency():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    currency_sign = request.form['currency_sign']
    if expense_manager.update_currency_preference(session['user_id'], currency_sign):
        flash('Currency preference updated successfully', 'success')
    else:
        flash('Failed to update currency preference', 'error')
    return redirect(url_for('profile'))




if __name__ == '__main__':
    app.run(debug=True)