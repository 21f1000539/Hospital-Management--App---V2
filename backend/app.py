import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from extensions import cache
from models import db
from routes import admin_bp, auth_bp, doctor_bp, patient_bp
from celery_app import init_celery
from utils import seed_defaults


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hms_v2.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "hospital-management-dev-secret-key-2026"
    app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
    app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    app.config["TASKS_SYNC"] = not bool(os.getenv("REDIS_URL"))
    app.config["CACHE_TYPE"] = "RedisCache" if os.getenv("REDIS_URL") else "SimpleCache"
    app.config["CACHE_REDIS_URL"] = app.config["REDIS_URL"]
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
    app.config["CELERY_BROKER_URL"] = app.config["REDIS_URL"]
    app.config["CELERY_RESULT_BACKEND"] = app.config["REDIS_URL"]
    app.config["EXPORT_FOLDER"] = os.path.join(app.root_path, "exports")
    app.config["MAIL_HOST"] = os.getenv("MAIL_HOST")
    app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_SENDER"] = os.getenv("MAIL_SENDER")

    db.init_app(app)
    cache.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    init_celery(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(patient_bp)

    @app.get("/api/hello")
    def hello():
        return jsonify({"message": "Hospital Management System backend is running"})

    with app.app_context():
        db.create_all()
        seed_defaults()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
