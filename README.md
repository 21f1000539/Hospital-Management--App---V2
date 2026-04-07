# Hospital Management System - V2

Simple college project built with Flask, Vue, Bootstrap, SQLite, Redis, and Celery.

## Features

- Admin login with pre-created account
- Patient register and login
- Doctor login
- Admin dashboard for doctors, patients, and appointments
- Doctor availability for next 7 days
- Patient appointment booking and cancellation
- Doctor treatment update after appointment
- Patient treatment history
- CSV export of patient treatment records
- Daily reminder and monthly report job setup

## Tech Stack

- Flask for backend API
- Vue 3 for frontend
- Bootstrap 5 for UI
- SQLite for database
- Redis for caching
- Celery for background jobs

## Project Structure

```
text
Hospital-Management--App---V2/
|-- backend/
|   |-- app.py
|   |-- celery_app.py
|   |-- mail.py
|   |-- models.py
|   |-- utils.py
|   |-- routes/
|-- frontend/
|   |-- src/
|   |-- public/
|-- README.md
```

## Default Admin Login

- Email: `admin@gmail.com`
- Password: `1234`

## Backend Setup

Open terminal in `backend` folder:

```powershell
cd backend
.\venv\Scripts\activate
python app.py
```


## Frontend Setup
Open terminal in `frontend` folder:

```powershell
cd frontend
npm install
npm run serve
```

Frontend runs on:

```text
http://localhost:8080
```

## Redis and Celery Setup

This project can run without Redis for basic local demo. In that case, export runs in simple sync mode and email uses console fallback.

If you want full Redis + Celery setup:

```powershell
set REDIS_URL=redis://localhost:6379/0
cd backend
.\venv\Scripts\celery -A celery_app worker -P solo --loglevel=info
.\venv\Scripts\celery -A celery_app beat --loglevel=info
```

## Main Modules

### Admin

- View dashboard counts
- Add, update, and deactivate doctors
- View all appointments
- Search doctors and patients

### Doctor

- View weekly appointments
- Add availability
- Complete or cancel appointments
- Add diagnosis and prescription
- View patient history

### Patient

- Register and login
- Update profile
- View doctors and their availability
- Book or cancel appointments
- View treatment history
- Export treatment details as CSV

## API Overview

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Admin

- `GET /api/admin/dashboard`
- `GET /api/admin/departments`
- `POST /api/admin/departments`
- `GET /api/admin/doctors`
- `POST /api/admin/doctors`
- `PUT /api/admin/doctors/<doctor_id>`
- `PATCH /api/admin/doctors/<doctor_id>/status`
- `GET /api/admin/patients`
- `PATCH /api/admin/patients/<patient_id>/status`
- `GET /api/admin/appointments`

### Doctor

- `GET /api/doctor/dashboard`
- `GET /api/doctor/appointments`
- `GET /api/doctor/availability`
- `POST /api/doctor/availability`
- `POST /api/doctor/appointments/<appointment_id>/complete`
- `POST /api/doctor/appointments/<appointment_id>/cancel`
- `GET /api/doctor/patients/<patient_id>/history`

### Patient

- `GET /api/patient/profile`
- `PUT /api/patient/profile`
- `GET /api/patient/departments`
- `GET /api/patient/doctors`
- `GET /api/patient/doctors/<doctor_id>/availability`
- `GET /api/patient/appointments`
- `POST /api/patient/appointments`
- `PUT /api/patient/appointments/<appointment_id>`
- `POST /api/patient/appointments/<appointment_id>/cancel`
- `GET /api/patient/treatments`
- `POST /api/patient/export`
- `GET /api/patient/export-status`
- `GET /api/patient/export-download/<export_id>`

## Notes

- Database tables are created automatically from Flask models.
- Admin is created programmatically on first run.
- Bootstrap is used for simple UI styling.
- If email credentials are not added, reminder/report/export messages are printed in console.

## Viva Explanation

This project is a role-based hospital management system. Admin manages doctors and appointments, doctors manage availability and treatment details, and patients can register, book appointments, and check their medical history.

I used Flask with SQLite because it is simple and easy to explain. Vue is used for the frontend to make the pages interactive, and Redis/Celery are added for caching and background jobs as required in the project statement.
