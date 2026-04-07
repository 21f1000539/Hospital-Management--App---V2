<template>
  <div>
    <h2 class="mb-3">Admin Dashboard</h2>

    <div class="row g-3 mb-4">
      <div class="col-md-3" v-for="card in cards" :key="card.label">
        <div class="card shadow-sm">
          <div class="card-body">
            <div class="text-muted small">{{ card.label }}</div>
            <div class="fs-3 fw-bold">{{ card.value }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h5 class="mb-3">Add Department</h5>
        <form class="row g-2 mb-4" @submit.prevent="addDepartment">
          <div class="col-md-4">
            <input v-model="departmentForm.name" class="form-control" placeholder="Department name" required>
          </div>
          <div class="col-md-6">
            <input v-model="departmentForm.description" class="form-control" placeholder="Description">
          </div>
          <div class="col-md-2">
            <button class="btn btn-outline-primary w-100">Add</button>
          </div>
        </form>

        <h5>Add Doctor</h5>
        <form class="row g-2" @submit.prevent="addDoctor">
          <div class="col-md-3">
            <input v-model="doctorForm.name" class="form-control" placeholder="Name" required>
          </div>
          <div class="col-md-3">
            <input v-model="doctorForm.email" type="email" class="form-control" placeholder="Email" required>
          </div>
          <div class="col-md-2">
            <input v-model="doctorForm.password" class="form-control" placeholder="Password" required>
          </div>
          <div class="col-md-2">
            <select v-model="doctorForm.department_id" class="form-select" required>
              <option value="">Department</option>
              <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                {{ dept.name }}
              </option>
            </select>
          </div>
          <div class="col-md-2">
            <input v-model="doctorForm.specialization" class="form-control" placeholder="Specialization" required>
          </div>
          <div class="col-md-3">
            <input v-model="doctorForm.qualification" class="form-control" placeholder="Qualification">
          </div>
          <div class="col-md-3">
            <input v-model="doctorForm.phone_number" class="form-control" placeholder="Phone">
          </div>
          <div class="col-md-2">
            <input v-model="doctorForm.experience_years" type="number" class="form-control" placeholder="Experience">
          </div>
          <div class="col-md-4">
            <input v-model="doctorForm.bio" class="form-control" placeholder="Bio">
          </div>
          <div class="col-12">
            <button class="btn btn-primary">Add Doctor</button>
          </div>
        </form>
      </div>
    </div>

    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0">Doctors</h5>
          <input v-model="doctorSearch" class="form-control w-auto" placeholder="Search name or specialization">
        </div>
        <div class="table-responsive">
          <table class="table table-bordered align-middle">
            <thead>
              <tr>
                <th>Name</th>
                <th>Specialization</th>
                <th>Department</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doctor in filteredDoctors" :key="doctor.id">
                <td>{{ doctor.name }}</td>
                <td>{{ doctor.specialization }}</td>
                <td>{{ doctor.department_name }}</td>
                <td>{{ doctor.is_active ? "Active" : "Inactive" }}</td>
                <td>
                  <button class="btn btn-sm btn-outline-secondary" @click="toggleDoctor(doctor)">
                    {{ doctor.is_active ? "Deactivate" : "Activate" }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="mb-3">Appointments</h5>
        <div class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="appointment in appointments" :key="appointment.id">
                <td>{{ appointment.patient.name }}</td>
                <td>{{ appointment.doctor.name }}</td>
                <td>{{ appointment.date }}</td>
                <td>{{ appointment.time }}</td>
                <td>{{ appointment.status }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../services/api"

export default {
  data() {
    return {
      stats: {},
      departments: [],
      doctors: [],
      appointments: [],
      doctorSearch: "",
      departmentForm: {
        name: "",
        description: ""
      },
      doctorForm: {
        name: "",
        email: "",
        password: "",
        department_id: "",
        specialization: "",
        qualification: "",
        phone_number: "",
        experience_years: "",
        bio: ""
      }
    }
  },
  computed: {
    cards() {
      return [
        { label: "Doctors", value: this.stats.total_doctors || 0 },
        { label: "Patients", value: this.stats.total_patients || 0 },
        { label: "Appointments", value: this.stats.total_appointments || 0 },
        { label: "Upcoming", value: this.stats.upcoming_appointments || 0 }
      ]
    },
    filteredDoctors() {
      const search = this.doctorSearch.toLowerCase()
      if (!search) return this.doctors
      return this.doctors.filter((doctor) =>
        doctor.name.toLowerCase().includes(search) ||
        doctor.specialization.toLowerCase().includes(search)
      )
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    async loadData() {
      const [statsRes, deptRes, doctorRes, appointmentRes] = await Promise.all([
        api.get("/api/admin/dashboard"),
        api.get("/api/admin/departments"),
        api.get("/api/admin/doctors"),
        api.get("/api/admin/appointments")
      ])
      this.stats = statsRes.data
      this.departments = deptRes.data.departments
      this.doctors = doctorRes.data.doctors
      this.appointments = appointmentRes.data.appointments
    },
    async addDoctor() {
      await api.post("/api/admin/doctors", this.doctorForm)
      this.doctorForm = {
        name: "",
        email: "",
        password: "",
        department_id: "",
        specialization: "",
        qualification: "",
        phone_number: "",
        experience_years: "",
        bio: ""
      }
      await this.loadData()
    },
    async addDepartment() {
      await api.post("/api/admin/departments", this.departmentForm)
      this.departmentForm = {
        name: "",
        description: ""
      }
      await this.loadData()
    },
    async toggleDoctor(doctor) {
      await api.patch(`/api/admin/doctors/${doctor.id}/status`, {
        is_active: !doctor.is_active
      })
      await this.loadData()
    }
  }
}
</script>
