from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from extensions import cache
from models import Appointment, Department, DoctorProfile, PatientProfile, User, db
from utils import (
    appointment_to_dict,
    clear_cache,
    department_to_dict,
    doctor_to_dict,
    patient_to_dict,
    role_required,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/dashboard")
@role_required("admin")
@cache.cached(timeout=180, query_string=True)
def dashboard():
    return jsonify(
        {
            "total_doctors": DoctorProfile.query.filter_by(is_active=True).count(),
            "total_patients": PatientProfile.query.filter_by(is_active=True).count(),
            "total_appointments": Appointment.query.count(),
            "upcoming_appointments": Appointment.query.filter_by(status="booked").count(),
        }
    )


@admin_bp.get("/departments")
@role_required("admin")
@cache.cached(timeout=300, query_string=True)
def get_departments():
    departments = Department.query.order_by(Department.name.asc()).all()
    return jsonify({"departments": [department_to_dict(item) for item in departments]})


@admin_bp.post("/departments")
@role_required("admin")
def add_department():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"message": "Department name is required"}), 400

    if Department.query.filter_by(name=name).first():
        return jsonify({"message": "Department already exists"}), 400

    department = Department(name=name, description=data.get("description"))
    db.session.add(department)
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Department added", "department": department_to_dict(department)})


@admin_bp.get("/doctors")
@role_required("admin")
@cache.cached(timeout=300, query_string=True)
def get_doctors():
    name = (request.args.get("name") or "").strip()
    specialization = (request.args.get("specialization") or "").strip()

    query = DoctorProfile.query.join(User).join(Department)
    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if specialization:
        query = query.filter(DoctorProfile.specialization.ilike(f"%{specialization}%"))

    doctors = query.order_by(User.name.asc()).all()
    return jsonify({"doctors": [doctor_to_dict(item) for item in doctors]})


@admin_bp.post("/doctors")
@role_required("admin")
def add_doctor():
    data = request.get_json() or {}
    required_fields = ["name", "email", "password", "department_id", "specialization"]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"message": "Missing fields", "fields": missing}), 400

    if User.query.filter_by(email=data["email"].strip().lower()).first():
        return jsonify({"message": "Email already exists"}), 400

    department = Department.query.get(int(data["department_id"]))
    if not department:
        return jsonify({"message": "Department not found"}), 404

    user = User(
        name=data["name"].strip(),
        email=data["email"].strip().lower(),
        password=generate_password_hash(data["password"]),
        role="doctor",
    )
    db.session.add(user)
    db.session.flush()

    profile = DoctorProfile(
        user_id=user.id,
        department_id=department.id,
        specialization=data["specialization"].strip(),
        qualification=data.get("qualification"),
        phone_number=data.get("phone_number"),
        bio=data.get("bio"),
        experience_years=data.get("experience_years"),
        is_active=True,
    )
    db.session.add(profile)
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Doctor added", "doctor": doctor_to_dict(profile)})


@admin_bp.put("/doctors/<int:doctor_id>")
@role_required("admin")
def update_doctor(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    data = request.get_json() or {}

    if data.get("name"):
        doctor.user.name = data["name"].strip()
    if data.get("email"):
        email = data["email"].strip().lower()
        existing = User.query.filter(User.email == email, User.id != doctor.user.id).first()
        if existing:
            return jsonify({"message": "Email already exists"}), 400
        doctor.user.email = email
    if data.get("password"):
        doctor.user.password = generate_password_hash(data["password"])
    if data.get("department_id"):
        department = Department.query.get(int(data["department_id"]))
        if not department:
            return jsonify({"message": "Department not found"}), 404
        doctor.department_id = department.id
    if data.get("specialization"):
        doctor.specialization = data["specialization"].strip()

    for field in ["qualification", "phone_number", "bio", "experience_years"]:
        if field in data:
            setattr(doctor, field, data.get(field))

    db.session.commit()
    clear_cache()
    return jsonify({"message": "Doctor updated", "doctor": doctor_to_dict(doctor)})


@admin_bp.patch("/doctors/<int:doctor_id>/status")
@role_required("admin")
def toggle_doctor_status(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    active = bool((request.get_json() or {}).get("is_active", False))
    doctor.is_active = active
    doctor.user.is_active = active
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Doctor status updated", "doctor": doctor_to_dict(doctor)})


@admin_bp.get("/patients")
@role_required("admin")
def get_patients():
    query_value = (request.args.get("query") or "").strip()
    query = PatientProfile.query.join(User)
    if query_value:
        query = query.filter(
            (User.name.ilike(f"%{query_value}%"))
            | (User.email.ilike(f"%{query_value}%"))
            | (PatientProfile.phone_number.ilike(f"%{query_value}%"))
        )

    patients = query.order_by(User.name.asc()).all()
    return jsonify({"patients": [patient_to_dict(item) for item in patients]})


@admin_bp.patch("/patients/<int:patient_id>/status")
@role_required("admin")
def toggle_patient_status(patient_id):
    patient = PatientProfile.query.get_or_404(patient_id)
    active = bool((request.get_json() or {}).get("is_active", False))
    patient.is_active = active
    patient.user.is_active = active
    db.session.commit()
    clear_cache()
    return jsonify({"message": "Patient status updated", "patient": patient_to_dict(patient)})


@admin_bp.get("/appointments")
@role_required("admin")
def get_appointments():
    status = (request.args.get("status") or "").strip()
    query = Appointment.query
    if status:
        query = query.filter_by(status=status)

    appointments = query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return jsonify({"appointments": [appointment_to_dict(item) for item in appointments]})
