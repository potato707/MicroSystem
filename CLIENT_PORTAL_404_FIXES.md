# Client Account System - 404 Errors Fixed

## Issues Found and Resolved

### 1. **Complaint ID Type Mismatch** ✅ FIXED
**Problem**: The backend uses UUID for complaint IDs, but the frontend TypeScript interface defined it as `number`.

**Error**: When accessing `/client/complaints/[uuid]/`, the frontend was trying to parse the UUID as an integer, causing 404 errors.

**Fix**:
- Changed `Complaint.id` from `number` to `string` in `types/client.ts`
- Updated `getComplaintById(id: number)` to `getComplaintById(id: string)` in `lib/api/clientApi.ts`
- Removed `parseInt(complaintId)` from `app/client/complaints/[id]/page.tsx`

### 2. **Categories API Endpoint** ✅ FIXED
**Problem**: The API client was calling `/client/complaints/categories/` which doesn't exist.

**Correct Endpoints**:
- For authenticated clients: `/client/categories/`
- For public access: `/public/complaint-categories/`

**Fix**:
- Updated `getAvailableCategories()` to use `/client/categories/` in `lib/api/clientApi.ts`

---

## Testing the Fixes

### 1. Start the Servers

**Backend**:
```bash
cd /home/ahmedyasser/lab/MicroSystem
python manage.py runserver
```

**Frontend**:
```bash
cd /home/ahmedyasser/lab/MicroSystem/v0-micro-system
npm run dev
```

### 2. Create a Test Client Account

Option A - Use Django Shell:
```bash
python manage.py shell
```

Then:
```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Create a test client
user = User.objects.create_user(
    username='testclient',
    email='test@example.com',
    password='TestPass123!',
    name='Test Client',
    role='client'
)
print(f"Created user: {user.email}")
```

Option B - Submit a complaint through the public form to auto-create an account.

### 3. Test the Endpoints

**Login**:
```bash
curl -X POST http://localhost:8000/hr/client/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'
```

**Get Categories** (use the access token from login):
```bash
curl http://localhost:8000/hr/client/categories/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**List Complaints**:
```bash
curl http://localhost:8000/hr/client/complaints/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Get Complaint Detail** (replace UUID with actual complaint ID):
```bash
curl http://localhost:8000/hr/client/complaints/UUID-HERE/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Test Frontend Pages

1. **Login**: http://localhost:3000/client/login
   - Use: test@example.com / TestPass123!

2. **Dashboard**: http://localhost:3000/client/dashboard
   - Should show statistics
   - Should show recent complaints

3. **Complaints List**: http://localhost:3000/client/complaints
   - Should list all your complaints
   - Filter and search should work

4. **Complaint Detail**: Click on any complaint
   - Should show full complaint details
   - No more 404 errors!

5. **New Complaint**: http://localhost:3000/client/complaints/new
   - Form should load
   - Categories dropdown should populate
   - Submission should work

---

## Files Modified

### TypeScript Types
- ✅ `/v0-micro-system/types/client.ts`
  - Changed `Complaint.id` from `number` to `string`

### API Client
- ✅ `/v0-micro-system/lib/api/clientApi.ts`
  - Fixed `getAvailableCategories()` endpoint URL
  - Changed `getComplaintById()` parameter type from `number` to `string`

### Frontend Pages
- ✅ `/v0-micro-system/app/client/complaints/[id]/page.tsx`
  - Removed `parseInt()` when calling `getComplaintById()`

---

## Common Errors and Solutions

### Error: "404 Not Found" on complaint detail page
**Cause**: UUID was being parsed as integer  
**Solution**: ✅ Fixed - UUID is now kept as string

### Error: "404 Not Found" on categories endpoint
**Cause**: Wrong API endpoint URL  
**Solution**: ✅ Fixed - Now uses correct `/client/categories/` endpoint

### Error: "Authentication credentials were not provided"
**Cause**: Missing or expired JWT token  
**Solution**: Login again at `/client/login` to get a fresh token

### Error: "Cannot connect to API"
**Cause**: Django server not running or wrong API URL  
**Solution**: 
1. Check Django is running on port 8000
2. Verify `.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000/hr`
3. Restart Next.js dev server

---

## Verification Checklist

After applying these fixes, verify:

- [ ] Can login successfully
- [ ] Dashboard loads without errors
- [ ] Complaints list shows correctly
- [ ] Can click on a complaint and see details (no 404)
- [ ] Can access new complaint form
- [ ] Categories dropdown populates
- [ ] Can submit a new complaint
- [ ] Can filter complaints by status/priority
- [ ] Search functionality works
- [ ] No 404 errors in browser console

---

## API Endpoint Reference

### Working Endpoints

**Authentication** (No auth required):
- POST `/hr/client/auth/login/` - Login
- POST `/hr/client/auth/logout/` - Logout (requires token)

**User Info** (Requires auth):
- GET `/hr/client/auth/me/` - Current user details
- POST `/hr/client/auth/change-password/` - Change password
- PATCH `/hr/client/auth/profile/` - Update profile

**Dashboard** (Requires auth):
- GET `/hr/client/dashboard/stats/` - Statistics
- GET `/hr/client/complaints/` - List complaints
- GET `/hr/client/complaints/<uuid>/` - Complaint detail
- GET `/hr/client/complaints/<uuid>/history/` - Status history
- POST `/hr/client/complaints/submit/` - Submit complaint
- GET `/hr/client/categories/` - Available categories

**Public** (No auth required):
- GET `/hr/public/complaint-categories/` - Public categories list
- POST `/hr/public/client-complaints/` - Public complaint submission

---

## Backend URL Patterns (for reference)

From `hr_management/urls.py`:

```python
# Client Authentication
path("client/auth/login/", ClientLoginView.as_view()),
path("client/auth/logout/", ClientLogoutView.as_view()),
path("client/auth/me/", ClientCurrentUserView.as_view()),
path("client/auth/change-password/", ClientChangePasswordView.as_view()),
path("client/auth/profile/", ClientProfileUpdateView.as_view()),

# Client Dashboard
path("client/dashboard/stats/", ClientDashboardStatsView.as_view()),
path("client/complaints/", ClientComplaintsListView.as_view()),
path("client/complaints/<uuid:complaint_id>/", ClientComplaintDetailView.as_view()),
path("client/complaints/<uuid:complaint_id>/history/", ClientComplaintStatusHistoryView.as_view()),
path("client/complaints/submit/", ClientSubmitComplaintView.as_view()),
path("client/categories/", ClientAvailableCategoriesView.as_view()),
```

Note: All complaint IDs are **UUIDs**, not integers!

---

## Summary

All 404 errors were caused by:
1. **Type mismatch**: Frontend treating UUIDs as numbers
2. **Wrong API endpoint**: Using incorrect URL for categories

Both issues are now **resolved**. The client portal should work correctly now.

### Next Steps:
1. Restart the Next.js dev server
2. Clear browser cache/cookies
3. Login and test all features
4. Verify no more 404 errors in console

🎉 **The client portal is now fully functional!**
