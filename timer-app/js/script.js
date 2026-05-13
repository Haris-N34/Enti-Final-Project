const display   = document.getElementById('display');
const btnStart  = document.getElementById('btn-start');
const btnReset  = document.getElementById('btn-reset');
const inputMin  = document.getElementById('input-min');
const inputSec  = document.getElementById('input-sec');

let remaining = 0;
let interval  = null;
let running   = false;

function fmt(n) { return String(n).padStart(2, '0'); }

function render() {
  const m = Math.floor(remaining / 60);
  const s = remaining % 60;
  display.textContent = `${fmt(m)}:${fmt(s)}`;
  display.classList.toggle('urgent', remaining <= 10 && remaining > 0);
}

function tick() {
  if (remaining <= 0) {
    clearInterval(interval);
    running = false;
    btnStart.textContent = 'Start';
    display.textContent = '00:00';
    display.classList.remove('urgent');
    return;
  }
  remaining--;
  render();
}

function getInputSeconds() {
  const m = Math.max(0, parseInt(inputMin.value) || 0);
  const s = Math.min(59, Math.max(0, parseInt(inputSec.value) || 0));
  return m * 60 + s;
}

btnStart.addEventListener('click', () => {
  if (running) {
    clearInterval(interval);
    running = false;
    btnStart.textContent = 'Resume';
    inputMin.disabled = false;
    inputSec.disabled = false;
  } else {
    if (!running && remaining === 0) {
      remaining = getInputSeconds();
      if (remaining === 0) return;
    }
    render();
    interval = setInterval(tick, 1000);
    running = true;
    btnStart.textContent = 'Pause';
    inputMin.disabled = true;
    inputSec.disabled = true;
  }
});

btnReset.addEventListener('click', () => {
  clearInterval(interval);
  running = false;
  remaining = 0;
  btnStart.textContent = 'Start';
  inputMin.disabled = false;
  inputSec.disabled = false;
  display.classList.remove('urgent');
  const m = Math.max(0, parseInt(inputMin.value) || 0);
  const s = Math.min(59, Math.max(0, parseInt(inputSec.value) || 0));
  display.textContent = `${fmt(m)}:${fmt(s)}`;
});

inputMin.addEventListener('input', () => { if (!running && remaining === 0) render2(); });
inputSec.addEventListener('input', () => { if (!running && remaining === 0) render2(); });

function render2() {
  const m = Math.max(0, parseInt(inputMin.value) || 0);
  const s = Math.min(59, Math.max(0, parseInt(inputSec.value) || 0));
  display.textContent = `${fmt(m)}:${fmt(s)}`;
}

render2();

// ─── Firework / Sparkle Effect ────────────────────────────────────────────
//
// HOW TO CUSTOMIZE:
//
//   COLORS — edit the PARTICLE_COLORS array below.
//     Each entry is any valid CSS color string (hex, rgb, hsl, named color).
//     Add or remove entries freely; the engine picks one at random per particle.
//
//   PARTICLE COUNT — change PARTICLE_COUNT.
//     Higher values = denser burst (try 40–120). Heavier on the GPU at >150.
//
//   ANIMATION SPEED — two knobs:
//     • PARTICLE_SPEED  – initial launch speed in px/frame. Higher = bigger spread.
//     • DURATION_MS     – total lifetime of the burst in milliseconds.
//                         Changing this alone stretches/shrinks the whole animation
//                         without altering how far particles fly.
//     • GRAVITY         – downward acceleration per frame (0 = float, 0.15 = arc).

const PARTICLE_COLORS = [
  '#ff6b6b', // coral red
  '#ffd93d', // golden yellow
  '#6bcb77', // mint green
  '#4d96ff', // sky blue
  '#ff6fd8', // hot pink
  '#c77dff', // violet
  '#00d2ff', // cyan
  '#ff9a3c', // orange
];

const PARTICLE_COUNT = 72;   // number of particles per burst
const PARTICLE_SPEED = 7;    // base launch speed (px per frame)
const DURATION_MS    = 2000; // total animation lifetime in ms
const GRAVITY        = 0.12; // downward pull added each frame

const canvas = document.getElementById('firework-canvas');
const ctx    = canvas.getContext('2d');

// Keep canvas pixel-perfect at any window size
function resizeCanvas() {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

let particles   = [];
let animationId = null;

// Build one particle flying in direction `angle` (radians)
function makeParticle(x, y, angle) {
  const speed = PARTICLE_SPEED * (0.5 + Math.random() * 0.9); // slight variance
  return {
    x, y,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed,
    radius: 2 + Math.random() * 3,
    color: PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)],
    alpha: 1,
  };
}

// Launch a burst from the centre of a DOM element
function launchFirework(sourceElement) {
  const rect = sourceElement.getBoundingClientRect();
  const originX = rect.left + rect.width  / 2;
  const originY = rect.top  + rect.height / 2;

  // Spread particles evenly around a full 360° circle
  particles = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const angle = (i / PARTICLE_COUNT) * Math.PI * 2;
    particles.push(makeParticle(originX, originY, angle));
  }

  const startTime = performance.now();

  // Cancel any burst already in progress before starting a fresh one
  if (animationId) cancelAnimationFrame(animationId);

  function frame(now) {
    const elapsed  = now - startTime;
    const progress = elapsed / DURATION_MS; // 0 → 1

    if (progress >= 1) {
      // Animation finished — clear the canvas and stop
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      animationId = null;
      return;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
      // Move particle outward; gravity bends trajectory downward
      p.x  += p.vx;
      p.y  += p.vy;
      p.vy += GRAVITY; // To remove gravity: set GRAVITY = 0 above

      // Fade out over the animation's lifetime
      p.alpha = 1 - progress;

      ctx.save();
      ctx.globalAlpha = p.alpha;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();
      ctx.restore();
    });

    animationId = requestAnimationFrame(frame);
  }

  animationId = requestAnimationFrame(frame);
}

// Fire sparkles only when the timer actually starts (not on Pause)
btnStart.addEventListener('click', () => {
  // `running` is updated by the timer logic above; read state AFTER that toggle
  // by deferring with setTimeout(0), so we see the new value of `running`.
  setTimeout(() => {
    if (running) launchFirework(btnStart);
  }, 0);
});
// ─────────────────────────────────────────────────────────────────────────
