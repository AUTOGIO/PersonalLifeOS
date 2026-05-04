/* charts.js — LIFE OS Chart.js initializations */
'use strict';

const CHART_DEFAULTS = {
  color: '#9ca3af',
  font: { family: "'JetBrains Mono', monospace", size: 11 },
};
Chart.defaults.color = CHART_DEFAULTS.color;
Chart.defaults.font = CHART_DEFAULTS.font;

const PALETTE = {
  black: '#000000', white: '#ffffff', green: '#22c55e', blue: '#2563eb',
  yellow: '#eab308', red: '#ef4444', orange: '#f97316',
  purple: '#6366f1', pink: '#f472b6',
};

function gridOpts(color = 'rgba(31,45,61,.6)') {
  return { color, drawBorder: false };
}

function tooltipOpts() {
  return {
    backgroundColor: 'rgba(17,24,39,.95)',
    borderColor: 'rgba(249,115,22,.35)',
    borderWidth: 1,
    titleFont: { family: "'Rajdhani',sans-serif", weight: 700 },
    bodyFont: { family: "'JetBrains Mono',monospace", size: 11 },
    padding: 10,
  };
}

// ── 1. Monthly Activity Bar Chart ──────────────────────────────────────────
async function initMonthlyBar() {
  const res = await fetch('/api/analytics/monthly/');
  const data = await res.json();
  const labels = Object.keys(data);
  const values = Object.values(data);
  const colors = labels.map((_, i) => Object.values(PALETTE)[i % 9]);

  new Chart(document.getElementById('monthlyBar'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Activities',
        data: values,
        backgroundColor: colors.map(c => c + '55'),
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false }, tooltip: tooltipOpts() },
      scales: {
        x: { grid: gridOpts(), ticks: { maxRotation: 35 } },
        y: { grid: gridOpts(), beginAtZero: true },
      }
    }
  });
}

// ── 2. AI Dev Donut ────────────────────────────────────────────────────────
async function initAiDonut() {
  const res = await fetch('/api/analytics/ai-donut/');
  const data = await res.json();
  const labels = { AI_DEV_CORE:'Core', AI_DEV_BUSINESS:'Business', AI_DEV_MACOS:'macOS', AI_DEV_TOOLS:'Tools' };
  const keys = Object.keys(data);
  const colors = ['#7c3aed','#f59e0b','#3b82f6','#ec4899'];

  new Chart(document.getElementById('aiDonut'), {
    type: 'doughnut',
    data: {
      labels: keys.map(k => labels[k] || k),
      datasets: [{
        data: Object.values(data),
        backgroundColor: colors.map(c => c + '99'),
        borderColor: colors,
        borderWidth: 2,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true } },
        tooltip: { ...tooltipOpts(), callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}h` } },
      }
    }
  });
}

// ── 3. Weekly AI Hours Bar ─────────────────────────────────────────────────
async function initWeeklyAiBar() {
  const res = await fetch('/api/analytics/weekly-ai/');
  const { labels, values } = await res.json();

  new Chart(document.getElementById('weeklyAiBar'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'AI Dev Hours',
        data: values,
        backgroundColor: PALETTE.purple + '66',
        borderColor: PALETTE.purple,
        borderWidth: 2,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false }, tooltip: tooltipOpts() },
      scales: {
        x: { grid: gridOpts() },
        y: { grid: gridOpts(), beginAtZero: true, title: { display: true, text: 'Hours' } },
      }
    }
  });
}

// ── 4. Mood & Energy Line ──────────────────────────────────────────────────
async function initMoodLine() {
  const res = await fetch('/api/analytics/mood/');
  const { labels, mood, energy } = await res.json();

  new Chart(document.getElementById('moodLine'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Mood',
          data: mood,
          borderColor: PALETTE.pink,
          backgroundColor: PALETTE.pink + '22',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: PALETTE.pink,
          pointRadius: 3,
        },
        {
          label: 'Energy',
          data: energy,
          borderColor: PALETTE.green,
          backgroundColor: PALETTE.green + '22',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: PALETTE.green,
          pointRadius: 3,
        },
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { usePointStyle: true, padding: 16 } },
        tooltip: tooltipOpts(),
      },
      scales: {
        x: { grid: gridOpts() },
        y: { grid: gridOpts(), beginAtZero: false, min: 1, max: 10 },
      }
    }
  });
}

// ── 5. Time Distribution Donut ────────────────────────────────────────────
async function initTimeDistDonut() {
  const res = await fetch('/api/analytics/time-distribution/');
  const data = await res.json();
  const keys = Object.keys(data);
  const colors = Object.values(PALETTE).slice(0, keys.length);

  new Chart(document.getElementById('timeDistDonut'), {
    type: 'doughnut',
    data: {
      labels: keys,
      datasets: [{
        data: Object.values(data),
        backgroundColor: colors.map(c => c + '99'),
        borderColor: colors,
        borderWidth: 2,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      cutout: '60%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 12, usePointStyle: true, font: { size: 10 } } },
        tooltip: { ...tooltipOpts(), callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}%` } },
      }
    }
  });
}

