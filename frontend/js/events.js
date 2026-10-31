/**
 * ANALYTIX CLUB - PUBLIC & MEMBER EVENTS / HACKATHONS / ANNOUNCEMENTS CONTROLLER
 * Hardened with XSS protection, image fallbacks, and real database data.
 */

document.addEventListener('DOMContentLoaded', async () => {
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
  const path = window.location.pathname.toLowerCase();
  if (path.includes('events.html') || path.endsWith('/events')) {
    loadPublicEvents(currentUser);
  } else if (path.includes('hackathons.html') || path.endsWith('/hackathons')) {
    loadPublicHackathons(currentUser);
  } else if (path.includes('announcements.html') || path.endsWith('/announcements')) {
    loadPublicAnnouncements();
  } else if (path.includes('index.html') || path === '/' || path.endsWith('/')) {
    loadLandingPageData(currentUser);
  }
});

/**
 * Public Events Page
 */
async function loadPublicEvents(currentUser) {
  const container = document.getElementById('events-grid');
  if (!container) return;
  container.innerHTML = `<div class="text-center" style="grid-column: 1/-1; padding: 48px; color: #64748b;">
    <div style="font-size: 2rem; margin-bottom: 8px;">⏳</div>
    <p>Loading scheduled club events...</p>
  </div>`;

  try {
    const events = await API.get('/api/events');
    if (!events || !events.length) {
      container.innerHTML = `
        <div class="card-panel" style="grid-column: 1/-1; text-align: center; padding: 48px 24px;">
          <div style="font-size: 2.5rem; margin-bottom: 12px;">📅</div>
          <h3 style="margin-bottom: 8px; color: var(--dark-bg);">No Events Currently Scheduled</h3>
          <p style="color: #64748b; max-width: 480px; margin: 0 auto 20px;">
            The club coordinators are actively organizing upcoming workshops and hackathons. Check back soon or join the club to get notified!
          </p>
          <a href="index.html" class="btn btn-secondary btn-sm">Return Home</a>
        </div>
      `;
      return;
    }

    container.innerHTML = events.map(ev => {
      const cleanTitle = API.escapeHtml(ev.title);
      const cleanDesc = API.escapeHtml(ev.description);
      const cleanVenue = API.escapeHtml(ev.venue);
      const cleanInstructions = API.escapeHtml(ev.instructions || '');
      const posterUrl = ev.poster_url || 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800';

      return `
        <div class="event-card">
          <div class="event-poster-wrapper">
            <img src="${posterUrl}" 
                 class="event-poster" 
                 alt="${cleanTitle}"
                 onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800';">
            <span class="event-badge badge-published">${API.escapeHtml(ev.status)}</span>
          </div>
          <div class="event-content">
            <div class="event-meta">
              <span>📅 ${API.formatDate(ev.event_date)}</span>
              <span>📍 ${cleanVenue}</span>
            </div>
            <h3 class="event-title">${cleanTitle}</h3>
            <p class="event-desc">${cleanDesc}</p>
            ${cleanInstructions ? `<div style="background: #f8fafc; border: 1px dashed #cbd5e1; padding: 10px 14px; border-radius: 6px; font-size: 0.82rem; margin-bottom: 16px; color: #475569;"><strong>Instructions:</strong> ${cleanInstructions}</div>` : ''}
            <div class="event-footer">
              <span style="font-size: 0.82rem; color: #64748b;">Deadline: ${API.formatDate(ev.registration_deadline)}</span>
              ${currentUser
                ? (ev.is_registered
                    ? `<span class="status-pill status-${ev.my_registration_status || 'approved'}">Registered (${API.escapeHtml(ev.my_registration_status || 'pending')})</span>`
                    : `<button onclick="handleEventRegister('${ev.id}')" class="btn btn-primary btn-sm">Register</button>`
                  )
                : `<a href="login.html" class="btn btn-primary btn-sm">Login to Register</a>`
              }
            </div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `
      <div class="card-panel" style="grid-column: 1/-1; text-align: center; padding: 40px; border-color: #fecaca;">
        <p style="color: #ef4444; font-weight: 600; margin-bottom: 8px;">Failed to load events.</p>
        <p style="color: #64748b; font-size: 0.9rem;">${API.escapeHtml(err.message)}</p>
        <button onclick="window.location.reload()" class="btn btn-secondary btn-sm" style="margin-top: 14px;">Retry</button>
      </div>
    `;
  }
}

async function handleEventRegister(eventId) {
  try {
    await API.post(`/api/registrations/events/${eventId}`, {});
    API.toast('Successfully registered for event!', 'success');
    setTimeout(() => window.location.reload(), 600);
  } catch (err) {
    API.toast(err.message || 'Registration failed', 'warning');
  }
}

/**
 * Public Hackathons Page
 */
async function loadPublicHackathons(currentUser) {
  const container = document.getElementById('hackathons-grid');
  if (!container) return;
  container.innerHTML = `<div class="text-center" style="grid-column: 1/-1; padding: 48px; color: #64748b;">
    <div style="font-size: 2rem; margin-bottom: 8px;">⏳</div>
    <p>Loading hackathons & sprints...</p>
  </div>`;

  try {
    const hackathons = await API.get('/api/hackathons');
    if (!hackathons || !hackathons.length) {
      container.innerHTML = `
        <div class="card-panel" style="grid-column: 1/-1; text-align: center; padding: 48px 24px;">
          <div style="font-size: 2.5rem; margin-bottom: 12px;">🚀</div>
          <h3 style="margin-bottom: 8px; color: var(--dark-bg);">No Active Hackathons Listed</h3>
          <p style="color: #64748b; max-width: 480px; margin: 0 auto 20px;">
            External competitions and internal hackathons will be listed here as soon as they open for student participation.
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = hackathons.map(h => {
      const cleanTitle = API.escapeHtml(h.title);
      const cleanOrganizer = API.escapeHtml(h.organizer);
      const cleanDesc = API.escapeHtml(h.description);
      const cleanLocation = API.escapeHtml(h.location);
      const cleanEligibility = API.escapeHtml(h.eligibility);
      const cleanSkills = API.escapeHtml(h.required_skills || '');
      const posterUrl = h.poster_url || 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800';

      return `
        <div class="event-card">
          <div class="event-poster-wrapper">
            <img src="${posterUrl}" 
                 class="event-poster" 
                 alt="${cleanTitle}"
                 onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800';">
            <span class="event-badge badge-${API.escapeHtml(h.mode)}">${API.escapeHtml(h.mode.toUpperCase())}</span>
          </div>
          <div class="event-content">
            <div class="event-meta">
              <span>📅 Starts: ${API.formatDate(h.start_date)}</span>
              <span>📍 ${cleanLocation}</span>
            </div>
            <h3 class="event-title">${cleanTitle}</h3>
            <div style="font-size: 0.85rem; font-weight: 600; color: var(--primary); margin-bottom: 8px;">Organized by ${cleanOrganizer}</div>
            <p class="event-desc">${cleanDesc}</p>
            
            <div style="margin-bottom: 16px; font-size: 0.82rem; color: #64748b;">
              <div><strong>Eligibility:</strong> ${cleanEligibility}</div>
              ${cleanSkills ? `<div><strong>Skills:</strong> ${cleanSkills}</div>` : ''}
            </div>

            <div class="event-footer">
              <span style="font-size: 0.82rem; color: #64748b;">Deadline: ${API.formatDate(h.deadline)}</span>
              <div style="display: flex; gap: 8px;">
                ${h.registration_link ? `<a href="${encodeURI(h.registration_link)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm">Official Link ↗</a>` : ''}
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
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `
      <div class="card-panel" style="grid-column: 1/-1; text-align: center; padding: 40px; border-color: #fecaca;">
        <p style="color: #ef4444; font-weight: 600; margin-bottom: 8px;">Failed to load hackathons.</p>
        <p style="color: #64748b; font-size: 0.9rem;">${API.escapeHtml(err.message)}</p>
      </div>
    `;
  }
}

async function handleHackathonApply(hackathonId) {
  const teamName = prompt('Enter your team or project group name (optional):', 'Analytix Innovators');
  if (teamName === null) return;

  try {
    await API.post(`/api/registrations/hackathons/${hackathonId}`, { team_name: teamName });
    API.toast('Hackathon application submitted successfully!', 'success');
    setTimeout(() => window.location.reload(), 600);
  } catch (err) {
    API.toast(err.message || 'Application failed', 'warning');
  }
}

/**
 * Public Announcements Page
 */
async function loadPublicAnnouncements() {
  const container = document.getElementById('announcements-container');
  if (!container) return;
  container.innerHTML = `<div class="text-center" style="padding: 48px; color: #64748b;">Loading notices...</div>`;

  try {
    const list = await API.get('/api/announcements');
    if (!list || !list.length) {
      container.innerHTML = `
        <div class="card-panel" style="text-align: center; padding: 48px 24px;">
          <div style="font-size: 2.5rem; margin-bottom: 12px;">📢</div>
          <h3 style="margin-bottom: 8px; color: var(--dark-bg);">No Notices at this time</h3>
          <p style="color: #64748b;">Important club notices and updates will be published here.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = list.map(a => {
      const cleanTitle = API.escapeHtml(a.title);
      const cleanCategory = API.escapeHtml(a.category || 'Notice');
      const cleanDesc = API.escapeHtml(a.description);
      const imageUrl = a.image_url;

      return `
        <div class="announcement-card" style="margin-bottom: 20px;">
          <div class="announcement-icon">📢</div>
          <div class="announcement-body">
            <div class="announcement-header">
              <div>
                <strong style="font-size: 1.2rem;">${cleanTitle}</strong>
                <span class="skill-pill" style="margin-left: 10px;">${cleanCategory}</span>
              </div>
              <span class="announcement-time">${API.formatDate(a.created_at)}</span>
            </div>
            <p class="announcement-desc" style="margin-top: 10px; font-size: 0.95rem;">${cleanDesc}</p>
            ${imageUrl ? `<img src="${imageUrl}" style="max-width: 480px; border-radius: 8px; margin-top: 14px; width: 100%; object-fit: cover;" alt="${cleanTitle}" onerror="this.style.display='none'">` : ''}
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<p style="color: #ef4444; text-align: center; padding: 30px;">Failed to load announcements: ${API.escapeHtml(err.message)}</p>`;
  }
}

/**
 * Landing Page Dynamic Sections
 */
async function loadLandingPageData(currentUser) {
  // 1. Load authentic club metrics (no invented numbers)
  try {
    const stats = await API.get('/api/stats');
    const mEl = document.getElementById('stat-members-count');
    if (mEl) mEl.textContent = stats.members_count;
    const eEl = document.getElementById('stat-events-count');
    if (eEl) eEl.textContent = stats.events_count;
    const hEl = document.getElementById('stat-hackathons-count');
    if (hEl) hEl.textContent = stats.hackathons_count;
  } catch (e) {
    console.debug('Stats load error:', e);
  }

  // 2. Load upcoming events snippet
  const eventsBox = document.getElementById('home-events-grid');
  if (eventsBox) {
    try {
      const events = await API.get('/api/events');
      const upcoming = events.slice(0, 3);
      if (upcoming.length) {
        eventsBox.innerHTML = upcoming.map(ev => {
          const cleanTitle = API.escapeHtml(ev.title);
          const cleanDesc = API.escapeHtml(ev.description);
          const cleanVenue = API.escapeHtml(ev.venue);
          const posterUrl = ev.poster_url || 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500';

          return `
            <div class="event-card">
              <div class="event-poster-wrapper" style="height: 160px;">
                <img src="${posterUrl}" 
                     class="event-poster" 
                     alt="${cleanTitle}"
                     onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500';">
              </div>
              <div class="event-content" style="padding: 20px;">
                <div class="event-meta" style="font-size: 0.8rem;">
                  <span>📅 ${API.formatDate(ev.event_date)}</span>
                  <span>📍 ${cleanVenue}</span>
                </div>
                <h4 style="font-size: 1.15rem; margin-bottom: 8px;">${cleanTitle}</h4>
                <p class="event-desc" style="font-size: 0.88rem;">${cleanDesc}</p>
                <div class="event-footer" style="padding-top: 12px;">
                  <a href="events.html" class="btn btn-outline btn-sm">View Details & Register →</a>
                </div>
              </div>
            </div>
          `;
        }).join('');
      } else {
        eventsBox.innerHTML = `<p style="color: #64748b; grid-column: 1/-1;">Check back soon for new club events!</p>`;
      }
    } catch (e) {
      console.error(e);
    }
  }

  // 3. Load latest announcements snippet
  const announceBox = document.getElementById('home-announcements-list');
  if (announceBox) {
    try {
      const notices = await API.get('/api/announcements');
      const topNotices = notices.slice(0, 2);
      if (topNotices.length) {
        announceBox.innerHTML = topNotices.map(a => {
          const cleanTitle = API.escapeHtml(a.title);
          const cleanDesc = API.escapeHtml(a.description);

          return `
            <div class="announcement-card" style="margin-bottom: 16px;">
              <div class="announcement-icon" style="width: 42px; height: 42px; font-size: 1.2rem;">📢</div>
              <div class="announcement-body">
                <div class="announcement-header">
                  <strong style="font-size: 1.05rem;">${cleanTitle}</strong>
                  <span class="announcement-time">${API.formatDate(a.created_at)}</span>
                </div>
                <p class="announcement-desc" style="margin-top: 6px;">${cleanDesc}</p>
              </div>
            </div>
          `;
        }).join('');
      }
    } catch (e) {
      console.error(e);
    }
  }
}
