# E-Commerce Frontend - Authentication Demo

A React-based e-commerce frontend where **only authentication is functional** with the Django backend. All other features (products, cart, checkout) use static/mock data for demonstration purposes.

## 🎯 What's Functional vs Static

### ✅ Fully Functional (Backend Integration)
- **User Login** - Connects to Django `/api/auth/login/`
- **User Registration** - Connects to Django `/api/auth/register/`  
- **Admin Login** - Connects to Django `/api/auth/admin/login/`
- **Profile Update** - Connects to Django `PUT /api/auth/profile/` ⭐ NEW
- **Change Password** - Connects to Django `POST /api/auth/change-password/` ⭐ NEW
- **Token Management** - JWT tokens stored in localStorage
- **Protected Routes** - Authentication guards on all pages

### 📦 Static/Mock Data (No Backend)
- **Product Listing** - 8 hardcoded products with static images and prices
- **Shopping Cart** - Works with browser localStorage only
- **Checkout** - UI only, shows success message (no payment/order API)
- **Admin Dashboard** - CRUD operations stored in localStorage only

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Django backend running with authentication endpoints

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Update .env with your backend URL
# REACT_APP_API_URL=http://localhost:8000/api

# Start development server
npm start
```

The app will open at `http://localhost:3000`

## 🔌 Required Backend Endpoints

Your Django backend only needs these authentication endpoints:

```
POST   /api/auth/login/              # User login
POST   /api/auth/admin/login/        # Admin login  
POST   /api/auth/register/           # User registration
PUT    /api/auth/profile/            # Update user profile ⭐
POST   /api/auth/change-password/    # Change password ⭐
GET    /api/auth/verify/             # Token verification
POST   /api/auth/logout/             # Logout (optional)
```

### Expected Request/Response

**User Login:**
```javascript
// Request
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "password123"
}

// Response
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Admin Login:**
```javascript
// Request
POST /api/auth/admin/login/
{
  "email": "admin@example.com",
  "password": "admin123"
}

// Response - Same as user login
```

**Register:**
```javascript
// Request
POST /api/auth/register/
{
  "email": "newuser@example.com",
  "password": "password123",
  "password2": "password123",
  "first_name": "Jane",
  "last_name": "Smith"
}

// Response - Same as login (with tokens)
```

**Update Profile:**
```javascript
// Request
PUT /api/auth/profile/
Headers: { Authorization: "Bearer {access_token}" }
{
  "first_name": "Updated",
  "last_name": "Name",
  "phone": "+1234567890",
  "email": "newemail@example.com"
}

// Response
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "email": "newemail@example.com",
    "first_name": "Updated",
    "last_name": "Name",
    "phone": "+1234567890"
  }
}
```

**Change Password:**
```javascript
// Request
POST /api/auth/change-password/
Headers: { Authorization: "Bearer {access_token}" }
{
  "old_password": "password123",
  "new_password": "newpassword456",
  "new_password2": "newpassword456"
}

// Response
{
  "message": "Password changed successfully"
}
```

## 📱 Features Overview

### User Flow
1. **Register/Login** → Calls backend API ✅
2. **Update Profile** → Edit name, email, phone via `/profile` page ✅
3. **Change Password** → Update password securely ✅
4. **Browse Products** → Shows 8 static products 📦
5. **Add to Cart** → Saves to localStorage 📦
6. **View Cart** → Reads from localStorage 📦
7. **Checkout** → Shows success message 📦

### Admin Flow
1. **Admin Login** → Calls backend API ✅
2. **View Products** → Loads from localStorage 📦
3. **Add/Edit/Delete** → Updates localStorage only 📦

## 🎨 Design Features

- **Luxury Editorial Aesthetic** - Playfair Display + DM Sans fonts
- **Sophisticated Colors** - Noir, Gold, and Cream palette
- **Fully Responsive** - Desktop, tablet, and mobile
- **Smooth Animations** - Modern transitions and effects
- **Error Handling** - Toast notifications and validation

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t ecommerce-frontend .
```

### Run Container
```bash
docker run -d -p 80:80 \
  -e REACT_APP_API_URL=http://your-backend:8000/api \
  ecommerce-frontend
```

