"""The three batch jobs required by the spec.

  a. daily_reminder            — scheduled, nightly deadline nudges to students
  b. monthly_report            — scheduled, HTML activity report mailed to admin
  c. export_applications_csv   — user-triggered async CSV export + completion alert
"""

# ══════════════════════════════════════════════════════════════════════
# ── IMPORTS ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
import csv                                    # CSV file likhne ke liye standard library
import os                                     # file paths banane ke liye (folder + filename join karna)
from datetime import datetime, timedelta      # date/time calculations ke liye (deadline, timestamps)

from flask import current_app                 # Flask ka config (EXPORT_FOLDER, ADMIN_EMAIL) uthane ke liye

from extensions import celery, db             # celery = task register karne ka object, db = database (yaha directly use nahi ho raha)
from models import StudentProfile, PlacementDrive, Application   # database tables (models)
from tasks.mailer import send_email           # apna khud ka mail bhejne wala helper function


# ══════════════════════════════════════════════════════════════════════
# ── (a) DAILY REMINDER — har raat students ko deadline yaad dilana ───
# ══════════════════════════════════════════════════════════════════════

@celery.task(name='tasks.daily_reminder')   # ye function ek Celery scheduled task hai (roz 6pm chalega)
def daily_reminder():
    """Nudge students about drives closing soon that they have not applied to."""

    # Config se number of days uthao jitne din pehle warning deni hai (e.g. 3 din)
    window = current_app.config['REMINDER_WINDOW_DAYS']
    now = datetime.utcnow()   # abhi ka UTC time

    # ── Step 1: wo saari drives dhundo jo jald band hone wali hain ──
    closing_soon = (PlacementDrive.query
                    .filter(PlacementDrive.status == 'approved')            # sirf approved drives
                    .filter(PlacementDrive.deadline >= now)                 # jinki deadline abhi tak nahi aayi
                    .filter(PlacementDrive.deadline <= now + timedelta(days=window))  # aur window ke andar aa rahi hai
                    .all())

    # Agar koi drive band hone wali nahi hai, to kaam khatam — kisi ko mail mat bhejo
    if not closing_soon:
        return 'No drives closing soon — no reminders sent.'

    # ── Step 2: har active (blacklist nahi hue) student ko check karo ──
    students = StudentProfile.query.filter_by(is_blacklisted=False).all()
    sent = 0   # kitne students ko mail bheja uska counter

    for student in students:
        # Is student ne jin-jin drive-ids me already apply kar diya hai, unka set banao
        applied_ids = {a.drive_id for a in student.applications}

        # Sirf wo drives jinme student eligible hai AUR abhi tak apply nahi kiya
        pending = [d for d in closing_soon
                   if d.id not in applied_ids and d.check_eligibility(student) is None]
        if not pending:
            continue   # agar koi pending drive nahi hai to is student ko skip karo

        # ── Step 3: HTML table banao jisme pending drives ki list ho ──
        rows = ''.join(
            f'<tr><td>{d.job_title}</td><td>{d.company.company_name}</td>'
            f'<td>{d.deadline.strftime("%d %b %Y")}</td></tr>'
            for d in pending
        )
        # Poora email ka HTML content taiyar karo
        html = f"""
        <h3>Hello {student.name},</h3>
        <p>You have <b>{len(pending)}</b> placement drive(s) closing within
           {window} days that you have not applied to yet:</p>
        <table border="1" cellpadding="6" cellspacing="0">
          <tr><th>Job Title</th><th>Company</th><th>Deadline</th></tr>
          {rows}
        </table>
        <p>Log in to the Placement Portal to apply before the deadline.</p>
        """
        # ── Step 4: mail bhejo aur counter badhao ──
        send_email(student.user.email, 'Placement drives closing soon', html)
        sent += 1

    # Function ka summary return karo (Celery log/result me dikhega)
    return f'Reminders sent to {sent} student(s) about {len(closing_soon)} drive(s).'


# ══════════════════════════════════════════════════════════════════════
# ── (b) MONTHLY ACTIVITY REPORT — mahine ka summary admin ko bhejna ──
# ══════════════════════════════════════════════════════════════════════

