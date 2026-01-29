import { defineComponent as s, inject as c, ref as i, createElementBlock as p, openBlock as g, createElementVNode as l, normalizeClass as _ } from "vue";
const m = { class: "globe-toggle" }, u = ["title"], v = /* @__PURE__ */ s({
  __name: "GlobeToggle",
  setup(o) {
    const e = c("tangramApi");
    if (!e)
      throw new Error("assert: tangram api not provided");
    const t = i(!1), r = () => {
      if (!e.map.isReady.value) return;
      const n = e.map.getMapInstance(), a = !t.value;
      n.setProjection(a ? { type: "globe" } : { type: "mercator" }), t.value = a;
    };
    return (n, a) => (g(), p("div", m, [
      l("button", {
        class: _({ active: t.value }),
        title: t.value ? "Switch to mercator view" : "Switch to globe view",
        onClick: r
      }, [...a[0] || (a[0] = [
        l("span", { class: "fa fa-globe" }, null, -1)
      ])], 10, u)
    ]));
  }
}), b = (o, e) => {
  const t = o.__vccOpts || o;
  for (const [r, n] of e)
    t[r] = n;
  return t;
}, d = /* @__PURE__ */ b(v, [["__scopeId", "data-v-871c94ae"]]);
function w(o, e) {
  o.ui.registerWidget("globe-toggle", "TopBar", d, {
    priority: e?.topbar_order
  });
}
export {
  w as install
};
//# sourceMappingURL=index.js.map
