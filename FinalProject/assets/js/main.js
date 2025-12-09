let currentIndex = 0;
const TRANSITION_LOCK_MS = 850;
const MIN_NAV_GAP = 900;
const SWIPE_THRESHOLD = 30;
const TOUCH_THRESHOLD = 50;

const scrollContainer = document.getElementById("scroll-container");
const panels = Array.from(document.querySelectorAll(".panel"));
const navButtons = Array.from(document.querySelectorAll("[data-target]"));
const progressDots = Array.from(document.querySelectorAll(".progress-dot"));
const topNav = document.getElementById("top-nav");
const progressIndicator = document.querySelector(".progress-indicator");

let isTransitioning = false;
let transitionTimeout = null;
let lastNavTime = 0;

/* ============================================
   SIDEBAR NAVIGATION WITH FILTERING
   ============================================ */
const tabGroups = {
  1: [0, 1, 2],
  2: [3, 4, 5],
  3: [6, 7, 8]
};

let activeTabGroup = 1;

function initSidebar() {
  const sidebarTabs = document.querySelectorAll(".sidebar-tab");

  sidebarTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const tabId = parseInt(tab.dataset.tab);

      sidebarTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      activeTabGroup = tabId;
      filterPanelsByTab(tabId);

      const firstPanel = tabGroups[tabId][0];
      scrollToPanel(firstPanel);
    });
  });

  filterPanelsByTab(1);
}

function filterPanelsByTab(tabId) {
  const visibleIndices = tabGroups[tabId];

  panels.forEach((panel, index) => {
    if (visibleIndices.includes(index)) {
      panel.classList.remove("filtered-out");
    } else {
      panel.classList.add("filtered-out");
    }
  });

  progressDots.forEach((dot, index) => {
    dot.style.display = visibleIndices.includes(index) ? "" : "none";
  });

  const navLinkButtons = document.querySelectorAll(".nav-links button");
  let vizNumber = 1;
  navLinkButtons.forEach((btn) => {
    const targetIndex = parseInt(btn.dataset.target);
    if (!Number.isNaN(targetIndex)) {
      if (visibleIndices.includes(targetIndex)) {
        btn.style.display = "";
        btn.textContent = `Viz ${vizNumber}`;
        vizNumber++;
      } else {
        btn.style.display = "none";
      }
    }
  });
}

function syncSidebarWithPanel(panelIndex) {
  const sidebarTabs = document.querySelectorAll(".sidebar-tab");

  for (const [tabId, indices] of Object.entries(tabGroups)) {
    if (indices.includes(panelIndex)) {
      sidebarTabs.forEach(t => {
        t.classList.toggle("active", parseInt(t.dataset.tab) === parseInt(tabId));
      });
      break;
    }
  }
}

function getTabGroupForPanel(panelIndex) {
  for (const [tabId, indices] of Object.entries(tabGroups)) {
    if (indices.includes(panelIndex)) {
      return parseInt(tabId);
    }
  }
  return 1;
}

function initParticles() {
  const container = document.getElementById("particles");
  if (!container) return;

  for (let i = 0; i < 25; i++) {
    const particle = document.createElement("div");
    particle.className = "particle";
    particle.style.left = `${Math.random() * 100}%`;
    particle.style.animationDuration = `${Math.random() * 6 + 5}s`;
    particle.style.animationDelay = `${Math.random() * 8}s`;
    particle.style.opacity = Math.random() * 0.4 + 0.2;

    const colors = [
      "rgba(76, 141, 255, 0.6)",
      "rgba(168, 85, 247, 0.6)",
      "rgba(34, 211, 238, 0.5)",
      "rgba(255, 255, 255, 0.4)"
    ];
    particle.style.background = colors[Math.floor(Math.random() * colors.length)];
    container.appendChild(particle);
  }
}

function initNavbarVisibility() {
  const panelInners = document.querySelectorAll(".panel-inner");
  panelInners.forEach((panelInner) => {
    panelInner.addEventListener("scroll", checkNavbarVisibility);
  });
  checkNavbarVisibility();
}

