import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../components/LandingPage.vue'
import LoginPage from '../components/LoginPage.vue'
import SignupPage from '../components/SignupPage.vue'
import PersonalSignupForm from '../components/PersonalSignupForm.vue'
import LawyerSignupForm from '../components/LawyerSignupForm.vue'
import RightsDiagnosisPage from '../components/RightsDiagnosisPage.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingPage },
  { path: '/login', name: 'login', component: LoginPage },
  { path: '/signup', name: 'signup', component: SignupPage },
  { path: '/signup/personal', name: 'personal-signup', component: PersonalSignupForm },
  { path: '/signup/lawyer', name: 'lawyer-signup', component: LawyerSignupForm },
  { path: '/rights-check', name: 'rights-check', component: RightsDiagnosisPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
