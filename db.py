import sqlite3
import os
import datetime
import hashlib
import secrets
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'dfox_tracker.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return hashed, salt

def verify_password(password, stored_hash, salt):
    test_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return test_hash == stored_hash

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users & Authentication Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Developer', -- 'HOD', 'Team Lead', 'Developer'
        designation TEXT DEFAULT 'Software Engineer',
        avatar_color TEXT DEFAULT '#7928CA',
        is_verified INTEGER DEFAULT 0,
        verification_otp TEXT,
        verification_token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Sessions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # Tasks Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'General',
        priority TEXT DEFAULT 'Medium',
        assignee_id INTEGER,
        allocated_hours REAL NOT NULL DEFAULT 0.0,
        allocated_minutes INTEGER NOT NULL DEFAULT 0,
        allocated_total_hours REAL NOT NULL DEFAULT 0.0,
        actual_hours REAL DEFAULT 0.0,
        actual_minutes INTEGER DEFAULT 0,
        actual_total_hours REAL DEFAULT 0.0,
        status TEXT DEFAULT 'Assigned', -- Assigned, In Progress, In Review, Completed, Cancelled
        efficiency REAL DEFAULT NULL,
        completion_notes TEXT,
        pr_link TEXT,
        due_date TEXT,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        created_by TEXT DEFAULT 'Team Lead',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL
    )
    ''')
    
    # Email Logs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        recipient_email TEXT NOT NULL,
        recipient_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        body_html TEXT NOT NULL,
        status TEXT DEFAULT 'SENT', -- SENT, SIMULATED, FAILED
        error_message TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )
    ''')
    
    # Settings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    conn.commit()
    
    # Seed HOD & Team Lead initial accounts if empty (with sample default password 'Dfox@123' so they can log in or sign up)
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        h_sachin, s_sachin = hash_password('Dfox@123')
        h_rupesh, s_rupesh = hash_password('Dfox@123')
        h_alex, s_alex = hash_password('Dfox@123')
        h_dinesh, s_dinesh = hash_password('Dfox@123')
        
        initial_users = [
            ('Sachin Pawar', 'sachin@dfoxmedia.com', h_sachin, s_sachin, 'HOD', 'HOD Development', '#D81B60', 1),
            ('Rupesh Ghumare', 'rupesh@dfoxmedia.com', h_rupesh, s_rupesh, 'Team Lead', 'Team Lead', '#7928CA', 1),
            ('Alex Rivera', 'alex.rivera@dfoxmedia.com', h_alex, s_alex, 'Developer', 'Senior UI/UX Engineer', '#0284c7', 1),
            ('Dinesh Katyare', 'dinesh.k@dfoxmedia.com', h_dinesh, s_dinesh, 'Developer', 'Senior Backend Engineer', '#059669', 1)
        ]
        
        cursor.executemany('''
            INSERT INTO users (name, email, password_hash, salt, role, designation, avatar_color, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', initial_users)
        conn.commit()
        
    # Seed initial sample tasks if empty
    cursor.execute('SELECT COUNT(*) FROM tasks')
    if cursor.fetchone()[0] == 0:
        sample_tasks = [
            (
                'Build Responsive Navigation Bar',
                'Design mobile-first navigation bar with DFOX logo and responsive menu.',
                'Frontend',
                'High',
                3, # Alex Rivera
                4, 0, 4.0,
                3, 15, 3.25,
                'Completed',
                123.1,
                'Completed with mobile drawer and smooth transitions.',
                'https://github.com/dfoxmedia/dev-tracker/pull/12',
                '2026-08-25',
                '2026-08-21 09:00:00',
                '2026-08-21 12:15:00',
                'Rupesh Ghumare (Team Lead)'
            ),
            (
                'Implement User Auth & Verification API',
                'Develop backend endpoints for user signup, email verification with OTP, and session authentication.',
                'Backend',
                'Urgent',
                4, # Dinesh Katyare
                6, 0, 6.0,
                5, 0, 5.0,
                'Completed',
                120.0,
                'Auth REST endpoints and verification OTP email flow verified.',
                'https://github.com/dfoxmedia/dev-tracker/pull/14',
                '2026-08-22',
                '2026-08-21 08:30:00',
                '2026-08-21 13:30:00',
                'Sachin Pawar (HOD)'
            )
        ]
        cursor.executemany('''
            INSERT INTO tasks (
                title, description, category, priority, assignee_id,
                allocated_hours, allocated_minutes, allocated_total_hours,
                actual_hours, actual_minutes, actual_total_hours,
                status, efficiency, completion_notes, pr_link, due_date,
                assigned_at, completed_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_tasks)
        conn.commit()

    conn.close()

# ----------------- User & Authentication Functions -----------------

def create_user(name, email, password, designation):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute('SELECT id, is_verified FROM users WHERE email = ?', (email.strip().lower(),))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        if existing['is_verified']:
            return None, 'An account with this email address already exists. Please log in.'
        else:
            # User exists but not verified -> update password and generate fresh OTP
            otp = f"{random.randint(100000, 999999)}"
            token = secrets.token_urlsafe(32)
            pwd_hash, salt = hash_password(password)
            
            # Determine role
            email_lower = email.strip().lower()
            if email_lower == 'sachin@dfoxmedia.com' or 'hod' in designation.lower() or 'head' in designation.lower():
                role = 'HOD'
            elif email_lower == 'rupesh@dfoxmedia.com' or 'lead' in designation.lower():
                role = 'Team Lead'
            else:
                role = 'Developer'
                
            cursor_up = get_db().cursor()
            cursor_up.execute('''
                UPDATE users SET
                    name = ?,
                    password_hash = ?,
                    salt = ?,
                    role = ?,
                    designation = ?,
                    verification_otp = ?,
                    verification_token = ?
                WHERE id = ?
            ''', (name.strip(), pwd_hash, salt, role, designation.strip(), otp, token, existing['id']))
            cursor_up.connection.commit()
            cursor_up.connection.close()
            
            user = get_user_by_id(existing['id'])
            return user, None

    # Determine Role based on User Specifications:
    email_clean = email.strip().lower()
    desig_clean = designation.strip().lower()
    
    if email_clean == 'sachin@dfoxmedia.com' or 'hod' in desig_clean or 'head' in desig_clean:
        role = 'HOD'
        avatar_color = '#D81B60'
    elif email_clean == 'rupesh@dfoxmedia.com' or 'lead' in desig_clean:
        role = 'Team Lead'
        avatar_color = '#7928CA'
    else:
        role = 'Developer'
        avatar_colors = ['#0284c7', '#059669', '#9C27B0', '#ea580c', '#e11d48', '#6441a5']
        avatar_color = random.choice(avatar_colors)
        
    pwd_hash, salt = hash_password(password)
    otp = f"{random.randint(100000, 999999)}"
    token = secrets.token_urlsafe(32)
    
    cursor.execute('''
        INSERT INTO users (
            name, email, password_hash, salt, role, designation,
            avatar_color, is_verified, verification_otp, verification_token
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    ''', (name.strip(), email_clean, pwd_hash, salt, role, designation.strip(), avatar_color, otp, token))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    
    user = get_user_by_id(user_id)
    return user, None

def verify_user_otp(email, otp_code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email.strip().lower(),))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, 'User not found'
        
    if user['is_verified']:
        conn.close()
        return True, 'Account is already verified. You can log in.'
        
    if user['verification_otp'] == str(otp_code).strip():
        cursor.execute('''
            UPDATE users SET
                is_verified = 1,
                verification_otp = NULL,
                verification_token = NULL,
                verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (user['id'],))
        conn.commit()
        conn.close()
        return True, 'Account successfully verified! You can now log in.'
    else:
        conn.close()
        return False, 'Invalid verification code. Please check the code sent to your email.'

def verify_user_token(token):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE verification_token = ?', (token,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False, 'Invalid or expired verification link'
        
    cursor.execute('''
        UPDATE users SET
            is_verified = 1,
            verification_otp = NULL,
            verification_token = NULL,
            verified_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (user['id'],))
    conn.commit()
    conn.close()
    return True, 'Account verified successfully!'

