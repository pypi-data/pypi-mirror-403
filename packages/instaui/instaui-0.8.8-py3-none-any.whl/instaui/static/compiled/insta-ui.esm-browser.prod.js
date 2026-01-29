var bt = Object.defineProperty;
var _t = (e, t, n) => t in e ? bt(e, t, { enumerable: !0, configurable: !0, writable: !0, value: n }) : e[t] = n;
var _ = (e, t, n) => _t(e, typeof t != "symbol" ? t + "" : t, n);
import * as St from "vue";
import { unref as X, toRef as I, readonly as Se, customRef as re, ref as k, onBeforeUnmount as We, onMounted as Ee, nextTick as He, getCurrentScope as Et, onScopeDispose as kt, getCurrentInstance as Je, watch as $, isRef as P, shallowRef as ie, watchEffect as Ke, computed as A, onErrorCaptured as Vt, toValue as y, h as E, defineComponent as O, openBlock as L, createElementBlock as N, createElementVNode as Ge, renderSlot as se, toDisplayString as qe, createCommentVNode as ye, mergeProps as F, createBlock as Qe, Teleport as Ct, useAttrs as ke, Fragment as Z, useSlots as J, cloneVNode as D, useTemplateRef as xt, normalizeStyle as ge, vModelDynamic as At, vShow as Ot, withDirectives as Ye, toRaw as Xe, normalizeClass as Te, withModifiers as $t, resolveDynamicComponent as Tt, provide as Ze, inject as et, isVNode as Pt, TransitionGroup as Nt, createTextVNode as jt, createApp as Rt } from "vue";
function T(e, t) {
  t = t || {};
  const n = [...Object.keys(t), "__Vue"], r = [...Object.values(t), St];
  try {
    return new Function(...n, `return (${e})`)(...r);
  } catch (s) {
    throw new Error(s + " in function code: " + e);
  }
}
function oe(e, t = !0) {
  if (!(typeof e != "object" || e === null)) {
    if (Array.isArray(e)) {
      t && e.forEach((n) => oe(n, !0));
      return;
    }
    for (const [n, r] of Object.entries(e))
      if (n.startsWith(":"))
        try {
          e[n.slice(1)] = new Function(`return (${r})`)(), delete e[n];
        } catch (s) {
          console.error(
            `Error while converting ${n} attribute to function:`,
            s
          );
        }
      else
        t && oe(r, !0);
  }
}
function Ft(e, t) {
  const n = e.startsWith(":");
  return n && (e = e.slice(1), t = T(t)), { name: e, value: t, isFunc: n };
}
let tt;
function Dt(e) {
  let t = e.serverInfo;
  t && (t = {
    ...t,
    asset_icons_url: `${t.assets_url}/${t.assets_icons_name}`
  }), tt = {
    ...e,
    serverInfo: t
  };
}
function z() {
  return tt;
}
function Ve(e) {
  return Et() ? (kt(e), !0) : !1;
}
function K(e) {
  return typeof e == "function" ? e() : X(e);
}
const nt = typeof window < "u" && typeof document < "u";
typeof WorkerGlobalScope < "u" && globalThis instanceof WorkerGlobalScope;
const It = (e) => e != null, Lt = Object.prototype.toString, Mt = (e) => Lt.call(e) === "[object Object]", Ce = () => {
};
function Bt(e, t) {
  function n(...r) {
    return new Promise((s, o) => {
      Promise.resolve(e(() => t.apply(this, r), { fn: t, thisArg: this, args: r })).then(s).catch(o);
    });
  }
  return n;
}
const rt = (e) => e();
function zt(e = rt) {
  const t = k(!0);
  function n() {
    t.value = !1;
  }
  function r() {
    t.value = !0;
  }
  const s = (...o) => {
    t.value && e(...o);
  };
  return { isActive: Se(t), pause: n, resume: r, eventFilter: s };
}
function st(e) {
  return Je();
}
function ot(...e) {
  if (e.length !== 1)
    return I(...e);
  const t = e[0];
  return typeof t == "function" ? Se(re(() => ({ get: t, set: Ce }))) : k(t);
}
function Ut(e, t, n = {}) {
  const {
    eventFilter: r = rt,
    ...s
  } = n;
  return $(
    e,
    Bt(
      r,
      t
    ),
    s
  );
}
function Wt(e, t, n = {}) {
  const {
    eventFilter: r,
    ...s
  } = n, { eventFilter: o, pause: a, resume: i, isActive: c } = zt(r);
  return { stop: Ut(
    e,
    t,
    {
      ...s,
      eventFilter: o
    }
  ), pause: a, resume: i, isActive: c };
}
function Ht(e, t) {
  st() && We(e, t);
}
function at(e, t = !0, n) {
  st() ? Ee(e, n) : t ? e() : He(e);
}
function Jt(e, t, n) {
  let r;
  P(n) ? r = {
    evaluating: n
  } : r = n || {};
  const {
    lazy: s = !1,
    evaluating: o = void 0,
    shallow: a = !0,
    onError: i = Ce
  } = r, c = k(!s), l = a ? ie(t) : k(t);
  let u = 0;
  return Ke(async (f) => {
    if (!c.value)
      return;
    u++;
    const d = u;
    let h = !1;
    o && Promise.resolve().then(() => {
      o.value = !0;
    });
    try {
      const p = await e((m) => {
        f(() => {
          o && (o.value = !1), h || m();
        });
      });
      d === u && (l.value = p);
    } catch (p) {
      i(p);
    } finally {
      o && d === u && (o.value = !1), h = !0;
    }
  }), s ? A(() => (c.value = !0, l.value)) : l;
}
const U = nt ? window : void 0, Kt = nt ? window.document : void 0;
function xe(e) {
  var t;
  const n = K(e);
  return (t = n == null ? void 0 : n.$el) != null ? t : n;
}
function Pe(...e) {
  let t, n, r, s;
  if (typeof e[0] == "string" || Array.isArray(e[0]) ? ([n, r, s] = e, t = U) : [t, n, r, s] = e, !t)
    return Ce;
  Array.isArray(n) || (n = [n]), Array.isArray(r) || (r = [r]);
  const o = [], a = () => {
    o.forEach((u) => u()), o.length = 0;
  }, i = (u, f, d, h) => (u.addEventListener(f, d, h), () => u.removeEventListener(f, d, h)), c = $(
    () => [xe(t), K(s)],
    ([u, f]) => {
      if (a(), !u)
        return;
      const d = Mt(f) ? { ...f } : f;
      o.push(
        ...n.flatMap((h) => r.map((p) => i(u, h, p, d)))
      );
    },
    { immediate: !0, flush: "post" }
  ), l = () => {
    c(), a();
  };
  return Ve(l), l;
}
function Gt() {
  const e = k(!1), t = Je();
  return t && Ee(() => {
    e.value = !0;
  }, t), e;
}
function it(e) {
  const t = Gt();
  return A(() => (t.value, !!e()));
}
function qt(e, t, n = {}) {
  const { window: r = U, ...s } = n;
  let o;
  const a = it(() => r && "MutationObserver" in r), i = () => {
    o && (o.disconnect(), o = void 0);
  }, c = A(() => {
    const d = K(e), h = (Array.isArray(d) ? d : [d]).map(xe).filter(It);
    return new Set(h);
  }), l = $(
    () => c.value,
    (d) => {
      i(), a.value && d.size && (o = new MutationObserver(t), d.forEach((h) => o.observe(h, s)));
    },
    { immediate: !0, flush: "post" }
  ), u = () => o == null ? void 0 : o.takeRecords(), f = () => {
    l(), i();
  };
  return Ve(f), {
    isSupported: a,
    stop: f,
    takeRecords: u
  };
}
function Qt(e, t = {}) {
  const { window: n = U } = t, r = it(() => n && "matchMedia" in n && typeof n.matchMedia == "function");
  let s;
  const o = k(!1), a = (l) => {
    o.value = l.matches;
  }, i = () => {
    s && ("removeEventListener" in s ? s.removeEventListener("change", a) : s.removeListener(a));
  }, c = Ke(() => {
    r.value && (i(), s = n.matchMedia(K(e)), "addEventListener" in s ? s.addEventListener("change", a) : s.addListener(a), o.value = s.matches);
  });
  return Ve(() => {
    c(), i(), s = void 0;
  }), o;
}
const te = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : typeof global < "u" ? global : typeof self < "u" ? self : {}, ne = "__vueuse_ssr_handlers__", Yt = /* @__PURE__ */ Xt();
function Xt() {
  return ne in te || (te[ne] = te[ne] || {}), te[ne];
}
function ct(e, t) {
  return Yt[e] || t;
}
function Zt(e) {
  return Qt("(prefers-color-scheme: dark)", e);
}
function en(e) {
  return e == null ? "any" : e instanceof Set ? "set" : e instanceof Map ? "map" : e instanceof Date ? "date" : typeof e == "boolean" ? "boolean" : typeof e == "string" ? "string" : typeof e == "object" ? "object" : Number.isNaN(e) ? "any" : "number";
}
const tn = {
  boolean: {
    read: (e) => e === "true",
    write: (e) => String(e)
  },
  object: {
    read: (e) => JSON.parse(e),
    write: (e) => JSON.stringify(e)
  },
  number: {
    read: (e) => Number.parseFloat(e),
    write: (e) => String(e)
  },
  any: {
    read: (e) => e,
    write: (e) => String(e)
  },
  string: {
    read: (e) => e,
    write: (e) => String(e)
  },
  map: {
    read: (e) => new Map(JSON.parse(e)),
    write: (e) => JSON.stringify(Array.from(e.entries()))
  },
  set: {
    read: (e) => new Set(JSON.parse(e)),
    write: (e) => JSON.stringify(Array.from(e))
  },
  date: {
    read: (e) => new Date(e),
    write: (e) => e.toISOString()
  }
}, Ne = "vueuse-storage";
function ve(e, t, n, r = {}) {
  var s;
  const {
    flush: o = "pre",
    deep: a = !0,
    listenToStorageChanges: i = !0,
    writeDefaults: c = !0,
    mergeDefaults: l = !1,
    shallow: u,
    window: f = U,
    eventFilter: d,
    onError: h = (g) => {
      console.error(g);
    },
    initOnMounted: p
  } = r, m = (u ? ie : k)(typeof t == "function" ? t() : t);
  if (!n)
    try {
      n = ct("getDefaultStorage", () => {
        var g;
        return (g = U) == null ? void 0 : g.localStorage;
      })();
    } catch (g) {
      h(g);
    }
  if (!n)
    return m;
  const v = K(t), C = en(v), V = (s = r.serializer) != null ? s : tn[C], { pause: he, resume: x } = Wt(
    m,
    () => ee(m.value),
    { flush: o, deep: a, eventFilter: d }
  );
  f && i && at(() => {
    n instanceof Storage ? Pe(f, "storage", R) : Pe(f, Ne, G), p && R();
  }), p || R();
  function j(g, b) {
    if (f) {
      const S = {
        key: e,
        oldValue: g,
        newValue: b,
        storageArea: n
      };
      f.dispatchEvent(n instanceof Storage ? new StorageEvent("storage", S) : new CustomEvent(Ne, {
        detail: S
      }));
    }
  }
  function ee(g) {
    try {
      const b = n.getItem(e);
      if (g == null)
        j(b, null), n.removeItem(e);
      else {
        const S = V.write(g);
        b !== S && (n.setItem(e, S), j(b, S));
      }
    } catch (b) {
      h(b);
    }
  }
  function M(g) {
    const b = g ? g.newValue : n.getItem(e);
    if (b == null)
      return c && v != null && n.setItem(e, V.write(v)), v;
    if (!g && l) {
      const S = V.read(b);
      return typeof l == "function" ? l(S, v) : C === "object" && !Array.isArray(S) ? { ...v, ...S } : S;
    } else return typeof b != "string" ? b : V.read(b);
  }
  function R(g) {
    if (!(g && g.storageArea !== n)) {
      if (g && g.key == null) {
        m.value = v;
        return;
      }
      if (!(g && g.key !== e)) {
        he();
        try {
          (g == null ? void 0 : g.newValue) !== V.write(m.value) && (m.value = M(g));
        } catch (b) {
          h(b);
        } finally {
          g ? He(x) : x();
        }
      }
    }
  }
  function G(g) {
    R(g.detail);
  }
  return m;
}
const nn = "*,*::before,*::after{-webkit-transition:none!important;-moz-transition:none!important;-o-transition:none!important;-ms-transition:none!important;transition:none!important}";
function rn(e = {}) {
  const {
    selector: t = "html",
    attribute: n = "class",
    initialValue: r = "auto",
    window: s = U,
    storage: o,
    storageKey: a = "vueuse-color-scheme",
    listenToStorageChanges: i = !0,
    storageRef: c,
    emitAuto: l,
    disableTransition: u = !0
  } = e, f = {
    auto: "",
    light: "light",
    dark: "dark",
    ...e.modes || {}
  }, d = Zt({ window: s }), h = A(() => d.value ? "dark" : "light"), p = c || (a == null ? ot(r) : ve(a, r, o, { window: s, listenToStorageChanges: i })), m = A(() => p.value === "auto" ? h.value : p.value), v = ct(
    "updateHTMLAttrs",
    (x, j, ee) => {
      const M = typeof x == "string" ? s == null ? void 0 : s.document.querySelector(x) : xe(x);
      if (!M)
        return;
      const R = /* @__PURE__ */ new Set(), G = /* @__PURE__ */ new Set();
      let g = null;
      if (j === "class") {
        const S = ee.split(/\s/g);
        Object.values(f).flatMap((q) => (q || "").split(/\s/g)).filter(Boolean).forEach((q) => {
          S.includes(q) ? R.add(q) : G.add(q);
        });
      } else
        g = { key: j, value: ee };
      if (R.size === 0 && G.size === 0 && g === null)
        return;
      let b;
      u && (b = s.document.createElement("style"), b.appendChild(document.createTextNode(nn)), s.document.head.appendChild(b));
      for (const S of R)
        M.classList.add(S);
      for (const S of G)
        M.classList.remove(S);
      g && M.setAttribute(g.key, g.value), u && (s.getComputedStyle(b).opacity, document.head.removeChild(b));
    }
  );
  function C(x) {
    var j;
    v(t, n, (j = f[x]) != null ? j : x);
  }
  function V(x) {
    e.onChanged ? e.onChanged(x, C) : C(x);
  }
  $(m, V, { flush: "post", immediate: !0 }), at(() => V(m.value));
  const he = A({
    get() {
      return l ? p.value : m.value;
    },
    set(x) {
      p.value = x;
    }
  });
  return Object.assign(he, { store: p, system: h, state: m });
}
function sn(e = {}) {
  const {
    valueDark: t = "dark",
    valueLight: n = ""
  } = e, r = rn({
    ...e,
    onChanged: (a, i) => {
      var c;
      e.onChanged ? (c = e.onChanged) == null || c.call(e, a === "dark", i, a) : i(a);
    },
    modes: {
      dark: t,
      light: n
    }
  }), s = A(() => r.system.value);
  return A({
    get() {
      return r.value === "dark";
    },
    set(a) {
      const i = a ? "dark" : "light";
      s.value === i ? r.value = "auto" : r.value = i;
    }
  });
}
function on(e = null, t = {}) {
  var n, r, s;
  const {
    document: o = Kt,
    restoreOnUnmount: a = (f) => f
  } = t, i = (n = o == null ? void 0 : o.title) != null ? n : "", c = ot((r = e ?? (o == null ? void 0 : o.title)) != null ? r : null), l = e && typeof e == "function";
  function u(f) {
    if (!("titleTemplate" in t))
      return f;
    const d = t.titleTemplate || "%s";
    return typeof d == "function" ? d(f) : K(d).replace(/%s/g, f);
  }
  return $(
    c,
    (f, d) => {
      f !== d && o && (o.title = u(typeof f == "string" ? f : ""));
    },
    { immediate: !0 }
  ), t.observe && !t.titleTemplate && o && !l && qt(
    (s = o.head) == null ? void 0 : s.querySelector("title"),
    () => {
      o && o.title !== c.value && (c.value = u(o.title));
    },
    { childList: !0 }
  ), Ht(() => {
    if (a) {
      const f = a(i, c.value || "");
      f != null && o && (o.title = f);
    }
  }), c;
}
function an(e) {
  const t = k(!1), n = k("");
  function r(s, o) {
    let a;
    return o.component ? a = `Error captured from component:tag: ${o.component.tag} ; id: ${o.component.id} ` : a = "Error captured from app init", console.group(a), console.error("Component:", o.component), console.error("Error:", s), console.groupEnd(), e && (t.value = !0, n.value = `${a} ${s.message}`), !1;
  }
  return Vt(r), { hasError: t, errorMessage: n };
}
class cn {
  async eventSend(t, n) {
    const { fType: r = "sync", hKey: s } = t, o = z().serverInfo, a = r === "sync" ? o.event_url : o.event_async_url, c = await fetch(a, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        bind: n,
        hKey: s,
        ...{}
      })
    });
    if (!c.ok)
      throw new Error(`HTTP error! status: ${c.status}`);
    return await c.json();
  }
  async watchSend(t) {
    const { fType: n, hKey: r, inputs: s } = t.config, o = z().serverInfo, a = n === "sync" ? o.watch_url : o.watch_async_url, i = s ? s.map(y) : [];
    return await (await fetch(a, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        hKey: r,
        input: i
      })
    })).json();
  }
}
class ln {
  async eventSend(t, n) {
    const { fType: r, hKey: s, hKey: o } = t, c = {
      bind: n,
      fType: r,
      hKey: s,
      ...o !== void 0 ? { key: o } : {},
      ...{}
    };
    return await window.pywebview.api.event_call(c);
  }
  async watchSend(t) {
    const { fType: n, hKey: r, inputs: s } = t.config, o = s ? s.map(y) : [], a = {
      hKey: r,
      input: o,
      fType: n
    };
    return await window.pywebview.api.watch_call(a);
  }
}
let we;
function un(e) {
  switch (e) {
    case "web":
      we = new cn();
      break;
    case "webview":
      we = new ln();
      break;
  }
}
function lt() {
  return we;
}
function fn(e) {
  if (!(e === "web" || e === "webview") && e !== "zero")
    throw new Error(`Unsupported mode: ${e}`);
}
function dn(e, t) {
  const n = A(() => {
    const r = e.value;
    if (!r)
      return null;
    const a = new DOMParser().parseFromString(r, "image/svg+xml").querySelector("svg");
    if (!a)
      throw new Error("Invalid svg string");
    const i = {};
    for (const d of a.attributes)
      i[d.name] = d.value;
    const { size: c, color: l, attrs: u } = t;
    l.value !== null && l.value !== void 0 && (a.removeAttribute("fill"), a.querySelectorAll("*").forEach((h) => {
      h.hasAttribute("fill") && h.setAttribute("fill", "currentColor");
    }), i.color = l.value), c.value !== null && c.value !== void 0 && (i.width = c.value.toString(), i.height = c.value.toString());
    const f = a.innerHTML;
    return {
      ...i,
      ...u,
      innerHTML: f
    };
  });
  return () => {
    if (!n.value)
      return null;
    const r = n.value;
    return E("svg", r);
  };
}
async function hn(e) {
  var a;
  if (!e) return;
  const t = (a = z().serverInfo) == null ? void 0 : a.asset_icons_url;
  if (!t)
    throw new Error("Asset path is not set");
  const { names: n, sets: r } = e, s = [];
  if (n) {
    const i = {}, c = [];
    for (const l of n) {
      if (!l.includes(":")) {
        c.push(l);
        continue;
      }
      const [u, f] = l.split(":");
      i[u] || (i[u] = []), i[u].push(f);
    }
    c.length > 0 && console.warn(
      `Invalid icon names (missing file prefix): ${c.join(", ")}`
    );
    for (const l of Object.keys(i)) {
      const u = `${t}/${l}.svg`, f = await fetch(u);
      if (!f.ok) throw new Error(`Failed to load ${u}`);
      const d = await f.text(), p = new DOMParser().parseFromString(d, "image/svg+xml");
      for (const m of i[l]) {
        const v = p.getElementById(m);
        if (!v) {
          console.warn(`Failed to find icon ${m} in ${u}`);
          continue;
        }
        v.setAttribute("id", `${l}:${m}`), s.push(v.outerHTML);
      }
    }
  }
  if (r)
    for (const i of r) {
      const c = `/${t}/${i}.svg`, l = await fetch(c);
      if (!l.ok) throw new Error(`Failed to load ${c}`);
      const u = await l.text(), d = new DOMParser().parseFromString(u, "image/svg+xml"), h = Array.from(d.querySelectorAll("symbol"));
      if (h.length === 0) {
        console.warn(`No <symbol> found in ${c}`);
        continue;
      }
      for (const p of h) {
        const m = p.getAttribute("id");
        m && (p.setAttribute("id", `${i}:${m}`), s.push(p.outerHTML));
      }
    }
  const o = `<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
${s.join(
    `
`
  )}
</svg>`;
  document.body.insertAdjacentHTML("afterbegin", o);
}
const pn = {
  class: "app-box insta-theme",
  "data-scaling": "100%"
}, mn = { class: "insta-main" }, yn = {
  key: 0,
  style: { color: "red", "font-size": "1.2em", margin: "1rem", border: "1px dashed red", padding: "1rem" }
}, je = /* @__PURE__ */ O({
  __name: "App",
  props: {
    meta: {}
  },
  setup(e) {
    const t = e, { meta: n } = t, { debug: r = !1 } = n;
    Dt(n), (n.mode === "web" || n.mode === "webview") && (un(n.mode), hn(n.appIcons)), fn(n.mode);
    const { hasError: s, errorMessage: o } = an(r);
    return (a, i) => (L(), N("div", pn, [
      Ge("div", mn, [
        se(a.$slots, "default"),
        X(s) ? (L(), N("div", yn, qe(X(o)), 1)) : ye("", !0)
      ])
    ]));
  }
}), Re = /* @__PURE__ */ new Map([
  [
    "size",
    {
      classes: "ist-r-size",
      handler: (e) => gn(e)
    }
  ],
  [
    "weight",
    {
      classes: "ist-r-weight",
      styleVar: "--weight",
      handler: (e) => e
    }
  ],
  [
    "text_align",
    {
      classes: "ist-r-ta",
      styleVar: "--ta",
      handler: (e) => e
    }
  ],
  [
    "trim",
    {
      classes: (e) => vn("ist-r", e)
    }
  ],
  [
    "truncate",
    {
      classes: "ist-r-truncate"
    }
  ],
  [
    "text_wrap",
    {
      classes: "ist-r-tw",
      handler: (e) => wn(e)
    }
  ]
]);
function ut(e) {
  const t = {}, n = [], r = {};
  for (const [o, a] of Object.entries(e)) {
    if (a === void 0 || !Re.has(o))
      continue;
    const i = typeof a == "object" ? a : { initial: a };
    for (const [c, l] of Object.entries(i)) {
      const { classes: u, styleVar: f, handler: d, propHandler: h } = Re.get(o), p = c === "initial";
      if (u) {
        const m = typeof u == "function" ? u(l) : u, v = p ? m : `${c}:${m}`;
        n.push(v);
      }
      if (d) {
        const m = d(l);
        if (f) {
          const v = p ? f : `${f}-${c}`;
          t[v] = m;
        } else {
          if (!Array.isArray(m))
            throw new Error(`Invalid style value: ${m}`);
          m.forEach((v) => {
            for (const [C, V] of Object.entries(v))
              t[C] = V;
          });
        }
      }
      if (h) {
        const m = h(l);
        for (const [v, C] of Object.entries(m))
          r[v] = C;
      }
    }
  }
  return {
    classes: n.join(" "),
    style: t,
    props: r
  };
}
function gn(e) {
  const t = Number(e);
  if (isNaN(t))
    throw new Error(`Invalid font size value: ${e}`);
  return [
    { "--fs": `var(--font-size-${t})` },
    { "--lh": `var(--line-height-${t})` },
    { "--ls": `var(--letter-spacing-${t})` }
  ];
}
function vn(e, t) {
  return `${e}-lt-${t}`;
}
function wn(e) {
  if (e === "wrap")
    return [
      {
        "--ws": "normal"
      }
    ];
  if (e === "nowrap")
    return [
      {
        "--ws": "nowrap"
      }
    ];
  if (e === "pretty")
    return [{ "--ws": "normal" }, { "--tw": "pretty" }];
  if (e === "balance")
    return [{ "--ws": "normal" }, { "--tw": "balance" }];
  throw new Error(`Invalid text wrap value: ${e}`);
}
const bn = "insta-Heading", _n = O(Sn, {
  props: [
    "as",
    "as_child",
    "size",
    "weight",
    "align",
    "trim",
    "truncate",
    "text_wrap",
    "innerText"
  ]
});
function Sn(e) {
  return () => {
    const { classes: t, style: n, props: r } = ut(e), s = F(
      { class: t, style: n, ...r },
      { class: bn }
    );
    return E(e.as || "h1", s, e.innerText);
  };
}
const En = /* @__PURE__ */ O({
  __name: "_Teleport",
  props: {
    to: {},
    defer: { type: Boolean, default: !0 },
    disabled: { type: Boolean, default: !1 }
  },
  setup(e) {
    return (t, n) => (L(), Qe(Ct, {
      to: t.to,
      defer: t.defer,
      disabled: t.disabled
    }, [
      se(t.$slots, "default")
    ], 8, ["to", "defer", "disabled"]));
  }
}), kn = ["width", "height", "color"], Vn = ["xlink:href"], Cn = /* @__PURE__ */ O({
  __name: "Icon",
  props: {
    size: {},
    icon: {},
    color: {},
    assetPath: {},
    svgName: {},
    rawSvg: {}
  },
  setup(e) {
    const t = e, n = I(() => t.icon ? t.icon.split(":")[1] : ""), r = I(() => t.size || "1em"), s = I(() => t.color || "currentColor"), o = I(() => t.rawSvg || null), a = A(() => `#${t.icon}`), i = ke(), c = dn(o, {
      size: I(() => t.size),
      color: I(() => t.color),
      attrs: i
    });
    return (l, u) => (L(), N(Z, null, [
      n.value ? (L(), N("svg", F({
        key: 0,
        width: r.value,
        height: r.value,
        color: s.value
      }, X(i)), [
        Ge("use", { "xlink:href": a.value }, null, 8, Vn)
      ], 16, kn)) : ye("", !0),
      o.value ? (L(), Qe(X(c), { key: 1 })) : ye("", !0)
    ], 64));
  }
}), Y = /* @__PURE__ */ new Map([
  [
    "p",
    {
      classes: "ist-r-p",
      styleVar: "--p",
      handler: (e) => w("space", e)
    }
  ],
  [
    "px",
    {
      classes: "ist-r-px",
      styleVar: "--px",
      handler: (e) => w("space", e)
    }
  ],
  [
    "py",
    {
      classes: "ist-r-py",
      styleVar: "--py",
      handler: (e) => w("space", e)
    }
  ],
  [
    "pt",
    {
      classes: "ist-r-pt",
      styleVar: "--pt",
      handler: (e) => w("space", e)
    }
  ],
  [
    "pb",
    {
      classes: "ist-r-pb",
      styleVar: "--pb",
      handler: (e) => w("space", e)
    }
  ],
  [
    "pl",
    {
      classes: "ist-r-pl",
      styleVar: "--pl",
      handler: (e) => w("space", e)
    }
  ],
  [
    "pr",
    {
      classes: "ist-r-pr",
      styleVar: "--pr",
      handler: (e) => w("space", e)
    }
  ],
  [
    "width",
    {
      classes: "ist-r-w",
      styleVar: "--width",
      handler: (e) => e
    }
  ],
  [
    "height",
    {
      classes: "ist-r-h",
      styleVar: "--height",
      handler: (e) => e
    }
  ],
  [
    "min_width",
    {
      classes: "ist-r-min-w",
      styleVar: "--min_width",
      handler: (e) => e
    }
  ],
  [
    "min_height",
    {
      classes: "ist-r-min-h",
      styleVar: "--min_height",
      handler: (e) => e
    }
  ],
  [
    "max_width",
    {
      classes: "ist-r-max-w",
      styleVar: "--max_width",
      handler: (e) => e
    }
  ],
  [
    "max_height",
    {
      classes: "ist-r-max-h",
      styleVar: "--max_height",
      handler: (e) => e
    }
  ],
  [
    "position",
    {
      classes: "ist-r-position",
      styleVar: "--position",
      handler: (e) => e
    }
  ],
  [
    "inset",
    {
      classes: "ist-r-inset",
      styleVar: "--inset",
      handler: (e) => w("space", e)
    }
  ],
  [
    "top",
    {
      classes: "ist-r-top",
      styleVar: "--top",
      handler: (e) => w("space", e)
    }
  ],
  [
    "right",
    {
      classes: "ist-r-right",
      styleVar: "--right",
      handler: (e) => w("space", e)
    }
  ],
  [
    "bottom",
    {
      classes: "ist-r-bottom",
      styleVar: "--bottom",
      handler: (e) => w("space", e)
    }
  ],
  [
    "left",
    {
      classes: "ist-r-left",
      styleVar: "--left",
      handler: (e) => w("space", e)
    }
  ],
  [
    "overflow",
    {
      classes: "ist-r-overflow",
      styleVar: "--overflow",
      handler: (e) => e
    }
  ],
  [
    "overflow_x",
    {
      classes: "ist-r-ox",
      styleVar: "--overflow_x",
      handler: (e) => e
    }
  ],
  [
    "overflow_y",
    {
      classes: "ist-r-oy",
      styleVar: "--overflow_y",
      handler: (e) => e
    }
  ],
  [
    "flex_basis",
    {
      classes: "ist-r-fb",
      styleVar: "--flex_basis",
      handler: (e) => e
    }
  ],
  [
    "flex_shrink",
    {
      classes: "ist-r-fs",
      styleVar: "--flex_shrink",
      handler: (e) => e
    }
  ],
  [
    "flex_grow",
    {
      classes: "ist-r-fg",
      styleVar: "--flex_grow",
      handler: (e) => e
    }
  ],
  [
    "grid_area",
    {
      classes: "ist-r-ga",
      styleVar: "--grid_area",
      handler: (e) => e
    }
  ],
  [
    "grid_column",
    {
      classes: "ist-r-gc",
      styleVar: "--grid_column",
      handler: (e) => e
    }
  ],
  [
    "grid_column_start",
    {
      classes: "ist-r-gcs",
      styleVar: "--grid_column_start",
      handler: (e) => e
    }
  ],
  [
    "grid_column_end",
    {
      classes: "ist-r-gce",
      styleVar: "--grid_column_end",
      handler: (e) => e
    }
  ],
  [
    "grid_row",
    {
      classes: "ist-r-gr",
      styleVar: "--grid_row",
      handler: (e) => e
    }
  ],
  [
    "grid_row_start",
    {
      classes: "ist-r-grs",
      styleVar: "--grid_row_start",
      handler: (e) => e
    }
  ],
  [
    "grid_row_end",
    {
      classes: "ist-r-gre",
      styleVar: "--grid_row_end",
      handler: (e) => e
    }
  ],
  [
    "m",
    {
      classes: "ist-r-m",
      styleVar: "--m",
      handler: (e) => w("space", e)
    }
  ],
  [
    "mx",
    {
      classes: "ist-r-mx",
      styleVar: "--mx",
      handler: (e) => w("space", e)
    }
  ],
  [
    "my",
    {
      classes: "ist-r-my",
      styleVar: "--my",
      handler: (e) => w("space", e)
    }
  ],
  [
    "mt",
    {
      classes: "ist-r-mt",
      styleVar: "--mt",
      handler: (e) => w("space", e)
    }
  ],
  [
    "mr",
    {
      classes: "ist-r-mr",
      styleVar: "--mr",
      handler: (e) => w("space", e)
    }
  ],
  [
    "mb",
    {
      classes: "ist-r-mb",
      styleVar: "--mb",
      handler: (e) => w("space", e)
    }
  ],
  [
    "ml",
    {
      classes: "ist-r-ml",
      styleVar: "--ml",
      handler: (e) => w("space", e)
    }
  ],
  [
    "display",
    {
      classes: "ist-r-display",
      styleVar: "--display",
      handler: (e) => e
    }
  ],
  [
    "direction",
    {
      classes: "ist-r-fd",
      styleVar: "--direction",
      handler: (e) => e
    }
  ],
  [
    "align",
    {
      classes: "ist-r-ai",
      styleVar: "--align",
      handler: (e) => e
    }
  ],
  [
    "justify",
    {
      classes: "ist-r-jc",
      styleVar: "--justify",
      handler: (e) => e
    }
  ],
  [
    "wrap",
    {
      classes: "ist-r-wrap",
      styleVar: "--wrap",
      handler: (e) => e
    }
  ],
  [
    "gap",
    {
      classes: "ist-r-gap",
      styleVar: "--gap",
      handler: (e) => w("space", e)
    }
  ],
  [
    "gap_x",
    {
      classes: "ist-r-cg",
      styleVar: "--gap_x",
      handler: (e) => w("space", e)
    }
  ],
  [
    "gap_y",
    {
      classes: "ist-r-rg",
      styleVar: "--gap_y",
      handler: (e) => w("space", e)
    }
  ],
  [
    "areas",
    {
      classes: "ist-r-gta",
      styleVar: "--areas",
      handler: (e) => e
    }
  ],
  [
    "columns",
    {
      classes: "ist-r-gtc",
      styleVar: "--columns",
      handler: (e) => Fe(e)
    }
  ],
  [
    "rows",
    {
      classes: "ist-r-gtr",
      styleVar: "--rows",
      handler: (e) => Fe(e)
    }
  ],
  [
    "flow",
    {
      classes: "ist-r-gaf",
      styleVar: "--flow",
      handler: (e) => e
    }
  ],
  [
    "ctn_size",
    {
      classes: "ist-r-ctn_size",
      styleVar: "--ctn_size",
      handler: (e) => w("container", e)
    }
  ]
]);
function ce(e) {
  e.length > 1 && console.warn("Only accept one child element when as_child is true");
}
function le(e) {
  return Object.fromEntries(
    Object.entries(e).filter(([t, n]) => n !== void 0)
  );
}
function ue(e, t) {
  const n = {}, r = [], s = new Set(t || []), o = {
    style: {},
    class: []
  };
  for (const [i, c] of Object.entries(e)) {
    if (!Y.has(i))
      continue;
    const l = typeof c == "object" ? c : { initial: c };
    for (const [u, f] of Object.entries(l)) {
      const { classes: d, styleVar: h, handler: p } = Y.get(i), m = u === "initial", v = m ? d : `${u}:${d}`, C = m ? h : `${h}-${u}`, V = p(f);
      if (s.has(i)) {
        o.class.push(v), o.style[C] = V;
        continue;
      }
      r.push(v), n[C] = V;
    }
  }
  return {
    classes: r.join(" "),
    style: n,
    excludeReslut: o
  };
}
function w(e, t) {
  const n = Number(t);
  if (isNaN(n))
    return t;
  {
    const r = n < 0 ? -1 : 1;
    return `calc(var(--${e}-${n}) * ${r})`;
  }
}
function Fe(e) {
  const t = Number(e);
  return isNaN(t) ? e : `repeat(${t}, 1fr)`;
}
const fe = [
  "p",
  "px",
  "py",
  "pt",
  "pb",
  "pl",
  "pr",
  "width",
  "height",
  "min_width",
  "min_height",
  "max_width",
  "max_height",
  "position",
  "inset",
  "top",
  "right",
  "bottom",
  "left",
  "overflow",
  "overflow_x",
  "overflow_y",
  "flex_basis",
  "flex_shrink",
  "flex_grow",
  "grid_area",
  "grid_column",
  "grid_column_start",
  "grid_column_end",
  "grid_row",
  "grid_row_start",
  "grid_row_end",
  "m",
  "mx",
  "my",
  "mt",
  "mr",
  "mb",
  "ml"
], xn = [
  "as",
  "as_child",
  "display",
  "align",
  "justify",
  "wrap",
  "gap",
  "gap_x",
  "gap_y"
].concat(fe), An = ["direction"].concat(xn), On = [
  "as_child",
  "size",
  "display",
  "align",
  "ctn_size"
].concat(fe), $n = ["as", "as_child", "display"].concat(fe), Tn = [
  "as",
  "as_child",
  "display",
  "areas",
  "columns",
  "rows",
  "flow",
  "align",
  "justify",
  "gap",
  "gap_x",
  "gap_y"
].concat(fe), Pn = "insta-Box", Nn = O(jn, {
  props: $n
});
function jn(e) {
  const t = J();
  return () => {
    var i;
    const n = le(e), { classes: r, style: s } = ue(n), o = F(
      { class: r, style: s },
      { class: Pn }
    ), a = (i = t.default) == null ? void 0 : i.call(t);
    return e.as_child && a && a.length > 0 ? (ce(a), D(a[0], o)) : E(e.as || "div", o, a);
  };
}
const Rn = "insta-Flex", Fn = {
  gap: "2"
}, Dn = O(In, {
  props: An
});
function In(e) {
  const t = J();
  return () => {
    var i;
    const n = { ...Fn, ...le(e) }, { classes: r, style: s } = ue(n), o = F(
      { class: r, style: s },
      { class: Rn }
    ), a = (i = t.default) == null ? void 0 : i.call(t);
    return e.as_child && a && a.length > 0 ? (ce(a), D(a[0], o)) : E(e.as || "div", o, a);
  };
}
const Ln = "insta-Grid", Mn = {
  gap: "2"
}, Bn = O(zn, {
  props: Tn
});
function zn(e) {
  const t = J();
  return () => {
    var c;
    const n = { ...Mn, ...le(e) }, r = ue(n), [s, o] = Un(r.classes, r.style), a = F(
      { class: s, style: o },
      { class: Ln }
    ), i = (c = t.default) == null ? void 0 : c.call(t);
    return e.as_child && i && i.length > 0 ? (ce(i), D(i[0], a)) : E(e.as || "div", a, i);
  };
}
function Un(e, t) {
  const n = Y.get("areas").styleVar, r = Y.get("columns").styleVar, s = n in t, o = r in t;
  if (!s || o)
    return [e, t];
  const a = Wn(t[n]);
  if (a) {
    const { classes: i, styleVar: c } = Y.get("columns");
    e = `${e} ${i}`, t[c] = a;
  }
  return [e, t];
}
function Wn(e) {
  if (typeof e != "string") return null;
  const t = [...e.matchAll(/"([^"]+)"/g)].map((a) => a[1]);
  if (t.length === 0) return null;
  const s = t[0].trim().split(/\s+/).length;
  return t.every(
    (a) => a.trim().split(/\s+/).length === s
  ) ? `repeat(${s}, 1fr)` : null;
}
const Hn = "insta-Container", Jn = O(Kn, {
  props: On
});
function Kn(e) {
  const t = J();
  return () => {
    var l;
    const n = le(e), { classes: r, style: s, excludeReslut: o } = ue(n, [
      "ctn_size"
    ]), a = F(
      { class: r, style: s },
      { class: Hn }
    ), i = (l = t.default) == null ? void 0 : l.call(t);
    if (e.as_child && i && i.length > 0)
      return ce(i), D(i[0], a);
    const c = E(
      "div",
      F({ class: "insta-ContainerInner" }, o),
      i
    );
    return E("div", a, c);
  };
}
const Gn = "insta-Text", qn = O(Qn, {
  props: [
    "as",
    "as_child",
    "size",
    "weight",
    "align",
    "trim",
    "truncate",
    "text_wrap",
    "innerText"
  ]
});
function Qn(e) {
  return () => {
    const { classes: t, style: n, props: r } = ut(e), s = F(
      { class: t, style: n, ...r },
      { class: Gn }
    );
    return E(e.as || "span", s, e.innerText);
  };
}
const De = "insta-Link", Yn = O(Xn, {
  props: ["href", "text", "target", "type"]
});
function Xn(e) {
  const t = J().default;
  return () => {
    const n = t ? [De, "has-child"] : [De], r = {
      href: e.href,
      target: e.target,
      type: e.type,
      class: n
    };
    return E("a", r, t ? t() : e.text);
  };
}
const pe = /* @__PURE__ */ new Map();
function Zn(e, t, n, r) {
  const s = `${e}|${n ?? ""}`;
  if (pe.has(s))
    return pe.get(s);
  const o = /* @__PURE__ */ new WeakMap(), i = { observer: new IntersectionObserver(
    (c) => {
      for (const l of c) {
        const u = o.get(l.target);
        u && u(l.isIntersecting);
      }
    },
    {
      root: r,
      rootMargin: e,
      threshold: t
    }
  ), callbacks: o };
  return pe.set(s, i), i;
}
function er(e, t, n) {
  const r = n.margin ?? "0px", s = n.threshold ?? 0;
  let o = null;
  const a = () => {
    if (!e.value || n.enabled.value === !1) return;
    let l = null;
    n.rootSelector && (l = document.querySelector(n.rootSelector)), o = Zn(
      r,
      s,
      n.rootSelector,
      l
    ), o.callbacks.set(e.value, t), o.observer.observe(e.value);
  }, i = () => {
    o && e.value && (o.observer.unobserve(e.value), o.callbacks.delete(e.value));
  }, c = () => {
    if (e.value) {
      if (!o) {
        a();
        return;
      }
      o.callbacks.set(e.value, t), o.observer.observe(e.value);
    }
  };
  Ee(() => {
    a();
  }), We(() => {
    o && e.value && (o.observer.unobserve(e.value), o.callbacks.delete(e.value));
  }), $(
    () => n.enabled.value,
    (l, u) => {
      l !== u && (l ? c() : i());
    },
    { immediate: !1 }
  );
}
const tr = /* @__PURE__ */ O({
  __name: "Lazy-Render",
  props: {
    height: {
      type: String,
      default: "200px"
    },
    destroyOnLeave: {
      type: Boolean,
      default: !0
    },
    margin: {
      type: String,
      default: "0px"
    },
    root: {
      type: String,
      default: void 0
    },
    disable: {
      type: Boolean,
      default: !1
    }
  },
  emits: ["visibility"],
  setup(e, { emit: t }) {
    const n = t, r = e, s = xt("container"), o = k(!1), a = A(() => !r.disable);
    return er(
      s,
      (i) => {
        n("visibility", i), i ? o.value = !0 : r.destroyOnLeave && (o.value = !1);
      },
      {
        margin: r.margin,
        rootSelector: r.root,
        enabled: a
      }
    ), (i, c) => (L(), N("div", {
      ref_key: "container",
      ref: s,
      style: ge({ minHeight: e.height, position: "relative" })
    }, [
      o.value ? se(i.$slots, "default", { key: 0 }) : se(i.$slots, "hidden", { key: 1 })
    ], 4));
  }
});
function ft(e) {
  var n;
  if (!e) return e;
  const t = (n = z().serverInfo) == null ? void 0 : n.assets_url;
  try {
    return new URL(e), e;
  } catch {
    let r = e;
    return r.startsWith("/assets/") && (r = r.slice(7)), r.startsWith("/") || (r = "/" + r), t.replace(/\/$/, "") + r;
  }
}
const nr = O(rr, {
  props: ["src"]
});
function rr(e) {
  const t = ke();
  return () => E("img", {
    ...t.value,
    src: ft(e.src)
  });
}
const sr = O(or, {
  props: ["src"]
});
function or(e) {
  const t = ke();
  return () => E("video", {
    ...t.value,
    src: ft(e.src)
  });
}
function ar(e, t) {
  if (!t)
    return e;
  const n = [];
  return t.forEach((r) => {
    const { sys: s = 0, name: o, arg: a, mf: i } = r;
    if (o === "vmodel") {
      const c = r.value;
      if (e = D(e, {
        [`onUpdate:${a}`]: (l) => {
          c.value = l;
        }
      }), s === 1) {
        const l = i ? Object.fromEntries(i.map((u) => [u, !0])) : {};
        n.push([At, c.value, void 0, l]);
      } else
        e = D(e, {
          [a]: c.value
        });
    } else if (o === "vshow") {
      const c = y(r.value);
      n.push([Ot, c]);
    } else
      console.warn(`Directive ${o} is not supported yet`);
  }), n.length > 0 ? Ye(e, n) : e;
}
function Ie(e, t) {
  Object.entries(e).forEach(([n, r]) => t(r, n));
}
function be(e, t) {
  return ir(e, {
    valueFn: t
  });
}
function ir(e, t) {
  const { valueFn: n, keyFn: r } = t;
  return Object.fromEntries(
    Object.entries(e).map(([s, o], a) => [
      r ? r(s, o) : s,
      n(o, s, a)
    ])
  );
}
const cr = window.structuredClone || ((e) => JSON.parse(JSON.stringify(e)));
function Ae(e) {
  if (typeof e == "function")
    return e;
  try {
    return cr(Xe(y(e)));
  } catch {
    return e;
  }
}
class lr {
  toString() {
    return "";
  }
}
const W = new lr();
function H(e) {
  return Xe(e) === W;
}
function ur(e) {
  if (!e)
    return null;
  const t = {}, {
    bProps: n = {},
    pProps: r = [],
    sProps: s = {},
    ref: o
  } = e;
  return oe(s), Ie(n, (a, i) => {
    const c = y(a);
    H(c) || (oe(c), t[i] = fr(c, i));
  }), r.forEach((a) => {
    const i = y(a);
    typeof i == "object" && Ie(i, (c, l) => {
      const { name: u, value: f } = Ft(l, c);
      t[u] = f;
    });
  }), o && (t.ref = o), { ...s, ...t };
}
function fr(e, t) {
  return t === "innerText" ? qe(e) : e;
}
function dr(e) {
  if (!e)
    return;
  if (typeof e == "string")
    return {
      class: Te(e)
    };
  const { sClass: t, mClass: n, bClass: r } = e, s = [];
  return t && s.push(...t), n && s.push(be(n, y)), r && s.push(...r.map(y)), {
    class: Te(s)
  };
}
function hr(e) {
  if (!e)
    return;
  if (typeof e == "string")
    return {
      style: ge(e)
    };
  const t = [], {
    sStyle: n = {},
    bStyle: r = {},
    pStyle: s = []
  } = e;
  return t.push(be(n, y)), t.push(be(r, y)), t.push(...s.map(y)), {
    style: ge([n, t])
  };
}
class pr extends Map {
  constructor(t) {
    super(), this.factory = t;
  }
  getOrDefault(t) {
    if (!this.has(t)) {
      const n = this.factory();
      return this.set(t, n), n;
    }
    return super.get(t);
  }
}
function mr(e) {
  return new pr(e);
}
function yr(e, t, n) {
  const r = mr(() => []);
  for (const [s, o] of Object.entries(t ?? {}))
    (Array.isArray(o) ? o : [o]).forEach((a) => {
      const { handleEvent: i, modifier: c = [] } = a, { eventName: l, handleEvent: u } = gr({
        eventName: s,
        modifier: c,
        handleEvent: i
      });
      r.getOrDefault(l).push(u);
    });
  if (e = D(e, wr(r.entries())), n) {
    const s = {};
    if (n.mounted) {
      const o = Array.isArray(n.mounted) ? n.mounted : [n.mounted];
      s.mounted = function(a) {
        for (const i of o)
          i.handleEvent(a);
      };
    }
    e = Ye(e, [[s]]);
  }
  return e;
}
function gr(e) {
  const { eventName: t, handleEvent: n, modifier: r = [] } = e;
  if (r.length === 0)
    return {
      eventName: t,
      handleEvent: n
    };
  const s = ["passive", "capture", "once"], o = [], a = [];
  for (const l of r)
    s.includes(l) ? o.push(l[0].toUpperCase() + l.slice(1)) : a.push(l);
  const i = o.length > 0 ? t + o.join("") : t, c = a.length > 0 ? $t(n, a) : n;
  return {
    eventName: i,
    handleEvent: c
  };
}
function vr(e, t) {
  return (...n) => {
    for (const r of e)
      try {
        const s = r(...n);
        s instanceof Promise && s.catch((o) => {
          console.error(
            "[EventHandler Error]",
            {
              event: t == null ? void 0 : t.eventName,
              component: t == null ? void 0 : t.componentName,
              handler: r
            },
            o
          );
        });
      } catch (s) {
        console.error(
          "[EventHandler Error]",
          {
            event: t == null ? void 0 : t.eventName,
            component: t == null ? void 0 : t.componentName,
            handler: r
          },
          s
        );
      }
  };
}
function wr(e) {
  const t = {};
  for (const [n, r] of e)
    t[n] = vr(r, {
      eventName: n
    });
  return t;
}
function es(e) {
  const { tag: t, props: n, classes: r, style: s, slots: o, dirs: a, events: i, lifeEvents: c } = e, l = y(t), u = Tt(l), f = typeof u == "string", d = {
    ...ur(n),
    ...dr(r),
    ...hr(s)
  };
  let h = E(u, d, br(o, f));
  return h = yr(h, i, c), ar(h, a);
}
function br(e, t) {
  return !e || !t ? e : typeof e == "function" ? e() : e;
}
const ae = Symbol("instaui-scope");
function dt(e) {
  return Object.create(e || null);
}
function ht() {
  let e = et(ae, null);
  return e || (e = dt(), Ze(ae, e), e);
}
function _r(e) {
  const t = ht(), n = dt(t);
  return Object.assign(n, e), Ze(ae, n), n;
}
function Sr() {
  const e = et(ae, null);
  if (!e) throw new Error("Scope not initialized");
  return e;
}
function ts(e, t) {
  return E(Er, t, () => E(e));
}
const Er = O(kr, {
  props: ["vfor"]
});
function kr(e) {
  const t = J().default, { vfor: n } = e, r = {};
  if (n) {
    const { value: s, index: o, itemKey: a } = n;
    o && o.forEach(([i, c]) => {
      r[i] = k(c);
    }), s && s.forEach(([i, c]) => {
      r[i] = k(c);
    }), a && a.forEach(([i, c]) => {
      r[i] = k(c);
    }), _r(r);
  }
  return () => {
    if (e.vfor) {
      const { value: s, index: o, itemKey: a } = e.vfor;
      o && o.forEach(([i, c]) => {
        r[i].value = c;
      }), s && s.forEach(([i, c]) => {
        r[i].value = c;
      }), a && a.forEach(([i, c]) => {
        r[i].value = c;
      });
    }
    return t == null ? void 0 : t();
  };
}
function Le(e, t) {
  return !H(e) && JSON.stringify(t) === JSON.stringify(e);
}
function Oe(e) {
  if (P(e)) {
    const t = e;
    return re(() => ({
      get() {
        return y(t);
      },
      set(n) {
        const r = y(t);
        Le(r, n) || (t.value = n);
      }
    }));
  }
  return re((t, n) => ({
    get() {
      return t(), e;
    },
    set(r) {
      Le(e, r) || (e = r, n());
    }
  }));
}
function pt(e) {
  return Pt(e) || e instanceof Element;
}
function ns(e) {
  const { init: t, deepEqOnInput: n } = e || {};
  return n === void 0 ? ie(t ?? W) : Oe(t ?? W);
}
function mt(e) {
  const { config: t } = e;
  if (!t)
    return {
      run: () => {
      },
      tryReset: () => {
      }
    };
  const n = t.map((o) => {
    const [a, i, c] = o;
    function l(u, f) {
      const { type: d, value: h } = f;
      if (d === "const") {
        u.value = h;
        return;
      }
      if (d === "action") {
        const p = Vr(h);
        u.value = p;
        return;
      }
    }
    return {
      run: () => l(a, i),
      reset: () => l(a, c)
    };
  });
  return {
    run: () => {
      n.forEach((o) => o.run());
    },
    tryReset: () => {
      n.forEach((o) => o.reset());
    }
  };
}
function Vr(e) {
  const { inputs: t = [], code: n } = e, r = T(n), s = t.map(y);
  return r(...s);
}
function Me(e) {
  return e == null;
}
const Q = {
  Ref: 0,
  ElementRefAction: 2,
  JsCode: 3,
  FileDownload: 4
};
class yt extends Error {
  constructor(t) {
    super(t), this.name = "BrowserNotSupportedError";
  }
}
function gt(e, t) {
  switch (t) {
    case "kb":
      return e * 1024;
    case "mb":
      return e * 1024 * 1024;
    case "gb":
      return e * 1024 * 1024 * 1024;
    default:
      return e;
  }
}
class Cr {
  constructor(t, n) {
    _(this, "filename");
    _(this, "filepath");
    _(this, "chuckedConfig");
    _(this, "onProgress");
    _(this, "onStatus");
    _(this, "controller", null);
    _(this, "receivedBytes", 0);
    _(this, "totalBytes", 0);
    _(this, "chunks", []);
    _(this, "downloading", !1);
    this.url = t, this.filename = n.filename, this.filepath = n.filepath, this.chuckedConfig = n.config, this.onProgress = () => {
    }, this.onStatus = () => {
    };
  }
  async start() {
    this.downloading || (this.downloading = !0, await this.fetchChunk(this.receivedBytes));
  }
  pause() {
    var t;
    this.downloading && (this.downloading = !1, (t = this.controller) == null || t.abort());
  }
  async resume() {
    this.downloading || (this.downloading = !0, await this.fetchChunk(this.receivedBytes));
  }
  async fetchChunk(t) {
    var l;
    this.controller = new AbortController();
    const n = gt(
      this.chuckedConfig.chunk_size,
      this.chuckedConfig.chunk_size_unit
    ), r = new URLSearchParams({
      filepath: this.filepath,
      mode: "chunked",
      chunk_bytes: n.toString()
    }), s = `${this.url}?` + r.toString(), o = t ? { Range: `bytes=${t}-` } : {}, a = await fetch(s, {
      headers: o,
      signal: this.controller.signal
    });
    if (!a.ok && a.status !== 206 && a.status !== 200) {
      this.downloading = !1;
      return;
    }
    const i = a.headers.get("Content-Range");
    this.totalBytes = i && parseInt(i.split("/")[1]) || parseInt(a.headers.get("Content-Length") || "0", 10);
    const c = (l = a.body) == null ? void 0 : l.getReader();
    if (!c)
      throw new yt("Browser does not support streaming download");
    for (; this.downloading; ) {
      const { done: u, value: f } = await c.read();
      if (u) break;
      f && (this.chunks.push(f), this.receivedBytes += f.length, this.updateProgress());
    }
    this.receivedBytes >= this.totalBytes && this.finish();
  }
  updateProgress() {
    if (this.totalBytes > 0) {
      const t = parseFloat(
        (this.receivedBytes / this.totalBytes * 100).toFixed(2)
      );
      this.onProgress(t);
    } else
      (this.receivedBytes / 1024 / 1024).toFixed(2);
  }
  finish() {
    this.downloading = !1;
    const t = this.chunks.reduce(
      (a, i) => a + i.length,
      0
    ), n = new Uint8Array(t);
    let r = 0;
    for (const a of this.chunks)
      n.set(a, r), r += a.length;
    const s = new Blob([n]), o = document.createElement("a");
    o.href = URL.createObjectURL(s), o.download = this.filename, o.click(), URL.revokeObjectURL(o.href), this.chunks = [];
  }
  get progress() {
    return { received: this.receivedBytes, total: this.totalBytes };
  }
  get isDownloading() {
    return this.downloading;
  }
}
class _e {
  constructor(t, n) {
    _(this, "filename");
    _(this, "filepath");
    _(this, "onProgress");
    _(this, "onStatus");
    _(this, "controller", null);
    _(this, "receivedBytes", 0);
    _(this, "totalBytes", 0);
    _(this, "downloading", !1);
    this.url = t, this.filename = n.filename, this.filepath = n.filepath, this.onProgress = () => {
    }, this.onStatus = () => {
    };
  }
  async start() {
    this.downloading || (this.downloading = !0, await this.downloadFile());
  }
  pause() {
    var t;
    this.downloading && (this.downloading = !1, (t = this.controller) == null || t.abort());
  }
  async downloadFile() {
    var r;
    this.controller = new AbortController();
    const t = new URLSearchParams({ filepath: this.filepath }), n = `${this.url}?` + t.toString();
    try {
      const s = await fetch(n, {
        signal: this.controller.signal
      });
      if (!s.ok) {
        this.onStatus(`Download failed: ${s.statusText}`), this.downloading = !1;
        return;
      }
      this.totalBytes = parseInt(s.headers.get("Content-Length") || "0", 10);
      const o = (r = s.body) == null ? void 0 : r.getReader();
      if (!o) {
        this.onStatus("Web Browser not support download file"), this.downloading = !1;
        return;
      }
      const a = [];
      for (; this.downloading; ) {
        const { done: i, value: c } = await o.read();
        if (i) break;
        c && (a.push(c), this.receivedBytes += c.length, this.updateProgress());
      }
      this.receivedBytes >= this.totalBytes && this.finishDownload(a);
    } catch (s) {
      this.onStatus(`Download error: ${s instanceof Error ? s.message : String(s)}`), this.downloading = !1;
    }
  }
  updateProgress() {
    if (this.totalBytes > 0) {
      const t = parseFloat(
        (this.receivedBytes / this.totalBytes * 100).toFixed(2)
      );
      this.onProgress(t);
    }
  }
  finishDownload(t) {
    this.downloading = !1;
    const n = t.reduce((i, c) => i + c.length, 0), r = new Uint8Array(n);
    let s = 0;
    for (const i of t)
      r.set(i, s), s += i.length;
    const o = new Blob([r]), a = document.createElement("a");
    a.href = URL.createObjectURL(o), a.download = this.filename, a.click(), URL.revokeObjectURL(a.href);
  }
  get progress() {
    return { received: this.receivedBytes, total: this.totalBytes };
  }
  get isDownloading() {
    return this.downloading;
  }
}
async function xr(e) {
  const t = z().serverInfo.download_url;
  if (e.mode === "auto") {
    if (!e.config)
      throw new Error("Auto mode requires config parameters");
    const n = e.config, r = gt(
      n.threshold_size,
      n.threshold_size_unit
    );
    e.filesize < r ? await new _e(t, e).start() : await Be(t, e);
    return;
  }
  if (e.mode === "chunked") {
    await Be(t, e);
    return;
  }
  if (e.mode === "standard") {
    await new _e(t, e).start();
    return;
  }
}
async function Be(e, t) {
  try {
    await new Cr(e, t).start();
  } catch (n) {
    if (n instanceof yt)
      await new _e(e, t).start();
    else
      throw n;
  }
}
function Ar(e, t, n) {
  if (!t.length)
    return;
  let s = y(e);
  for (let a = 0; a < t.length - 1; a++) {
    const i = t[a];
    if (s[i] === null || s[i] === void 0) {
      const c = t[a + 1];
      s[i] = typeof c == "number" ? [] : {};
    }
    s = s[i];
  }
  const o = t[t.length - 1];
  s[o] = n;
}
function de(e, t, n) {
  if (Me(t) || Me(e.values))
    return;
  t = t, n = n ?? Array.from({ length: t.length }).fill(
    Q.Ref
  );
  const r = e.values, s = e.types ?? Array.from({ length: t.length }).fill(0);
  t.forEach((o, a) => {
    const i = s[a], c = n[a];
    if (i !== 1) {
      if (c === Q.Ref) {
        if (i === 2) {
          r[a].forEach(([u, f]) => {
            Ar(o, u, f);
          });
          return;
        }
        o.value = r[a];
        return;
      }
      if (c === Q.ElementRefAction) {
        const l = o.value, u = r[a], { method: f, args: d = [] } = u;
        l[f](...d);
        return;
      }
      if (c === Q.JsCode) {
        const l = r[a];
        if (!l)
          return;
        const u = T(l);
        Promise.resolve(u());
        return;
      }
      if (c === Q.FileDownload) {
        const l = r[a];
        xr(l);
        return;
      }
      o.value = r[a];
    }
  });
}
function* Or(e, t) {
  const n = e[Symbol.iterator](), r = t[Symbol.iterator]();
  for (; ; ) {
    const s = n.next(), o = r.next();
    if (s.done || o.done) return;
    yield [s.value, o.value];
  }
}
function $r(e) {
  let t = 1;
  const n = [];
  let r = !1, s = !1;
  async function o(u) {
    await Tr(u);
  }
  function a() {
    for (const u of n)
      if ([...e.get(u.config)].filter(
        (h) => n.some((p) => p.config === h)
      ).length === 0)
        return n.splice(n.indexOf(u), 1), u;
    return null;
  }
  async function i() {
    if (!r) {
      r = !0;
      try {
        for (; ; ) {
          const u = a();
          if (!u) break;
          await o(u);
        }
      } finally {
        r = !1;
      }
    }
  }
  function c() {
    s || (s = !0, Promise.resolve().then(() => {
      s = !1, i().catch((u) => {
        console.error("flushTasks error", u);
      });
    }));
  }
  function l(u, f, d) {
    const h = n.find((p) => p.config === u);
    if (h) {
      h.payload = { newVals: f, oldVals: d };
      return;
    }
    n.push({
      config: u,
      token: t++,
      payload: { newVals: f, oldVals: d }
    }), c();
  }
  return {
    pushTask: l,
    flushTasks: i
  };
}
function rs(e) {
  const t = e.map(Pr), n = /* @__PURE__ */ new Map();
  for (const s of t)
    n.set(s, /* @__PURE__ */ new Set());
  for (const s of t)
    if (!(s.type !== "c" || !s.outputs))
      for (const o of t)
        Array.from(Or(o.inputs, o.slient)).some(
          ([i, c]) => c !== 1 && s.outputs.includes(i)
        ) && n.get(o).add(s);
  const { pushTask: r } = $r(n);
  for (const s of t) {
    const {
      immediate: o = !0,
      deep: a = !0,
      once: i,
      flush: c,
      inputs: l = [],
      slient: u = []
    } = s;
    let f = u;
    l.length > 0 && u.length === 0 && (f = Array.from({ length: l.length }).fill(0));
    const d = l.filter(
      (h, p) => f[p] === 0 && P(h)
    );
    $(
      d,
      async (h, p) => {
        h.some(H) || r(s, h, p);
      },
      { immediate: o, deep: a, once: i, flush: c }
    );
  }
}
async function Tr(e) {
  const {
    outputs: t,
    opTypes: n,
    preSetup: r
  } = e.config, s = mt({
    config: r
  });
  try {
    s.run();
    const o = await lt().watchSend(e);
    if (!o)
      return;
    de(o, t, n);
  } finally {
    s.tryReset();
  }
}
function Pr(e) {
  const {
    inputs: t = [],
    outputs: n = [],
    opTypes: r,
    slient: s = [],
    data: o = [],
    fType: a = "sync"
  } = e;
  let i = s, c = o, l = r;
  return t.length > 0 && (s.length === 0 && (i = Array.from({ length: t.length }).fill(0)), o.length === 0 && (c = Array.from({ length: t.length }).fill(1)), r || (l = Array.from({ length: t.length }).fill(
    0
  ))), {
    ...e,
    inputs: t,
    outputs: n,
    opTypes: l,
    fType: a,
    data: c,
    slient: i
  };
}
const B = {
  Ref: 0,
  EventContext: 1,
  Data: 2,
  JsFn: 3,
  ElementRef: 4,
  EventContextDataset: 5
}, ze = {
  const: "c",
  ref: "r",
  range: "n"
};
function ss(e, t) {
  const { fkey: n, tsGroup: r = {} } = e, s = [];
  for (const [a, i, c] of Nr(e))
    s.push(
      ...t({
        i: a,
        v: i,
        k: c
      }).map((l) => {
        const u = Fr(n, { value: i, index: a });
        return D(l, { key: u });
      })
    );
  const o = N(Z, null, s);
  return r && Object.keys(r).length > 0 ? E(Nt, r, {
    default: () => o
  }) : o;
}
function Nr(e) {
  const { type: t, value: n } = e.array, r = t === ze.range, s = t === ze.const || r && typeof n == "number";
  if (r) {
    const { start: o = 0, end: a, step: i = 1 } = n, c = y(o), l = y(a), u = y(i);
    return Ue(c, l, u);
  }
  {
    const o = s ? n : y(n);
    if (typeof o == "number")
      return Ue(0, o, 1);
    if (Array.isArray(o)) {
      function* a() {
        for (let i = 0; i < o.length; i++)
          yield [i, o[i], i];
      }
      return a();
    }
    if (typeof o == "object" && o !== null) {
      function* a() {
        let i = 0;
        for (const [c, l] of Object.entries(o))
          yield [i++, l, c];
      }
      return a();
    }
    if (H(o))
      return o;
  }
  throw new Error("Not implemented yet");
}
function* Ue(e, t, n = 1) {
  if (n === 0)
    throw new Error("Step cannot be 0");
  let r = 0;
  if (n > 0)
    for (let s = e; s < t; s += n)
      yield [r++, s, r];
  else
    for (let s = e; s > t; s += n)
      yield [r++, s, r];
}
const jr = (e) => e, Rr = (e, t) => t;
function Fr(e, t) {
  const { value: n, index: r } = t, s = Dr(e ?? "index");
  return typeof s == "function" ? s(n, r) : e === "item" ? jr(n) : Rr(n, r);
}
function Dr(e) {
  const t = e.trim();
  if (t === "item" || t === "index")
    return;
  if (e.startsWith(":")) {
    e = e.slice(1);
    try {
      return T(e);
    } catch (r) {
      throw new Error(r + " in function code: " + e);
    }
  }
  const n = `(item, index) => { return ${t}; }`;
  try {
    return T(n);
  } catch (r) {
    throw new Error(r + " in function code: " + n);
  }
}
function os(e) {
  const { deepCompare: t = !1, value: n } = e;
  return t ? Oe(n) : k(n);
}
function as(e, t = []) {
  const n = e === null || typeof e != "object" && typeof e != "function" && !P(e);
  return re((r, s) => {
    function o() {
      let a = e, i, c, l = !0;
      n && (l = !1), P(a) && (a = a.value);
      for (const u of t) {
        if (a == null)
          return { value: void 0, writable: !1 };
        const f = y(u);
        if (typeof f == "string" || typeof f == "number")
          i = a, c = f, a = a[f], P(a) && (a = a.value);
        else if (Mr(f))
          a = Lr(f.op, a), l = !1;
        else {
          const d = y(f.v);
          a = Ir(f.op, a, d), l = !1;
        }
      }
      return { value: a, parent: i, key: c, writable: l };
    }
    return {
      get() {
        return r(), o().value;
      },
      set(a) {
        const i = o();
        if (!i.writable || !i.parent)
          throw new Error("This trackPath result is readonly");
        const c = i.parent, l = i.key;
        P(c[l]) ? c[l].value = a : c[l] = a, s();
      }
    };
  });
}
function Ir(e, t, n) {
  switch (e) {
    case ">":
      return t > n;
    case ">=":
      return t >= n;
    case "<":
      return t < n;
    case "<=":
      return t <= n;
    case "==":
      return t == n;
    case "!=":
      return t != n;
    case "+":
      return t + n;
    case "~+":
      return n + t;
    case "-":
      return t - n;
    case "~-":
      return n - t;
    case "*":
      return t * n;
    case "~*":
      return n * t;
    case "/":
      return t / n;
    case "~/":
      return n / t;
    case "&&":
      return t && n;
    case "||":
      return t || n;
    default:
      throw new Error(`Unsupported operator: ${e}`);
  }
}
function Lr(e, t) {
  switch (e) {
    case "!":
      return !t;
    case "~":
      return ~t;
    default:
      throw new Error(`Unsupported unary operator: ${e}`);
  }
}
function Mr(e) {
  return !("v" in e);
}
function vt(e) {
  return e.constructor.name === "AsyncFunction";
}
function Br(e, t) {
  const n = /* @__PURE__ */ new Map();
  return (...r) => {
    const s = t(...r);
    if (n.has(s))
      return n.get(s);
    const o = e(...r);
    return n.set(s, o), o;
  };
}
function zr(e) {
  if (!e) return null;
  switch (e) {
    case "unwrap_reactive":
      return Ur;
    default:
      throw new Error(`Invalid js computed tool ${e}`);
  }
}
function Ur(e, t, ...n) {
  const r = Ae(e);
  return t.forEach((s, o) => {
    const a = n[o];
    let i = r;
    for (let l = 0; l < s.length - 1; l++) {
      const u = s[l];
      i = i[u];
    }
    const c = s[s.length - 1];
    i[c] = a;
  }), r;
}
function is(e) {
  const {
    inputs: t = [],
    code: n,
    asyncInit: r = null,
    deepEqOnInput: s = 0,
    tool: o
  } = e, a = t.filter((f) => P(f));
  function i() {
    return t.map((f) => {
      const d = typeof f == "function", h = d ? f : y(f);
      return pt(h) || d ? h : Ae(h);
    });
  }
  const c = zr(o) ?? T(n), l = s === 0 ? ie(W) : Oe(W), u = { immediate: !0, deep: !0 };
  return vt(c) ? (l.value = r, $(
    a,
    async () => {
      const f = i();
      if (!f.some(H))
        try {
          l.value = await c(...f);
        } catch (d) {
          throw console.error(d, "in computed code: ", n), new Error(d + " in computed code: " + n);
        }
    },
    u
  )) : $(
    a,
    () => {
      const f = i();
      if (!f.some(H))
        try {
          l.value = c(...f);
        } catch (d) {
          throw console.error(d, "in computed code: ", n), new Error(d + " in computed code: " + n);
        }
    },
    u
  ), Se(l);
}
function cs(e) {
  const t = (e.args || []).map(y), n = Object.fromEntries(
    Object.entries(e.kws || {}).map(([r, s]) => [r, y(s)])
  );
  return Wr(y(e.code), ...t, n);
}
function Wr(e, ...t) {
  let n = {};
  if (t.length > 0) {
    const r = t[t.length - 1];
    typeof r == "object" && !Array.isArray(r) && (n = r, t = t.slice(0, -1));
  }
  return e = e.replace(/\{\}/g, () => {
    const r = t.shift();
    return r !== void 0 ? me(r) : "";
  }), e = e.replace(/\{(\d+)\}/g, (r, s) => {
    const o = Number(s);
    return t[o] !== void 0 ? me(t[o]) : "";
  }), e = e.replace(/\{([^{}\d][^{}]*)\}/g, (r, s) => Object.prototype.hasOwnProperty.call(n, s) ? me(n[s]) : r), e;
}
function me(e) {
  if (e === null) return "null";
  if (typeof e == "object")
    try {
      return JSON.stringify(e);
    } catch {
      return String(e);
    }
  return String(e);
}
function wt(e, t, n, r) {
  return [...e.map((o, a) => {
    const i = t[a], c = i === B.EventContextDataset;
    if (i === B.EventContext || c) {
      const l = o(...r);
      return l == null ? l : c ? JSON.parse(l) : l;
    }
    if (i === B.Ref)
      return y(o);
    if (i === B.Data)
      return o;
    if (i === B.ElementRef)
      return y(o);
    if (i === B.JsFn)
      return o;
    throw new Error(`unknown input type ${i}`);
  }), ...n.map(y)];
}
function $e(e, t) {
  return async (...n) => await e(t, ...n);
}
function ls(e) {
  const { inputs: t = [], iptTypes: n = [] } = e;
  async function r(o, ...a) {
    const i = wt(t, n, o, a), c = mt({
      config: e.preSetup
    });
    try {
      c.run();
      const l = await lt().eventSend(
        e,
        i
      );
      if (!l)
        return;
      de(
        l,
        e.outputs,
        e.opTypes
      );
    } finally {
      c.tryReset();
    }
  }
  function s(o) {
    return {
      handleEvent: $e(r, (o == null ? void 0 : o.params) || []),
      ...o
    };
  }
  return {
    fn: s
  };
}
function us(e) {
  const {
    outputs: t = [],
    code: n,
    inputs: r = [],
    iptTypes: s = [],
    opTypes: o = []
  } = e, a = T(n);
  async function i(l, ...u) {
    const f = wt(r, s, l, u), d = await a(...f);
    if (t.length > 0) {
      const p = t.length === 1 ? [d] : d, m = p.map((v) => v === void 0 ? 1 : 0);
      de(
        { values: p, types: m },
        t,
        o
      );
    }
  }
  function c(l) {
    return {
      handleEvent: $e(i, (l == null ? void 0 : l.params) || []),
      ...l
    };
  }
  return {
    fn: c
  };
}
function fs(e) {
  const { code: t, bind: n = {} } = e, r = T(t, n);
  async function s(a, ...i) {
    await r(...a, ...i);
  }
  function o(a) {
    return {
      handleEvent: $e(s, (a == null ? void 0 : a.params) || []),
      ...a
    };
  }
  return {
    fn: o
  };
}
function ds(e, t) {
  if (y(e.on))
    return N(Z, null, t());
}
function hs(e, t) {
  const { cs: n, df: r } = t;
  if (!n && !r)
    return null;
  const s = y(e);
  return n && n[s] ? N(Z, null, n[s]()) : r ? N(Z, null, r()) : null;
}
function ps(e) {
  e.forEach(Hr);
}
function Hr(e) {
  const {
    inputs: t = [],
    outputs: n,
    opTypes: r,
    slient: s,
    code: o,
    immediate: a = !0,
    deep: i = !0,
    once: c,
    flush: l
  } = e, u = s || Array.from({ length: t.length }).fill(0), f = T(o), d = t.filter(
    (p, m) => u[m] === 0 && P(p)
  );
  function h() {
    return t.map((p) => {
      const m = typeof p == "function", v = m ? p : y(p);
      return pt(v) || m ? v : Ae(v);
    });
  }
  $(
    d,
    async () => {
      let p = await f(...h());
      if (!n)
        return;
      const v = n.length === 1 ? [p] : p, C = v.map((V) => V === void 0 ? 1 : 0);
      de(
        {
          values: v,
          types: C
        },
        n,
        r
      );
    },
    { immediate: a, deep: i, once: c, flush: l }
  );
}
function ms(e) {
  e.forEach(Jr);
}
function Jr(e) {
  const {
    on: t,
    code: n,
    immediate: r = !1,
    deep: s = !1,
    once: o,
    flush: a,
    bind: i = {}
  } = e, c = T(n, i), l = t.length === 1 ? t[0] : t.map(
    (u) => () => typeof u == "function" ? u : y(u)
  );
  return $(l, c, { immediate: r, deep: s, once: o, flush: a });
}
function ys(e) {
  return jt(y(e));
}
function gs(e) {
  const { type: t, key: n, value: r } = e;
  return t === "local" ? ve(n, r) : ve(n, r, sessionStorage);
}
const Kr = "insta-color-scheme";
function vs() {
  return sn({
    storageKey: Kr,
    onChanged(t) {
      t ? (document.documentElement.setAttribute("theme-mode", "dark"), document.documentElement.classList.add("insta-dark")) : (document.documentElement.setAttribute("theme-mode", "light"), document.documentElement.classList.remove("insta-dark"));
    }
  });
}
const Gr = k("en_US");
function ws() {
  return Gr;
}
function bs(e) {
  return on(e);
}
function _s(e) {
  const { bind: t = {}, code: n } = e;
  if (vt(new Function(n)))
    return Jt(
      async () => await T(n, t)(),
      null,
      { lazy: !0 }
    );
  const r = T(n, t);
  return A(r);
}
function Ss(e, t) {
  const n = new URLSearchParams(window.location.search);
  return A(() => n.get(y(e)) ?? y(t));
}
function Es(e) {
  const t = ht();
  for (const n in e)
    t[n] = e[n];
}
function qr() {
  const e = Sr();
  return new Proxy(
    {},
    {
      get(t, n) {
        return e[n];
      }
    }
  );
}
function ks() {
  function e(t) {
    return qr()[t];
  }
  return {
    getRef: e
  };
}
function Vs(e) {
  const t = y(e);
  if (t !== W)
    return t;
  const n = k();
  return $(
    e,
    (r) => {
      n.value = r;
    },
    { immediate: !1, once: !0 }
  ), n;
}
const Qr = Br(
  Yr,
  (e, t, n) => `${e}|${t}|${n}`
);
function Cs(e, t) {
  const n = z().route.path;
  return A(
    () => Qr(n, y(e)) ?? y(t)
  );
}
function Yr(e, t, n = window.location.pathname) {
  const r = e.split("/").filter(Boolean), s = n.split("/").filter(Boolean);
  if (r.length === s.length)
    for (let o = 0; o < r.length; o++) {
      const a = r[o], i = s[o];
      if (a.startsWith(":")) {
        if (a.slice(1) === t)
          return decodeURIComponent(i);
      } else if (a !== i)
        return;
    }
}
function xs(e, t, n) {
  const s = (n ?? Rt)({
    setup() {
      return () => E(je, { meta: t }, () => E(e));
    }
  });
  return s.component("insta-ui", je), s.component("teleport", En), s.component("icon", Cn), s.component("heading", _n), s.component("box", Nn), s.component("flex", Dn), s.component("grid", Bn), s.component("container", Jn), s.component("ui-text", qn), s.component("ui-link", Yn), s.component("lazy-render", tr), s.component("ui-img", nr), s.component("ui-video", sr), s;
}
export {
  ys as content,
  oe as convertDynamicProperties,
  _s as createExprComputed,
  fs as createExprEvent,
  is as createJsComputed,
  us as createJsEvent,
  os as createRef,
  ns as createWebComputedRef,
  ls as createWebEvent,
  ms as exprWatch,
  ss as genVFor,
  hn as generateSvgSpriteEmbedInHtml,
  z as getAppInfo,
  qr as inject,
  xs as install,
  ps as jsWatch,
  hs as match,
  Es as provide,
  es as renderComponent,
  ts as renderScope,
  gs as storageRef,
  cs as strFormat,
  Vs as toValue,
  as as trackPath,
  ks as useBindingGetter,
  vs as useDark,
  vs as useDarkRef,
  ws as useLanguage,
  ws as useLanguageRef,
  bs as usePageTitle,
  bs as usePageTitleRef,
  Ss as useQueryParam,
  Cs as useRouteParam,
  ds as vif,
  rs as webWatchTaskScheduler
};
