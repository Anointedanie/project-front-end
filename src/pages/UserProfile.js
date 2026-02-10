import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import './UserProfile.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const UserProfile = () => {
  const { user, logout } = useAuth();
  
  // Profile update form
  const [profileData, setProfileData] = useState({
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
    phone: user?.phone || '',
    email: user?.email || ''
  });
  
  // Password change form
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  
  const [profileLoading, setProfileLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  
  const handleProfileChange = (e) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value
    });
  };
  
  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value
    });
  };
  
  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileError('');
    setProfileSuccess('');
    setProfileLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(
        `${API_URL}/auth/profile/`,
        {
          first_name: profileData.firstName,
          last_name: profileData.lastName,
          phone: profileData.phone,
          email: profileData.email
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      setProfileSuccess('Profile updated successfully!');
      setTimeout(() => setProfileSuccess(''), 3000);
    } catch (error) {
      setProfileError(error.response?.data?.message || error.response?.data?.error || 'Failed to update profile');
    } finally {
      setProfileLoading(false);
    }
  };
  
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');
    
    // Validate passwords match
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }
    
    // Validate password length
    if (passwordData.newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }
    
    setPasswordLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/auth/change-password/`,
        {
          old_password: passwordData.oldPassword,
          new_password: passwordData.newPassword,
          new_password2: passwordData.confirmPassword
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      setPasswordSuccess('Password changed successfully! Please login again.');
      
      // Clear form
      setPasswordData({
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
      
      // Logout after 2 seconds
      setTimeout(() => {
        logout();
      }, 2000);
    } catch (error) {
      setPasswordError(error.response?.data?.message || error.response?.data?.error || 'Failed to change password');
    } finally {
      setPasswordLoading(false);
    }
  };
  
  return (
    <div className="profile-container fade-in">
      <div className="profile-header">
        <h1>My Profile</h1>
        <p>Manage your account settings</p>
      </div>
      
      <div className="profile-content">
        {/* Profile Update Section */}
        <div className="profile-section">
          <h2>Profile Information</h2>
          
          <form onSubmit={handleProfileSubmit} className="profile-form">
            {profileError && (
              <div className="alert alert-error">
                {profileError}
              </div>
            )}
            
            {profileSuccess && (
              <div className="alert alert-success">
                {profileSuccess}
              </div>
            )}
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="firstName" className="form-label">First Name</label>
                <input
                  id="firstName"
                  name="firstName"
                  type="text"
                  className="form-input"
                  value={profileData.firstName}
                  onChange={handleProfileChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="lastName" className="form-label">Last Name</label>
                <input
                  id="lastName"
                  name="lastName"
                  type="text"
                  className="form-input"
                  value={profileData.lastName}
                  onChange={handleProfileChange}
                  required
                />
              </div>
            </div>
            
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email Address</label>
              <input
                id="email"
                name="email"
                type="email"
                className="form-input"
                value={profileData.email}
                onChange={handleProfileChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="phone" className="form-label">Phone Number</label>
              <input
                id="phone"
                name="phone"
                type="tel"
                className="form-input"
                value={profileData.phone}
                onChange={handleProfileChange}
                placeholder="+234..."
              />
            </div>
            
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={profileLoading}
            >
              {profileLoading ? 'Updating...' : 'Update Profile'}
            </button>
          </form>
        </div>
        
        {/* Password Change Section */}
        <div className="profile-section">
          <h2>Change Password</h2>
          
          <form onSubmit={handlePasswordSubmit} className="profile-form">
            {passwordError && (
              <div className="alert alert-error">
                {passwordError}
              </div>
            )}
            
            {passwordSuccess && (
              <div className="alert alert-success">
                {passwordSuccess}
              </div>
            )}
            
            <div className="form-group">
              <label htmlFor="oldPassword" className="form-label">Current Password</label>
              <input
                id="oldPassword"
                name="oldPassword"
                type="password"
                className="form-input"
                value={passwordData.oldPassword}
                onChange={handlePasswordChange}
                required
                placeholder="Enter current password"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="newPassword" className="form-label">New Password</label>
              <input
                id="newPassword"
                name="newPassword"
                type="password"
                className="form-input"
                value={passwordData.newPassword}
                onChange={handlePasswordChange}
                required
                placeholder="Minimum 8 characters"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="confirmPassword" className="form-label">Confirm New Password</label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                className="form-input"
                value={passwordData.confirmPassword}
                onChange={handlePasswordChange}
                required
                placeholder="Re-enter new password"
              />
            </div>
            
            <button 
              type="submit" 
              className="btn btn-gold"
              disabled={passwordLoading}
            >
              {passwordLoading ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