### Docker Compose
```bash
# Start both frontend and backend
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

```env
# .env file
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
```

### CORS Setup (Django)

Make sure your Django backend allows the frontend origin:

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## 📁 Project Structure

```
src/
├── contexts/
│   ├── AuthContext.js      # ✅ Functional - manages auth state
│   └── CartContext.js      # 📦 Static - localStorage only
├── pages/
│   ├── UserLogin.js        # ✅ Functional - calls backend
│   ├── AdminLogin.js       # ✅ Functional - calls backend
│   ├── Register.js         # ✅ Functional - calls backend
│   ├── UserProfile.js      # ✅ Functional - profile & password ⭐ NEW
│   ├── ProductList.js      # 📦 Static - hardcoded products
│   ├── Cart.js            # 📦 Static - localStorage
│   ├── Checkout.js        # 📦 Static - no backend
│   └── AdminDashboard.js  # 📦 Static - localStorage
├── services/
│   └── api.js             # API layer (only auth endpoints used)
└── App.js                 # Main app with routing
```

## 🧪 Testing Authentication

### Test User Flow
1. Go to `http://localhost:3000/register`
2. Create a new account
3. Should auto-login and redirect to products
4. Logout and login again
5. Should see products page

### Test Admin Flow
1. Go to `http://localhost:3000/admin/login`
2. Login with admin credentials
3. Should redirect to admin dashboard
4. Try adding/editing products (saves to localStorage)

### Test Profile Management
1. Login as a regular user
2. Click "Profile" link in navigation bar
3. Update your information (name, email, phone)
4. Click "Update Profile" → Success message
5. Scroll to "Change Password" section
6. Enter current and new password
7. Click "Change Password" → Auto-logout after 2 seconds
8. Login with new password to verify

### Verify Token Storage
1. Login successfully
2. Open DevTools (F12)
3. Go to Application → Local Storage
4. You should see `token` and `userType` stored

## 🚨 Important Notes

### What Works with Backend
- ✅ User authentication (login/register)
- ✅ Admin authentication
- ✅ Profile updates (name, email, phone)
- ✅ Password changes
- ✅ Token-based session management
- ✅ Protected route access control

### What's Static/Demo Only
- 📦 Product data (8 hardcoded items)
- 📦 Shopping cart (browser localStorage)
- 📦 Orders/Checkout (no API calls)
- 📦 Admin product management (localStorage)

### Why This Setup?
This configuration lets you:
- Test and develop authentication flows
- Demo the full UI/UX without full backend
- Focus on auth integration first
- Add backend endpoints incrementally later

## 🔄 Adding Backend Integration Later

When you want to connect products/cart/orders to backend:

1. Update `src/contexts/CartContext.js` - uncomment API calls
2. Update `src/pages/ProductList.js` - use productAPI
3. Update `src/pages/Checkout.js` - use orderAPI
4. Update `src/pages/AdminDashboard.js` - use productAPI

All the API integration code is already written in `src/services/api.js`, just currently unused for products/cart/orders.

## 📚 Available Commands

```bash
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
make docker-build  # Build Docker image
make docker-run    # Run Docker container
make help          # Show all make commands
```

## 🐛 Troubleshooting

### Login not working
- Verify Django backend is running on correct port
- Check browser console for CORS errors
- Verify `.env` has correct `REACT_APP_API_URL`
- Check Django CORS settings

### Can't see products after login
- Products are static/hardcoded - should always show
- Check browser console for JavaScript errors
- Clear browser cache and reload

### Cart not persisting
- Cart uses localStorage - check browser settings
- Some browsers block localStorage in private/incognito mode
- Check Application tab in DevTools

## 📖 Documentation

- `README.md` - This file (quick start)
- `SETUP_GUIDE.md` - Detailed setup for junior engineers
- `IMPLEMENTATION_GUIDE.md` - Full architecture and roadmap

## 🎯 Next Steps

1. ✅ Setup and test authentication
2. ⬜ Deploy backend to AWS EC2
3. ⬜ Deploy frontend to AWS EC2
4. ⬜ Setup SSL certificate
5. ⬜ Add monitoring (CloudWatch)
6. ⬜ Later: Add full product/cart backend integration

## 📄 License

Proprietary - All rights reserved

---

**Remember:** Only authentication is connected to the backend. Everything else (products, cart, checkout) is static demo data!