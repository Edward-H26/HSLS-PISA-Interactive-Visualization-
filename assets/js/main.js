const TRANSITION_LOCK_MS = 850;
const MIN_NAV_GAP = 900;
const SWIPE_THRESHOLD = 30;
const TOUCH_THRESHOLD = 50;
const MOBILE_BREAKPOINT = 980;
const CHART_ASSET_VERSION = "2";

const PANEL_GROUPS = {
  0: [0, 1, 2, 3],
  1: [4, 5, 6],
  2: [7, 8, 9],
  3: [10, 11, 12],
};

const PANEL_LABELS = {
  0: "Introduction",
  1: "Conclusion",
  2: "HSLS:09 Dataset",
  3: "PISA 2022 Dataset",
  4: "Family & STEM",
  5: "Digital & Immigration",
  6: "Internet & Gender",
  7: "Regional STEM",
  8: "SES & Efficacy",
  9: "Tech & Interest",
  10: "Anxiety & Belonging",
  11: "Regional Achievement",
  12: "Belonging & Outcomes",
};

const CHARTS = [
  { id: "viz-chart-1", file: "hsls_math_identity_race.json", width: 930, height: 450, minHeight: 300 },
  { id: "viz-chart-2", file: "combined_immigration.json", width: 1060, height: 500, minHeight: 320 },
  { id: "viz-chart-3", file: "pisa_gender_efficacy_dumbbell.json", width: 930, height: 470, minHeight: 300 },
  { id: "viz-chart-4", file: "hsls_gpa_ses_trajectory.json", width: 960, height: 420, minHeight: 300 },
  { id: "viz-chart-5", file: "combined_ses_achievement.json", width: 620, height: 280, minHeight: 260 },
  { id: "viz-chart-6", file: "combined_parent_education.json", width: 900, height: 420, minHeight: 280 },
  { id: "viz-chart-7", file: "pisa_anxiety_performance_heatmap.json", width: 900, height: 440, minHeight: 300 },
  { id: "viz-chart-8", file: "combined_efficacy_comparison.json", width: 680, height: 320, minHeight: 260 },
  { id: "viz-chart-9", file: "combined_gender_stem.json", width: 900, height: 430, minHeight: 300 },
];

const scrollContainer = document.getElementById("scroll-container");
const panels = Array.from(document.querySelectorAll(".panel"));
const navButtons = Array.from(document.querySelectorAll("[data-target]"));
const progressDots = Array.from(document.querySelectorAll(".progress-dot"));
const topNav = document.getElementById("top-nav");
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebar-toggle");
const progressIndicator = document.querySelector(".progress-indicator");
const sidebarTabs = Array.from(document.querySelectorAll(".sidebar-tab"));
const panelInners = Array.from(document.querySelectorAll(".panel-inner"));
const navLinkButtons = Array.from(document.querySelectorAll(".nav-links button"));

let currentIndex = 0;
let activeTabGroup = 0;
let isTransitioning = false;
let transitionTimeout = null;
let lastNavTime = 0;
let touchStartX = 0;
let touchStartY = 0;
let resizeTimeout = null;

