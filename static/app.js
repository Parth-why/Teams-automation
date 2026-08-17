/**
 * Smart Teams & Google Tasks Sync Hub - Visual Engine & Frontend Logic
 * Multi-Atmosphere Palettes, Dynamic Chart.js Gradients, Shooting Stars & Controls
 */

let subjectChartInstance = null;
let currentChartMode = 'bar'; // 'bar' or 'doughnut'
let cachedSubjectData = {};
let shootingStarTimer = null;

// Atmosphere Palette Theme Mappings for Chart Gradients
const THEME_CHART_COLORS = {
    // 🌆 Evening Sunset Sky
    'evening': {
        'Robotics': { start: '#4164B3', end: '#6A8DD6', border: '#315099' },
        'DSA': { start: '#E84D67', end: '#F68F9F', border: '#CF3750' },
        'DSA Lab': { start: '#F472B6', end: '#FBBF24', border: '#E8559E' },
        'EM-III': { start: '#6B4E9B', end: '#9D88CE', border: '#583D84' },
        'Python Prog': { start: '#0284C7', end: '#38BDF8', border: '#0369A1' },
        'Python Lab': { start: '#16A34A', end: '#4ADE80', border: '#15803D' },
        'ECA': { start: '#D97706', end: '#FCD34D', border: '#B45309' },
        'EDC': { start: '#E11D48', end: '#FB7185', border: '#BE123C' },
        'Tech Writing': { start: '#8B5CF6', end: '#C084FC', border: '#7C3AED' }
    },
    // 🌅 Dawn Sunrise
    'dawn': {
        'Robotics': { start: '#C2410C', end: '#F97316', border: '#9A3412' },
        'DSA': { start: '#E11D48', end: '#FB7185', border: '#BE123C' },
        'DSA Lab': { start: '#F43F5E', end: '#FDA4AF', border: '#E11D48' },
        'EM-III': { start: '#9333EA', end: '#C084FC', border: '#7E22CE' },
        'Python Prog': { start: '#0284C7', end: '#38BDF8', border: '#0369A1' },
        'Python Lab': { start: '#16A34A', end: '#4ADE80', border: '#15803D' },
        'ECA': { start: '#D97706', end: '#FCD34D', border: '#B45309' },
        'EDC': { start: '#E11D48', end: '#FB7185', border: '#BE123C' },
        'Tech Writing': { start: '#8B5CF6', end: '#C084FC', border: '#7C3AED' }
    },
    // ☀️ Daylight Azure
    'day': {
        'Robotics': { start: '#2563EB', end: '#60A5FA', border: '#1D4ED8' },
        'DSA': { start: '#E11D48', end: '#FB7185', border: '#BE123C' },
        'DSA Lab': { start: '#DB2777', end: '#F472B6', border: '#BE185D' },
        'EM-III': { start: '#6366F1', end: '#A5B4FC', border: '#4F46E5' },
        'Python Prog': { start: '#0284C7', end: '#38BDF8', border: '#0369A1' },
        'Python Lab': { start: '#16A34A', end: '#4ADE80', border: '#15803D' },
        'ECA': { start: '#D97706', end: '#FBBF24', border: '#B45309' },
        'EDC': { start: '#EF4444', end: '#F87171', border: '#DC2626' },
        'Tech Writing': { start: '#8B5CF6', end: '#C084FC', border: '#7C3AED' }
    },
    // 🌕 Moonlit Twilight Plum (Artwork Dark Theme)
    'twilight': {
        'Robotics': { start: '#7A9CE6', end: '#A4B8E9', border: '#5B82EA' },
        'DSA': { start: '#F68F9F', end: '#FDA4AF', border: '#EE7487' },
        'DSA Lab': { start: '#FB7185', end: '#FECDD3', border: '#F43F5E' },
        'EM-III': { start: '#9D88CE', end: '#C4B5FD', border: '#8B74B5' },
        'Python Prog': { start: '#4A8EC2', end: '#7DD3FC', border: '#3576A8' },
        'Python Lab': { start: '#34D399', end: '#6EE7B7', border: '#10B981' },
        'ECA': { start: '#FCD34D', end: '#FEF08A', border: '#F59E0B' },
        'EDC': { start: '#FB7185', end: '#FDA4AF', border: '#F43F5E' },
        'Tech Writing': { start: '#B5A4DD', end: '#E9D5FF', border: '#9D88CE' }
    },
    // 🌌 Deep Midnight Space
    'midnight': {
        'Robotics': { start: '#38BDF8', end: '#7DD3FC', border: '#0284C7' },
        'DSA': { start: '#F43F5E', end: '#FDA4AF', border: '#E11D48' },
        'DSA Lab': { start: '#EC4899', end: '#F472B6', border: '#DB2777' },
        'EM-III': { start: '#818CF8', end: '#C7D2FE', border: '#6366F1' },
        'Python Prog': { start: '#06B6D4', end: '#67E8F9', border: '#0891B2' },
        'Python Lab': { start: '#34D399', end: '#A7F3D0', border: '#10B981' },
        'ECA': { start: '#FBBF24', end: '#FDE68A', border: '#D97706' },
        'EDC': { start: '#F43F5E', end: '#FDA4AF', border: '#E11D48' },
        'Tech Writing': { start: '#A855F7', end: '#E9D5FF', border: '#9333EA' }
    },
    // 🌲 Aurora Borealis
    'aurora': {
        'Robotics': { start: '#2DD4BF', end: '#99F6E4', border: '#0D9488' },
        'DSA': { start: '#F472B6', end: '#FBCFE8', border: '#DB2777' },
        'DSA Lab': { start: '#FB7185', end: '#FECDD3', border: '#F43F5E' },
        'EM-III': { start: '#A78BFA', end: '#DDD6FE', border: '#8B5CF6' },
        'Python Prog': { start: '#38BDF8', end: '#BAE6FD', border: '#0284C7' },
        'Python Lab': { start: '#34D399', end: '#A7F3D0', border: '#10B981' },
        'ECA': { start: '#FCD34D', end: '#FEF08A', border: '#F59E0B' },
        'EDC': { start: '#FB7185', end: '#FDA4AF', border: '#F43F5E' },
        'Tech Writing': { start: '#C084FC', end: '#F3E8FF', border: '#A855F7' }
    },
    // 🌸 Sakura Dusk
    'sakura': {
        'Robotics': { start: '#DB2777', end: '#F472B6', border: '#BE185D' },
        'DSA': { start: '#E11D48', end: '#FB7185', border: '#BE123C' },
        'DSA Lab': { start: '#F43F5E', end: '#FDA4AF', border: '#E11D48' },
        'EM-III': { start: '#9333EA', end: '#C084FC', border: '#7E22CE' },
        'Python Prog': { start: '#0284C7', end: '#38BDF8', border: '#0369A1' },
        'Python Lab': { start: '#16A34A', end: '#4ADE80', border: '#15803D' },
        'ECA': { start: '#D97706', end: '#FCD34D', border: '#B45309' },
        'EDC': { start: '#E11D48', end: '#FB7185', border: '#BE123C' },
        'Tech Writing': { start: '#8B5CF6', end: '#C084FC', border: '#7C3AED' }
    }
};