function checkNavbarVisibility() {
  if (!topNav && !progressIndicator) return;

  const currentPanel = panels[currentIndex];
  const panelInner = currentPanel ? currentPanel.querySelector(".panel-inner") : null;

  const maxScroll = panelInner ? panelInner.scrollHeight - panelInner.clientHeight : 0;
  const isAtTop = !panelInner || panelInner.scrollTop < 50;
  const atBottom = panelInner && maxScroll > 0 && panelInner.scrollTop >= maxScroll - 50;

  if (topNav) {
    if (isAtTop) {
      topNav.classList.add("visible");
      document.body.classList.add("nav-visible");
    } else {
      topNav.classList.remove("visible");
      document.body.classList.remove("nav-visible");
    }
  }

  if (progressIndicator) {
    progressIndicator.classList.toggle("visible", atBottom);
  }
}

function initVisualizations() {
  const basePath = "assets/json/";

  const charts = [
    { id: "viz-chart-1", file: "hsls_math_identity_race.json", width: 1100, height: 310 },
    { id: "viz-chart-2", file: "combined_immigration.json", width: 1100, height: 310 },
    { id: "viz-chart-3", file: "pisa_gender_efficacy_dumbbell.json", width: 1100, height: 310 },
    { id: "viz-chart-4", file: "hsls_gpa_ses_trajectory.json", width: 1100, height: 310 },
    { id: "viz-chart-5", file: "combined_ses_achievement.json", width: 1100, height: 310 },
    { id: "viz-chart-6", file: "combined_parent_education.json", width: 1100, height: 310 },
    { id: "viz-chart-7", file: "pisa_anxiety_performance_heatmap.json", width: 1100, height: 310 },
    { id: "viz-chart-8", file: "combined_efficacy_comparison.json", width: 1100, height: 310 },
    { id: "viz-chart-9", file: "combined_gender_stem.json", width: 1100, height: 310 }
  ];

  if (typeof vegaEmbed === "undefined") {
    charts.forEach((c) => {
      const el = document.getElementById(c.id);
      if (el) showPlaceholder(el, c.file);
    });
    return;
  }

  const vegaOpts = {
    theme: "dark",
    actions: false,
    renderer: "svg",
    config: {
      background: "transparent",
      view: { stroke: "transparent" },
      axis: {
        domainColor: "#4a5568",
        gridColor: "#2d3748",
        tickColor: "#4a5568",
        labelColor: "#9aa3b5",
        titleColor: "#f4f6fb"
      },
      legend: { labelColor: "#9aa3b5", titleColor: "#f4f6fb" },
      title: { color: "#f4f6fb" }
    }
  };

  charts.forEach((c) => {
    const el = document.getElementById(c.id);
    if (!el) return;

    el.innerHTML = "<div class=\"loading-spinner\"></div>";

    fetch(basePath + c.file)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((spec) => {
        el.innerHTML = "";

        function setLargerDimensions(obj, targetWidth, targetHeight) {
          if (!obj || typeof obj !== "object") return;
          if (Array.isArray(obj)) {
            obj.forEach(item => setLargerDimensions(item, targetWidth, targetHeight));
            return;
          }
          if (obj.hasOwnProperty("width") || obj.hasOwnProperty("height") || obj.mark || obj.layer) {
            obj.width = targetWidth;
            obj.height = targetHeight;
          }
          if (obj.hconcat && Array.isArray(obj.hconcat)) {
            const chartWidth = Math.floor(targetWidth / obj.hconcat.length) - 20;
            obj.hconcat.forEach(chart => {
              chart.width = chartWidth;
              chart.height = targetHeight;
              setLargerDimensions(chart, chartWidth, targetHeight);
            });
          }
          if (obj.vconcat && Array.isArray(obj.vconcat)) {
            const chartHeight = Math.floor(targetHeight / obj.vconcat.length) - 20;
            obj.vconcat.forEach(chart => {
              chart.width = targetWidth;
              chart.height = chartHeight;
              setLargerDimensions(chart, targetWidth, chartHeight);
            });
          }
          if (obj.layer) {
            obj.layer.forEach(layer => setLargerDimensions(layer, targetWidth, targetHeight));
          }
          if (obj.spec) {
            setLargerDimensions(obj.spec, targetWidth, targetHeight);
          }
        }

        const cleanSpec = JSON.parse(JSON.stringify(spec));
        delete cleanSpec.autosize;

        setLargerDimensions(cleanSpec, c.width, c.height);

        const specWithFit = Object.assign({}, cleanSpec, {
          autosize: { type: "fit", contains: "padding", resize: true },
        });

        vegaEmbed(`#${c.id}`, specWithFit, vegaOpts).catch(() => showPlaceholder(el, c.file));
      })
      .catch(() => showPlaceholder(el, c.file));
  });
}

