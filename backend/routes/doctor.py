from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from models import Appointment, DoctorAvailability, PatientProfile, Treatment, db
from utils import (
    appointment_to_dict,
    availability_to_dict,
    clear_cache,
    get_current_user,
    parse_date,
    parse_optional_date,
    parse_time,
    patient_to_dict,
    role_required,
    treatment_to_dict,
)

doctor_bp = Blueprint("doctor", __name__, url_prefix="/api/doctor")

PRESET_SLOTS = {
    "morning": ("09:00", "11:00"),
    "afternoon": ("14:00", "16:00"),
    "evening": ("18:00", "20:00"),
}


def get_doctor_profile():
    user = get_current_user()
    if not user or not user.doctor_profile:
        return None
    return user.doctor_profile


@doctor_bp.get("/dashboard")
@role_required("doctor")
def dashboard():
    doctor = get_doctor_profile()
    today = date.today()
    week_end = today + timedelta(days=7)

    today_appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date == today,
        )
        .order_by(Appointment.time.asc())
        .all()
    )
    week_appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date >= today,
            Appointment.date <= week_end,
        )
        .order_by(Appointment.date.asc(), Appointment.time.asc())
        .all()
    )

    patient_ids = {item.patient_id for item in week_appointments}
    patients = PatientProfile.query.filter(PatientProfile.id.in_(patient_ids)).all() if patient_ids else []

    return jsonify(
        {
            "today_appointments": [appointment_to_dict(item) for item in today_appointments],
            "week_appointments": [appointment_to_dict(item) for item in week_appointments],
            "patients": [patient_to_dict(item) for item in patients],
        }
    )


@doctor_bp.get("/appointments")
@role_required("doctor")
def get_appointments():
    doctor = get_doctor_profile()
    status = (request.args.get("status") or "").strip()

    query = Appointment.query.filter_by(doctor_id=doctor.id)
    if status:
        query = query.filter_by(status=status)

    appointments = query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return jsonify({"appointments": [appointment_to_dict(item) for item in appointments]})


@doctor_bp.get("/availability")
@role_required("doctor")
def get_availability():
    doctor = get_doctor_profile()
    today = date.today()
    seven_days = today + timedelta(days=7)

    slots = (
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.date >= today,
            DoctorAvailability.date <= seven_days,
        )
        .order_by(DoctorAvailability.date.asc(), DoctorAvailability.start_time.asc())
        .all()
    )
    return jsonify({"availability": [availability_to_dict(item) for item in slots]})


@doctor_bp.post("/availability")
@role_required("doctor")
def add_availability():
    doctor = get_doctor_profile()
    data = request.get_json() or {}
    required_fields = ["date", "start_time", "end_time"]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"message": "Missing fields", "fields": missing}), 400

    slot = DoctorAvailability(
        doctor_id=doctor.id,
        date=parse_date(data["date"]),
        start_time=parse_time(data["start_time"]),
        end_time=parse_time(data["end_time"]),
        is_available=True,
    )
    if slot.start_time >= slot.end_time:
        return jsonify({"message": "End time must be greater than start time"}), 400

    db.session.add(slot)
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Availability added", "slot": availability_to_dict(slot)})


@doctor_bp.post("/availability/preset")
@role_required("doctor")
def add_preset_availability():
    doctor = get_doctor_profile()
    data = request.get_json() or {}

    weekdays = data.get("weekdays") or []
    slot_key = (data.get("slot_key") or "").strip()

    if not weekdays:
        return jsonify({"message": "Please select at least one weekday"}), 400
    if slot_key not in PRESET_SLOTS:
        return jsonify({"message": "Please select a valid time slot"}), 400

    start_time, end_time = PRESET_SLOTS[slot_key]
    start_time = parse_time(start_time)
    end_time = parse_time(end_time)

    today = date.today()
    created_slots = []
    skipped_count = 0

    for day_offset in range(7):
        slot_date = today + timedelta(days=day_offset)
        if slot_date.weekday() not in weekdays:
            continue

        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            date=slot_date,
            start_time=start_time,
            end_time=end_time,
        ).first()
        if existing:
            skipped_count += 1
            continue

        slot = DoctorAvailability(
            doctor_id=doctor.id,
            date=slot_date,
            start_time=start_time,
            end_time=end_time,
            is_available=True,
        )
        db.session.add(slot)
        created_slots.append(slot)

    db.session.commit()
    clear_cache()

    return jsonify(
        {
            "message": "Preset availability saved",
            "created_count": len(created_slots),
            "skipped_count": skipped_count,
            "slots": [availability_to_dict(slot) for slot in created_slots],
        }
    )


@doctor_bp.post("/appointments/<int:appointment_id>/complete")
@role_required("doctor")
def complete_appointment(appointment_id):
    doctor = get_doctor_profile()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != doctor.id:
        return jsonify({"message": "Appointment not found"}), 404

    data = request.get_json() or {}
    treatment = appointment.treatment or Treatment(appointment_id=appointment.id)
    treatment.diagnosis = data.get("diagnosis")
    treatment.prescription = data.get("prescription")
    treatment.notes = data.get("notes")
    treatment.next_visit_date = parse_optional_date(data.get("next_visit_date"))

    appointment.status = "completed"
    db.session.add(treatment)
    db.session.commit()
    clear_cache()
    return jsonify(
        {
            "message": "Appointment completed",
            "appointment": appointment_to_dict(appointment),
            "treatment": treatment_to_dict(treatment),
        }
    )


@doctor_bp.post("/appointments/<int:appointment_id>/cancel")
@role_required("doctor")
def cancel_appointment(appointment_id):
    doctor = get_doctor_profile()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != doctor.id:
        return jsonify({"message": "Appointment not found"}), 404
    if appointment.status == "completed":
        return jsonify({"message": "Completed appointment cannot be cancelled"}), 400

    appointment.status = "cancelled"
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Appointment cancelled", "appointment": appointment_to_dict(appointment)})


@doctor_bp.get("/patients/<int:patient_id>/history")
@role_required("doctor")
def patient_history(patient_id):
    doctor = get_doctor_profile()
    patient = PatientProfile.query.get_or_404(patient_id)

    appointments = (
        Appointment.query.filter_by(doctor_id=doctor.id, patient_id=patient.id)
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .all()
    )
    return jsonify(
        {
            "patient": patient_to_dict(patient),
            "appointments": [appointment_to_dict(item) for item in appointments],
        }
    )