const FALLBACK_GRADIENTS = [
    { start: '#4164B3', end: '#6A8DD6', border: '#315099' },
    { start: '#E84D67', end: '#F68F9F', border: '#CF3750' },
    { start: '#6B4E9B', end: '#9D88CE', border: '#583D84' },
    { start: '#D97706', end: '#FCD34D', border: '#B45309' },
    { start: '#0284C7', end: '#38BDF8', border: '#0369A1' },
    { start: '#16A34A', end: '#4ADE80', border: '#15803D' }
];

// Dark atmosphere set for quick toggle detection
const DARK_ATMOSPHERES = ['twilight', 'midnight', 'aurora'];

// ==========================================================================
// Theme & Atmosphere Management
// ==========================================================================

function initTheme() {
    // 1. Atmosphere Preset
    const savedAtm = localStorage.getItem('hub-atmosphere') || 'evening';
    selectAtmosphere(savedAtm, false);

    // 2. Star Density
    const savedDensity = localStorage.getItem('hub-star-density') || 'radiant';
    setStarDensity(savedDensity, false);

    // 3. Shooting Stars
    const shootingEnabled = localStorage.getItem('hub-shooting-stars') !== 'false';
    const shootingCheckbox = document.getElementById('toggleShootingStars');
    if (shootingCheckbox) shootingCheckbox.checked = shootingEnabled;
    toggleShootingStarsState(shootingEnabled, false);

    // 4. Font Typography
    const savedFont = localStorage.getItem('hub-font') || 'outfit';
    setFontFamily(savedFont, false);
}

