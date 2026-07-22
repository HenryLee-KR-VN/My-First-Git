const state = {
  filters: { source: "", domain: "", employment_type: "", career_level: "", location: "", q: "" },
  stacks: new Set(),
  trendDays: 7,
  charts: {},
};

// ---------- 색상 팔레트 (브랜드 블루 #4876EF 기반 체계적 팔레트) ----------
function bluePalette(n) {
  const colors = [];
  for (let i = 0; i < n; i++) {
    const hue = 224 - (i * 3);              // 블루 계열에서 살짝씩 변화
    const light = 42 + (i * (38 / Math.max(n - 1, 1))); // 42%~80% 밝기 단계
    colors.push(`hsl(${hue}, 72%, ${light}%)`);
  }
  return colors;
}

// ---------- 탭 전환 ----------
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const panel = document.getElementById(`tab-${btn.dataset.tab}`);
    panel.classList.add("active");
    if (btn.dataset.tab === "trend") {
      // 패널이 display:none -> block 으로 전환된 직후 바로 그리면 Chart.js가
      // 전환 전 레이아웃(폭 0)을 기준으로 그려버릴 수 있어 다음 프레임까지 기다린다.
      requestAnimationFrame(() => requestAnimationFrame(loadTrends));
    }
  });
});

// ---------- 필터 초기화 (드롭다운 옵션 채우기) ----------
async function loadFilterOptions() {
  const res = await fetch("/api/filters");
  const data = await res.json();

  fillSelect("f-source", data.sources);
  fillSelect("f-domain", data.domains);
  fillSelect("f-employment", data.employment_types);
  fillSelect("f-career", data.career_levels);
  fillSelect("f-location", data.locations);

  const stackWrap = document.getElementById("f-stacks");
  stackWrap.innerHTML = "";
  data.stacks.forEach(stack => {
    const id = `stack-${stack.replace(/[^a-zA-Z0-9]/g, "")}`;
    const label = document.createElement("label");
    label.innerHTML = `<input type="checkbox" id="${id}" value="${stack}"> ${stack}`;
    stackWrap.appendChild(label);
    label.querySelector("input").addEventListener("change", (e) => {
      if (e.target.checked) state.stacks.add(stack);
      else state.stacks.delete(stack);
      loadJobs();
    });
  });
}

function fillSelect(id, options) {
  const el = document.getElementById(id);
  const current = el.value;
  el.innerHTML = '<option value="">전체</option>';
  options.forEach(opt => {
    const o = document.createElement("option");
    o.value = opt;
    o.textContent = opt;
    el.appendChild(o);
  });
  el.value = current;
}

// ---------- 공고 리스트 ----------
function buildQuery() {
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(state.filters)) {
    if (v) params.append(k, v);
  }
  state.stacks.forEach(s => params.append("stack", s));
  return params.toString();
}

async function loadJobs() {
  const res = await fetch(`/api/jobs?${buildQuery()}`);
  const jobs = await res.json();
  renderJobs(jobs);
}

