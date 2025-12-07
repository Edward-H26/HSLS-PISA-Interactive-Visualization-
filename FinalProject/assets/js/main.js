let currentIndex = 0;
const totalPanels = 9;
const TRANSITION_LOCK_MS = 700;
const HORIZONTAL_DOMINANCE = 1.25;

const scrollContainer = document.getElementById("scroll-container");
const panels = Array.from(document.querySelectorAll(".panel"));
const navButtons = Array.from(document.querySelectorAll("[data-target]"));
const progressDots = Array.from(document.querySelectorAll(".progress-dot"));
const topNav = document.getElementById("top-nav");
const progressIndicator = document.querySelector(".progress-indicator");
let isTransitioning = false;
let transitionTimeout = null;

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
  const atBottom = !panelInner || maxScroll <= 0 || panelInner.scrollTop >= maxScroll - 50;

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
  const basePath = "../assets/json/";

  const charts = [
    { id: "viz-chart-1", file: "pisa_gender_efficacy_dumbbell.json" },
    { id: "viz-chart-2", file: "pisa_anxiety_performance_heatmap.json" },
    { id: "viz-chart-3", file: "combined_immigration.json" },
    { id: "viz-chart-4", file: "combined_gender_stem.json" },
    { id: "viz-chart-5", file: "hsls_math_identity_race.json" },
    { id: "viz-chart-6", file: "hsls_gpa_ses_trajectory.json" },
    { id: "viz-chart-7", file: "combined_efficacy_comparison.json" },
    { id: "viz-chart-8", file: "combined_ses_achievement.json" },
    { id: "viz-chart-9", file: "combined_parent_education.json" }
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
        const specWithFit = Object.assign({}, spec, {
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

function scrollToPanel(index) {
  const clampedIndex = clampIndex(index);
  const target = panels[clampedIndex];
  if (!target) return;

  scrollContainer.scrollTo({ left: target.offsetLeft, behavior: "smooth" });
  currentIndex = clampedIndex;
  updateActiveStates(clampedIndex);

  const panelInner = target.querySelector(".panel-inner");
  if (panelInner) panelInner.scrollTop = 0;

  if (topNav) topNav.classList.remove("visible");
  checkNavbarVisibility();
}

function clampIndex(index) {
  return Math.max(0, Math.min(totalPanels - 1, index));
}

function lockTransition() {
  isTransitioning = true;
  clearTimeout(transitionTimeout);
  transitionTimeout = setTimeout(() => {
    isTransitioning = false;
  }, TRANSITION_LOCK_MS);
}

function goToPanel(index) {
  const nextIndex = clampIndex(index);
  if (nextIndex === currentIndex || isTransitioning) return;
  scrollToPanel(nextIndex);
  lockTransition();
}

function updateActiveStates(index) {
  document.querySelectorAll(".nav-links button").forEach((btn, i) => {
    btn.classList.toggle("active", i === index);
  });
  progressDots.forEach((dot, i) => {
    dot.classList.toggle("active", i === index);
  });
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
  panels.forEach((panel, panelIndex) => {
    const panelInner = panel.querySelector(".panel-inner");
    if (!panelInner) return;

    panelInner.addEventListener("wheel", (e) => {
      const deltaY = e.deltaY;
      const atTop = panelInner.scrollTop <= 0;
      const atBottom = panelInner.scrollTop + panelInner.clientHeight >= panelInner.scrollHeight - 1;

      if ((deltaY > 0 && atBottom) || (deltaY < 0 && atTop)) {
        e.preventDefault();
        e.stopPropagation();
        goToPanel(panelIndex + (deltaY > 0 ? 1 : -1));
      }
    }, { passive: false });
  });

  scrollContainer.addEventListener("wheel", (e) => {
    if (isTransitioning || e.defaultPrevented) {
      e.preventDefault();
      return;
    }

    if (e.target.closest(".panel-inner")) return;

    const absX = Math.abs(e.deltaX);
    const absY = Math.abs(e.deltaY);
    const isHorizontal = absX > absY * HORIZONTAL_DOMINANCE;
    const primaryDelta = isHorizontal ? e.deltaX : e.deltaY;
    const threshold = 20;
    if ((isHorizontal && absX < threshold) || (!isHorizontal && absY < threshold)) return;

    e.preventDefault();
    // Direction: horizontal positive -> previous, horizontal negative -> next.
    // Vertical down (positive) -> next, up (negative) -> previous.
    const direction = isHorizontal
      ? (primaryDelta > 0 ? -1 : 1)
      : (primaryDelta > 0 ? 1 : -1);
    goToPanel(currentIndex + direction);
  }, { passive: false });

  scrollContainer.addEventListener("scroll", () => requestAnimationFrame(handleScroll));
}

function handleScroll() {
  const scrollLeft = scrollContainer.scrollLeft;
  const panelWidth = window.innerWidth;
  const newIndex = Math.round(scrollLeft / panelWidth);

  if (newIndex !== currentIndex && newIndex >= 0 && newIndex < totalPanels) {
    currentIndex = newIndex;
    updateActiveStates(currentIndex);
    if (topNav) topNav.classList.remove("visible");
    checkNavbarVisibility();
  }

  panels.forEach((panel) => {
    const rect = panel.getBoundingClientRect();
    if (rect.left < window.innerWidth * 0.75 && rect.right > window.innerWidth * 0.25) {
      panel.classList.add("visible");
    }
  });
}

function initTouch() {
  let startX = 0;
  let startY = 0;
  let startTime = 0;
  let isScrolling = false;
  let touchStartPanelInner = null;

  document.addEventListener("touchstart", (e) => {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    startTime = Date.now();
    isScrolling = false;
    touchStartPanelInner = e.target.closest(".panel-inner");
  }, { passive: true });

  document.addEventListener("touchmove", (e) => {
    if (!startX || !startY) return;

    const deltaY = Math.abs(e.touches[0].clientY - startY);
    if (touchStartPanelInner) {
      const panelInner = e.target.closest(".panel-inner");
      if (panelInner === touchStartPanelInner && deltaY > 5) {
        isScrolling = true;
      }
    }
  }, { passive: true });

  document.addEventListener("touchend", (e) => {
    if (!startX || !startY) return;

    const endX = e.changedTouches[0].clientX;
    const endY = e.changedTouches[0].clientY;
    const deltaX = endX - startX;
    const deltaY = endY - startY;
    const deltaTime = Date.now() - startTime;

    const wasScrolling = isScrolling;
    startX = 0;
    startY = 0;
    isScrolling = false;
    touchStartPanelInner = null;

    if (wasScrolling) return;

    const minSwipeDistance = 50;
    const maxSwipeTime = 500;

    const isHorizontalSwipe = Math.abs(deltaX) > Math.abs(deltaY);
    const isFastEnough = Math.abs(deltaX) >= minSwipeDistance;
    const isQuickEnough = deltaTime <= maxSwipeTime;

    if (isHorizontalSwipe && isFastEnough && isQuickEnough) {
      e.preventDefault();
      goToPanel(deltaX < 0 ? currentIndex + 1 : currentIndex - 1);
    }
  }, { passive: false });
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

  updateActiveStates(0);
  panels.forEach((p) => p.classList.add("visible"));
  checkNavbarVisibility();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
