import http.server
import socketserver
import urllib.parse
import json
import os
import mimetypes
import csv
import io
import db
import mailer

PORT = int(os.environ.get('PORT', 8000))
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')

class DFOXTrackerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def _send_json(self, data, status_code=200):
        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(response_bytes)

    def _read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
            return json.loads(body)
        return {}

    def _get_current_user(self):
        auth_header = self.headers.get('Authorization', '')
        token = ''
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '').strip()
        if not token:
            # Check cookie
            cookie_header = self.headers.get('Cookie', '')
            for cookie in cookie_header.split(';'):
                if 'dfox_session=' in cookie:
                    token = cookie.split('dfox_session=')[1].strip()
        if token:
            return db.get_user_by_session(token)
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # 1-Click Email Verification Link
        if path == '/verify':
            token = query.get('token', [None])[0]
            if token:
                success, msg = db.verify_user_token(token)
                self.send_response(302)
                self.send_header('Location', f'/?verified={1 if success else 0}&msg={urllib.parse.quote(msg)}')
                self.end_headers()
                return

        # API Endpoints
        if path.startswith('/api/'):
            # Current logged in user
            if path == '/api/auth/me':
                user = self._get_current_user()
                if user:
                    return self._send_json({'user': user})
                return self._send_json({'user': None})

            elif path == '/api/tasks':
                assignee_id = query.get('assignee_id', [None])[0]
                status = query.get('status', [None])[0]
                search = query.get('search', [None])[0]
                tasks = db.get_all_tasks(assignee_id=assignee_id, status=status, search=search)
                return self._send_json({'tasks': tasks})
                
            elif path.startswith('/api/tasks/'):
                task_id = path.replace('/api/tasks/', '')
                if task_id.isdigit():
                    task = db.get_task_by_id(int(task_id))
                    if task:
                        return self._send_json({'task': task})
                    return self._send_json({'error': 'Task not found'}, 404)

            elif path == '/api/members':
                members = db.get_all_members()
                return self._send_json({'members': members})

            elif path == '/api/analytics':
                analytics = db.get_analytics()
                return self._send_json(analytics)

            elif path == '/api/email/logs':
                limit = int(query.get('limit', [50])[0])
                logs = db.get_email_logs(limit=limit)
                return self._send_json({'logs': logs})

            elif path == '/api/settings':
                settings = db.get_settings()
                safe_settings = dict(settings)
                if 'smtp_pass' in safe_settings and safe_settings['smtp_pass']:
                    safe_settings['smtp_pass_set'] = True
                    safe_settings['smtp_pass'] = '••••••••'
                else:
                    safe_settings['smtp_pass_set'] = False
                return self._send_json({'settings': safe_settings})

            elif path == '/api/export':
                tasks = db.get_all_tasks()
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow([
                    'Task ID', 'Title', 'Priority', 'Assignee Name', 
                    'Assignee Email', 'Allocated Hours', 'Actual Hours', 
                    'Efficiency (%)', 'Status', 'Due Date', 'Assigned At', 'Completed At'
                ])
                for t in tasks:
                    writer.writerow([
                        t['id'],
                        t['title'],
                        t['priority'],
                        t.get('assignee_name', 'Unassigned'),
                        t.get('assignee_email', ''),
                        t['allocated_total_hours'],
                        t['actual_total_hours'],
                        f"{t['efficiency']}%" if t['efficiency'] is not None else 'N/A',
                        t['status'],
                        t['due_date'],
                        t['assigned_at'],
                        t['completed_at'] or ''
                    ])
                csv_bytes = output.getvalue().encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="dfox_tasks_efficiency.csv"')
                self.send_header('Content-Length', str(len(csv_bytes)))
                self.end_headers()
                self.wfile.write(csv_bytes)
                return

            return self._send_json({'error': 'Endpoint not found'}, 404)

        # Static files fallback
        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path.startswith('/api/'):
            body = self._read_json_body()

            # ----------------- Auth Endpoints -----------------
            if path == '/api/auth/signup':
                name = body.get('name', '').strip()
                email = body.get('email', '').strip()
                password = body.get('password', '')
                designation = body.get('designation', '').strip()

                if not name or not email or not password:
                    return self._send_json({'error': 'Name, Email, and Password are required'}, 400)

                user, err = db.create_user(name, email, password, designation)
                if err:
                    return self._send_json({'error': err}, 400)

                # Send verification email with 6-digit OTP
                otp_code = user.get('verification_otp')
                email_result = mailer.send_verification_email(user, otp_code)

                return self._send_json({
                    'message': 'Account created! Please check your email for the verification code.',
                    'email': email,
                    'email_result': email_result
                }, 201)

            elif path == '/api/auth/verify':
                email = body.get('email', '').strip()
                otp = body.get('otp', '').strip()

                if not email or not otp:
                    return self._send_json({'error': 'Email and verification code are required'}, 400)

                success, msg = db.verify_user_otp(email, otp)
                if success:
                    return self._send_json({'success': True, 'message': msg})
                return self._send_json({'error': msg}, 400)

            elif path == '/api/auth/resend-verification':
                email = body.get('email', '').strip()
                if not email:
                    return self._send_json({'error': 'Email is required'}, 400)

                user, err = db.resend_otp(email)
                if err:
                    return self._send_json({'error': err}, 400)

                otp_code = user.get('verification_otp')
                email_result = mailer.send_verification_email(user, otp_code)
                return self._send_json({
                    'message': f'A fresh verification code has been dispatched to {email}',
                    'email_result': email_result
                })

            elif path == '/api/auth/login':
                email = body.get('email', '').strip()
                password = body.get('password', '')

                if not email or not password:
                    return self._send_json({'error': 'Email and Password are required'}, 400)

                auth_data, err = db.authenticate_user(email, password)
                if err == 'UNVERIFIED_ACCOUNT':
                    # Send fresh OTP
                    user = db.get_db().cursor().execute('SELECT * FROM users WHERE email = ?', (email.lower(),)).fetchone()
                    if user and user['verification_otp']:
                        mailer.send_verification_email(dict(user), user['verification_otp'])
                    return self._send_json({
                        'error': 'Your email is not verified yet. Please enter the verification code sent to your email.',
                        'unverified': True,
                        'email': email
                    }, 403)
                elif err:
                    return self._send_json({'error': err}, 401)

                return self._send_json({
                    'message': 'Login successful',
                    'user': auth_data['user'],
                    'token': auth_data['token']
                })

            elif path == '/api/auth/logout':
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header.replace('Bearer ', '').strip()
                    db.delete_session(token)
                return self._send_json({'message': 'Logged out successfully'})

            # ----------------- Tasks & Settings Endpoints -----------------
            elif path == '/api/tasks':
                if not body.get('title'):
                    return self._send_json({'error': 'Task title is required'}, 400)
                    
                # Current user who created the task
                current_user = self._get_current_user()
                if current_user:
                    body['created_by'] = f"{current_user['name']} ({current_user['role']})"
                else:
                    body['created_by'] = 'Team Lead'
                    
                task_id = db.create_task(body)
                task = db.get_task_by_id(task_id)
                
                send_email = body.get('send_email', True)
                email_result = None
                if send_email and task.get('assignee_id'):
                    member = {
                        'name': task.get('assignee_name'),
                        'email': task.get('assignee_email')
                    }
                    if member['email']:
                        email_result = mailer.send_task_notification(task, member)
                        
                return self._send_json({'task': task, 'email_result': email_result}, 201)

            elif path == '/api/email/resend':
                task_id = body.get('task_id')
                if not task_id:
                    return self._send_json({'error': 'task_id required'}, 400)
                task = db.get_task_by_id(int(task_id))
                if not task:
                    return self._send_json({'error': 'Task not found'}, 404)
                member = {
                    'name': task.get('assignee_name'),
                    'email': task.get('assignee_email')
                }
                result = mailer.send_task_notification(task, member)
                return self._send_json({'success': True, 'result': result})

            elif path == '/api/settings':
                for key, val in body.items():
                    if key == 'smtp_pass' and val == '••••••••':
                        continue
                    db.save_setting(key, val)
                return self._send_json({'message': 'Settings saved successfully'})

            elif path == '/api/settings/test-smtp':
                host = body.get('smtp_host')
                port = body.get('smtp_port', 587)
                user = body.get('smtp_user')
                password = body.get('smtp_pass')
                use_tls = body.get('smtp_tls', True)
                test_to = body.get('test_recipient')
                
                if password == '••••••••' or not password:
                    settings = db.get_settings()
                    password = settings.get('smtp_pass', '')
                    
                result = mailer.test_smtp_connection(host, port, user, password, use_tls, test_to)
                return self._send_json(result)

            return self._send_json({'error': 'Endpoint not found'}, 404)

        return self._send_json({'error': 'Invalid request'}, 400)

    def do_PUT(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path.startswith('/api/tasks/'):
            task_id = path.replace('/api/tasks/', '')
            body = self._read_json_body()

            if task_id.isdigit():
                real_id = int(task_id)
                updated_task = db.update_task_status_and_time(real_id, body)
                if updated_task:
                    return self._send_json({'task': updated_task})
                return self._send_json({'error': 'Task not found'}, 404)

        return self._send_json({'error': 'Invalid request'}, 400)

    def do_DELETE(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path.startswith('/api/tasks/'):
            task_id = path.replace('/api/tasks/', '')
            if task_id.isdigit():
                db.delete_task(int(task_id))
                return self._send_json({'success': True, 'message': 'Task deleted'})

        elif path.startswith('/api/members/'):
            member_id = path.replace('/api/members/', '')
            if member_id.isdigit():
                db.delete_member(int(member_id))
                return self._send_json({'success': True, 'message': 'Member removed'})

        return self._send_json({'error': 'Endpoint not found'}, 404)

def run_server():
    db.init_db()
    
    mimetypes.add_type('application/javascript', '.js')
    mimetypes.add_type('text/css', '.css')
    mimetypes.add_type('image/png', '.png')
    mimetypes.add_type('image/svg+xml', '.svg')

    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReusableTCPServer(("", PORT), DFOXTrackerHandler) as httpd:
        print(f"🚀 DFOX Dev Task Tracker server running at: http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()

if __name__ == '__main__':
    run_server()
