from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from models import PatientProfile, User, db
from utils import create_user_token, get_current_user, role_required, user_to_dict

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}

    required_fields = ["name", "email", "password"]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"message": "Missing fields", "fields": missing}), 400

    existing = User.query.filter_by(email=data["email"].strip().lower()).first()
    if existing:
        return jsonify({"message": "Email already exists"}), 400

    user = User(
        name=data["name"].strip(),
        email=data["email"].strip().lower(),
        password=generate_password_hash(data["password"]),
        role="patient",
    )
    db.session.add(user)
    db.session.flush()

    patient_profile = PatientProfile(
        user_id=user.id,
        age=data.get("age"),
        gender=data.get("gender"),
        phone_number=data.get("phone_number"),
        address=data.get("address"),
        emergency_contact=data.get("emergency_contact"),
        medical_history=data.get("medical_history"),
    )
    db.session.add(patient_profile)
    db.session.commit()

    token = create_user_token(user)
    return jsonify({"message": "Patient registered", "token": token, "user": user_to_dict(user)})


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    selected_role = (data.get("role") or "").strip().lower()

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"message": "This account is inactive"}), 403

    if selected_role and user.role != selected_role:
        return jsonify({"message": "Selected role does not match this account"}), 403

    token = create_user_token(user)
    return jsonify({"token": token, "user": user_to_dict(user)})


@auth_bp.get("/me")
@role_required("admin", "doctor", "patient")
def me():
    user = get_current_user()
    return jsonify({"user": user_to_dict(user)})
