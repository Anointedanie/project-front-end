# Quick Start Guide - Authentication Only Version

## ⚡ What You're Getting

A **simplified React e-commerce frontend** where:
- ✅ **Authentication is FULLY FUNCTIONAL** (connects to your Django backend)
- 📦 **Everything else is STATIC/DEMO** (products, cart, checkout use mock data)

This lets you test and demo the authentication flow while showing a complete UI.

## 🚀 Setup in 3 Minutes

### Step 1: Extract and Install

```bash
# Extract the archive
tar -xzf ecommerce-frontend.tar.gz
cd ecommerce-frontend

# Install dependencies (takes ~1-2 minutes)
npm install
```

### Step 2: Configure Backend URL

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use any text editor
```

Update this line:
```env
REACT_APP_API_URL=http://localhost:8000/api
```

Change `localhost:8000` to your Django backend address.

### Step 3: Start the App

```bash
npm start
```

The app will automatically open at `http://localhost:3000`

## 🔐 What's Connected to Backend

Only these API endpoints are called:

```
POST /api/auth/login/           → User login
POST /api/auth/admin/login/     → Admin login
POST /api/auth/register/        → New user registration
PUT  /api/auth/profile/         → Update profile ⭐
POST /api/auth/change-password/ → Change password ⭐
GET  /api/auth/verify/          → Token verification
```

## 📦 What's Static (No Backend Needed)

- **Products**: 8 hardcoded products with images and prices
- **Shopping Cart**: Saves to browser localStorage
- **Checkout**: Shows success message (no API call)
- **Admin Dashboard**: Product CRUD saves to localStorage

## ✅ Test Authentication

### Test User Registration & Login

1. Open `http://localhost:3000/register`
2. Fill in the form:
   - First Name: John
   - Last Name: Doe
   - Email: john@example.com
   - Password: password123
3. Click "Create Account"
4. **Should call your backend** `/api/auth/register/`
5. On success: Redirects to products page
6. Logout and try logging in again

### Test Admin Login

1. Open `http://localhost:3000/admin/login`
2. Enter admin credentials
3. **Should call your backend** `/api/auth/admin/login/`
4. On success: Redirects to admin dashboard
5. Try adding a product (saves to localStorage only)

### Test Profile Management ⭐ NEW

1. Login as a regular user
2. Click **"Profile"** link in the navigation bar
3. **Update Profile Section:**
   - Change your name, email, or phone
   - Click "Update Profile"
   - **Should call your backend** `PUT /api/auth/profile/`
   - Success message appears
4. **Change Password Section:**
   - Enter current password
   - Enter new password (min 8 characters)
   - Confirm new password
   - Click "Change Password"
   - **Should call your backend** `POST /api/auth/change-password/`
   - Success message → Auto-logout after 2 seconds
   - Login again with new password to verify

## 🔍 Verify It's Working

### Check Backend Connection

Open browser DevTools (F12):
1. Go to **Network** tab
2. Login or register
3. You should see a request to `/api/auth/login/` or `/api/auth/register/`
4. Status should be 200 or 201

### Check Token Storage

After successful login:
1. Open DevTools (F12)
2. Go to **Application** tab
3. Click **Local Storage** → `http://localhost:3000`
4. You should see:
   - `token`: "eyJ0eXAiOiJKV1..."
   - `userType`: "user" or "admin"

## 🎨 The Full UI Experience

Even though products/cart/checkout don't call the backend, you still get:
- ✨ Beautiful luxury editorial design
- 📱 Fully responsive (mobile, tablet, desktop)
- 🛒 Working shopping cart (localStorage)
- 💳 Checkout form (UI only)
- 👨‍💼 Admin product management (localStorage)

This gives you a complete demo experience!

## ⚙️ Required Django Endpoints

Your backend needs to return this format:

### Login Response
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Register Response
```json
{
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "user": {
    "id": 2,
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Smith"
  }
}
```

### Profile Update Response ⭐
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "email": "updated@example.com",
    "first_name": "Updated",
    "last_name": "Name",
    "phone": "+1234567890"
  }
}
```

### Change Password Response ⭐
```json
{
  "message": "Password changed successfully"
}
```

## 🐛 Common Issues

### Issue: "Failed to fetch" error

**Solution:**
1. Check Django is running: `curl http://localhost:8000/api/`
2. Check CORS settings in Django:
   ```python
   CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
   ```
3. Verify `.env` has correct URL

### Issue: Login succeeds but shows "Invalid credentials"

**Solution:**
- Check Django response format matches above
- Look in browser console for error messages
- Verify token is in response

### Issue: Can't see products after login

**Solution:**
- Products are static/hardcoded and should always show
- Check browser console for JavaScript errors
- Try hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

## 📂 Project Structure

```
ecommerce-frontend/
├── src/
│   ├── pages/
│   │   ├── UserLogin.js       ✅ Backend connected
│   │   ├── AdminLogin.js      ✅ Backend connected
│   │   ├── Register.js        ✅ Backend connected
│   │   ├── UserProfile.js     ✅ Backend connected ⭐ NEW
│   │   ├── ProductList.js     📦 Static products
│   │   ├── Cart.js           📦 localStorage
│   │   ├── Checkout.js       📦 UI only
│   │   └── AdminDashboard.js 📦 localStorage
│   ├── contexts/
│   │   ├── AuthContext.js     ✅ Backend connected
│   │   └── CartContext.js     📦 localStorage
│   └── services/
│       └── api.js            API integration layer
├── package.json
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🐳 Docker Deployment

If you want to run in Docker:

```bash
# Build
docker build -t ecommerce-frontend .

# Run
docker run -d -p 80:80 \
  -e REACT_APP_API_URL=http://your-backend:8000/api \
  ecommerce-frontend

# Visit http://localhost
```

## 📚 Next Steps

1. ✅ Test authentication with your Django backend
2. ✅ Verify tokens are stored correctly
3. ✅ Demo the full UI to stakeholders
4. ⬜ When ready, add product/cart/order backend endpoints
5. ⬜ Deploy to AWS EC2 with SSL
6. ⬜ Setup monitoring

## 🆘 Need Help?

- Check `README.md` for detailed documentation
- Check `SETUP_GUIDE.md` for junior engineer guidance
- Check browser console (F12) for errors
- Check Django backend logs for API errors

## 💡 Pro Tips

1. **Test Login First**: Before anything else, make sure login works
2. **Check Token**: Verify token appears in localStorage after login
3. **Check CORS**: Most issues are CORS-related in Django
4. **Use DevTools**: Network tab shows all API requests
5. **Demo Ready**: The static products/cart look fully functional!

---

## 🎯 Remember

**Only authentication calls your backend** - everything else is local demo data. This is intentional and lets you test auth without needing a full backend implementation!

**Happy coding!** 🚀