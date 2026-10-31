import uuid
import logging
import bcrypt
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from backend.config import settings
from backend.models.user import normalize_phone_number

logger = logging.getLogger("analytix.database")

# Supabase Client setup (attempted if configured)
supabase_client = None
if settings.is_supabase_configured:
    try:
        from supabase import create_client, Client
        supabase_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
        )
        logger.info("Connected to Supabase PostgreSQL.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase_client = None
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(f"CRITICAL: Failed to initialize Supabase client in production: {e}")
else:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("CRITICAL: Supabase credentials are missing in production! In-memory fallback is disabled.")
    logger.info("Supabase credentials not configured. Running in local standalone/development mode.")

# ==============================================================================
# LOCAL / FALLBACK IN-MEMORY REPOSITORY
# Seeded with realistic club data so all features work out-of-the-box in VS Code!
# ==============================================================================
class InMemoryStore:
    def __init__(self):
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.passwords: Dict[str, str] = {}  # user_id -> hashed password
        self.events: Dict[str, Dict[str, Any]] = {}
        self.hackathons: Dict[str, Dict[str, Any]] = {}
        self.announcements: Dict[str, Dict[str, Any]] = {}
        self.registrations: Dict[str, Dict[str, Any]] = {}
        self.hackathon_registrations: Dict[str, Dict[str, Any]] = {}
        self.leaderboard_records: List[Dict[str, Any]] = []
        self._seed_sample_data()

    def _hash(self, password: str) -> str:
        pwd_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

    def _seed_sample_data(self):
        admin_id = "00000000-0000-0000-0000-000000000001"
        member_id = "00000000-0000-0000-0000-000000000002"
        member2_id = "00000000-0000-0000-0000-000000000003"
        member3_id = "00000000-0000-0000-0000-000000000004"

        now = datetime.now(timezone.utc).isoformat()

        # Seed Users
        self.profiles[admin_id] = {
            "id": admin_id,
            "email": "admin@analytixclub.edu",
            "full_name": "Arjun Sharma (Club Lead)",
            "phone": "+91 98765 43210",
            "profile_photo": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            "department": "Computer Science & Engineering",
            "year": "4th Year",
            "skills": "Python, FastAPI, Machine Learning, Leadership",
            "bio": "Lead coordinator of Analytix Club. Passionate about AI & Big Data.",
            "role": "admin",
            "team": "Tech",
            "created_at": now,
            "updated_at": now
        }
        self.passwords[admin_id] = self._hash("Admin@123")

        self.profiles[member_id] = {
            "id": member_id,
            "email": "member@analytixclub.edu",
            "full_name": "Priya Nair",
            "phone": "+91 98765 12345",
            "profile_photo": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
            "department": "Information Technology",
            "year": "3rd Year",
            "skills": "Figma, UI/UX, CSS, Graphic Design",
            "bio": "Creative thinker and UI enthusiast. Love designing engaging posters and intuitive digital interfaces.",
            "role": "member",
            "team": "Design",
            "created_at": now,
            "updated_at": now
        }
        self.passwords[member_id] = self._hash("Member@123")

        self.profiles[member2_id] = {
            "id": member2_id,
            "email": "rohit.verma@analytixclub.edu",
            "full_name": "Rohit Verma",
            "phone": "+91 98123 45678",
            "profile_photo": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
            "department": "Data Science & AI",
            "year": "2nd Year",
            "skills": "Python, Pandas, SQL, Scikit-learn",
            "bio": "Data geek exploring deep learning architectures and predictive modeling.",
            "role": "member",
            "team": "Tech",
            "created_at": now,
            "updated_at": now
        }
        self.passwords[member2_id] = self._hash("Member@123")

        self.profiles[member3_id] = {
            "id": member3_id,
            "email": "sneha.k@analytixclub.edu",
            "full_name": "Sneha Kulkarni",
            "phone": "+91 97654 32109",
            "profile_photo": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&auto=format&fit=crop&q=80",
            "department": "Electronics & Communication",
            "year": "3rd Year",
            "skills": "Public Speaking, Content Writing, Event Logistics",
            "bio": "MOC team coordinator handling event coverage, stage moderation, and press releases.",
            "role": "member",
            "team": "MOC",
            "created_at": now,
            "updated_at": now
        }
        self.passwords[member3_id] = self._hash("Member@123")

        # Seed Events
        ev1_id = "10000000-0000-0000-0000-000000000001"
        ev2_id = "10000000-0000-0000-0000-000000000002"
        self.events[ev1_id] = {
            "id": ev1_id,
            "title": "Data Crunch 2026: Hands-on Machine Learning Bootcamp",
            "description": "An intensive weekend bootcamp covering exploratory data analysis, feature engineering, and deploying ML models with FastAPI. Open to all students.",
            "poster_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80",
            "photos": [
                "https://images.unsplash.com/photo-1531482615713-2afd69097998?w=800&auto=format&fit=crop&q=80"
            ],
            "event_date": "2026-11-15T10:00:00Z",
            "venue": "Auditorium Hall B & Virtual Stream",
            "registration_deadline": "2026-11-14T18:00:00Z",
            "instructions": "Bring your laptop with Python 3.10+ installed and VS Code ready. Extension cords and high-speed Wi-Fi provided.",
            "status": "published",
            "created_by": admin_id,
            "created_at": now,
            "updated_at": now
        }
        self.events[ev2_id] = {
            "id": ev2_id,
            "title": "Design Sprint: Crafting Engaging Data Visualizations",
            "description": "Learn how to turn boring spreadsheets into compelling, narrative-driven UI dashboards using Figma and interactive charts.",
            "poster_url": "https://images.unsplash.com/photo-1542744094-3a31f272c490?w=800&auto=format&fit=crop&q=80",
            "photos": [],
            "event_date": "2026-11-22T14:00:00Z",
            "venue": "Design Studio Lab 3",
            "registration_deadline": "2026-11-21T23:59:00Z",
            "instructions": "No prior design experience required. Bring your laptop and your curiosity!",
            "status": "published",
            "created_by": admin_id,
            "created_at": now,
            "updated_at": now
        }

        # Seed Hackathons
        h1_id = "20000000-0000-0000-0000-000000000001"
        self.hackathons[h1_id] = {
            "id": h1_id,
            "title": "HackAnalytix 36-Hour National Hackathon",
            "organizer": "Analytix Club x Tech Titans",
            "description": "Build real-world solutions across AI/ML, FinTech, and Smart Campus automation. Cash prizes worth ₹1,50,000 + internship offers for top teams.",
            "poster_url": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&auto=format&fit=crop&q=80",
            "start_date": "2026-12-05T09:00:00Z",
            "deadline": "2026-11-30T23:59:00Z",
            "location": "Main Campus Innovation Hub",
            "mode": "hybrid",
            "registration_link": "https://analytixclub.edu/hackanalytix-2026",
            "eligibility": "Open to all undergraduate and postgraduate students in teams of 2-4 members.",
            "required_skills": "Python, React / Web Dev, AI/ML APIs, Database Design",
            "status": "published",
            "created_by": admin_id,
            "created_at": now,
            "updated_at": now
        }

        # Seed Announcements
        a1_id = "30000000-0000-0000-0000-000000000001"
        a2_id = "30000000-0000-0000-0000-000000000002"
        self.announcements[a1_id] = {
            "id": a1_id,
            "title": "Welcome to Analytix Club Academic Year 2026-27!",
            "description": "Orientation meet for all new recruits will be held this Wednesday at 4:30 PM. Check your email for room details.",
            "image_url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&auto=format&fit=crop&q=80",
            "category": "Notice",
            "status": "published",
            "created_by": admin_id,
            "created_at": now,
            "updated_at": now
        }
        self.announcements[a2_id] = {
            "id": a2_id,
            "title": "Call for Project Mentors: Tech, Design & MOC",
            "description": "Senior members interested in leading teams for upcoming inter-college competitions can apply via the dashboard.",
            "image_url": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&auto=format&fit=crop&q=80",
            "category": "Opportunity",
            "status": "published",
            "created_by": admin_id,
            "created_at": now,
            "updated_at": now
        }

        # Seed Registrations
        reg1_id = "40000000-0000-0000-0000-000000000001"
        self.registrations[reg1_id] = {
            "id": reg1_id,
            "member_id": member_id,
            "event_id": ev1_id,
            "status": "approved",
            "registered_at": now
        }

        # Seed Leaderboard Records
        self.leaderboard_records.append({
            "id": str(uuid.uuid4()),
            "member_id": member_id,
            "points": 50,
            "activity_description": "Designed primary banner for Data Crunch 2026",
            "awarded_by": admin_id,
            "created_at": now
        })
        self.leaderboard_records.append({
            "id": str(uuid.uuid4()),
            "member_id": member2_id,
            "points": 75,
            "activity_description": "Built baseline ML pipeline for campus dataset challenge",
            "awarded_by": admin_id,
            "created_at": now
        })
        self.leaderboard_records.append({
            "id": str(uuid.uuid4()),
            "member_id": member3_id,
            "points": 60,
            "activity_description": "Organized venue logistics and anchor script for Orientation",
            "awarded_by": admin_id,
            "created_at": now
        })

store = InMemoryStore()

# ==============================================================================
# UNIFIED DATABASE REPOSITORY INTERFACE
# Handles both Supabase (if configured) and InMemoryStore (if local/dev mode)
# ==============================================================================
class Database:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            pwd_bytes = plain_password.encode('utf-8')[:72]
            return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
        except Exception:
            return False

    def hash_password(self, password: str) -> str:
        pwd_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

    # --- PROFILES / USERS ---
    def get_profile_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if supabase_client:
            res = supabase_client.table("profiles").select("*").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                p = res.data[0]
                p["points"] = self.get_member_points(user_id)
                return p
            return None
        profile = store.profiles.get(user_id)
        if profile:
            profile_copy = dict(profile)
            profile_copy["points"] = self.get_member_points(user_id)
            return profile_copy
        return None

    def get_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower()
        if supabase_client:
            res = supabase_client.table("profiles").select("*").eq("email", clean_email).execute()
            if res.data and len(res.data) > 0:
                p = res.data[0]
                p["points"] = self.get_member_points(p["id"])
                return p
            return None
        for p in store.profiles.values():
            if p["email"].strip().lower() == clean_email:
                p_copy = dict(p)
                p_copy["points"] = self.get_member_points(p_copy["id"])
                return p_copy
        return None

    def get_profile_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        clean_phone = normalize_phone_number(phone)
        if not clean_phone:
            return None
        if supabase_client:
            # 1. Direct match with normalized format
            res = supabase_client.table("profiles").select("*").eq("phone", clean_phone).execute()
            if res.data and len(res.data) > 0:
                p = res.data[0]
                p["points"] = self.get_member_points(p["id"])
                return p
            # 2. Match across all records in case of spaces or older format
            all_res = supabase_client.table("profiles").select("*").execute()
            for p in (all_res.data or []):
                if normalize_phone_number(p.get("phone", "")) == clean_phone:
                    p["points"] = self.get_member_points(p["id"])
                    return p
            return None
        for p in store.profiles.values():
            if normalize_phone_number(p.get("phone", "")) == clean_phone:
                p_copy = dict(p)
                p_copy["points"] = self.get_member_points(p_copy["id"])
                return p_copy
        return None

    def create_user(self, user_dict: Dict[str, Any], password_hash: str) -> Dict[str, Any]:
        user_id = user_dict.get("id") or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        record = {
            "id": user_id,
            "email": user_dict["email"].strip().lower(),
            "full_name": user_dict["full_name"],
            "phone": normalize_phone_number(user_dict.get("phone", "")),
            "profile_photo": user_dict.get("profile_photo", ""),
            "department": user_dict.get("department", ""),
            "year": user_dict.get("year", ""),
            "skills": user_dict.get("skills", ""),
            "bio": user_dict.get("bio", ""),
            "role": user_dict.get("role", "member"),
            "team": user_dict.get("team", "None"),
            "created_at": now,
            "updated_at": now
        }

        if supabase_client:
            # When Supabase is connected, users are inserted via Supabase Auth signup or service role
            res = supabase_client.table("profiles").upsert(record).execute()
            return res.data[0] if res.data else record
        
        store.profiles[user_id] = record
        store.passwords[user_id] = password_hash
        record_copy = dict(record)
        record_copy["points"] = 0
        return record_copy

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now
        if "phone" in updates and updates["phone"]:
            updates["phone"] = normalize_phone_number(updates["phone"])
        
        if supabase_client:
            res = supabase_client.table("profiles").update(updates).eq("id", user_id).execute()
            return res.data[0] if res.data else None
            
        if user_id in store.profiles:
            store.profiles[user_id].update(updates)
            p = dict(store.profiles[user_id])
            p["points"] = self.get_member_points(user_id)
            return p
        return None

    def list_profiles(self, search: Optional[str] = None, team: Optional[str] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
        if supabase_client:
            query = supabase_client.table("profiles").select("*")
            if team and team != "All":
                query = query.eq("team", team)
            if role and role != "All":
                query = query.eq("role", role)
            res = query.order("full_name").execute()
            results = res.data or []
            for r in results:
                r["points"] = self.get_member_points(r["id"])
            if search:
                s = search.lower()
                results = [r for r in results if s in r["full_name"].lower() or s in r["email"].lower()]
            return results

        results = list(store.profiles.values())
        if search:
            s = search.lower()
            results = [r for r in results if s in r["full_name"].lower() or s in r["email"].lower()]
        if team and team != "All":
            results = [r for r in results if r.get("team") == team]
        if role and role != "All":
            results = [r for r in results if r.get("role") == role]

        for r in results:
            r["points"] = self.get_member_points(r["id"])
        return sorted(results, key=lambda x: x["full_name"])

    # --- EVENTS ---
    def list_events(self, status: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        if supabase_client:
            query = supabase_client.table("events").select("*")
            if status:
                query = query.eq("status", status)
            res = query.order("event_date", desc=False).execute()
            events = res.data or []
        else:
            events = list(store.events.values())
            if status:
                events = [e for e in events if e.get("status") == status]
            events = sorted(events, key=lambda x: x.get("event_date", ""))

        # Attach registrations count and user registration status
        for e in events:
            e["registrations_count"] = self.count_event_registrations(e["id"])
            if user_id:
                reg = self.get_registration(user_id, e["id"])
                e["is_registered"] = bool(reg)
                e["my_registration_status"] = reg["status"] if reg else None
            else:
                e["is_registered"] = False
                e["my_registration_status"] = None
        return events

    def get_event_by_id(self, event_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        event = None
        if supabase_client:
            res = supabase_client.table("events").select("*").eq("id", event_id).execute()
            if res.data and len(res.data) > 0:
                event = res.data[0]
        else:
            event = store.events.get(event_id)

        if event:
            event_copy = dict(event)
            event_copy["registrations_count"] = self.count_event_registrations(event_id)
            if user_id:
                reg = self.get_registration(user_id, event_id)
                event_copy["is_registered"] = bool(reg)
                event_copy["my_registration_status"] = reg["status"] if reg else None
            return event_copy
        return None

    def create_event(self, event_dict: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": event_id,
            "title": event_dict["title"],
            "description": event_dict["description"],
            "venue": event_dict["venue"],
            "event_date": event_dict["event_date"].isoformat() if hasattr(event_dict["event_date"], "isoformat") else str(event_dict["event_date"]),
            "registration_deadline": event_dict["registration_deadline"].isoformat() if hasattr(event_dict["registration_deadline"], "isoformat") else str(event_dict["registration_deadline"]),
            "instructions": event_dict.get("instructions", ""),
            "status": event_dict.get("status", "published"),
            "poster_url": event_dict.get("poster_url", ""),
            "photos": event_dict.get("photos", []),
            "created_by": created_by,
            "created_at": now,
            "updated_at": now
        }

        if supabase_client:
            res = supabase_client.table("events").insert(record).execute()
            return res.data[0] if res.data else record
            
        store.events[event_id] = record
        return record

    def update_event(self, event_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        clean_updates = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in updates.items() if v is not None}
        clean_updates["updated_at"] = now

        if supabase_client:
            res = supabase_client.table("events").update(clean_updates).eq("id", event_id).execute()
            return res.data[0] if res.data else None

        if event_id in store.events:
            store.events[event_id].update(clean_updates)
            return dict(store.events[event_id])
        return None

    def delete_event(self, event_id: str) -> bool:
        if supabase_client:
            res = supabase_client.table("events").delete().eq("id", event_id).execute()
            return True
        if event_id in store.events:
            del store.events[event_id]
            # Also clean up registrations
            store.registrations = {k: v for k, v in store.registrations.items() if v.get("event_id") != event_id}
            return True
        return False

    # --- HACKATHONS ---
    def list_hackathons(self, status: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        hackathons = []
        if supabase_client:
            query = supabase_client.table("hackathons").select("*")
            if status:
                query = query.eq("status", status)
            res = query.order("start_date", desc=False).execute()
            hackathons = res.data or []
        else:
            hackathons = list(store.hackathons.values())
            if status:
                hackathons = [h for h in hackathons if h.get("status") == status]
            hackathons = sorted(hackathons, key=lambda x: x.get("start_date", ""))

        for h in hackathons:
            if user_id:
                reg = self.get_hackathon_registration(user_id, h["id"])
                h["is_registered"] = bool(reg)
                h["my_registration_status"] = reg["status"] if reg else None
            else:
                h["is_registered"] = False
                h["my_registration_status"] = None
        return hackathons

    def get_hackathon_by_id(self, hackathon_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        hackathon = None
        if supabase_client:
            res = supabase_client.table("hackathons").select("*").eq("id", hackathon_id).execute()
            if res.data and len(res.data) > 0:
                hackathon = res.data[0]
        else:
            hackathon = store.hackathons.get(hackathon_id)

        if hackathon:
            h_copy = dict(hackathon)
            if user_id:
                reg = self.get_hackathon_registration(user_id, hackathon_id)
                h_copy["is_registered"] = bool(reg)
                h_copy["my_registration_status"] = reg["status"] if reg else None
            return h_copy
        return None

    def create_hackathon(self, h_dict: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        h_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": h_id,
            "title": h_dict["title"],
            "organizer": h_dict["organizer"],
            "description": h_dict["description"],
            "start_date": h_dict["start_date"].isoformat() if hasattr(h_dict["start_date"], "isoformat") else str(h_dict["start_date"]),
            "deadline": h_dict["deadline"].isoformat() if hasattr(h_dict["deadline"], "isoformat") else str(h_dict["deadline"]),
            "location": h_dict["location"],
            "mode": h_dict.get("mode", "online"),
            "registration_link": h_dict.get("registration_link", ""),
            "eligibility": h_dict.get("eligibility", "All college students"),
            "required_skills": h_dict.get("required_skills", ""),
            "status": h_dict.get("status", "published"),
            "poster_url": h_dict.get("poster_url", ""),
            "created_by": created_by,
            "created_at": now,
            "updated_at": now
        }

        if supabase_client:
            res = supabase_client.table("hackathons").insert(record).execute()
            return res.data[0] if res.data else record
            
        store.hackathons[h_id] = record
        return record

    def update_hackathon(self, hackathon_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        clean_updates = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in updates.items() if v is not None}
        clean_updates["updated_at"] = now

        if supabase_client:
            res = supabase_client.table("hackathons").update(clean_updates).eq("id", hackathon_id).execute()
            return res.data[0] if res.data else None

        if hackathon_id in store.hackathons:
            store.hackathons[hackathon_id].update(clean_updates)
            return dict(store.hackathons[hackathon_id])
        return None

    def delete_hackathon(self, hackathon_id: str) -> bool:
        if supabase_client:
            supabase_client.table("hackathons").delete().eq("id", hackathon_id).execute()
            return True
        if hackathon_id in store.hackathons:
            del store.hackathons[hackathon_id]
            store.hackathon_registrations = {k: v for k, v in store.hackathon_registrations.items() if v.get("hackathon_id") != hackathon_id}
            return True
        return False

    # --- ANNOUNCEMENTS ---
    def list_announcements(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if supabase_client:
            query = supabase_client.table("announcements").select("*")
            if status:
                query = query.eq("status", status)
            res = query.order("created_at", desc=True).execute()
            return res.data or []

        announcements = list(store.announcements.values())
        if status:
            announcements = [a for a in announcements if a.get("status") == status]
        return sorted(announcements, key=lambda x: x.get("created_at", ""), reverse=True)

    def create_announcement(self, a_dict: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        a_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": a_id,
            "title": a_dict["title"],
            "description": a_dict["description"],
            "category": a_dict.get("category", "General"),
            "image_url": a_dict.get("image_url", ""),
            "status": a_dict.get("status", "published"),
            "created_by": created_by,
            "created_at": now,
            "updated_at": now
        }

        if supabase_client:
            res = supabase_client.table("announcements").insert(record).execute()
            return res.data[0] if res.data else record
            
        store.announcements[a_id] = record
        return record

    def update_announcement(self, a_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        clean_updates["updated_at"] = now

        if supabase_client:
            res = supabase_client.table("announcements").update(clean_updates).eq("id", a_id).execute()
            return res.data[0] if res.data else None

        if a_id in store.announcements:
            store.announcements[a_id].update(clean_updates)
            return dict(store.announcements[a_id])
        return None

    def delete_announcement(self, a_id: str) -> bool:
        if supabase_client:
            supabase_client.table("announcements").delete().eq("id", a_id).execute()
            return True
        if a_id in store.announcements:
            del store.announcements[a_id]
            return True
        return False

    # --- REGISTRATIONS (EVENTS) ---
    def count_event_registrations(self, event_id: str) -> int:
        if supabase_client:
            res = supabase_client.table("registrations").select("id", count="exact").eq("event_id", event_id).execute()
            return res.count or len(res.data) if res.data else 0
        return sum(1 for r in store.registrations.values() if r.get("event_id") == event_id)

    def get_registration(self, member_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        if supabase_client:
            res = supabase_client.table("registrations").select("*").eq("member_id", member_id).eq("event_id", event_id).execute()
            return res.data[0] if res.data and len(res.data) > 0 else None
            
        for r in store.registrations.values():
            if r.get("member_id") == member_id and r.get("event_id") == event_id:
                return r
        return None

    def register_for_event(self, member_id: str, event_id: str) -> Dict[str, Any]:
        existing = self.get_registration(member_id, event_id)
        if existing:
            return existing

        reg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": reg_id,
            "member_id": member_id,
            "event_id": event_id,
            "status": "pending",
            "registered_at": now
        }

        if supabase_client:
            res = supabase_client.table("registrations").insert(record).execute()
            return res.data[0] if res.data else record
            
        store.registrations[reg_id] = record
        return record

    def cancel_event_registration(self, member_id: str, event_id: str) -> bool:
        if supabase_client:
            supabase_client.table("registrations").delete().eq("member_id", member_id).eq("event_id", event_id).execute()
            return True
        for k, v in list(store.registrations.items()):
            if v.get("member_id") == member_id and v.get("event_id") == event_id:
                del store.registrations[k]
                return True
        return False

    def list_user_event_registrations(self, member_id: str) -> List[Dict[str, Any]]:
        regs = []
        if supabase_client:
            res = supabase_client.table("registrations").select("*, events(*)").eq("member_id", member_id).order("registered_at", desc=True).execute()
            for row in res.data or []:
                row["event"] = row.get("events")
                regs.append(row)
            return regs

        for r in store.registrations.values():
            if r.get("member_id") == member_id:
                r_copy = dict(r)
                r_copy["event"] = store.events.get(r.get("event_id"))
                regs.append(r_copy)
        return sorted(regs, key=lambda x: x.get("registered_at", ""), reverse=True)

    def list_all_event_registrations(self, event_id: Optional[str] = None) -> List[Dict[str, Any]]:
        regs = []
        if supabase_client:
            query = supabase_client.table("registrations").select("*, profiles(*), events(*)")
            if event_id:
                query = query.eq("event_id", event_id)
            res = query.order("registered_at", desc=True).execute()
            for row in res.data or []:
                row["member"] = row.get("profiles")
                row["event"] = row.get("events")
                regs.append(row)
            return regs

        for r in store.registrations.values():
            if not event_id or r.get("event_id") == event_id:
                r_copy = dict(r)
                r_copy["member"] = store.profiles.get(r.get("member_id"))
                r_copy["event"] = store.events.get(r.get("event_id"))
                regs.append(r_copy)
        return sorted(regs, key=lambda x: x.get("registered_at", ""), reverse=True)

    def update_registration_status(self, reg_id: str, status: str) -> Optional[Dict[str, Any]]:
        if supabase_client:
            res = supabase_client.table("registrations").update({"status": status}).eq("id", reg_id).execute()
            return res.data[0] if res.data else None

        if reg_id in store.registrations:
            store.registrations[reg_id]["status"] = status
            return dict(store.registrations[reg_id])
        return None

    # --- HACKATHON REGISTRATIONS ---
    def get_hackathon_registration(self, member_id: str, hackathon_id: str) -> Optional[Dict[str, Any]]:
        if supabase_client:
            res = supabase_client.table("hackathon_registrations").select("*").eq("member_id", member_id).eq("hackathon_id", hackathon_id).execute()
            return res.data[0] if res.data and len(res.data) > 0 else None

        for r in store.hackathon_registrations.values():
            if r.get("member_id") == member_id and r.get("hackathon_id") == hackathon_id:
                return r
        return None

    def register_for_hackathon(self, member_id: str, hackathon_id: str, team_name: str = "") -> Dict[str, Any]:
        existing = self.get_hackathon_registration(member_id, hackathon_id)
        if existing:
            return existing

        reg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": reg_id,
            "member_id": member_id,
            "hackathon_id": hackathon_id,
            "team_name": team_name,
            "status": "registered",
            "registered_at": now
        }

        if supabase_client:
            res = supabase_client.table("hackathon_registrations").insert(record).execute()
            return res.data[0] if res.data else record
            
        store.hackathon_registrations[reg_id] = record
        return record

    def list_user_hackathon_registrations(self, member_id: str) -> List[Dict[str, Any]]:
        regs = []
        if supabase_client:
            res = supabase_client.table("hackathon_registrations").select("*, hackathons(*)").eq("member_id", member_id).order("registered_at", desc=True).execute()
            for row in res.data or []:
                row["hackathon"] = row.get("hackathons")
                regs.append(row)
            return regs

        for r in store.hackathon_registrations.values():
            if r.get("member_id") == member_id:
                r_copy = dict(r)
                r_copy["hackathon"] = store.hackathons.get(r.get("hackathon_id"))
                regs.append(r_copy)
        return sorted(regs, key=lambda x: x.get("registered_at", ""), reverse=True)

    # --- LEADERBOARD & POINTS ---
    def get_member_points(self, member_id: str) -> int:
        if supabase_client:
            res = supabase_client.table("leaderboard").select("points").eq("member_id", member_id).execute()
            return sum(item["points"] for item in (res.data or []))
        return sum(rec["points"] for rec in store.leaderboard_records if rec["member_id"] == member_id)

    def award_points(self, member_id: str, points: int, description: str, awarded_by: str) -> Dict[str, Any]:
        rec_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": rec_id,
            "member_id": member_id,
            "points": points,
            "activity_description": description,
            "awarded_by": awarded_by,
            "created_at": now
        }

        if supabase_client:
            res = supabase_client.table("leaderboard").insert(record).execute()
            return res.data[0] if res.data else record

        store.leaderboard_records.append(record)
        return record

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        # Calculate leaderboard ranking across all members
        profiles = list(store.profiles.values()) if not supabase_client else (supabase_client.table("profiles").select("*").execute().data or [])
        
        leaderboard_data = []
        for p in profiles:
            p_id = p["id"]
            if supabase_client:
                records = supabase_client.table("leaderboard").select("*").eq("member_id", p_id).execute().data or []
            else:
                records = [r for r in store.leaderboard_records if r["member_id"] == p_id]
            
            total_points = sum(r["points"] for r in records)
            leaderboard_data.append({
                "member_id": p_id,
                "full_name": p["full_name"],
                "email": p["email"],
                "department": p.get("department", ""),
                "year": p.get("year", ""),
                "team": p.get("team", "None"),
                "profile_photo": p.get("profile_photo", ""),
                "total_points": total_points,
                "activities_count": len(records),
                "rank": 0
            })

        # Sort by points descending, then name
        sorted_leaderboard = sorted(leaderboard_data, key=lambda x: (x["total_points"], x["activities_count"]), reverse=True)
        for idx, item in enumerate(sorted_leaderboard):
            item["rank"] = idx + 1
        return sorted_leaderboard

    # --- ADMIN OVERVIEW STATS ---
    def get_overview_stats(self) -> Dict[str, Any]:
        if supabase_client:
            try:
                total_members = len(supabase_client.table("profiles").select("id").execute().data or [])
                total_events = len(supabase_client.table("events").select("id").execute().data or [])
                total_hackathons = len(supabase_client.table("hackathons").select("id").execute().data or [])
                total_registrations = len(supabase_client.table("registrations").select("id").execute().data or [])
            except Exception as e:
                logger.error(f"Error querying Supabase overview stats: {e}")
                if settings.ENVIRONMENT == "production":
                    raise
                total_members, total_events, total_hackathons, total_registrations = 0, 0, 0, 0
        elif settings.ENVIRONMENT == "production":
            raise RuntimeError("Database unavailable in production environment.")
        else:
            total_members = len(store.profiles)
            total_events = len(store.events)
            total_hackathons = len(store.hackathons)
            total_registrations = len(store.registrations)
        
        # Recent activities
        recent_activities = []
        if supabase_client:
            try:
                # Latest event registrations
                reg_res = supabase_client.table("registrations").select("registered_at, profiles(full_name), events(title)").order("registered_at", desc=True).limit(5).execute()
                for r in (reg_res.data or []):
                    m_name = (r.get("profiles") or {}).get("full_name", "A member")
                    e_title = (r.get("events") or {}).get("title", "an event")
                    recent_activities.append({
                        "type": "registration",
                        "message": f"{m_name} registered for {e_title}",
                        "timestamp": r.get("registered_at")
                    })
                # Latest points awarded
                lb_res = supabase_client.table("leaderboard").select("points, activity_description, created_at, profiles(full_name)").order("created_at", desc=True).limit(5).execute()
                for l in (lb_res.data or []):
                    m_name = (l.get("profiles") or {}).get("full_name", "A member")
                    recent_activities.append({
                        "type": "award",
                        "message": f"+{l.get('points')} points awarded to {m_name} ({l.get('activity_description')})",
                        "timestamp": l.get("created_at")
                    })
            except Exception as e:
                logger.error(f"Error querying Supabase recent activities: {e}")
        elif settings.ENVIRONMENT != "production":
            # Only use in-memory store in local development
            for r in list(store.registrations.values())[-5:]:
                mem = store.profiles.get(r.get("member_id"), {})
                ev = store.events.get(r.get("event_id"), {})
                recent_activities.append({
                    "type": "registration",
                    "message": f"{mem.get('full_name', 'A member')} registered for {ev.get('title', 'an event')}",
                    "timestamp": r.get("registered_at")
                })
            for l in store.leaderboard_records[-5:]:
                mem = store.profiles.get(l.get("member_id"), {})
                recent_activities.append({
                    "type": "award",
                    "message": f"+{l.get('points')} points awarded to {mem.get('full_name', 'a member')} ({l.get('activity_description')})",
                    "timestamp": l.get("created_at")
                })

        recent_activities = sorted(recent_activities, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]

        return {
            "total_members": total_members,
            "total_events": total_events,
            "upcoming_hackathons": total_hackathons,
            "total_event_registrations": total_registrations,
            "recent_activities": recent_activities
        }

db = Database()
