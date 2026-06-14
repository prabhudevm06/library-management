from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = 'library_secret_key_2024'

DB_PATH = 'database/library.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            phone TEXT,
            address TEXT,
            joined_date TEXT DEFAULT CURRENT_DATE,
            avatar TEXT DEFAULT 'default.png'
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            category TEXT,
            publisher TEXT,
            year INTEGER,
            total_copies INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1,
            price REAL DEFAULT 0,
            cover_image TEXT DEFAULT 'book_default.png',
            description TEXT,
            rating REAL DEFAULT 0,
            reviews_count INTEGER DEFAULT 0,
            added_date TEXT DEFAULT CURRENT_DATE
        );

        CREATE TABLE IF NOT EXISTS borrows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            borrow_date TEXT DEFAULT CURRENT_DATE,
            due_date TEXT,
            return_date TEXT,
            status TEXT DEFAULT 'borrowed',
            fine REAL DEFAULT 0,
            issued_by INTEGER,
            notes TEXT,
            student_name TEXT,
            branch TEXT,
            year TEXT,
            usn TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (issued_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            rating INTEGER,
            comment TEXT,
            date TEXT DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            added_date TEXT DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        );
    ''')

    # Seed admin user
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = hashlib.md5('admin123'.encode()).hexdigest()
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                       ('Admin User', 'admin@library.com', admin_pass, 'admin'))

        books = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 'Fiction', 'Scribner', 1925, 5, 5, 299, 'gatsby.jpg', 'A story of the fabulously wealthy Jay Gatsby and his love for Daisy Buchanan.', 4.2, 1240),
            ('To Kill a Mockingbird', 'Harper Lee', '9780061935466', 'Fiction', 'HarperCollins', 1960, 4, 4, 349, 'mockingbird.jpg', 'The story of racial injustice and the loss of innocence in the American South.', 4.8, 3200),
            ('1984', 'George Orwell', '9780451524935', 'Dystopian', 'Signet Classic', 1949, 6, 6, 299, '1984.jpg', 'A dystopian social science fiction novel and cautionary tale.', 4.7, 4100),
            ('Harry Potter and the Sorcerer\'s Stone', 'J.K. Rowling', '9780439708180', 'Fantasy', 'Scholastic', 1997, 8, 8, 499, 'hp1.jpg', 'The first novel in the Harry Potter series.', 4.9, 8900),
            ('The Alchemist', 'Paulo Coelho', '9780062315007', 'Fiction', 'HarperOne', 1988, 5, 5, 399, 'alchemist.jpg', 'A philosophical novel about a young Andalusian shepherd.', 4.6, 5600),
            ('Sapiens', 'Yuval Noah Harari', '9780062316097', 'History', 'Harper', 2011, 4, 4, 599, 'sapiens.jpg', 'A brief history of humankind from ancient times to the present.', 4.5, 7200),
            ('Atomic Habits', 'James Clear', '9780735211292', 'Self-Help', 'Avery', 2018, 7, 7, 549, 'atomic.jpg', 'An easy and proven way to build good habits and break bad ones.', 4.8, 6800),
            ('The Lean Startup', 'Eric Ries', '9780307887894', 'Business', 'Crown Business', 2011, 3, 3, 499, 'lean.jpg', 'How today\'s entrepreneurs use continuous innovation to create successful businesses.', 4.4, 3100),
            ('Python Crash Course', 'Eric Matthes', '9781593276034', 'Technology', 'No Starch Press', 2015, 5, 5, 699, 'python.jpg', 'A hands-on, project-based introduction to programming.', 4.6, 4500),
            ('Clean Code', 'Robert C. Martin', '9780132350884', 'Technology', 'Prentice Hall', 2008, 4, 4, 749, 'cleancode.jpg', 'A handbook of agile software craftsmanship.', 4.4, 3800),
            ('The Da Vinci Code', 'Dan Brown', '9780307474278', 'Thriller', 'Anchor', 2003, 6, 6, 349, 'davinci.jpg', 'A mystery thriller novel following symbologist Robert Langdon.', 4.0, 9200),
            ('Thinking, Fast and Slow', 'Daniel Kahneman', '9780374533557', 'Psychology', 'Farrar, Straus and Giroux', 2011, 3, 3, 599, 'thinking.jpg', 'A ground-breaking tour of the mind.', 4.6, 5100),
        ]
        cursor.executemany(
            "INSERT INTO books (title, author, isbn, category, publisher, year, total_copies, available_copies, price, cover_image, description, rating, reviews_count) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            books
        )

    conn.commit()
    conn.close()

# ─── Auth ────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            return redirect(url_for('index'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        phone = request.form.get('phone', '')
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (name, email, password, phone) VALUES (?,?,?,?)", (name, email, password, phone))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Email already exists', 'error')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Pages ──────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    featured = conn.execute("SELECT * FROM books ORDER BY rating DESC LIMIT 8").fetchall()
    new_arrivals = conn.execute("SELECT * FROM books ORDER BY id DESC LIMIT 8").fetchall()
    stats = {
        'total_books': conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        'total_members': conn.execute("SELECT COUNT(*) FROM users WHERE role='member'").fetchone()[0],
        'active_borrows': conn.execute("SELECT COUNT(*) FROM borrows WHERE status='borrowed'").fetchone()[0],
        'categories': conn.execute("SELECT COUNT(DISTINCT category) FROM books").fetchone()[0],
    }
    categories = conn.execute("SELECT DISTINCT category FROM books").fetchall()
    conn.close()
    return render_template('index.html', featured=featured, new_arrivals=new_arrivals, stats=stats, categories=categories)

@app.route('/books')
def books():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'title')
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    if category:
        query += " AND category=?"
        params.append(category)
    query += f" ORDER BY {sort}"
    all_books = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT DISTINCT category FROM books").fetchall()
    conn.close()
    return render_template('books.html', books=all_books, categories=categories, search=search, selected_category=category)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    reviews = conn.execute("""
        SELECT r.*, u.name as user_name FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.book_id=? ORDER BY r.date DESC
    """, (book_id,)).fetchall()
    in_wishlist = conn.execute("SELECT id FROM wishlist WHERE user_id=? AND book_id=?",
                               (session['user_id'], book_id)).fetchone()
    related = conn.execute("SELECT * FROM books WHERE category=? AND id!=? LIMIT 4",
                           (book['category'], book_id)).fetchall()
    conn.close()
    return render_template('book_detail.html', book=book, reviews=reviews,
                           in_wishlist=bool(in_wishlist), related=related)

@app.route('/my-books')
def my_books():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    borrows = conn.execute("""
        SELECT b.*, bk.title, bk.author, bk.cover_image, bk.category
        FROM borrows b JOIN books bk ON b.book_id = bk.id
        WHERE b.user_id=? ORDER BY b.borrow_date DESC
    """, (session['user_id'],)).fetchall()
    conn.close()
    return render_template('my_books.html', borrows=borrows)

@app.route('/wishlist')
def wishlist():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    items = conn.execute("""
        SELECT bk.*, w.id as wish_id FROM wishlist w
        JOIN books bk ON w.book_id = bk.id WHERE w.user_id=?
    """, (session['user_id'],)).fetchall()
    conn.close()
    return render_template('wishlist.html', items=items)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    stats = {
        'total_borrowed': conn.execute("SELECT COUNT(*) FROM borrows WHERE user_id=?", (session['user_id'],)).fetchone()[0],
        'currently_borrowed': conn.execute("SELECT COUNT(*) FROM borrows WHERE user_id=? AND status='borrowed'", (session['user_id'],)).fetchone()[0],
        'wishlist_count': conn.execute("SELECT COUNT(*) FROM wishlist WHERE user_id=?", (session['user_id'],)).fetchone()[0],
    }
    conn.close()
    return render_template('profile.html', user=user, stats=stats)

# ─── Admin ───────────────────────────────────────────────
@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    conn = get_db()
    stats = {
        'total_books': conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        'total_members': conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        'active_borrows': conn.execute("SELECT COUNT(*) FROM borrows WHERE status='borrowed'").fetchone()[0],
        'overdue': conn.execute("SELECT COUNT(*) FROM borrows WHERE status='borrowed' AND due_date < date('now')").fetchone()[0],
    }
    recent_borrows = conn.execute("""
        SELECT b.*, COALESCE(u.name, b.student_name) as user_name, bk.title as book_title
        FROM borrows b LEFT JOIN users u ON b.user_id=u.id JOIN books bk ON b.book_id=bk.id
        ORDER BY b.borrow_date DESC LIMIT 20
    """).fetchall()
    members = conn.execute("SELECT id, name, email FROM users WHERE role='member' ORDER BY name").fetchall()
    conn.close()
    return render_template('admin.html', stats=stats, recent_borrows=recent_borrows, members=members)

# ─── API ─────────────────────────────────────────────────
@app.route('/api/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book or book['available_copies'] < 1:
        conn.close()
        return jsonify({'error': 'Book not available'}), 400
    existing = conn.execute("SELECT id FROM borrows WHERE user_id=? AND book_id=? AND status='borrowed'",
                            (session['user_id'], book_id)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Already borrowed'}), 400
    due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    conn.execute("INSERT INTO borrows (user_id, book_id, due_date) VALUES (?,?,?)",
                 (session['user_id'], book_id, due_date))
    conn.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Book borrowed! Due: {due_date}'})

@app.route('/api/return/<int:borrow_id>', methods=['POST'])
def return_book(borrow_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    conn = get_db()
    # Allow admin to return any book; member can only return their own
    if session.get('user_role') == 'admin':
        borrow = conn.execute("SELECT * FROM borrows WHERE id=?", (borrow_id,)).fetchone()
    else:
        borrow = conn.execute("SELECT * FROM borrows WHERE id=? AND user_id=?",
                              (borrow_id, session['user_id'])).fetchone()
    if not borrow:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    fine = 0
    if datetime.now().date() > datetime.strptime(borrow['due_date'], '%Y-%m-%d').date():
        days_late = (datetime.now().date() - datetime.strptime(borrow['due_date'], '%Y-%m-%d').date()).days
        fine = days_late * 5
    conn.execute("UPDATE borrows SET status='returned', return_date=date('now'), fine=? WHERE id=?", (fine, borrow_id))
    conn.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id=?", (borrow['book_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'fine': fine})

@app.route('/api/wishlist/toggle/<int:book_id>', methods=['POST'])
def toggle_wishlist(book_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    conn = get_db()
    existing = conn.execute("SELECT id FROM wishlist WHERE user_id=? AND book_id=?",
                            (session['user_id'], book_id)).fetchone()
    if existing:
        conn.execute("DELETE FROM wishlist WHERE id=?", (existing['id'],))
        conn.commit()
        conn.close()
        return jsonify({'added': False})
    else:
        conn.execute("INSERT INTO wishlist (user_id, book_id) VALUES (?,?)", (session['user_id'], book_id))
        conn.commit()
        conn.close()
        return jsonify({'added': True})

@app.route('/api/review/<int:book_id>', methods=['POST'])
def add_review(book_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO reviews (user_id, book_id, rating, comment) VALUES (?,?,?,?)",
                 (session['user_id'], book_id, data['rating'], data['comment']))
    avg = conn.execute("SELECT AVG(rating) FROM reviews WHERE book_id=?", (book_id,)).fetchone()[0]
    count = conn.execute("SELECT COUNT(*) FROM reviews WHERE book_id=?", (book_id,)).fetchone()[0]
    conn.execute("UPDATE books SET rating=?, reviews_count=? WHERE id=?", (round(avg, 1), count, book_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ─── Admin Book APIs ──────────────────────────────────────
@app.route('/api/admin/books', methods=['POST'])
def add_book():
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    conn = get_db()
    conn.execute("""INSERT INTO books (title, author, isbn, category, publisher, year, total_copies,
        available_copies, price, description) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (data['title'], data['author'], data['isbn'], data['category'], data['publisher'],
         data['year'], data['copies'], data['copies'], data['price'], data['description']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    # Check if book has active borrows
    active = conn.execute("SELECT COUNT(*) FROM borrows WHERE book_id=? AND status='borrowed'", (book_id,)).fetchone()[0]
    if active > 0:
        conn.close()
        return jsonify({'error': f'Cannot delete: {active} active borrow(s) exist'}), 400
    conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/books/<int:book_id>', methods=['PUT'])
def edit_book(book_id):
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    conn = get_db()
    conn.execute("""UPDATE books SET title=?, author=?, category=?, publisher=?, year=?,
        total_copies=?, price=?, description=? WHERE id=?""",
        (data['title'], data['author'], data['category'], data['publisher'],
         data['year'], data['copies'], data['price'], data['description'], book_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ─── Admin Issue API (admin issues book to member) ───────
@app.route('/api/admin/issue', methods=['POST'])
def admin_issue_book():
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    days = int(data.get('days', 14))
    notes = data.get('notes', '')
    student_name = data.get('student_name', '')
    branch = data.get('branch', '')
    year = data.get('year', '')
    usn = data.get('usn', '')
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book or book['available_copies'] < 1:
        conn.close()
        return jsonify({'error': 'Book not available'}), 400
    user_id = int(user_id) if user_id else None
    if user_id:
        existing = conn.execute("SELECT id FROM borrows WHERE user_id=? AND book_id=? AND status='borrowed'",
                                (user_id, book_id)).fetchone()
        if existing:
            conn.close()
            return jsonify({'error': 'Member already has this book'}), 400
    due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    conn.execute(
        "INSERT INTO borrows (user_id, book_id, due_date, issued_by, notes, student_name, branch, year, usn) VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id, book_id, due_date, session['user_id'], notes, student_name, branch, year, usn)
    )
    conn.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'due_date': due_date})

# ─── Admin Return API ─────────────────────────────────────
@app.route('/api/admin/return/<int:borrow_id>', methods=['POST'])
def admin_return_book(borrow_id):
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json or {}
    waive_fine = data.get('waive_fine', False)
    conn = get_db()
    borrow = conn.execute("SELECT * FROM borrows WHERE id=?", (borrow_id,)).fetchone()
    if not borrow:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    fine = 0
    if not waive_fine and datetime.now().date() > datetime.strptime(borrow['due_date'], '%Y-%m-%d').date():
        days_late = (datetime.now().date() - datetime.strptime(borrow['due_date'], '%Y-%m-%d').date()).days
        fine = days_late * 5
    conn.execute("UPDATE borrows SET status='returned', return_date=date('now'), fine=? WHERE id=?", (fine, borrow_id))
    conn.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id=?", (borrow['book_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'fine': fine})

# ─── Admin All Borrows API ────────────────────────────────
@app.route('/api/admin/borrows')
def admin_borrows():
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    status_filter = request.args.get('status', 'borrowed')
    conn = get_db()
    borrows = conn.execute("""
        SELECT b.*, COALESCE(u.name, b.student_name) as user_name,
               COALESCE(u.email, '') as user_email,
               bk.title as book_title, bk.author as book_author
        FROM borrows b
        LEFT JOIN users u ON b.user_id=u.id
        JOIN books bk ON b.book_id=bk.id
        WHERE b.status=?
        ORDER BY b.borrow_date DESC
    """, (status_filter,)).fetchall()
    conn.close()
    result = []
    for b in borrows:
        row = dict(b)
        if b['status'] == 'borrowed':
            due = datetime.strptime(b['due_date'], '%Y-%m-%d').date()
            today = datetime.now().date()
            row['days_left'] = (due - today).days
            row['overdue'] = (due - today).days < 0
            if row['overdue']:
                row['current_fine'] = abs((due - today).days) * 5
            else:
                row['current_fine'] = 0
        result.append(row)
    return jsonify(result)

@app.route('/api/admin/datastore')
def admin_datastore():
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    rows = conn.execute("""
        SELECT b.*, COALESCE(u.name, b.student_name) as user_name,
               COALESCE(u.email, '') as user_email,
               bk.title as book_title, bk.author as book_author
        FROM borrows b
        LEFT JOIN users u ON b.user_id=u.id
        JOIN books bk ON b.book_id=bk.id
        ORDER BY b.id DESC
    """).fetchall()
    conn.close()
    result = []
    for b in rows:
        row = dict(b)
        if b['status'] == 'borrowed' and b['due_date']:
            due = datetime.strptime(b['due_date'], '%Y-%m-%d').date()
            today = datetime.now().date()
            row['days_left'] = (due - today).days
            row['overdue'] = (due - today).days < 0
            row['current_fine'] = abs((due - today).days) * 5 if row['overdue'] else 0
        result.append(row)
    return jsonify(result)

@app.route('/api/admin/books-list')
def admin_books_list():
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    q = request.args.get('q', '')
    conn = get_db()
    books = conn.execute("""
        SELECT id, title, author, category, total_copies, available_copies, price, year, publisher, description
        FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY title
    """, (f'%{q}%', f'%{q}%')).fetchall()
    conn.close()
    return jsonify([dict(b) for b in books])

@app.route('/api/search')
def search_api():
    q = request.args.get('q', '')
    conn = get_db()
    results = conn.execute(
        "SELECT id, title, author, category, cover_image FROM books WHERE title LIKE ? OR author LIKE ? LIMIT 8",
        (f'%{q}%', f'%{q}%')
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in results])

if __name__ == '__main__':
    os.makedirs('database', exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
