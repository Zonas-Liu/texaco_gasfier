/* TEXACO 工作台：所有指标来自计算输出，缺失值以破折号显示。 */
const OUTPUT_LABELS = {
  Iter: "迭代",
  KONVER: "收敛标志",
  SUMFE: "气体组分",
  SUMWE: "固体质量流",
  SUMX: "固体碳分数",
  SUMT: "温度",
  I: "格子号",
  "H(m)": "高度 (m)",
  "U0(m/s)": "气速 (m/s)",
  "ResidenceTime(s)": "停留时间 (s)",
  "WE(kg/s)": "碳质量流 (kg/s)",
  "T(C)": "温度 (°C)",
  "X(%)": "碳转化率 (%)",
};
const GAS_LABELS = {
  O2: "O₂",
  CH4: "CH₄",
  CO: "CO",
  CO2: "CO₂",
  H2S: "H₂S",
  H2: "H₂",
  N2: "N₂",
  H2O: "H₂O",
};
const COLORS = [
  "#147d73",
  "#e68136",
  "#628cbd",
  "#9676a8",
  "#95a7b4",
  "#b89260",
  "#769b65",
  "#809daa",
];
const GAS_COLORS = {
  CO: "#147d73",
  H2: "#429e92",
  CO2: "#83bdb5",
  CH4: "#e68136",
  H2S: "#9676a8",
  N2: "#95a7b4",
  O2: "#628cbd",
  H2O: "#809daa",
};
const $ = (id) => document.getElementById(id);
const state = {
  info: {},
  result: null,
  active: "tab-overview",
  rendered: new Set(),
  polling: false,
  loaded: false,
  dirty: false,
  raw: "",
};
const finite = (v) => typeof v === "number" && Number.isFinite(v);
const fmt = (v, digits = 2) =>
  finite(v)
    ? v.toLocaleString("en-US", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      })
    : "—";
const escapeHtml = (v) =>
  String(v ?? "—").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
