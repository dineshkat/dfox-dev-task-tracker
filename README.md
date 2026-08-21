# DFOX MEDIA &bull; Development Task Tracker &amp; Efficiency Hub

A dedicated, lightweight, and high-performance task management and developer efficiency tracking tool built for **DFOX MEDIA** (Design &bull; Digital &bull; Development).

![DFOX MEDIA](public/assets/logo.png)

---

## 🌟 Key Features

### 1. 👑 Department Head & Team Lead Task Assignment
- **Detailed Specifications**: Assign tasks with Title, Requirements / Description, Category (Frontend, Backend, UI/UX, API, DevOps, Database, QA), Priority (Urgent, High, Medium, Low), and Target Due Date.
- **Time Allocation**: Specify required duration per task in **Hours & Minutes** (e.g., 3 hrs 30 mins).
- **Assignee Selection**: Direct assignment to specific development team members with profile avatar, role, and company email.

### 2. 📧 Automated Email Notifications
- Upon assigning a task, an automated **responsive HTML email** styled with the DFOX purple-magenta brand theme is sent to the developer's company email.
- The email includes:
  - Task Title & Detailed Requirements
  - Allocated Duration (⏱️)
  - Priority Badge & Due Date
  - Quick action button to access the dashboard
- **SMTP Support**: Works with standard company SMTP (Gmail, Microsoft 365 / Outlook, AWS SES, Zoho, Custom SMTP) with STARTTLS/SSL, or runs in safe simulation mode with live in-app email preview.

### 3. 💻 Developer Workspace & Live Stopwatch
- Developers can filter to their personalized queue.
- **Live Built-in Stopwatch / Timer**: Developers can start, pause, and sync active time directly into tasks.
- **Task Status Progression**: `Assigned` &rarr; `In Progress` &rarr; `In Review` &rarr; `Completed`.
- Enter actual completion time (Hours & Minutes), attach GitHub Pull Request links, and submit completion notes.

### 4. ⚡ Automated Developer Efficiency Calculation
Efficiency is automatically calculated the moment a task is marked **Completed**:

$$\text{Efficiency \%} = \left(\frac{\text{Allocated Duration}}{\text{Actual Time Taken}}\right) \times 100$$

- **🚀 $\ge 120\%$ — Super Fast / Top Performer** (Completed well ahead of schedule)
- **🎯 $100\% - 119\%$ — Optimal Efficiency** (Delivered on target)
- **⚡ $80\% - 99\%$ — Acceptable** (Minor schedule delay)
- **⚠️ $< 80\%$ — Overrun** (Exceeded allocated time)

### 5. 🏆 Team Analytics & Leaderboard
- Real-time ranking of developers based on their average efficiency score and completed tasks.
- Metrics for total allocated hours vs. actual hours spent, and net time saved.
- **One-click CSV Export** (`📥 Export CSV`) for weekly/monthly management reports.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+** (Built-in standard libraries: `sqlite3`, `http.server`, `smtplib`, `json`). Zero external npm or pip dependencies required!

### Starting the Server
Run the startup script:
```bash
./start.sh
```
Or run directly:
```bash
python3 server.py
```

Open your browser and navigate to:
```
http://localhost:8000
```

---

## ⚙️ SMTP Email Configuration

To enable live email dispatch to real company email addresses:
1. Click the **⚙️ Settings** icon in the top navigation bar.
2. Check **Enable Live SMTP Email Dispatch**.
3. Fill in your SMTP details:
   - **SMTP Host**: e.g., `smtp.gmail.com` or `mail.dfoxmedia.com`
   - **SMTP Port**: `587` (TLS) or `465` (SSL)
   - **SMTP User**: e.g., `notifications@dfoxmedia.com`
   - **SMTP Password / App Password**: Your SMTP or Gmail App Password
   - **Sender Name**: `DFOX Media Dev Tracker`
   - **Sender From Email**: `no-reply@dfoxmedia.com`
4. Use **Test SMTP Connection** to verify delivery.
5. Click **Save Settings**.

*(Note: If SMTP is not configured, email alerts will still be logged and previewable under the **✉️ Email Center** tab).*

---

## 📁 Project Structure

```
DFOX Dev Task Tracker/
├── server.py              # Python HTTP REST API server & static file handler
├── db.py                  # SQLite database engine, tables & analytics
├── mailer.py              # HTML email generator & SMTP dispatcher
├── start.sh               # One-click startup script
├── README.md              # Project documentation
├── data/
│   └── dfox_tracker.db    # Persistent SQLite database
└── public/
    ├── index.html         # Main SPA interface
    ├── css/
    │   └── styles.css     # DFOX custom design system & gradients
    ├── js/
    │   ├── app.js         # Frontend controller, state & modals
    │   ├── timer.js       # Live stopwatch & time tracking
    │   └── api.js         # REST API client
    └── assets/
        └── logo.png       # DFOX MEDIA company logo
```

---
&copy; 2026 **DFOX MEDIA** &bull; Design &bull; Digital &bull; Development.