@celery.task(name='tasks.monthly_report')   # ye bhi scheduled task hai (har mahine ki 1 tareek, 8am)
def monthly_report():
    """Build last month's activity report and mail it to the admin."""

    # ── Step 1: "pichhle mahine" ka date range nikalo ──
    now = datetime.utcnow()
    this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # is mahine ki 1 tareek, midnight
    last_month = (this_month - timedelta(days=1)).replace(day=1)                # pichhle mahine ki 1 tareek

    # ── Step 2: pichhle mahine ki drives aur applications database se nikalo ──
    drives = (PlacementDrive.query
              .filter(PlacementDrive.created_at >= last_month)
              .filter(PlacementDrive.created_at < this_month)
              .all())
    applications = (Application.query
                    .filter(Application.application_date >= last_month)
                    .filter(Application.application_date < this_month)
                    .all())

    # ── Step 3: kuch summary numbers calculate karo ──
    selected = [a for a in applications if a.status == 'selected']       # jinko job mil gayi
    shortlisted = [a for a in applications if a.status == 'shortlisted']  # jinka shortlist hua
    applicants = {a.student_id for a in applications}                    # kitne unique students ne apply kiya

    # ── Step 4: har drive ki ek row banao HTML table ke liye ──
    drive_rows = ''.join(
        f'<tr><td>{d.drive_name}</td><td>{d.company.company_name}</td>'
        f'<td>{d.job_title}</td><td>{len(d.applications)}</td>'
        f'<td>{sum(1 for a in d.applications if a.status == "selected")}</td></tr>'
        for d in drives
    ) or '<tr><td colspan="5">No drives were conducted this month.</td></tr>'
    # (agar ek bhi drive nahi thi to "No drives" wala message dikhega)

    # ── Step 5: poora HTML report banao ──
    html = f"""
    <html><body style="font-family:Arial,sans-serif">
      <h2>Monthly Placement Activity Report</h2>
      <p><b>Period:</b> {last_month.strftime('%B %Y')}</p>

      <h3>Summary</h3>
      <ul>
        <li>Drives conducted: <b>{len(drives)}</b></li>
        <li>Applications received: <b>{len(applications)}</b></li>
        <li>Distinct students who applied: <b>{len(applicants)}</b></li>
        <li>Students shortlisted: <b>{len(shortlisted)}</b></li>
        <li>Students selected: <b>{len(selected)}</b></li>
      </ul>

      <h3>Drive breakdown</h3>
      <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>Drive</th><th>Company</th><th>Job Title</th>
            <th>Applicants</th><th>Selected</th></tr>
        {drive_rows}
      </table>
    </body></html>
    """

    # ── Step 6: report ki ek copy disk pe bhi save kar do (backup ke liye) ──
    path = os.path.join(current_app.config['EXPORT_FOLDER'],
                        f'monthly_report_{last_month.strftime("%Y_%m")}.html')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(html)

    # ── Step 7: report ko admin ke email pe bhej do ──
    send_email(
        current_app.config['ADMIN_EMAIL'],
        f'Placement Activity Report — {last_month.strftime("%B %Y")}',
        html,
    )
    return f'Monthly report for {last_month.strftime("%B %Y")} generated and mailed.'


# ══════════════════════════════════════════════════════════════════════
# ── (c) USER-TRIGGERED CSV EXPORT — student apni history download kare ──
# ══════════════════════════════════════════════════════════════════════

# Har application status ka ek color (email me badge dikhane ke liye)
STATUS_COLORS = {
    'applied': '#3b82f6',       # blue
    'shortlisted': '#0ea5e9',   # sky blue
    'waiting': '#f59e0b',       # orange
    'selected': '#16a34a',      # green
    'rejected': '#dc2626',      # red
}