function selectAtmosphere(atmName, shouldSave = true) {
    if (!THEME_CHART_COLORS[atmName]) atmName = 'evening';

    document.documentElement.setAttribute('data-theme', atmName);
    if (shouldSave) localStorage.setItem('hub-atmosphere', atmName);

    // Update active button in Modal
    document.querySelectorAll('.atmosphere-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-atm') === atmName);
    });

    // Update Header Toggle Icon & Label
    const isDark = DARK_ATMOSPHERES.includes(atmName);
    const icon = document.getElementById('themeIcon');
    const label = document.getElementById('themeLabel');
    if (icon) icon.textContent = isDark ? '☀️' : '🌙';
    if (label) label.textContent = isDark ? 'Light' : 'Dark';

    // Re-render chart with dynamic gradient
    if (subjectChartInstance && Object.keys(cachedSubjectData).length > 0) {
        renderSubjectChart(cachedSubjectData);
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'evening';
    const isDark = DARK_ATMOSPHERES.includes(current);
    const next = isDark ? 'evening' : 'twilight';
    selectAtmosphere(next);
}

function setStarDensity(density, shouldSave = true) {
    const starsLayer = document.getElementById('starsLayer');
    if (starsLayer) {
        starsLayer.className = `stars-layer density-${density}`;
    }

    if (shouldSave) localStorage.setItem('hub-star-density', density);

    document.querySelectorAll('.chip-btn[data-density]').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-density') === density);
    });
}

function toggleShootingStarsState(enabled, shouldSave = true) {
    if (shouldSave) localStorage.setItem('hub-shooting-stars', enabled ? 'true' : 'false');

    if (enabled) {
        startShootingStars();
    } else {
        stopShootingStars();
    }
}

function setFontFamily(font, shouldSave = true) {
    document.documentElement.setAttribute('data-font', font);
    if (shouldSave) localStorage.setItem('hub-font', font);

    document.querySelectorAll('.chip-btn[data-font]').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-font') === font);
    });
}

// ==========================================================================
// Shooting Stars Spawner Engine
// ==========================================================================

function startShootingStars() {
    if (shootingStarTimer) clearInterval(shootingStarTimer);

    // Initial shooting star after 3s
    setTimeout(spawnSingleShootingStar, 3000);

    // Occasional meteor streak every 12-18 seconds
    shootingStarTimer = setInterval(() => {
        const density = localStorage.getItem('hub-star-density');
        if (density !== 'off') {
            spawnSingleShootingStar();
        }
    }, Math.floor(Math.random() * 6000) + 12000);
}

function stopShootingStars() {
    if (shootingStarTimer) {
        clearInterval(shootingStarTimer);
        shootingStarTimer = null;
    }
    const container = document.getElementById('shootingStarsLayer');
    if (container) container.innerHTML = '';
}

function spawnSingleShootingStar() {
    const container = document.getElementById('shootingStarsLayer');
    if (!container) return;

    const star = document.createElement('div');
    star.className = 'shooting-star';

    // Randomize starting coordinates (top 45% of viewport)
    const startX = Math.floor(Math.random() * (window.innerWidth - 200)) + 200;
    const startY = Math.floor(Math.random() * (window.innerHeight * 0.45));

    star.style.left = `${startX}px`;
    star.style.top = `${startY}px`;

    container.appendChild(star);

    setTimeout(() => {
        star.remove();
    }, 2500);
}

// ==========================================================================
// Modal Helpers
// ==========================================================================

function openThemeModal() {
    document.getElementById('themeModal').classList.add('active');
}

function closeThemeModal() {
    document.getElementById('themeModal').classList.remove('active');
}

function openClearModal() {
    document.getElementById('clearModal').classList.add('active');
}

function closeClearModal() {
    document.getElementById('clearModal').classList.remove('active');
}

// ==========================================================================
// Status & Dashboard Loading
// ==========================================================================

async function loadStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        if (data.success) {
            updateDashboard(data);
        }
    } catch (err) {
        console.error('Error fetching status:', err);
    }
}

function updateDashboard(data) {
    const stats = data.stats || {};
    const subjects = data.subject_breakdown || {};
    const logs = data.activity_logs || [];
    cachedSubjectData = subjects;

    // 1. Google Status Badge
    const badgeText = document.getElementById('googleStatusText');
    if (badgeText) {
        if (data.gcal_ready) {
            badgeText.textContent = `🟢 Google Connected (${stats.synced_tasks || 0} Tasks Synced)`;
        } else {
            badgeText.textContent = '⚠️ Google credentials.json not found';
        }
    }

    // 2. Urgency Metrics
    document.getElementById('metricUrgent48h').textContent = stats.urgent_48h || 0;
    document.getElementById('metricThisWeek').textContent = stats.this_week || 0;
    document.getElementById('metricLater').textContent = stats.later || 0;

    // 3. Render Subject-wise Interactive Gradient Chart
    renderSubjectChart(subjects);

    // 4. Live Activity Logs
    const logWindow = document.getElementById('consoleLogWindow');
    logWindow.innerHTML = '';
    logs.forEach(log => {
        const entry = document.createElement('div');
        entry.className = `log-entry ${log.level || 'info'}`;
        entry.innerHTML = `<span class="log-time">[${log.time}]</span> ${escapeHtml(log.message)}`;
        logWindow.appendChild(entry);
    });

    // 5. Footer Database Counter
    document.getElementById('footerDbStatus').textContent = 
        `Local Database: ${stats.total_tracked || 0} active assignments preserved (data/assignments.json)`;
}

