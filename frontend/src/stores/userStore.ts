import { reactive, readonly, computed } from 'vue'
import { apiClient } from '../api'

const state = reactive({
  id: null as number | null,
  username: '',
  nickname: '',
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  avatar: '' as string | null,
  role: '' as string | null,
  isAuthenticated: false,
})

export function useUser() {
  function setUser(payload: Partial<typeof state>) {
    Object.assign(state, payload)
  }

  async function fetchMe() {
    try {
      const res = await apiClient.get('/accounts/profile/me/')
      const data = res.data
      setUser({
        id: data.id || null,
        username: data.username || '',
        nickname: data.nickname || '',
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        email: data.email || '',
        phone_number: data.phone_number || '',
        avatar: data.avatar || null,
        isAuthenticated: true,
      })
      return data
    } catch (err) {
      console.error('Failed to fetch profile', err)
      throw err
    }
  }

  function updateUser(payload: Partial<typeof state>) {
    setUser(payload)
  }

  async function logout() {
    // Call backend logout API to blacklist refresh token
    try {
      const refresh = localStorage.getItem('refresh');
      if (refresh) {
        await apiClient.post('/accounts/logout/', { refresh });
      }
    } catch (err) {
      console.error('Failed to call logout API', err);
      // Continue with client-side logout even if API call fails
    }

    // Clear all tokens from localStorage
    try {
      localStorage.removeItem('access')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh')
      localStorage.removeItem('token')
      localStorage.removeItem('auth')
    } catch (e) {
      console.error('Failed to clear tokens', e)
    }

    // Reset user state
    setUser({
      id: null,
      username: '',
      nickname: '',
      first_name: '',
      last_name: '',
      email: '',
      phone_number: '',
      avatar: null,
      role: null,
      isAuthenticated: false,
    })
  }

  // Check if user has a valid token
  function checkAuth() {
    const token = localStorage.getItem('access') || localStorage.getItem('access_token')
    if (token) {
      state.isAuthenticated = true
      return true
    }
    state.isAuthenticated = false
    return false
  }

  const isLoggedIn = computed(() => state.isAuthenticated)

  return {
    user: readonly(state),
    isLoggedIn,
    setUser,
    fetchMe,
    updateUser,
    logout,
    checkAuth,
  }
}
