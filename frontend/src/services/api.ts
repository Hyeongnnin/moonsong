import axios from 'axios'

const resolvedBaseUrl =
  import.meta.env.VITE_API_BASE_URL ?? (typeof window !== 'undefined' ? window.location.origin : '')

const api = axios.create({
  baseURL: resolvedBaseUrl,
})

export default api