async function api(path, body) {
  const r = await fetch(
    path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const data = await r.json();
  if (!r.ok)
    throw Object.assign(new Error(data.error || `请求失败 (${r.status})`), {
      status: r.status,
    });
  return data;
}
function message(text, type = "info") {
  $("sidebar-msg").className = `msg ${type}`;
  $("sidebar-msg").textContent = text;
}
function status(text, type = "") {
  $("run-status").textContent = text;
  $("run-status").className = `status ${type}`;
}
function setBusy(busy) {
  state.polling = busy;
  $("btn-save").disabled = busy || !state.loaded;
  $("btn-run").disabled = busy || !state.loaded;
  $("btn-run").textContent = busy ? "计算进行中" : "运行模拟";
  document
    .querySelectorAll("#params-form input, #params-form select")
    .forEach((el) => (el.disabled = busy));
  syncDesignControls();
}
function syncDesignControls() {
  const mode = $("param-RSC_MODE"),
    model = $("param-KMODEL");
  if (!mode || !model) return;
  const enabled = model.value === "1",
    target = enabled && mode.value === "1";
  for (const [name, info] of Object.entries(state.info)) {
    if (info.group === "辐射废锅设计" && name !== "KMODEL") {
      const targetOnly = ["T_RSC_OUT_C", "H_RSC_MIN", "H_RSC_MAX"].includes(
        name,
      );
      $(`param-${name}`).disabled =
        state.polling || !enabled || (targetOnly && !target);
    }
  }
  document.querySelector('label[for="param-H_RSC"]').textContent = target
    ? "高度搜索初值"
    : "废锅有效高度";
}
function caption() {
  $("result-caption").textContent =
    state.polling && state.result
      ? "当前正在计算 · 下方保留上次结果"
      : state.dirty && state.result
        ? "参数已修改 · 下方为上次计算结果"
        : "最近一次计算的输出";
}
function syncDrawer() {
  const mobile = window.innerWidth <= 760,
    open = mobile && $("parameter-panel").classList.contains("open");
  $("parameter-panel").toggleAttribute("inert", mobile && !open);
  $("main-content").toggleAttribute("inert", open);
  $("sidebar-backdrop").hidden = !open;
  document.body.classList.toggle("drawer-open", open);
  $("btn-params").setAttribute("aria-expanded", String(open));
  if (!mobile) {
    $("parameter-panel").classList.remove("open");
  }
}
function drawer(open) {
  $("parameter-panel").classList.toggle("open", open);
  $("sidebar-backdrop").hidden = !open;
  document.body.classList.toggle("drawer-open", open);
  $("btn-params").setAttribute("aria-expanded", String(open));
  syncDrawer();
  if (open) $("param-search").focus();
  else if (window.innerWidth <= 760) $("btn-params").focus();
}

document.addEventListener("DOMContentLoaded", async () => {
  syncDrawer();
  window.addEventListener("resize", syncDrawer);
  $("btn-save").addEventListener("click", saveParams);
  $("btn-run").addEventListener("click", runSimulation);
  $("params-form").addEventListener("submit", (e) => e.preventDefault());
  $("params-form").addEventListener("input", (e) => {
    if (e.target.id === "param-KMODEL" && e.target.value === "0")
      $("param-RSC_MODE").value = "0";
    syncDesignControls();
    state.dirty = true;
    caption();
    message("参数已修改，运行时将自动保存。");
  });
  $("param-search").addEventListener("input", filterParams);
  $("btn-params").addEventListener("click", () =>
    drawer(!$("parameter-panel").classList.contains("open")),
  );
  $("sidebar-backdrop").addEventListener("click", () => drawer(false));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") drawer(false);
    if (e.key === "Tab" && document.body.classList.contains("drawer-open")) {
      const nodes = [
        ...$("parameter-panel").querySelectorAll(
          "button:not(:disabled),input:not(:disabled),select:not(:disabled),summary",
        ),
      ].filter((n) => n.getClientRects().length);
      if (e.shiftKey && document.activeElement === nodes[0]) {
        e.preventDefault();
        nodes.at(-1).focus();
      } else if (!e.shiftKey && document.activeElement === nodes.at(-1)) {
        e.preventDefault();
        nodes[0].focus();
      }
    }
  });
  document.querySelectorAll(".tab-btn").forEach((btn, index) => {
    btn.addEventListener("click", () => activateTab(btn.dataset.tab));
    btn.addEventListener("keydown", (e) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
      e.preventDefault();
      const tabs = [...document.querySelectorAll(".tab-btn")];
      let next =
        e.key === "Home"
          ? 0
          : e.key === "End"
            ? tabs.length - 1
            : (index + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) %
              tabs.length;
      tabs[next].focus();
      activateTab(tabs[next].dataset.tab);
    });
  });
  $("btn-raw").addEventListener("click", () => activateTab("tab-raw"));
  $("btn-back").addEventListener("click", () => activateTab("tab-overview"));
  $("btn-retry").addEventListener("click", loadResults);
  await Promise.allSettled([loadParams(), loadResults()]);
  try {
    const progress = await api("/api/progress");
    if (progress.running) {
      setBusy(true);
      caption();
      status("正在计算", "running");
      $("progress-card").hidden = false;
      pollProgress();
    }
  } catch (e) {
    message(`无法查询运行状态：${e.message}`, "error");
  }
});

