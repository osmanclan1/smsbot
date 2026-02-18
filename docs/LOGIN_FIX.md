# Login Error Fix & Student Auth Info

## 🔧 Admin Login Error Fix

### Problem
Error: `Unexpected token '<', "<!DOCTYPE "... is not valid JSON`

This happens when the frontend tries to parse HTML as JSON. This can occur if:
1. The API returns an HTML error page instead of JSON
2. CORS preflight fails and returns HTML
3. The endpoint doesn't exist and returns 404 HTML

### Solution Applied
Updated `admin/src/LoginPage.jsx` to:
1. Check `Content-Type` header before parsing JSON
2. Handle non-JSON responses gracefully
3. Show better error messages

### Testing
The API endpoint is working correctly:
```bash
curl -X POST https://wsb8nu652d.execute-api.us-east-1.amazonaws.com/Prod/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrong"}'
# Returns: {"detail":"Invalid credentials"} ✅
```

### Admin Credentials
Admin credentials are set via environment variables in Lambda:
- `ADMIN_USERNAME` (default: "admin")
- `ADMIN_PASSWORD` (default: "admin")

**⚠️ Update these in Lambda console with secure credentials!**

---

## 🎓 Student Authentication

### Student Auth Endpoints

Student authentication is available at `/api/student/auth/*`:

1. **Login**: `POST /api/student/auth/login`
   ```json
   {
     "username": "student_username",
     "password": "student_password"
   }
   ```

2. **Register**: `POST /api/student/auth/register`
   ```json
   {
     "username": "student_username",
     "password": "student_password",
     "email": "student@example.com",
     "name": "Student Name"
   }
   ```

3. **Logout**: `POST /api/student/auth/logout`

4. **Get Current Student**: `GET /api/student/auth/me`

### Student Frontend

There's a student frontend in `student/src/`:
- `student/src/AuthPage.jsx` - Login/Register page
- `student/src/App.jsx` - Main student dashboard
- `student/src/login.html` - Login page HTML

### Student Data Storage

Student accounts are stored in DynamoDB table: `smsbot-students`

### How to Deploy Student Frontend

Similar to admin frontend, you can deploy the student frontend:

1. **Build student frontend**:
   ```bash
   npm run build:student
   ```

2. **Deploy to Amplify** (create separate app or use subdomain):
   - Option 1: Create new Amplify app for students
   - Option 2: Deploy to same app with different base path

3. **Student frontend URLs**:
   - Login: `/student/login.html`
   - Dashboard: `/student/`

### Student vs Admin Auth

| Feature | Admin | Student |
|---------|-------|---------|
| Endpoint | `/api/auth/*` | `/api/student/auth/*` |
| Storage | Environment vars | DynamoDB table |
| Session | `authenticated` | `student_authenticated` |
| Frontend | `admin/src/` | `student/src/` |

---

## 🚀 Next Steps

1. **Rebuild and redeploy admin frontend** with the login fix
2. **Test admin login** with correct credentials
3. **Update Lambda environment variables**:
   - Set `ADMIN_USERNAME` and `ADMIN_PASSWORD`
4. **Deploy student frontend** (if needed)
5. **Create student accounts** via registration endpoint



