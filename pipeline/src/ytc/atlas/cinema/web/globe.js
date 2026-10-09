// The Atlas globe: NASA's Earth by day and by night, the dataset draped over the countries, a glowing column on each
// country, and a camera that flies between the beats' countries. globe.py bakes scene/; its capture calls
// window.renderAt(t) for every frame, so every frame is a pure function of t.
import * as THREE from 'three';

THREE.ColorManagement.enabled = false;
const S = await (await fetch('scene/scene.json')).json();
const W = 1080, H = 1920;
const smooth = (a, b, t) => { const u = Math.min(1, Math.max(0, (t - a) / (b - a))); return u * u * (3 - 2 * u); };
const ease = (u) => { u = Math.min(1, Math.max(0, u)); return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };

function vec(lat, lon) {
  const la = THREE.MathUtils.degToRad(lat), ph = THREE.MathUtils.degToRad(lon + 180);
  return new THREE.Vector3(-Math.cos(ph) * Math.cos(la), Math.sin(la), Math.sin(ph) * Math.cos(la));
}

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
document.body.insertBefore(renderer.domElement, document.getElementById('labels'));
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x02040a);
const camera = new THREE.PerspectiveCamera(35, W / H, 0.01, 200);
// The globe's centre sits at 40% of the frame height, above the captions.
camera.setViewOffset(W, H * 1.2, 0, H * 0.2, W, H);

const loader = new THREE.TextureLoader();
const load = async (name) => {
  const t = await loader.loadAsync(name);
  t.colorSpace = THREE.NoColorSpace; t.anisotropy = 8;
  return t;
};
const [day, night, data] = await Promise.all([load('scene/day.jpg'), load('scene/night.jpg'), load('scene/data.png')]);
const hiNames = [...new Set(S.shots.map((s) => s.hi).filter(Boolean))];
const hiTex = Object.fromEntries(await Promise.all(hiNames.map(async (n) => [n, await load('scene/' + n)])));
const blank = new THREE.DataTexture(new Uint8Array([0, 0, 0, 0]), 1, 1); blank.needsUpdate = true;

const earthMat = new THREE.ShaderMaterial({
  uniforms: {
    day: { value: day }, night: { value: night }, data: { value: data }, hi: { value: blank },
    sun: { value: new THREE.Vector3(1, 0, 0) }, dataA: { value: 0.85 }, hiA: { value: 0 }, camPos: { value: new THREE.Vector3() },
    hiBox: { value: new THREE.Vector4(0, 0, 1, 1) },
  },
  vertexShader: `
    varying vec3 vN; varying vec2 vUv; varying vec3 vW;
    void main() {
      vUv = uv; vN = normalize(mat3(modelMatrix) * normal); vW = (modelMatrix * vec4(position, 1.0)).xyz;
      gl_Position = projectionMatrix * viewMatrix * vec4(vW, 1.0);
    }`,
  fragmentShader: `
    uniform sampler2D day, night, data, hi; uniform vec3 sun, camPos; uniform float dataA, hiA; uniform vec4 hiBox;
    varying vec3 vN; varying vec2 vUv; varying vec3 vW;
    void main() {
      vec3 n = normalize(vN); vec3 v = normalize(camPos - vW);
      float l = dot(n, sun);
      float lit = smoothstep(-0.15, 0.25, l);
      vec3 d = texture2D(day, vUv).rgb;
      vec3 col = d * (0.06 + 1.12 * max(l, 0.0));
      vec3 lights = texture2D(night, vUv).rgb;
      lights = pow(lights, vec3(1.6)) * vec3(1.0, 0.78, 0.48) * 2.2;
      col = mix(lights + d * 0.03, col, lit);
      float ocean = smoothstep(0.02, 0.10, d.b - max(d.r, d.g) * 0.9);
      vec3 h = normalize(sun + v);
      col += ocean * pow(max(dot(n, h), 0.0), 70.0) * 0.45 * lit;
      vec4 dt = texture2D(data, vUv);
      col = mix(col, dt.rgb * (0.30 + 0.85 * max(l, 0.0) + 0.25 * (1.0 - lit)), dt.a * dataA);
      // The highlight covers only its countries' box, so its outline stays sharp on a close-up.
      vec2 bu = (vUv - hiBox.xy) / (hiBox.zw - hiBox.xy);
      float inside = step(0.0, bu.x) * step(bu.x, 1.0) * step(0.0, bu.y) * step(bu.y, 1.0);
      vec4 ht = texture2D(hi, clamp(bu, 0.0, 1.0)) * inside;
      col = mix(col, ht.rgb, ht.a * hiA);
      float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0);
      col += vec3(0.30, 0.58, 1.0) * rim * 0.55 * (0.35 + 0.65 * lit);
      gl_FragColor = vec4(col, 1.0);
    }`,
});
scene.add(new THREE.Mesh(new THREE.SphereGeometry(1, 192, 128), earthMat));

