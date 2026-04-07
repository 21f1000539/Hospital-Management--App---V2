import { createRouter, createWebHistory } from "vue-router"
import AdminDashboard from "../views/AdminDashboard.vue"
import DoctorDashboard from "../views/DoctorDashboard.vue"
import LoginView from "../views/LoginView.vue"
import PatientDashboard from "../views/PatientDashboard.vue"
import RegisterView from "../views/RegisterView.vue"

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: LoginView },
  { path: "/register", component: RegisterView },
  { path: "/admin", component: AdminDashboard, meta: { role: "admin" } },
  { path: "/doctor", component: DoctorDashboard, meta: { role: "doctor" } },
  { path: "/patient", component: PatientDashboard, meta: { role: "patient" } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const savedUser = localStorage.getItem("user")
  const user = savedUser ? JSON.parse(savedUser) : null

  if (to.meta.role && (!user || user.role !== to.meta.role)) {
    next("/login")
    return
  }

  if ((to.path === "/login" || to.path === "/register") && user) {
    next(`/${user.role}`)
    return
  }

  next()
})

export default router
