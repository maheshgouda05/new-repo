/**
 * ANALYTIX CLUB - MEMBER DASHBOARD SCRIPT
 * Manages member view: dashboard metrics, upcoming events,
 * my registrations, club hackathons, announcements, and leaderboard.
 */

let currentMember = null;

document.addEventListener('DOMContentLoaded', async () => {
  currentMember = await Auth.requireAuth();
  if (!currentMember) return;

  setupMemberNavigation();
  loadMemberDashboard();

  // Mobile sidebar toggle
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.dashboard-sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
});

function setupMemberNavigation() {
  const links = document.querySelectorAll('.sidebar-link[data-tab]');
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const tabName = link.getAttribute('data-tab');
      switchMemberTab(tabName);
    });
  });
}

function switchMemberTab(tabName) {
  document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
  const activeLink = document.querySelector(`.sidebar-link[data-tab="${tabName}"]`);
  if (activeLink) activeLink.classList.add('active');

  document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
  const activeSection = document.getElementById(`section-${tabName}`);
  if (activeSection) activeSection.classList.add('active');

  const titleMap = {
    overview: 'Member Dashboard',
    events: 'Club Events',
    hackathons: 'Hackathons & Competitions',
    announcements: 'Announcements & Notices',
    registrations: 'My Registrations',
    leaderboard: 'Club Leaderboard',
    profile: 'My Profile'
  };
  const topbarTitle = document.getElementById('dashboard-title');
  if (topbarTitle) topbarTitle.textContent = titleMap[tabName] || 'Member Dashboard';

  const sidebar = document.querySelector('.dashboard-sidebar');
  if (sidebar) sidebar.classList.remove('open');

  if (tabName === 'overview') loadMemberDashboard();
  else if (tabName === 'events') loadMemberEvents();
  else if (tabName === 'hackathons') loadMemberHackathons();
  else if (tabName === 'announcements') loadMemberAnnouncements();
  else if (tabName === 'registrations') loadMyRegistrations();
  else if (tabName === 'leaderboard') loadMemberLeaderboard();
  else if (tabName === 'profile') loadMemberProfileForm();
}

/**
 * 1. MEMBER DASHBOARD OVERVIEW
 */
async function loadMemberDashboard() {
  try {
    const data = await API.get('/api/members/overview');
    
    // Greeting
    const welcomeName = document.getElementById('member-welcome-name');
    if (welcomeName) welcomeName.textContent = data.member.full_name;

    // Stat cards (if present)
    const pointsEl = document.getElementById('member-points-stat');
    if (pointsEl) pointsEl.textContent = data.total_points;
    const rankEl = document.getElementById('member-rank-stat');
    if (rankEl) rankEl.textContent = `#${data.rank}`;
    const teamEl = document.getElementById('member-team-stat');
    if (teamEl) teamEl.textContent = data.team || 'None';
    const eventsEl = document.getElementById('member-events-stat');
    if (eventsEl) eventsEl.textContent = data.registered_events_count;

    // Upcoming events preview
    const eventsContainer = document.getElementById('member-upcoming-events');
    if (eventsContainer) {
      if (!data.upcoming_events || !data.upcoming_events.length) {
        eventsContainer.innerHTML = `<p style="color: #64748b; padding: 12px 0;">No upcoming club events scheduled right now. Check back soon!</p>`;
      } else {
        eventsContainer.innerHTML = data.upcoming_events.map(ev => `
          <div class="event-card" style="box-shadow: none; border: 1px solid #e2e8f0;">
            <div class="event-poster-wrapper" style="height: 120px;">
              <img src="${ev.poster_url || 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400'}" class="event-poster" alt="Poster">
            </div>
            <div class="event-content" style="padding: 16px;">
              <div class="event-meta" style="margin-bottom: 6px; font-size: 0.8rem;">
                <span>📅 ${API.formatDate(ev.event_date)}</span>
                <span>📍 ${ev.venue}</span>
              </div>
              <h4 style="font-size: 1.05rem; margin-bottom: 12px;">${ev.title}</h4>
              <div class="event-footer" style="padding-top: 10px;">
                ${ev.is_registered 
                  ? `<span class="status-pill status-approved">Registered (${ev.my_registration_status})</span>`
                  : `<button onclick="registerForEvent('${ev.id}')" class="btn btn-primary btn-sm">Register</button>`
                }
              </div>
            </div>
          </div>
        `).join('');
      }
    }

    // Latest Announcements preview
    const noticesContainer = document.getElementById('member-latest-notices');
    if (noticesContainer) {
      if (!data.latest_announcements || !data.latest_announcements.length) {
        noticesContainer.innerHTML = `<p style="color: #64748b; padding: 12px 0;">No new notices.</p>`;
      } else {
        noticesContainer.innerHTML = data.latest_announcements.map(a => `
          <div class="announcement-card" style="padding: 16px; margin-bottom: 12px; box-shadow: none;">
            <div class="announcement-icon" style="width: 38px; height: 38px; font-size: 1.1rem;">📢</div>
            <div class="announcement-body">
              <div class="announcement-header">
                <strong style="font-size: 0.98rem;">${a.title}</strong>
                <span class="announcement-time">${API.formatDate(a.created_at)}</span>
              </div>
              <p style="font-size: 0.88rem; color: #64748b; margin-top: 4px;">${a.description}</p>
            </div>
          </div>
        `).join('');
      }
    }

  } catch (err) {
    API.toast('Failed to load member dashboard', 'error');
  }
}

