from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="patient", index=True)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor_profile = db.relationship("DoctorProfile", backref="user", uselist=False)
    patient_profile = db.relationship("PatientProfile", backref="user", uselist=False)


class Department(db.Model):
    __tablename__ = "department"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200))

    doctors = db.relationship("DoctorProfile", backref="department", lazy=True)


class DoctorProfile(db.Model):
    __tablename__ = "doctor_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"), nullable=False)
    specialization = db.Column(db.String(80), nullable=False, index=True)
    qualification = db.Column(db.String(120))
    phone_number = db.Column(db.String(20))
    bio = db.Column(db.Text)
    experience_years = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

    appointments = db.relationship("Appointment", backref="doctor", lazy=True)
    availability = db.relationship("DoctorAvailability", backref="doctor", lazy=True)


class PatientProfile(db.Model):
    __tablename__ = "patient_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(200))
    emergency_contact = db.Column(db.String(80))
    medical_history = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    appointments = db.relationship("Appointment", backref="patient", lazy=True)
    exports = db.relationship("ExportRequest", backref="patient", lazy=True)


class Appointment(db.Model):
    __tablename__ = "appointment"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor_profile.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient_profile.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default="booked", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    treatment = db.relationship("Treatment", backref="appointment", uselist=False)

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "date", "time", name="unique_doctor_slot"),
    )


class Treatment(db.Model):
    __tablename__ = "treatment"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id"), unique=True, nullable=False
    )
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    next_visit_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor_profile.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint(
            "doctor_id", "date", "start_time", "end_time", name="unique_doctor_availability"
        ),
    )


class ExportRequest(db.Model):
    __tablename__ = "export_request"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient_profile.id"), nullable=False)
    status = db.Column(db.String(20), default="pending", index=True)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