async function loadParams() {
  try {
    const data = await api("/api/params");
    state.info = data.info;
    renderParams(data);
    state.loaded = true;
    setBusy(false);
  } catch (e) {
    message(`参数读取失败：${e.message}，请刷新重试。`, "error");
  }
}
function renderParams(data) {
  $("params-form").replaceChildren();
  const order = [
    "进料参数",
    "辐射废锅设计",
    "状态与几何",
    "煤质与操作",
    "控制与收敛",
  ];
  for (const group of order.filter((g) => data.grouped[g])) {
    const details = document.createElement("details");
    details.className = "param-group";
    details.open = group === "进料参数";
    const summary = document.createElement("summary");
    summary.innerHTML =
      '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5"/></svg>' +
      escapeHtml(group);
    details.append(summary);
    const fields = document.createElement("div");
    fields.className = "group-fields";
    if (group === "辐射废锅设计") {
      const hint = document.createElement("p");
      hint.className = "parameter-hint";
      hint.textContent = "目标温度模式联动计算有效高度、回收热负荷和产汽量。";
      fields.append(hint);
    }
    for (const name of data.grouped[group]) {
      const info = data.info[name];
      const row = document.createElement("div");
      row.className = "form-group";
      row.dataset.search = `${name} ${info.cn} ${info.desc}`.toLowerCase();
      row.innerHTML = `<div class="field-label"><label for="param-${name}" title="${escapeHtml(info.desc)}">${escapeHtml(info.cn)}</label><small>${name}</small></div><div class="input-shell"><input id="param-${name}" name="${name}" type="number" step="${info.type === "int" ? "1" : "any"}" required aria-describedby="unit-${name}"><span class="field-unit" id="unit-${name}">${escapeHtml(info.unit || "无量纲")}</span></div>`;
      if (info.options) {
        row.classList.add("select-field");
        const select = document.createElement("select");
        select.id = `param-${name}`;
        select.name = name;
        for (const [value, label] of Object.entries(info.options))
          select.add(new Option(label, value));
        row.querySelector("input").replaceWith(select);
      }
      row.querySelector("input,select").value = data.values[name];
      fields.append(row);
    }
    details.append(fields);
    $("params-form").append(details);
  }
}
function filterParams() {
  const q = $("param-search").value.trim().toLowerCase();
  let count = 0;
  document.querySelectorAll(".param-group").forEach((group) => {
    let matches = 0;
    group.querySelectorAll(".form-group").forEach((row) => {
      row.hidden = q && !row.dataset.search.includes(q);
      if (!row.hidden) matches++;
    });
    group.hidden = matches === 0;
    if (q) group.open = matches > 0;
    count += matches;
  });
  $("search-empty").hidden = count !== 0;
}
function collectParams() {
  const data = {};
  for (const name of Object.keys(state.info)) {
    const input = $(`param-${name}`);
    if (!input.checkValidity()) {
      const group = input.closest("details");
      group.open = true;
      group.hidden = false;
      input.closest(".form-group").hidden = false;
      if (window.innerWidth <= 760) drawer(true);
      input.reportValidity();
      throw new Error(`${state.info[name].cn}：请输入有效数值`);
    }
    data[name] = Number(input.value);
  }
  return data;
}
async function saveParams() {
  if (state.polling) return;
  $("btn-save").disabled = true;
  try {
    await api("/api/params", collectParams());
    message("参数已保存，运行模拟以更新结果。", "success");
  } catch (e) {
    message(e.message, "error");
  } finally {
    $("btn-save").disabled = state.polling || !state.loaded;
  }
}
async function runSimulation() {
  if (state.polling) return;
  let params;
  try {
    params = collectParams();
  } catch (e) {
    message(e.message, "error");
    return;
  }
  setBusy(true);
  caption();
  drawer(false);
  $("progress-card").hidden = false;
  $("console-area").hidden = true;
  $("progress-card").classList.remove("error");
  updateProgress({
    iteration: 0,
    max_iterations: params.ITMAX,
    message: "正在初始化计算",
  });
  status("正在计算", "running");
  try {
    await api("/api/run", params);
    message("模拟已启动。");
    pollProgress();
  } catch (e) {
    setBusy(false);
    caption();
    status("启动失败", "error");
    $("progress-title").textContent = "启动失败";
    $("progress-text").textContent = e.message;
    $("progress-card").classList.add("error");
    message(e.message, "error");
  }
}
async function pollProgress() {
  if (!state.polling) return;
  try {
    const data = await api("/api/progress");
    updateProgress(data);
    if (data.running) {
      setTimeout(pollProgress, 700);
      return;
    }
    setBusy(false);
    caption();
    if (data.stdout || data.stderr) {
      $("console-area").hidden = false;
      $("console-output").textContent = [data.stdout, data.stderr]
        .filter(Boolean)
        .join("\n");
    }
    if (data.returncode === 0) {
      state.dirty = false;
      $("progress-card").hidden = true;
      message("计算已收敛，结果已更新。", "success");
      await loadResults();
    } else {
      const text =
        data.returncode === 2
          ? data.message || "达到迭代上限，未收敛"
          : "计算失败";
      status(text, "error");
      $("progress-title").textContent = text;
      $("progress-card").classList.add("error");
      message(text + "，请检查参数与运行日志。", "error");
      if (data.returncode === 2) {
        await loadResults();
        $("result-caption").textContent =
          "本次计算未通过全部收敛条件 · 结果仅供诊断";
      }
    }
  } catch (e) {
    $("progress-title").textContent = "连接暂时中断";
    $("progress-text").textContent = "仍在查询计算状态，请勿重复启动。";
    message(e.message, "error");
    setTimeout(pollProgress, 2000);
  }
}
function updateProgress(data) {
  const percent = Math.max(
    0,
    Math.min(100, (Number(data.progress) || 0) * 100),
  );
  $("progress-title").textContent = "计算进行中";
  $("progress-count").textContent =
    `${data.iteration || 0} / ${data.max_iterations || 0} 次迭代`;
  $("progress-fill").style.width = percent + "%";
  document
    .querySelector(".progress-track")
    .setAttribute("aria-valuenow", String(Math.round(percent)));
  $("progress-text").textContent = data.message || "正在计算";
  $("residual-values").textContent = Object.entries(data.residuals || {})
    .map(([k, v]) => `${k} ${finite(v) ? v.toExponential(2) : "—"}`)
    .join("   ·   ");
}

