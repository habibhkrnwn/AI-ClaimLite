const API_BASE_URL = 'http://localhost:3001';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  active_until?: string | null;
  created_at: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  data: {
    user: User;
    accessToken: string;
    refreshToken: string;
  };
}

export interface RegisterResponse {
  success: boolean;
  message: string;
  data: User;
}

export interface ApiError {
  success: false;
  message: string;
}

class ApiService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    // Load tokens from localStorage on initialization
    this.accessToken = localStorage.getItem('accessToken');
    this.refreshToken = localStorage.getItem('refreshToken');
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  getAccessToken() {
    return this.accessToken;
  }

  async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Request failed');
      }

      return data;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  // Auth endpoints
  async register(email: string, password: string, full_name: string): Promise<RegisterResponse> {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    });
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.success && response.data) {
      this.setTokens(response.data.accessToken, response.data.refreshToken);
    }

    return response;
  }

  async logout(): Promise<void> {
    try {
      if (this.refreshToken) {
        await this.request('/api/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refreshToken: this.refreshToken }),
        });
      }
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.request('/api/auth/me');
    return response.data;
  }

  async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.request('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refreshToken: this.refreshToken }),
    });

    if (response.success && response.data) {
      this.accessToken = response.data.accessToken;
      localStorage.setItem('accessToken', response.data.accessToken);
      return response.data.accessToken;
    }

    throw new Error('Token refresh failed');
  }

  // Admin endpoints (Admin Meta only)
  async createAdminRS(data: {
    email: string;
    password: string;
    full_name: string;
    active_until?: string | null;
  }): Promise<{ success: boolean; message: string; data: User }> {
    return this.request('/api/admin/admin-rs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAllAdminRS(): Promise<{ success: boolean; data: User[] }> {
    return this.request('/api/admin/admin-rs');
  }

  async updateAdminRSStatus(
    userId: number,
    data: {
      is_active?: boolean;
      active_until?: string | null;
    }
  ): Promise<{ success: boolean; message: string; data: User }> {
    return this.request(`/api/admin/admin-rs/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteAdminRS(userId: number): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/admin/admin-rs/${userId}`, {
      method: 'DELETE',
    });
  }

  async checkExpiredAccounts(): Promise<{ success: boolean; message: string; data: { deactivated_count: number } }> {
    return this.request('/api/admin/admin-rs/check-expiration', {
      method: 'POST',
    });
  }

  // Analysis endpoints
  async logAnalysis(data: {
    diagnosis: string;
    procedure: string;
    medication: string;
  }): Promise<{ success: boolean; message: string; data: any }> {
    return this.request('/api/analysis/log', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMyAnalysisLogs(limit?: number): Promise<{ success: boolean; data: any[] }> {
    const url = limit ? `/api/analysis/my-logs?limit=${limit}` : '/api/analysis/my-logs';
    return this.request(url);
  }

  async getMyAnalysisCount(): Promise<{ success: boolean; data: { count: number } }> {
    return this.request('/api/analysis/my-count');
  }

  // Statistics endpoints (Admin Meta only)
  async getUserStatistics(): Promise<{ success: boolean; data: any[] }> {
    return this.request('/api/admin/statistics/users');
  }

  async getOverallStatistics(): Promise<{ success: boolean; data: any }> {
    return this.request('/api/admin/statistics/overall');
  }

  // AI Analysis endpoints
  async analyzeClaimAI(data: {
    mode?: 'form' | 'text';
    diagnosis?: string;
    procedure?: string;
    medication?: string;
    input_text?: string;
  }): Promise<{ 
    success: boolean; 
    data: any;
    usage?: { used: number; remaining: number; limit: number };
  }> {
    return this.request('/api/ai/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async validateClaimInput(data: {
    diagnosis: string;
    procedure: string;
    medication: string;
  }): Promise<{ success: boolean; data: any }> {
    return this.request('/api/ai/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Get AI usage status
  async getAIUsageStatus(): Promise<{ success: boolean; data: { used: number; remaining: number; limit: number } }> {
    return this.request('/api/ai/usage', {
      method: 'GET',
    });
  }
}

export const apiService = new ApiService();
export default apiService;
