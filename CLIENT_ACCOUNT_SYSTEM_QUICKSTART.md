# Client Account System - Quick Start Guide

## Test the Complete System (5 Minutes)

### Step 1: Verify Backend is Running
```bash
# In the MicroSystem directory
python manage.py runserver
```

Expected output: `Starting development server at http://127.0.0.1:8000/`

### Step 2: Start Frontend
```bash
# In a new terminal
cd v0-micro-system
npm run dev
```

Expected output: `- Local: http://localhost:3000`

### Step 3: Test Backend API (Optional)
Run the automated test suite:
```bash
python test_client_account_system.py
```

This will:
- Create a test client account
- Submit a complaint
- Verify account creation
- Test authentication
- Display test credentials

### Step 4: Test Frontend

#### Option A: Use Existing Test Account
If you ran the backend tests, use the credentials shown in the output:
- Email: `testclient@example.com`
- Password: (shown in test output, e.g., `fP5Lwv##om&K`)

#### Option B: Create New Account via Public Form
1. Go to: `http://localhost:3000/client-portal`
2. Submit a complaint with your email
3. Check Django console for the generated password
4. Use those credentials to login

### Step 5: Login to Client Portal
1. Go to: `http://localhost:3000/client/login`
2. Enter email and password
3. Click "Sign in"
4. You should be redirected to the dashboard

### Step 6: Explore Dashboard
On the dashboard, you should see:
- Statistics cards (total, pending, in-progress, resolved)
- Recent complaints list
- Buttons to submit new complaint or view all complaints

### Step 7: Submit a New Complaint
1. Click "Submit New Complaint"
2. Fill in the form (contact info should be pre-filled)
3. Select a category and priority
4. Click "Submit Complaint"
5. You should see a success message

### Step 8: View Complaints
1. Click "View All Complaints" from dashboard
2. Try filtering by status or priority
3. Use the search box to search complaints
4. Click on any complaint to view details

### Step 9: View Complaint Details
1. Click on a complaint from the list
2. View full details including:
   - Title and description
   - Status and priority
   - Contact information
   - Assignment (if assigned)
   - Resolution (if resolved)

---

## Quick URLs Reference

### Frontend
- Login: `http://localhost:3000/client/login`
- Dashboard: `http://localhost:3000/client/dashboard`
- All Complaints: `http://localhost:3000/client/complaints`
- New Complaint: `http://localhost:3000/client/complaints/new`
- Public Complaint Form: `http://localhost:3000/client-portal`

### Backend API (if testing directly)
- Login: `POST http://localhost:8000/hr/client/auth/login/`
- Dashboard Stats: `GET http://localhost:8000/hr/client/dashboard/stats/`
- Complaints List: `GET http://localhost:8000/hr/client/complaints/`

---

## Testing Checklist

- [ ] Backend server is running
- [ ] Frontend dev server is running
- [ ] Can create new client account (via complaint submission)
- [ ] Receive welcome email with password (check console)
- [ ] Can login with generated credentials
- [ ] Dashboard displays correctly
- [ ] Statistics show correct numbers
- [ ] Can submit new complaint
- [ ] Can view complaints list
- [ ] Can filter complaints by status/priority
- [ ] Can search complaints
- [ ] Can view complaint details
- [ ] Can logout successfully
- [ ] Cannot access protected pages without login

---

## Common Issues & Solutions

### Issue: "Cannot connect to API"
**Solution**: Make sure Django server is running on port 8000

### Issue: "Module not found" errors in frontend
**Solution**: 
```bash
cd v0-micro-system
npm install
```

### Issue: "Migration errors"
**Solution**:
```bash
python manage.py migrate
```

### Issue: "Invalid credentials" when logging in
**Solution**: 
- Check the console output for the correct password
- Or submit a new complaint to create a fresh account

### Issue: Frontend shows blank page
**Solution**:
- Check browser console for errors
- Verify `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000/hr`
- Restart Next.js dev server

---

## Test Data

### Create Sample Categories (if needed)
```bash
python manage.py shell
```

Then in the shell:
```python
from hr_management.models import ComplaintCategory
ComplaintCategory.objects.get_or_create(name='Technical Support')
ComplaintCategory.objects.get_or_create(name='Billing')
ComplaintCategory.objects.get_or_create(name='Service Quality')
ComplaintCategory.objects.get_or_create(name='General Inquiry')
exit()
```

---

## Next Steps

After verifying everything works:

1. **Configure Email for Production**
   - Update `settings.py` with real SMTP settings
   - Test email delivery

2. **Customize UI**
   - Update colors/branding in Tailwind config
   - Add company logo
   - Customize text/messages

3. **Add More Features**
   - File uploads for complaints
   - Comment system
   - Email notifications for status changes
   - Password reset functionality

4. **Deploy to Production**
   - Set up production database (PostgreSQL)
   - Configure proper email backend
   - Set DEBUG=False
   - Configure ALLOWED_HOSTS
   - Set up HTTPS
   - Deploy frontend to Vercel/Netlify
   - Deploy backend to your server

---

## Success! 🎉

You now have a fully functional client account system where:
- Clients automatically get accounts when submitting complaints
- Clients can log in securely
- Clients can view their dashboard with statistics
- Clients can manage their complaints
- Everything is protected by JWT authentication

For detailed documentation, see:
- `CLIENT_ACCOUNT_SYSTEM_COMPLETE.md` - Full implementation guide
- `CLIENT_ACCOUNT_SYSTEM_IMPLEMENTATION.md` - Backend details
- `CLIENT_ACCOUNT_SYSTEM_TESTING.md` - Testing guide
