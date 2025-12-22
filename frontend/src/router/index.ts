import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

const MainLayout = () => import("../components/MainLayout.vue");

// Public pages
const LandingPage = () => import("../components/LandingPage.vue");
const LoginPage = () => import("../components/LoginPage.vue");
const SignupPage = () => import("../components/SignupPage.vue");

// Profile edit page
const EditProfile = () => import("../pages/EditProfile.vue");

const routes: Array<RouteRecordRaw> = [
  // Public pages under PublicLayout (root '/')
  {
    path: "/",
    component: () => import("../components/PublicLayout.vue"),
    children: [
      { path: "", component: LandingPage },
      { path: "login", component: LoginPage },
      { path: "signup", component: SignupPage },
    ],
  },

  // Main app layout mounted at /dashboard
  // All section switching (labor, ai-consult, profile-edit, documents) happens internally via state
  {
    path: "/dashboard",
    component: MainLayout,
  },

  // Edit profile page (standalone)
  {
    path: "/edit-profile",
    component: EditProfile,
  },

  // fallback redirect
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard to protect authenticated routes
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access') || localStorage.getItem('access_token');
  const isAuthenticated = !!token;

  // Protected routes that require authentication
  const protectedRoutes = ['/dashboard', '/edit-profile'];
  const isProtectedRoute = protectedRoutes.some(route => to.path.startsWith(route));

  // If trying to access protected route without authentication
  if (isProtectedRoute && !isAuthenticated) {
    next('/login');
  } 
  // If already authenticated and trying to access login/signup
  else if (isAuthenticated && (to.path === '/login' || to.path === '/signup')) {
    next('/dashboard');
  }
  // Otherwise allow navigation
  else {
    next();
  }
});

export default router;
