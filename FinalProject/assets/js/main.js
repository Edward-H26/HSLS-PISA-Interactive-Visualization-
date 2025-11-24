const scrollContainer = document.getElementById("scroll-container");
const sections = Array.from(document.querySelectorAll(".panel"));
const navButtons = Array.from(document.querySelectorAll("[data-target]"));
const ctaShowcase = document.getElementById("cta-showcase");
const form = document.getElementById("contact-form");
const formStatus = document.getElementById("form-status");
const cursorOuter = document.querySelector(".cursor-outer");
const cursorInner = document.querySelector(".cursor-inner");

function scrollToIndex(index) {
  const target = sections[index];
  if (!target) return;
  const isMobile = window.innerWidth <= 960;
  if (isMobile) {
    const top = target.offsetTop;
    scrollContainer.scrollTo({ top, behavior: "smooth" });
  } else {
    const left = target.offsetLeft;
    scrollContainer.scrollTo({ left, behavior: "smooth" });
  }
}

function setupNav() {
  navButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const index = Number(btn.dataset.target);
      scrollToIndex(index);
    });
  });
  if (ctaShowcase) ctaShowcase.addEventListener("click", () => scrollToIndex(0));
}

function setupForm() {
  if (!form) return;
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    formStatus.textContent = "Message sent! We will reach out shortly.";
    form.reset();
    setTimeout(() => (formStatus.textContent = ""), 3000);
  });
}

function setupCursor() {
  if (!cursorOuter || !cursorInner) return;
  let targetX = window.innerWidth / 2;
  let targetY = window.innerHeight / 2;
  let outerX = targetX;
  let outerY = targetY;

  document.addEventListener("mousemove", (e) => {
    targetX = e.clientX;
    targetY = e.clientY;
  });

  function animate() {
    outerX += (targetX - outerX) * 0.35;
    outerY += (targetY - outerY) * 0.35;
    cursorOuter.style.transform = `translate(${outerX}px, ${outerY}px)`;
    cursorInner.style.transform = `translate(${targetX}px, ${targetY}px)`;
    requestAnimationFrame(animate);
  }
  animate();
}

function setVisibility() {
  const viewportW = window.innerWidth;
  const viewportH = window.innerHeight;
  sections.forEach((panel) => {
    const rect = panel.getBoundingClientRect();
    const isMobile = viewportW <= 960;
    const inView = isMobile
      ? rect.top < viewportH * 0.65 && rect.bottom > viewportH * 0.35
      : rect.left < viewportW * 0.65 && rect.right > viewportW * 0.35;
    if (inView) panel.classList.add("visible");
  });
}

function setupReveal() {
  setVisibility();
  scrollContainer.addEventListener("scroll", () => {
    requestAnimationFrame(setVisibility);
  });
  window.addEventListener("resize", () => {
    requestAnimationFrame(setVisibility);
  });
}

function setupWheelScroll() {
  scrollContainer.addEventListener(
    "wheel",
    (event) => {
      const isMobile = window.innerWidth <= 960;
      if (isMobile) return; // allow default vertical scroll on mobile
      event.preventDefault();
      const delta = event.deltaY;
      scrollContainer.scrollBy({ left: delta, behavior: "smooth" });
    },
    { passive: false }
  );
}

function init() {
  setupNav();
  setupForm();
  setupCursor();
  setupReveal();
  setupWheelScroll();
}

window.addEventListener("DOMContentLoaded", init);