function parseIndex(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

function isMobileLayout() {
  return window.innerWidth <= MOBILE_BREAKPOINT;
}

function setSidebarOpen(isOpen) {
  document.body.classList.toggle("sidebar-open", isOpen);
  if (sidebarToggle) {
    sidebarToggle.setAttribute("aria-expanded", String(isOpen));
  }
}

function closeSidebar() {
  if (isMobileLayout()) {
    setSidebarOpen(false);
  }
}

function getTabGroupForPanel(panelIndex) {
  for (const [tabId, indices] of Object.entries(PANEL_GROUPS)) {
    if (indices.includes(panelIndex)) {
      return Number.parseInt(tabId, 10);
    }
  }

  return 0;
}

function getNextPanelInGroup(panelIndex, direction) {
  const groupPanels = PANEL_GROUPS[activeTabGroup] ?? PANEL_GROUPS[0];
  const currentPosition = groupPanels.indexOf(panelIndex);

  if (currentPosition === -1) {
    return groupPanels[0];
  }

  const nextPosition = currentPosition + direction;
  if (nextPosition >= 0 && nextPosition < groupPanels.length) {
    return groupPanels[nextPosition];
  }

  const orderedGroups = Object.keys(PANEL_GROUPS).map(Number).sort((a, b) => a - b);
  const groupPosition = orderedGroups.indexOf(activeTabGroup);

  if (direction > 0 && groupPosition < orderedGroups.length - 1) {
    const nextGroup = orderedGroups[groupPosition + 1];
    return PANEL_GROUPS[nextGroup][0];
  }

  if (direction < 0 && groupPosition > 0) {
    const previousGroup = orderedGroups[groupPosition - 1];
    const previousPanels = PANEL_GROUPS[previousGroup];
    return previousPanels[previousPanels.length - 1];
  }

  return panelIndex;
}

function updateTopNavLabels(tabId) {
  const visibleIndices = PANEL_GROUPS[tabId] ?? PANEL_GROUPS[0];

  navLinkButtons.forEach((button) => {
    const targetIndex = parseIndex(button.dataset.target);
    if (targetIndex === null) {
      return;
    }

    const isVisible = visibleIndices.includes(targetIndex);
    button.hidden = !isVisible;

    if (isVisible) {
      button.textContent = PANEL_LABELS[targetIndex] ?? `Panel ${targetIndex + 1}`;
    }
  });
}

function filterPanelsByTab(tabId) {
  const visibleIndices = PANEL_GROUPS[tabId] ?? PANEL_GROUPS[0];

  panels.forEach((panel, panelIndex) => {
    panel.classList.toggle("filtered-out", !visibleIndices.includes(panelIndex));
  });

  progressDots.forEach((dot) => {
    const dotTarget = parseIndex(dot.dataset.target);
    dot.hidden = dotTarget === null ? true : !visibleIndices.includes(dotTarget);
  });

  updateTopNavLabels(tabId);
}

function syncSidebarWithPanel(panelIndex) {
  const nextTabGroup = getTabGroupForPanel(panelIndex);
  activeTabGroup = nextTabGroup;

  sidebarTabs.forEach((tab) => {
    const tabIndex = parseIndex(tab.dataset.tab);
    tab.classList.toggle("active", tabIndex === nextTabGroup);
  });

  filterPanelsByTab(nextTabGroup);
}

function clampIndex(index) {
  return Math.max(0, Math.min(panels.length - 1, index));
}

function easeInOutCubic(progress) {
  return progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
}

function smoothScrollTo(element, targetX, duration) {
  const startX = element.scrollLeft;
  const distance = targetX - startX;
  const startTime = performance.now();

  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easedProgress = easeInOutCubic(progress);
    element.scrollLeft = startX + distance * easedProgress;

    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      element.scrollLeft = targetX;
    }
  }

  requestAnimationFrame(step);
}

function showTopNav(shouldShow) {
  if (!topNav) {
    return;
  }

  topNav.classList.toggle("visible", shouldShow);
  document.body.classList.toggle("nav-visible", shouldShow);
}

function checkNavbarVisibility() {
  const currentPanel = panels[currentIndex];
  const currentPanelInner = currentPanel?.querySelector(".panel-inner");
  const maxScroll = currentPanelInner ? currentPanelInner.scrollHeight - currentPanelInner.clientHeight : 0;
  const isAtTop = !currentPanelInner || currentPanelInner.scrollTop < 48;
  const isAtBottom = Boolean(currentPanelInner && maxScroll > 0 && currentPanelInner.scrollTop >= maxScroll - 48);

  showTopNav(isAtTop);

  if (progressIndicator) {
    progressIndicator.classList.toggle("visible", isAtBottom);
  }
}

