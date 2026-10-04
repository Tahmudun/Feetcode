/** A small, dependency-free confetti burst for Accepted. Honors prefers-reduced-motion. */
export function confetti(origin?: { x: number; y: number }) {
  if (typeof window === "undefined" || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const canvas = document.createElement("canvas");
  canvas.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:100";
  canvas.width = innerWidth * devicePixelRatio;
  canvas.height = innerHeight * devicePixelRatio;
  document.body.appendChild(canvas);
  const ctx = canvas.getContext("2d")!;
  ctx.scale(devicePixelRatio, devicePixelRatio);
  const css = getComputedStyle(document.documentElement);
  const colors = ["--accent", "--teal", "--violet", "--sky", "--rose"].map((v) => css.getPropertyValue(v).trim() || "#ffb454");
  const ox = origin?.x ?? innerWidth * 0.7;
  const oy = origin?.y ?? innerHeight * 0.35;
  const parts = Array.from({ length: 140 }, () => {
    const angle = Math.random() * Math.PI * 2;
    const speed = 4 + Math.random() * 9;
    return {
      x: ox, y: oy, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed - 6,
      w: 5 + Math.random() * 6, h: 3 + Math.random() * 4, r: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 0.4,
      c: colors[Math.floor(Math.random() * colors.length)], life: 1,
    };
  });
  let frame = 0;
  const tick = () => {
    frame++;
    ctx.clearRect(0, 0, innerWidth, innerHeight);
    for (const p of parts) {
      p.vy += 0.32;
      p.vx *= 0.985;
      p.x += p.vx;
      p.y += p.vy;
      p.r += p.vr;
      p.life -= 0.009;
      ctx.save();
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.translate(p.x, p.y);
      ctx.rotate(p.r);
      ctx.fillStyle = p.c;
      ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
      ctx.restore();
    }
    if (frame < 140) requestAnimationFrame(tick);
    else canvas.remove();
  };
  requestAnimationFrame(tick);
}
