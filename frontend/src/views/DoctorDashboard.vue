<template>
  <div>
    <h2 class="mb-3">Doctor Dashboard</h2>

    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h5>Add Availability</h5>
        <div v-if="message" class="alert alert-success py-2">{{ message }}</div>
        <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
        <div class="border rounded p-3 mb-3 bg-light">
          <div class="fw-semibold mb-2">Quick Weekly Setup</div>
          <div class="mb-3">
            <div class="small text-muted mb-2">Select weekdays</div>
            <div class="d-flex flex-wrap gap-2">
              <button
                v-for="day in weekdays"
                :key="day.value"
                type="button"
                class="btn btn-sm"
                :class="selectedWeekdays.includes(day.value) ? 'btn-primary' : 'btn-outline-primary'"
                @click="toggleWeekday(day.value)"
              >
                {{ day.label }}
              </button>
            </div>
          </div>
          <div class="mb-3">
            <div class="small text-muted mb-2">Select time slot</div>
            <div class="d-flex flex-wrap gap-2">
              <button
                v-for="slot in presetSlots"
                :key="slot.key"
                type="button"
                class="btn btn-sm"
                :class="selectedPreset === slot.key ? 'btn-success' : 'btn-outline-success'"
                @click="selectedPreset = slot.key"
              >
                {{ slot.label }}
              </button>
            </div>
          </div>
          <button class="btn btn-dark" @click="savePresetAvailability">
            Save Weekly Slots
          </button>
        </div>

        <div class="small text-muted mb-2">Or add one custom slot manually</div>
        <form class="row g-2" @submit.prevent="addAvailability">
          <div class="col-md-3">
            <input v-model="slotForm.date" type="date" class="form-control" required>
          </div>
          <div class="col-md-3">
            <input v-model="slotForm.start_time" type="time" class="form-control" required>
          </div>
          <div class="col-md-3">
            <input v-model="slotForm.end_time" type="time" class="form-control" required>
          </div>
          <div class="col-md-3">
            <button class="btn btn-primary w-100">Save Slot</button>
          </div>
        </form>
      </div>
    </div>

    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h5 class="mb-3">Saved Slots</h5>
        <div v-if="availability.length" class="table-responsive">
          <table class="table table-bordered">
            <thead>
              <tr>
                <th>Date</th>
                <th>Start Time</th>
                <th>End Time</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="slot in availability" :key="slot.id">
                <td>{{ slot.date }}</td>
                <td>{{ slot.start_time }}</td>
                <td>{{ slot.end_time }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="text-muted mb-0">No slots added yet.</p>
      </div>
    </div>

    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h5 class="mb-3">Week Appointments</h5>
        <div class="table-responsive">
          <table class="table table-bordered align-middle">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th>Diagnosis</th>
                <th>Prescription</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="appointment in appointments" :key="appointment.id">
                <td>{{ appointment.patient.name }}</td>
                <td>{{ appointment.date }}</td>
                <td>{{ appointment.time }}</td>
                <td>{{ appointment.status }}</td>
                <td>
                  <input v-model="notes[appointment.id].diagnosis" class="form-control form-control-sm">
                </td>
                <td>
                  <input v-model="notes[appointment.id].prescription" class="form-control form-control-sm">
                </td>
                <td class="d-flex gap-2">
                  <button
                    class="btn btn-sm btn-success"
                    @click="completeAppointment(appointment.id)"
                    :disabled="appointment.status === 'completed'"
                  >
                    Complete
                  </button>
                  <button
                    class="btn btn-sm btn-outline-danger"
                    @click="cancelAppointment(appointment.id)"
                    :disabled="appointment.status === 'completed'"
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
        <h5 class="mb-3">Patients This Week</h5>
        <ul class="list-group">
          <li v-for="patient in patients" :key="patient.id" class="list-group-item">
            {{ patient.name }} - {{ patient.phone_number || "No phone" }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../services/api"

export default {
  data() {
    return {
      appointments: [],
      patients: [],
      availability: [],
      error: "",
      message: "",
      selectedPreset: "morning",
      selectedWeekdays: [],
      weekdays: [
        { label: "Mon", value: 0 },
        { label: "Tue", value: 1 },
        { label: "Wed", value: 2 },
        { label: "Thu", value: 3 },
        { label: "Fri", value: 4 },
        { label: "Sat", value: 5 },
        { label: "Sun", value: 6 }
      ],
      presetSlots: [
        { key: "morning", label: "Morning 09:00 - 11:00" },
        { key: "afternoon", label: "Afternoon 14:00 - 16:00" },
        { key: "evening", label: "Evening 18:00 - 20:00" }
      ],
      slotForm: {
        date: "",
        start_time: "",
        end_time: ""
      },
      notes: {}
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    prepareNotes() {
      this.notes = {}
      this.appointments.forEach((appointment) => {
        this.notes[appointment.id] = {
          diagnosis: appointment.treatment?.diagnosis || "",
          prescription: appointment.treatment?.prescription || "",
          notes: appointment.treatment?.notes || ""
        }
      })
    },
    async loadData() {
      const [dashboardRes, availabilityRes] = await Promise.all([
        api.get("/api/doctor/dashboard"),
        api.get("/api/doctor/availability")
      ])
      this.appointments = dashboardRes.data.week_appointments
      this.patients = dashboardRes.data.patients
      this.availability = availabilityRes.data.availability
      this.prepareNotes()
    },
    toggleWeekday(dayValue) {
      if (this.selectedWeekdays.includes(dayValue)) {
        this.selectedWeekdays = this.selectedWeekdays.filter((item) => item !== dayValue)
        return
      }
      this.selectedWeekdays.push(dayValue)
    },
    async savePresetAvailability() {
      this.error = ""
      this.message = ""
      try {
        const response = await api.post("/api/doctor/availability/preset", {
          weekdays: this.selectedWeekdays,
          slot_key: this.selectedPreset
        })
        this.message = `Weekly slots saved. Created ${response.data.created_count}, skipped ${response.data.skipped_count}.`
        await this.loadData()
      } catch (error) {
        this.error = error.response?.data?.message || "Could not save weekly slots"
      }
    },
    async addAvailability() {
      this.error = ""
      this.message = ""
      try {
        await api.post("/api/doctor/availability", this.slotForm)
        this.message = "Slot saved successfully"
        this.slotForm = { date: "", start_time: "", end_time: "" }
        await this.loadData()
      } catch (error) {
        this.error = error.response?.data?.message || "Could not save slot"
      }
    },
    async completeAppointment(appointmentId) {
      this.error = ""
      this.message = ""
      try {
        await api.post(`/api/doctor/appointments/${appointmentId}/complete`, this.notes[appointmentId])
        this.message = "Appointment marked as completed"
        await this.loadData()
      } catch (error) {
        this.error = error.response?.data?.message || "Could not complete appointment"
      }
    },
    async cancelAppointment(appointmentId) {
      this.error = ""
      this.message = ""
      try {
        await api.post(`/api/doctor/appointments/${appointmentId}/cancel`)
        this.message = "Appointment cancelled"
        await this.loadData()
      } catch (error) {
        this.error = error.response?.data?.message || "Could not cancel appointment"
      }
    }
  }
}
</script>
