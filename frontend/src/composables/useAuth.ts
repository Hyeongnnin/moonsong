import { computed, ref } from 'vue'

export interface AuthUser {
  id: number
  username: string
  email: string
  role: string
  phone: string
  birth_date: string
  gender: string
  first_name: string
}

const STORAGE_KEY = 'notav-auth-user'

const readFromStorage = (): AuthUser | null => {
  if (typeof window === 'undefined') {
    return null
  }
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return null
  }
  try {
    return JSON.parse(raw) as AuthUser
  } catch (error) {
    console.error('Failed to parse stored auth user', error)
    window.localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

const currentUser = ref<AuthUser | null>(readFromStorage())

const persistUser = (user: AuthUser | null) => {
  if (typeof window === 'undefined') {
    return
  }
  if (user) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
  } else {
    window.localStorage.removeItem(STORAGE_KEY)
  }
}

export const useAuth = () => {
  const setUser = (user: AuthUser | null) => {
    currentUser.value = user
    persistUser(user)
  }

  const logout = () => setUser(null)

  const displayName = computed(() => {
    const user = currentUser.value
    if (!user) return ''
    return user.first_name?.trim() || user.username
  })

  return {
    currentUser,
    isLoggedIn: computed(() => Boolean(currentUser.value)),
    setUser,
    logout,
    displayName,
  }
}
