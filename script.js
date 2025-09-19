/* ===== Utility ===== */
const $ = sel => document.querySelector(sel);
const canvas = $("#emergenceCanvas");
const ctx = canvas.getContext("2d", { alpha: true });
let width = 0, height = 0, dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));

function resize() {
  width = canvas.clientWidth;
  height = canvas.clientHeight;
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
window.addEventListener("resize", resize, { passive: true });
resize();
$("#year").textContent = new Date().getFullYear();

/* ===== Emergent Flocking Particles =====
   Simple boids-like system with local rules:
   1) Cohesion (move toward local center of mass)
   2) Separation (avoid crowding)
   3) Alignment (match velocity with neighbors)
   + Mouse: attract or repel (toggle with click)
*/
const MAX_PARTICLES = 220; // adapt via density below
const particles = [];
let mouse = { x: width/2, y: height/2, down: false, repel: false };
let pausedForReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

canvas.addEventListener("mousemove", e => {
  const rect = canvas.getBoundingClientRect();
  mouse.x = e.clientX - rect.left;
  mouse.y = e.clientY - rect.top;
}, { passive: true });
canvas.addEventListener("touchmove", e => {
  const t = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  mouse.x = t.clientX - rect.left;
  mouse.y = t.clientY - rect.top;
}, { passive: true });
canvas.addEventListener("mousedown", () => mouse.down = true);
canvas.addEventListener("mouseup", () => mouse.down = false);
canvas.addEventListener("mouseleave", () => mouse.down = false);
canvas.addEventListener("click", () => { mouse.repel = !mouse.repel; });

function rand(min, max){ return Math.random() * (max - min) + min; }

class Particle {
  constructor(){
    const speed = rand(.2,.8);
    this.x = rand(0, width);
    this.y = rand(0, height);
    this.vx = rand(-speed, speed);
    this.vy = rand(-speed, speed);
  }
}

function seed(){
  particles.length = 0;
  // density-aware count (keeps perf on phones)
  const area = width * height;
  const density = Math.min(MAX_PARTICLES, Math.floor(area / 9000));
  for(let i=0;i<density;i++) particles.push(new Particle());
}
seed();
window.addEventListener("resize", seed);

/* ===== Simulation Params ===== */
const params = {
  perception: 55,  // neighbor radius
  separationDist: 16,
  maxSpeed: 2.2,
  maxForce: 0.045,
  cohesionWeight: 0.4,
  alignmentWeight: 0.8,
  separationWeight: 1.2,
  mouseWeight: 1.0
};

function step(){
  for(const p of particles){
    let total = 0;
    let steerCohesion = {x:0,y:0};
    let steerAlignment = {x:0,y:0};
    let steerSeparation = {x:0,y:0};

    for(const other of particles){
      if (other === p) continue;
      const dx = other.x - p.x;
      const dy = other.y - p.y;
      const dist = Math.hypot(dx, dy);
      if (dist < params.perception && dist > 0){
        // Cohesion
        steerCohesion.x += other.x;
        steerCohesion.y += other.y;
        // Alignment
        steerAlignment.x += other.vx;
        steerAlignment.y += other.vy;
        // Separation (inverse square)
        if (dist < params.separationDist){
          const inv = 1 / (dist * dist + 0.0001);
          steerSeparation.x -= dx * inv;
          steerSeparation.y -= dy * inv;
        }
        total++;
      }
    }

    // Average & desired vectors
    if (total > 0){
      // Cohesion
      steerCohesion.x = (steerCohesion.x/total - p.x);
      steerCohesion.y = (steerCohesion.y/total - p.y);
      // Alignment
      steerAlignment.x /= total; steerAlignment.y /= total;
    }

    // Mouse influence
    const mdx = mouse.x - p.x;
    const mdy = mouse.y - p.y;
    const md = Math.hypot(mdx, mdy) || 1;
    const mouseFactor = Math.min(1, 140 / md); // closer → stronger
    let steerMouse = {
      x: (mouse.repel ? -mdx : mdx) / md * mouseFactor,
      y: (mouse.repel ? -mdy : mdy) / md * mouseFactor
    };

    // Combine
    let ax = 0, ay = 0;
    ax += steerCohesion.x * params.cohesionWeight;
    ay += steerCohesion.y * params.cohesionWeight;
    ax += steerAlignment.x * params.alignmentWeight;
    ay += steerAlignment.y * params.alignmentWeight;
    ax += steerSeparation.x * params.separationWeight;
    ay += steerSeparation.y * params.separationWeight;
    if (mouse.down) { // stronger when pressing
      ax += steerMouse.x * params.mouseWeight * 1.8;
      ay += steerMouse.y * params.mouseWeight * 1.8;
    } else {
      ax += steerMouse.x * params.mouseWeight * .6;
      ay += steerMouse.y * params.mouseWeight * .6;
    }

    // Limit force
    const af = Math.hypot(ax, ay);
    const maxF = params.maxForce;
    if (af > maxF){ ax = ax / af * maxF; ay = ay / af * maxF; }

    // Integrate
    p.vx += ax; p.vy += ay;

    // Limit speed
    const sp = Math.hypot(p.vx, p.vy);
    if (sp > params.maxSpeed){ p.vx = p.vx / sp * params.maxSpeed; p.vy = p.vy / sp * params.maxSpeed; }

    // Move
    p.x += p.vx; p.y += p.vy;

    // Wrap edges (torus topology helps emergent swirls)
    if (p.x < -10) p.x = width + 10;
    if (p.x > width + 10) p.x = -10;
    if (p.y < -10) p.y = height + 10;
    if (p.y > height + 10) p.y = -10;
  }
}

function draw(){
  // trailing fade for flow visualization
  ctx.fillStyle = "rgba(11,13,16,0.12)";
  ctx.fillRect(0,0,width,height);

  // field lines
  ctx.globalCompositeOperation = "lighter";
  for(const p of particles){
    const sp = Math.hypot(p.vx, p.vy);
    const brightness = Math.min(1, (sp / params.maxSpeed) * 0.9 + 0.1);
    ctx.strokeStyle = `rgba(125,211,252,${0.18 + brightness*0.2})`; // brand glow
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    ctx.lineTo(p.x - p.vx * 4, p.y - p.vy * 4);
    ctx.stroke();
  }
  ctx.globalCompositeOperation = "source-over";
}

function loop(){
  if (!pausedForReducedMotion){
    step();
    draw();
  }
  requestAnimationFrame(loop);
}
loop();

/* Accessibility: pause when tab not visible or reduced motion toggles */
document.addEventListener("visibilitychange", () => {
  pausedForReducedMotion = document.hidden || window.matchMedia("(prefers-reduced-motion: reduce)").matches;
});