function showPlaceholder(el, file) {
  el.innerHTML = `
    <div style="text-align:center;color:#9aa3b5;padding:40px;">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48" style="margin-bottom:12px;opacity:0.5;">
        <path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>
      </svg>
      <p style="font-size:1rem;margin-bottom:8px;">Visualization</p>
      <p style="font-size:0.75rem;opacity:0.6;">${file}</p>
    </div>
  `;
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function smoothScrollTo(element, targetX, duration) {
  const startX = element.scrollLeft;
  const distance = targetX - startX;
  const startTime = performance.now();

  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease = easeInOutCubic(progress);

    element.scrollLeft = startX + distance * ease;

    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      element.scrollLeft = targetX;
    }
  }

  requestAnimationFrame(step);
}

function scrollToPanel(index) {
  const clampedIndex = clampIndex(index);
  const target = panels[clampedIndex];
  if (!target) return;

  smoothScrollTo(scrollContainer, target.offsetLeft, 800);

  currentIndex = clampedIndex;
  updateActiveStates(clampedIndex);

  const panelInner = target.querySelector(".panel-inner");
  if (panelInner) panelInner.scrollTop = 0;

  if (topNav) topNav.classList.remove("visible");
  checkNavbarVisibility();
}

function clampIndex(index) {
  return Math.max(0, Math.min(panels.length - 1, index));
}

function lockTransition() {
  isTransitioning = true;
  clearTimeout(transitionTimeout);
  transitionTimeout = setTimeout(() => {
    isTransitioning = false;
  }, 850);
}

function goToPanel(index) {
  const nextIndex = clampIndex(index);
  if (nextIndex === currentIndex || isTransitioning) return;

  const now = Date.now();
  if (now - lastNavTime < MIN_NAV_GAP) return;
  lastNavTime = now;

  const currentSection = getTabGroupForPanel(currentIndex);
  const targetSection = getTabGroupForPanel(nextIndex);

  if (currentSection !== targetSection) {
    activeTabGroup = targetSection;
    filterPanelsByTab(targetSection);

    const sidebarTabs = document.querySelectorAll(".sidebar-tab");
    sidebarTabs.forEach(t => {
      t.classList.toggle("active", parseInt(t.dataset.tab) === targetSection);
    });
  }

  scrollToPanel(nextIndex);
  lockTransition();
  updateActiveStates(nextIndex);
  checkNavbarVisibility();
}

function updateActiveStates(index) {
  document.querySelectorAll(".nav-links button").forEach((btn, i) => {
    btn.classList.toggle("active", i === index);
  });
  progressDots.forEach((dot, i) => {
    dot.classList.toggle("active", i === index);
  });
  syncSidebarWithPanel(index);
}

function initNavigation() {
  navButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const index = parseInt(btn.dataset.target);
      if (!Number.isNaN(index)) goToPanel(index);
    });
  });
}

function initKeyboard() {
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    if (e.key === "ArrowRight") {
      e.preventDefault();
      goToPanel(currentIndex + 1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      goToPanel(currentIndex - 1);
    }
  });
}

