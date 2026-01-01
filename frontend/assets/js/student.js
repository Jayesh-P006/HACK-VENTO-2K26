import { requireRole, api, showToast, hydrateUserBadge, attachLogout, setGreeting, animateStagger } from './app.js';

const auth = requireRole([1]);
if (!auth) return;

hydrateUserBadge(auth);
attachLogout();
setGreeting();

const statsEl = document.querySelector('#stats');
const jobsEl = document.querySelector('#jobs-list');
const announcementsEl = document.querySelector('#announcements');
const applicationsEl = document.querySelector('#applications');

let jobs = [];
let applications = [];

async function loadEverything() {
  try {
    const [jobsRes, appsRes, annRes] = await Promise.all([
      api('/student/jobs'),
      api('/student/applications'),
      api('/announcements'),
    ]);
    jobs = jobsRes || [];
    applications = appsRes || [];
    renderStats();
    renderJobs();
    renderAnnouncements(annRes || []);
    renderApplications();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderStats() {
  const eligible = jobs.filter(j => !j.has_applied).length;
  const applied = applications.length;
  const shortlisted = applications.filter(a => a.status === 'Shortlisted' || a.status === 'Interview').length;
  const selected = applications.filter(a => a.status === 'Selected').length;
  statsEl.innerHTML = `
    <div class="card animate">
      <p class="minor">Eligible Jobs</p>
      <h2>${eligible}</h2>
    </div>
    <div class="card animate">
      <p class="minor">Applications</p>
      <h2>${applied}</h2>
    </div>
    <div class="card animate">
      <p class="minor">Shortlisted / Interview</p>
      <h2>${shortlisted}</h2>
    </div>
    <div class="card animate">
      <p class="minor">Selected</p>
      <h2>${selected}</h2>
    </div>`;
}

function renderJobs() {
  jobsEl.innerHTML = jobs.map(job => `
    <article class="job-card animate" data-job-id="${job.id}">
      <div class="inline-actions" style="justify-content: space-between; align-items: flex-start;">
        <div>
          <h3>${job.title}</h3>
          <div class="job-meta">${job.company_name || 'Company'} • ${job.location}</div>
        </div>
        <span class="badge ${job.job_type === 'Internship' ? 'badge-amber' : 'badge-blue'}">${job.job_type}</span>
      </div>
      <p class="minor" style="margin: 10px 0;">${job.description || 'No description provided.'}</p>
      <div class="job-meta">
        <span>CGPA ${job.min_cgpa || 0}+</span>
        <span>Deadline ${new Date(job.application_deadline).toLocaleDateString()}</span>
        ${job.salary_range ? `<span>${job.salary_range}</span>` : ''}
      </div>
      <div class="job-meta">${job.requirements || ''}</div>
      <div class="inline-actions" style="margin-top: 12px;">
        ${job.has_applied ? `<span class="badge badge-green">Applied</span>` : `<button class="btn btn-primary" data-apply="${job.id}">Apply</button>`}
        <span class="chip">${job.job_type}</span>
      </div>
    </article>
  `).join('');
  animateStagger('.job-card');
}

jobsEl?.addEventListener('click', async (e) => {
  const applyId = e.target.getAttribute('data-apply');
  if (!applyId) return;
  const btn = e.target;
  btn.disabled = true;
  btn.textContent = 'Applying...';
  try {
    await api(`/student/apply/${applyId}`, { method: 'POST' });
    showToast('Application submitted', 'success');
    await loadEverything();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Apply';
  }
});

function renderAnnouncements(list) {
  announcementsEl.innerHTML = list.length ? list.map(item => `
    <div class="card animate">
      <h4>${item.title}</h4>
      <p class="minor" style="margin: 6px 0 12px;">${item.message}</p>
      <span class="badge badge-amber">${new Date(item.created_at).toLocaleDateString()}</span>
    </div>
  `).join('') : '<p class="minor">No announcements right now.</p>';
  animateStagger('#announcements .card');
}

function renderApplications() {
  const byStatus = ['Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected'];
  applicationsEl.innerHTML = byStatus.map(status => {
    const group = applications.filter(a => a.status === status);
    return `
      <div class="card animate">
        <div class="section-title">
          <h4>${status}</h4>
          <span class="badge badge-blue">${group.length}</span>
        </div>
        <div class="app-grid">
          ${group.map(app => `
            <div class="app-card">
              <h4>${app.job_title}</h4>
              <p class="minor">${app.company_name}</p>
              <div class="chip">Applied ${new Date(app.applied_at).toLocaleDateString()}</div>
            </div>
          `).join('') || '<p class="minor">No applications here yet.</p>'}
        </div>
      </div>`;
  }).join('');
  animateStagger('#applications .card');
}

loadEverything();
