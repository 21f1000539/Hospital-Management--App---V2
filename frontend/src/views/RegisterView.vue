<template>
  <div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
      <div class="card shadow-sm">
        <div class="card-body">
          <h3 class="mb-3 text-center">Patient Register</h3>
          <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
          <div v-if="success" class="alert alert-success py-2">{{ success }}</div>

          <form @submit.prevent="registerUser">
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Name</label>
                <input v-model="form.name" class="form-control" required>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Email</label>
                <input v-model="form.email" type="email" class="form-control" required>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Password</label>
                <input v-model="form.password" type="password" class="form-control" required>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Phone</label>
                <input v-model="form.phone_number" class="form-control">
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">Age</label>
                <input v-model="form.age" type="number" class="form-control">
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">Gender</label>
                <input v-model="form.gender" class="form-control">
              </div>
              <div class="col-md-4 mb-3">
                <label class="form-label">Emergency Contact</label>
                <input v-model="form.emergency_contact" class="form-control">
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Address</label>
              <textarea v-model="form.address" class="form-control" rows="2"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Medical History</label>
              <textarea v-model="form.medical_history" class="form-control" rows="3"></textarea>
            </div>
            <button class="btn btn-success w-100" :disabled="loading">
              {{ loading ? "Creating..." : "Create Account" }}
            </button>
          </form>
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
      loading: false,
      error: "",
      success: "",
      form: {
        name: "",
        email: "",
        password: "",
        age: "",
        gender: "",
        phone_number: "",
        address: "",
        emergency_contact: "",
        medical_history: ""
      }
    }
  },
  methods: {
    async registerUser() {
      this.loading = true
      this.error = ""
      this.success = ""
      try {
        await api.post("/api/auth/register", this.form)
        this.success = "Registration successful. You can log in now."
        this.form = {
          name: "",
          email: "",
          password: "",
          age: "",
          gender: "",
          phone_number: "",
          address: "",
          emergency_contact: "",
          medical_history: ""
        }
      } catch (error) {
        this.error = error.response?.data?.message || "Registration failed"
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