def resend_otp(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email.strip().lower(),))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None, 'No account found with this email'
    if user['is_verified']:
        conn.close()
        return None, 'Account is already verified'
        
    otp = f"{random.randint(100000, 999999)}"
    cursor.execute('UPDATE users SET verification_otp = ? WHERE id = ?', (otp, user['id']))
    conn.commit()
    conn.close()
    
    updated_user = get_user_by_id(user['id'])
    return updated_user, None

def authenticate_user(email, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return None, 'Invalid email or password'
        
    if not verify_password(password, user['password_hash'], user['salt']):
        return None, 'Invalid email or password'
        
    if not user['is_verified']:
        return None, 'UNVERIFIED_ACCOUNT'
        
    # Create Session Token
    session_token = secrets.token_hex(32)
    conn = get_db()
    cursor = conn.cursor()
    expires = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)', (session_token, user['id'], expires))
    cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
    conn.commit()
    conn.close()
    
    safe_user = dict(user)
    del safe_user['password_hash']
    del safe_user['salt']
    return {'user': safe_user, 'token': session_token}, None

def get_user_by_session(session_token):
    if not session_token:
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.* FROM users u
        JOIN sessions s ON u.id = s.user_id
        WHERE s.token = ? AND (s.expires_at IS NULL OR s.expires_at > CURRENT_TIMESTAMP)
    ''', (session_token,))
    row = cursor.fetchone()
    conn.close()
    if row:
        safe_user = dict(row)
        del safe_user['password_hash']
        del safe_user['salt']
        return safe_user
    return None

def delete_session(session_token):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE token = ?', (session_token,))
    conn.commit()
    conn.close()

def get_all_members():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, role, designation, avatar_color, is_verified, created_at FROM users WHERE is_verified = 1 ORDER BY CASE role WHEN "HOD" THEN 1 WHEN "Team Lead" THEN 2 ELSE 3 END, name ASC')
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return members

def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, role, designation, avatar_color, is_verified, verification_otp, verification_token, created_at FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_member(member_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (member_id,))
    conn.commit()
    conn.close()

# ----------------- Tasks CRUD -----------------

def get_all_tasks(assignee_id=None, status=None, search=None):
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT t.*, u.name as assignee_name, u.email as assignee_email, 
               u.role as assignee_role, u.avatar_color as assignee_avatar_color
        FROM tasks t
        LEFT JOIN users u ON t.assignee_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if assignee_id:
        query += ' AND t.assignee_id = ?'
        params.append(assignee_id)
        
    if status and status != 'ALL':
        query += ' AND t.status = ?'
        params.append(status)
        
    if search:
        query += ' AND (t.title LIKE ? OR t.description LIKE ? OR u.name LIKE ?)'
        wildcard = f'%{search}%'
        params.extend([wildcard, wildcard, wildcard])
        
    query += ' ORDER BY CASE t.priority WHEN "Urgent" THEN 1 WHEN "High" THEN 2 WHEN "Medium" THEN 3 ELSE 4 END, t.due_date ASC, t.id DESC'
    
    cursor.execute(query, params)
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_task_by_id(task_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, u.name as assignee_name, u.email as assignee_email, 
               u.role as assignee_role, u.avatar_color as assignee_avatar_color
        FROM tasks t
        LEFT JOIN users u ON t.assignee_id = u.id
        WHERE t.id = ?
    ''', (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_task(data):
    conn = get_db()
    cursor = conn.cursor()
    
    alloc_h = float(data.get('allocated_hours', 0))
    alloc_m = int(data.get('allocated_minutes', 0))
    alloc_total = round(alloc_h + (alloc_m / 60.0), 2)
    
    cursor.execute('''
        INSERT INTO tasks (
            title, description, category, priority, assignee_id,
            allocated_hours, allocated_minutes, allocated_total_hours,
            status, due_date, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Assigned', ?, ?)
    ''', (
        data.get('title'),
        data.get('description', ''),
        data.get('category', 'General'),
        data.get('priority', 'Medium'),
        data.get('assignee_id'),
        alloc_h,
        alloc_m,
        alloc_total,
        data.get('due_date'),
        data.get('created_by', 'Team Lead')
    ))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def update_task_status_and_time(task_id, data):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    if not task:
        conn.close()
        return None
        
    status = data.get('status', task['status'])
    notes = data.get('completion_notes', task['completion_notes'])
    pr_link = data.get('pr_link', task['pr_link'])
    
    act_h = float(data.get('actual_hours', task['actual_hours'] or 0))
    act_m = int(data.get('actual_minutes', task['actual_minutes'] or 0))
    act_total = round(act_h + (act_m / 60.0), 2)
    
    efficiency = task['efficiency']
    completed_at = task['completed_at']
    started_at = task['started_at']
    
    if status == 'In Progress' and not started_at:
        started_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    if status == 'Completed':
        completed_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alloc_total = task['allocated_total_hours']
        if act_total > 0 and alloc_total > 0:
            efficiency = round((alloc_total / act_total) * 100, 1)
        elif alloc_total > 0 and act_total == 0:
            efficiency = 100.0
            
    cursor.execute('''
        UPDATE tasks SET
            status = ?,
            actual_hours = ?,
            actual_minutes = ?,
            actual_total_hours = ?,
            efficiency = ?,
            completion_notes = ?,
            pr_link = ?,
            started_at = ?,
            completed_at = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        status, act_h, act_m, act_total, efficiency,
        notes, pr_link, started_at, completed_at, task_id
    ))
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)

def delete_task(task_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def get_analytics():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM tasks')
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "Completed"')
    completed_tasks = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "In Progress"')
    in_progress_tasks = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "Assigned"')
    assigned_tasks = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(allocated_total_hours), SUM(actual_total_hours) FROM tasks WHERE status = "Completed"')
    hours_row = cursor.fetchone()
    total_allocated_hours = round(hours_row[0] or 0, 1)
    total_actual_hours = round(hours_row[1] or 0, 1)
    
    cursor.execute('SELECT AVG(efficiency) FROM tasks WHERE status = "Completed" AND efficiency IS NOT NULL')
    avg_eff_row = cursor.fetchone()
    avg_efficiency = round(avg_eff_row[0] or 0, 1)
    
    cursor.execute('''
        SELECT 
            u.id,
            u.name,
            u.email,
            u.role,
            u.designation,
            u.avatar_color,
            COUNT(t.id) as total_tasks,
            SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
            SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) as active_tasks,
            SUM(CASE WHEN t.status = 'Completed' THEN t.allocated_total_hours ELSE 0 END) as sum_allocated_hours,
            SUM(CASE WHEN t.status = 'Completed' THEN t.actual_total_hours ELSE 0 END) as sum_actual_hours,
            AVG(CASE WHEN t.status = 'Completed' AND t.efficiency IS NOT NULL THEN t.efficiency ELSE NULL END) as avg_efficiency
        FROM users u
        LEFT JOIN tasks t ON u.id = t.assignee_id
        WHERE u.is_verified = 1
        GROUP BY u.id
        ORDER BY avg_efficiency DESC, completed_tasks DESC
    ''')
    
    leaderboard = []
    for row in cursor.fetchall():
        r_dict = dict(row)
        r_dict['avg_efficiency'] = round(r_dict['avg_efficiency'] or 0, 1)
        r_dict['sum_allocated_hours'] = round(r_dict['sum_allocated_hours'] or 0, 1)
        r_dict['sum_actual_hours'] = round(r_dict['sum_actual_hours'] or 0, 1)
        
        eff = r_dict['avg_efficiency']
        if r_dict['completed_tasks'] == 0:
            badge = 'No Completed Tasks'
            badge_class = 'badge-neutral'
        elif eff >= 120:
            badge = '🚀 Super Fast'
            badge_class = 'badge-success-glow'
        elif eff >= 100:
            badge = '🎯 Optimal'
            badge_class = 'badge-success'
        elif eff >= 80:
            badge = '⚡ Acceptable'
            badge_class = 'badge-warning'
        else:
            badge = '⚠️ Overrun'
            badge_class = 'badge-danger'
            
        r_dict['performance_badge'] = badge
        r_dict['badge_class'] = badge_class
        leaderboard.append(r_dict)
        
    conn.close()
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'assigned_tasks': assigned_tasks,
        'total_allocated_hours': total_allocated_hours,
        'total_actual_hours': total_actual_hours,
        'avg_efficiency': avg_efficiency,
        'leaderboard': leaderboard
    }

def log_email(task_id, recipient_email, recipient_name, subject, body_html, status='SENT', error_message=''):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO email_logs (task_id, recipient_email, recipient_name, subject, body_html, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (task_id, recipient_email, recipient_name, subject, body_html, status, error_message))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id

def get_email_logs(limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, t.title as task_title 
        FROM email_logs e
        LEFT JOIN tasks t ON e.task_id = t.id
        ORDER BY e.sent_at DESC
        LIMIT ?
    ''', (limit,))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs

def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM settings')
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()
    return settings

def save_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()
