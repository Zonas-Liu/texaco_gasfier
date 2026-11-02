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
    .querySelectorAll("#params-form input")
    .forEach((el) => (el.disabled = busy));
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
  $("params-form").addEventListener("input", () => {
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
          "button:not(:disabled),input:not(:disabled),summary",
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
  const order = ["进料参数", "状态与几何", "煤质与操作", "控制与收敛"];
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
    for (const name of data.grouped[group]) {
      const info = data.info[name];
      const row = document.createElement("div");
      row.className = "form-group";
      row.dataset.search = `${name} ${info.cn} ${info.desc}`.toLowerCase();
      row.innerHTML = `<div class="field-label"><label for="param-${name}" title="${escapeHtml(info.desc)}">${escapeHtml(info.cn)}</label><small>${name}</small></div><div class="input-shell"><input id="param-${name}" name="${name}" type="number" step="${info.type === "int" ? "1" : "any"}" required aria-describedby="unit-${name}"><span class="field-unit" id="unit-${name}">${escapeHtml(info.unit || "无量纲")}</span></div>`;
      row.querySelector("input").value = data.values[name];
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
      const text = data.returncode === 2 ? "达到迭代上限，未收敛" : "计算失败";
      status(text, "error");
      $("progress-title").textContent = text;
      $("progress-card").classList.add("error");
      message(text + "，请检查参数与运行日志。", "error");
      if (data.returncode === 2) {
        await loadResults();
        $("result-caption").textContent = "本次计算未收敛 · 结果仅供诊断";
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
  $("heat-panel").hidden = !isRsc;
  $("zone-legend").hidden = !isRsc;
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
      size: 11,
      color: "#647383",
    },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    margin: { l: 56, r: 22, t: 28, b: 52 },
    xaxis: {
      title: { text: xTitle, font: { size: 11 } },
      gridcolor: "#edf1f4",
      zeroline: false,
      automargin: true,
    },
    yaxis: {
      title: { text: yTitle, font: { size: 11 } },
      gridcolor: "#e7edf1",
      zeroline: false,
      automargin: true,
    },
    legend: { orientation: "h", x: 0, y: 1.15, font: { size: 10 } },
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
    line: { width: 2.5, color: options.color || GAS_COLORS[key] || COLORS[i] },
    hovertemplate: "%{y:.4g}<extra>%{fullData.name}</extra>",
  }));
  const spec = layout(yTitle, options.x === "Iter" ? "迭代次数" : "格子号");
  spec.showlegend = keys.length > 1;
  if (options.log) spec.yaxis.type = "log";
  if (options.zones && rows.length > 30) {
    spec.shapes = [
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
        text: "燃烧室出口",
        showarrow: false,
        xanchor: "right",
        yshift: 15,
        font: { size: 10, color: "#147d73" },
      },
    ];
  }
  Plotly.newPlot(id, traces, spec, PLOT_CONFIG);
}
function plotBar(id, data, unit, horizontal = false) {
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
    spec.xaxis.range = [0, Math.max(...values, 1) * 1.23];
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
    `<table><thead><tr>${columns.map((c) => `<th scope="col">${escapeHtml(OUTPUT_LABELS[c] || GAS_LABELS[c] || c)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${columns.map((c) => `<td>${escapeHtml(formatters[c] ? formatters[c](row[c]) : finite(row[c]) ? fmt(row[c], c === "I" || c === "Iter" || c === "KONVER" ? 0 : 3) : row[c])}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
function objectTable(id, data, label) {
  renderTable(
    id,
    ["组分", label],
    Object.entries(data).map(([k, v]) => ({
      组分: GAS_LABELS[k] || k,
      [label]: v,
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
  if (id === "tab-syngas") {
    plotBar("plot-syngas", r.syngas_composition || {}, "%");
    plotBar("plot-volume", r.volume_flow || {}, "Nm³/s");
    objectTable("syngas-table", r.syngas_composition || {}, "体积分数 (%)");
    objectTable("volume-table", r.volume_flow || {}, "流量 (Nm³/s)");
    const wet = r.wet_syngas;
    if (wet) {
      $("wet-summary").textContent =
        `H₂O 体积分数 ${fmt(wet.h2o_frac * 100, 3)}% · 湿基总流量 ${fmt(wet.total_wet_nms, 3)} Nm³/s（${fmt(wet.total_wet_nmh, 1)} Nm³/h）`;
      plotBar("plot-wet", wet.wet_flow_nmh, "Nm³/h");
      renderTable(
        "wet-table",
        ["组分", "Nm³/s", "Nm³/h"],
        Object.keys(wet.wet_flow_nms).map((k) => ({
          组分: GAS_LABELS[k] || k,
          "Nm³/s": wet.wet_flow_nms[k],
          "Nm³/h": wet.wet_flow_nmh[k],
        })),
      );
    } else {
      $("wet-summary").textContent = "没有可用的湿基组成数据。";
      $("plot-wet").replaceChildren();
      $("wet-table").replaceChildren();
    }
  }
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
