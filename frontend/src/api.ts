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
let isRefreshing = false;
let pendingQueue: Array<(token: string | null) => void> = [];

function onRefreshed(token: string | null) {
  pendingQueue.forEach((cb) => cb(token));
  pendingQueue = [];
}

apiClient.interceptors.response.use(
  (response) => {
    try {
      const method = (response.config.method || '').toUpperCase();
      const url = response.config.url || '';
      // 근로기록 저장/수정/삭제 및 월 스케줄 저장 후 갱신 이벤트 발생
      const isMutating = method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE';
      if (isMutating) {
        const u = url.replace(apiBaseUrl, '');
        const isWorkRecord = /\/labor\/work-records\/?/.test(u);
        const isJobSchedules = /\/labor\/jobs\/\d+\/(schedules|monthly-schedule-override|monthly-schedule|monthly-work-records)\/?/.test(u);
        if ((isWorkRecord || isJobSchedules) && typeof window !== 'undefined') {
          window.dispatchEvent(new Event('labor-updated'));
        }
      }
    } catch (_) {
      // ignore
    }
    return response;
  },
  async (error) => {
    const status = error?.response?.status;
    const originalRequest = error?.config || {};
    if (typeof window !== 'undefined') {
      console.error('[api] error response', status, error?.response?.data || error?.message);
    }

    // 401 처리: refresh 토큰으로 갱신 시도 후 1회 재시도
    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refresh = localStorage.getItem('refresh');
        if (!refresh) throw new Error('no-refresh');

        if (isRefreshing) {
          // 다른 요청이 갱신 중이면 큐에 대기 후 재시도
          return new Promise((resolve, reject) => {
            pendingQueue.push((newToken) => {
              if (!newToken) {
                reject(error);
                return;
              }
              try {
                originalRequest.headers = originalRequest.headers || {};
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
                resolve(apiClient(originalRequest));
              } catch (e) {
                reject(e);
              }
            });
          });
        }

        isRefreshing = true;
        const refreshRes = await axios.post(`${apiBaseUrl}/accounts/token/refresh/`, { refresh });
        const newAccess = refreshRes.data?.access as string | undefined;
        if (!newAccess) throw new Error('no-access');
        // 저장 및 기본 헤더 갱신
        localStorage.setItem('access', newAccess);
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccess}`;
        onRefreshed(newAccess);
        // 원 요청 재시도
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers['Authorization'] = `Bearer ${newAccess}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        // 갱신 실패: 토큰 정리 후 로그인 페이지로
        try {
          localStorage.removeItem('access');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh');
          localStorage.removeItem('token');
          localStorage.removeItem('auth');
        } catch (e) { }
        onRefreshed(null);
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
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

export async function signup(username: string, nickname: string, email: string, password: string) {
  const response = await apiClient.post("/accounts/signup/", {
    username,
    nickname,
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

// Documents API helpers
export interface DocumentTemplate {
  id: number;
  name: string;
  doc_type: string;
  description?: string;
  required_fields_json?: any;
  file_path?: string;
  is_active?: boolean;
}

export interface GeneratedDocument {
  id: number;
  template: number | DocumentTemplate | null;
  doc_type?: string | null;  // ✅ B 프로젝트 병합: 템플릿 없이도 서류 유형 지정 가능
  title?: string | null;
  user: number;
  employee?: number | null;
  consultation?: number | null;
  filled_data_json?: any;
  file_url?: string | null;
  status?: string;
  created_at?: string;
}

export async function fetchTemplates(): Promise<DocumentTemplate[]> {
  const res = await apiClient.get<DocumentTemplate[]>("/documents/templates/");
  return res.data;
}

export async function fetchGenerated(): Promise<GeneratedDocument[]> {
  const res = await apiClient.get<GeneratedDocument[]>("/documents/generated/");
  return res.data;
}

export async function createGenerated(payload: FormData): Promise<GeneratedDocument> {
  const res = await apiClient.post<GeneratedDocument>("/documents/generated/", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function deleteGenerated(id: number): Promise<void> {
  await apiClient.delete(`/documents/generated/${id}/`);
}

export async function updateGenerated(id: number, payload: FormData): Promise<GeneratedDocument> {
  const res = await apiClient.patch<GeneratedDocument>(`/documents/generated/${id}/`, payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}


// ===================================================================
// ✅ B 프로젝트 병합: 이력서 자동 생성 API
// ===================================================================

export interface ResumeExperience {
  company?: string;
  role?: string;
  period?: string;
  achievements?: string[];
  description?: string;
}

export interface ResumeEducation {
  school?: string;
  major?: string;
  period?: string;
  description?: string;
}

export interface ResumePayload {
  name: string;
  title?: string;
  phone?: string;
  email?: string;
  address?: string;
  summary?: string;
  experiences?: ResumeExperience[];
  educations?: ResumeEducation[];
  skills?: string[];
  certifications?: string[];
  languages?: string[];
  save_to_documents?: boolean;
  document_title?: string;
  status?: string;
}

export async function generateResumeDocx(payload: ResumePayload): Promise<{
  blob: Blob;
  filename: string;
  saved: boolean;
  url?: string
}> {
  const res = await apiClient.post(`/documents/resume/generate/`, payload, {
    responseType: 'blob',
  });

  const disposition = res.headers['content-disposition'] || '';
  const match = disposition.match(/filename="?([^";]+)"?/);
  const filename = match ? decodeURIComponent(match[1]) : 'resume.docx';
  const saved = res.headers['x-document-saved'] === 'true';
  const url = res.headers['x-document-url'];
  return { blob: res.data as Blob, filename, saved, url };
}

// ===================================================================
// AI 상담 API
// ===================================================================

export interface AiConsultationResponse {
  consultation_id: number;
  answer: string;
}

export async function aiConsult(content: string, title?: string, category?: string): Promise<AiConsultationResponse> {
  const response = await apiClient.post<AiConsultationResponse>("/consultations/ai-consult/", {
    title,
    content,
    category,
  });
  return response.data;
}
