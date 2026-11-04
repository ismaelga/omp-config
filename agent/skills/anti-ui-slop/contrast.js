// WCAG 2.x text contrast for every visible element that owns text, run inside the page.
// Returns { failing, unmeasured }: failing entries are below 4.5:1 (3:1 for large text);
// unmeasured entries sit on an image or gradient, where no single background colour exists.
(() => {
  const parse = (c) => {
    const m = c.match(/[\d.]+/g);
    if (!m) return null;
    const [r, g, b, a = 1] = m.map(Number);
    return { r, g, b, a };
  };
  const over = (top, bottom) => ({
    r: top.r * top.a + bottom.r * (1 - top.a),
    g: top.g * top.a + bottom.g * (1 - top.a),
    b: top.b * top.a + bottom.b * (1 - top.a),
    a: 1,
  });
  const lum = ({ r, g, b }) => {
    const f = (v) => ((v /= 255) <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  // Composite translucent backgrounds from the element up to the canvas (white).
  const background = (el) => {
    const layers = [];
    for (let n = el; n; n = n.parentElement) {
      const s = getComputedStyle(n);
      if (s.backgroundImage !== "none") return null;
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) {
        layers.push(c);
        if (c.a === 1) break;
      }
    }
    return layers.reduceRight((acc, layer) => over(layer, acc), { r: 255, g: 255, b: 255, a: 1 });
  };
  const ownsText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
  // Off-page elements (skip links parked at negative offsets until focused) are not on screen.
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    const onPage = r.bottom + scrollY > 0 && r.right + scrollX > 0 && r.left + scrollX < document.documentElement.scrollWidth;
    return onPage && r.width > 1 && r.height > 1 && s.visibility !== "hidden" && +s.opacity > 0 && s.clipPath === "none";
  };
  const label = (el) => `${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}${el.classList.length ? "." + [...el.classList].join(".") : ""} "${el.textContent.trim().slice(0, 30)}"`;
  // A colour-scheme switch or hover can leave colours mid-transition; cancelling
  // transitions snaps every computed colour to its end value before measuring.
  const freeze = document.createElement("style");
  freeze.textContent = "*, *::before, *::after { transition: none !important; animation: none !important; }";
  document.head.append(freeze);
  void document.body.offsetHeight;
  const failing = [];
  const unmeasured = [];
  for (const el of document.body.querySelectorAll("*")) {
    if (!ownsText(el) || !visible(el)) continue;
    const s = getComputedStyle(el);
    const bg = background(el);
    if (!bg) {
      unmeasured.push(label(el));
      continue;
    }
    const fg = over(parse(s.color), bg);
    const [hi, lo] = [lum(fg), lum(bg)].sort((x, y) => y - x);
    const ratio = (hi + 0.05) / (lo + 0.05);
    const size = parseFloat(s.fontSize);
    const large = size >= 24 || (size >= 18.66 && +s.fontWeight >= 700);
    const need = large ? 3 : 4.5;
    if (ratio < need) failing.push({ element: label(el), ratio: +ratio.toFixed(2), need, color: s.color });
  }
  freeze.remove();
  return { failing, unmeasured };
})()
