import os
from datetime import date, timedelta

from flask import Blueprint, current_app, jsonify, request, send_file

from extensions import cache
from models import Appointment, Department, DoctorAvailability, DoctorProfile, ExportRequest, User, db
from celery_app import generate_patient_export
from utils import (
    appointment_to_dict,
    availability_to_dict,
    clear_cache,
    department_to_dict,
    doctor_to_dict,
    get_current_user,
    is_slot_available,
    parse_date,
    parse_time,
    patient_to_dict,
    role_required,
)

patient_bp = Blueprint("patient", __name__, url_prefix="/api/patient")


def get_patient_profile():
    user = get_current_user()
    if not user or not user.patient_profile:
        return None
    return user.patient_profile


@patient_bp.get("/profile")
@role_required("patient")
def get_profile():
    return jsonify({"profile": patient_to_dict(get_patient_profile())})


@patient_bp.put("/profile")
@role_required("patient")
def update_profile():
    profile = get_patient_profile()
    data = request.get_json() or {}

    if data.get("name"):
        profile.user.name = data["name"].strip()

    for field in [
        "age",
        "gender",
        "phone_number",
        "address",
        "emergency_contact",
        "medical_history",
    ]:
        if field in data:
            setattr(profile, field, data.get(field))

    db.session.commit()
    clear_cache()
    return jsonify({"message": "Profile updated", "profile": patient_to_dict(profile)})


@patient_bp.get("/departments")
@role_required("patient")
@cache.cached(timeout=300, query_string=True)
def get_departments():
    departments = Department.query.order_by(Department.name.asc()).all()
    return jsonify({"departments": [department_to_dict(item) for item in departments]})


@patient_bp.get("/doctors")
@role_required("patient")
@cache.cached(timeout=300, query_string=True)
def get_doctors():
    name = (request.args.get("name") or "").strip()
    specialization = (request.args.get("specialization") or "").strip()

    query = DoctorProfile.query.join(User).filter(
        DoctorProfile.is_active.is_(True),
        User.is_active.is_(True),
    )
    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if specialization:
        query = query.filter(DoctorProfile.specialization.ilike(f"%{specialization}%"))

    doctors = query.order_by(User.name.asc()).all()
    return jsonify({"doctors": [doctor_to_dict(item) for item in doctors]})


@patient_bp.get("/doctors/<int:doctor_id>/availability")
@role_required("patient")
@cache.cached(timeout=300, query_string=True)
def doctor_availability(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    today = date.today()
    max_date = today + timedelta(days=7)

    slots = (
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.date >= today,
            DoctorAvailability.date <= max_date,
            DoctorAvailability.is_available.is_(True),
        )
        .order_by(DoctorAvailability.date.asc(), DoctorAvailability.start_time.asc())
        .all()
    )
    return jsonify(
        {"doctor": doctor_to_dict(doctor), "availability": [availability_to_dict(item) for item in slots]}
    )


@patient_bp.get("/appointments")
@role_required("patient")
def get_appointments():
    profile = get_patient_profile()
    appointments = (
        Appointment.query.filter_by(patient_id=profile.id)
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .all()
    )
    return jsonify({"appointments": [appointment_to_dict(item) for item in appointments]})


@patient_bp.post("/appointments")
@role_required("patient")
def book_appointment():
    profile = get_patient_profile()
    data = request.get_json() or {}
    required_fields = ["doctor_id", "date", "time"]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"message": "Missing fields", "fields": missing}), 400

    doctor = DoctorProfile.query.get(int(data["doctor_id"]))
    if not doctor or not doctor.is_active or not doctor.user.is_active:
        return jsonify({"message": "Doctor not available"}), 404

    appointment_date = parse_date(data["date"])
    appointment_time = parse_time(data["time"])

    if not is_slot_available(doctor.id, appointment_date, appointment_time):
        return jsonify({"message": "Selected slot is not available"}), 400

    existing = Appointment.query.filter_by(
        doctor_id=doctor.id,
        date=appointment_date,
        time=appointment_time,
    ).first()
    if existing:
        return jsonify({"message": "This doctor already has an appointment in that slot"}), 400

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=profile.id,
        date=appointment_date,
        time=appointment_time,
        reason=data.get("reason"),
        status="booked",
    )
    db.session.add(appointment)
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Appointment booked", "appointment": appointment_to_dict(appointment)})


