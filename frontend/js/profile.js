/**
 * ANALYTIX CLUB - USER PROFILE CONTROLLER
 */

let currentUser = null;

document.addEventListener('DOMContentLoaded', async () => {
  currentUser = await Auth.requireAuth();
  if (!currentUser) return;

  populateProfile();

  const profileForm = document.getElementById('profile-form');
  if (profileForm) {
    profileForm.addEventListener('submit', handleProfileUpdate);
  }
});

function populateProfile() {
  document.getElementById('profile-name').value = currentUser.full_name || '';
  document.getElementById('profile-email').value = currentUser.email || '';
  document.getElementById('profile-phone').value = currentUser.phone || '';
  document.getElementById('profile-dept').value = currentUser.department || '';
  document.getElementById('profile-year').value = currentUser.year || '';
  document.getElementById('profile-skills').value = currentUser.skills || '';
  document.getElementById('profile-bio').value = currentUser.bio || '';
  document.getElementById('profile-photo').value = currentUser.profile_photo || '';

  // Badges & read-only displays
  document.getElementById('display-role-badge').textContent = currentUser.role.toUpperCase();
  document.getElementById('display-team-badge').textContent = currentUser.team || 'None';
  document.getElementById('display-points-badge').textContent = `${currentUser.points || 0} pts`;
  document.getElementById('profile-header-name').textContent = currentUser.full_name;
  document.getElementById('profile-header-email').textContent = currentUser.email;

  const avatar = document.getElementById('profile-avatar-preview');
  if (currentUser.profile_photo) {
    avatar.innerHTML = `<img src="${currentUser.profile_photo}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" alt="Avatar">`;
  } else {
    avatar.textContent = (currentUser.full_name || 'U').charAt(0).toUpperCase();
  }

  // Back link to appropriate dashboard
  const backBtn = document.getElementById('back-to-dashboard-btn');
  if (backBtn) {
    backBtn.href = currentUser.role === 'admin' ? 'admin-dashboard.html' : 'member-dashboard.html';
  }
}

async function handleProfileUpdate(e) {
  e.preventDefault();

  const payload = {
    full_name: document.getElementById('profile-name').value.trim(),
    phone: document.getElementById('profile-phone').value.trim(),
    department: document.getElementById('profile-dept').value.trim(),
    year: document.getElementById('profile-year').value.trim(),
    skills: document.getElementById('profile-skills').value.trim(),
    bio: document.getElementById('profile-bio').value.trim(),
    profile_photo: document.getElementById('profile-photo').value.trim()
  };

  try {
    const updated = await API.put('/api/members/me', payload);
    currentUser = updated;
    API.setUser(updated);
    Auth.updateNavbarUser(updated);
    populateProfile();
    API.toast('Profile updated successfully!', 'success');
  } catch (err) {
    API.toast('Failed to update profile: ' + err.message, 'error');
  }
}

