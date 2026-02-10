import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');
    
    if (token) {
      verifyAuthentication();
    } else {
      setLoading(false);
    }
    
    if (userType === 'admin') {
      setIsAdmin(true);
    }
  }, []);

  const verifyAuthentication = async () => {
    try {
      const response = await authAPI.verifyToken();
      setUser(response.data.user);
      setLoading(false);
    } catch (error) {
      // Token is invalid, clear storage
      localStorage.removeItem('token');
      localStorage.removeItem('userType');
      setUser(null);
      setIsAdmin(false);
      setLoading(false);
    }
  };

  const login = async (email, password, isAdminLogin = false) => {
    try {
      const response = isAdminLogin 
        ? await authAPI.loginAdmin(email, password)
        : await authAPI.loginUser(email, password);
      
      const { tokens, user } = response.data;
      
      // Store access token (backend returns tokens.access and tokens.refresh)
      localStorage.setItem('token', tokens.access);
      localStorage.setItem('userType', isAdminLogin ? 'admin' : 'user');
      
      setUser(user);
      setIsAdmin(isAdminLogin);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || error.response?.data?.error || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      const { tokens, user } = response.data;
      
      // Store access token (backend returns tokens.access and tokens.refresh)
      localStorage.setItem('token', tokens.access);
      localStorage.setItem('userType', 'user');
      
      setUser(user);
      setIsAdmin(false);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || error.response?.data?.error || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    setUser(null);
    setIsAdmin(false);
  };

  const value = {
    user,
    isAdmin,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
