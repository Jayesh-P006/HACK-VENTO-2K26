# Mock Data Seeding (50 Students + 10 Companies)

This repo includes a schema-aligned seed script that creates **exactly** the number of mock students/companies you request and also marks **OTP + verification as approved** for all seeded students.

## Script
- `backend/seed_mock_portal_data.py`

It creates:
- Students (`role_id=1`) + `students` profile rows
- Companies (`role_id=2`) + `companies` profile rows
- `student_verification` rows with:
  - `status='Verified'`
  - `otp_verified=True`
  - timestamps set to `now`

## How to Run (Railway CLI)
From the repo root:

```bash
railway run python backend/seed_mock_portal_data.py --students 50 --companies 10 --tag mock
```

If you want to re-run safely (delete the previously seeded mock users for the same tag first):

```bash
railway run python backend/seed_mock_portal_data.py --clear --students 50 --companies 10 --tag mock
```

## Login Examples
The script prints working credentials after it finishes, but by default:

- Student: `student.<tag>.1@university.edu` / `student123`
- Company: `company.<tag>.1@company.com` / `company123`

You can override passwords:

```bash
railway run python backend/seed_mock_portal_data.py --tag mock --student-password MyStudentPass --company-password MyCompanyPass
```

## Notes
- The script is idempotent per email: if a user already exists, it will skip that index and continue until the requested count is reached.
- `--tag` is important to avoid colliding with real accounts.
