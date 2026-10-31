"""
Seed script to populate initial admin, member, events, hackathons, and announcements
into the live Supabase PostgreSQL database.
"""
import uuid
from datetime import datetime, timezone, timedelta
from backend.database import supabase_client, db

def seed_supabase():
    if not supabase_client:
        print("❌ Supabase client is not configured.")
        return

    print("🚀 Seeding live Supabase database...")
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # 1. CREATE ADMIN USER
    admin_email = "admin@analytixclub.edu"
    admin_password = "Admin@12345"
    admin_id = None

    try:
        # Check if already in auth
        users_resp = supabase_client.auth.admin.list_users()
        existing_admin = next((u for u in users_resp if u.email == admin_email), None)
        if existing_admin:
            admin_id = existing_admin.id
            print(f"ℹ️ Admin user already exists in Auth: {admin_id}")
        else:
            admin_user = supabase_client.auth.admin.create_user({
                "email": admin_email,
                "password": admin_password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": "Arjun Sharma (Club Lead)",
                    "role": "admin"
                }
            })
            admin_id = admin_user.user.id
            print(f"✅ Created Admin Auth user: {admin_email} (ID: {admin_id})")
        
        # Upsert profile with admin role
        supabase_client.table("profiles").upsert({
            "id": admin_id,
            "email": admin_email,
            "full_name": "Arjun Sharma (Club Lead)",
            "phone": "+91 98765 43210",
            "profile_photo": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80",
            "department": "Computer Science & Engineering",
            "year": "4th Year",
            "skills": "Python, FastAPI, Machine Learning, PostgreSQL, Leadership",
            "bio": "Lead coordinator of Analytix Club. Passionate about AI, Data Science and building student developer communities.",
            "role": "admin",
            "team": "Tech",
            "created_at": now_iso,
            "updated_at": now_iso
        }).execute()
        print("✅ Upserted Admin Profile in Supabase 'profiles' table.")
    except Exception as e:
        print(f"⚠️ Error creating admin user: {e}")

    # 2. CREATE MEMBER USER
    member_email = "member@analytixclub.edu"
    member_password = "Member@12345"
    member_id = None

    try:
        users_resp = supabase_client.auth.admin.list_users()
        existing_member = next((u for u in users_resp if u.email == member_email), None)
        if existing_member:
            member_id = existing_member.id
            print(f"ℹ️ Member user already exists in Auth: {member_id}")
        else:
            member_user = supabase_client.auth.admin.create_user({
                "email": member_email,
                "password": member_password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": "Priya Nair",
                    "role": "member"
                }
            })
            member_id = member_user.user.id
            print(f"✅ Created Member Auth user: {member_email} (ID: {member_id})")

        # Upsert member profile
        supabase_client.table("profiles").upsert({
            "id": member_id,
            "email": member_email,
            "full_name": "Priya Nair",
            "phone": "+91 98765 12345",
            "profile_photo": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&auto=format&fit=crop&q=80",
            "department": "Information Technology",
            "year": "3rd Year",
            "skills": "Figma, UI/UX, CSS, Graphic Design",
            "bio": "Creative thinker and UI enthusiast. Love designing engaging posters and accessible web interfaces.",
            "role": "member",
            "team": "Design",
            "created_at": now_iso,
            "updated_at": now_iso
        }).execute()
        print("✅ Upserted Member Profile in Supabase 'profiles' table.")
    except Exception as e:
        print(f"⚠️ Error creating member user: {e}")

    # 3. SEED EVENTS
    ev1_id = "11111111-1111-1111-1111-111111111111"
    ev2_id = "22222222-2222-2222-2222-222222222222"
    ev3_id = "33333333-3333-3333-3333-333333333333"

    events = [
        {
            "id": ev1_id,
            "title": "Data Crunch 2026: Campus Analytics Hackathon",
            "description": "Our premier flagship annual analytics and machine learning competition! Form teams of 2 to 4 members to solve real-world predictive modeling challenges.",
            "poster_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80",
            "event_date": (now + timedelta(days=14)).isoformat(),
            "registration_deadline": (now + timedelta(days=10)).isoformat(),
            "venue": "Campus Innovation Lab & Main Auditorium",
            "instructions": "Bring your laptop, charger, and university ID card. Pre-installed Python 3.10+ and Jupyter Notebook is recommended.",
            "status": "published",
            "created_by": admin_id or "00000000-0000-0000-0000-000000000001",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": ev2_id,
            "title": "Hands-on PyData & FastAPI Workshop",
            "description": "A beginner-to-intermediate crash course on modern Python backend engineering, RESTful APIs, and integrating PostgreSQL databases.",
            "poster_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=80",
            "event_date": (now + timedelta(days=7)).isoformat(),
            "registration_deadline": (now + timedelta(days=5)).isoformat(),
            "venue": "Lab 402, Computer Science Block",
            "instructions": "All participants will receive workshop source code and verified certificate of completion.",
            "status": "published",
            "created_by": admin_id or "00000000-0000-0000-0000-000000000001",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": ev3_id,
            "title": "UI/UX Design Sprint for Developers",
            "description": "Hosted by our Design Team! Learn how to transform rough wireframes into sleek, modern, accessible design systems using Figma.",
            "poster_url": "https://images.unsplash.com/photo-1581291518857-4e27b48ff24e?w=800&auto=format&fit=crop&q=80",
            "event_date": (now + timedelta(days=21)).isoformat(),
            "registration_deadline": (now + timedelta(days=18)).isoformat(),
            "venue": "Design Studio 201",
            "instructions": "No prior Figma experience required. Sign up for a free Figma educational account beforehand.",
            "status": "published",
            "created_by": admin_id or "00000000-0000-0000-0000-000000000001",
            "created_at": now_iso,
            "updated_at": now_iso
        }
    ]

    for ev in events:
        try:
            supabase_client.table("events").upsert(ev).execute()
        except Exception as e:
            print(f"Error upserting event {ev['title']}: {e}")
    print(f"✅ Upserted {len(events)} events.")

    # 4. SEED HACKATHONS
    h1_id = "44444444-4444-4444-4444-444444444444"
    h2_id = "55555555-5555-5555-5555-555555555555"

    hackathons = [
        {
            "id": h1_id,
            "title": "Smart India National Innovation Challenge 2026",
            "organizer": "Ministry of Education & AICTE",
            "description": "Nationwide digital initiative providing students a platform to solve pressing problems faced by ministries, departments and industry leaders.",
            "poster_url": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&auto=format&fit=crop&q=80",
            "start_date": (now + timedelta(days=30)).isoformat(),
            "deadline": (now + timedelta(days=20)).isoformat(),
            "location": "National / Hybrid",
            "mode": "hybrid",
            "registration_link": "https://sih.gov.in",
            "eligibility": "All enrolled college undergraduate and graduate students",
            "required_skills": "Fullstack, AI/ML, IoT, Cloud, Problem Solving",
            "status": "published",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": h2_id,
            "title": "Google Cloud Generative AI Global Hackathon",
            "organizer": "Google Cloud Developer Community",
            "description": "Build high-impact multimodal applications and autonomous AI agents using Gemini models, Vertex AI, and Google Cloud services.",
            "poster_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=80",
            "start_date": (now + timedelta(days=15)).isoformat(),
            "deadline": (now + timedelta(days=12)).isoformat(),
            "location": "Online / Virtual",
            "mode": "online",
            "registration_link": "https://cloud.google.com/innovators",
            "eligibility": "Open to all developers and students worldwide",
            "required_skills": "Python, Gemini API, RAG, Web Development",
            "status": "published",
            "created_at": now_iso,
            "updated_at": now_iso
        }
    ]

    for h in hackathons:
        try:
            supabase_client.table("hackathons").upsert(h).execute()
        except Exception as e:
            print(f"Error upserting hackathon {h['title']}: {e}")
    print(f"✅ Upserted {len(hackathons)} hackathons.")

    # 5. SEED ANNOUNCEMENTS
    announcements = [
        {
            "id": "66666666-6666-6666-6666-666666666666",
            "title": "Welcome to Analytix Club Academic Year 2026-27!",
            "description": "We are thrilled to welcome our newest batch of members! Weekly club workshops, hackathons, and project mentorship sessions start this Friday at 4:30 PM.",
            "image_url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&auto=format&fit=crop&q=80",
            "status": "published",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "id": "77777777-7777-7777-7777-777777777777",
            "title": "Call for Project Mentors: Tech, Design & MOC Teams",
            "description": "Senior members interested in leading teams for upcoming inter-college analytics competitions can apply via the dashboard.",
            "image_url": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&auto=format&fit=crop&q=80",
            "status": "published",
            "created_at": now_iso,
            "updated_at": now_iso
        }
    ]

    for a in announcements:
        try:
            supabase_client.table("announcements").upsert(a).execute()
        except Exception as e:
            print(f"Error upserting announcement {a['title']}: {e}")
    print(f"✅ Upserted {len(announcements)} announcements.")

    # 6. SEED LEADERBOARD
    if member_id and admin_id:
        leaderboard_items = [
            {
                "id": str(uuid.uuid4()),
                "member_id": member_id,
                "points": 50,
                "activity_description": "Designed primary banner and posters for Data Crunch 2026",
                "awarded_by": admin_id,
                "created_at": now_iso
            }
        ]
        for item in leaderboard_items:
            try:
                supabase_client.table("leaderboard").insert(item).execute()
            except Exception as e:
                print(f"Error inserting leaderboard item: {e}")
        print("✅ Upserted Leaderboard sample entries.")

    print("\n🎉 Live Supabase seeding complete!")
    print(f"👉 Admin login: {admin_email} / {admin_password}")
    print(f"👉 Member login: {member_email} / {member_password}")

if __name__ == "__main__":
    seed_supabase()
