import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authentication token to requests
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage (or wherever it's stored)
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 responses (unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token');
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
