let currentIndex = 0;
const TRANSITION_LOCK_MS = 850;
const MIN_NAV_GAP = 900; // Debounce for navigation
const SWIPE_THRESHOLD = 30; // Min delta to trigger swipe
const TOUCH_THRESHOLD = 50; // Min px to trigger touch swipe

// DOM Elements
const scrollContainer = document.getElementById("scroll-container");
const panels = Array.from(document.querySelectorAll(".panel"));
const navButtons = Array.from(document.querySelectorAll("[data-target]"));
const progressDots = Array.from(document.querySelectorAll(".progress-dot"));
const topNav = document.getElementById("top-nav");
const progressIndicator = document.querySelector(".progress-indicator");

// State
let isTransitioning = false;
let transitionTimeout = null;
let lastNavTime = 0;

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

  // Use optional chaining and defaults
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
        
        // Helper to recursively remove fixed dimensions
        function removeFixedDimensions(obj) {
          if (!obj || typeof obj !== 'object') return;
          if (Array.isArray(obj)) {
            obj.forEach(removeFixedDimensions);
            return;
          }
          delete obj.width;
          delete obj.height;
          // Recurse into common nesting properties
          ['layer', 'hconcat', 'vconcat', 'spec'].forEach(prop => {
            if (obj[prop]) removeFixedDimensions(obj[prop]);
          });
        }
        
        // Clone spec to avoid mutating original if cached (though we fetch fresh)
        const cleanSpec = JSON.parse(JSON.stringify(spec));
        removeFixedDimensions(cleanSpec);
        delete cleanSpec.autosize;

        const specWithFit = Object.assign({}, cleanSpec, {
          width: "container",
          // height: "container", // Enabling this makes it try to fill vertical space too
          // given the "did not fit perfectly" complaint, filling the box is safest.
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
       // Ensure we land exactly on target
       element.scrollLeft = targetX;
    }
  }

  requestAnimationFrame(step);
}

function scrollToPanel(index) {
  const clampedIndex = clampIndex(index);
  const target = panels[clampedIndex];
  if (!target) return;

  // Custom smooth scroll for consistency and "premium" feel
  smoothScrollTo(scrollContainer, target.offsetLeft, 800);
  
  currentIndex = clampedIndex;
  updateActiveStates(clampedIndex);

  // Reset scroll of the target panel content to top
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
  // Lock for slightly longer than the animation to prevent rapid-fire overlaps
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
  // Handle Vertical Scrolling to trigger panel changes at edges
  panels.forEach((panel, panelIndex) => {
    const panelInner = panel.querySelector(".panel-inner");
    if (!panelInner) return;

    panelInner.addEventListener("wheel", (e) => {
      if (isTransitioning) return;
      
      const deltaY = e.deltaY;
      const atTop = panelInner.scrollTop <= 0;
      const atBottom = panelInner.scrollTop + panelInner.clientHeight >= panelInner.scrollHeight - 1;

      // Only trigger if purely vertical scroll and at edges
      if (Math.abs(deltaY) > Math.abs(e.deltaX) && ((deltaY > 0 && atBottom) || (deltaY < 0 && atTop))) {
        // Debounce handled in goToPanel
        // deltaY > 0 (Scroll Down) -> Next Panel
        // deltaY < 0 (Scroll Up) -> Prev Panel
        
        // Prevent default only if we are actually going to navigate
        // We check time here to avoid preventing default if we are in cooldown
        const now = Date.now();
        if (now - lastNavTime >= MIN_NAV_GAP) {
           e.preventDefault();
           e.stopPropagation();
           goToPanel(panelIndex + (deltaY > 0 ? 1 : -1));
        }
      }
    }, { passive: false });
  });

  // Handle Horizontal Swipe on Container
  scrollContainer.addEventListener("wheel", (e) => {
    // Check if it's a horizontal swipe
    if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
      // ALWAYS prevent default for horizontal swipes to block browser history navigation,
      // even if we are currently transitioning or the threshold isn't met.
      e.preventDefault(); 
      
      if (isTransitioning) return;

      if (Math.abs(e.deltaX) > SWIPE_THRESHOLD) {
         // Swipe Left (deltaX > 0) -> Next Panel
         // Swipe Right (deltaX < 0) -> Prev Panel
         if (e.deltaX > 0) {
           goToPanel(currentIndex + 1);
         } else {
           goToPanel(currentIndex - 1);
         }
      }
    }
  }, { passive: false });

  // Update active state on scroll (in case of native/momentum scroll)
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
    // Fade/Visibility logic could go here
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
  }, { passive: false }); // Changed to false to allow preventing default if needed in future

  // Add touchmove listener to prevent native swipe navigation
  document.addEventListener("touchmove", (e) => {
    const currentX = e.touches[0].clientX;
    const currentY = e.touches[0].clientY;
    const diffX = currentX - startX;
    const diffY = currentY - startY;

    // If movement is predominantly horizontal, prevent default to stop browser nav
    if (Math.abs(diffX) > Math.abs(diffY)) {
      e.preventDefault();
    }
  }, { passive: false });

  document.addEventListener("touchend", (e) => {
    const endX = e.changedTouches[0].clientX;
    const endY = e.changedTouches[0].clientY;
    
    const diffX = endX - startX;
    const diffY = endY - startY;

    // Check if horizontal swipe dominant
    if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > TOUCH_THRESHOLD) {
      // Swipe Left (finger moves left, endX < startX, diffX < 0) -> Next Panel
      // Swipe Right (finger moves right, endX > startX, diffX > 0) -> Prev Panel
      
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

  updateActiveStates(0);
  panels.forEach((p) => p.classList.add("visible"));
  checkNavbarVisibility();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}