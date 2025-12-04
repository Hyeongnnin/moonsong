import { reactive, readonly } from 'vue'
import { apiClient } from '../api'

const state = reactive({
  id: null as number | null,
  username: '',
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  avatar: '' as string | null,
  role: '' as string | null,
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
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        email: data.email || '',
        phone_number: data.phone_number || '',
        avatar: data.avatar || null,
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

  return {
    user: readonly(state),
    setUser,
    fetchMe,
    updateUser,
  }
}
