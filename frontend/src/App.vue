<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container">
        <router-link class="navbar-brand fw-bold" to="/">Hospital HMS</router-link>
        <div class="d-flex align-items-center gap-2">
          <span v-if="user" class="text-white small">
            {{ user.name }} ({{ user.role }})
          </span>
          <button v-if="user" class="btn btn-sm btn-light" @click="logout">
            Logout
          </button>
        </div>
      </div>
    </nav>

    <div class="container py-4">
      <router-view @logged-in="loadUser"></router-view>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      user: null
    }
  },
  mounted() {
    this.loadUser()
  },
  methods: {
    loadUser() {
      const savedUser = localStorage.getItem("user")
      this.user = savedUser ? JSON.parse(savedUser) : null
    },
    logout() {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      this.user = null
      this.$router.push("/login")
    }
  }
}
</script>
