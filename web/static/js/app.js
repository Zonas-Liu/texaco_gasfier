/* TEXACO 工作台：所有指标来自计算输出，缺失值以破折号显示。 */
const OUTPUT_LABELS = {
  Iter: "迭代",
  KONVER: "收敛标志",
  SUMFE: "气体组分修正量 (kmol/s)",
  SUMWE: "固体流修正量 (kg/s)",
  SUMX: "碳分数修正量",
  SUMT: "温度修正量 (K)",
  I: "格子号",
  "H(m)": "高度 (m)",
  "U0(m/s)": "气速 (m/s)",
  "ResidenceTime(s)": "累计停留时间 (s)",
  "WE(kg/s)": "总固体流 (kg/s)",
  "T(C)": "温度 (°C)",
  "X(%)": "碳转化指标 (%)",
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
// 颜色具有固定语义：热端琥珀色，RSC冷蓝，物种颜色跨图表一致。
const COLORS = ["#204f9c", "#c16b22", "#5a8cbb", "#8b6d9d", "#8492a6", "#9a7a55", "#607f6d", "#658e9a"];
const GAS_COLORS = { CO:"#204f9c", H2:"#5a8cbb", CO2:"#a2b7d1", CH4:"#c16b22", H2S:"#8b6d9d", N2:"#8492a6", O2:"#607f6d", H2O:"#658e9a" };
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
  outletBasis: "dry",
  flowUnit: "kmol/h",
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
  const inverse = $("param-FEED_MODE")?.value === "1";
  for (const [name, info] of Object.entries(state.info)) {
    if (info.group === "燃烧室反算" && name !== "FEED_MODE") {
      $(`param-${name}`).disabled = state.polling || !inverse;
      $(`param-${name}`).closest(".form-group").classList.toggle("mode-inactive", !inverse);
    }
  }
  for (const [name, normal, initial] of [["FOXY", "氧煤比", "氧煤比搜索初值"], ["BSLURRY", "水煤浆质量流量", "煤浆量搜索初值"]]) {
    const label = document.querySelector(`label[for="param-${name}"]`);
    if (label) label.textContent = inverse ? initial : normal;
  }
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
        : state.result && (state.result.feed_design?.overall_success === false || state.result.rsc_design?.success === false || state.result.convergence_history?.at(-1)?.KONVER !== 0)
          ? "本次计算未通过全部收敛条件 · 结果仅供诊断"
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
  $("btn-close-params").addEventListener("click", () => drawer(false));
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
  document.querySelectorAll("[data-reset-panel]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(`#${button.dataset.resetPanel} .js-plotly-plot`)
        .forEach((plot) => Plotly.relayout(plot, { "xaxis.autorange": true, "yaxis.autorange": true }));
    });
  });
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
    "燃烧室反算",
    "进料参数",
    "辐射废锅设计",
    "状态与几何",
    "煤质与操作",
    "控制与收敛",
  ];
  for (const group of order.filter((g) => data.grouped[g])) {
    const details = document.createElement("details");
    details.className = "param-group";
    details.open = ["进料参数", "燃烧室反算"].includes(group);
    const summary = document.createElement("summary");
    summary.innerHTML =
      '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5"/></svg>' +
      escapeHtml(group);
    details.append(summary);
    const fields = document.createElement("div");
    fields.className = "group-fields";
    if (group === "燃烧室反算") {
      const hint = document.createElement("p");
      hint.className = "parameter-hint";
      hint.textContent = "选择给定进料，或用出口温度与有效气量反算进料。";
      fields.append(hint);
    }
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
      row.innerHTML = `<div class="field-label"><label for="param-${name}" title="${escapeHtml(info.desc)}">${escapeHtml(info.cn)}</label><small>${name}</small></div><div class="input-shell"><input id="param-${name}" name="${name}" type="number" step="${info.type === "int" ? "1" : "any"}" required aria-describedby="unit-${name}"><span class="field-unit" id="unit-${name}">${escapeHtml(info.display?.unit || info.unit || "")}</span></div>`;
      if (info.options) {
        row.classList.add("select-field");
        const select = document.createElement("select");
        select.id = `param-${name}`;
        select.name = name;
        for (const [value, label] of Object.entries(info.options))
          select.add(new Option(label, value));
        row.querySelector("input").replaceWith(select);
      }
      const display = info.display || { scale: 1, offset: 0 };
      row.querySelector("input,select").value = Number((data.values[name] * display.scale + display.offset).toPrecision(12));
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
    const display = state.info[name].display || { scale: 1, offset: 0 };
    data[name] = (Number(input.value) - display.offset) / display.scale;
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
    $("result-caption").textContent = e.status === 404
      ? "设置工况并运行模拟，生成第一组结果"
      : "暂时无法读取结果，请重试";
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
  renderProcess(r, isRsc);
  $("model-name").textContent = isRsc ? "晋华炉 3.0" : "TEXACO";
  const final = r.outlet_sections?.at(-1),
    flows = Object.values(r.volume_flow || {}),
    total = finite(final?.total_dry_nms) ? final.total_dry_nms : flows.length ? flows.reduce((a, b) => a + b, 0) : null;
  $("summary-grid").innerHTML =
    metric("碳转化率", finite(r.outlet?.CarbonConversion) ? fmt(r.outlet.CarbonConversion * 100) : "—", "%") +
    metric("干基煤气流量", fmt(finite(total) ? total * 3600 : null, 0), "Nm³/h") +
    metric("出口有效气量", fmt(final?.effective_gas_nmh, 0), "Nm³/h") +
    (isRsc ? metric("总产汽量", fmt(heat.steam_total_tph), "t/h") : metric("迭代次数", last ? last.Iter : "—", "次"));
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
  if (r.feed_design)
    status(r.feed_design.overall_success ? "双目标反算已完成" : "反算目标未全部达到",
      r.feed_design.overall_success ? "success" : "error");
  renderFeedDesign(r.feed_design);
  $("heat-panel").hidden = !isRsc;
  $("zone-legend").hidden = !isRsc;
  renderDesign(r.rsc_design);
  const wall = heat.steam_wall_tph, rsc = heat.steam_rsc_tph;
  $("heat-metrics").innerHTML = isRsc ?
    `<div class="heat-row"><span>燃烧室水冷壁</span><small>回收热负荷 ${fmt(heat.heat_wall_mw, 3)} MW</small><strong>${fmt(wall)}<small>t/h</small></strong></div>
     <div class="heat-row"><span>辐射废锅</span><small>回收热负荷 ${fmt(heat.heat_rsc_mw, 3)} MW</small><strong>${fmt(rsc)}<small>t/h</small></strong></div>
     <div class="heat-row pressure"><span>汽包压力</span><strong>${fmt(finite(heat.drum_pressure_mpa) ? heat.drum_pressure_mpa - 0.101325 : null, 3)}<small>MPaG</small></strong></div>` : "";
  const sum = finite(wall) && finite(rsc) ? wall + rsc : null;
  $("heat-allocation").innerHTML = finite(sum) && sum > 0 && wall >= 0 && rsc >= 0 ?
    `<div class="heat-allocation-label"><span>产汽分配</span><strong>废锅占比 ${fmt(rsc / sum * 100, 1)}%</strong></div><div class="heat-allocation-bar" aria-label="水冷壁与废锅产汽占比"><span style="width:${wall / sum * 100}%"></span><span style="width:${rsc / sum * 100}%"></span></div>` : "";
}
// 工艺示意只绑定本次结果，绝不借用用户正在编辑的参数填补旧输出。
function renderProcess(r, isRsc) {
  const sections = r.outlet_sections || [],
    chamber = sections.find((s) => s.key === "chamber"),
    rsc = sections.find((s) => s.key === "rsc");
  $("process-board").classList.toggle("texaco", !isRsc);
  document.querySelector(".process-section h2").textContent = isRsc ? "气化与热回收" : "气化流程";
  document.querySelector(".gasifier-drawing").setAttribute("aria-label", isRsc ? "燃烧室与辐射废锅串联示意，非尺寸比例图" : "TEXACO 气化炉示意，非尺寸比例图");
  $("chamber-stage-label").textContent = isRsc ? "燃烧室出口" : "气化炉出口";
  $("process-chamber-temp").textContent = fmt(chamber?.temperature_c, 1);
  $("process-chamber-gas").textContent = fmt(chamber?.effective_gas_nmh, 0);
  $("process-rsc-temp").textContent = fmt(rsc?.temperature_c, 1);
  $("process-rsc-steam").textContent = fmt(r.heat_recovery?.steam_rsc_tph);
  const delta = isRsc && finite(chamber?.temperature_c) && finite(rsc?.temperature_c) ? chamber.temperature_c - rsc.temperature_c : null;
  $("temperature-drop").textContent = finite(delta) ? `废锅温降 ${fmt(delta, 1)} ℃` : "";
  document.querySelector("#tab-syngas .section-heading h2").textContent = isRsc ? "两处出口，同一工况" : "气化炉出口合成气";
  document.querySelector("#tab-syngas .section-heading p").textContent = isRsc ? "并列核对组成、摩尔流量与灰流量" : "核对出口组成、摩尔流量与灰流量";
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
      family: "Bahnschrift, Microsoft YaHei UI, Microsoft YaHei, sans-serif",
      size: 12,
      color: "#60718a",
    },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    margin: { l: 64, r: 22, t: 28, b: 52 },
    xaxis: {
      title: { text: xTitle, font: { size: 12 } },
      showgrid: false,
      showline: true,
      linecolor: "#d6e0ea",
      ticks: "outside",
      tickcolor: "#d6e0ea",
      ticklen: 4,
      nticks: 7,
      zeroline: false,
      automargin: true,
      tickfont: { size: 11 },
      showspikes: true,
      spikemode: "across",
      spikesnap: "cursor",
      spikethickness: 1,
      spikecolor: "#a2b7d1",
    },
    yaxis: {
      title: { text: yTitle, font: { size: 12 }, standoff: 12 },
      gridcolor: "#e8edf4",
      nticks: 5,
      zeroline: false,
      automargin: true,
      tickfont: { size: 11 },
      separatethousands: true,
    },
    legend: {
      orientation: "h",
      x: 0,
      y: -0.24,
      yanchor: "top",
      font: { size: 12 },
      traceorder: "normal",
      itemsizing: "constant",
    },
    hovermode: "x unified",
    hoverlabel: { bgcolor: "#24334a", font: { color: "#fff", size: 12 } },
    showlegend: false,
  };
}
function seriesUnit(key, title) {
  return ({SUMFE: "kmol/s", SUMWE: "kg/s", SUMX: "（无量纲）", SUMT: "K"})[key]
    ?? title.match(/\(([^)]+)\)/)?.[1] ?? "";
}
function plotLine(id, rows, keys, yTitle, options = {}) {
  if (!rows.length) return;
  const traces = keys.map((key, i) => ({
    x: rows.map((r) => r[options.x || "I"]),
    y: rows.map((r) => r[key]),
    name: ({SUMFE:'气体组分',SUMWE:'固体流',SUMX:'碳分数',SUMT:'温度'})[key] || GAS_LABELS[key] || OUTPUT_LABELS[key] || key,
    mode: "lines",
    connectgaps: false,
    line: {
      width: 2.4,
      shape: "linear",
      color: options.color || GAS_COLORS[key] || COLORS[i],
      dash: options.log && i > 0 ? ["solid", "dot", "dash"][i] : "solid",
    },
    hovertemplate: `%{y:${options.log ? ".3e" : ",.4~g"}} ${escapeHtml(seriesUnit(key, yTitle))}<extra>%{fullData.name}</extra>`,
  }));
  const spec = layout(yTitle, options.x === "Iter" ? "迭代次数" : "格子号");
  spec.showlegend = keys.length > 1;
  spec.xaxis.hoverformat = ".0f";
  if (keys.length > 1 || options.legendSpace) spec.margin.b = 90;
  if (options.log) {
    spec.yaxis.type = "log";
    spec.yaxis.exponentformat = "power";
    spec.yaxis.showexponent = "all";
  } else if (keys[0] === "T(C)") spec.yaxis.tickformat = ",.0f";
  if (options.zones && rows.length > 30) {
    // 分段着色沿用原网格数值，交界点共用以保持曲线连续。
    const hot = rows.filter((r) => r.I <= 30), cool = rows.filter((r) => r.I >= 30);
    traces[0].x = hot.map((r) => r.I);
    traces[0].y = hot.map((r) => r[keys[0]]);
    traces[0].name = "燃烧室";
    traces.push({ ...traces[0], x: cool.map((r) => r.I), y: cool.map((r) => r[keys[0]]),
      name: "辐射废锅", line: { ...traces[0].line, color: "#5a8cbb" } });
    spec.shapes = [
      {
        type: "rect",
        x0: 30,
        x1: rows.at(-1).I,
        y0: 0,
        y1: 1,
        yref: "paper",
        fillcolor: "rgba(90,140,187,0.06)",
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
        line: { color: "#9db6cd", width: 1.2, dash: "dot" },
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
        yshift: 8,
        font: { size: 11, color: "#204f9c" },
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
        color: ["#c16b22", "#5a8cbb"],
        line: { color: "#fff", width: 2 },
      },
    });
    exits.forEach((r, i) =>
      spec.annotations.push({
        x: r.I,
        y: r[keys[0]],
        text: `${fmt(r[keys[0]], 1)} ℃`,
        showarrow: true,
        arrowhead: 0,
        arrowcolor: "#aebdc5",
        ax: i === 0 ? 0 : -52,
        ay: i === 0 ? -36 : -28,
        bgcolor: "#fff",
        borderpad: 3,
        font: { size: 12, color: i === 0 ? "#a55719" : "#204f9c" },
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
    customdata: values.map((v) => finite(v) ? v.toPrecision(5) : "—"),
    text: horizontal ? [] : values.map((v) => fmt(v, 2)),
    textposition: "outside",
    cliponaxis: false,
    hovertemplate: `%{customdata} ${unit}<extra></extra>`,
  };
  const spec = layout(
    horizontal ? "" : unit,
    horizontal ? `体积分数 (${unit})` : "组分",
  );
  spec.margin = { l: 42, r: 88, t: 18, b: 44 };
  spec.bargap = 0.52;
  spec.hovermode = "closest";
  if (horizontal) {
    spec.yaxis.autorange = "reversed";
    spec.yaxis.tickmode = "array";
    spec.yaxis.tickvals = keys.map((k) => GAS_LABELS[k] || k);
    spec.xaxis.range = [0, maximum || Math.ceil(Math.max(...values, 1) / 10) * 10];
    spec.xaxis.tickformat = ".0f";
    spec.yaxis.showgrid = false;
    spec.annotations = keys.map((k, i) => ({
      x: 1.03, xref: "paper", xanchor: "left", y: GAS_LABELS[k] || k,
      text: `${values[i] !== 0 && Math.abs(values[i]) < .01 ? values[i].toExponential(1) : fmt(values[i], 2)}${unit}`,
      showarrow: false, font: { size: 12, color: "#24334a" },
    }));
  } else {
    spec.yaxis.range = [0, Math.max(...values, 1) * 1.22];
    spec.xaxis.showgrid = false;
  }
  Plotly.newPlot(id, [trace], spec, PLOT_CONFIG);
}
// 仅格式化展示：微量非零数保留科学计数，title保留输出原值。
function numberCell(value, digits = 3) {
  if (!finite(value)) return '<span class="missing-value" aria-label="未记录">—</span>';
  const small = value !== 0 && Math.abs(value) < 10 ** -digits;
  const text = small ? value.toExponential(2) : fmt(value, digits);
  const display = small ? text.replace(/e([+-]?\d+)/, (_, exponent) => ` × 10<sup>${Number(exponent)}</sup>`) : text;
  return `<span class="numeric-value${small ? ' scientific-value' : ''}" title="原始值 ${value}">${display}</span>`;
}
function columnHeading(column) {
  const label = OUTPUT_LABELS[column] || GAS_LABELS[column] || column;
  const match = label.match(/^(.*?)\s*\(([^)]+)\)$/);
  return match ? `${escapeHtml(match[1])}<small class="column-unit">${escapeHtml(match[2])}</small>` : escapeHtml(label);
}
function renderTable(id, columns, rows, formatters = {}) {
  const host = $(id);
  host.tabIndex = 0;
  host.setAttribute("role", "region");
  host.setAttribute("aria-label", `${id === 'history-table' ? '迭代' : '计算'}明细，可横向滚动`);
  if (!rows.length) { host.textContent = "暂无数据"; return; }
  const exits = state.result?.outlet_sections || [];
  host.innerHTML = `<table class="detail-table"><caption>${rows.length} 条记录 · 悬停数值查看原始值</caption><thead><tr>${columns.map((c) => `<th scope="col">${columnHeading(c)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => {
    const outlet = finite(row.I) ? exits.find((s) => s.cell === row.I) : null;
    return `<tr class="${outlet ? 'section-boundary' : ''}">${columns.map((c, index) => {
      let value = formatters[c] ? escapeHtml(formatters[c](row[c])) : finite(row[c]) ? numberCell(row[c], ["I", "Iter", "KONVER", "轮次", "内层迭代"].includes(c) ? 0 : c === 'T(C)' ? 2 : 3) : escapeHtml(row[c]);
      if (c === "KONVER" && finite(row[c])) value = `<span class="table-state ${row[c] === 0 ? 'converged' : ''}" title="KONVER=${row[c]}">${row[c] === 0 ? '收敛' : '未收敛'}</span>`;
      return index === 0 ? `<th scope="row">${value}${outlet ? `<small class="row-context">${escapeHtml(outlet.label)}</small>` : ''}</th>` : `<td>${value}</td>`;
    }).join('')}</tr>`;
  }).join('')}</tbody></table>`;
}
const OUTLET_SPECIES = ["CO", "H2", "CO2", "CH4", "N2", "H2S", "O2", "H2O"];
function outletFlow(section, gas, unit) {
  if (unit === "kmol/h") return section.molar_flow_kmol_h?.[gas];
  const flow = section.volume_flow?.[gas];
  return finite(flow) ? flow * (unit === "Nm³/h" ? 3600 : 1) : null;
}
function outletTotal(section, unit) {
  if (unit === "kmol/h") return section.total_molar_kmol_h;
  return finite(section.total_wet_nms) ? section.total_wet_nms * (unit === "Nm³/h" ? 3600 : 1) : null;
}
function compositionTotal(section, basis) {
  const keys = OUTLET_SPECIES.filter((g) => basis === 'wet' || g !== 'H2O');
  const data = section[`${basis}_composition`] || {};
  return keys.every((g) => finite(data[g])) ? keys.reduce((sum, g) => sum + data[g], 0) : null;
}
function outletCsv(sections, unit) {
  const header = ['组分', ...sections.flatMap((s) => [`${s.label} 干基 (%)`, `${s.label} 湿基 (%)`, `${s.label} 流量 (${unit})`])];
  const rows = OUTLET_SPECIES.map((g) => [g, ...sections.flatMap((s) => [s.dry_composition?.[g], s.wet_composition?.[g], outletFlow(s,g,unit)])]);
  rows.push(['合计', ...sections.flatMap((s) => [compositionTotal(s,'dry'), compositionTotal(s,'wet'), outletTotal(s,unit)])]);
  rows.push(['灰质量流量 (kg/h)', ...sections.flatMap((s) => ['', '', s.ash_kg_h])]);
  return [header,...rows].map((row) => row.map((v) => `"${String(v ?? '').replaceAll('"','""')}"`).join(',')).join('\r\n');
}
function downloadOutletCsv(sections) {
  const blob = new Blob(['\ufeff',outletCsv(sections,state.flowUnit)], {type:'text/csv;charset=utf-8'});
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url;
  link.download = 'outlet-comparison.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function renderOutletMatrix(sections) {
  const unit = state.flowUnit;
  $('outlet-matrix').innerHTML = `<table class="outlet-matrix${sections.length === 1 ? ' single-outlet' : ''}"><caption>8 种组分 · 气体流量合计包含水蒸气；灰单独列示</caption><thead>
    <tr class="outlet-column-groups"><th rowspan="2" scope="col">组分</th>${sections.map((s) => `<th scope="colgroup" colspan="3" class="${s.key}">${escapeHtml(s.label)}<small>${fmt(s.temperature_c,1)} ℃</small></th>`).join('')}</tr>
    <tr>${sections.map(() => `<th scope="col" class="group-start">干基<small class="column-unit">%</small></th><th scope="col">湿基<small class="column-unit">%</small></th><th scope="col" class="flow-column">摩尔 / 标方流量<small class="column-unit">${unit}</small></th>`).join('')}</tr>
    </thead><tbody>${OUTLET_SPECIES.map((g) => `<tr class="${g === 'H2O' ? 'water-row' : ''}"><th scope="row"><span class="species-name">${GAS_LABELS[g]}</span>${g === 'H2O' ? '<small class="row-context">水蒸气</small>' : ''}</th>${sections.map((s) => `<td class="group-start">${numberCell(s.dry_composition?.[g])}</td><td>${numberCell(s.wet_composition?.[g])}</td><td class="flow-column">${numberCell(outletFlow(s,g,unit))}</td>`).join('')}</tr>`).join('')}</tbody>
    <tfoot><tr><th scope="row">合计</th>${sections.map((s) => `<td class="group-start">${numberCell(compositionTotal(s,'dry'))}</td><td>${numberCell(compositionTotal(s,'wet'))}</td><td class="flow-column">${numberCell(outletTotal(s,unit))}</td>`).join('')}</tr><tr class="ash-row"><th scope="row">灰<small class="column-unit">kg/h</small></th>${sections.map((s) => `<td colspan="3" class="group-start">${numberCell(s.ash_kg_h,2)}</td>`).join('')}</tr></tfoot></table>`;
  // 列名随所选单位变化，避免将标方流量误称为摩尔流量。
  document.querySelectorAll('#outlet-matrix thead .flow-column').forEach((cell) => {
    cell.firstChild.textContent = unit === 'kmol/h' ? '摩尔流量' : '标方流量';
  });
}
function renderOutletChart(sections) {
  const basis = state.outletBasis, keys = OUTLET_SPECIES.filter((g) => basis === 'wet' || g !== 'H2O');
  const traces = sections.map((s) => ({
    type:'bar', orientation:'h', name:s.label,
    x:keys.map((g) => finite(s[`${basis}_composition`]?.[g]) ? s[`${basis}_composition`][g] : null),
    y:keys.map((g) => GAS_LABELS[g]),
    marker:{color:s.key === 'rsc' ? '#5a8cbb' : '#c16b22'},
    customdata:keys.map((g) => finite(s[`${basis}_composition`]?.[g]) ? s[`${basis}_composition`][g].toPrecision(5) : '未记录'),
    hovertemplate:'%{y}　%{customdata}%<extra>%{fullData.name}</extra>',
  }));
  const spec = layout('', '体积分数 / %');
  spec.margin = {l:40,r:16,t:12,b:72};
  spec.barmode = 'group'; spec.bargap = .32; spec.bargroupgap = .14;
  spec.showlegend = sections.length > 1;
  spec.legend = {...spec.legend,y:-.2,font:{size:11}};
  spec.hovermode = 'y unified';
  spec.xaxis = {...spec.xaxis,showgrid:true,gridcolor:'#e8edf4',showspikes:false,rangemode:'tozero',tickformat:'.0f'};
  spec.yaxis = {...spec.yaxis,autorange:'reversed',showgrid:false,tickmode:'array',tickvals:keys.map((g) => GAS_LABELS[g])};
  Plotly.newPlot('plot-outlet-comparison',traces,spec,PLOT_CONFIG);
  document.querySelectorAll('[data-outlet-basis]').forEach((button) => button.setAttribute('aria-pressed',String(button.dataset.outletBasis === basis)));
  $('composition-basis-note').textContent = basis === 'dry' ? '干基扣除水蒸气；小组分保留真实比例。' : '湿基包含水蒸气；与下方湿基列一一对应。';
}
function renderOutlets(sections) {
  const host = $('outlet-comparison');
  document.querySelector('.comparison-key').hidden = true;
  if (!sections.length) { host.textContent = '没有可用的出口截面数据，请重新运行模拟。'; return; }
  host.innerHTML = `<div class="outlet-analysis panel">
    <section class="composition-comparison" aria-label="出口组成对比"><div class="data-panel-heading"><h3>组成对比</h3><div class="segmented" role="group" aria-label="组成基准"><button type="button" data-outlet-basis="dry">干基</button><button type="button" data-outlet-basis="wet">湿基</button></div></div><div id="plot-outlet-comparison" class="plot comparison-plot"></div><p id="composition-basis-note" class="chart-note"></p></section>
    <div class="outlet-readouts">${sections.map((s) => `<section class="outlet-readout ${s.key}"><div class="readout-heading"><h3>${escapeHtml(s.label)}<small>第 ${s.cell} 格</small></h3><strong>${fmt(s.temperature_c,1)}<small>℃</small></strong></div><dl><div><dt>干基气量 <small>Nm³/h</small></dt><dd>${numberCell(finite(s.total_dry_nms) ? s.total_dry_nms * 3600 : null,1)}</dd></div><div><dt>有效气量 <small>CO＋H₂ · Nm³/h</small></dt><dd>${numberCell(s.effective_gas_nmh,1)}</dd></div><div><dt>H₂ / CO</dt><dd>${numberCell(s.h2_co_ratio,3)}</dd></div><div><dt>灰质量流量 <small>kg/h</small></dt><dd>${numberCell(s.ash_kg_h,2)}</dd></div></dl></section>`).join('')}</div>
    </div><section class="panel outlet-data-panel"><div class="data-panel-heading"><div><h3>组分与流量明细</h3><p>同一组分横向比较；悬停数值查看原始值。</p></div><div class="table-actions"><label for="outlet-flow-unit">流量单位</label><select id="outlet-flow-unit"><option>kmol/h</option><option>Nm³/h</option><option>Nm³/s</option></select><button class="btn btn-outline btn-small" id="download-outlets">下载 CSV</button></div></div><div class="table-wrap" id="outlet-matrix" tabindex="0" role="region" aria-label="出口组分对照表，可横向滚动"></div><p class="table-footnote">— 表示未记录或不适用；微量非零数使用科学计数法。下载保留原始精度。</p></section>`;
  $('outlet-flow-unit').value = state.flowUnit;
  $('outlet-flow-unit').addEventListener('change', (event) => {state.flowUnit = event.target.value; renderOutletMatrix(sections);});
  $('download-outlets').addEventListener('click', () => downloadOutletCsv(sections));
  document.querySelectorAll('[data-outlet-basis]').forEach((button) => button.addEventListener('click', () => {state.outletBasis = button.dataset.outletBasis; renderOutletChart(sections);}));
  renderOutletChart(sections);
  renderOutletMatrix(sections);
}
function renderFeedDesign(design) {
  $("feed-design-result").hidden = !design;
  if (!design) return;
  $("feed-design-result").innerHTML =
    `<div class="design-heading"><h3>燃烧室目标工况反算</h3><span class="design-state ${design.success ? "" : "failed"}">${design.success ? "双目标已达到" : "目标未达到"}</span></div>
    <div class="design-metrics">${metric("反算氧煤比", fmt(design.oxygen_coal_ratio, 5), "kg O₂/kg BSWAF")}${metric("反算煤浆总量", fmt(design.slurry_kg_s, 4), "kg/s")}${metric("燃烧室出口温度", fmt(design.temperature_c, 2), "℃")}${metric("有效气量 CO＋H₂", fmt(design.effective_gas_nmh, 1), "Nm³/h")}</div>
    <p class="design-note">目标 ${fmt(design.target_temperature_c, 1)} ℃ / ${fmt(design.target_effective_gas_nmh, 1)} Nm³/h · 温差 ${fmt(design.temperature_error_c, 3)} ℃ · 气量差 ${fmt(design.flow_error_nmh, 2)} Nm³/h</p>
    <p class="design-note">${escapeHtml(design.message)} · 允许误差 ±${fmt(design.temperature_tolerance_c, 1)} ℃ / ±${fmt(design.flow_tolerance_nmh, 1)} Nm³/h。反算值见上方，输入框保留搜索初值。</p>
    <details class="design-history"><summary>查看氧煤比与进料量求解过程（${design.evaluations} 次试算）</summary><div class="table-wrap" id="feed-design-table"></div></details>`;
  renderTable("feed-design-table", ["轮次", "氧煤比", "煤浆量 (kg/s)", "出口温度 (℃)", "有效气量 (Nm³/h)", "内层状态"],
    design.trials.map((t, i) => ({轮次: i + 1, 氧煤比: t.oxygen_coal_ratio, "煤浆量 (kg/s)": t.slurry_kg_s,
      "出口温度 (℃)": t.temperature_c, "有效气量 (Nm³/h)": t.effective_gas_nmh, 内层状态: t.converged ? "收敛" : "未收敛"})));
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
      color: "#c16b22",
      zones: Object.keys(heat).length > 0,
    });
    plotBar("plot-overview-gas", r.outlet_sections?.at(-1)?.dry_composition || r.syngas_composition || {}, "%", true);
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
      legendSpace: true,
      color: "#c16b22",
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
      color: "#c16b22",
      zones: Object.keys(heat).length > 0,
    });
    plotLine("plot-x", internal, ["X(%)"], "碳转化指标 (%)");
    plotLine("plot-we", internal, ["WE(kg/s)"], "总固体流 (kg/s)");
    plotLine("plot-u0", internal, ["U0(m/s)"], "气速 (m/s)");
    renderTable(
      "internal-table",
      ["I", "H(m)", "U0(m/s)", "ResidenceTime(s)", "WE(kg/s)", "T(C)", "X(%)"],
      internal,
    );
    plotLine("plot-gas-main", gas, ["CO", "H2", "CO2", "H2O"], "体积分数 (%)");
    plotLine("plot-gas-other", gas, ["CH4", "N2", "H2S", "O2"], "体积分数 (%)");
    renderTable(
      "gas-table",
      ["I", "O2", "CH4", "CO", "CO2", "H2S", "H2", "N2", "H2O"],
      gas,
    );
  }
}
