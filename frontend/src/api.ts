import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: false,
});

function extractAccessToken(raw: string | null): string | null {
  if (!raw) return null;
  raw = raw.trim();
  // If stored as JSON string with access/refresh, try to parse
  if ((raw.startsWith('{') && raw.endsWith('}')) || (raw.startsWith('"') && raw.endsWith('"'))) {
    try {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        if (typeof parsed.access === 'string') return parsed.access;
        if (typeof parsed.token === 'string') return parsed.token;
      }
    } catch (e) {
      // not JSON, fallthrough
    }
  }
  // Basic JWT format check (three segments)
  const parts = raw.split('.');
  if (parts.length === 3) return raw;
  return null;
}

// 요청 인터셉터: 로그인 후 저장된 JWT 액세스 토큰을 모든 요청에 자동 첨부
apiClient.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem('access') || localStorage.getItem('access_token') || localStorage.getItem('token') || localStorage.getItem('auth');
    const token = extractAccessToken(raw);
    if (token) {
      const headers = (config.headers as any) || {};
      const currentAuth = headers.Authorization || headers.authorization;
      if (!currentAuth) {
        (config.headers as any).Authorization = `Bearer ${token}`;
      }
    }
  } catch (err) {
    // ignore
  }
  return config;
});

// 응답 인터셉터: 401 발생 시 토큰 제거 및 로그인 페이지로 리다이렉트
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      try {
        localStorage.removeItem('access');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh');
        localStorage.removeItem('token');
        localStorage.removeItem('auth');
      } catch (e) {}
      // redirect to login page (force full reload to clear app state)
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface UserMe {
  id: number;
  username: string;
  email: string;
  status: string;
  date_joined: string;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("/accounts/token/", {
    username,
    password,
  });
  return response.data;
}

export async function signup(username: string, email: string, password: string) {
  const response = await apiClient.post("/accounts/signup/", {
    username,
    email,
    password,
  });
  return response.data;
}

export async function fetchMe(accessToken: string): Promise<UserMe> {
  const response = await apiClient.get<UserMe>("/accounts/me/", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  return response.data;
}
