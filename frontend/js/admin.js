/**
 * ANALYTIX CLUB - ADMIN DASHBOARD SCRIPT
 * Orchestrates all administrative functions: Overview, Events, Hackathons,
 * Announcements, Members, Registrations, and Leaderboard Points.
 */

let currentAdmin = null;

document.addEventListener('DOMContentLoaded', async () => {
  // Enforce Admin Authentication
  currentAdmin = await Auth.requireAdmin();
  if (!currentAdmin) return;

  setupNavigation();
  loadOverview();

  // Mobile sidebar toggle
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.dashboard-sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
});

/**
 * Handle sidebar tab switching
 */
function setupNavigation() {
  const links = document.querySelectorAll('.sidebar-link[data-tab]');
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const tabName = link.getAttribute('data-tab');
      switchTab(tabName);
    });
  });
}

function switchTab(tabName) {
  // Update sidebar active link
  document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
  const activeLink = document.querySelector(`.sidebar-link[data-tab="${tabName}"]`);
  if (activeLink) activeLink.classList.add('active');

  // Update content section
  document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
  const activeSection = document.getElementById(`section-${tabName}`);
  if (activeSection) activeSection.classList.add('active');

  // Update topbar title
  const titleMap = {
    overview: 'Admin Overview',
    events: 'Manage Club Events',
    hackathons: 'Manage Hackathons',
    announcements: 'Manage Announcements',
    members: 'Manage Club Members',
    registrations: 'Event Registrations',
    leaderboard: 'Club Leaderboard',
    profile: 'Admin Profile'
  };
  const topbarTitle = document.getElementById('dashboard-title');
  if (topbarTitle) topbarTitle.textContent = titleMap[tabName] || 'Admin Dashboard';

  // Close mobile sidebar if open
  const sidebar = document.querySelector('.dashboard-sidebar');
  if (sidebar) sidebar.classList.remove('open');

  // Load section-specific data
  if (tabName === 'overview') loadOverview();
  else if (tabName === 'events') loadEvents();
  else if (tabName === 'hackathons') loadHackathons();
  else if (tabName === 'announcements') loadAnnouncements();
  else if (tabName === 'members') loadMembers();
  else if (tabName === 'registrations') loadRegistrations();
  else if (tabName === 'leaderboard') loadLeaderboard();
  else if (tabName === 'profile') loadAdminProfile();
}

/**
 * 1. OVERVIEW
 */
async function loadOverview() {
  try {
    const stats = await API.get('/api/admin/overview');
    document.getElementById('stat-members').textContent = stats.total_members;
    document.getElementById('stat-events').textContent = stats.total_events;
    document.getElementById('stat-hackathons').textContent = stats.upcoming_hackathons;
    document.getElementById('stat-registrations').textContent = stats.total_event_registrations;

    // Render recent activities
    const activityList = document.getElementById('recent-activity-list');
    if (activityList) {
      if (!stats.recent_activities || stats.recent_activities.length === 0) {
        activityList.innerHTML = `<li class="activity-item"><div class="activity-text">No recent club activities recorded yet.</div></li>`;
      } else {
        activityList.innerHTML = stats.recent_activities.map(act => `
          <li class="activity-item">
            <div class="activity-badge ${act.type === 'award' ? 'activity-badge-award' : 'activity-badge-reg'}">
              ${act.type === 'award' ? '⭐' : '📅'}
            </div>
            <div class="activity-content">
              <div class="activity-text">${act.message}</div>
              <div class="activity-time">${API.formatDateTime(act.timestamp)}</div>
            </div>
          </li>
        `).join('');
      }
    }
  } catch (err) {
    API.toast('Failed to load overview statistics', 'error');
  }
}

/**
 * 2. MANAGE EVENTS
 */