async function loadResults() {
  try {
    const result = await api("/api/results");
    if (!result.internal_profile?.length)
      throw Object.assign(new Error("还没有完整的计算结果"), { status: 404 });
    state.result = result;
    state.rendered.clear();
    $("empty-state").hidden = true;
    $("results-area").hidden = false;
    $("btn-raw").disabled = false;
    showSummary(result);
    activateTab(state.active);
    caption();
    try {
      state.raw = (await api("/api/output")).text;
      $("raw-output").textContent = state.raw;
    } catch (e) {
      $("raw-output").textContent = `读取失败：${e.message}`;
    }
  } catch (e) {
    if (state.result) {
      message(`结果刷新失败：${e.message}`, "error");
      return;
    }
    $("empty-state").hidden = false;
    $("btn-retry").hidden = e.status === 404;
    $("empty-title").textContent =
      e.status === 404 ? "准备第一个工况" : "结果读取失败";
    if (e.status !== 404) $("empty-message").textContent = e.message;
    status(
      e.status === 404 ? "等待计算" : "连接异常",
      e.status === 404 ? "" : "error",
    );
  }
}
function metric(label, value, unit = "") {
  return `<div class="metric"><div class="metric-label">${escapeHtml(label)}</div><div class="metric-value">${escapeHtml(value)}<small>${escapeHtml(unit)}</small></div></div>`;
}
function showSummary(r) {
  const hist = r.convergence_history || [],
    last = hist.at(-1),
    heat = r.heat_recovery || {};
  const isRsc = Object.keys(heat).length > 0;
  $("model-name").textContent = isRsc ? "晋华炉 3.0" : "TEXACO";
  const flows = Object.values(r.volume_flow || {});
  const total = flows.length ? flows.reduce((a, b) => a + b, 0) : null;
  $("summary-grid").innerHTML =
    metric(
      isRsc ? "废锅出口温度" : "气化炉出口温度",
      fmt(r.outlet?.["Temperature(C)"]),
      "°C",
    ) +
    metric(
      "碳转化率",
      finite(r.outlet?.CarbonConversion)
        ? fmt(r.outlet.CarbonConversion * 100)
        : "—",
      "%",
    ) +
    metric("干基煤气流量", fmt(total), "Nm³/s") +
    (isRsc
      ? metric("总产汽量", fmt(heat.steam_total_tph), "t/h")
      : metric("迭代次数", last ? last.Iter : "—", "次"));
  status(
    last
      ? `${last.KONVER === 0 ? "已收敛" : "未收敛"} · ${last.Iter} 次迭代`
      : "收敛状态未知",
    last?.KONVER === 0 ? "success" : "error",
  );
  if (r.rsc_design)
    status(
      r.rsc_design.success
        ? `目标已达到 · ${r.rsc_design.evaluations} 轮设计计算`
        : "目标温度未达到",
      r.rsc_design.success ? "success" : "error",
    );
  $("heat-panel").hidden = !isRsc;
  $("zone-legend").hidden = !isRsc;
  renderDesign(r.rsc_design);
  $("heat-metrics").innerHTML = isRsc
    ? metric("水冷壁", fmt(heat.steam_wall_tph), "t/h") +
      metric("辐射废锅", fmt(heat.steam_rsc_tph), "t/h") +
      metric("汽包压力", fmt(heat.drum_pressure_mpa), "MPa")
    : "";
}
function activateTab(id) {
  state.active = id;
  document
    .querySelectorAll(".tab-panel")
    .forEach((p) => (p.hidden = p.id !== id));
  document.querySelectorAll(".tab-btn").forEach((b) => {
    const active = b.dataset.tab === id;
    b.classList.toggle("active", active);
    b.setAttribute("aria-selected", String(active));
    b.tabIndex = active ? 0 : -1;
  });
  $("btn-raw").setAttribute("aria-pressed", String(id === "tab-raw"));
  if (state.result && !state.rendered.has(id)) {
    renderTab(id);
    state.rendered.add(id);
  }
  requestAnimationFrame(() =>
    document
      .querySelectorAll(`#${id} .js-plotly-plot`)
      .forEach((p) => Plotly.Plots.resize(p)),
  );
}

