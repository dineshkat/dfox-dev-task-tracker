import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import db
import datetime

def generate_verification_email_html(user, otp_code):
    user_name = user.get('name', 'Team Member')
    user_email = user.get('email', '')
    role = user.get('role', 'Developer')
    designation = user.get('designation', '')
    token = user.get('verification_token', '')
    
    verify_url = f"http://localhost:8000/verify?token={token}&email={user_email}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Verify Your DFOX MEDIA Account</title>
      <style>
        body {{
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          background-color: #f4f6fb;
          margin: 0;
          padding: 24px;
          color: #1e293b;
        }}
        .container {{
          max-width: 560px;
          margin: 0 auto;
          background: #ffffff;
          border-radius: 16px;
          overflow: hidden;
          border: 1px solid #e2e8f0;
          box-shadow: 0 10px 30px rgba(42, 8, 69, 0.08);
        }}
        .header {{
          background: linear-gradient(135deg, #2A0845 0%, #6441A5 45%, #D6249F 85%, #FF007A 100%);
          padding: 32px 24px;
          text-align: center;
          color: #ffffff;
        }}
        .header h1 {{
          margin: 0;
          font-size: 22px;
          font-weight: 900;
          letter-spacing: 1.5px;
          text-transform: uppercase;
        }}
        .header p {{
          margin: 6px 0 0 0;
          font-size: 12px;
          opacity: 0.95;
          letter-spacing: 2px;
          font-weight: 600;
        }}
        .content {{
          padding: 32px 24px;
          text-align: center;
        }}
        .greeting {{
          font-size: 19px;
          font-weight: 800;
          color: #0f172a;
          margin-bottom: 12px;
        }}
        .desc {{
          color: #475569;
          font-size: 14px;
          line-height: 1.6;
          margin: 0 0 24px 0;
        }}
        .otp-box {{
          background: #f8fafc;
          border: 2px dashed #6441A5;
          border-radius: 12px;
          padding: 20px;
          margin: 24px auto;
          max-width: 320px;
        }}
        .otp-label {{
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: #64748b;
          font-weight: 700;
          margin-bottom: 8px;
        }}
        .otp-code {{
          font-family: 'Courier New', monospace;
          font-size: 32px;
          font-weight: 900;
          letter-spacing: 8px;
          color: #D81B60;
        }}
        .btn {{
          display: inline-block;
          background: linear-gradient(135deg, #6441A5 0%, #D81B60 100%);
          color: #ffffff !important;
          text-decoration: none;
          padding: 13px 32px;
          font-weight: 700;
          font-size: 14px;
          border-radius: 8px;
          box-shadow: 0 4px 14px rgba(216, 27, 96, 0.3);
          margin-top: 16px;
        }}
        .footer {{
          text-align: center;
          padding: 20px;
          font-size: 12px;
          color: #64748b;
          border-top: 1px solid #e2e8f0;
          background: #f8fafc;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>DFOX MEDIA</h1>
          <p>DEV TASK TRACKER &bull; ACCOUNT VERIFICATION</p>
        </div>
        <div class="content">
          <div class="greeting">Welcome, {user_name}!</div>
          <p class="desc">
            Your account has been created with role <strong>{role}</strong> ({designation}).<br>
            Please use the 6-digit verification code below to verify your email and activate your account:
          </p>
          
          <div class="otp-box">
            <div class="otp-label">Verification OTP Code</div>
            <div class="otp-code">{otp_code}</div>
          </div>
          
          <p style="font-size: 13px; color: #64748b; margin-top: 16px;">
            Enter this code on the verification screen to complete your registration.
          </p>
        </div>
        <div class="footer">
          &copy; {datetime.datetime.now().year} DFOX MEDIA &bull; Design &bull; Digital &bull; Development.
        </div>
      </div>
    </body>
    </html>
    """
    return html

def send_verification_email(user, otp_code):
    settings = db.get_settings()
    recipient_email = user.get('email')
    recipient_name = user.get('name')
    
    subject = f"[DFOX Media Tracker] Your Account Verification Code: {otp_code}"
    body_html = generate_verification_email_html(user, otp_code)
    
    smtp_enabled = settings.get('smtp_enabled', 'false').lower() == 'true'
    smtp_host = settings.get('smtp_host', '')
    smtp_port = int(settings.get('smtp_port', 587))
    smtp_user = settings.get('smtp_user', '')
    smtp_pass = settings.get('smtp_pass', '')
    smtp_from_email = settings.get('smtp_from_email', smtp_user or 'no-reply@dfoxmedia.com')
    smtp_from_name = settings.get('smtp_from_name', 'DFOX Media Tracker')
    use_tls = settings.get('smtp_tls', 'true').lower() == 'true'
    
    if smtp_enabled and smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'"{smtp_from_name}" <{smtp_from_email}>'
            msg['To'] = f'"{recipient_name}" <{recipient_email}>'
            
            text_part = MIMEText(f"Hello {recipient_name},\n\nYour DFOX Task Tracker verification code is: {otp_code}\n\nEnter this code to verify your account.", 'plain')
            html_part = MIMEText(body_html, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            if smtp_port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=10) as server:
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_from_email, recipient_email, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    if use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_from_email, recipient_email, msg.as_string())
                    
            db.log_email(None, recipient_email, recipient_name, subject, body_html, status='SENT')
            return {'success': True, 'mode': 'SMTP_DELIVERED', 'message': f'Verification email sent to {recipient_email}'}
        except Exception as e:
            error_msg = str(e)
            db.log_email(None, recipient_email, recipient_name, subject, body_html, status='FAILED', error_message=error_msg)
            return {'success': False, 'mode': 'SMTP_FAILED', 'error': error_msg}
    else:
        # Simulated log mode
        db.log_email(None, recipient_email, recipient_name, subject, body_html, status='SIMULATED', error_message=f'Verification OTP: {otp_code}. Safe simulation mode.')
        return {'success': True, 'mode': 'SIMULATED', 'otp': otp_code, 'message': f'Verification code {otp_code} logged in Email Center.'}

def generate_task_assignment_email_html(task, member):
    task_title = task.get('title', 'New Assigned Task')
    task_desc = task.get('description', 'No additional description provided.')
    priority = task.get('priority', 'Medium')
    allocated_h = task.get('allocated_hours', 0)
    allocated_m = task.get('allocated_minutes', 0)
    due_date = task.get('due_date', 'Not specified')
    created_by = task.get('created_by', 'Team Lead')
    member_name = member.get('name', 'Team Member')
    
    priority_styles = {
        'Urgent': 'background: #ffe4e6; color: #e11d48; border: 1px solid #fecdd3;',
        'High': 'background: #ffedd5; color: #ea580c; border: 1px solid #fed7aa;',
        'Medium': 'background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff;',
        'Low': 'background: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd;'
    }
    p_style = priority_styles.get(priority, 'background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff;')
    
    allocated_str = f"{int(allocated_h)} hrs" if allocated_h > 0 else ""
    if allocated_m > 0:
        allocated_str += f" {allocated_m} mins"
    if not allocated_str:
        allocated_str = "0 mins"
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>New Task Assignment - DFOX MEDIA</title>
      <style>
        body {{
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          background-color: #f4f6fb;
          margin: 0;
          padding: 24px;
          color: #1e293b;
        }}
        .container {{
          max-width: 600px;
          margin: 0 auto;
          background: #ffffff;
          border-radius: 16px;
          overflow: hidden;
          border: 1px solid #e2e8f0;
          box-shadow: 0 10px 30px rgba(42, 8, 69, 0.08);
        }}
        .header {{
          background: linear-gradient(135deg, #2A0845 0%, #6441A5 45%, #D6249F 85%, #FF007A 100%);
          padding: 32px 24px;
          text-align: center;
          color: #ffffff;
        }}
        .header h1 {{
          margin: 0;
          font-size: 24px;
          font-weight: 900;
          letter-spacing: 1.5px;
          text-transform: uppercase;
        }}
        .header p {{
          margin: 6px 0 0 0;
          font-size: 13px;
          opacity: 0.95;
          letter-spacing: 2px;
          font-weight: 600;
        }}
        .content {{
          padding: 28px 24px;
        }}
        .greeting {{
          font-size: 18px;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 14px;
        }}
        .task-card {{
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-left: 4px solid #D81B60;
          border-radius: 10px;
          padding: 20px;
          margin: 20px 0;
        }}
        .task-title {{
          font-size: 20px;
          font-weight: 800;
          color: #0f172a;
          margin: 0 0 10px 0;
        }}
        .task-desc {{
          font-size: 14px;
          color: #475569;
          line-height: 1.6;
          white-space: pre-wrap;
          margin: 0 0 18px 0;
        }}
        .meta-grid {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          border-top: 1px solid #e2e8f0;
          padding-top: 16px;
        }}
        .meta-item {{
          font-size: 13px;
        }}
        .meta-label {{
          color: #64748b;
          display: block;
          margin-bottom: 4px;
          font-size: 11px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: 0.5px;
        }}
        .meta-value {{
          font-weight: 700;
          color: #0f172a;
        }}
        .badge {{
          display: inline-block;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 800;
        }}
        .badge-time {{
          background: #f3e8ff;
          color: #6441a5;
          border: 1px solid #d8b4fe;
        }}
        .action-container {{
          text-align: center;
          margin: 30px 0 10px 0;
        }}
        .btn {{
          display: inline-block;
          background: linear-gradient(135deg, #6441A5 0%, #D81B60 100%);
          color: #ffffff !important;
          text-decoration: none;
          padding: 12px 28px;
          font-weight: 700;
          font-size: 14px;
          border-radius: 8px;
          box-shadow: 0 4px 14px rgba(216, 27, 96, 0.3);
        }}
        .footer {{
          text-align: center;
          padding: 20px;
          font-size: 12px;
          color: #64748b;
          border-top: 1px solid #e2e8f0;
          background: #f8fafc;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>DFOX MEDIA</h1>
          <p>DESIGN &bull; DIGITAL &bull; DEVELOPMENT</p>
        </div>
        <div class="content">
          <div class="greeting">Hello {member_name},</div>
          <p style="color: #475569; font-size: 14px; line-height: 1.5; margin: 0 0 16px 0;">
            A new development task has been assigned to you by <strong>{created_by}</strong>. 
            Please review the requirements and allocated duration below:
          </p>
          
          <div class="task-card">
            <div class="task-title">{task_title}</div>
            <div class="task-desc">{task_desc}</div>
            
            <div class="meta-grid">
              <div class="meta-item">
                <span class="meta-label">Allocated Duration</span>
                <span class="badge badge-time">⏱️ {allocated_str}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Priority</span>
                <span class="badge" style="{p_style}">{priority}</span>
              </div>
              <div class="meta-item" style="margin-top: 10px;">
                <span class="meta-label">Due Date</span>
                <span class="meta-value" style="color: #e11d48;">📅 {due_date or 'No deadline'}</span>
              </div>
            </div>
          </div>
          
          <p style="font-size: 13px; color: #64748b; line-height: 1.5;">
            💡 <strong>Efficiency Tip:</strong> Log your active time in the developer workspace. Your efficiency score is computed upon task completion based on allocated target duration vs actual time spent.
          </p>
          
          <div class="action-container">
            <a href="http://localhost:8000" class="btn">Open Task Dashboard &rarr;</a>
          </div>
        </div>
        <div class="footer">
          &copy; {datetime.datetime.now().year} DFOX MEDIA Development Tracker. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    """
    return html

def send_task_notification(task, member):
    settings = db.get_settings()
    recipient_email = member.get('email')
    recipient_name = member.get('name')
    task_id = task.get('id')
    task_title = task.get('title')
    
    subject = f"[DFOX Dev Tracker] New Task Assigned: {task_title}"
    body_html = generate_task_assignment_email_html(task, member)
    
    smtp_enabled = settings.get('smtp_enabled', 'false').lower() == 'true'
    smtp_host = settings.get('smtp_host', '')
    smtp_port = int(settings.get('smtp_port', 587))
    smtp_user = settings.get('smtp_user', '')
    smtp_pass = settings.get('smtp_pass', '')
    smtp_from_email = settings.get('smtp_from_email', smtp_user or 'no-reply@dfoxmedia.com')
    smtp_from_name = settings.get('smtp_from_name', 'DFOX Media Tracker')
    use_tls = settings.get('smtp_tls', 'true').lower() == 'true'
    
    if smtp_enabled and smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'"{smtp_from_name}" <{smtp_from_email}>'
            msg['To'] = f'"{recipient_name}" <{recipient_email}>'
            
            text_part = MIMEText(f"Hello {recipient_name},\n\nYou have been assigned a new task: {task_title}\nAllocated Time: {task.get('allocated_hours', 0)}h {task.get('allocated_minutes', 0)}m\nDue Date: {task.get('due_date')}\n\nCheck your DFOX dashboard.", 'plain')
            html_part = MIMEText(body_html, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            if smtp_port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=10) as server:
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_from_email, recipient_email, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    if use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_from_email, recipient_email, msg.as_string())
                    
            db.log_email(task_id, recipient_email, recipient_name, subject, body_html, status='SENT')
            return {'success': True, 'mode': 'SMTP_DELIVERED', 'message': f'Email successfully dispatched to {recipient_email}'}
        except Exception as e:
            error_msg = str(e)
            db.log_email(task_id, recipient_email, recipient_name, subject, body_html, status='FAILED', error_message=error_msg)
            return {'success': False, 'mode': 'SMTP_FAILED', 'error': error_msg}
    else:
        db.log_email(task_id, recipient_email, recipient_name, subject, body_html, status='SIMULATED', error_message='SMTP not active or in sandbox mode. Email preview captured.')
        return {'success': True, 'mode': 'SIMULATED', 'message': f'Notification recorded in email center for {recipient_email}'}

def test_smtp_connection(host, port, user, password, use_tls=True, test_recipient=None):
    try:
        port = int(port)
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=10) as server:
                server.login(user, password)
                if test_recipient:
                    msg = MIMEText('Test email from DFOX Media Task Tracker SMTP configuration test.', 'plain')
                    msg['Subject'] = 'DFOX Media SMTP Test'
                    msg['From'] = user
                    msg['To'] = test_recipient
                    server.sendmail(user, test_recipient, msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                server.login(user, password)
                if test_recipient:
                    msg = MIMEText('Test email from DFOX Media Task Tracker SMTP configuration test.', 'plain')
                    msg['Subject'] = 'DFOX Media SMTP Test'
                    msg['From'] = user
                    msg['To'] = test_recipient
                    server.sendmail(user, test_recipient, msg.as_string())
        return {'success': True, 'message': 'SMTP credentials and connection verified successfully!'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
