<template>
  <div>
    <h2 class="mb-3">Patient Dashboard</h2>

    <div class="row g-4">
      <div class="col-lg-5">
        <div class="card shadow-sm mb-4">
          <div class="card-body">
            <h5>My Profile</h5>
            <div v-if="message" class="alert alert-success py-2">{{ message }}</div>
            <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
            <form class="row g-2" @submit.prevent="saveProfile">
              <div class="col-md-6">
                <input v-model="profile.name" class="form-control" placeholder="Name">
              </div>
              <div class="col-md-6">
                <input v-model="profile.phone_number" class="form-control" placeholder="Phone">
              </div>
              <div class="col-md-6">
                <input v-model="profile.age" type="number" class="form-control" placeholder="Age">
              </div>
              <div class="col-md-6">
                <input v-model="profile.gender" class="form-control" placeholder="Gender">
              </div>
              <div class="col-12">
                <textarea v-model="profile.address" class="form-control" rows="2" placeholder="Address"></textarea>
              </div>
              <div class="col-12">
                <button class="btn btn-outline-primary w-100">Update Profile</button>
              </div>
            </form>
          </div>
        </div>

        <div class="card shadow-sm mb-4">
          <div class="card-body">
            <h5>Book Appointment</h5>
            <form class="row g-2" @submit.prevent="bookAppointment">
              <div class="col-12">
                <select
                  v-model="appointmentForm.doctor_id"
                  class="form-select"
                  @change="handleDoctorChange"
                  required
                >
                  <option value="">Select doctor</option>
                  <option v-for="doctor in filteredDoctors" :key="doctor.id" :value="doctor.id">
                    {{ doctor.name }} - {{ doctor.specialization }}
                  </option>
                </select>
              </div>
              <div class="col-12" v-if="appointmentForm.doctor_id">
                <div class="border rounded p-3 bg-light">
                  <div class="fw-semibold mb-2">Available Slots</div>
                  <div v-if="loadingSlots" class="text-muted small">Loading slots...</div>
                  <div v-else-if="availability.length" class="d-flex flex-wrap gap-2">
                    <button
                      v-for="slot in availability"
                      :key="slot.id"
                      type="button"
                      class="btn btn-sm btn-outline-primary"
                      @click="selectSlot(slot)"
                    >
                      {{ slot.date }} {{ slot.start_time }}
                    </button>
                  </div>
                  <div v-else class="text-muted small">
                    No slots available for this doctor in the next 7 days.
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <input v-model="appointmentForm.date" type="date" class="form-control" required>
              </div>
              <div class="col-md-6">
                <input v-model="appointmentForm.time" type="time" class="form-control" required>
              </div>
              <div class="col-12">
                <input v-model="appointmentForm.reason" class="form-control" placeholder="Reason">
              </div>
              <div class="col-12">
                <button class="btn btn-primary w-100">Book</button>
              </div>
            </form>
          </div>
        </div>

        <div class="card shadow-sm">
          <div class="card-body">
            <h5 class="mb-3">Doctors</h5>
            <input v-model="search" class="form-control mb-3" placeholder="Search name or specialization">
            <ul class="list-group">
              <li
                v-for="doctor in filteredDoctors"
                :key="doctor.id"
                class="list-group-item"
                @click="showAvailability(doctor.id)"
                style="cursor: pointer"
              >
                <div class="fw-semibold">{{ doctor.name }}</div>
                <div class="small text-muted">{{ doctor.specialization }} | {{ doctor.department_name }}</div>
              </li>
            </ul>

            <div v-if="availability.length" class="mt-3">
              <h6>Next 7 days availability</h6>
              <p class="small text-muted">Click a slot to auto-fill booking date and time.</p>
              <ul class="list-group">
                <li
                  v-for="slot in availability"
                  :key="slot.id"
                  class="list-group-item py-2"
                  @click="selectSlot(slot)"
                  style="cursor: pointer"
                >
                  {{ slot.date }} | {{ slot.start_time }} - {{ slot.end_time }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-7">
        <div class="card shadow-sm mb-4">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="mb-0">My Appointments</h5>
              <button class="btn btn-outline-success btn-sm" @click="startExport">
                Export CSV
              </button>
            </div>
            <div v-if="exportInfo" class="alert alert-info py-2">
              Export status: {{ exportInfo.status }}
            </div>
            <div class="table-responsive">
              <table class="table table-striped align-middle">
                <thead>
                  <tr>
                    <th>Doctor</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="appointment in appointments" :key="appointment.id">
                    <td>{{ appointment.doctor.name }}</td>
                    <td>{{ appointment.date }}</td>
                    <td>{{ appointment.time }}</td>
                    <td>{{ appointment.status }}</td>
                    <td>
                      <button
                        class="btn btn-sm btn-outline-danger"
                        @click="cancelAppointment(appointment.id)"
                        :disabled="appointment.status !== 'booked'"
                      >
                        Cancel
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
            <h5 class="mb-3">Treatment History</h5>
            <div class="table-responsive">
              <table class="table table-bordered">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Doctor</th>
                    <th>Diagnosis</th>
                    <th>Prescription</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="appointment in treatments" :key="appointment.id">
                    <td>{{ appointment.date }}</td>
                    <td>{{ appointment.doctor.name }}</td>
                    <td>{{ appointment.treatment?.diagnosis || "-" }}</td>
                    <td>{{ appointment.treatment?.prescription || "-" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
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
      doctors: [],
      availability: [],
      profile: {
        name: "",
        age: "",
        gender: "",
        phone_number: "",
        address: ""
      },
      appointments: [],
      treatments: [],
      exportInfo: null,
      error: "",
      loadingSlots: false,
      message: "",
      search: "",
      appointmentForm: {
        doctor_id: "",
        date: "",
        time: "",
        reason: ""
      }
    }
  },
  computed: {
    filteredDoctors() {
      const searchText = this.search.toLowerCase()
      if (!searchText) return this.doctors
      return this.doctors.filter((doctor) =>
        doctor.name.toLowerCase().includes(searchText) ||
        doctor.specialization.toLowerCase().includes(searchText)
      )
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    async loadData() {
      const [profileRes, doctorRes, appointmentRes, treatmentRes, exportRes] = await Promise.all([
        api.get("/api/patient/profile"),
        api.get("/api/patient/doctors"),
        api.get("/api/patient/appointments"),
        api.get("/api/patient/treatments"),
        api.get("/api/patient/export-status")
      ])
      this.profile = profileRes.data.profile
      this.doctors = doctorRes.data.doctors
      this.appointments = appointmentRes.data.appointments
      this.treatments = treatmentRes.data.appointments
      this.exportInfo = exportRes.data.export
    },
    async bookAppointment() {
      this.error = ""
      this.message = ""
      try {
        await api.post("/api/patient/appointments", this.appointmentForm)
        this.message = "Appointment booked successfully"
        this.appointmentForm = {
          doctor_id: "",
          date: "",
          time: "",
          reason: ""
        }
        this.availability = []
        await this.loadData()
      } catch (error) {
        this.error = error.response?.data?.message || "Could not book appointment"
      }
    },
    async saveProfile() {
      this.error = ""
      this.message = ""
      try {
        await api.put("/api/patient/profile", this.profile)
        this.message = "Profile updated"
        await this.loadData()
      } catch (error) {
        this.error = error.response?.data?.message || "Could not update profile"
      }
    },
    async showAvailability(doctorId) {
      this.error = ""
      this.message = ""
      this.loadingSlots = true
      try {
        const response = await api.get(`/api/patient/doctors/${doctorId}/availability`)
        this.availability = response.data.availability
        this.appointmentForm.doctor_id = doctorId
      } catch (error) {
        this.error = error.response?.data?.message || "Could not load doctor availability"
        this.availability = []
      } finally {
        this.loadingSlots = false
      }
    },
    async handleDoctorChange() {
      if (!this.appointmentForm.doctor_id) {
        this.availability = []
        return
      }
      await this.showAvailability(this.appointmentForm.doctor_id)
    },
    selectSlot(slot) {
      this.appointmentForm.date = slot.date
      this.appointmentForm.time = slot.start_time
    },
    async cancelAppointment(appointmentId) {
      this.error = ""
      this.message = ""
      try {
        await api.post(`/api/patient/appointments/${appointmentId}/cancel`)
        this.message = "Appointment cancelled"
        await this.loadData()
      } catch (error) {
        this.error = error.response?.data?.message || "Could not cancel appointment"
      }
    },
    async startExport() {
      this.error = ""
      this.message = ""
      try {
        await api.post("/api/patient/export")
        this.message = "Export started"
        await this.loadData()
      } catch (error) {
        this.error = error.response?.data?.message || "Could not start export"
      }
    }
  }
}
</script>