// ── 6. Kite Sessions Scatter ──────────────────────────────────────────────
async function initKiteScatter() {
  const res = await fetch('/api/analytics/kite/');
  const data = await res.json();

  new Chart(document.getElementById('kiteScatter'), {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'Kite Sessions',
        data: data.map(s => ({ x: s.x, y: s.y })),
        backgroundColor: PALETTE.blue + '99',
        borderColor: PALETTE.blue,
        borderWidth: 1,
        pointRadius: 7,
        pointHoverRadius: 10,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...tooltipOpts(),
          callbacks: {
            label: ctx => ` Date: ${ctx.raw.x}  Wind: ${ctx.raw.y}kn`,
          }
        }
      },
      scales: {
        x: { type: 'time', grid: gridOpts(), title: { display: true, text: 'Date' } },
        y: { grid: gridOpts(), beginAtZero: true, title: { display: true, text: 'Wind (knots)' } },
      }
    }
  });
}

// ── 7. Habit Streak Bar ───────────────────────────────────────────────────
async function initHabitStreak() {
  const res = await fetch('/api/analytics/habit-streak/');
  const { labels, streaks } = await res.json();

  new Chart(document.getElementById('habitStreak'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Streak (days)',
        data: streaks,
        backgroundColor: PALETTE.orange + '66',
        borderColor: PALETTE.orange,
        borderWidth: 2,
        borderRadius: 4,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend: { display: false }, tooltip: tooltipOpts() },
      scales: {
        x: { grid: gridOpts(), beginAtZero: true, title: { display: true, text: 'Days' } },
        y: { grid: gridOpts() },
      }
    }
  });
}

// ── 8. Weekly Heatmap (GitHub-style) ─────────────────────────────────────
async function initHeatmap() {
  const res = await fetch('/api/analytics/heatmap/');
  const data = await res.json();
  const container = document.getElementById('heatmapContainer');
  if (!container) return;

  const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  const HOURS = Array.from({length: 24}, (_, i) => `${String(i).padStart(2,'0')}:00`);

  let html = '<div style="display:grid;grid-template-columns:40px repeat(24,1fr);gap:3px;font-size:.6rem;font-family:JetBrains Mono,monospace">';
  html += '<div></div>';
  HOURS.forEach((h, i) => {
    html += `<div style="text-align:center;color:#6b7280;transform:rotate(-60deg);transform-origin:center bottom;height:32px;line-height:32px">${i % 3 === 0 ? h.slice(0,2) : ''}</div>`;
  });

  DAYS.forEach((day, di) => {
    html += `<div style="color:#9ca3af;display:flex;align-items:center">${day}</div>`;
    for (let h = 0; h < 24; h++) {
      const count = (data[di] && data[di][h]) ? data[di][h] : 0;
      const opacity = Math.min(count / 3, 1);
      const bg = count === 0 ? 'rgba(31,45,61,.5)' : `rgba(249,115,22,${0.2 + opacity * 0.8})`;
      html += `<div title="${day} ${h}:00 — ${count} activities" style="background:${bg};border-radius:2px;height:16px;cursor:default"></div>`;
    }
  });
  html += '</div>';
  container.innerHTML = html;
}

// ── Boot all charts ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('monthlyBar'))   initMonthlyBar();
  if (document.getElementById('aiDonut'))      initAiDonut();
  if (document.getElementById('weeklyAiBar'))  initWeeklyAiBar();
  if (document.getElementById('moodLine'))     initMoodLine();
  if (document.getElementById('timeDistDonut'))initTimeDistDonut();
  if (document.getElementById('kiteScatter'))  initKiteScatter();
  if (document.getElementById('habitStreak'))  initHabitStreak();
  if (document.getElementById('heatmapContainer')) initHeatmap();
});