// ==========================================================================
// Chart.js Subject Workload Engine with Dynamic Gradient Fills
// ==========================================================================

function renderSubjectChart(subjects) {
    const canvas = document.getElementById('subjectWorkloadChart');
    const emptyMsg = document.getElementById('chartEmptyMessage');

    if (!canvas) return;

    const entries = Object.entries(subjects);
    if (entries.length === 0) {
        canvas.style.display = 'none';
        emptyMsg.style.display = 'block';
        if (subjectChartInstance) {
            subjectChartInstance.destroy();
            subjectChartInstance = null;
        }
        return;
    }

    canvas.style.display = 'block';
    emptyMsg.style.display = 'none';

    // Sort descending by task count
    entries.sort((a, b) => b[1] - a[1]);
    const labels = entries.map(e => e[0]);
    const counts = entries.map(e => e[1]);

    const activeTheme = document.documentElement.getAttribute('data-theme') || 'evening';
    const colorThemeMap = THEME_CHART_COLORS[activeTheme] || THEME_CHART_COLORS['evening'];
    const isDark = DARK_ATMOSPHERES.includes(activeTheme);

    const ctx = canvas.getContext('2d');
    const chartHeight = canvas.parentElement.clientHeight || 180;
    const chartWidth = canvas.parentElement.clientWidth || 300;

    // Generate Dynamic Linear Canvas Gradients
    const bgGradients = [];
    const borderColors = [];

    labels.forEach((lbl, idx) => {
        const colorCfg = colorThemeMap[lbl] || FALLBACK_GRADIENTS[idx % FALLBACK_GRADIENTS.length];
        
        let grad;
        if (currentChartMode === 'bar') {
            // Horizontal gradient for horizontal bars (left to right)
            grad = ctx.createLinearGradient(0, 0, chartWidth, 0);
            grad.addColorStop(0, colorCfg.start);
            grad.addColorStop(1, colorCfg.end);
        } else {
            // Vertical gradient for doughnut arcs
            grad = ctx.createLinearGradient(0, 0, 0, chartHeight);
            grad.addColorStop(0, colorCfg.start);
            grad.addColorStop(1, colorCfg.end);
        }

        bgGradients.push(grad);
        borderColors.push(colorCfg.border);
    });

    if (subjectChartInstance) {
        subjectChartInstance.destroy();
    }

    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
    const textColor = isDark ? '#F8F6FD' : '#191228';
    const subTextColor = isDark ? '#C8BFDE' : '#483C60';
    const tooltipBg = isDark ? '#1C162E' : '#191228';
    const tooltipBorder = borderColors[0] || '#4164B3';

    if (currentChartMode === 'bar') {
        // Horizontal Bar Chart with Dynamic Gradients
        subjectChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Assignments',
                    data: counts,
                    backgroundColor: bgGradients,
                    borderColor: borderColors,
                    borderWidth: 1.5,
                    borderRadius: 6,
                    barPercentage: 0.68,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: tooltipBg,
                        titleColor: '#FFFFFF',
                        bodyColor: '#FBBF24',
                        borderColor: tooltipBorder,
                        borderWidth: 1,
                        padding: 10,
                        displayColors: false,
                        cornerRadius: 6,
                        callbacks: {
                            label: function(context) {
                                const val = context.raw || 0;
                                return ` ${val} active ${val === 1 ? 'assignment' : 'assignments'}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: subTextColor,
                            font: { size: 11, weight: '500' },
                            stepSize: 1,
                            precision: 0
                        },
                        grid: {
                            color: gridColor,
                            drawBorder: false,
                        }
                    },
                    y: {
                        ticks: {
                            color: textColor,
                            font: { size: 12, weight: '600' }
                        },
                        grid: { display: false }
                    }
                },
                animation: {
                    duration: 450,
                    easing: 'easeOutQuart'
                }
            }
        });
    } else {
        // Modern Doughnut Chart with Dynamic Gradients
        subjectChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: bgGradients,
                    borderColor: isDark ? '#1C162E' : '#FFFFFF',
                    borderWidth: 2,
                    hoverOffset: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: textColor,
                            font: { size: 11, weight: '500' },
                            padding: 8,
                            boxWidth: 10,
                            boxHeight: 10,
                            borderRadius: 2,
                            useBorderRadius: true
                        }
                    },
                    tooltip: {
                        backgroundColor: tooltipBg,
                        titleColor: '#FFFFFF',
                        bodyColor: '#60A5FA',
                        borderColor: tooltipBorder,
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 6,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const val = context.raw || 0;
                                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                                return ` ${val} tasks (${pct}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 450
                }
            }
        });
    }
}

