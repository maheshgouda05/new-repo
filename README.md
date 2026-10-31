# Analytix Club Website

> Complete, responsive college technical club website with role-based access control, FastAPI REST backend, and Supabase database architecture.

---

## 📁 Project Architecture & Folder Structure

```
analytix-club/
│
├── frontend/
│   ├── index.html               # Public Landing page (Hero, Teams, Events, Notices)
│   ├── login.html               # Role-based Login with 1-click Demo credentials
│   ├── register.html            # Member registration (defaults to 'member' role)
│   ├── admin-dashboard.html     # Dedicated Admin Dashboard with sidebar navigation
│   ├── member-dashboard.html    # Dedicated Member Dashboard with sidebar navigation
│   ├── events.html              # Club events listing & one-click registration
│   ├── hackathons.html          # Hackathons & coding competitions directory
│   ├── announcements.html       # Official circulars, updates, & notices
│   ├── profile.html             # Profile viewer & editor with permission checks
│   │
│   ├── css/
│   │   ├── style.css            # Global design system, colors, navbar, footer, cards
│   │   ├── auth.css             # Authentication cards & form styling
│   │   ├── admin.css            # Admin table controls, actions, points awarding
│   │   └── dashboard.css        # Responsive sidebar, stats grids, data tables
│   │
│   ├── js/
│   │   ├── api.js               # Centralized REST client, JWT Bearer handler & toasts
│   │   ├── auth.js              # Role verification & redirection guard
│   │   ├── admin.js             # Admin dashboard controller (CRUD, points, teams)
│   │   ├── member.js            # Member dashboard controller (overview, stats)
│   │   ├── events.js            # Events, hackathons, & announcements renderer
│   │   └── profile.js           # Member & admin profile editor
│   │
│   └── assets/
│       ├── images/              # Club branding & photography
│       ├── posters/             # Event banners & posters
│       └── uploads/             # Local upload storage fallback
│
├── backend/
│   ├── main.py                  # FastAPI application entrypoint & static mounts
│   ├── config.py                # Pydantic environment configuration loader
│   ├── database.py              # Supabase PostgreSQL client + Dev fallback repository
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Template for Supabase credentials
│   │
│   ├── routers/
│   │   ├── auth.py              # Login, register, session verification (/api/auth)
│   │   ├── admin.py             # Admin overview, role assignment, points (/api/admin)
│   │   ├── members.py           # Member profile, overview, leaderboard (/api/members)
│   │   ├── events.py            # Event CRUD, registration lists, uploads (/api/events)
│   │   ├── hackathons.py        # Hackathon management & listing (/api/hackathons)
│   │   ├── announcements.py     # Announcements CRUD & uploads (/api/announcements)
│   │   └── registrations.py     # Event & hackathon applications (/api/registrations)
│   │
│   ├── models/
│   │   ├── user.py              # Pydantic models for user profiles & auth
│   │   ├── event.py             # Pydantic models for events, hackathons, notices
│   │   └── registration.py      # Pydantic models for registrations & leaderboard
│   │
│   └── services/
│       ├── auth_service.py      # JWT encoding, Bearer validation, require_admin guard
│       └── storage_service.py   # Supabase Storage uploader with local fallback
│
├── database/
│   └── schema.sql               # PostgreSQL tables, RLS policies, triggers, buckets
│
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- Modern web browser (Chrome, Edge, Firefox, Safari)
- VS Code (optional but recommended)

---

### 2. Setting Up Python Environment

Open a terminal inside the project directory:

```bash
cd "analytix-club"

# 1. Create a Python virtual environment
python3 -m venv venv

# 2. Activate the virtual environment
# On macOS / Linux:
source venv/bin/activate
# On Windows (Command Prompt / PowerShell):
# venv\Scripts\activate

# 3. Install required dependencies
pip install -r backend/requirements.txt
```

---

### 3. Starting the Backend Server

Start the FastAPI application with auto-reload:

```bash
uvicorn backend.main:app --reload --port 8000
```

The server will start at:
- **Website & Frontend**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc API Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

> 💡 **Notice**: The FastAPI server directly serves all frontend HTML, CSS, JavaScript, and asset files. Navigating to `http://localhost:8000` opens the landing page immediately!

---

### 4. Running the Frontend in VS Code

You have two easy options:

1. **Integrated Server (Recommended)**:
   Keep the FastAPI server running (`uvicorn backend.main:app --reload`) and open `http://localhost:8000` in your browser. All API calls and pages connect seamlessly without CORS issues.

2. **VS Code Live Server Extension**:
   Right-click `frontend/index.html` in VS Code and select **Open with Live Server** (runs on port 5500). `frontend/js/api.js` automatically routes all requests to `http://localhost:8000`.

---

## 👥 Demo Accounts (Out-of-the-Box Testing)

The system includes pre-seeded accounts so you can test both roles right away before configuring Supabase:

| Role | Email | Password | Default Dashboard |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@analytixclub.edu` | `Admin@123` | `admin-dashboard.html` |
| **Member** | `member@analytixclub.edu` | `Member@123` | `member-dashboard.html` |

On the `login.html` page, click the **1-Click Demo Buttons** to automatically fill credentials.

---

## 🔒 Security & Role-Based Access Control

1. **No Client-Side Trust**:
   Frontend JavaScript never decides user roles independently. Every dashboard request and mutation verifies the user's JWT token and fetches their authoritative role from the backend database.
2. **Backend API Protection**:
   - `require_admin` dependency rejects non-admin users with `403 Forbidden` on all `/api/admin/*` endpoints and event modification endpoints.
   - Members cannot access admin panels or promote themselves.
3. **Restricted Profile Editing**:
   - Members can edit: Full Name, Phone, Department, Year, Skills, Bio, Profile Photo.
   - Members **cannot** edit: Role, Team (assigned by admins), Points, or other members' accounts.
4. **Duplicate Registration Prevention**:
   - The database enforces `UNIQUE (member_id, event_id)` and `UNIQUE (member_id, hackathon_id)`. Attempting to register twice returns a clear conflict warning.

---

## 🗄️ Supabase PostgreSQL Setup (When Ready)

When you are ready to connect your live Supabase project:

1. Log in to [Supabase](https://supabase.com) and click **New Project**.
2. Go to **SQL Editor** in your Supabase Dashboard.
3. Copy the entire contents of [`database/schema.sql`](file:///Users/maheshbasarkod/Documents/untitled%20folder/analytix-club/database/schema.sql) and click **Run**.
   - This creates all 7 tables (`profiles`, `events`, `hackathons`, `announcements`, `registrations`, `hackathon_registrations`, `leaderboard`).
   - Configures foreign keys, cascade rules, and updated_at triggers.
   - Configures Row Level Security (RLS) policies.
   - Creates storage buckets (`posters`, `avatars`, `event-photos`).
4. Copy `backend/.env.example` to `backend/.env` (or project root `.env`).
5. Fill in your credentials:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   SUPABASE_JWT_SECRET=your-supabase-jwt-secret
   ```
6. Restart the backend:
   ```bash
   uvicorn backend.main:app --reload
   ```

---

## 👑 Creating the First Admin Account

1. Register an account via the website at `register.html` (e.g. `admin@college.edu`).
2. Go to **Supabase Dashboard -> SQL Editor** and execute:
   ```sql
   UPDATE public.profiles 
   SET role = 'admin', team = 'Tech' 
   WHERE email = 'admin@college.edu';
   ```
3. That user is now a full system administrator. They can log in to access `admin-dashboard.html` and promote other team leads to admins directly from the **Manage Members** panel.

