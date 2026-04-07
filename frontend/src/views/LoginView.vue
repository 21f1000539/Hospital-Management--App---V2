<template>
  <div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
      <div class="card shadow-sm">
        <div class="card-body">
          <h3 class="mb-3 text-center">Login</h3>
          <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

          <form @submit.prevent="loginUser">
            <div class="mb-3">
              <label class="form-label">Role</label>
              <select v-model="form.role" class="form-select" required>
                <option value="">Select role</option>
                <option value="admin">Admin</option>
                <option value="doctor">Doctor</option>
                <option value="patient">Patient</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="form.email" type="email" class="form-control" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <input v-model="form.password" type="password" class="form-control" required>
            </div>
            <button class="btn btn-primary w-100" :disabled="loading">
              {{ loading ? "Logging in..." : "Login" }}
            </button>
          </form>

          <p class="text-center mt-3 mb-0">
            Patient? <router-link to="/register">Create account</router-link>
          </p>
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
      form: {
        role: "",
        email: "",
        password: ""
      }
    }
  },
  methods: {
    async loginUser() {
      this.loading = true
      this.error = ""
      try {
        const response = await api.post("/api/auth/login", this.form)
        localStorage.setItem("token", response.data.token)
        localStorage.setItem("user", JSON.stringify(response.data.user))
        this.$emit("logged-in")
        this.$router.push(`/${response.data.user.role}`)
      } catch (error) {
        this.error = error.response?.data?.message || "Login failed"
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