/**
 * 2. EVENTS
 */
async function loadMemberEvents() {
  const container = document.getElementById('member-events-grid');
  if (!container) return;
  container.innerHTML = `<p class="text-center" style="grid-column: 1/-1; padding: 30px;">Loading events...</p>`;

  try {
    const events = await API.get('/api/events');
    if (!events.length) {
      container.innerHTML = `<p class="text-center" style="grid-column: 1/-1; padding: 30px;">No events published at the moment.</p>`;
      return;
    }

    container.innerHTML = events.map(ev => `
      <div class="event-card">
        <div class="event-poster-wrapper">
          <img src="${ev.poster_url || 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600'}" class="event-poster" alt="Poster">
          <span class="event-badge badge-published">${ev.status}</span>
        </div>
        <div class="event-content">
          <div class="event-meta">
            <span>📅 ${API.formatDate(ev.event_date)}</span>
            <span>📍 ${ev.venue}</span>
          </div>
          <h3 class="event-title">${ev.title}</h3>
          <p class="event-desc">${ev.description}</p>
          ${ev.instructions ? `<div style="background: #f8fafc; border: 1px dashed #cbd5e1; padding: 8px 12px; border-radius: 6px; font-size: 0.82rem; margin-bottom: 16px; color: #475569;"><strong>Instructions:</strong> ${ev.instructions}</div>` : ''}
          <div class="event-footer">
            <span style="font-size: 0.82rem; color: #64748b;">Deadline: ${API.formatDate(ev.registration_deadline)}</span>
            ${ev.is_registered
              ? `<span class="status-pill status-${ev.my_registration_status || 'approved'}">Registered (${ev.my_registration_status || 'pending'})</span>`
              : `<button onclick="registerForEvent('${ev.id}')" class="btn btn-primary btn-sm">Register Now</button>`
            }
          </div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<p style="color: red; text-align: center; grid-column: 1/-1;">Failed to load events.</p>`;
  }
}

async function registerForEvent(eventId) {
  try {
    await API.post(`/api/registrations/events/${eventId}`, {});
    API.toast('Successfully registered for event!', 'success');
    loadMemberEvents();
    loadMemberDashboard();
  } catch (err) {
    API.toast(err.message, 'warning');
  }
}

/**
 * 3. HACKATHONS
 */
async function loadMemberHackathons() {
  const container = document.getElementById('member-hackathons-grid');
  if (!container) return;
  container.innerHTML = `<p class="text-center" style="grid-column: 1/-1; padding: 30px;">Loading hackathons...</p>`;

  try {
    const hackathons = await API.get('/api/hackathons');
    if (!hackathons.length) {
      container.innerHTML = `<p class="text-center" style="grid-column: 1/-1; padding: 30px;">No hackathons listed at this moment.</p>`;
      return;
    }

    container.innerHTML = hackathons.map(h => `
      <div class="event-card">
        <div class="event-poster-wrapper">
          <img src="${h.poster_url || 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=600'}" class="event-poster" alt="Poster">
          <span class="event-badge badge-${h.mode}">${h.mode}</span>
        </div>
        <div class="event-content">
          <div class="event-meta">
            <span>📅 Starts: ${API.formatDate(h.start_date)}</span>
            <span>📍 ${h.location}</span>
          </div>
          <h3 class="event-title">${h.title}</h3>
          <div style="font-size: 0.85rem; font-weight: 600; color: var(--primary); margin-bottom: 8px;">Organized by ${h.organizer}</div>
          <p class="event-desc">${h.description}</p>
          
          <div style="margin-bottom: 16px; font-size: 0.82rem; color: #64748b;">
            <div><strong>Eligibility:</strong> ${h.eligibility}</div>
            ${h.required_skills ? `<div><strong>Skills:</strong> ${h.required_skills}</div>` : ''}
          </div>

          <div class="event-footer">
            <span style="font-size: 0.82rem; color: #64748b;">Deadline: ${API.formatDate(h.deadline)}</span>
            <div style="display: flex; gap: 8px;">
              ${h.registration_link ? `<a href="${h.registration_link}" target="_blank" class="btn btn-secondary btn-sm">External Link ↗</a>` : ''}
              ${h.is_registered 
                ? `<span class="status-pill status-approved">Applied</span>`
                : `<button onclick="applyForHackathon('${h.id}')" class="btn btn-primary btn-sm">Apply Club Team</button>`
              }
            </div>
          </div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<p style="color: red; text-align: center; grid-column: 1/-1;">Failed to load hackathons.</p>`;
  }
}

async function applyForHackathon(hackathonId) {
  const teamName = prompt('Enter your team name (or leave blank for individual):', 'Analytix Innovators');
  if (teamName === null) return;

  try {
    await API.post(`/api/registrations/hackathons/${hackathonId}`, { team_name: teamName });
    API.toast('Hackathon application submitted!', 'success');
    loadMemberHackathons();
  } catch (err) {
    API.toast(err.message, 'warning');
  }
}

/**
 * 4. ANNOUNCEMENTS
 */
async function loadMemberAnnouncements() {
  const container = document.getElementById('member-announcements-list');
  if (!container) return;
  container.innerHTML = `<p class="text-center" style="padding: 24px;">Loading announcements...</p>`;

  try {
    const list = await API.get('/api/announcements');
    if (!list.length) {
      container.innerHTML = `<p class="text-center" style="padding: 24px;">No announcements posted.</p>`;
      return;
    }

    container.innerHTML = list.map(a => `
      <div class="announcement-card" style="margin-bottom: 16px;">
        <div class="announcement-icon">📢</div>
        <div class="announcement-body">
          <div class="announcement-header">
            <div>
              <strong style="font-size: 1.15rem;">${a.title}</strong>
              <span class="skill-pill" style="margin-left: 10px;">${a.category || 'General'}</span>
            </div>
            <span class="announcement-time">${API.formatDate(a.created_at)}</span>
          </div>
          <p class="announcement-desc" style="margin-top: 8px;">${a.description}</p>
          ${a.image_url ? `<img src="${a.image_url}" style="max-width: 320px; border-radius: 8px; margin-top: 12px;" alt="Notice Image">` : ''}
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<p style="color: red; text-align: center;">Failed to load announcements.</p>`;
  }
}

/**
 * 5. MY REGISTRATIONS
 */
async function loadMyRegistrations() {
  const eventTable = document.getElementById('my-events-table-body');
  const hackTable = document.getElementById('my-hackathons-table-body');

  if (eventTable) eventTable.innerHTML = `<tr><td colspan="4" class="text-center">Loading registrations...</td></tr>`;
  if (hackTable) hackTable.innerHTML = `<tr><td colspan="4" class="text-center">Loading hackathons...</td></tr>`;

  try {
    const data = await API.get('/api/registrations/my');
    
    // Events
    if (eventTable) {
      if (!data.events.length) {
        eventTable.innerHTML = `<tr><td colspan="4" class="text-center" style="padding: 24px;">You haven't registered for any events yet.</td></tr>`;
      } else {
        eventTable.innerHTML = data.events.map(r => `
          <tr>
            <td><strong>${r.event ? r.event.title : 'Event'}</strong></td>
            <td>${r.event ? API.formatDateTime(r.event.event_date) : 'N/A'}</td>
            <td>${API.formatDate(r.registered_at)}</td>
            <td><span class="status-pill status-${r.status}">${r.status}</span></td>
          </tr>
        `).join('');
      }
    }

    // Hackathons
    if (hackTable) {
      if (!data.hackathons.length) {
        hackTable.innerHTML = `<tr><td colspan="4" class="text-center" style="padding: 24px;">You haven't applied for any hackathons yet.</td></tr>`;
      } else {
        hackTable.innerHTML = data.hackathons.map(h => `
          <tr>
            <td><strong>${h.hackathon ? h.hackathon.title : 'Hackathon'}</strong></td>
            <td>${h.team_name || 'Individual'}</td>
            <td>${API.formatDate(h.registered_at)}</td>
            <td><span class="status-pill status-approved">${h.status}</span></td>
          </tr>
        `).join('');
      }
    }

  } catch (err) {
    API.toast('Failed to load my registrations', 'error');
  }
}

/**
 * 6. LEADERBOARD
 */
async function loadMemberLeaderboard() {
  const container = document.getElementById('member-leaderboard-body');
  if (!container) return;
  container.innerHTML = `<tr><td colspan="5" class="text-center">Loading leaderboard...</td></tr>`;

  try {
    const leaderboard = await API.get('/api/members/leaderboard');
    if (!leaderboard.length) {
      container.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 24px;">No members ranked yet.</td></tr>`;
      return;
    }

    container.innerHTML = leaderboard.map(item => `
      <tr style="${item.member_id === currentMember.id ? 'background-color: #f0fdf4;' : ''}">
        <td>
          <strong style="font-size: 1.1rem; color: ${item.rank === 1 ? '#d97706' : item.rank === 2 ? '#64748b' : item.rank === 3 ? '#b45309' : '#0f172a'};">
            #${item.rank}
          </strong>
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 10px;">
            <div class="user-avatar" style="width: 32px; height: 32px; font-size: 0.8rem;">
              ${item.profile_photo ? `<img src="${item.profile_photo}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">` : (item.full_name || 'U').charAt(0)}
            </div>
            <div>
              <strong>${item.full_name}</strong>
              ${item.member_id === currentMember.id ? `<span class="skill-pill" style="margin-left: 6px; background: #bbf7d0; color: #166534;">You</span>` : ''}
            </div>
          </div>
        </td>
        <td><span class="skill-pill">${item.team || 'None'}</span></td>
        <td><span class="points-pill">⭐ ${item.total_points}</span></td>
        <td>${item.activities_count} activities</td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="5" class="text-center" style="color: red;">Failed to load leaderboard.</td></tr>`;
  }
}

/**
 * 7. MEMBER PROFILE
 */
function loadMemberProfileForm() {
  if (!currentMember) return;
  document.getElementById('member-profile-name').value = currentMember.full_name || '';
  document.getElementById('member-profile-email').value = currentMember.email || '';
  document.getElementById('member-profile-phone').value = currentMember.phone || '';
  document.getElementById('member-profile-dept').value = currentMember.department || '';
  document.getElementById('member-profile-year').value = currentMember.year || '';
  document.getElementById('member-profile-skills').value = currentMember.skills || '';
  document.getElementById('member-profile-bio').value = currentMember.bio || '';
  document.getElementById('member-profile-photo').value = currentMember.profile_photo || '';

  // Read-only badges & Header Strip
  document.getElementById('member-badge-role').textContent = currentMember.role.toUpperCase();
  document.getElementById('member-badge-team').textContent = `TEAM: ${(currentMember.team || 'None').toUpperCase()}`;
  document.getElementById('member-badge-points').textContent = `${currentMember.points || 0} pts`;

  const headerName = document.getElementById('member-header-name');
  if (headerName) headerName.textContent = currentMember.full_name;

  const headerEmail = document.getElementById('member-header-email');
  if (headerEmail) headerEmail.textContent = currentMember.email;

  const avatarCircle = document.getElementById('member-avatar-circle');
  if (avatarCircle) {
    if (currentMember.profile_photo) {
      avatarCircle.innerHTML = `<img src="${currentMember.profile_photo}" alt="Avatar">`;
    } else {
      avatarCircle.textContent = (currentMember.full_name || 'M').charAt(0).toUpperCase();
    }
  }
}

async function handleMemberProfileSubmit(e) {
  e.preventDefault();
  const payload = {
    full_name: document.getElementById('member-profile-name').value.trim(),
    phone: document.getElementById('member-profile-phone').value.trim(),
    department: document.getElementById('member-profile-dept').value.trim(),
    year: document.getElementById('member-profile-year').value.trim(),
    skills: document.getElementById('member-profile-skills').value.trim(),
    bio: document.getElementById('member-profile-bio').value.trim(),
    profile_photo: document.getElementById('member-profile-photo').value.trim()
  };

  try {
    const updated = await API.put('/api/members/me', payload);
    currentMember = updated;
    API.setUser(updated);
    Auth.updateNavbarUser(updated);
    loadMemberProfileForm();
    API.toast('Profile updated successfully!', 'success');
  } catch (err) {
    API.toast('Update failed: ' + err.message, 'error');
  }
}

