/* ozaydin.dev — bit alanı, sayfa geçişleri (pjax), sayfa davranışları.
   Sayfalar sunucuda (Django) üretilir; bu dosya sadece görünüşü ve geçişleri yönetir.
   JavaScript kapalıyken de bütün linkler normal sayfa olarak çalışır. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const mob = matchMedia('(max-width: 759px)');
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const app = $('#app');
  const isHome = () => app.dataset.page === 'home';

  /* ---------- Çözülen metin ---------- */
  const rbit = () => (Math.random() < 0.5 ? '0' : '1');
  function wrapChars(el, txt) {
    el.textContent = '';
    const sr = document.createElement('span'); sr.className = 'sr'; sr.textContent = txt; el.appendChild(sr);
    const box = document.createElement('span'); box.setAttribute('aria-hidden', 'true'); el.appendChild(box);
    const cs = [];
    txt.split(' ').forEach((w, i, arr) => {
      const ws = document.createElement('span'); ws.className = 'w';
      for (const ch of w) { const c = document.createElement('span'); c.className = 'c off'; c.textContent = ch; c.dataset.b = rbit(); ws.appendChild(c); cs.push(c); }
      box.appendChild(ws);
      if (i < arr.length - 1) box.appendChild(document.createTextNode(' '));
    });
    el.classList.add('dc');
    return cs;
  }
  function decode(el, dur = 800, delay = 0) {
    if (reduce || el._dc) return;
    const txt = el.textContent; el._dc = true;
    const cs = wrapChars(el, txt), n = cs.length, t0 = performance.now() + delay;
    (function tick(now) {
      const p = (now - t0) / dur;
      for (let i = 0; i < n; i++) {
        const c = cs[i];
        if (i / n < p) c.classList.remove('off');
        else if (Math.random() < 0.2) c.dataset.b = rbit();
      }
      if (p < 1.02) requestAnimationFrame(tick);
      else { el.textContent = txt; el.classList.remove('dc'); el._dc = false; }
    })(performance.now());
  }


  /* ---------- 3B bit alanı ---------- */
  const field = { want: '01', hov: null, base(n) { this.want = n; this.apply(); }, hover(n) { this.hov = n; this.apply(); }, apply() {}, vel: 0 };

  function initField() {
    if (!window.THREE) return;
    const canvas = $('#bits');
    let renderer;
    try { renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false, powerPreference: 'high-performance' }); } catch (e) { return; }
    const weak = innerWidth < 760 || (navigator.hardwareConcurrency || 8) <= 4;
    const N = weak ? 7000 : 16000, DUST = Math.floor(N * 0.12), M = N - DUST;
    const PR = Math.min(devicePixelRatio || 1, weak ? 1.5 : 1.75);
    renderer.setPixelRatio(PR); renderer.setClearColor(0x000000, 0);
    const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(40, 1, 0.1, 140);
    cam.position.z = 22;
    const group = new THREE.Group(); scene.add(group);
    const VIS_H = 2 * 22 * Math.tan(20 * Math.PI / 180);

    let sd = 7; const rnd = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
    const dust = new Float32Array(DUST * 3);
    for (let i = 0; i < DUST; i++) { dust[i * 3] = (rnd() - 0.5) * 48; dust[i * 3 + 1] = (rnd() - 0.5) * 26; dust[i * 3 + 2] = -22 + rnd() * 28; }
    const fin = (a) => { a.set(dust, M * 3); return a; };

    const widths = { helix: 16, sphere: 8.4 }, cache = {};
    function textForm(key, str) {
      const W = 1024, H = 512, c = document.createElement('canvas'); c.width = W; c.height = H;
      const x = c.getContext('2d', { willReadFrequently: true });
      let fs = 440; const font = () => { x.font = '600 ' + fs + 'px Geist, system-ui, sans-serif'; };
      font(); let w = x.measureText(str).width;
      if (w > 940) { fs *= 940 / w; font(); w = 940; }
      const m = x.measureText(str);
      x.textAlign = 'center'; x.fillStyle = '#fff';
      x.fillText(str, W / 2, H / 2 + (m.actualBoundingBoxAscent - m.actualBoundingBoxDescent) / 2);
      const d = x.getImageData(0, 0, W, H).data, pts = [];
      for (let py = 0; py < H; py += 2) for (let px = 0; px < W; px += 2) if (d[(py * W + px) * 4 + 3] > 128) pts.push(px, py);
      const a = new Float32Array(N * 3), k = 24 / W, n = pts.length / 2;
      for (let i = 0; i < M; i++) {
        const j = n ? ((rnd() * n) | 0) * 2 : 0;
        a[i * 3] = ((pts[j] || W / 2) + rnd() * 2 - W / 2) * k;
        a[i * 3 + 1] = -((pts[j + 1] || H / 2) + rnd() * 2 - H / 2) * k;
        a[i * 3 + 2] = (rnd() - 0.5) * 1.6;
      }
      widths[key] = w * k;
      return fin(a);
    }
    function form(n) {
      if (cache[n]) return cache[n];
      const a = new Float32Array(N * 3);
      if (n === '01' || n === '0' || n === '1') return (cache[n] = textForm(n, n));
      if (n.startsWith('d-')) return (cache[n] = textForm(n, n.slice(2)));
      if (n === 'floor') {
        const cols = Math.round(Math.sqrt(M * 48 / 31)), rows = Math.ceil(M / cols);
        for (let i = 0; i < M; i++) { const cx = i % cols, rz = (i / cols) | 0; a[i * 3] = (cx / (cols - 1) - 0.5) * 48; a[i * 3 + 1] = 0; a[i * 3 + 2] = -22 + (rz / (rows - 1)) * 31; }
      } else if (n === 'helix') {
        for (let i = 0; i < M; i++) {
          let s = rnd() * 2 - 1; const R = 1.8;
          if (rnd() < 0.78) { const ang = s * Math.PI * 5 + (rnd() < 0.5 ? 0 : Math.PI); a[i * 3] = s * 8; a[i * 3 + 1] = Math.sin(ang) * R + (rnd() - 0.5) * 0.16; a[i * 3 + 2] = Math.cos(ang) * R + (rnd() - 0.5) * 0.16; }
          else { s = Math.round(s * 16) / 16; const ang = s * Math.PI * 5, tt = rnd() * 2 - 1; a[i * 3] = s * 8; a[i * 3 + 1] = Math.sin(ang) * R * tt; a[i * 3 + 2] = Math.cos(ang) * R * tt; }
        }
      } else if (n === 'sphere') {
        for (let i = 0; i < M; i++) { const y = 1 - (i / (M - 1)) * 2, r = Math.sqrt(1 - y * y), th = i * 2.399963, R = 4.2 * (0.97 + rnd() * 0.06); a[i * 3] = Math.cos(th) * r * R; a[i * 3 + 1] = y * R; a[i * 3 + 2] = Math.sin(th) * r * R; }
      } else {
        for (let i = 0; i < M; i++) { const th = rnd() * 6.283, ph = Math.acos(2 * rnd() - 1), R = 10 + rnd() * 18; a[i * 3] = Math.sin(ph) * Math.cos(th) * R; a[i * 3 + 1] = Math.sin(ph) * Math.sin(th) * R; a[i * 3 + 2] = Math.cos(ph) * R - 6; }
      }
      return (cache[n] = fin(a));
    }

    const seed = new Float32Array(N), rand = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      seed[i] = rnd();
      const th = rnd() * 6.283, ph = Math.acos(2 * rnd() - 1), R = 0.4 + rnd();
      rand[i * 3] = Math.sin(ph) * Math.cos(th) * R; rand[i * 3 + 1] = Math.sin(ph) * Math.sin(th) * R; rand[i * 3 + 2] = Math.cos(ph) * R;
    }
    const fromArr = new Float32Array(form('scatter')), toArr = new Float32Array(N * 3);
    const geo = new THREE.BufferGeometry();
    const aFrom = new THREE.BufferAttribute(fromArr, 3), aTo = new THREE.BufferAttribute(toArr, 3);
    geo.setAttribute('position', aTo); geo.setAttribute('aFrom', aFrom);
    geo.setAttribute('aSeed', new THREE.BufferAttribute(seed, 1)); geo.setAttribute('aRand', new THREE.BufferAttribute(rand, 3));

    const ac = document.createElement('canvas'); ac.width = 256; ac.height = 128;
    const ax = ac.getContext('2d'); ax.fillStyle = '#fff'; ax.textAlign = 'center'; ax.textBaseline = 'middle';
    ax.font = '500 112px "Geist Mono", ui-monospace, monospace'; ax.fillText('0', 64, 70); ax.fillText('1', 192, 70);
    const atlas = new THREE.CanvasTexture(ac);

    const U = { uT: { value: 0 }, uTime: { value: 0 }, uPR: { value: PR }, uSize: { value: 15 }, uScatter: { value: 2.6 }, uAspect: { value: 1 },
      uDim: { value: 1 }, uWave: { value: 0 }, uVel: { value: 0 }, uScale: { value: 1 }, uPtr: { value: new THREE.Vector2(-9, -9) }, uPush: { value: 0.14 }, uAtlas: { value: atlas } };
    const mat = new THREE.ShaderMaterial({
      uniforms: U, transparent: true, depthWrite: false, depthTest: false,
      vertexShader: [
        'attribute vec3 aFrom; attribute float aSeed; attribute vec3 aRand;',
        'uniform float uT,uTime,uPR,uSize,uScatter,uAspect,uDim,uWave,uVel,uScale,uPush; uniform vec2 uPtr;',
        'varying float vDigit; varying float vAlpha; varying float vBright;',
        'void main(){',
        '  float t=clamp(uT*1.55-aSeed*0.55,0.0,1.0); float e=t*t*(3.0-2.0*t);',
        '  vec3 p=mix(aFrom,position,e);',
        '  float arc=sin(3.14159*t);',
        '  p+=aRand*(arc*uScatter+uVel*0.4);',
        '  p.y+=sin(p.x*0.55+uTime*0.7)*cos(p.z*0.4+uTime*0.45)*uWave;',
        '  p.x+=sin(uTime*0.6+aSeed*40.0)*0.04; p.y+=cos(uTime*0.5+aSeed*31.0)*0.04;',
        '  vec4 mv=modelViewMatrix*vec4(p,1.0); vec4 clip=projectionMatrix*mv;',
        '  vec2 df=clip.xy/clip.w-uPtr; df.x*=uAspect; float f=smoothstep(0.3,0.0,length(df));',
        '  vec2 push=normalize(df+vec2(0.0001))*f*uPush; push.x/=uAspect; clip.xy+=push*clip.w;',
        '  gl_Position=clip;',
        '  float depth=-mv.z; float r1=fract(aSeed*7.13); float r2=fract(aSeed*91.7); float r3=fract(aSeed*3.71);',
        '  gl_PointSize=min(uSize*(0.55+0.9*r1)*uPR*uScale*(22.0/max(depth,0.5)),48.0*uPR);',
        '  float k=floor(uTime*(0.3+1.6*r3)+aSeed*100.0)+floor(uTime*16.0)*step(0.25,f)+floor(arc*6.0);',
        '  vDigit=step(0.5,fract(sin(k*12.9898+aSeed*78.233)*43758.5453));',
        '  vBright=(r2>0.9?1.0:(r2>0.55?0.6:0.32))+f*0.7+arc*0.25;',
        '  vAlpha=uDim*smoothstep(46.0,22.0,depth)*smoothstep(0.5,4.0,depth);',
        '}'
      ].join('\n'),
      fragmentShader: [
        'uniform sampler2D uAtlas; varying float vDigit; varying float vAlpha; varying float vBright;',
        'void main(){',
        '  vec2 uv=vec2((gl_PointCoord.x+vDigit)*0.5,1.0-gl_PointCoord.y);',
        '  float a=texture2D(uAtlas,uv).a; if(a<0.05) discard;',
        '  float b=clamp(vBright,0.0,1.0);',
        '  gl_FragColor=vec4(mix(vec3(0.36,0.41,0.52),vec3(0.95,0.96,0.98),b),a*vAlpha*(0.45+0.55*b));',
        '}'
      ].join('\n')
    });
    const points = new THREE.Points(geo, mat); points.frustumCulled = false; group.add(points);

    let tall = false, dur = 2.4, live = null, dirty = true;
    function pose(n) {
      const visW = VIS_H * cam.aspect;
      if (n === 'floor' || n === 'wave') return { x: 0, y: n === 'wave' ? -5 : -5.6, s: 1, dim: n === 'wave' ? 0.9 : 0.45, wave: n === 'wave' ? 1 : 0.3, spin: 0 };
      const w = widths[n] || 8, hero = n === '01';
      const short = innerHeight < 760, k = short ? 0.6 : 1;
      if (tall) return { x: 0, y: VIS_H * (short ? 0.25 : hero ? 0.26 : 0.22), s: Math.min(0.55, visW * 0.84 / w) * k, dim: hero ? 1 : 0.9, wave: 0, spin: n === 'helix' ? 1 : 0 };
      const frac = n === 'sphere' ? 0.34 : n === 'helix' ? 0.42 : 0.48;
      return { x: visW * 0.22, y: hero ? 0.9 : 0.2, s: Math.min(hero ? 1.1 : 1, visW * frac / w), dim: hero ? 1 : 0.85, wave: 0, spin: n === 'helix' ? 1 : 0 };
    }
    const cur = { x: 0, y: 0, s: 1, dim: 1, wave: 0 }, velo = { x: 0, y: 0, s: 0 };
    let tgt = cur, spinA = 0, spinOn = 0;

    function setTarget(n, d) {
      const key = n === 'wave' ? 'floor' : n, arr = form(key), T = U.uT.value;
      if (live !== null && key !== (live === 'wave' ? 'floor' : live)) {
        for (let i = 0; i < N; i++) {
          const t = clamp(T * 1.55 - seed[i] * 0.55, 0, 1), e = t * t * (3 - 2 * t), j = i * 3;
          fromArr[j] += (toArr[j] - fromArr[j]) * e; fromArr[j + 1] += (toArr[j + 1] - fromArr[j + 1]) * e; fromArr[j + 2] += (toArr[j + 2] - fromArr[j + 2]) * e;
        }
        aFrom.needsUpdate = true;
      }
      if (live === null || key !== (live === 'wave' ? 'floor' : live)) { toArr.set(arr); aTo.needsUpdate = true; U.uT.value = reduce || field.instant ? 1 : 0; dur = d; }
      live = n; tgt = pose(n); dirty = true;
    }
    field.apply = function () { const n = this.hov || this.want; if (n !== live) setTarget(n, live === null ? 2.4 : this.hov ? 0.9 : 1.4); };

    function layout() {
      const w = innerWidth, h = innerHeight;
      renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix();
      tall = cam.aspect < 0.9 || w < 760; U.uAspect.value = cam.aspect;
      if (live) tgt = pose(live);
      dirty = true;
    }
    layout(); addEventListener('resize', layout);
    field.apply();
    if (reduce || field.instant) { Object.assign(cur, tgt); field.instant = false; }

    const ptr = { x: 0, y: 0 };
    addEventListener('pointermove', (e) => {
      if (e.pointerType !== 'mouse') return;
      ptr.x = e.clientX / innerWidth * 2 - 1; ptr.y = -(e.clientY / innerHeight * 2 - 1);
      U.uPtr.value.set(ptr.x, ptr.y); dirty = true;
    }, { passive: true });
    document.addEventListener('pointerleave', () => U.uPtr.value.set(-9, -9));
    /* Dokunma: parmağın değdiği yerde bitler dağılır, bırakınca geri toplanır */
    let tUp = false;
    if (!reduce) {
      const tp = (e) => { const t = e.touches[0]; if (!t) return; U.uPtr.value.set(t.clientX / innerWidth * 2 - 1, -(t.clientY / innerHeight * 2 - 1)); U.uPush.value = 0.26; tUp = false; dirty = true; };
      addEventListener('touchstart', tp, { passive: true }); addEventListener('touchmove', tp, { passive: true });
      addEventListener('touchend', () => { tUp = true; }, { passive: true }); addEventListener('touchcancel', () => { tUp = true; }, { passive: true });
    }

    let raf = 0, last = 0, sx = 0, sy = 0;
    function frame(now) {
      raf = requestAnimationFrame(frame);
      const t = now * 0.001, dt = Math.min(0.05, last ? t - last : 0.016); last = t;
      if (reduce) { if (!dirty) return; Object.assign(cur, tgt); }
      else {
        if (U.uT.value < 1) U.uT.value = Math.min(1, U.uT.value + dt / dur);
        for (const k of ['x', 'y', 's']) { const acc = -70 * (cur[k] - tgt[k]) - 13 * velo[k]; velo[k] += acc * dt; cur[k] += velo[k] * dt; }
        const kk = 1 - Math.pow(0.02, dt);
        cur.dim += (tgt.dim - cur.dim) * kk; cur.wave += (tgt.wave - cur.wave) * kk;
        spinOn += ((tgt.spin || 0) - spinOn) * kk;
        spinA += dt * 0.5 * spinOn;
        if (!tgt.spin) { spinA %= 6.2832; spinA += ((spinA > 3.1416 ? 6.2832 : 0) - spinA) * kk; }
        sx += (ptr.x - sx) * kk; sy += (ptr.y - sy) * kk;
        field.vel *= Math.pow(0.004, dt);
        if (tUp) { U.uPush.value *= Math.pow(0.06, dt); if (U.uPush.value < 0.01) { tUp = false; U.uPtr.value.set(-9, -9); U.uPush.value = 0.14; } }
        U.uTime.value = t; U.uVel.value = Math.min(1.2, field.vel);
      }
      dirty = false;
      group.position.set(cur.x, cur.y, 0); group.scale.setScalar(cur.s);
      group.rotation.y = (reduce ? 0 : Math.sin(t * 0.25) * 0.26) + sx * 0.16;
      group.rotation.x = spinA - sy * 0.08;
      const dk = tall && !(mob.matches && isHome()) && (live !== 'wave') ? clamp(1 - (scrollY - innerHeight * 0.08) / (innerHeight * 0.3), 0.05, 1) : 1;
      U.uDim.value = cur.dim * dk; U.uWave.value = cur.wave; U.uScale.value = 0.6 + 0.4 * Math.min(1, cur.s);
      renderer.render(scene, cam);
      if (!canvas.classList.contains('on')) { canvas.classList.add('on'); const po = $('.poster'); if (po) { po.classList.add('gone'); setTimeout(() => po.remove(), 900); } }
    }
    const start = () => { if (!raf) { last = 0; raf = requestAnimationFrame(frame); } };
    document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelAnimationFrame(raf); raf = 0; } else { dirty = true; start(); } });
    canvas.addEventListener('webglcontextlost', (e) => { e.preventDefault(); cancelAnimationFrame(raf); raf = 0; canvas.remove(); });
    field.dirty = () => { dirty = true; };
    start();
  }


  /* ---------- Bit perdesi: sayfa geçişi ---------- */
  const wipe = (() => {
    const c = $('#wipe'), x = c.getContext('2d');
    let cs, cols, rows, thr, bits, busy = false;
    function size() {
      const d = Math.min(devicePixelRatio || 1, 1.5);
      c.width = innerWidth * d; c.height = innerHeight * d; x.setTransform(d, 0, 0, d, 0, 0);
      cs = innerWidth < 760 ? 24 : 32; cols = Math.ceil(innerWidth / cs); rows = Math.ceil(innerHeight / cs);
      thr = new Float32Array(cols * rows); bits = new Uint8Array(cols * rows);
      for (let r = 0; r < rows; r++) for (let q = 0; q < cols; q++) { thr[r * cols + q] = (q / cols) * 0.56 + (r / rows) * 0.2 + Math.random() * 0.12; bits[r * cols + q] = Math.random() < 0.5 ? 0 : 1; }
    }
    function draw(p, out) {
      x.clearRect(0, 0, innerWidth, innerHeight);
      x.font = '500 ' + Math.round(cs * 0.44) + 'px "Geist Mono", ui-monospace, monospace'; x.textAlign = 'center'; x.textBaseline = 'middle';
      for (let i = 0; i < thr.length; i++) {
        const age = ((out ? thr[i] + 0.12 - p * 1.0 : p * 1.0 - thr[i]) ) / 0.12;
        if (age <= 0) continue;
        const q = i % cols, r = (i / cols) | 0, edge = age < 1;
        x.fillStyle = edge ? '#111B33' : '#02040A'; x.fillRect(q * cs, r * cs, cs + 0.5, cs + 0.5);
        if (edge && Math.random() < 0.3) bits[i] ^= 1;
        x.fillStyle = edge ? 'rgba(241,243,248,0.95)' : 'rgba(241,243,248,0.08)';
        x.fillText(bits[i] ? '1' : '0', q * cs + cs / 2, r * cs + cs / 2 + 1);
      }
    }
    function phase(ms, out) {
      return new Promise((res) => {
        const t0 = performance.now();
        (function tick(now) { const p = clamp((now - t0) / ms, 0, 1); draw(p, out); p < 1 ? requestAnimationFrame(tick) : res(); })(t0);
      });
    }
    return {
      async run(mid) {
        if (reduce || busy || document.hidden) { mid(); return; }
        busy = true; size(); c.style.display = 'block';
        await phase(420, false);
        mid();
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
        await phase(480, true);
        c.style.display = 'none'; busy = false;
      }
    };
  })();


  /* ---------- Sahne: ekranın ortasındaki bölüm bit alanının şeklini seçer ---------- */
  let connected = false, scene = null, homeCard = null;
  const formName = (f) => (f === 'c' ? (connected ? '1' : '0') : f);
  function pickScene() {
    const mid = innerHeight * 0.5; let hit = null;
    $$('[data-form]', app).forEach((el) => { const r = el.getBoundingClientRect(); if (r.top <= mid && r.bottom >= mid) hit = el; });
    if (!hit) hit = $('[data-form]', app);
    if (!hit) return;
    scene = hit;
    field.base(mob.matches && hit.id === 'sec-projeler' && homeCard ? 'd-' + homeCard : formName(hit.dataset.form));
  }
  addEventListener('resize', () => requestAnimationFrame(pickScene));

  const dcIO = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { dcIO.unobserve(e.target); decode(e.target, 700); } }), { rootMargin: '0px 0px -10% 0px' });
  const rvIO = new IntersectionObserver((es) => {
    let k = 0;
    es.forEach((e) => {
      if (!e.isIntersecting) return; rvIO.unobserve(e.target);
      if (reduce || !e.target.animate) return;
      e.target.animate([{ opacity: 0, transform: 'translateY(24px)' }, { opacity: 1, transform: 'none' }], { duration: 800, delay: k++ * 80, easing: 'cubic-bezier(0.2, 0.7, 0.2, 1)', fill: 'backwards' });
    });
  });

  /* ---------- Telefon: yana kaydırılan kartlar ve bit noktaları ---------- */
  function swipes(root) {
    $$('#home-rows, .caps', root).forEach((box) => {
      const items = [...box.children]; if (!items.length) return;
      const pips = document.createElement('p');
      pips.className = 'pips'; pips.setAttribute('aria-hidden', 'true');
      pips.innerHTML = items.map(() => '<span>0</span>').join('');
      box.after(pips);
      let at = -1;
      const upd = () => {
        const w = (items[0].offsetWidth || 1) + 16, i = clamp(Math.round(box.scrollLeft / w), 0, items.length - 1);
        if (i === at) return; at = i;
        [...pips.children].forEach((s, k) => { s.textContent = k === i ? '1' : '0'; s.classList.toggle('on', k === i); });
        if (box.id === 'home-rows') { homeCard = items[i].dataset.idx; if (mob.matches && scene && scene.id === 'sec-projeler') field.base('d-' + homeCard); }
      };
      box.addEventListener('scroll', () => requestAnimationFrame(upd), { passive: true });
      upd();
    });
  }

  /* ---------- Projeler: alan filtresi (her alan bir bit) ---------- */
  function filters(root) {
    const box = $('#filters', root); if (!box) return;
    const active = new Set(), btns = $$('.tog', box), mask = $('#mask', box), word = mask ? mask.dataset.word : '';
    box.addEventListener('click', (e) => {
      const b = e.target.closest('.tog'); if (!b) return;
      const c = b.dataset.cat; active.has(c) ? active.delete(c) : active.add(c);
      b.setAttribute('aria-pressed', active.has(c) ? 'true' : 'false');
      if (mask) mask.textContent = word + ' ' + btns.map((x) => (active.has(x.dataset.cat) ? '1' : '0')).join('');
      let shown = 0;
      $$('#all-rows .rw', root).forEach((w) => {
        const cats = (w.dataset.cats || '').trim().split(/\s+/);
        const ok = !active.size || cats.some((k) => active.has(k));
        w.classList.toggle('out', !ok); w.inert = !ok; if (ok) shown++;
      });
      const empty = $('#p-empty', root); if (empty) empty.hidden = shown > 0;
    });
  }

  /* ---------- Galeri: tam ekran görüntüleyici ---------- */
  const lb = $('#lightbox');
  let shots = [], at = 0, lastFocus = null;
  function lbShow(i) {
    at = (i + shots.length) % shots.length;
    const a = shots[at], img = $('img', lb);
    img.src = a.href; img.alt = a.dataset.caption || '';
    $('figcaption', lb).textContent = a.dataset.caption || '';
    $('.lb-prev', lb).hidden = $('.lb-next', lb).hidden = shots.length < 2;
  }
  function lbOpen(list, i) { shots = list; lastFocus = document.activeElement; lb.hidden = false; document.documentElement.style.overflow = 'hidden'; lbShow(i); $('.lb-close', lb).focus(); }
  function lbClose() { lb.hidden = true; document.documentElement.style.overflow = ''; $('img', lb).removeAttribute('src'); if (lastFocus) lastFocus.focus(); }
  if (lb) {
    $('.lb-close', lb).addEventListener('click', lbClose);
    $('.lb-prev', lb).addEventListener('click', () => lbShow(at - 1));
    $('.lb-next', lb).addEventListener('click', () => lbShow(at + 1));
    lb.addEventListener('click', (e) => { if (e.target === lb) lbClose(); });
    addEventListener('keydown', (e) => {
      if (lb.hidden) return;
      if (e.key === 'Escape') lbClose();
      else if (e.key === 'ArrowLeft') lbShow(at - 1);
      else if (e.key === 'ArrowRight') lbShow(at + 1);
    });
    let tx = null;
    lb.addEventListener('touchstart', (e) => { tx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', (e) => { if (tx === null) return; const d = e.changedTouches[0].clientX - tx; if (Math.abs(d) > 48) lbShow(at + (d < 0 ? 1 : -1)); tx = null; }, { passive: true });
  }
  function gallery(root) {
    $$('.gallery', root).forEach((g) => {
      const list = $$('.shot', g);
      list.forEach((a, i) => a.addEventListener('click', (e) => { if (e.metaKey || e.ctrlKey) return; e.preventDefault(); lbOpen(list, i); }));
    });
  }

  /* ---------- İletişim: kopyala, durum biti, form ---------- */
  function copyText(text, sel) {
    const fallback = () => { if (!sel) return false; const r = document.createRange(); r.selectNodeContents(sel); const s = getSelection(); s.removeAllRanges(); s.addRange(r); return false; };
    try { return navigator.clipboard.writeText(text).then(() => true, fallback); } catch (e) { return Promise.resolve(fallback()); }
  }
  function setConnected() {
    connected = true; const b = $('#conn'); if (!b) return;
    b.textContent = '1'; b.classList.add('pop'); setTimeout(() => b.classList.remove('pop'), 300);
    if (app.dataset.page === 'contact') field.base('1');
  }
  function contact(root) {
    const btn = $('#copy-mail', root);
    if (btn) {
      const label = btn.textContent;
      btn.addEventListener('click', async () => {
        const mail = $('#mail', root), ok = await copyText(mail.textContent, mail);
        btn.textContent = ok ? btn.dataset.copied : btn.dataset.selected; if (ok) setConnected();
        setTimeout(() => { btn.textContent = label; }, 1800);
      });
    }
    if (connected) { const b = $('#conn', root); if (b) b.textContent = '1'; }
    const form = $('#contact-form', root); if (!form) return;
    const note = $('#note', form), submit = $('[type=submit]', form), idle = note.textContent, sendLabel = submit.textContent;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      $$('.field', form).forEach((f) => { f.classList.remove('bad'); const x = $('.err', f); if (x) x.remove(); });
      submit.disabled = true; submit.textContent = form.dataset.sending; note.classList.remove('ok');
      try {
        const res = await fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'X-Requested-With': 'fetch', 'Accept': 'application/json' }, credentials: 'same-origin' });
        const data = await res.json().catch(() => ({}));
        if (data.ok) {
          form.reset(); note.textContent = data.message || idle; note.classList.add('ok'); setConnected();
        } else {
          note.textContent = data.message || idle;
          Object.entries(data.errors || {}).forEach(([name, msg]) => {
            const input = form.elements[name]; if (!input) return;
            const f = input.closest('.field'); if (!f) return;
            f.classList.add('bad'); const p = document.createElement('p'); p.className = 'err'; p.textContent = msg; f.appendChild(p);
          });
          const first = $('.field.bad input, .field.bad textarea', form); if (first) first.focus();
        }
      } catch (err) {
        note.textContent = idle;
        form.submit();
        return;
      }
      submit.disabled = false; submit.textContent = sendLabel;
    });
  }

  /* ---------- İkilik saat (BCD), İstanbul ---------- */
  const fmt = new Intl.DateTimeFormat('tr-TR', { timeZone: 'Europe/Istanbul', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  let clockDots = null, clockEl = null;
  function clock(root) {
    clockEl = $('#clock', root); clockDots = null;
    if (!clockEl) return;
    const cg = $('.clock-grid', clockEl); clockDots = [];
    for (let i = 0; i < 24; i++) { const d = document.createElement('i'); cg.appendChild(d); clockDots.push(d); }
    tickClock();
  }
  function tickClock() {
    if (!clockDots || !clockEl || !clockEl.isConnected) return;
    const s = fmt.format(new Date()), digits = s.replace(/\D/g, '');
    for (let c = 0; c < 6; c++) for (let r = 0; r < 4; r++) clockDots[c * 4 + r].classList.toggle('on', ((+digits[c]) >> (3 - r)) & 1);
    $('#clock-label', clockEl).textContent = clockEl.dataset.city + ' ' + s;
    clockEl.setAttribute('aria-label', clockEl.dataset.label + ' ' + s);
  }
  setInterval(() => { if (!document.hidden) tickClock(); }, 1000);

  /* ---------- Manifesto: kaydırdıkça çözülen cümle ---------- */
  let mf = null, mfChars = [], mfShown = 0;
  function manifesto(root) {
    mf = $('#mf', root); mfChars = []; mfShown = 0;
    if (!mf) return;
    const t = $('#mf-text', mf);
    mfChars = wrapChars(t, t.textContent);
    if (reduce) { mfChars.forEach((c) => c.classList.remove('off')); mfShown = mfChars.length; }
  }
  if (!reduce) setInterval(() => { if (!mf || document.hidden) return; for (let k = 0; k < 4; k++) { const c = mfChars[(Math.random() * mfChars.length) | 0]; if (c && c.classList.contains('off')) c.dataset.b = rbit(); } }, 160);

  /* ---------- Kaydırma: bayt göstergesi, sahne, manifesto, hız ---------- */
  const byteEl = $('#byte');
  let lastY = scrollY, queued = false;
  function onScroll() {
    queued = false;
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight), y = scrollY;
    byteEl.textContent = '0b' + Math.round(clamp(y / max, 0, 1) * 255).toString(2).padStart(8, '0');
    pickScene();
    field.vel = Math.min(1.5, field.vel + Math.abs(y - lastY) / 500); lastY = y; if (field.dirty) field.dirty();
    if (!reduce && mf && mfChars.length) {
      const r = mf.getBoundingClientRect(), p = clamp((innerHeight * 0.35 - r.top) / Math.max(1, r.height - innerHeight * 0.75), 0, 1);
      const n = Math.round(p * mfChars.length);
      if (n !== mfShown) { for (let i = Math.min(n, mfShown); i < Math.max(n, mfShown); i++) mfChars[i].classList.toggle('off', i >= n); mfShown = n; }
    }
  }
  addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(onScroll); } }, { passive: true });

  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-scroll]'); if (!b) return;
    const t = $(b.dataset.scroll); if (t) t.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  });

  /* ---------- Bir sayfanın davranışlarını bağla (ilk açılışta ve her geçişte) ---------- */
  function hoverIdx(root) {
    $$('[data-idx]', root).forEach((a) => {
      if (!a.closest('#home-rows') && !a.classList.contains('next')) return;
      const on = () => field.hover('d-' + a.dataset.idx), off = () => field.hover(null);
      a.addEventListener('pointerenter', (e) => { if (e.pointerType === 'mouse') on(); }); a.addEventListener('pointerleave', off);
      a.addEventListener('focus', on); a.addEventListener('blur', off);
    });
  }
  function navState() {
    const page = app.dataset.page;
    const section = { project: 'projects', post: 'blog', tag: 'blog' }[page] || page;
    $$('[data-nav]').forEach((a) => (a.dataset.nav === section ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current')));
    $$('.langs a').forEach((a) => { const u = app.dataset['alt' + (a.dataset.lang === 'en' ? 'En' : 'Tr')]; if (u) a.href = u; });
    document.documentElement.classList.toggle('snap', isHome());
  }
  function initPage(first) {
    if (!first) { const po = $('.poster'); if (po) po.remove(); }
    homeCard = null; scene = null;
    const steps = [
      navState,
      () => { $$('[data-dcio]', app).forEach((s) => dcIO.observe(s)); $$('.rv, .row', app).forEach((s) => rvIO.observe(s)); },
      // Uzun başlıklarda harf harf çözülme ilk açılışta pahalı (yüzlerce öğe): sadece kısa başlıklarda ya da geçişlerde yap.
      () => $$('[data-dc]', app).forEach((el, i) => { if (!first || el.textContent.trim().length <= 18) decode(el, 900, (first ? 300 : 380) + i * 140); }),
      () => { hoverIdx(app); filters(app); gallery(app); contact(app); },
      () => { swipes(app); clock(app); },
      () => manifesto(app),
      () => { if (field.hover) field.hover(null); onScroll(); },
      () => document.dispatchEvent(new CustomEvent('page:ready', { detail: { page: app.dataset.page } })),
    ];
    if (!first) { steps.forEach((f) => f()); return; }
    // İlk açılışta işler küçük parçalara bölünür: tarayıcı arada ekranı çizebilir, sayfa takılmaz.
    const run = (i) => { if (i < steps.length) { steps[i](); setTimeout(() => run(i + 1), 0); } };
    run(0);
  }

  /* ---------- Sayfa geçişi: yeni sayfayı arkadan çek, bit perdesiyle değiştir ---------- */
  const cache = new Map();
  const sameSite = (u) => u.origin === location.origin;
  function wantsPjax(a, e) {
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return false;
    if (a.target && a.target !== '_self') return false;
    if (a.hasAttribute('download') || a.dataset.noPjax !== undefined || a.closest('.gallery')) return false;
    const u = new URL(a.href, location.href);
    if (!sameSite(u)) return false;
    if (/^\/(admin|media|static)\//.test(u.pathname) || /\.(xml|txt|rss|pdf|png|jpe?g|webp)$/.test(u.pathname) || u.pathname.endsWith('/rss/')) return false;
    if (u.pathname === location.pathname && u.search === location.search && u.hash) return false;
    const lang = (p) => (p === '/en' || p.startsWith('/en/') ? 'en' : 'tr');
    if (lang(u.pathname) !== lang(location.pathname)) return false; // dil değişince menü metinleri de değişir: tam yükleme
    return u;
  }
  function fetchPage(url) {
    if (!cache.has(url)) cache.set(url, fetch(url, { headers: { 'X-Requested-With': 'pjax' }, credentials: 'same-origin' }).then((r) => {
      if (!r.ok && r.status !== 404) throw new Error(r.status);
      return r.text();
    }).catch((err) => { cache.delete(url); throw err; }));
    return cache.get(url);
  }
  let navigating = false;
  async function go(url, push) {
    if (navigating) return; navigating = true;
    let html;
    try { html = await fetchPage(url); } catch (e) { location.href = url; return; }
    cache.delete(url);
    const doc = new DOMParser().parseFromString(html, 'text/html'), next = doc.getElementById('app');
    if (!next) { location.href = url; return; }
    const swap = () => {
      app.innerHTML = next.innerHTML;
      ['page', 'title', 'altTr', 'altEn'].forEach((k) => { app.dataset[k] = next.dataset[k] || ''; });
      document.title = doc.title;
      const desc = doc.querySelector('meta[name="description"]'), cur = document.querySelector('meta[name="description"]');
      if (desc && cur) cur.content = desc.content;
      if (push) history.pushState({ pjax: true }, '', url);
      const hash = new URL(url, location.href).hash, target = hash && document.getElementById(hash.slice(1));
      if (target) target.scrollIntoView(); else scrollTo(0, 0);
      initPage(false);
      const h = $('h1', app); if (h && h.tabIndex === -1) h.focus({ preventScroll: true });
    };
    await wipe.run(swap);
    navigating = false;
  }
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href]'), u = wantsPjax(a, e); if (!u) return;
    e.preventDefault();
    if (u.href === location.href) { scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' }); return; }
    go(u.href, true);
  });
  // Bağlantının üstüne gelince sayfayı önceden çek: tıklayınca geçiş anında başlar.
  document.addEventListener('pointerover', (e) => {
    const a = e.target.closest && e.target.closest('a[href]'); if (!a) return;
    const u = wantsPjax(a, { button: 0 }); if (u && u.href !== location.href) fetchPage(u.href).catch(() => {});
  }, { passive: true });
  addEventListener('popstate', () => go(location.href, false));
  try { history.scrollRestoration = 'manual'; history.replaceState({ pjax: true }, ''); } catch (e) {}

  /* ---------- İmleç biti ve mıknatıs ---------- */
  if (fine && !reduce) {
    const cur = $('#cur'); let tx = 0, ty = 0, x = 0, y = 0, vx = 0, vy = 0, lastT = 0, on = false;
    addEventListener('pointermove', (e) => {
      tx = e.clientX + 14; ty = e.clientY + 14; cur.classList.add('show');
      const hit = !!e.target.closest('a, button, input, textarea'); if (hit !== on) { on = hit; cur.textContent = on ? '1' : '0'; }
    }, { passive: true });
    document.addEventListener('pointerleave', () => cur.classList.remove('show'));
    // Yay hareketi: imleç durunca döngü de durur, işlemciyi boşuna meşgul etmez.
    let running = false;
    function loop(now) {
      const dt = Math.min(0.033, (now - lastT) / 1000 || 0.016); lastT = now;
      vx += (-300 * (x - tx) - 30 * vx) * dt; vy += (-300 * (y - ty) - 30 * vy) * dt; x += vx * dt; y += vy * dt;
      cur.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
      if (Math.abs(x - tx) + Math.abs(y - ty) + Math.abs(vx) + Math.abs(vy) > 0.2) requestAnimationFrame(loop); else running = false;
    }
    addEventListener('pointermove', () => { if (!running) { running = true; lastT = performance.now(); requestAnimationFrame(loop); } }, { passive: true });
    document.addEventListener('pointermove', (e) => {
      const b = e.target.closest('.btn'); if (!b) return;
      const r = b.getBoundingClientRect();
      b.style.transition = 'transform 0.12s ease-out, background-color 0.2s ease, box-shadow 0.2s ease';
      b.style.transform = 'translate(' + ((e.clientX - r.left - r.width / 2) * 0.1).toFixed(1) + 'px,' + ((e.clientY - r.top - r.height / 2) * 0.1).toFixed(1) + 'px)';
    }, { passive: true });
    document.addEventListener('pointerout', (e) => { const b = e.target.closest && e.target.closest('.btn'); if (b && !b.contains(e.relatedTarget)) { b.style.transition = ''; b.style.transform = ''; } });
  }

  /* ---------- Başlat ---------- */
  initPage(true);
  // 3B alan sayfa açıldıktan sonra, tarayıcı boşa çıkınca yüklenir: ilk görüntü ve etkileşim beklemez.
  function loadField() {
    const s = document.createElement('script');
    s.src = document.querySelector('script[data-three]').dataset.three;
    s.onload = () => {
      const fontsReady = document.fonts && document.fonts.load
        ? Promise.race([Promise.all([document.fonts.load('600 400px "Geist"'), document.fonts.load('500 112px "Geist Mono"')]), new Promise((r) => setTimeout(r, 1500))])
        : Promise.resolve();
      fontsReady.then(() => { initField(); pickScene(); }, () => { initField(); pickScene(); });
    };
    document.head.appendChild(s);
  }
  // 3B alan ziyaretçinin ilk hareketinde (fare, dokunma, kaydırma, tuş) başlar. O ana kadar ana sayfada
  // alanın hazır çekilmiş bir resmi (poster) görünür; WebGL başlayınca resim yumuşakça kaybolur.
  // Böylece sayfa ilk açılışta hafif kalır, telefonun işlemcisi ve pili boşuna yorulmaz.
  const poster = $('.poster');
  if (poster && poster.complete && poster.naturalWidth) field.instant = true;
  else if (poster) poster.addEventListener('load', () => { if (!field.started) field.instant = true; }, { once: true });
  const kicks = ['pointermove', 'pointerdown', 'touchstart', 'wheel', 'scroll', 'keydown'];
  function kick() {
    kicks.forEach((ev) => removeEventListener(ev, kick, { passive: true }));
    if (field.started) return; field.started = true;
    if (!poster || !poster.isConnected) field.instant = false;
    loadField();
  }
  kicks.forEach((ev) => addEventListener(ev, kick, { passive: true }));
})();