function updateActiveStates(panelIndex) {
  navLinkButtons.forEach((button) => {
    const targetIndex = parseIndex(button.dataset.target);
    button.classList.toggle("active", targetIndex === panelIndex);
  });

  progressDots.forEach((dot) => {
    const targetIndex = parseIndex(dot.dataset.target);
    dot.classList.toggle("active", targetIndex === panelIndex);
  });

  syncSidebarWithPanel(panelIndex);
}

function scrollToPanel(panelIndex) {
  const nextIndex = clampIndex(panelIndex);
  const targetPanel = panels[nextIndex];

  if (!targetPanel || !scrollContainer) {
    return;
  }

  smoothScrollTo(scrollContainer, targetPanel.offsetLeft, 800);
  currentIndex = nextIndex;

  const panelInner = targetPanel.querySelector(".panel-inner");
  if (panelInner) {
    panelInner.scrollTop = 0;
  }

  updateActiveStates(nextIndex);
  checkNavbarVisibility();
}

function lockTransition() {
  isTransitioning = true;
  window.clearTimeout(transitionTimeout);
  transitionTimeout = window.setTimeout(() => {
    isTransitioning = false;
  }, TRANSITION_LOCK_MS);
}

function goToPanel(panelIndex) {
  const nextIndex = clampIndex(panelIndex);
  if (nextIndex === currentIndex || isTransitioning) {
    return;
  }

  const now = Date.now();
  if (now - lastNavTime < MIN_NAV_GAP) {
    return;
  }

  lastNavTime = now;
  activeTabGroup = getTabGroupForPanel(nextIndex);
  filterPanelsByTab(activeTabGroup);
  scrollToPanel(nextIndex);
  lockTransition();
  closeSidebar();
}

function handleScroll() {
  if (isTransitioning) {
    return;
  }

  const viewportCenter = window.innerWidth / 2;
  let closestIndex = currentIndex;
  let closestDistance = Number.POSITIVE_INFINITY;

  panels.forEach((panel, panelIndex) => {
    const panelRect = panel.getBoundingClientRect();
    const panelCenter = panelRect.left + panelRect.width / 2;
    const distance = Math.abs(panelCenter - viewportCenter);

    if (distance < closestDistance) {
      closestDistance = distance;
      closestIndex = panelIndex;
    }

    if (panelRect.left < window.innerWidth * 0.75 && panelRect.right > window.innerWidth * 0.25) {
      panel.classList.add("visible");
    }
  });

  if (closestIndex !== currentIndex) {
    currentIndex = closestIndex;
    updateActiveStates(currentIndex);
    checkNavbarVisibility();
  }
}

function initSidebar() {
  sidebarTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const tabId = parseIndex(tab.dataset.tab);
      if (tabId === null) {
        return;
      }

      activeTabGroup = tabId;
      filterPanelsByTab(tabId);
      scrollToPanel(PANEL_GROUPS[tabId][0]);
      closeSidebar();
    });
  });

  filterPanelsByTab(activeTabGroup);
}

function initSidebarToggle() {
  if (!sidebarToggle || !sidebar) {
    return;
  }

  sidebarToggle.addEventListener("click", () => {
    const shouldOpen = !document.body.classList.contains("sidebar-open");
    setSidebarOpen(shouldOpen);
  });

  document.addEventListener("click", (event) => {
    if (!isMobileLayout() || !document.body.classList.contains("sidebar-open")) {
      return;
    }

    const target = event.target;
    if (!(target instanceof Node)) {
      return;
    }

    if (!sidebar.contains(target) && !sidebarToggle.contains(target)) {
      setSidebarOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setSidebarOpen(false);
    }
  });
}

function initNavigation() {
  navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const targetIndex = parseIndex(button.dataset.target);
      if (targetIndex !== null) {
        goToPanel(targetIndex);
      }
    });
  });
}

function initKeyboard() {
  document.addEventListener("keydown", (event) => {
    const targetTag = event.target?.tagName;
    if (targetTag === "INPUT" || targetTag === "TEXTAREA") {
      return;
    }

    if (event.key === "ArrowRight") {
      event.preventDefault();
      goToPanel(getNextPanelInGroup(currentIndex, 1));
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      goToPanel(getNextPanelInGroup(currentIndex, -1));
    }
  });
}