const PLOT_CONFIG = {
  responsive: true,
  displaylogo: false,
  displayModeBar: false,
  scrollZoom: false,
};
function layout(yTitle, xTitle = "格子号") {
  return {
    font: {
      family: "Segoe UI, Microsoft YaHei, sans-serif",
      size: 12,
      color: "#647383",
    },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    margin: { l: 62, r: 28, t: 46, b: 54 },
    xaxis: {
      title: { text: xTitle, font: { size: 12 } },
      showgrid: false,
      showline: true,
      linecolor: "#dce5eb",
      ticks: "outside",
      tickcolor: "#dce5eb",
      ticklen: 4,
      nticks: 7,
      zeroline: false,
      automargin: true,
    },
    yaxis: {
      title: { text: yTitle, font: { size: 12 } },
      gridcolor: "#edf1f4",
      nticks: 5,
      zeroline: false,
      automargin: true,
    },
    legend: {
      orientation: "h",
      x: 0,
      y: 1.2,
      font: { size: 12 },
      traceorder: "normal",
    },
    hovermode: "x unified",
    hoverlabel: { bgcolor: "#172c3e", font: { color: "#fff", size: 12 } },
    showlegend: false,
  };
}
function plotLine(id, rows, keys, yTitle, options = {}) {
  if (!rows.length) return;
  const traces = keys.map((key, i) => ({
    x: rows.map((r) => r[options.x || "I"]),
    y: rows.map((r) => r[key]),
    name: GAS_LABELS[key] || OUTPUT_LABELS[key] || key,
    mode: "lines",
    connectgaps: false,
    line: {
      width: 3,
      shape: "linear",
      color: options.color || GAS_COLORS[key] || COLORS[i],
      dash: options.log && i > 0 ? ["solid", "dot", "dash"][i] : "solid",
    },
    hovertemplate: "%{y:.4g}<extra>%{fullData.name}</extra>",
  }));
  const spec = layout(yTitle, options.x === "Iter" ? "迭代次数" : "格子号");
  spec.showlegend = keys.length > 1;
  if (options.log) spec.yaxis.type = "log";
  if (options.zones && rows.length > 30) {
    spec.shapes = [
      {
        type: "rect",
        x0: 30,
        x1: rows.at(-1).I,
        y0: 0,
        y1: 1,
        yref: "paper",
        fillcolor: "rgba(20,125,115,0.045)",
        line: { width: 0 },
        layer: "below",
      },
      {
        type: "line",
        x0: 30,
        x1: 30,
        y0: 0,
        y1: 1,
        yref: "paper",
        line: { color: "#83b7ae", width: 1.2, dash: "dot" },
      },
    ];
    spec.annotations = [
      {
        x: 30,
        y: 1,
        yref: "paper",
        text: "燃烧室 / 辐射废锅",
        showarrow: false,
        xanchor: "right",
        yshift: 15,
        font: { size: 11, color: "#147d73" },
      },
    ];
    const exits = [rows.find((r) => r.I === 30), rows.at(-1)].filter(Boolean);
    traces.push({
      x: exits.map((r) => r.I),
      y: exits.map((r) => r[keys[0]]),
      type: "scatter",
      mode: "markers",
      showlegend: false,
      hoverinfo: "skip",
      marker: {
        size: 8,
        color: options.color || COLORS[0],
        line: { color: "#fff", width: 2 },
      },
    });
    exits.forEach((r, i) =>
      spec.annotations.push({
        x: r.I,
        y: r[keys[0]],
        text: `${i === 0 ? "燃烧室" : "废锅"} ${fmt(r[keys[0]], 1)} °C`,
        showarrow: true,
        arrowhead: 0,
        arrowcolor: "#aebdc5",
        ax: i === 0 ? 0 : -52,
        ay: i === 0 ? -36 : -28,
        bgcolor: "#fff",
        bordercolor: "#dce5eb",
        borderpad: 5,
        font: { size: 11, color: "#172c3e" },
      }),
    );
  }
  Plotly.newPlot(id, traces, spec, PLOT_CONFIG);
}
function plotBar(id, data, unit, horizontal = false, maximum = null) {
  let keys = Object.keys(data);
  if (horizontal)
    keys = ["CO", "H2", "CO2", "CH4", "N2", "H2S", "O2"].filter((k) =>
      finite(data[k]),
    );
  const values = keys.map((k) => data[k]);
  const trace = {
    type: "bar",
    x: horizontal ? values : keys.map((k) => GAS_LABELS[k] || k),
    y: horizontal ? keys.map((k) => GAS_LABELS[k] || k) : values,
    orientation: horizontal ? "h" : "v",
    marker: { color: keys.map((k) => GAS_COLORS[k] || COLORS[0]) },
    text: values.map((v) => fmt(v, 2) + (unit === "%" ? "%" : "")),
    textposition: "outside",
    cliponaxis: false,
    hovertemplate: "%{text}<extra></extra>",
  };
  const spec = layout(
    horizontal ? "" : unit,
    horizontal ? `体积分数 (${unit})` : "组分",
  );
  spec.margin = { l: 48, r: 48, t: 24, b: 48 };
  spec.bargap = 0.4;
  spec.hovermode = "closest";
  if (horizontal) {
    spec.yaxis.autorange = "reversed";
    spec.yaxis.tickmode = "array";
    spec.yaxis.tickvals = keys.map((k) => GAS_LABELS[k] || k);
    spec.xaxis.range = [0, maximum || Math.max(...values, 1) * 1.23];
    spec.yaxis.showgrid = false;
  } else {
    spec.yaxis.range = [0, Math.max(...values, 1) * 1.22];
    spec.xaxis.showgrid = false;
  }
  Plotly.newPlot(id, [trace], spec, PLOT_CONFIG);
}
function renderTable(id, columns, rows, formatters = {}) {
  if (!rows.length) {
    $(id).textContent = "暂无数据";
    return;
  }
  $(id).innerHTML =
    `<table><thead><tr>${columns.map((c) => `<th scope="col">${escapeHtml(OUTPUT_LABELS[c] || GAS_LABELS[c] || c)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr class="${row.I === 30 || row.I === state.result?.internal_profile?.at(-1)?.I ? "section-boundary" : ""}">${columns.map((c) => `<td>${escapeHtml(formatters[c] ? formatters[c](row[c]) : finite(row[c]) ? fmt(row[c], ["I", "Iter", "KONVER", "轮次", "内层迭代"].includes(c) ? 0 : 3) : row[c])}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
function renderOutlets(sections) {
  const host = $("outlet-comparison");
  document.querySelector(".comparison-key").hidden = sections.length < 2;
  if (!sections.length) {
    host.textContent = "没有可用的出口截面数据，请重新运行模拟。";
    return;
  }
  host.innerHTML = sections
    .map(
      (s, i) => `<section class="panel outlet-card ${s.key}">
    <div class="outlet-heading"><div><span class="outlet-position">第 ${s.cell} 格</span><h2>${escapeHtml(s.label)}</h2></div><div class="outlet-temperature">${fmt(s.temperature_c, 1)}<small>°C</small></div></div>
    <div class="outlet-stats"><div><span>干基总流量</span><strong>${fmt(s.total_dry_nms, 3)}<small>Nm³/s</small></strong></div><div><span>H₂ / CO</span><strong>${fmt(s.h2_co_ratio, 3)}</strong></div></div>
    <div class="chart-heading">干基组成 <span>体积分数 / %</span></div><div class="plot outlet-plot" id="plot-outlet-${i}"></div>
    <div class="table-wrap outlet-table" id="table-outlet-${i}"></div>
    <div class="outlet-footer"><span>湿基总流量（含 H₂O）</span><strong>${fmt(s.total_wet_nms, 3)} Nm³/s</strong><small>${fmt(finite(s.total_wet_nms) ? s.total_wet_nms * 3600 : null, 1)} Nm³/h</small></div>
    ${Object.keys(s.volume_flow).length ? "" : '<p class="section-note">此历史输出缺少该出口流量，请重新计算补全。</p>'}
  </section>`,
    )
    .join("");
  const maximum =
    Math.max(
      1,
      ...sections.flatMap((s) =>
        Object.values(s.dry_composition).filter(finite),
      ),
    ) * 1.23;
  sections.forEach((s, i) => {
    plotBar(`plot-outlet-${i}`, s.dry_composition, "%", true, maximum);
    const keys = ["CO", "H2", "CO2", "CH4", "N2", "H2S", "O2", "H2O"];
    renderTable(
      `table-outlet-${i}`,
      ["组分", "干基 (%)", "湿基 (%)", "流量 (Nm³/s)"],
      keys.map((g) => ({
        组分: GAS_LABELS[g],
        "干基 (%)": s.dry_composition[g],
        "湿基 (%)": s.wet_composition[g],
        "流量 (Nm³/s)": s.volume_flow[g],
      })),
    );
  });
}
function renderDesign(design) {
  $("design-result").hidden = !design;
  if (!design) return;
  $("design-result").innerHTML =
    `<div class="design-heading"><h3>目标温度设计</h3><span class="design-state ${design.success ? "" : "failed"}">${design.success ? "已达目标" : "目标未达到"}</span></div>
    <div class="design-metrics">${metric("目标出口温度", fmt(design.target_temperature_c, 1), "°C")}${metric("计算有效高度", fmt(design.height_m, 2), "m")}${metric("废锅回收热负荷", fmt(design.heat_rsc_mw, 3), "MW")}${metric("废锅产汽量", fmt(design.steam_rsc_tph, 3), "t/h")}</div>
    <p class="design-note">实际出口 ${fmt(design.temperature_c, 2)} °C · 温差 ${design.temperature_error_c >= 0 ? "+" : ""}${fmt(design.temperature_error_c, 3)} °C · 允许温差 ±${fmt(design.tolerance_c, 1)} °C · ${design.evaluations} 轮设计计算</p>
    <details class="design-history"><summary>查看高度、温度与产汽联动过程</summary><div class="table-wrap" id="design-table"></div></details>`;
  renderTable(
    "design-table",
    [
      "轮次",
      "有效高度 (m)",
      "出口温度 (°C)",
      "回收热量 (MW)",
      "废锅产汽 (t/h)",
      "内层迭代",
    ],
    design.trials.map((t, i) => ({
      轮次: i + 1,
      "有效高度 (m)": t.height_m,
      "出口温度 (°C)": t.temperature_c,
      "回收热量 (MW)": t.heat_rsc_mw,
      "废锅产汽 (t/h)": t.steam_rsc_tph,
      内层迭代: t.iterations,
    })),
  );
}
function renderTab(id) {
  const r = state.result,
    internal = r.internal_profile || [],
    gas = r.gas_composition_profile || [],
    hist = r.convergence_history || [],
    heat = r.heat_recovery || {};
  if (id === "tab-overview") {
    plotLine("plot-overview-temp", internal, ["T(C)"], "温度 (°C)", {
      color: "#e68136",
      zones: Object.keys(heat).length > 0,
    });
    plotBar("plot-overview-gas", r.syngas_composition || {}, "%", true);
  }
  if (id === "tab-history") {
    plotLine(
      "plot-history-main",
      hist,
      ["SUMFE", "SUMWE", "SUMX"],
      "修正量（对数）",
      { x: "Iter", log: true },
    );
    plotLine("plot-history-t", hist, ["SUMT"], "温度修正量 (K)", {
      x: "Iter",
      log: true,
      color: "#e68136",
    });
    renderTable(
      "history-table",
      ["Iter", "KONVER", "SUMFE", "SUMWE", "SUMX", "SUMT"],
      hist,
      Object.fromEntries(
        ["SUMFE", "SUMWE", "SUMX", "SUMT"].map((k) => [
          k,
          (v) => (finite(v) ? v.toExponential(4) : "—"),
        ]),
      ),
    );
  }
  if (id === "tab-syngas") renderOutlets(r.outlet_sections || []);
  if (id === "tab-profile") {
    plotLine("plot-temp", internal, ["T(C)"], "温度 (°C)", {
      color: "#e68136",
      zones: Object.keys(heat).length > 0,
    });
    plotLine("plot-x", internal, ["X(%)"], "碳转化率 (%)");
    plotLine("plot-we", internal, ["WE(kg/s)"], "质量流量 (kg/s)");
    plotLine("plot-u0", internal, ["U0(m/s)"], "气速 (m/s)");
    renderTable(
      "internal-table",
      ["I", "H(m)", "U0(m/s)", "ResidenceTime(s)", "WE(kg/s)", "T(C)", "X(%)"],
      internal,
    );
    plotLine("plot-gas-main", gas, ["CO", "H2", "CO2", "CH4"], "体积分数 (%)");
    plotLine("plot-gas-other", gas, ["O2", "H2O", "N2", "H2S"], "体积分数 (%)");
    renderTable(
      "gas-table",
      ["I", "O2", "CH4", "CO", "CO2", "H2S", "H2", "N2", "H2O"],
      gas,
    );
  }
}
