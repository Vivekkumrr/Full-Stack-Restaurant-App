// src/services/api.js

import axios from 'axios';
import Cookies from 'js-cookie';


const BACKEND_API = import.meta.env.VITE_API_URL || '/api';

const setSession = (user) => {
  if (user) {
    localStorage.setItem('user', JSON.stringify(user));
  } else {
    localStorage.removeItem('user');
  }
};

const normalizeUser = (user) => {
  if (!user) return null;
  return {
    ...user,
    user_type:
      user.user_type ||
      (user.is_superuser ? 'admin' : user.is_staff ? 'staff' : user.role === 'customer' ? 'member' : user.role || 'member'),
    name: user.username || user.first_name || 'Customer',
    points: 0,
    vipStatus: 'Customer'
  };
};

// Axios instance for backend calls
// Basic Auth and Session Auth rely on cookies and credentials
const axiosInstance = axios.create({
  baseURL: BACKEND_API,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Set CSRF Token for all requests if it exists in cookies
axiosInstance.interceptors.request.use(
  (config) => {
    const csrfToken = Cookies.get('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Generic post helper for the backend using axiosInstance
const post = async (endpoint, body) => {
  try {
    const csrfToken = Cookies.get('csrftoken');
    if (!csrfToken) {
      try {
        await axiosInstance.get('/csrf');
      } catch (e) {
        console.error('Unable to fetch CSRF cookie:', e);
      }
    }
    const response = await axiosInstance.post(endpoint, body);
    const data = response.data;
    
    if (endpoint === '/login' && data.success && data.user) {
      const user = normalizeUser(data.user);
      setSession(user);
      return {
        data: {
          ...data,
          user
        },
        status: response.status
      };
    }

    if (data.success && data.user) {
      setSession(normalizeUser(data.user));
    }

    return { data, status: response.status };
  } catch (error) {
    console.error(`API post error (${endpoint}):`, error);
    // Return data from error response if available
    if (error.response) {
      return { data: error.response.data, status: error.response.status };
    }
    throw error;
  }
};

const get = async (endpoint) => {
  try {
    const response = await axiosInstance.get(endpoint);
    return { data: response.data, status: response.status };
  } catch (error) {
    if (error.response) {
      if (error.response.status !== 401) {
        console.error(`API get error (${endpoint}):`, error);
      }
      return { data: error.response.data, status: error.response.status };
    }
    console.error(`API get error (${endpoint}):`, error);
    throw error;
  }
};

export const tableAPI = {
  async getAll() {
    const { data } = await get('/tables/');
    return data;
  },
  async getAvailable({ date, time, guests }) {
    const { data } = await get(`/tables/?is_available=true&date=${date}&time=${time}&guests=${guests}`);
    return data;
  },
  async create(payload) {
    const { data } = await post('/tables/', payload);
    return data;
  },
  async update(id, payload) {
    try {
      const response = await axiosInstance.patch(`/tables/${id}/`, payload);
      return response.data;
    } catch (error) {
      if (error.response) return error.response.data;
      throw error;
    }
  },
  async delete(id) {
    try {
      const response = await axiosInstance.delete(`/tables/${id}/`);
      return { success: true, status: response.status };
    } catch (error) {
      if (error.response) return { success: false, data: error.response.data, status: error.response.status };
      throw error;
    }
  },
};

export const reservationAPI = {
  async create(data) {
    const { data: res } = await post('/reservations/', data);
    return res;
  },

  async getAll() {
    const { data } = await get('/reservations/');
    return data;
  },

  async updateStatus(id, status) {
    try {
      const response = await axiosInstance.patch(`/reservations/${id}/`, { status });
      return response.data;
    } catch (error) {
      if (error.response) return error.response.data;
      throw error;
    }
  },

  async getMyReservations() {
    const { data } = await get('/my-reservations');
    return data;
  },

  async cancel(id) {
    const { data } = await post(`/my-reservations/${id}/cancel`, {});
    return data;
  },

  async delete(id) {
    try {
      const response = await axiosInstance.delete(`/reservations/${id}/`);
      return { success: true, status: response.status };
    } catch (error) {
      if (error.response) return { success: false, data: error.response.data, status: error.response.status };
      throw error;
    }
  },
};

export const authAPI = {
  async getCSRFToken() {
    try {
      const response = await axiosInstance.get('/csrf');
      return response.data;
    } catch (error) {
      console.error('getCSRFToken error:', error);
      throw error;
    }
  },

  async checkSession() {
    try {
      const { data, status } = await get('/me');
      if (status === 200 && data.success && data.user) {
        const userData = normalizeUser(data.user);
        setSession(userData);
        return {
          success: true,
          data: userData
        };
      }
      setSession(null);
      return { success: false, error: 'Session invalid' };
    } catch (error) {
      setSession(null);
      if (error?.response?.status === 401) {
        return { success: false, error: 'Session invalid' };
      }
      console.error('checkSession error:', error);
      return { success: false, error: 'Network error' };
    }
  },

  async login(credentials) {
    const { data } = await post('/login', credentials);
    return data;
  },

  async register(userData) {
    const { data } = await post('/register', userData);
    if (data.success && data.user) {
      const user = normalizeUser(data.user);
      setSession(user);
      return {
        ...data,
        user
      };
    }
    return data;
  },

  async logout() {
    try {
      const { data, status } = await post('/logout', {});
      setSession(null);
      return { data, status };
    } catch (error) {
      console.error('logout error:', error);
      setSession(null);
      return { success: false, error: error.message };
    }
  },

  async adminLogout() {
    return this.logout();
  },
};

export default { authAPI, reservationAPI, tableAPI, post };