function initScrollHandling() {
  document.addEventListener("wheel", (e) => {
    if (Math.abs(e.deltaX) > Math.abs(e.deltaY) && Math.abs(e.deltaX) > 5) {
      e.preventDefault();
    }
  }, { passive: false });

  panels.forEach((panel, panelIndex) => {
    const panelInner = panel.querySelector(".panel-inner");
    if (!panelInner) return;

    panelInner.addEventListener("wheel", (e) => {
      if (isTransitioning) return;

      const deltaY = e.deltaY;
      const atTop = panelInner.scrollTop <= 0;
      const atBottom = panelInner.scrollTop + panelInner.clientHeight >= panelInner.scrollHeight - 1;

      if (Math.abs(deltaY) > Math.abs(e.deltaX) && ((deltaY > 0 && atBottom) || (deltaY < 0 && atTop))) {
        const now = Date.now();
        if (now - lastNavTime >= MIN_NAV_GAP) {
          e.preventDefault();
          e.stopPropagation();
          goToPanel(panelIndex + (deltaY > 0 ? 1 : -1));
        }
      }
    }, { passive: false });
  });

  scrollContainer.addEventListener("wheel", (e) => {
    if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
      e.preventDefault();

      if (isTransitioning) return;

      if (Math.abs(e.deltaX) > SWIPE_THRESHOLD) {
        if (e.deltaX > 0) {
          goToPanel(currentIndex + 1);
        } else {
          goToPanel(currentIndex - 1);
        }
      }
    }
  }, { passive: false });

  scrollContainer.addEventListener("scroll", () => requestAnimationFrame(handleScroll));
}

function handleScroll() {
  if (isTransitioning) return;
  const viewportCenter = window.innerWidth / 2;
  let closestIndex = currentIndex;
  let closestDistance = Number.POSITIVE_INFINITY;

  panels.forEach((panel, idx) => {
    const rect = panel.getBoundingClientRect();
    const panelCenter = rect.left + rect.width / 2;
    const distance = Math.abs(panelCenter - viewportCenter);
    if (distance < closestDistance) {
      closestDistance = distance;
      closestIndex = idx;
    }
    if (rect.left < window.innerWidth * 0.75 && rect.right > window.innerWidth * 0.25) {
      panel.classList.add("visible");
    }
  });

  if (closestIndex !== currentIndex) {
    currentIndex = closestIndex;
    updateActiveStates(currentIndex);
    checkNavbarVisibility();
  }
}

function initTouch() {
  let startX = 0;
  let startY = 0;

  document.addEventListener("touchstart", (e) => {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
  }, { passive: false });

  document.addEventListener("touchmove", (e) => {
    const currentX = e.touches[0].clientX;
    const currentY = e.touches[0].clientY;
    const diffX = currentX - startX;
    const diffY = currentY - startY;

    if (Math.abs(diffX) > Math.abs(diffY)) {
      e.preventDefault();
    }
  }, { passive: false });

  document.addEventListener("touchend", (e) => {
    const endX = e.changedTouches[0].clientX;
    const endY = e.changedTouches[0].clientY;

    const diffX = endX - startX;
    const diffY = endY - startY;

    if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > TOUCH_THRESHOLD) {
      if (diffX < 0) {
        goToPanel(currentIndex + 1);
      } else {
        goToPanel(currentIndex - 1);
      }
    }
  }, { passive: true });
}

function initResize() {
  let timeout;
  window.addEventListener("resize", () => {
    clearTimeout(timeout);
    timeout = setTimeout(() => scrollToPanel(currentIndex), 200);
  });
}

function init() {
  initParticles();
  initNavigation();
  initKeyboard();
  initScrollHandling();
  initTouch();
  initResize();
  initNavbarVisibility();
  initVisualizations();
  initSidebar();

  updateActiveStates(0);
  panels.forEach((p) => p.classList.add("visible"));
  checkNavbarVisibility();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