// Switch between Bar Chart and Donut View
function switchChartMode(mode) {
    if (currentChartMode === mode) return;

    currentChartMode = mode;

    document.getElementById('btnChartBar').classList.toggle('active', mode === 'bar');
    document.getElementById('btnChartDonut').classList.toggle('active', mode === 'doughnut');

    renderSubjectChart(cachedSubjectData);
}

// ==========================================================================
// Action Handlers (Scan, Sync, Clear, Export)
// ==========================================================================

// Action 1: Scan Teams Only
async function triggerScanTeams() {
    const btn = document.getElementById('btnScanTeams');
    btn.disabled = true;
    btn.textContent = 'Scanning Teams...';
    showToast('Opening Microsoft Teams browser session to scan assignments...', 'info');

    try {
        const res = await fetch('/api/scan-teams', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            pollScanStatus();
        } else {
            showToast(data.message || 'Scan failed.', 'error');
            btn.disabled = false;
            btn.textContent = 'Scan Teams Now';
        }
    } catch (e) {
        showToast('Error starting Teams scan.', 'error');
        btn.disabled = false;
        btn.textContent = 'Scan Teams Now';
    }
}

function pollScanStatus() {
    const interval = setInterval(async () => {
        const res = await fetch('/api/status');
        const data = await res.json();
        updateDashboard(data);

        if (!data.is_fetching) {
            clearInterval(interval);
            const btn = document.getElementById('btnScanTeams');
            btn.disabled = false;
            btn.textContent = 'Scan Teams Now';
            showToast('Teams scan complete! Click "Sync Tasks to Google" when ready.', 'success');
        }
    }, 2000);
}

// Action 2: Sync to Google Tasks
async function triggerSyncGoogle() {
    const btn = document.getElementById('btnSyncOnly');
    btn.disabled = true;
    btn.textContent = 'Syncing to Google...';
    showToast('Pushing 9:00 AM checklist tasks to Google Tasks...', 'info');

    try {
        const res = await fetch('/api/sync-google', { method: 'POST' });
        const data = await res.json();

        btn.disabled = false;
        btn.textContent = 'Sync Tasks to Google';

        if (data.success) {
            const s = data.stats;
            showToast(`Google Tasks Synced: ${s.tasks_created || 0} created, ${s.tasks_updated || 0} updated.`, 'success');
            loadStatus();
        } else {
            showToast(data.error || 'Sync failed.', 'error');
        }
    } catch (e) {
        btn.disabled = false;
        btn.textContent = 'Sync Tasks to Google';
        showToast('Error connecting to Google Tasks API.', 'error');
    }
}

// Action 3: Clear Google Tasks
async function executeClearGoogle() {
    const btn = document.getElementById('btnConfirmClear');
    btn.disabled = true;
    btn.textContent = 'Decongesting Google Tasks...';

    try {
        const res = await fetch('/api/clear-google', { method: 'POST' });
        const data = await res.json();

        closeClearModal();
        btn.disabled = false;
        btn.textContent = 'Yes, Clear Cloud Tasks';

        if (data.success) {
            showToast('Google Tasks cleared! Local database preserved.', 'success');
            loadStatus();
        } else {
            showToast(data.message || 'Error clearing cloud tasks.', 'error');
        }
    } catch (e) {
        closeClearModal();
        btn.disabled = false;
        btn.textContent = 'Yes, Clear Cloud Tasks';
        showToast('Error performing clear operation.', 'error');
    }
}

// Action 4: Download .ICS Feed
function downloadIcs() {
    window.location.href = '/api/export-ics';
    showToast('Downloading offline .ICS calendar feed...', 'info');
}

// Toast Feedback Helper
function showToast(message, type = 'info') {
    const area = document.getElementById('toastArea');
    const toast = document.createElement('div');
    toast.className = `toast-msg ${type}`;

    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';

    toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;
    area.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(8px)';
        setTimeout(() => toast.remove(), 250);
    }, 4000);
}

// XSS Sanitizer
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Auto-refresh & Theme Init on load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadStatus();
    setInterval(loadStatus, 15000);
});
