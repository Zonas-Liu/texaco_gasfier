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
const CHART = { ink:"#24334a", muted:"#526780", grid:"#e3eaf2", hot:"#b56320", cool:"#306daf", blue:"#245ca6", teal:"#137f78", slate:"#63748b", purple:"#805b98" };
const COLORS = [CHART.blue, CHART.teal, CHART.slate, CHART.purple, CHART.hot, "#a94f6a", "#687b37", "#526875"];
const GAS_COLORS = { CO:CHART.blue, H2:CHART.teal, CO2:CHART.slate, CH4:CHART.hot, H2S:"#a94f6a", N2:"#526875", O2:"#687b37", H2O:CHART.purple };
const GAS_DASHES = { CO:"solid", H2:"dash", CO2:"dot", H2O:"dashdot", CH4:"solid", N2:"dash", H2S:"dot", O2:"dashdot" };
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
  $("zone-legend").hidden = true; // 分区图例统一在图表上方呈现。
  renderDesign(r.rsc_design);
  const wall = heat.steam_wall_tph, rsc = heat.steam_rsc_tph;
  $("heat-metrics").innerHTML = isRsc ?
    `<div class="heat-row"><span>燃烧室水冷壁</span><small>回收热负荷 ${fmt(heat.heat_wall_mw, 3)} MW</small><strong>${fmt(wall)}<small>t/h</small></strong></div>
     <div class="heat-row"><span>辐射废锅</span><small>回收热负荷 ${fmt(heat.heat_rsc_mw, 3)} MW</small><strong>${fmt(rsc)}<small>t/h</small></strong></div>
     <div class="heat-row pressure"><span>汽包压力</span><strong>${fmt(finite(heat.drum_pressure_mpa) ? heat.drum_pressure_mpa - 0.101325 : null, 3)}<small>MPaG</small></strong></div>` : "";
  const sum = finite(wall) && finite(rsc) ? wall + rsc : null;
  $("heat-allocation").innerHTML = finite(sum) && sum > 0 && wall >= 0 && rsc >= 0 ?
    `<div class="heat-allocation-label"><span>产汽分配</span><strong>合计 ${fmt(sum, 2)} t/h</strong></div><div class="heat-allocation-bar" role="img" aria-label="水冷壁产汽占${fmt(wall / sum * 100, 1)}%，废锅产汽占${fmt(rsc / sum * 100, 1)}%"><span style="width:${wall / sum * 100}%"></span><span style="width:${rsc / sum * 100}%"></span></div><div class="heat-share-legend"><span><i aria-hidden="true"></i>水冷壁 <b>${fmt(wall / sum * 100, 1)}%</b></span><span><i aria-hidden="true"></i>辐射废锅 <b>${fmt(rsc / sum * 100, 1)}%</b></span></div>` : "";
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
  responsive: true, displaylogo: false, displayModeBar: false, scrollZoom: false,
};
// 图形、悬浮读数和键盘读数共用显示规则；原始值始终保留。
function chartNumber(value, digits = 2) {
  if (!finite(value)) return "—";
  if (value !== 0 && (Math.abs(value) < .01 || Math.abs(value) >= 1e7)) return value.toExponential(3);
  return fmt(value, digits);
}
function seriesLabel(key) {
  return ({SUMFE:"气体组分", SUMWE:"固体流", SUMX:"碳分数", SUMT:"温度"})[key]
    || GAS_LABELS[key] || OUTPUT_LABELS[key]?.replace(/\s*\([^)]*\)/g, "") || key;
}
function seriesUnit(key, title) {
  return ({SUMFE:"kmol/s", SUMWE:"kg/s", SUMX:"（无量纲）", SUMT:"K"})[key]
    ?? title.match(/\(([^)]+)\)/)?.[1] ?? "";
}
function layout(yTitle, xTitle = "格子号") {
  return {
    font: {family:"Bahnschrift, Microsoft YaHei UI, Microsoft YaHei, sans-serif", size:12, color:CHART.muted},
    paper_bgcolor:"#ffffff", plot_bgcolor:"#fbfcfe",
    margin:{l:54, r:18, t:28, b:48},
    xaxis: {
      title:{text:xTitle, font:{size:12}, standoff:12},
      showgrid:false, showline:true, linecolor:CHART.grid,
      ticks:"outside", tickcolor:CHART.grid, ticklen:5, nticks:6,
      zeroline:false, automargin:true, tickfont:{size:12},
      showspikes:true, spikemode:"across", spikesnap:"data", spikethickness:1, spikecolor:"#849bb5",
    },
    yaxis: {
      title:{text:""}, gridcolor:CHART.grid, nticks:5,
      zeroline:false, automargin:true, tickfont:{size:12}, separatethousands:true,
    },
    annotations:yTitle ? [{text:yTitle, x:0, xref:"paper", xanchor:"left", y:1.06, yref:"paper", yanchor:"bottom", showarrow:false, font:{size:11, color:CHART.muted}}] : [],
    hovermode:"x unified", hoverdistance:35,
    hoverlabel:{bgcolor:"#ffffff", bordercolor:"#b8c9dc", font:{color:CHART.ink, size:12}, namelength:-1, align:"left"},
    showlegend:false, dragmode:"zoom", transition:{duration:0},
  };
}
function resetChart(plot) {
  Plotly.relayout(plot, {"xaxis.autorange":true, "yaxis.autorange":true});
}
// 原生控件放在绘图区外，图例可通过键盘切换，读数不依赖鼠标悬停。
function chartChrome(id, meta) {
  const host = $(id);
  if (!host) return;
  document.querySelectorAll(`[data-chart-owner="${id}"]`).forEach((node) => node.remove());
  host.setAttribute("role", "img");
  host.setAttribute("aria-label", `${meta.title}。${meta.summaryText}。逐点数据见图下方读数。`);
  const top = document.createElement("div");
  top.dataset.chartOwner = id;
  top.className = "chart-meta";
  top.innerHTML = `<div class="chart-summary">${meta.summary}</div><div class="chart-legend" aria-label="${escapeHtml(meta.title)}图例">${(meta.legend || []).map((item, index) => {
    const tag = item.indices ? 'button' : 'span';
    const dash = item.dash === 'dot' ? 'dotted' : item.dash && item.dash !== 'solid' ? 'dashed' : 'solid';
    return `<${tag} class="chart-key" ${item.indices ? `type="button" data-series="${index}" aria-pressed="true" aria-label="显示${escapeHtml(item.name)}"` : ''}><i class="${item.bar ? `bar-key${item.pattern ? ' patterned' : ''}` : ''}" aria-hidden="true" style="--series-color:${item.color};--series-dash:${dash}"></i>${escapeHtml(item.name)}</${tag}>`;
  }).join('')}</div>`;
  host.before(top);
  top.querySelectorAll('[data-series]').forEach((button) => button.addEventListener('click', () => {
    const active = button.getAttribute('aria-pressed') !== 'true';
    button.setAttribute('aria-pressed', String(active));
    Plotly.restyle(host, {visible:active ? true : 'legendonly'}, meta.legend[Number(button.dataset.series)].indices);
  }));
  const foot = document.createElement("div");
  foot.dataset.chartOwner = id;
  foot.className = "chart-footer";
  foot.innerHTML = `<details class="chart-reader"><summary>逐点读数</summary><div class="chart-reader-body"><label for="${id}-point">${escapeHtml(meta.pointLabel)}</label><select id="${id}-point">${meta.points.map((p, i) => `<option value="${i}">${escapeHtml(p.label)}</option>`).join('')}</select><dl aria-live="polite" aria-atomic="true"></dl></div></details><span class="chart-method">${escapeHtml(meta.note)}</span><button type="button" class="chart-reset" aria-label="恢复${escapeHtml(meta.title)}坐标范围">恢复</button>`;
  host.after(foot);
  const select = foot.querySelector('select'), output = foot.querySelector('dl');
  function updateReading() {
    const point = meta.points[Number(select.value)];
    output.innerHTML = point ? point.values.map((v) => `<div><dt>${escapeHtml(v.name)}</dt><dd title="原始值 ${escapeHtml(finite(v.value) ? v.value : '未记录')}">${escapeHtml(chartNumber(v.value, 4))}<small>${escapeHtml(v.unit)}</small></dd></div>`).join('') : '<div><dt>读数</dt><dd>未记录</dd></div>';
  }
  select.disabled = !meta.points.length;
  select.value = String(Math.max(0, meta.points.length - 1));
  updateReading();
  select.addEventListener('change', updateReading);
  foot.querySelector('button').addEventListener('click', () => resetChart(host));
}
function plotLine(id, rows, keys, yTitle, options = {}) {
  const xKey = options.x || 'I', isHistory = xKey === 'Iter';
  const unit = seriesUnit(keys[0], yTitle);
  const traces = keys.map((key, i) => ({
    type:'scatter', x:rows.map((r) => r[xKey]),
    // 对数轴不能绘制0或负值，明确断开；逐点读数和原始表仍保留原值。
    y:rows.map((r) => finite(r[key]) && (!options.log || r[key] > 0) ? r[key] : null),
    customdata:rows.map((r) => finite(r[key]) ? String(r[key]) : '未记录'),
    name:seriesLabel(key), mode:'lines+markers', connectgaps:false,
    line:{width:2.6, shape:'linear', simplify:false, color:options.color || GAS_COLORS[key] || COLORS[i], dash:GAS_DASHES[key] || 'solid'},
    marker:{size:rows.map((_, index) => index === rows.length - 1 ? 6 : 0)},
    hovertemplate:`%{customdata} ${escapeHtml(seriesUnit(key, yTitle))}<extra>%{fullData.name}</extra>`,
  }));
  const spec = layout(unit, isHistory ? '迭代次数' : '格子号');
  spec.xaxis.hoverformat = '.0f';
  if (options.log) {
    spec.yaxis.type = 'log'; spec.yaxis.exponentformat = 'power'; spec.yaxis.showexponent = 'all';
  } else {
    spec.yaxis.rangemode = 'tozero';
    if (keys[0] === 'T(C)') { spec.yaxis.rangemode = 'normal'; spec.yaxis.tickformat = ',.0f'; }
  }
  const legend = keys.length > 1 ? traces.map((t, i) => ({name:t.name, color:t.line.color, dash:t.line.dash, indices:[i]})) : [];
  if (options.zones && rows.some((r) => r.I > 30)) {
    // 分段着色沿用原网格数值，交界点共用；缺失点不补值、不插值。
    const hot = rows.filter((r) => r.I <= 30), cool = rows.filter((r) => r.I >= 30);
    const section = (data, name, color) => ({...traces[0], x:data.map((r) => r.I),
      y:data.map((r) => finite(r[keys[0]]) ? r[keys[0]] : null),
      customdata:data.map((r) => finite(r[keys[0]]) ? String(r[keys[0]]) : '未记录'),
      name, line:{...traces[0].line, color}, marker:{size:data.map((_, i) => i === data.length - 1 ? 7 : 0), color},
    });
    traces[0] = section(hot, '燃烧室', CHART.hot);
    traces.push(section(cool, '辐射废锅', CHART.cool));
    legend.push({name:'燃烧室', color:CHART.hot}, {name:'辐射废锅', color:CHART.cool});
    spec.shapes = [
      {type:'rect', x0:30, x1:rows.at(-1).I, y0:0, y1:1, yref:'paper', fillcolor:'rgba(48,109,175,.045)', line:{width:0}, layer:'below'},
      {type:'line', x0:30, x1:30, y0:0, y1:1, yref:'paper', line:{color:'#91a9c4', width:1, dash:'dot'}},
    ];
    spec.annotations.push({x:30, y:1.06, yref:'paper', xanchor:'center', yanchor:'bottom', text:'30格 · 燃烧室出口', showarrow:false, font:{size:10, color:CHART.muted}});
  }
  const last = rows.at(-1)?.[keys[0]], lead = isHistory ? '末次' : options.zones && rows.some((r) => r.I > 30) ? '废锅出口' : '出口';
  const summaryText = keys.length === 1 ? `${lead} ${chartNumber(last)} ${unit}` : `${keys.length} 种组分 · 湿基体积分数`;
  const summary = keys.length === 1 ? `<span>${lead}</span><strong>${escapeHtml(chartNumber(last))}</strong><small>${escapeHtml(unit)}</small>` : `<span>${escapeHtml(summaryText)}</span>`;
  if (!rows.length) spec.annotations.push({text:'暂无数据', x:.5, y:.5, xref:'paper', yref:'paper', showarrow:false});
  Plotly.newPlot(id, traces, spec, PLOT_CONFIG);
  chartChrome(id, {
    title:yTitle, summaryText, summary, legend,
    pointLabel:isHistory ? '迭代轮次' : '格子号',
    note:options.log ? '对数轴 · 非正值不绘制' : `${rows.length} 格 · 原始网格`,
    points:rows.map((r) => ({label:`第 ${r[xKey]} ${isHistory ? '次' : '格'}`, values:keys.map((key) => ({name:seriesLabel(key), value:r[key], unit:seriesUnit(key,yTitle)}))})),
  });
}
function plotBar(id, data, unit, horizontal = false, maximum = null) {
  const keys = horizontal ? ['CO','H2','CO2','CH4','N2','H2S','O2'] : Object.keys(data);
  const values = keys.map((k) => finite(data[k]) ? data[k] : null);
  const labels = keys.map((k) => GAS_LABELS[k] || k);
  const trace = {
    type:'bar', x:horizontal ? values : labels, y:horizontal ? labels : values,
    orientation:horizontal ? 'h' : 'v',
    marker:{color:keys.map((k) => GAS_COLORS[k] || COLORS[0])},
    customdata:keys.map((k) => finite(data[k]) ? String(data[k]) : '未记录'),
    hovertemplate:`%{customdata} ${escapeHtml(unit)}<extra></extra>`,
  };
  const spec = layout(horizontal ? '' : unit, horizontal ? `体积分数 / ${unit}` : '组分');
  spec.margin = {l:40, r:96, t:10, b:46}; spec.bargap = .55; spec.hovermode = 'closest';
  if (horizontal) {
    spec.yaxis = {...spec.yaxis, autorange:'reversed', categoryorder:'array', categoryarray:labels, showgrid:false};
    spec.xaxis = {...spec.xaxis, showgrid:true, gridcolor:CHART.grid, range:[0, maximum || Math.ceil(Math.max(...values.filter(finite),1)/10)*10], tickformat:'.0f', showspikes:false};
    spec.annotations = keys.map((k, i) => ({x:1.04, xref:'paper', xanchor:'left', y:labels[i], text:`${chartNumber(values[i])}${finite(values[i]) ? unit : ''}`, showarrow:false, font:{size:12, color:CHART.ink}}));
  } else spec.yaxis.rangemode = 'tozero';
  Plotly.newPlot(id, [trace], spec, PLOT_CONFIG);
  const effective = finite(data.CO) && finite(data.H2) ? data.CO + data.H2 : null;
  const summaryText = `CO＋H₂ ${chartNumber(effective)}%`;
  chartChrome(id, {title:'最终出口干基组成', summaryText,
    summary:`<span>CO＋H₂</span><strong>${chartNumber(effective)}</strong><small>%</small>`,
    pointLabel:'气体组分', note:'干基 · 真实比例',
    points:keys.map((k) => ({label:GAS_LABELS[k] || k, values:[{name:'干基体积分数', value:data[k], unit}]})),
  });
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
const OUTLET_NAMES = {CO:"一氧化碳", H2:"氢气", CO2:"二氧化碳", CH4:"甲烷", N2:"氮气", H2S:"硫化氢", O2:"氧气", H2O:"水蒸气"};
// 明细表整数/小数分层排版，仍沿用原有精度及微量值规则。
function matrixNumber(value, digits = 3) {
  if (!finite(value) || (value !== 0 && Math.abs(value) < 10 ** -digits))
    return numberCell(value, digits);
  const [whole, fraction] = fmt(value, digits).split('.');
  return `<span class="matrix-number" title="原始值 ${value}"><span class="number-whole">${whole}</span>${fraction ? `<span class="number-fraction">.${fraction}</span>` : ''}</span>`;
}
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
function outletMatrixHtml(sections, unit) {
  const flowTitle = unit === 'kmol/h' ? '摩尔流量' : '标方流量';
  const cols = sections.map(() => '<col class="matrix-percent-col"><col class="matrix-percent-col"><col class="matrix-flow-col">').join('');
  const groupHeaders = sections.map((section) => `<th scope="colgroup" colspan="3" class="${section.key === 'rsc' ? 'rsc' : 'chamber'}"><div class="matrix-outlet-heading"><span class="matrix-outlet-label">${escapeHtml(section.label)}</span><span class="matrix-outlet-temp">${fmt(section.temperature_c,1)}<small>℃</small></span></div></th>`).join('');
  const columnHeaders = sections.map(() => `<th scope="col" class="group-start"><span>干基</span><small class="matrix-column-unit">%</small></th><th scope="col"><span>湿基</span><small class="matrix-column-unit">%</small></th><th scope="col" class="flow-column" title="${flowTitle}" aria-label="${flowTitle} ${escapeHtml(unit)}"><span>流量</span><small class="matrix-column-unit">${escapeHtml(unit)}</small></th>`).join('');
  const body = OUTLET_SPECIES.map((gas) => `<tr class="${gas === 'H2O' ? 'water-row' : ''}"><th scope="row" aria-label="${GAS_LABELS[gas]} ${OUTLET_NAMES[gas]}"><div class="matrix-species"><span class="species-name">${GAS_LABELS[gas]}</span><span class="species-description">${OUTLET_NAMES[gas]}</span></div></th>${sections.map((section) => `<td class="group-start">${gas === 'H2O' ? '<span class="not-applicable" title="干基扣除水蒸气，不计入组成合计">不计</span>' : matrixNumber(section.dry_composition?.[gas])}</td><td>${matrixNumber(section.wet_composition?.[gas])}</td><td class="flow-column">${matrixNumber(outletFlow(section,gas,unit))}</td>`).join('')}</tr>`).join('');
  return `<table class="outlet-matrix${sections.length === 1 ? ' single-outlet' : ''}">
    <caption class="matrix-caption">出口组分及流量对照：干基扣除水蒸气，湿基和气体总流量包含水蒸气；固相灰单独列示。</caption>
    <colgroup><col class="matrix-species-col">${cols}</colgroup>
    <thead><tr class="outlet-column-groups"><th rowspan="2" scope="col" class="matrix-species-heading">组分<small>化学式 / 名称</small></th>${groupHeaders}</tr><tr>${columnHeaders}</tr></thead>
    <tbody>${body}</tbody>
    <tfoot><tr class="gas-total-row"><th scope="row">气体合计</th>${sections.map((section) => `<td class="group-start">${matrixNumber(compositionTotal(section,'dry'))}</td><td>${matrixNumber(compositionTotal(section,'wet'))}</td><td class="flow-column">${matrixNumber(outletTotal(section,unit))}</td>`).join('')}</tr>
    <tr class="ash-row"><th scope="row">固相灰</th>${sections.map((section) => `<td colspan="3" class="group-start"><span class="matrix-mass">${matrixNumber(section.ash_kg_h,2)}<small>kg/h</small></span></td>`).join('')}</tr></tfoot>
  </table>`;
}
function renderOutletMatrix(sections) {
  $('outlet-matrix').innerHTML = outletMatrixHtml(sections, state.flowUnit);
}
function renderOutletChart(sections) {
  const basis = state.outletBasis, keys = OUTLET_SPECIES.filter((g) => basis === 'wet' || g !== 'H2O');
  const labels = keys.map((g) => GAS_LABELS[g]);
  const traces = sections.map((s) => ({
    type:'bar', orientation:'h', name:s.label,
    x:keys.map((g) => finite(s[`${basis}_composition`]?.[g]) ? s[`${basis}_composition`][g] : null), y:labels,
    marker:{color:s.key === 'rsc' ? CHART.cool : CHART.hot, pattern:{shape:s.key === 'rsc' ? '/' : '', fillmode:'overlay', fgcolor:'#ffffff', fgopacity:.45, solidity:.15, size:7}},
    customdata:keys.map((g) => finite(s[`${basis}_composition`]?.[g]) ? String(s[`${basis}_composition`][g]) : '未记录'),
    hovertemplate:'%{customdata}%<extra>%{fullData.name}</extra>',
  }));
  const spec = layout('', '体积分数 / %');
  spec.margin = {l:40,r:16,t:10,b:46};
  spec.barmode = 'group'; spec.bargap = .35; spec.bargroupgap = .12;
  spec.hovermode = 'y unified';
  spec.xaxis = {...spec.xaxis,showgrid:true,gridcolor:CHART.grid,showspikes:false,rangemode:'tozero',tickformat:'.0f'};
  spec.yaxis = {...spec.yaxis,autorange:'reversed',showgrid:false,categoryorder:'array',categoryarray:labels,tickmode:'array',tickvals:labels};
  Plotly.newPlot('plot-outlet-comparison',traces,spec,PLOT_CONFIG);
  chartChrome('plot-outlet-comparison', {
    title:'出口组成对比', summaryText:`${basis === 'dry' ? '干基' : '湿基'}，${keys.length} 种气体`,
    summary:`<span>${keys.length} 种气体 · ${basis === 'dry' ? '干基' : '湿基'}</span>`,
    legend:sections.map((s) => ({name:s.label,color:s.key === 'rsc' ? CHART.cool : CHART.hot,bar:true,pattern:s.key === 'rsc'})),
    pointLabel:'气体组分', note:'同一组分轴 · 真实比例',
    points:keys.map((g) => ({label:GAS_LABELS[g], values:sections.map((s) => ({name:s.label, value:s[`${basis}_composition`]?.[g], unit:'%'}))})),
  });
  document.querySelectorAll('[data-outlet-basis]').forEach((button) => button.setAttribute('aria-pressed',String(button.dataset.outletBasis === basis)));
  $('composition-basis-note').textContent = basis === 'dry' ? '干基扣除水蒸气；微量组分可在逐点读数中核对。' : '湿基包含水蒸气；与下方湿基列一一对应。';
}
function renderOutlets(sections) {
  const host = $('outlet-comparison');
  document.querySelector('.comparison-key').hidden = true;
  if (!sections.length) { host.textContent = '没有可用的出口截面数据，请重新运行模拟。'; return; }
  host.innerHTML = `<div class="outlet-analysis panel">
    <section class="composition-comparison" aria-label="出口组成对比"><div class="data-panel-heading"><h3>组成对比</h3><div class="segmented" role="group" aria-label="组成基准"><button type="button" data-outlet-basis="dry">干基</button><button type="button" data-outlet-basis="wet">湿基</button></div></div><div id="plot-outlet-comparison" class="plot comparison-plot"></div><p id="composition-basis-note" class="chart-note"></p></section>
    <div class="outlet-readouts">${sections.map((s) => `<section class="outlet-readout ${s.key}"><div class="readout-heading"><h3>${escapeHtml(s.label)}<small>第 ${s.cell} 格</small></h3><strong>${fmt(s.temperature_c,1)}<small>℃</small></strong></div><dl><div><dt>干基气量 <small>Nm³/h</small></dt><dd>${numberCell(finite(s.total_dry_nms) ? s.total_dry_nms * 3600 : null,1)}</dd></div><div><dt>有效气量 <small>CO＋H₂ · Nm³/h</small></dt><dd>${numberCell(s.effective_gas_nmh,1)}</dd></div><div><dt>H₂ / CO</dt><dd>${numberCell(s.h2_co_ratio,3)}</dd></div><div><dt>灰质量流量 <small>kg/h</small></dt><dd>${numberCell(s.ash_kg_h,2)}</dd></div></dl></section>`).join('')}</div>
    </div><section class="panel outlet-data-panel"><div class="data-panel-heading"><div><h3>组分与流量明细</h3><p>8 种气体组分<span class="table-meta-divider"></span>同次计算结果</p></div><div class="table-actions"><label for="outlet-flow-unit">流量单位</label><select id="outlet-flow-unit"><option>kmol/h</option><option>Nm³/h</option><option>Nm³/s</option></select><button class="btn btn-outline btn-small" id="download-outlets">下载 CSV</button></div></div><div class="table-wrap" id="outlet-matrix" tabindex="0" role="region" aria-label="出口组分对照表，可横向滚动"></div><p class="table-footnote"><span>— 未记录<span class="table-meta-divider"></span>不计：干基扣除水蒸气</span><span>悬停查看原值 · 下载保留原始精度</span></p></section>`;
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
      color: CHART.hot,
      zones: Object.keys(heat).length > 0,
    });
    plotBar("plot-overview-gas", r.outlet_sections?.at(-1)?.dry_composition || r.syngas_composition || {}, "%", true);
  }
  if (id === "tab-history") {
    plotLine(
      "plot-history-main",
      hist,
      ["SUMFE"],
      "气体组分修正量 (kmol/s)",
      { x: "Iter", log: true },
    );
    plotLine("plot-history-we", hist, ["SUMWE"], "固体流修正量 (kg/s)", {x:"Iter", log:true, color:CHART.teal});
    plotLine("plot-history-x", hist, ["SUMX"], "碳分数修正量", {x:"Iter", log:true, color:CHART.purple});
    plotLine("plot-history-t", hist, ["SUMT"], "温度修正量 (K)", {
      x: "Iter",
      log: true,
      legendSpace: true,
      color: CHART.hot,
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
      color: CHART.hot,
      zones: Object.keys(heat).length > 0,
    });
    plotLine("plot-x", internal, ["X(%)"], "碳转化指标 (%)");
    plotLine("plot-we", internal, ["WE(kg/s)"], "总固体流 (kg/s)", {color:CHART.teal});
    plotLine("plot-u0", internal, ["U0(m/s)"], "气速 (m/s)", {color:CHART.purple});
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
