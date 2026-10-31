import uuid
import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Known seeded credentials for tests
ADMIN_EMAIL = "admin@analytixclub.edu"
ADMIN_PASSWORD = "Admin@12345"

MEMBER_EMAIL = "member@analytixclub.edu"
MEMBER_PASSWORD = "Member@12345"

# --- 1. HEALTH CHECK ---
def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["supabase_configured"] is True
    assert data["database_connected"] is True

def test_public_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "members_count" in data
    assert "events_count" in data
    assert data["teams_count"] == 3

# --- 2. AUTHENTICATION & SECURITY ---
def test_admin_login():
    response = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == ADMIN_EMAIL

def test_member_login():
    response = client.post("/api/auth/login", json={
        "email": MEMBER_EMAIL,
        "password": MEMBER_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "member"
    assert data["user"]["email"] == MEMBER_EMAIL

def test_invalid_login():
    response = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": "WrongPassword@999"
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_new_member_registration():
    unique_email = f"student_{uuid.uuid4().hex[:8]}@analytixclub.edu"
    response = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": "SecurePassword@123",
        "full_name": "Test Student",
        "phone": "+91 91234 56789",
        "department": "Computer Science",
        "year": "1st Year",
        "skills": "Python, Data Analysis",
        "bio": "Excited to learn and collaborate with club members."
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    # Security: Verify that new registrations are strictly assigned 'member' role
    assert data["user"]["role"] == "member"
    assert data["user"]["email"] == unique_email

# --- 3. ROLE-BASED AUTHORIZATION & RESTRICTIONS ---
def test_member_forbidden_from_admin_endpoints():
    member_res = client.post("/api/auth/login", json={
        "email": MEMBER_EMAIL,
        "password": MEMBER_PASSWORD
    })
    member_token = member_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {member_token}"}

    # Overview endpoint
    overview_res = client.get("/api/admin/overview", headers=headers)
    assert overview_res.status_code == 403

    # Member list endpoint
    members_res = client.get("/api/admin/members", headers=headers)
    assert members_res.status_code == 403

    # Create event endpoint
    event_res = client.post("/api/events", headers=headers, json={
        "title": "Unauthorized Member Event",
        "description": "Should be blocked",
        "venue": "Hall A",
        "event_date": "2026-11-20T10:00:00Z",
        "registration_deadline": "2026-11-19T10:00:00Z"
    })
    assert event_res.status_code == 403

def test_admin_access_allowed():
    admin_res = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    admin_token = admin_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    overview_res = client.get("/api/admin/overview", headers=headers)
    assert overview_res.status_code == 200
    assert "total_members" in overview_res.json()

# --- 4. EVENT CREATION, EDITING & REGISTRATION ---
def test_event_crud_and_duplicate_registration():
    # 1. Admin logs in
    admin_res = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Admin creates a new event
    create_res = client.post("/api/events", headers=admin_headers, json={
        "title": "Automated Test Workshop 2026",
        "description": "Validating end-to-end event registration and duplicate protection.",
        "venue": "Campus Computing Center",
        "event_date": "2026-11-25T14:00:00Z",
        "registration_deadline": "2026-11-24T23:59:00Z",
        "instructions": "Bring laptop with Python installed.",
        "status": "published"
    })
    assert create_res.status_code == 200
    event_id = create_res.json()["id"]

    # 3. Admin edits the event
    edit_res = client.put(f"/api/events/{event_id}", headers=admin_headers, json={
        "title": "Automated Test Workshop 2026 (Updated)",
        "venue": "Main Hall"
    })
    assert edit_res.status_code == 200
    assert edit_res.json()["title"] == "Automated Test Workshop 2026 (Updated)"

    # 4. Member registers for the event
    member_res = client.post("/api/auth/login", json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD})
    member_token = member_res.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    reg_res = client.post(f"/api/registrations/events/{event_id}", headers=member_headers)
    # Could be 200 or 409 if already registered from earlier test run
    assert reg_res.status_code in [200, 409]

    # 5. Duplicate registration check (must return 409 Conflict)
    duplicate_res = client.post(f"/api/registrations/events/{event_id}", headers=member_headers)
    assert duplicate_res.status_code == 409
    assert "already registered" in duplicate_res.json()["detail"].lower()

# --- 5. HACKATHON CREATION & APPLICATION ---
def test_hackathon_creation_and_registration():
    admin_res = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create hackathon
    create_res = client.post("/api/hackathons", headers=admin_headers, json={
        "title": "Analytix Campus Sprint 2026",
        "organizer": "Analytix Tech Team",
        "description": "24-hour sprint to build data science models.",
        "start_date": "2026-12-01T09:00:00Z",
        "deadline": "2026-11-28T23:59:00Z",
        "location": "Innovation Lab",
        "mode": "hybrid",
        "registration_link": "",
        "eligibility": "Open to all students",
        "required_skills": "Python, SQL",
        "status": "published"
    })
    assert create_res.status_code == 200
    hackathon_id = create_res.json()["id"]

    # Member applies
    member_res = client.post("/api/auth/login", json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD})
    member_token = member_res.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    apply_res = client.post(f"/api/registrations/hackathons/{hackathon_id}", headers=member_headers, json={
        "team_name": "Data Pioneers"
    })
    assert apply_res.status_code in [200, 409]

