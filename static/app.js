/**
 * Smart Teams & Google Tasks Sync Hub - Frontend Logic
 * Evening Sky (Light Mode) & Moonlit Twilight (Dark Mode) Theme Engine & Chart.js Integration
 */

let subjectChartInstance = null;
let currentChartMode = 'bar'; // 'bar' or 'doughnut'
let cachedSubjectData = {};

// 🌆 Evening Sky Palette (Light Mode)
const EVENING_SUBJECT_COLORS = {
    'Robotics': { bg: '#4164B3', border: '#315099' },      // Dusk Sky Indigo
    'DSA': { bg: '#E84D67', border: '#CF3750' },           // Sunset Coral
    'DSA Lab': { bg: '#F472B6', border: '#E8559E' },       // Cotton Candy Rose
    'EM-III': { bg: '#6B4E9B', border: '#583D84' },        // Twilight Lilac
    'Python Prog': { bg: '#0284C7', border: '#0369A1' },    // Sky Cerulean
    'Python Lab': { bg: '#16A34A', border: '#15803D' },     // Emerald Green
    'ECA': { bg: '#D97706', border: '#B45309' },            // Sunset Gold
    'EDC': { bg: '#E11D48', border: '#BE123C' },            // Deep Crimson
    'Tech Writing': { bg: '#8B5CF6', border: '#7C3AED' },   // Twilight Mist
};

// 🌕 Moonlit Twilight Palette (Dark Mode - Restored from Artwork)
const NIGHT_SUBJECT_COLORS = {
    'Robotics': { bg: '#7A9CE6', border: '#5B82EA' },      // Luminous Periwinkle Sky
    'DSA': { bg: '#F68F9F', border: '#EE7487' },           // Sunset Cloud Peach / Coral
    'DSA Lab': { bg: '#FB7185', border: '#F43F5E' },       // Cotton Candy Rose
    'EM-III': { bg: '#9D88CE', border: '#8B74B5' },        // Twilight Lilac / Plum
    'Python Prog': { bg: '#4A8EC2', border: '#3576A8' },    // Luminous Sky Blue
    'Python Lab': { bg: '#34D399', border: '#10B981' },     // Sage Jade
    'ECA': { bg: '#FCD34D', border: '#F59E0B' },            // Moonbeam Gold
    'EDC': { bg: '#FB7185', border: '#F43F5E' },            // Deep Sunset Rose
    'Tech Writing': { bg: '#B5A4DD', border: '#9D88CE' },   // Dusty Lilac
};

const FALLBACK_COLORS = [
    { bg: '#4164B3', border: '#315099' },
    { bg: '#E84D67', border: '#CF3750' },
    { bg: '#6B4E9B', border: '#583D84' },
    { bg: '#D97706', border: '#B45309' },
    { bg: '#0284C7', border: '#0369A1' },
    { bg: '#16A34A', border: '#15803D' },
];

// ==========================================================================
// Theme Management (Light Mode ⇄ Dark Mode)
// ==========================================================================

function initTheme() {
    const savedTheme = localStorage.getItem('hub-theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        setTheme('light');
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('hub-theme', theme);

    const btn = document.getElementById('themeToggleBtn');
    const icon = document.getElementById('themeIcon');
    const label = document.getElementById('themeLabel');

    if (theme === 'dark') {
        if (icon) icon.textContent = '☀️';
        if (label) label.textContent = 'Light Mode';
        if (btn) btn.title = 'Switch to Light Mode';
    } else {
        if (icon) icon.textContent = '🌙';
        if (label) label.textContent = 'Dark Mode';
        if (btn) btn.title = 'Switch to Dark Mode';
    }

    // Refresh Chart styling to match active theme
    if (subjectChartInstance && Object.keys(cachedSubjectData).length > 0) {
        renderSubjectChart(cachedSubjectData);
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
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
    const badge = document.getElementById('googleConnectionBadge');
    const badgeText = document.getElementById('googleStatusText');

    if (data.gcal_ready) {
        badgeText.textContent = `🟢 Google Connected (${stats.synced_tasks || 0} Tasks Synced)`;
    } else {
        badgeText.textContent = '⚠️ Google credentials.json not found';
    }

    // 2. Urgency Metrics
    document.getElementById('metricUrgent48h').textContent = stats.urgent_48h || 0;
    document.getElementById('metricThisWeek').textContent = stats.this_week || 0;
    document.getElementById('metricLater').textContent = stats.later || 0;

    // 3. Render Subject-wise Interactive Chart
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
// Chart.js Subject Workload Engine (Restored Artwork Colors)
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

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const colorMap = isDark ? NIGHT_SUBJECT_COLORS : EVENING_SUBJECT_COLORS;

    const bgColors = [];
    const borderColors = [];

    labels.forEach((lbl, idx) => {
        if (colorMap[lbl]) {
            bgColors.push(colorMap[lbl].bg);
            borderColors.push(colorMap[lbl].border);
        } else {
            const fallback = FALLBACK_COLORS[idx % FALLBACK_COLORS.length];
            bgColors.push(fallback.bg);
            borderColors.push(fallback.border);
        }
    });

    if (subjectChartInstance) {
        subjectChartInstance.destroy();
    }

    const gridColor = isDark ? '#342A52' : '#E2D9F3';
    const textColor = isDark ? '#F8F6FD' : '#191228';
    const subTextColor = isDark ? '#C8BFDE' : '#483C60';
    const tooltipBg = isDark ? '#1C162E' : '#191228';
    const tooltipBorder = isDark ? '#9D88CE' : '#E84D67';

    const ctx = canvas.getContext('2d');

    if (currentChartMode === 'bar') {
        // Horizontal Bar Chart
        subjectChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Assignments',
                    data: counts,
                    backgroundColor: bgColors,
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
                        bodyColor: isDark ? '#F68F9F' : '#FCA5A5',
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
                            font: { family: 'Inter', size: 11, weight: '500' },
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
                            font: { family: 'Inter', size: 12, weight: '600' }
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
        // Modern Doughnut Chart
        subjectChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: bgColors,
                    borderColor: isDark ? '#1C162E' : '#FFFFFF',
                    borderWidth: 2,
                    hoverOffset: 5,
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
                            font: { family: 'Inter', size: 11, weight: '500' },
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
                        bodyColor: isDark ? '#7A9CE6' : '#93C5FD',
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
function openClearModal() {
    document.getElementById('clearModal').classList.add('active');
}

function closeClearModal() {
    document.getElementById('clearModal').classList.remove('active');
}

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
