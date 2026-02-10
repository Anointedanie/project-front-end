# E-Commerce Frontend Setup Guide for Junior Engineers

Welcome! This guide will walk you through setting up and understanding the e-commerce frontend application step by step.

## 📚 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Local Development Setup](#local-development-setup)
4. [Testing Your Setup](#testing-your-setup)
5. [Common Issues & Solutions](#common-issues--solutions)
6. [Understanding the Codebase](#understanding-the-codebase)
7. [Making Your First Changes](#making-your-first-changes)
8. [Deployment Workflow](#deployment-workflow)

## Prerequisites

### Required Software

Before starting, install these tools:

1. **Node.js and npm** (v18 or higher)
   ```bash
   # Check if installed
   node --version  # Should show v18.x.x or higher
   npm --version   # Should show v9.x.x or higher
   
   # If not installed, download from: https://nodejs.org/
   ```

2. **Git**
   ```bash
   # Check if installed
   git --version
   
   # If not installed, download from: https://git-scm.com/
   ```

3. **Docker** (for containerized deployment)
   ```bash
   # Check if installed
   docker --version
   docker-compose --version
   
   # If not installed, download from: https://www.docker.com/
   ```

4. **Code Editor** - Recommended: Visual Studio Code
   - Download from: https://code.visualstudio.com/

### Recommended VS Code Extensions

- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter
- ESLint
- Auto Rename Tag
- Path Intellisense

## Understanding the Architecture

### High-Level Overview

```
┌─────────────┐      HTTP/HTTPS       ┌──────────────┐
│   Browser   │ ◄──────────────────► │   Frontend   │
│  (User UI)  │                       │   (React)    │
└─────────────┘                       └──────┬───────┘
                                             │
                                             │ REST API
                                             │ (Axios)
                                             ▼
                                      ┌──────────────┐
                                      │   Backend    │
                                      │   (Django)   │
                                      └──────┬───────┘
                                             │
                                             │ SQL
                                             ▼
                                      ┌──────────────┐
                                      │  Database    │
                                      │  (RDS PG)    │
                                      └──────────────┘
```

### Frontend Stack

- **React**: UI library for building components
- **React Router**: Client-side routing
- **Axios**: HTTP client for API calls
- **Context API**: State management
- **Custom CSS**: Styling (no frameworks like Bootstrap)

### Key Concepts

1. **Component-Based Architecture**: UI is broken into reusable components
2. **State Management**: Using React Context for global state (auth, cart)
3. **Client-Side Routing**: Navigation without page reloads
4. **API Integration**: RESTful communication with Django backend

## Local Development Setup

### Step 1: Clone the Repository

```bash
# Navigate to your projects directory
cd ~/projects

# Clone the repo (replace with actual repo URL)
git clone <repository-url>
cd ecommerce-frontend
```

### Step 2: Install Dependencies

```bash
# Install all npm packages
npm install

# This will create node_modules/ directory with all dependencies
```

### Step 3: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Open .env in your editor
code .env
```

Update the `.env` file:

```env
# Your Django backend URL (local development)
REACT_APP_API_URL=http://localhost:8000/api

# Environment
REACT_APP_ENV=development
```

### Step 4: Start Development Server

```bash
# Start the React development server
npm start
```

The app should automatically open at `http://localhost:3000`

**What happens when you run `npm start`?**
1. Webpack compiles your React code
2. Development server starts on port 3000
3. Hot reload is enabled (changes reflect immediately)
4. Browser automatically opens

### Step 5: Verify Backend Connection

Make sure your Django backend is running on port 8000:

```bash
# In a separate terminal, navigate to backend
cd ../ecommerce-backend

# Start Django server
python manage.py runserver
```

## Testing Your Setup

### Test 1: Homepage Loads

✅ Navigate to `http://localhost:3000`
✅ You should see the product listing or login page
✅ Check browser console (F12) for no errors

### Test 2: Login Flow

1. Go to login page
2. Enter credentials (if you have test accounts)
3. Should redirect to products page on success

### Test 3: API Connection

Open browser console (F12) and go to Network tab:
1. Perform any action (login, view products)
2. You should see API requests to `http://localhost:8000/api`
3. Status codes should be 200 or 201 for success

### Test 4: React DevTools

Install React DevTools browser extension:
- Chrome: Search "React Developer Tools" in Chrome Web Store
- Firefox: Search in Firefox Add-ons

Open DevTools → React tab to inspect component tree

## Common Issues & Solutions

### Issue 1: `npm install` fails

**Symptoms**: Errors during npm install

**Solutions**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Issue 2: Port 3000 already in use

**Symptoms**: "Port 3000 is already in use"

**Solutions**:
```bash
# Find process using port 3000
lsof -i :3000  # Mac/Linux
netstat -ano | findstr :3000  # Windows

# Kill the process
kill -9 <PID>  # Mac/Linux

# Or use a different port
PORT=3001 npm start
```

### Issue 3: Cannot connect to backend

**Symptoms**: API errors, CORS errors

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/api/products/`
2. Check `.env` has correct API URL
3. Verify Django CORS settings allow `http://localhost:3000`

### Issue 4: White screen after starting

**Symptoms**: Blank page, console shows errors

**Solutions**:
1. Check browser console for errors
2. Verify all imports in code are correct
3. Check for syntax errors in recent changes
4. Try clearing browser cache (Ctrl+Shift+R or Cmd+Shift+R)

## Understanding the Codebase

### Directory Structure Explained

```
src/
├── contexts/          # Global state management
│   ├── AuthContext.js    # User authentication state
│   └── CartContext.js    # Shopping cart state
│
├── pages/            # Page components (routes)
│   ├── UserLogin.js      # User login page
│   ├── AdminLogin.js     # Admin login page
│   ├── Register.js       # Registration page
│   ├── ProductList.js    # Products listing
│   ├── Cart.js           # Shopping cart
│   ├── Checkout.js       # Checkout process
│   └── AdminDashboard.js # Admin panel
│
├── services/         # API communication layer
│   └── api.js           # Axios setup & API functions
│
├── App.js            # Main app component with routing
├── App.css           # Global styles
└── index.js          # App entry point
```

### Key Files Explained

#### `src/index.js` - Entry Point
```javascript
// This is where React starts
// It renders App component into HTML div with id="root"
ReactDOM.render(<App />, document.getElementById('root'));
```

#### `src/App.js` - Main Component
```javascript
// Defines all routes and wraps app in Context providers
// Routes: /login, /products, /cart, /checkout, /admin
```

#### `src/contexts/AuthContext.js` - Authentication
```javascript
// Manages user login/logout state
// Provides: user, isAuthenticated, login(), logout()
```

#### `src/contexts/CartContext.js` - Shopping Cart
```javascript
// Manages shopping cart state
// Provides: cart, addToCart(), removeFromCart(), etc.
```

#### `src/services/api.js` - API Layer
```javascript
// All backend communication goes through here
// Uses Axios for HTTP requests
// Includes token authentication
```

### How Data Flows

1. **User logs in**
   ```
   LoginPage → AuthContext.login() → API.loginUser() → Backend
   ← Token returned → Stored in localStorage → State updated
   ```

2. **User adds product to cart**
   ```
   ProductCard → CartContext.addToCart() → API.addToCart() → Backend
   ← Cart updated → State refreshed → UI re-renders
   ```

3. **Protected routes**
   ```
   User navigates to /products → ProtectedRoute checks AuthContext
   → If authenticated: Show page
   → If not: Redirect to /login
   ```

## Making Your First Changes

### Task 1: Change a Color

Let's change the gold accent color to blue:

1. Open `src/App.css`
2. Find the color variables:
   ```css
   :root {
     --color-gold: #c9a961;  /* Change this */
   }
   ```
3. Change to blue:
   ```css
   :root {
     --color-gold: #3b82f6;  /* New blue color */
   }
   ```
4. Save and watch the app update automatically!

### Task 2: Add a New Product Card Feature

Let's add a "Quick View" button to product cards:

1. Open `src/pages/ProductList.js`
2. Find the product card JSX
3. Add a button:
   ```javascript
   <button 
     onClick={() => alert(`Quick view: ${product.name}`)}
     className="btn btn-secondary btn-sm"
   >
     Quick View
   </button>
   ```
4. Save and test the button!

### Task 3: Customize the Welcome Message

1. Open `src/pages/ProductList.js`
2. Find the header:
   ```javascript
   <h1>Curated Collection</h1>
   ```
3. Change to:
   ```javascript
   <h1>Welcome to Our Store!</h1>
   ```

### Best Practices for Changes

✅ **DO:**
- Test your changes locally before committing
- Write descriptive commit messages
- Follow existing code style
- Ask questions if unsure

❌ **DON'T:**
- Push directly to main branch
- Make changes without testing
- Mix multiple unrelated changes in one commit
- Delete code you don't understand (ask first!)

## Deployment Workflow

### Development → Staging → Production

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Development │───▶│   Staging   │───▶│ Production  │
│  (Local)    │    │  (AWS EC2)  │    │   (EKS)     │
└─────────────┘    └─────────────┘    └─────────────┘
     npm start         Docker            K8s/EKS
```

### Step 1: Local Testing

```bash
# Run locally
npm start

# Run tests
npm test

# Build production bundle
npm run build
```

### Step 2: Docker Testing

```bash
# Build Docker image
make docker-build

# Run locally in Docker
make docker-run

# Test at http://localhost
```

### Step 3: Push to Git

```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add quick view button to product cards"

# Push to remote
git push origin feature/my-new-feature

# Create Pull Request on GitHub/GitLab
```

### Step 4: Deploy to Staging

```bash
# After PR is merged to main
git checkout main
git pull

# Build and deploy
make deploy-local
```

### Step 5: Deploy to Production

This will be done later with:
- CloudFormation templates
- Terraform/Pulumi
- EKS deployment

## Learning Resources

### React Fundamentals
- [Official React Tutorial](https://react.dev/learn)
- [React Context API](https://react.dev/reference/react/useContext)
- [React Hooks](https://react.dev/reference/react)

### JavaScript/ES6
- [ES6 Features](https://github.com/lukehoban/es6features)
- [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)

### CSS
- [CSS Grid](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)

### Tools
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- [Docker Tutorial](https://docs.docker.com/get-started/)

## Getting Help

### When Stuck:

1. **Check the Error Message**: Read it carefully, it usually tells you what's wrong
2. **Check Browser Console**: F12 → Console tab for JavaScript errors
3. **Check Network Tab**: F12 → Network tab for API errors
4. **Search the Error**: Google the exact error message
5. **Check Documentation**: React, Axios, React Router docs
6. **Ask the Team**: Don't struggle alone! Ask senior developers

### Useful Commands

```bash
# See available make commands
make help

# Clean and restart
make clean
npm install
npm start

# View logs
make logs-frontend

# Check health
make health
```

## Next Steps

After you're comfortable with local development:

1. ✅ Master React basics
2. ✅ Understand Context API
3. ✅ Learn Axios and API integration
4. ✅ Practice making small features
5. ⬜ Learn Docker basics
6. ⬜ Understand Kubernetes
7. ⬜ Learn AWS services (EC2, RDS, EKS)

## Quick Reference

### Common npm Commands
```bash
npm start              # Start dev server
npm test               # Run tests
npm run build          # Production build
npm install <package>  # Install package
```

### Common git Commands
```bash
git status            # Check status
git add .             # Stage all changes
git commit -m "msg"   # Commit changes
git push              # Push to remote
git pull              # Pull from remote
```

### Common Docker Commands
```bash
docker ps             # List running containers
docker logs <id>      # View container logs
docker stop <id>      # Stop container
docker rm <id>        # Remove container
```

---

**Remember**: Every senior developer was once a junior. Don't be afraid to ask questions and make mistakes - that's how you learn! 🚀

Good luck with your development journey!
