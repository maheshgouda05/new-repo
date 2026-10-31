import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_login_as_member():
    response = client.post("/api/auth/login", json={
        "email": "member@analytixclub.edu",
        "password": "Member@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "member"
    assert data["user"]["email"] == "member@analytixclub.edu"

def test_login_as_admin():
    response = client.post("/api/auth/login", json={
        "email": "admin@analytixclub.edu",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"

def test_member_registration_always_assigns_member_role():
    response = client.post("/api/auth/register", json={
        "email": "newstudent@analytixclub.edu",
        "password": "Password@123",
        "full_name": "New Student",
        "phone": "+91 99999 88888",
        "department": "Computer Science",
        "year": "1st Year",
        "skills": "Python, C++",
        "bio": "Enthusiastic beginner coder"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "member"

def test_member_forbidden_from_admin_overview():
    member_res = client.post("/api/auth/login", json={
        "email": "member@analytixclub.edu",
        "password": "Member@123"
    })
    member_token = member_res.json()["access_token"]

    response = client.get("/api/admin/overview", headers={
        "Authorization": f"Bearer {member_token}"
    })
    assert response.status_code == 403
    assert "Admin authorization required" in response.json()["detail"]

def test_member_forbidden_from_creating_event():
    member_res = client.post("/api/auth/login", json={
        "email": "member@analytixclub.edu",
        "password": "Member@123"
    })
    member_token = member_res.json()["access_token"]

    response = client.post("/api/events", headers={
        "Authorization": f"Bearer {member_token}"
    }, json={
        "title": "Unauthorized Member Event",
        "description": "This should be rejected",
        "venue": "Lab 1",
        "event_date": "2026-12-01T10:00:00Z",
        "registration_deadline": "2026-11-30T18:00:00Z"
    })
    assert response.status_code == 403

def test_admin_can_access_overview_and_create_event():
    admin_res = client.post("/api/auth/login", json={
        "email": "admin@analytixclub.edu",
        "password": "Admin@123"
    })
    admin_token = admin_res.json()["access_token"]

    overview_res = client.get("/api/admin/overview", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert overview_res.status_code == 200
    assert "total_members" in overview_res.json()

    event_res = client.post("/api/events", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={
        "title": "FastAPI & Supabase Masterclass",
        "description": "Learn modern backend API development with PostgreSQL RLS security.",
        "venue": "Seminar Hall 1",
        "event_date": "2026-11-28T14:00:00Z",
        "registration_deadline": "2026-11-27T23:59:00Z",
        "instructions": "Bring your laptop and college ID card.",
        "status": "published"
    })
    assert event_res.status_code == 200
    created_event = event_res.json()
    event_id = created_event["id"]

    member_res = client.post("/api/auth/login", json={
        "email": "member@analytixclub.edu",
        "password": "Member@123"
    })
    member_token = member_res.json()["access_token"]

    reg_res = client.post(f"/api/registrations/events/{event_id}", headers={
        "Authorization": f"Bearer {member_token}"
    })
    assert reg_res.status_code == 200
    assert reg_res.json()["status"] == "pending"

    dup_res = client.post(f"/api/registrations/events/{event_id}", headers={
        "Authorization": f"Bearer {member_token}"
    })
    assert dup_res.status_code == 409
    assert "already registered" in dup_res.json()["detail"].lower()

def test_hackathon_creation_and_registration():
    admin_res = client.post("/api/auth/login", json={
        "email": "admin@analytixclub.edu",
        "password": "Admin@123"
    })
    admin_token = admin_res.json()["access_token"]

    hack_res = client.post("/api/hackathons", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={
        "title": "AI Innovation Summit Hackathon",
        "organizer": "Analytix & AWS",
        "description": "Build generative AI solutions for smart universities.",
        "start_date": "2026-12-10T09:00:00Z",
        "deadline": "2026-12-05T18:00:00Z",
        "location": "Innovation Lab & Online",
        "mode": "hybrid",
        "registration_link": "https://aws.amazon.com",
        "eligibility": "Open to all engineering students",
        "required_skills": "Python, LLMs, REST APIs",
        "status": "published"
    })
    assert hack_res.status_code == 200
    hackathon_id = hack_res.json()["id"]

    member_res = client.post("/api/auth/login", json={
        "email": "member@analytixclub.edu",
        "password": "Member@123"
    })
    member_token = member_res.json()["access_token"]

    apply_res = client.post(f"/api/registrations/hackathons/{hackathon_id}", headers={
        "Authorization": f"Bearer {member_token}"
    }, json={
        "hackathon_id": hackathon_id,
        "team_name": "Analytix Neural Squad"
    })
    assert apply_res.status_code == 200
    assert apply_res.json()["status"] == "registered"

def test_announcement_crud():
    admin_res = client.post("/api/auth/login", json={
        "email": "admin@analytixclub.edu",
        "password": "Admin@123"
    })
    admin_token = admin_res.json()["access_token"]

    ann_res = client.post("/api/announcements", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={
        "title": "Club Hackathon Prep Session Tomorrow",
        "description": "Join Google Meet at 7:00 PM for project pitch guidelines.",
        "category": "Urgent",
        "status": "published"
    })
    assert ann_res.status_code == 200
    ann_id = ann_res.json()["id"]

    list_res = client.get("/api/announcements")
    assert list_res.status_code == 200
    assert any(a["id"] == ann_id for a in list_res.json())

def test_admin_member_management_team_and_role():
    admin_res = client.post("/api/auth/login", json={
        "email": "admin@analytixclub.edu",
        "password": "Admin@123"
    })
    admin_token = admin_res.json()["access_token"]

    members_res = client.get("/api/admin/members", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert members_res.status_code == 200
    members = members_res.json()
    target_member = next(m for m in members if m["role"] == "member")
    target_id = target_member["id"]

    team_res = client.patch(f"/api/admin/members/{target_id}/team", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={"team": "Design"})
    assert team_res.status_code == 200
    assert team_res.json()["team"] == "Design"

    role_res = client.patch(f"/api/admin/members/{target_id}/role", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={"role": "admin"})
    assert role_res.status_code == 200
    assert role_res.json()["role"] == "admin"

    demote_res = client.patch(f"/api/admin/members/{target_id}/role", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={"role": "member"})
    assert demote_res.status_code == 200
    assert demote_res.json()["role"] == "member"

def test_admin_award_points_and_leaderboard():
    admin_res = client.post("/api/auth/login", json={
        "email": "admin@analytixclub.edu",
        "password": "Admin@123"
    })
    admin_token = admin_res.json()["access_token"]

    members_res = client.get("/api/admin/members", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert members_res.status_code == 200
    members = members_res.json()
    target_member = next(m for m in members if m["role"] == "member")

    award_res = client.post("/api/admin/leaderboard/award", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={
        "member_id": target_member["id"],
        "points": 35,
        "activity_description": "Built automated test suite for club backend"
    })
    assert award_res.status_code == 200

    leaderboard_res = client.get("/api/members/leaderboard", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert leaderboard_res.status_code == 200
    leaderboard = leaderboard_res.json()
    assert len(leaderboard) > 0
    ranked_member = next(item for item in leaderboard if item["member_id"] == target_member["id"])
    assert ranked_member["total_points"] >= 35

def test_member_profile_update_permissions():
    member_res = client.post("/api/auth/login", json={
        "email": "member@analytixclub.edu",
        "password": "Member@123"
    })
    member_token = member_res.json()["access_token"]

    update_res = client.put("/api/members/me", headers={
        "Authorization": f"Bearer {member_token}"
    }, json={
        "full_name": "Priya Nair (Lead Designer)",
        "phone": "+91 99999 11111",
        "skills": "Figma, Advanced UI Prototyping, CSS",
        "bio": "Updated bio description."
    })
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["full_name"] == "Priya Nair (Lead Designer)"
    assert data["role"] == "member"