function initScrollHandling() {
  document.addEventListener("wheel", (event) => {
    if (Math.abs(event.deltaX) > Math.abs(event.deltaY) && Math.abs(event.deltaX) > 5) {
      event.preventDefault();
    }
  }, { passive: false });

  panels.forEach((panel, panelIndex) => {
    const panelInner = panel.querySelector(".panel-inner");
    if (!panelInner) {
      return;
    }

    panelInner.addEventListener("wheel", (event) => {
      if (isTransitioning) {
        return;
      }

      const atTop = panelInner.scrollTop <= 0;
      const atBottom = panelInner.scrollTop + panelInner.clientHeight >= panelInner.scrollHeight - 1;
      const isVerticalIntent = Math.abs(event.deltaY) > Math.abs(event.deltaX);
      const shouldAdvance = (event.deltaY > 0 && atBottom) || (event.deltaY < 0 && atTop);

      if (isVerticalIntent && shouldAdvance) {
        const now = Date.now();
        if (now - lastNavTime >= MIN_NAV_GAP) {
          event.preventDefault();
          event.stopPropagation();
          goToPanel(getNextPanelInGroup(panelIndex, event.deltaY > 0 ? 1 : -1));
        }
      }
    }, { passive: false });
  });

  scrollContainer?.addEventListener("wheel", (event) => {
    if (Math.abs(event.deltaX) <= Math.abs(event.deltaY)) {
      return;
    }

    event.preventDefault();
    if (isTransitioning || Math.abs(event.deltaX) <= SWIPE_THRESHOLD) {
      return;
    }

    goToPanel(getNextPanelInGroup(currentIndex, event.deltaX > 0 ? 1 : -1));
  }, { passive: false });

  scrollContainer?.addEventListener("scroll", () => {
    requestAnimationFrame(handleScroll);
  });
}

function initTouch() {
  document.addEventListener("touchstart", (event) => {
    touchStartX = event.touches[0].clientX;
    touchStartY = event.touches[0].clientY;
  }, { passive: false });

  document.addEventListener("touchmove", (event) => {
    const currentX = event.touches[0].clientX;
    const currentY = event.touches[0].clientY;
    const diffX = currentX - touchStartX;
    const diffY = currentY - touchStartY;

    if (Math.abs(diffX) > Math.abs(diffY)) {
      event.preventDefault();
    }
  }, { passive: false });

  document.addEventListener("touchend", (event) => {
    const endX = event.changedTouches[0].clientX;
    const endY = event.changedTouches[0].clientY;
    const diffX = endX - touchStartX;
    const diffY = endY - touchStartY;

    if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > TOUCH_THRESHOLD) {
      goToPanel(getNextPanelInGroup(currentIndex, diffX < 0 ? 1 : -1));
    }
  }, { passive: true });
}

function parseNumeric(value) {
  const parsed = Number.parseFloat(value ?? "");
  return Number.isFinite(parsed) ? parsed : null;
}

function updateChartFrame(chart, width, height) {
  const element = document.getElementById(chart.id);
  const frame = element?.closest(".viz-chart-container");
  if (!frame) {
    return;
  }

  const naturalWidth = width ?? chart.width;
  const naturalHeight = height ?? chart.height;
  const horizontalChrome = window.innerWidth <= 768 ? 28 : 40;
  const availableWidth = Math.max(240, frame.clientWidth - horizontalChrome);
  const scale = Math.min(1, availableWidth / naturalWidth);
  const targetHeight = Math.max(chart.minHeight, Math.round(naturalHeight * scale));

  frame.style.setProperty("--chart-height", `${targetHeight}px`);
}

function makeEmbeddedSvgResponsive(chart, element) {
  const svg = element.querySelector("svg");
  if (!svg) {
    updateChartFrame(chart, chart.width, chart.height);
    return;
  }

  const width = parseNumeric(svg.getAttribute("width")) ?? chart.width;
  const height = parseNumeric(svg.getAttribute("height")) ?? chart.height;

  if (!svg.getAttribute("viewBox")) {
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  }

  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  svg.removeAttribute("width");
  svg.removeAttribute("height");
  svg.dataset.chartWidth = String(width);
  svg.dataset.chartHeight = String(height);

  updateChartFrame(chart, width, height);
}