scene.add(new THREE.Mesh(new THREE.SphereGeometry(1.06, 96, 64), new THREE.ShaderMaterial({
  uniforms: { sun: earthMat.uniforms.sun },
  vertexShader: `varying vec3 vN; varying vec3 vW;
    void main() { vN = normalize(mat3(modelMatrix) * normal); vW = (modelMatrix * vec4(position, 1.0)).xyz;
      gl_Position = projectionMatrix * viewMatrix * vec4(vW, 1.0); }`,
  fragmentShader: `uniform vec3 sun; varying vec3 vN; varying vec3 vW;
    void main() {
      vec3 v = normalize(cameraPosition - vW);
      float f = pow(max(0.0, 0.72 + dot(normalize(vN), v)), 5.0);
      float lit = 0.35 + 0.65 * smoothstep(-0.4, 0.5, dot(normalize(vN), sun));
      gl_FragColor = vec4(vec3(0.32, 0.62, 1.0) * f * 1.6 * lit, f);
    }`,
  side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false,
})));

// Stars, fixed by a seeded generator.
let seed = 7;
const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const starPos = [], starCol = [];
for (let i = 0; i < 2600; i++) {
  const u = rnd() * 2 - 1, a = rnd() * Math.PI * 2, r = 80, s = Math.sqrt(1 - u * u);
  starPos.push(r * s * Math.cos(a), r * u, r * s * Math.sin(a));
  const b = 0.35 + 0.65 * Math.pow(rnd(), 3);
  starCol.push(b, b, b * (0.9 + 0.2 * rnd()));
}
const starGeo = new THREE.BufferGeometry();
starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
starGeo.setAttribute('color', new THREE.Float32BufferAttribute(starCol, 3));
scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ size: 1.6, sizeAttenuation: false, vertexColors: true })));

// One column per country: height from the value's rank, colour from the map's scale.
const colGeo = new THREE.CylinderGeometry(1, 1, 1, 18, 1, false);
colGeo.translate(0, 0.5, 0);
const capGeo = new THREE.CircleGeometry(1, 18);
capGeo.rotateX(-Math.PI / 2);
const Y = new THREE.Vector3(0, 1, 0);
const WHITE = new THREE.Color(1, 1, 1);
const columns = S.countries.map((c) => {
  const n = vec(c.lat, c.lon);
  const color = new THREE.Color(c.c);
  const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.92 });
  const capMat = new THREE.MeshBasicMaterial({ color: color.clone().lerp(WHITE, 0.55), transparent: true });
  const mesh = new THREE.Mesh(colGeo, mat), cap = new THREE.Mesh(capGeo, capMat);
  const g = new THREE.Group();
  g.add(mesh); g.add(cap);
  g.position.copy(n.clone().multiplyScalar(1.0005));
  g.quaternion.setFromUnitVectors(Y, n);
  scene.add(g);
  return { c, n, mesh, cap, mat, capMat, width: c.w || 0.0065 };
});
const byIso = Object.fromEntries(columns.map((k) => [k.c.iso, k]));

// Camera poses: a direction from the centre and an altitude above the surface.
function target(i, t) {
  const s = S.shots[i];
  const dt = Math.max(0, t - s.t0);
  const drift = s.kind === 'world' || s.kind === 'card' || s.kind === 'rank' ? 2.6 : 0.7;
  const dir = vec(s.focus[0], s.focus[1] + drift * dt);
  const span = Math.max(s.t1 - s.t0, 0.1);
  return { dir, alt: s.alt * (1 - 0.07 * Math.min(1, dt / span)) };
}
function flyTime(i) {
  const s = S.shots[i];
  return Math.min(1.25, 0.42 * (s.t1 - s.t0));
}
function samePlace(a, b) {
  return a.focus[0] === b.focus[0] && a.focus[1] === b.focus[1] && a.alt === b.alt;
}
function pose(i, t) {
  const to = target(i, t);
  if (i === 0) return to;
  const s = S.shots[i], p = S.shots[i - 1];
  const F = flyTime(i);
  if (t - s.t0 >= F || samePlace(p, s)) return to;
  const from = pose(i - 1, s.t0);
  const e = ease((t - s.t0) / F);
  const angle = from.dir.angleTo(to.dir);
  const q = new THREE.Quaternion().setFromUnitVectors(from.dir, to.dir);
  const dir = from.dir.clone().applyQuaternion(new THREE.Quaternion().slerp(q, e));
  const alt = Math.exp(Math.log(from.alt) * (1 - e) + Math.log(to.alt) * e) + Math.sin(Math.PI * e) * angle * 0.8;
  return { dir, alt };
}

