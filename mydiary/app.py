from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secretkey123'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        name TEXT,
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        done INTEGER DEFAULT 0,
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        plan_date DATE,
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        target_amount REAL,
        current_amount REAL DEFAULT 0,
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        image TEXT,
        created_at TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

def check_auth():
    if 'user_id' not in session:
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        name = request.form['name']
        conn = sqlite3.connect('diary.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, name, created_at) VALUES (?,?,?,?)",
                      (username, password, name, datetime.now()))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            session['user_id'] = user_id
            session['username'] = username
            session['name'] = name
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Имя пользователя уже занято!', 'error')
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        conn = sqlite3.connect('diary.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = username
            session['name'] = user[1]
            flash(f'Добро пожаловать, {user[1]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!', 'error')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if check_auth(): return check_auth()
    return render_template('index.html')

@app.route('/notes')
def notes():
    if check_auth(): return check_auth()
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    notes = c.fetchall()
    conn.close()
    return render_template('notes.html', notes=notes)

@app.route('/add_note', methods=['POST'])
def add_note():
    title = request.form['title']
    content = request.form['content']
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, title, content, created_at) VALUES (?,?,?,?)",
              (user_id, title, content, datetime.now()))
    conn.commit()
    conn.close()
    return redirect(url_for('notes'))

@app.route('/delete_note/<int:id>')
def delete_note(id):
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('notes'))

@app.route('/tasks')
def tasks():
    if check_auth(): return check_auth()
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY done ASC, created_at DESC", (user_id,))
    tasks = c.fetchall()
    conn.close()
    return render_template('tasks.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form['title']
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, title, created_at) VALUES (?,?,?)", (user_id, title, datetime.now()))
    conn.commit()
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/toggle_task/<int:id>')
def toggle_task(id):
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = NOT done WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/delete_task/<int:id>')
def delete_task(id):
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/plans')
def plans():
    if check_auth(): return check_auth()
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("SELECT * FROM plans WHERE user_id=? ORDER BY plan_date ASC", (user_id,))
    plans = c.fetchall()
    conn.close()
    return render_template('plans.html', plans=plans)

@app.route('/add_plan', methods=['POST'])
def add_plan():
    title = request.form['title']
    plan_date = request.form['plan_date']
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("INSERT INTO plans (user_id, title, plan_date, created_at) VALUES (?,?,?,?)",
              (user_id, title, plan_date, datetime.now()))
    conn.commit()
    conn.close()
    return redirect(url_for('plans'))

@app.route('/delete_plan/<int:id>')
def delete_plan(id):
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("DELETE FROM plans WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('plans'))

@app.route('/goals')
def goals():
    if check_auth(): return check_auth()
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("SELECT * FROM goals WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    goals = c.fetchall()
    conn.close()
    return render_template('goals.html', goals=goals)

@app.route('/add_goal', methods=['POST'])
def add_goal():
    title = request.form['title']
    target_amount = float(request.form['target_amount'])
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("INSERT INTO goals (user_id, title, target_amount, created_at) VALUES (?,?,?,?)",
              (user_id, title, target_amount, datetime.now()))
    conn.commit()
    conn.close()
    return redirect(url_for('goals'))

@app.route('/add_to_goal/<int:id>', methods=['POST'])
def add_to_goal(id):
    amount = float(request.form['amount'])
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("UPDATE goals SET current_amount = current_amount + ? WHERE id=? AND user_id=?", (amount, id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('goals'))

@app.route('/delete_goal/<int:id>')
def delete_goal(id):
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("DELETE FROM goals WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('goals'))

@app.route('/memories')
def memories():
    if check_auth(): return check_auth()
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("SELECT * FROM memories WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    memories = c.fetchall()
    conn.close()
    return render_template('memories.html', memories=memories)

@app.route('/add_memory', methods=['POST'])
def add_memory():
    title = request.form['title']
    content = request.form['content']
    user_id = session['user_id']
    image = None
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("INSERT INTO memories (user_id, title, content, image, created_at) VALUES (?,?,?,?,?)",
              (user_id, title, content, image, datetime.now()))
    conn.commit()
    conn.close()
    return redirect(url_for('memories'))

@app.route('/delete_memory/<int:id>')
def delete_memory(id):
    user_id = session['user_id']
    conn = sqlite3.connect('diary.db')
    c = conn.cursor()
    c.execute("DELETE FROM memories WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('memories'))

if __name__ == '__main__':
    app.run(debug=True)