function updateRenderedChartFrames() {
  CHARTS.forEach((chart) => {
    const element = document.getElementById(chart.id);
    const svg = element?.querySelector("svg");
    const width = parseNumeric(svg?.dataset.chartWidth);
    const height = parseNumeric(svg?.dataset.chartHeight);
    updateChartFrame(chart, width, height);
  });
}

function showPlaceholder(element, chart) {
  element.innerHTML = `
    <div style="text-align:center;color:#9aa3b5;padding:40px;">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48" style="margin-bottom:12px;opacity:0.5;">
        <path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>
      </svg>
      <p style="font-size:1rem;margin-bottom:8px;">Visualization</p>
      <p style="font-size:0.75rem;opacity:0.6;">${chart.file}</p>
    </div>
  `;

  updateChartFrame(chart, chart.width, chart.height);
}

async function renderChart(chart) {
  const element = document.getElementById(chart.id);
  if (!element) {
    return;
  }

  element.innerHTML = "<div class=\"loading-spinner\"></div>";

  try {
    const response = await fetch(`assets/json/${chart.file}?v=${CHART_ASSET_VERSION}`);
    if (!response.ok) {
      throw new Error(`Unable to load ${chart.file}`);
    }

    const rawSpec = await response.json();
    const spec = JSON.parse(JSON.stringify(rawSpec));
    delete spec.autosize;

    await vegaEmbed(`#${chart.id}`, spec, {
      theme: "dark",
      actions: false,
      renderer: "svg",
    });

    makeEmbeddedSvgResponsive(chart, element);
  } catch (_error) {
    showPlaceholder(element, chart);
  }
}

function initVisualizations() {
  if (typeof vegaEmbed === "undefined") {
    CHARTS.forEach((chart) => {
      const element = document.getElementById(chart.id);
      if (element) {
        showPlaceholder(element, chart);
      }
    });
    return;
  }

  CHARTS.forEach((chart) => {
    void renderChart(chart);
  });
}

function initParticles() {
  const container = document.getElementById("particles");
  if (!container) {
    return;
  }

  for (let particleIndex = 0; particleIndex < 25; particleIndex += 1) {
    const particle = document.createElement("div");
    particle.className = "particle";
    particle.style.left = `${Math.random() * 100}%`;
    particle.style.animationDuration = `${Math.random() * 6 + 5}s`;
    particle.style.animationDelay = `${Math.random() * 8}s`;
    particle.style.opacity = String(Math.random() * 0.4 + 0.2);

    const colors = [
      "rgba(76, 141, 255, 0.6)",
      "rgba(168, 85, 247, 0.6)",
      "rgba(34, 211, 238, 0.5)",
      "rgba(255, 255, 255, 0.4)",
    ];

    particle.style.background = colors[Math.floor(Math.random() * colors.length)];
    container.appendChild(particle);
  }
}

function initNavbarVisibility() {
  panelInners.forEach((panelInner) => {
    panelInner.addEventListener("scroll", checkNavbarVisibility);
  });

  checkNavbarVisibility();
}

function initResize() {
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimeout);
    resizeTimeout = window.setTimeout(() => {
      if (!isMobileLayout()) {
        setSidebarOpen(false);
      }

      scrollToPanel(currentIndex);
      updateRenderedChartFrames();
    }, 180);
  });
}

function init() {
  initParticles();
  initSidebar();
  initSidebarToggle();
  initNavigation();
  initKeyboard();
  initScrollHandling();
  initTouch();
  initResize();
  initNavbarVisibility();
  initVisualizations();

  updateActiveStates(currentIndex);
  panels.forEach((panel) => {
    panel.classList.add("visible");
  });
  updateRenderedChartFrames();
  checkNavbarVisibility();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
