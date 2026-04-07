import os
from datetime import date, datetime, timedelta

from celery import Celery
from celery.schedules import crontab

from models import Appointment, DoctorProfile, ExportRequest, db
from utils import (
    build_doctor_monthly_html,
    build_patient_export,
    ensure_export_folder,
    format_date,
    format_time,
)
from mail import send_email

celery_app = Celery(__name__)


def init_celery(app):
    broker_url = app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = app.config.get("CELERY_RESULT_BACKEND", broker_url)

    celery_app.conf.update(
        broker_url=broker_url,
        result_backend=result_backend,
        timezone="Asia/Kolkata",
        beat_schedule={
            "daily-patient-reminder": {
                "task": "celery_app.send_daily_reminders",
                "schedule": crontab(hour=8, minute=0),
            },
            "monthly-doctor-report": {
                "task": "celery_app.send_monthly_reports",
                "schedule": crontab(hour=9, minute=0, day_of_month=1),
            },
        },
    )

    class FlaskTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = FlaskTask
    return celery_app


@celery_app.task(name="celery_app.send_daily_reminders")
def send_daily_reminders():
    today = date.today()
    appointments = Appointment.query.filter_by(date=today, status="booked").all()

    for appointment in appointments:
        patient_email = appointment.patient.user.email
        doctor_name = appointment.doctor.user.name
        message = (
            f"Reminder: You have an appointment with Dr. {doctor_name} on "
            f"{format_date(appointment.date)} at {format_time(appointment.time)}."
        )
        send_email("Hospital Appointment Reminder", message, [patient_email])

    return {"processed": len(appointments)}


@celery_app.task(name="celery_app.send_monthly_reports")
def send_monthly_reports():
    first_day_this_month = date.today().replace(day=1)
    last_day_previous_month = first_day_this_month - timedelta(days=1)
    first_day_previous_month = last_day_previous_month.replace(day=1)

    doctors = DoctorProfile.query.filter_by(is_active=True).all()
    report_count = 0

    for doctor in doctors:
        appointments = (
            Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.date >= first_day_previous_month,
                Appointment.date <= last_day_previous_month,
            )
            .order_by(Appointment.date.desc(), Appointment.time.desc())
            .all()
        )

        subject = f"Monthly Report - {doctor.user.name}"
        body = (
            f"Monthly report for {doctor.user.name} from "
            f"{first_day_previous_month} to {last_day_previous_month}"
        )
        html_body = build_doctor_monthly_html(doctor.user.name, appointments)
        send_email(subject, body, [doctor.user.email], html_body=html_body)
        report_count += 1

    return {"processed": report_count}


@celery_app.task(name="celery_app.generate_patient_export")
def generate_patient_export(patient_id, export_request_id):
    export_request = ExportRequest.query.get(export_request_id)
    if not export_request:
        return {"message": "Export request not found"}

    patient_appointments = (
        Appointment.query.filter_by(patient_id=patient_id)
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .all()
    )

    export_folder = ensure_export_folder()
    file_name = f"patient_{patient_id}_export_{export_request_id}.csv"
    export_path = os.path.join(export_folder, file_name)

    build_patient_export(export_path, patient_appointments)

    export_request.status = "completed"
    export_request.file_path = export_path
    export_request.completed_at = datetime.utcnow()
    db.session.commit()

    patient_email = export_request.patient.user.email
    send_email(
        "Treatment export ready",
        f"Your treatment export is ready: {file_name}",
        [patient_email],
    )

    return {"message": "Export generated", "file_name": file_name}


if __name__ == "__main__":
    from app import app
    print("=========================================")
    print("Hospital Management System - Celery App")
    print("=========================================")
    print("This file acts as the Celery module. To start the background worker, please run:")
    print("    .\\venv\\Scripts\\celery -A celery_app worker -P solo --loglevel=info")
    print("\nRunning a quick local test of the background jobs synchronously...")
    with app.app_context():
        try:
            print("1. Testing Daily Reminders...")
            res1 = send_daily_reminders()
            print(f"   Success! Processed: {res1.get('processed')} reminders.")
            
            print("2. Testing Monthly Reports...")
            res2 = send_monthly_reports()
            print(f"   Success! Processed: {res2.get('processed')} doctors' reports.")
            
            print("\nTests completed smoothly!")
            
        except Exception as e:
            print(f"Test failed with error: {str(e)}")