@patient_bp.put("/appointments/<int:appointment_id>")
@role_required("patient")
def reschedule_appointment(appointment_id):
    profile = get_patient_profile()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient_id != profile.id:
        return jsonify({"message": "Appointment not found"}), 404
    if appointment.status == "completed":
        return jsonify({"message": "Completed appointment cannot be changed"}), 400

    data = request.get_json() or {}
    appointment_date = parse_date(data["date"])
    appointment_time = parse_time(data["time"])

    if not is_slot_available(appointment.doctor_id, appointment_date, appointment_time):
        return jsonify({"message": "Selected slot is not available"}), 400

    existing = Appointment.query.filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.date == appointment_date,
        Appointment.time == appointment_time,
        Appointment.id != appointment.id,
    ).first()
    if existing:
        return jsonify({"message": "This doctor already has an appointment in that slot"}), 400

    appointment.date = appointment_date
    appointment.time = appointment_time
    appointment.reason = data.get("reason", appointment.reason)
    appointment.status = "booked"
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Appointment updated", "appointment": appointment_to_dict(appointment)})


@patient_bp.post("/appointments/<int:appointment_id>/cancel")
@role_required("patient")
def cancel_appointment(appointment_id):
    profile = get_patient_profile()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient_id != profile.id:
        return jsonify({"message": "Appointment not found"}), 404
    if appointment.status == "completed":
        return jsonify({"message": "Completed appointment cannot be cancelled"}), 400

    appointment.status = "cancelled"
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Appointment cancelled", "appointment": appointment_to_dict(appointment)})


@patient_bp.get("/treatments")
@role_required("patient")
def treatment_history():
    profile = get_patient_profile()
    appointments = (
        Appointment.query.filter_by(patient_id=profile.id)
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .all()
    )
    return jsonify({"appointments": [appointment_to_dict(item) for item in appointments]})


@patient_bp.post("/export")
@role_required("patient")
def create_export():
    profile = get_patient_profile()
    export_request = ExportRequest(patient_id=profile.id, status="pending")
    db.session.add(export_request)
    db.session.commit()

    if current_app.config.get("TASKS_SYNC", True):
        generate_patient_export(profile.id, export_request.id)
    else:
        try:
            generate_patient_export.delay(profile.id, export_request.id)
        except Exception:
            generate_patient_export(profile.id, export_request.id)

    return jsonify({"message": "Export started", "export_id": export_request.id})


@patient_bp.get("/export-status")
@role_required("patient")
def export_status():
    profile = get_patient_profile()
    latest_export = (
        ExportRequest.query.filter_by(patient_id=profile.id)
        .order_by(ExportRequest.created_at.desc())
        .first()
    )
    if not latest_export:
        return jsonify({"export": None})

    return jsonify(
        {
            "export": {
                "id": latest_export.id,
                "status": latest_export.status,
                "file_path": latest_export.file_path,
                "created_at": latest_export.created_at.isoformat(),
                "completed_at": latest_export.completed_at.isoformat()
                if latest_export.completed_at
                else None,
            }
        }
    )


@patient_bp.get("/export-download/<int:export_id>")
@role_required("patient")
def export_download(export_id):
    profile = get_patient_profile()
    export_request = ExportRequest.query.get_or_404(export_id)
    if export_request.patient_id != profile.id:
        return jsonify({"message": "Export not found"}), 404
    if not export_request.file_path or not os.path.exists(export_request.file_path):
        return jsonify({"message": "Export file not ready"}), 404

    return send_file(export_request.file_path, as_attachment=True)