const LOOK = { world: { data: 0.62, others: 1.0 }, country: { data: 0.32, others: 0.3 }, group: { data: 0.4, others: 0.35 },
  region: { data: 0.45, others: 0.5 }, rank: { data: 0.35, others: 0.55 }, card: { data: 0.25, others: 0.45 } };

const labels = document.getElementById('labels');
const pins = {};
function pin(iso) {
  if (pins[iso]) return pins[iso];
  const k = byIso[iso];
  const e = document.createElement('div');
  e.className = 'pin';
  for (const [cls, text] of [['name', k.c.name], ['value', k.c.value], ['stem', '']]) {
    const part = document.createElement('div');
    part.className = cls;
    part.textContent = text;
    e.appendChild(part);
  }
  e.style.setProperty('--accent', k.c.c);
  labels.appendChild(e);
  return (pins[iso] = e);
}
const GROW = S.grow || [0.0, 1.4];

window.renderAt = (t) => {
  let i = S.shots.findIndex((s) => t < s.t1);
  if (i < 0) i = S.shots.length - 1;
  const s = S.shots[i], prev = S.shots[Math.max(0, i - 1)];
  const { dir, alt } = pose(i, t);
  camera.position.copy(dir.clone().multiplyScalar(1 + alt));
  camera.up.set(0, 1, 0);
  camera.lookAt(0, 0, 0);
  camera.updateMatrixWorld();
  const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
  const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
  earthMat.uniforms.sun.value.copy(dir.clone().multiplyScalar(0.62).addScaledVector(right, -0.62).addScaledVector(up, 0.42).normalize());
  earthMat.uniforms.camPos.value.copy(camera.position);

  const F = i ? flyTime(i) : 0.0;
  const arrive = i && !samePlace(prev, s) ? smooth(0, Math.max(F, 0.01), t - s.t0) : (i ? smooth(0, 0.4, t - s.t0) : 1);
  const a = LOOK[s.kind] || LOOK.world, b = LOOK[prev.kind] || LOOK.world;
  earthMat.uniforms.dataA.value = b.data + (a.data - b.data) * arrive;
  const focused = new Set(s.isos || []);
  const hiOn = (s.kind === 'country' || s.kind === 'group') && s.hi;
  earthMat.uniforms.hi.value = hiOn ? hiTex[s.hi] : blank;
  if (hiOn) earthMat.uniforms.hiBox.value.set(...s.hibox);
  earthMat.uniforms.hiA.value = hiOn ? smooth(F * 0.7, F + 0.35, t - s.t0) : 0;

  const camDir = camera.position.clone().normalize();
  const prevIsos = prev.isos || [];
  for (const k of columns) {
    const rank = k.c.h;
    const g = smooth(GROW[0] + (GROW[1] - GROW[0]) * 0.45 * (1 - rank), GROW[1], t);
    const h = Math.max(0.0005, (0.004 + 0.2 * rank) * (0.06 + 0.94 * g));
    const isFocus = focused.has(k.c.iso);
    const dim = focused.size ? (isFocus ? 1 : a.others) : a.others;
    const prevDim = prevIsos.length ? (prevIsos.includes(k.c.iso) ? 1 : b.others) : b.others;
    const op = prevDim + (dim - prevDim) * arrive;
    const facing = Math.max(0, k.n.dot(camDir));
    const w = k.width * (isFocus ? 1.6 : 1.0) * Math.min(1.4, Math.max(0.6, alt / 2.5));
    k.mesh.scale.set(w, h, w);
    k.cap.position.y = h;
    k.cap.scale.set(w, 1, w);
    // Columns read from afar; on a close-up they'd be blobs seen end-on, and at the limb, stray sticks.
    k.mat.opacity = 0.9 * op * smooth(0.12, 0.4, facing) * smooth(0.005, 0.02, h) * smooth(0.95, 1.7, alt);
    k.capMat.opacity = k.mat.opacity;
    k.mat.color.set(k.c.c);
    if (isFocus) k.mat.color.lerp(WHITE, 0.18 + 0.12 * Math.sin(t * 6));
  }

  for (const e of Object.values(pins)) e.style.opacity = 0;
  if (s.kind === 'country' || s.kind === 'group' || s.kind === 'world') {
    for (const iso of (s.isos || []).slice(0, 3)) {
      const k = byIso[iso];
      if (!k) continue;
      const top = k.n.clone().multiplyScalar(1.0005 + k.mesh.scale.y + 0.004);
      const p = top.clone().project(camera);
      const e = pin(iso);
      e.style.left = `${(p.x * 0.5 + 0.5) * W}px`;
      e.style.top = `${(-p.y * 0.5 + 0.5) * H}px`;
      const at = s.pin_at ?? F;
      e.style.opacity = smooth(at, at + 0.3, t - s.t0) * (k.n.dot(camDir) > 0.15 ? 1 : 0);
    }
  }
  renderer.render(scene, camera);
};

window.renderAt(0);
window.ready = true;