# --- 6. MEMBER PROFILE EDITING RESTRICTIONS ---
def test_member_profile_update_permissions():
    member_res = client.post("/api/auth/login", json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD})
    member_token = member_res.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    # Member updates safe profile fields
    update_res = client.put("/api/members/me", headers=member_headers, json={
        "full_name": "Priya Nair",
        "phone": "+91 98765 12345",
        "department": "Information Technology",
        "year": "3rd Year",
        "skills": "Figma, UI/UX, CSS, Graphic Design",
        "bio": "Updated bio via test suite."
    })
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["full_name"] == "Priya Nair"
    # Ensure role is still member
    assert data["role"] == "member"

# --- 7. IMAGE UPLOADS VALIDATION ---
def test_poster_upload_validation():
    admin_res = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Valid PNG upload (header magic bytes \x89PNG\r\n\x1a\n)
    valid_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    valid_file = io.BytesIO(valid_png_bytes)
    upload_res = client.post(
        "/api/events/upload-poster",
        headers=admin_headers,
        files={"file": ("test_poster.png", valid_file, "image/png")}
    )
    assert upload_res.status_code == 200
    assert "url" in upload_res.json()
    assert upload_res.json()["url"].startswith("http")

    # 2. Invalid file type rejection (text file disguised as image)
    invalid_file = io.BytesIO(b"This is just plain text, not an image!")
    bad_upload_res = client.post(
        "/api/events/upload-poster",
        headers=admin_headers,
        files={"file": ("fake_image.png", invalid_file, "image/png")}
    )
    assert bad_upload_res.status_code == 400
    assert "valid image format" in bad_upload_res.json()["detail"].lower()

# --- 8. LEADERBOARD & POINTS PERMISSIONS ---
def test_leaderboard_permissions():
    admin_res = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    member_res = client.post("/api/auth/login", json={"email": MEMBER_EMAIL, "password": MEMBER_PASSWORD})
    member_data = member_res.json()["user"]
    member_token = member_res.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    # 1. Admin can award points
    award_res = client.post("/api/admin/leaderboard/award", headers=admin_headers, json={
        "member_id": member_data["id"],
        "points": 25,
        "activity_description": "Active participation in automated verification workshop"
    })
    assert award_res.status_code == 200

    # 2. Member is forbidden from awarding points
    member_award_res = client.post("/api/admin/leaderboard/award", headers=member_headers, json={
        "member_id": member_data["id"],
        "points": 100,
        "activity_description": "Self-awarding points"
    })
    assert member_award_res.status_code == 403

    # 3. Members can view the leaderboard
    lb_res = client.get("/api/members/leaderboard", headers=member_headers)
    assert lb_res.status_code == 200
    assert isinstance(lb_res.json(), list)
