import csv
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

from flask import current_app, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash

from models import Department, DoctorAvailability, User, db


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or not user.is_active:
                return jsonify({"message": "User not found or inactive"}), 403

            claims = get_jwt()
            role = claims.get("role", user.role)
            if role not in allowed_roles:
                return jsonify({"message": "Access denied"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_current_user():
    user_id = get_jwt_identity()
    if not user_id:
        return None
    return User.query.get(int(user_id))


def create_user_token(user):
    from flask_jwt_extended import create_access_token

    return create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "name": user.name},
    )


def format_date(value):
    return value.isoformat() if value else None


def format_time(value):
    return value.strftime("%H:%M") if value else None


def format_datetime(value):
    return value.isoformat() if value else None


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def parse_optional_date(value):
    if not value:
        return None
    return parse_date(value)


def department_to_dict(department):
    return {
        "id": department.id,
        "name": department.name,
        "description": department.description,
        "doctor_count": len([doctor for doctor in department.doctors if doctor.is_active]),
    }


def doctor_to_dict(profile):
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": profile.user.name,
        "email": profile.user.email,
        "department_id": profile.department_id,
        "department_name": profile.department.name if profile.department else "",
        "specialization": profile.specialization,
        "qualification": profile.qualification,
        "phone_number": profile.phone_number,
        "bio": profile.bio,
        "experience_years": profile.experience_years,
        "is_active": profile.is_active and profile.user.is_active,
    }


def patient_to_dict(profile):
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": profile.user.name,
        "email": profile.user.email,
        "age": profile.age,
        "gender": profile.gender,
        "phone_number": profile.phone_number,
        "address": profile.address,
        "emergency_contact": profile.emergency_contact,
        "medical_history": profile.medical_history,
        "is_active": profile.is_active and profile.user.is_active,
    }


def treatment_to_dict(treatment):
    return {
        "id": treatment.id,
        "diagnosis": treatment.diagnosis,
        "prescription": treatment.prescription,
        "notes": treatment.notes,
        "next_visit_date": format_date(treatment.next_visit_date),
        "created_at": format_datetime(treatment.created_at),
    }


def appointment_to_dict(appointment):
    return {
        "id": appointment.id,
        "date": format_date(appointment.date),
        "time": format_time(appointment.time),
        "reason": appointment.reason,
        "status": appointment.status,
        "created_at": format_datetime(appointment.created_at),
        "updated_at": format_datetime(appointment.updated_at),
        "doctor": doctor_to_dict(appointment.doctor),
        "patient": patient_to_dict(appointment.patient),
        "treatment": treatment_to_dict(appointment.treatment)
        if appointment.treatment
        else None,
    }


def availability_to_dict(slot):
    return {
        "id": slot.id,
        "date": format_date(slot.date),
        "start_time": format_time(slot.start_time),
        "end_time": format_time(slot.end_time),
        "is_available": slot.is_available,
    }


def user_to_dict(user):
    data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }
    if user.role == "doctor" and user.doctor_profile:
        data["doctor_profile"] = doctor_to_dict(user.doctor_profile)
    if user.role == "patient" and user.patient_profile:
        data["patient_profile"] = patient_to_dict(user.patient_profile)
    return data


def is_slot_available(doctor_id, appointment_date, appointment_time):
    matching_slot = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date == appointment_date,
        DoctorAvailability.is_available.is_(True),
        DoctorAvailability.start_time <= appointment_time,
        DoctorAvailability.end_time > appointment_time,
    ).first()
    return matching_slot is not None


def clear_cache():
    try:
        from extensions import cache

        cache.clear()
    except Exception:
        pass


def seed_defaults():
    admin = User.query.filter_by(email="admin@gmail.com").first()
    if not admin:
        admin = User(
            name="Admin User",
            email="admin@gmail.com",
            role="admin",
            password=generate_password_hash("1234"),
            is_active=True,
        )
        db.session.add(admin)

    db.session.commit()





def ensure_export_folder():
    export_folder = current_app.config.get(
        "EXPORT_FOLDER", os.path.join(current_app.root_path, "exports")
    )
    os.makedirs(export_folder, exist_ok=True)
    return export_folder


def build_patient_export(export_path, appointments):
    with open(export_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "patient_name",
                "doctor_name",
                "department",
                "appointment_date",
                "appointment_time",
                "diagnosis",
                "prescription",
                "notes",
                "next_visit_date",
            ]
        )
        for appointment in appointments:
            treatment = appointment.treatment
            writer.writerow(
                [
                    appointment.patient.user.name,
                    appointment.doctor.user.name,
                    appointment.doctor.department.name if appointment.doctor.department else "",
                    format_date(appointment.date),
                    format_time(appointment.time),
                    treatment.diagnosis if treatment else "",
                    treatment.prescription if treatment else "",
                    treatment.notes if treatment else "",
                    format_date(treatment.next_visit_date) if treatment else "",
                ]
            )


def build_doctor_monthly_html(doctor_name, appointments):
    rows = []
    for appointment in appointments:
        treatment = appointment.treatment
        rows.append(
            f"""
            <tr>
                <td>{appointment.patient.user.name}</td>
                <td>{format_date(appointment.date)}</td>
                <td>{format_time(appointment.time)}</td>
                <td>{appointment.status}</td>
                <td>{treatment.diagnosis if treatment else '-'}</td>
                <td>{treatment.prescription if treatment else '-'}</td>
            </tr>
            """
        )

    if not rows:
        rows.append("<tr><td colspan='6'>No appointments for this month.</td></tr>")

    return f"""
    <html>
        <body>
            <h3>Monthly Activity Report - Dr. {doctor_name}</h3>
            <table border="1" cellspacing="0" cellpadding="6">
                <thead>
                    <tr>
                        <th>Patient</th>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Status</th>
                        <th>Diagnosis</th>
                        <th>Prescription</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </body>
    </html>
    """
