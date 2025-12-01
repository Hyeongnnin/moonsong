import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: false,
});

// 요청 인터셉터: 로그인 후 저장된 JWT 액세스 토큰을 모든 요청에 자동 첨부
apiClient.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem("access") || localStorage.getItem("access_token");
    if (token) {
      // axios may separate headers by method; normalize to headers as Record<string, any>
      const headers: Record<string, any> = (config.headers as any) || {};
      const currentAuth = headers.Authorization || headers.authorization;
      if (!currentAuth) {
        headers.Authorization = `Bearer ${token}`;
      }
      config.headers = headers;
    }
  } catch {
    // ignore
  }
  return config;
});

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