function renderJobs(jobs) {
  const list = document.getElementById("job-list");
  document.getElementById("job-count").textContent = `${jobs.length}건`;

  if (jobs.length === 0) {
    list.innerHTML = '<div class="empty-state">조건에 맞는 공고가 없습니다.</div>';
    return;
  }

  list.innerHTML = jobs.map(job => `
    <div class="job-card" data-url="${escapeHtml(job.url)}">
      <div class="job-card-main">
        <div class="job-company">${escapeHtml(job.company_name)}</div>
        <div class="job-title">${escapeHtml(job.job_title)}</div>
        <div class="job-meta">
          <span>${escapeHtml(job.company_domain || "-")}</span>
          <span>${escapeHtml(job.employment_type || "-")}</span>
          <span>${escapeHtml(job.career_level || "-")}</span>
          <span>${escapeHtml(job.location || "-")}</span>
        </div>
        <div class="tag-badges">
          ${job.tech_stack.map(t => `<span class="tag-badge">${escapeHtml(t)}</span>`).join("")}
        </div>
      </div>
      <div class="job-card-side">
        <span class="job-source ${job.source === "잡코리아" ? "jobkorea" : "saramin"}">${escapeHtml(job.source)}</span>
        <span class="job-date">${escapeHtml(job.posted_date || "-")}</span>
      </div>
    </div>
  `).join("");

  list.querySelectorAll(".job-card").forEach(card => {
    card.addEventListener("click", () => {
      const url = card.dataset.url;
      if (url) window.open(url, "_blank", "noopener,noreferrer");
    });
  });
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

document.getElementById("f-q").addEventListener("input", debounce(e => {
  state.filters.q = e.target.value;
  loadJobs();
}, 300));

["f-source", "f-domain", "f-employment", "f-career", "f-location"].forEach(id => {
  const keyMap = {
    "f-source": "source", "f-domain": "domain", "f-employment": "employment_type",
    "f-career": "career_level", "f-location": "location",
  };
  document.getElementById(id).addEventListener("change", e => {
    state.filters[keyMap[id]] = e.target.value;
    loadJobs();
  });
});

document.getElementById("f-reset").addEventListener("click", () => {
  state.filters = { source: "", domain: "", employment_type: "", career_level: "", location: "", q: "" };
  state.stacks.clear();
  document.getElementById("f-q").value = "";
  ["f-source", "f-domain", "f-employment", "f-career", "f-location"].forEach(id => {
    document.getElementById(id).value = "";
  });
  document.querySelectorAll("#f-stacks input[type=checkbox]").forEach(cb => cb.checked = false);
  loadJobs();
});

function debounce(fn, wait) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

// ---------- 트렌드 대시보드 ----------
document.querySelectorAll(".range-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".range-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.trendDays = parseInt(btn.dataset.days, 10);
    loadTrends();
  });
});

async function loadTrends() {
  const res = await fetch(`/api/trends?days=${state.trendDays}`);
  const data = await res.json();

  document.getElementById("sum-new-jobs").textContent = `${data.new_jobs_count}건`;
  document.getElementById("sum-top-stack").textContent = data.top_stack || "-";
  document.getElementById("sum-top-domain").textContent = data.top_domain || "-";

  renderDomainChart(data.domain_counts);
  renderStackChart(data.stack_counts_top15);
  renderDailyChart(data.daily_counts);
  renderCompanyChart(data.top_companies);
}

function destroyIfExists(key) {
  if (state.charts[key]) {
    state.charts[key].destroy();
  }
}

function renderDomainChart(domainCounts) {
  destroyIfExists("domain");
  const ctx = document.getElementById("chart-domain");
  const labels = domainCounts.map(d => d[0]);
  const values = domainCounts.map(d => d[1]);
  state.charts.domain = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label: "공고 수", data: values, backgroundColor: bluePalette(labels.length) }] },
    options: baseOptions(false),
  });
  state.charts.domain.resize();
}

function renderStackChart(stackCounts) {
  destroyIfExists("stack");
  const ctx = document.getElementById("chart-stack");
  const labels = stackCounts.map(d => d[0]);
  const values = stackCounts.map(d => d[1]);
  state.charts.stack = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label: "수요 건수", data: values, backgroundColor: bluePalette(labels.length) }] },
    options: { ...baseOptions(true), indexAxis: "y" },
  });
  state.charts.stack.resize();
}

function renderDailyChart(dailyCounts) {
  destroyIfExists("daily");
  const ctx = document.getElementById("chart-daily");
  const labels = dailyCounts.map(d => d[0]);
  const values = dailyCounts.map(d => d[1]);
  state.charts.daily = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "일별 등록 공고 수",
        data: values,
        borderColor: "#4876EF",
        backgroundColor: "rgba(72,118,239,0.12)",
        fill: true,
        tension: 0.25,
        pointRadius: 3,
      }],
    },
    options: baseOptions(false),
  });
  state.charts.daily.resize();
}

function renderCompanyChart(topCompanies) {
  destroyIfExists("company");
  const ctx = document.getElementById("chart-company");
  const labels = topCompanies.map(d => d[0]);
  const values = topCompanies.map(d => d[1]);
  state.charts.company = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label: "공고 수", data: values, backgroundColor: bluePalette(labels.length) }] },
    options: { ...baseOptions(true), indexAxis: "y" },
  });
  state.charts.company.resize();
}

function baseOptions(horizontal) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { beginAtZero: true, ticks: { precision: 0 } },
      y: { beginAtZero: true, ticks: { precision: 0 } },
    },
  };
}

// ---------- 초기 로딩 ----------
(async function init() {
  await loadFilterOptions();
  await loadJobs();
})();
