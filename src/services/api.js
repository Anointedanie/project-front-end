import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Authentication APIs
export const authAPI = {
  // User login
  loginUser: (email, password) =>
    apiClient.post('/auth/login', { email, password }),

  // Admin login
  loginAdmin: (email, password) =>
    apiClient.post('/auth/admin/login', { email, password }),

  // Register user
  register: (userData) =>
    apiClient.post('/auth/register', userData),

  // Logout
  logout: () =>
    apiClient.post('/auth/logout'),

  // Verify token
  verifyToken: () =>
    apiClient.get('/auth/verify'),
};

// Product APIs
export const productAPI = {
  // Get all products
  getAllProducts: () => 
    apiClient.get('/products/'),
  
  // Get single product
  getProduct: (id) => 
    apiClient.get(`/products/${id}/`),
  
  // Create product (admin only)
  createProduct: (productData) => 
    apiClient.post('/products/', productData),
  
  // Update product (admin only)
  updateProduct: (id, productData) => 
    apiClient.put(`/products/${id}/`, productData),
  
  // Delete product (admin only)
  deleteProduct: (id) => 
    apiClient.delete(`/products/${id}/`),
};

// Cart APIs
export const cartAPI = {
  // Get user's cart
  getCart: () => 
    apiClient.get('/cart/'),
  
  // Add item to cart
  addToCart: (productId, quantity) => 
    apiClient.post('/cart/add/', { product_id: productId, quantity }),
  
  // Update cart item
  updateCartItem: (itemId, quantity) => 
    apiClient.put(`/cart/items/${itemId}/`, { quantity }),
  
  // Remove item from cart
  removeFromCart: (itemId) => 
    apiClient.delete(`/cart/items/${itemId}/`),
  
  // Clear cart
  clearCart: () => 
    apiClient.delete('/cart/clear/'),
};

// Order APIs
export const orderAPI = {
  // Create order
  createOrder: (orderData) => 
    apiClient.post('/orders/', orderData),
  
  // Get user orders
  getUserOrders: () => 
    apiClient.get('/orders/'),
  
  // Get single order
  getOrder: (id) => 
    apiClient.get(`/orders/${id}/`),
};

export default apiClient;