@celery.task(name='tasks.export_applications_csv')   # ye async task hai, student ke "Export" button dabane pe chalta hai
def export_applications_csv(student_id):
    """Export one student's placement history, then alert them by email."""

    # ── Step 1: student ko database se dhundo ──
    student = StudentProfile.query.get(student_id)
    if not student:
        raise ValueError(f'No student with id {student_id}')   # agar student hi nahi mila to error do

    # ── Step 2: CSV file ka naam aur path banao (timestamp ke saath, taaki unique rahe) ──
    stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'applications_{student.roll_number or student.id}_{stamp}.csv'
    path = os.path.join(current_app.config['EXPORT_FOLDER'], filename)

    # ── Step 3: is student ki saari applications database se nikalo (date ke hisaab se sorted) ──
    applications = (Application.query
                    .filter_by(student_id=student.id)
                    .order_by(Application.application_date)
                    .all())

    # ── Step 4: CSV ka header row (column names) ──
    header = [
        'Roll Number', 'Student Name', 'Email', 'Branch', 'CGPA',
        'Company Name', 'Drive Title', 'Job Title', 'Application Status',
        'Application Date', 'Deadline', 'Interview Mode', 'Remark',
    ]
    # Har application ke liye ek row banao (list ke andar list)
    rows = [[
        student.roll_number or student.id,
        student.name,
        student.user.email,
        student.branch,
        student.cgpa,
        a.drive.company.company_name,
        a.drive.drive_name,
        a.drive.job_title,
        a.status.title(),
        a.application_date.strftime('%Y-%m-%d'),
        a.drive.deadline.strftime('%Y-%m-%d'),
        a.interview_mode,
        a.remark,
    ] for a in applications]

    # ── Step 5: CSV file disk pe likho ──
    with open(path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(header)   # pehle header likho
        writer.writerows(rows)    # phir saari rows likho

    # ── Step 6: usi CSV file ko bytes me wapas padho (email attachment ke liye chahiye) ──
    with open(path, 'rb') as handle:
        csv_bytes = handle.read()

    # ── Step 7: email ke andar dikhane ke liye ek HTML table banao (preview jaisa) ──
    table_rows = ''.join(
        f"""<tr>
              <td style="padding:10px 14px;border-bottom:1px solid #eef0f3">{a.drive.company.company_name}</td>
              <td style="padding:10px 14px;border-bottom:1px solid #eef0f3">{a.drive.job_title}</td>
              <td style="padding:10px 14px;border-bottom:1px solid #eef0f3">{a.application_date.strftime('%d %b %Y')}</td>
              <td style="padding:10px 14px;border-bottom:1px solid #eef0f3">
                <span style="background:{STATUS_COLORS.get(a.status, '#6b7280')};color:#fff;
                             padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600">
                  {a.status.title()}
                </span>
              </td>
            </tr>"""
        for a in applications
    ) or '<tr><td colspan="4" style="padding:14px;color:#6b7280">No applications yet.</td></tr>'
    # (agar koi application hi nahi hai to "No applications yet" dikhega)

    # ── Step 8: poora email ka HTML design taiyar karo ──
    html = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;max-width:640px;margin:auto;
                background:#f4f6f9;padding:24px">
      <div style="background:#fff;border-radius:10px;overflow:hidden;
                  box-shadow:0 1px 3px rgba(0,0,0,0.08)">

        <div style="background:linear-gradient(90deg,#1f2937,#111827);padding:24px 28px">
          <h2 style="color:#fff;margin:0;font-size:20px">Placement Portal</h2>
          <p style="color:#cbd5e1;margin:4px 0 0;font-size:13px">Placement History Export</p>
        </div>

        <div style="padding:28px">
          <p style="font-size:15px;color:#111827">Hello <b>{student.name}</b>,</p>
          <p style="font-size:14px;color:#374151">
            Your placement history export is ready — <b>{len(applications)}</b>
            application(s) in total. The full CSV is attached to this email
            (<b>{filename}</b>), and you can also download it from your dashboard.
          </p>

          <table style="width:100%;border-collapse:collapse;margin-top:20px;
                         background:#fafbfc;border-radius:6px;overflow:hidden">
            <thead>
              <tr style="background:#f1f3f5;text-align:left">
                <th style="padding:10px 14px;font-size:12px;color:#6b7280;
                           text-transform:uppercase;letter-spacing:0.03em">Company</th>
                <th style="padding:10px 14px;font-size:12px;color:#6b7280;
                           text-transform:uppercase;letter-spacing:0.03em">Job Title</th>
                <th style="padding:10px 14px;font-size:12px;color:#6b7280;
                           text-transform:uppercase;letter-spacing:0.03em">Applied On</th>
                <th style="padding:10px 14px;font-size:12px;color:#6b7280;
                           text-transform:uppercase;letter-spacing:0.03em">Status</th>
              </tr>
            </thead>
            <tbody>{table_rows}</tbody>
          </table>

          <p style="font-size:12px;color:#9ca3af;margin-top:24px">
            Roll Number: {student.roll_number} &nbsp;·&nbsp; Branch: {student.branch}
            &nbsp;·&nbsp; CGPA: {student.cgpa}
          </p>
        </div>
      </div>
    </div>
    """

    # ── Step 9: student ko mail bhejo, CSV file ko attachment ke roop me jodo ──
    # Yahi wo "alert once done" hai jo spec me maanga gaya tha
    send_email(
        student.user.email,
        'Your placement history export is ready',
        html,
        attachments=[(filename, csv_bytes, 'csv')],
    )
    return filename   # Celery task result me filename return ho jayega (frontend isse poll karta hai)
