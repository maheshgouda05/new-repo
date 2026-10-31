/**
 * ANALYTIX CLUB - PUBLIC & MEMBER EVENTS / HACKATHONS / ANNOUNCEMENTS CONTROLLER
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Check optional logged in user to update navbar and registration buttons
  let currentUser = null;
  const token = API.getToken();
  if (token) {
    try {
      currentUser = await API.get('/api/auth/me');
      Auth.updateNavbarUser(currentUser);
    } catch (e) {
      API.clearAuth();
    }
  }

  // Mobile menu toggle on public pages
  const mobileToggle = document.querySelector('.nav-mobile-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });
  }

  // Detect current page to trigger appropriate load
  const path = window.location.pathname;
  if (path.endsWith('events.html')) {
    loadPublicEvents(currentUser);
  } else if (path.endsWith('hackathons.html')) {
    loadPublicHackathons(currentUser);
  } else if (path.endsWith('announcements.html')) {
    loadPublicAnnouncements();
  } else if (path.endsWith('index.html') || path === '/' || path.endsWith('/')) {
    loadLandingPageData(currentUser);
  }
});

/**
 * Public Events Page
 */
async function loadPublicEvents(currentUser) {
  const container = document.getElementById('events-grid');
  if (!container) return;
  container.innerHTML = `<p class="text-center" style="grid-column: 1/-1; padding: 40px;">Loading events...</p>`;

  try {
    const events = await API.get('/api/events');
    if (!events.length) {
      container.innerHTML = `<p class="text-center" style="grid-column: 1/-1; padding: 40px; color: #64748b;">No events scheduled currently. Please check back later!</p>`;
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
            ${currentUser
              ? (ev.is_registered
                  ? `<span class="status-pill status-${ev.my_registration_status || 'approved'}">Registered (${ev.my_registration_status || 'pending'})</span>`
                  : `<button onclick="handleEventRegister('${ev.id}')" class="btn btn-primary btn-sm">Register</button>`
                )
              : `<a href="login.html" class="btn btn-primary btn-sm">Login to Register</a>`
            }
          </div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<p style="color: red; text-align: center; grid-column: 1/-1;">Failed to load events.</p>`;
  }
}

async function handleEventRegister(eventId) {
  try {
    await API.post(`/api/registrations/events/${eventId}`, {});
    API.toast('Successfully registered for event!', 'success');
    setTimeout(() => window.location.reload(), 600);
  } catch (err) {
    API.toast(err.message, 'warning');
  }
}

/**
 * Public Hackathons Page
 */
async function loadPublicHackathons(currentUser) {
  const container = document.getElementById('hackathons-grid');
  if (!container) return;
  container.innerHTML = `<p class="text-center" style="grid-column: 1/-1; padding: 40px;">Loading hackathons...</p>`;

  try {
    const hackathons = await API.get('/api/hackathons');
    if (!hackathons.length) {
      container.innerHTML = `<p class="text-center" style="grid-column: 1/-1; padding: 40px; color: #64748b;">No hackathons listed currently.</p>`;
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
              ${currentUser
                ? (h.is_registered
                    ? `<span class="status-pill status-approved">Applied</span>`
                    : `<button onclick="handleHackathonApply('${h.id}')" class="btn btn-primary btn-sm">Apply Club Team</button>`
                  )
                : `<a href="login.html" class="btn btn-primary btn-sm">Login to Apply</a>`
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

async function handleHackathonApply(hackathonId) {
  const teamName = prompt('Enter your team name (or leave empty for solo):', 'Analytix Innovators');
  if (teamName === null) return;

  try {
    await API.post(`/api/registrations/hackathons/${hackathonId}`, { team_name: teamName });
    API.toast('Hackathon application submitted successfully!', 'success');
    setTimeout(() => window.location.reload(), 600);
  } catch (err) {
    API.toast(err.message, 'warning');
  }
}

/**
 * Public Announcements Page
 */
async function loadPublicAnnouncements() {
  const container = document.getElementById('announcements-container');
  if (!container) return;
  container.innerHTML = `<p class="text-center" style="padding: 40px;">Loading notices...</p>`;

  try {
    const list = await API.get('/api/announcements');
    if (!list.length) {
      container.innerHTML = `<p class="text-center" style="padding: 40px; color: #64748b;">No announcements at this time.</p>`;
      return;
    }

    container.innerHTML = list.map(a => `
      <div class="announcement-card" style="margin-bottom: 20px;">
        <div class="announcement-icon">📢</div>
        <div class="announcement-body">
          <div class="announcement-header">
            <div>
              <strong style="font-size: 1.2rem;">${a.title}</strong>
              <span class="skill-pill" style="margin-left: 10px;">${a.category || 'General'}</span>
            </div>
            <span class="announcement-time">${API.formatDate(a.created_at)}</span>
          </div>
          <p class="announcement-desc" style="margin-top: 10px; font-size: 0.95rem;">${a.description}</p>
          ${a.image_url ? `<img src="${a.image_url}" style="max-width: 400px; border-radius: 8px; margin-top: 14px;" alt="Notice Image">` : ''}
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<p style="color: red; text-align: center;">Failed to load announcements.</p>`;
  }
}

/**
 * Landing Page Dynamic Sections
 */
async function loadLandingPageData(currentUser) {
  // Load upcoming events snippet
  const eventsBox = document.getElementById('home-events-grid');
  if (eventsBox) {
    try {
      const events = await API.get('/api/events');
      const upcoming = events.slice(0, 3);
      if (upcoming.length) {
        eventsBox.innerHTML = upcoming.map(ev => `
          <div class="event-card">
            <div class="event-poster-wrapper" style="height: 160px;">
              <img src="${ev.poster_url || 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500'}" class="event-poster" alt="Poster">
            </div>
            <div class="event-content" style="padding: 20px;">
              <div class="event-meta" style="font-size: 0.8rem;">
                <span>📅 ${API.formatDate(ev.event_date)}</span>
                <span>📍 ${ev.venue}</span>
              </div>
              <h4 style="font-size: 1.15rem; margin-bottom: 8px;">${ev.title}</h4>
              <p class="event-desc" style="font-size: 0.88rem;">${ev.description}</p>
              <div class="event-footer" style="padding-top: 12px;">
                <a href="events.html" class="btn btn-outline btn-sm">View Details & Register →</a>
              </div>
            </div>
          </div>
        `).join('');
      } else {
        eventsBox.innerHTML = `<p style="color: #64748b; grid-column: 1/-1;">Check back soon for new club events!</p>`;
      }
    } catch (e) {
      console.error(e);
    }
  }

  // Load latest announcements snippet
  const announceBox = document.getElementById('home-announcements-list');
  if (announceBox) {
    try {
      const notices = await API.get('/api/announcements');
      const topNotices = notices.slice(0, 2);
      if (topNotices.length) {
        announceBox.innerHTML = topNotices.map(a => `
          <div class="announcement-card" style="margin-bottom: 16px;">
            <div class="announcement-icon" style="width: 42px; height: 42px; font-size: 1.2rem;">📢</div>
            <div class="announcement-body">
              <div class="announcement-header">
                <strong style="font-size: 1.05rem;">${a.title}</strong>
                <span class="announcement-time">${API.formatDate(a.created_at)}</span>
              </div>
              <p class="announcement-desc" style="margin-top: 6px;">${a.description}</p>
            </div>
          </div>
        `).join('');
      }
    } catch (e) {
      console.error(e);
    }
  }
}