async function loadEvents() {
  const container = document.getElementById('events-table-body');
  if (!container) return;
  container.innerHTML = `<tr><td colspan="6" class="text-center">Loading events...</td></tr>`;

  try {
    const events = await API.get('/api/events');
    if (!events.length) {
      container.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 30px;">No events created yet. Click "Add New Event" to get started!</td></tr>`;
      return;
    }

    container.innerHTML = events.map(ev => `
      <tr>
        <td>
          <div style="display: flex; align-items: center; gap: 12px;">
            <img src="${ev.poster_url || 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=100'}" 
                 style="width: 48px; height: 36px; object-fit: cover; border-radius: 4px;" alt="Poster"
                 onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=100';">
            <div>
              <strong>${API.escapeHtml(ev.title)}</strong>
              <div style="font-size: 0.8rem; color: #64748b;">${API.escapeHtml(ev.venue)}</div>
            </div>
          </div>
        </td>
        <td>${API.formatDateTime(ev.event_date)}</td>
        <td>${API.formatDate(ev.registration_deadline)}</td>
        <td><span class="status-pill status-${API.escapeHtml(ev.status)}">${API.escapeHtml(ev.status)}</span></td>
        <td>
          <button onclick="viewEventRegistrations('${ev.id}', '${escapeQuotes(ev.title)}')" class="btn-table btn-table-primary">
            👥 ${ev.registrations_count || 0} registered
          </button>
        </td>
        <td>
          <div class="table-actions">
            <button onclick="editEvent('${ev.id}')" class="btn-table">✏️ Edit</button>
            <button onclick="deleteEvent('${ev.id}', '${escapeQuotes(ev.title)}')" class="btn-table btn-table-danger">🗑️</button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="6" class="text-center" style="color: red;">Failed to load events.</td></tr>`;
  }
}

function openAddEventModal() {
  document.getElementById('event-modal-title').textContent = 'Add New Club Event';
  document.getElementById('event-form').reset();
  document.getElementById('event-id').value = '';
  document.getElementById('event-poster-preview').src = '';
  document.getElementById('event-poster-preview').style.display = 'none';
  document.getElementById('event-modal').classList.add('active');
}

async function editEvent(eventId) {
  try {
    const ev = await API.get(`/api/events/${eventId}`);
    document.getElementById('event-modal-title').textContent = 'Edit Club Event';
    document.getElementById('event-id').value = ev.id;
    document.getElementById('event-title').value = ev.title;
    document.getElementById('event-description').value = ev.description;
    document.getElementById('event-venue').value = ev.venue;
    document.getElementById('event-instructions').value = ev.instructions || '';
    document.getElementById('event-status').value = ev.status;
    document.getElementById('event-poster-url').value = ev.poster_url || '';

    // Format ISO string to datetime-local input (YYYY-MM-DDTHH:MM)
    if (ev.event_date) {
      document.getElementById('event-date').value = ev.event_date.slice(0, 16);
    }
    if (ev.registration_deadline) {
      document.getElementById('event-deadline').value = ev.registration_deadline.slice(0, 16);
    }

    if (ev.poster_url) {
      const preview = document.getElementById('event-poster-preview');
      preview.src = ev.poster_url;
      preview.style.display = 'block';
    }

    document.getElementById('event-modal').classList.add('active');
  } catch (e) {
    API.toast('Could not load event details', 'error');
  }
}

async function handleEventFormSubmit(e) {
  e.preventDefault();
  const eventId = document.getElementById('event-id').value;
  const posterFile = document.getElementById('event-poster-file').files[0];
  let posterUrl = document.getElementById('event-poster-url').value;

  // If new poster file selected, upload first
  if (posterFile) {
    try {
      const formData = new FormData();
      formData.append('file', posterFile);
      const uploadRes = await API.upload('/api/events/upload-poster', formData);
      posterUrl = uploadRes.url;
    } catch (uploadErr) {
      API.toast('Poster upload failed: ' + uploadErr.message, 'error');
      return;
    }
  }

  const payload = {
    title: document.getElementById('event-title').value.trim(),
    description: document.getElementById('event-description').value.trim(),
    venue: document.getElementById('event-venue').value.trim(),
    event_date: new Date(document.getElementById('event-date').value).toISOString(),
    registration_deadline: new Date(document.getElementById('event-deadline').value).toISOString(),
    instructions: document.getElementById('event-instructions').value.trim(),
    status: document.getElementById('event-status').value,
    poster_url: posterUrl
  };

  try {
    if (eventId) {
      await API.put(`/api/events/${eventId}`, payload);
      API.toast('Event updated successfully', 'success');
    } else {
      await API.post('/api/events', payload);
      API.toast('Event created and published', 'success');
    }
    closeModal('event-modal');
    loadEvents();
    loadOverview();
  } catch (err) {
    API.toast(err.message, 'error');
  }
}

async function deleteEvent(eventId, title) {
  if (!confirm(`Are you sure you want to delete the event "${title}"? This cannot be undone.`)) return;

  try {
    await API.delete(`/api/events/${eventId}`);
    API.toast('Event deleted successfully', 'success');
    loadEvents();
    loadOverview();
  } catch (err) {
    API.toast('Failed to delete event: ' + err.message, 'error');
  }
}

async function viewEventRegistrations(eventId, eventTitle) {
  const modal = document.getElementById('event-registrations-modal');
  const titleEl = document.getElementById('event-registrations-title');
  const listEl = document.getElementById('event-registrations-list');

  titleEl.textContent = `Registrations: ${eventTitle}`;
  listEl.innerHTML = `<tr><td colspan="5" class="text-center">Loading registrations...</td></tr>`;
  modal.classList.add('active');

  try {
    const regs = await API.get(`/api/events/${eventId}/registrations`);
    if (!regs.length) {
      listEl.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 24px;">No members have registered for this event yet.</td></tr>`;
      return;
    }

    listEl.innerHTML = regs.map((r, i) => `
      <tr>
        <td>${i + 1}</td>
        <td><strong>${r.member ? r.member.full_name : 'Unknown Member'}</strong></td>
        <td>${r.member ? r.member.email : 'N/A'}</td>
        <td>${API.formatDateTime(r.registered_at)}</td>
        <td>
          <select onchange="updateRegStatus('${r.id}', this.value)" class="team-select-pill">
            <option value="pending" ${r.status === 'pending' ? 'selected' : ''}>Pending</option>
            <option value="approved" ${r.status === 'approved' ? 'selected' : ''}>Approved</option>
            <option value="attended" ${r.status === 'attended' ? 'selected' : ''}>Attended</option>
            <option value="rejected" ${r.status === 'rejected' ? 'selected' : ''}>Rejected</option>
          </select>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    listEl.innerHTML = `<tr><td colspan="5" class="text-center" style="color: red;">Failed to load registrations.</td></tr>`;
  }
}

/**
 * 3. MANAGE HACKATHONS
 */
async function loadHackathons() {
  const container = document.getElementById('hackathons-table-body');
  if (!container) return;
  container.innerHTML = `<tr><td colspan="6" class="text-center">Loading hackathons...</td></tr>`;

  try {
    const hackathons = await API.get('/api/hackathons');
    if (!hackathons.length) {
      container.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 30px;">No hackathons listed. Click "Add Hackathon" to add one!</td></tr>`;
      return;
    }

    container.innerHTML = hackathons.map(h => `
      <tr>
        <td>
          <strong>${API.escapeHtml(h.title)}</strong>
          <div style="font-size: 0.8rem; color: #64748b;">Org: ${API.escapeHtml(h.organizer)}</div>
        </td>
        <td><span class="event-badge badge-${API.escapeHtml(h.mode)}" style="position: static;">${API.escapeHtml(h.mode)}</span></td>
        <td>${API.formatDate(h.start_date)}</td>
        <td>${API.formatDate(h.deadline)}</td>
        <td><span class="status-pill status-${API.escapeHtml(h.status)}">${API.escapeHtml(h.status)}</span></td>
        <td>
          <div class="table-actions">
            <button onclick="editHackathon('${h.id}')" class="btn-table">✏️ Edit</button>
            <button onclick="deleteHackathon('${h.id}', '${escapeQuotes(h.title)}')" class="btn-table btn-table-danger">🗑️</button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="6" class="text-center" style="color: red;">Failed to load hackathons.</td></tr>`;
  }
}

function openAddHackathonModal() {
  document.getElementById('hackathon-modal-title').textContent = 'Add New Hackathon';
  document.getElementById('hackathon-form').reset();
  document.getElementById('hackathon-id').value = '';
  document.getElementById('hackathon-modal').classList.add('active');
}

async function editHackathon(hId) {
  try {
    const h = await API.get(`/api/hackathons/${hId}`);
    document.getElementById('hackathon-modal-title').textContent = 'Edit Hackathon';
    document.getElementById('hackathon-id').value = h.id;
    document.getElementById('hackathon-title').value = h.title;
    document.getElementById('hackathon-organizer').value = h.organizer;
    document.getElementById('hackathon-description').value = h.description;
    document.getElementById('hackathon-location').value = h.location;
    document.getElementById('hackathon-mode').value = h.mode;
    document.getElementById('hackathon-link').value = h.registration_link || '';
    document.getElementById('hackathon-eligibility').value = h.eligibility || '';
    document.getElementById('hackathon-skills').value = h.required_skills || '';
    document.getElementById('hackathon-status').value = h.status;
    document.getElementById('hackathon-poster-url').value = h.poster_url || '';

    if (h.start_date) document.getElementById('hackathon-start-date').value = h.start_date.slice(0, 10);
    if (h.deadline) document.getElementById('hackathon-deadline').value = h.deadline.slice(0, 10);

    document.getElementById('hackathon-modal').classList.add('active');
  } catch (err) {
    API.toast('Could not load hackathon', 'error');
  }
}

async function handleHackathonFormSubmit(e) {
  e.preventDefault();
  const hId = document.getElementById('hackathon-id').value;
  const posterFile = document.getElementById('hackathon-poster-file').files[0];
  let posterUrl = document.getElementById('hackathon-poster-url').value;

  if (posterFile) {
    try {
      const formData = new FormData();
      formData.append('file', posterFile);
      const res = await API.upload('/api/hackathons/upload-poster', formData);
      posterUrl = res.url;
    } catch (err) {
      API.toast('Poster upload failed: ' + err.message, 'error');
      return;
    }
  }

  const payload = {
    title: document.getElementById('hackathon-title').value.trim(),
    organizer: document.getElementById('hackathon-organizer').value.trim(),
    description: document.getElementById('hackathon-description').value.trim(),
    location: document.getElementById('hackathon-location').value.trim(),
    mode: document.getElementById('hackathon-mode').value,
    registration_link: document.getElementById('hackathon-link').value.trim(),
    eligibility: document.getElementById('hackathon-eligibility').value.trim(),
    required_skills: document.getElementById('hackathon-skills').value.trim(),
    start_date: new Date(document.getElementById('hackathon-start-date').value).toISOString(),
    deadline: new Date(document.getElementById('hackathon-deadline').value).toISOString(),
    status: document.getElementById('hackathon-status').value,
    poster_url: posterUrl
  };

  try {
    if (hId) {
      await API.put(`/api/hackathons/${hId}`, payload);
      API.toast('Hackathon updated', 'success');
    } else {
      await API.post('/api/hackathons', payload);
      API.toast('Hackathon created', 'success');
    }
    closeModal('hackathon-modal');
    loadHackathons();
  } catch (err) {
    API.toast(err.message, 'error');
  }
}

async function deleteHackathon(hId, title) {
  if (!confirm(`Are you sure you want to delete "${title}"?`)) return;
  try {
    await API.delete(`/api/hackathons/${hId}`);
    API.toast('Hackathon deleted', 'success');
    loadHackathons();
  } catch (err) {
    API.toast(err.message, 'error');
  }
}

/**
 * 4. MANAGE ANNOUNCEMENTS
 */
async function loadAnnouncements() {
  const container = document.getElementById('announcements-table-body');
  if (!container) return;
  container.innerHTML = `<tr><td colspan="5" class="text-center">Loading announcements...</td></tr>`;

  try {
    const announcements = await API.get('/api/announcements');
    if (!announcements.length) {
      container.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 30px;">No announcements posted yet.</td></tr>`;
      return;
    }

    container.innerHTML = announcements.map(a => `
      <tr>
        <td>
          <strong>${API.escapeHtml(a.title)}</strong>
          <div style="font-size: 0.8rem; color: #64748b; max-width: 400px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            ${API.escapeHtml(a.description)}
          </div>
        </td>
        <td><span class="skill-pill">${API.escapeHtml(a.category || 'General')}</span></td>
        <td>${API.formatDate(a.created_at)}</td>
        <td><span class="status-pill status-${API.escapeHtml(a.status)}">${API.escapeHtml(a.status)}</span></td>
        <td>
          <div class="table-actions">
            <button onclick="editAnnouncement('${a.id}')" class="btn-table">✏️ Edit</button>
            <button onclick="deleteAnnouncement('${a.id}')" class="btn-table btn-table-danger">🗑️</button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="5" class="text-center" style="color: red;">Failed to load announcements.</td></tr>`;
  }
}

function openAddAnnouncementModal() {
  document.getElementById('announcement-modal-title').textContent = 'Create Announcement';
  document.getElementById('announcement-form').reset();
  document.getElementById('announcement-id').value = '';
  document.getElementById('announcement-modal').classList.add('active');
}

async function editAnnouncement(aId) {
  try {
    const list = await API.get('/api/announcements');
    const a = list.find(item => item.id === aId);
    if (!a) return;

    document.getElementById('announcement-modal-title').textContent = 'Edit Announcement';
    document.getElementById('announcement-id').value = a.id;
    document.getElementById('announcement-title').value = a.title;
    document.getElementById('announcement-description').value = a.description;
    document.getElementById('announcement-category').value = a.category;
    document.getElementById('announcement-status').value = a.status;
    document.getElementById('announcement-modal').classList.add('active');
  } catch (err) {
    API.toast('Could not load announcement', 'error');
  }
}

async function handleAnnouncementFormSubmit(e) {
  e.preventDefault();
  const aId = document.getElementById('announcement-id').value;
  const imageFile = document.getElementById('announcement-image-file').files[0];
  let imageUrl = '';

  if (imageFile) {
    try {
      const formData = new FormData();
      formData.append('file', imageFile);
      const res = await API.upload('/api/announcements/upload-image', formData);
      imageUrl = res.url;
    } catch (err) {
      API.toast('Image upload failed: ' + err.message, 'error');
      return;
    }
  }

  const payload = {
    title: document.getElementById('announcement-title').value.trim(),
    description: document.getElementById('announcement-description').value.trim(),
    category: document.getElementById('announcement-category').value,
    status: document.getElementById('announcement-status').value,
    image_url: imageUrl
  };

  try {
    if (aId) {
      await API.put(`/api/announcements/${aId}`, payload);
      API.toast('Announcement updated', 'success');
    } else {
      await API.post('/api/announcements', payload);
      API.toast('Announcement published', 'success');
    }
    closeModal('announcement-modal');
    loadAnnouncements();
  } catch (err) {
    API.toast(err.message, 'error');
  }
}

async function deleteAnnouncement(aId) {
  if (!confirm('Are you sure you want to delete this announcement?')) return;
  try {
    await API.delete(`/api/announcements/${aId}`);
    API.toast('Announcement deleted', 'success');
    loadAnnouncements();
  } catch (err) {
    API.toast(err.message, 'error');
  }
}

/**
 * 5. MANAGE MEMBERS
 */
async function loadMembers() {
  const container = document.getElementById('members-table-body');
  if (!container) return;
  const search = document.getElementById('member-search') ? document.getElementById('member-search').value : '';
  const team = document.getElementById('member-team-filter') ? document.getElementById('member-team-filter').value : 'All';

  container.innerHTML = `<tr><td colspan="6" class="text-center">Loading club members...</td></tr>`;

  try {
    const query = new URLSearchParams();
    if (search) query.append('search', search);
    if (team && team !== 'All') query.append('team', team);

    const members = await API.get(`/api/admin/members?${query.toString()}`);
    if (!members.length) {
      container.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 24px;">No members found matching filters.</td></tr>`;
      return;
    }

    container.innerHTML = members.map(m => `
      <tr>
        <td>
          <div style="display: flex; align-items: center; gap: 10px;">
            <div class="user-avatar" style="width: 34px; height: 34px; font-size: 0.85rem;">
              ${m.profile_photo ? `<img src="${m.profile_photo}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" onerror="this.onerror=null;this.textContent='${(m.full_name || 'U').charAt(0)}';">` : (m.full_name || 'U').charAt(0)}
            </div>
            <div>
              <strong>${API.escapeHtml(m.full_name)}</strong>
              <div style="font-size: 0.78rem; color: #64748b;">${API.escapeHtml(m.email)}</div>
            </div>
          </div>
        </td>
        <td>
          <select onchange="updateMemberTeam('${m.id}', this.value)" class="team-select-pill">
            <option value="None" ${m.team === 'None' ? 'selected' : ''}>None</option>
            <option value="Tech" ${m.team === 'Tech' ? 'selected' : ''}>Tech</option>
            <option value="Design" ${m.team === 'Design' ? 'selected' : ''}>Design</option>
            <option value="MOC" ${m.team === 'MOC' ? 'selected' : ''}>MOC</option>
          </select>
        </td>
        <td>
          <span class="points-pill">⭐ ${m.points || 0} pts</span>
        </td>
        <td>
          <select onchange="updateMemberRole('${m.id}', this.value)" class="team-select-pill" style="font-weight: 700; color: ${m.role === 'admin' ? '#dc2626' : '#2563eb'};">
            <option value="member" ${m.role === 'member' ? 'selected' : ''}>Member</option>
            <option value="admin" ${m.role === 'admin' ? 'selected' : ''}>Admin</option>
          </select>
        </td>
        <td>
          <div style="font-size: 0.82rem; color: #64748b;">
            ${API.escapeHtml(m.department || 'General')} (${API.escapeHtml(m.year || 'N/A')})
          </div>
        </td>
        <td>
          <div class="table-actions">
            <button onclick="openAwardModal('${m.id}', '${escapeQuotes(m.full_name)}')" class="btn-table btn-table-primary">
              ⭐ Award
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="6" class="text-center" style="color: red;">Failed to load members.</td></tr>`;
  }
}

async function updateMemberTeam(memberId, newTeam) {
  try {
    await API.patch(`/api/admin/members/${memberId}/team`, { team: newTeam });
    API.toast(`Team updated to ${newTeam}`, 'success');
  } catch (err) {
    API.toast('Failed to update team: ' + err.message, 'error');
    loadMembers();
  }
}

async function updateMemberRole(memberId, newRole) {
  if (!confirm(`Are you sure you want to change this user's role to ${newRole.toUpperCase()}?`)) {
    loadMembers();
    return;
  }

  try {
    await API.patch(`/api/admin/members/${memberId}/role`, { role: newRole });
    API.toast(`Role successfully updated to ${newRole}`, 'success');
    loadMembers();
  } catch (err) {
    API.toast('Failed to update role: ' + err.message, 'error');
    loadMembers();
  }
}

function openAwardModal(memberId, memberName) {
  document.getElementById('award-member-id').value = memberId;
  document.getElementById('award-member-name').textContent = memberName;
  document.getElementById('award-points-input').value = 25;
  document.getElementById('award-desc-input').value = '';
  document.getElementById('award-modal').classList.add('active');
}

async function handleAwardPointsSubmit(e) {
  e.preventDefault();
  const memberId = document.getElementById('award-member-id').value;
  const points = parseInt(document.getElementById('award-points-input').value, 10);
  const desc = document.getElementById('award-desc-input').value.trim();

  if (!points || !desc) {
    API.toast('Please provide valid points and activity description', 'warning');
    return;
  }

  try {
    await API.post('/api/admin/leaderboard/award', {
      member_id: memberId,
      points: points,
      activity_description: desc
    });
    API.toast(`Successfully awarded ${points} points!`, 'success');
    closeModal('award-modal');
    loadMembers();
    loadOverview();
  } catch (err) {
    API.toast('Failed to award points: ' + err.message, 'error');
  }
}

/**
 * 6. REGISTRATIONS
 */
async function loadRegistrations() {
  const container = document.getElementById('all-registrations-table-body');
  if (!container) return;
  container.innerHTML = `<tr><td colspan="5" class="text-center">Loading event registrations...</td></tr>`;

  try {
    const regs = await API.get('/api/registrations/admin/all');
    if (!regs.length) {
      container.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 24px;">No event registrations yet.</td></tr>`;
      return;
    }

    container.innerHTML = regs.map(r => `
      <tr>
        <td><strong>${r.event ? API.escapeHtml(r.event.title) : 'Event'}</strong></td>
        <td>
          <strong>${r.member ? API.escapeHtml(r.member.full_name) : 'Member'}</strong>
          <div style="font-size: 0.78rem; color: #64748b;">${r.member ? API.escapeHtml(r.member.email) : ''}</div>
        </td>
        <td>${API.formatDateTime(r.registered_at)}</td>
        <td><span class="status-pill status-${API.escapeHtml(r.status)}">${API.escapeHtml(r.status)}</span></td>
        <td>
          <select onchange="updateRegStatus('${r.id}', this.value)" class="team-select-pill">
            <option value="pending" ${r.status === 'pending' ? 'selected' : ''}>Pending</option>
            <option value="approved" ${r.status === 'approved' ? 'selected' : ''}>Approved</option>
            <option value="attended" ${r.status === 'attended' ? 'selected' : ''}>Attended</option>
            <option value="rejected" ${r.status === 'rejected' ? 'selected' : ''}>Rejected</option>
          </select>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="5" class="text-center" style="color: red;">Failed to load registrations.</td></tr>`;
  }
}

async function updateRegStatus(regId, newStatus) {
  try {
    await API.patch(`/api/registrations/events/${regId}/status`, { status: newStatus });
    API.toast(`Registration status updated to ${newStatus}`, 'success');
  } catch (err) {
    API.toast('Status update failed: ' + err.message, 'error');
  }
}

/**
 * 7. LEADERBOARD
 */
async function loadLeaderboard() {
  const container = document.getElementById('leaderboard-table-body');
  if (!container) return;
  container.innerHTML = `<tr><td colspan="6" class="text-center">Loading leaderboard...</td></tr>`;

  try {
    const leaderboard = await API.get('/api/members/leaderboard');
    if (!leaderboard.length) {
      container.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 24px;">No points recorded yet.</td></tr>`;
      return;
    }

    container.innerHTML = leaderboard.map(item => `
      <tr>
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
            <strong>${item.full_name}</strong>
          </div>
        </td>
        <td><span class="skill-pill">${item.team || 'None'}</span></td>
        <td><span class="points-pill">⭐ ${item.total_points}</span></td>
        <td>${item.activities_count} activities</td>
        <td>
          <button onclick="openAwardModal('${item.member_id}', '${escapeQuotes(item.full_name)}')" class="btn-table btn-table-primary">
            + Award Points
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="6" class="text-center" style="color: red;">Failed to load leaderboard.</td></tr>`;
  }
}

/**
 * 8. ADMIN PROFILE
 */
function loadAdminProfile() {
  if (!currentAdmin) return;
  document.getElementById('admin-profile-name').value = currentAdmin.full_name || '';
  document.getElementById('admin-profile-email').value = currentAdmin.email || '';
  document.getElementById('admin-profile-phone').value = currentAdmin.phone || '';
  document.getElementById('admin-profile-dept').value = currentAdmin.department || '';
  document.getElementById('admin-profile-year').value = currentAdmin.year || '';
  document.getElementById('admin-profile-skills').value = currentAdmin.skills || '';
  document.getElementById('admin-profile-bio').value = currentAdmin.bio || '';
  document.getElementById('admin-profile-photo').value = currentAdmin.profile_photo || '';

  const badgeTeam = document.getElementById('admin-badge-team');
  if (badgeTeam) badgeTeam.textContent = `TEAM: ${(currentAdmin.team || 'Tech').toUpperCase()}`;

  const headerName = document.getElementById('admin-header-name');
  if (headerName) headerName.textContent = currentAdmin.full_name;

  const headerEmail = document.getElementById('admin-header-email');
  if (headerEmail) headerEmail.textContent = currentAdmin.email;

  const avatarCircle = document.getElementById('admin-avatar-circle');
  if (avatarCircle) {
    if (currentAdmin.profile_photo) {
      avatarCircle.innerHTML = `<img src="${currentAdmin.profile_photo}" alt="Avatar">`;
    } else {
      avatarCircle.textContent = (currentAdmin.full_name || 'A').charAt(0).toUpperCase();
    }
  }
}

async function handleAdminProfileSubmit(e) {
  e.preventDefault();
  const payload = {
    full_name: document.getElementById('admin-profile-name').value.trim(),
    phone: document.getElementById('admin-profile-phone').value.trim(),
    department: document.getElementById('admin-profile-dept').value.trim(),
    year: document.getElementById('admin-profile-year').value.trim(),
    skills: document.getElementById('admin-profile-skills').value.trim(),
    bio: document.getElementById('admin-profile-bio').value.trim(),
    profile_photo: document.getElementById('admin-profile-photo').value.trim()
  };

  try {
    const updated = await API.put('/api/members/me', payload);
    currentAdmin = updated;
    Auth.updateNavbarUser(updated);
    loadAdminProfile();
    API.toast('Profile updated successfully!', 'success');
  } catch (err) {
    API.toast('Update failed: ' + err.message, 'error');
  }
}

/**
 * Modal Helpers
 */
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

function escapeQuotes(str) {
  return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

