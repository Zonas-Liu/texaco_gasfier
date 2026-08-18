/* TEXACO 纯 HTML 前端交互脚本 */

const OUTPUT_LABELS = {
    Iter: "迭代次数",
    KONVER: "收敛标志",
    SUMFE: "气体组分残差",
    SUMWE: "固体质量流残差",
    SUMX: "碳转化率残差",
    SUMT: "温度残差",
    I: "格子号",
    "H(m)": "高度 (m)",
    "U0(m/s)": "气体速度 (m/s)",
    "ResidenceTime(s)": "停留时间 (s)",
    "WE(kg/s)": "碳质量流 (kg/s)",
    "T(C)": "温度 (°C)",
    "X(%)": "碳转化率 (%)",
    O2: "氧气 O₂",
    CH4: "甲烷 CH₄",
    CO: "一氧化碳 CO",
    CO2: "二氧化碳 CO₂",
    H2S: "硫化氢 H₂S",
    H2: "氢气 H₂",
    N2: "氮气 N₂",
    H2O: "水蒸气 H₂O",
};

const GAS_COLORS = {
    O2: "#E45756",
    CH4: "#F58518",
    CO: "#72B7B2",
    CO2: "#54A24B",
    H2S: "#B279A2",
    H2: "#4C78A8",
    N2: "#79706E",
    H2O: "#D67195",
};

const COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"];

let paramInfo = {};
let paramGroups = [];
let isPolling = false;

// ---------------------------------------------------------------------------
// 初始化
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    loadParams();

    document.getElementById("btn-save").addEventListener("click", saveParams);
    document.getElementById("btn-run").addEventListener("click", runSimulation);
});

function initTabs() {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
        });
    });
}

function showSidebarMsg(text, type = "info") {
    const el = document.getElementById("sidebar-msg");
    el.className = `msg ${type}`;
    el.textContent = text;
    el.style.display = "block";
}

// ---------------------------------------------------------------------------
// 参数加载与渲染
// ---------------------------------------------------------------------------
async function loadParams() {
    try {
        const res = await fetch("/api/params");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        paramInfo = data.info;
        paramGroups = data.groups;
        renderParamsForm(data);
    } catch (err) {
        showSidebarMsg(`加载参数失败: ${err.message}`, "error");
    }
}

function renderParamsForm(data) {
    const container = document.getElementById("params-form");
    container.innerHTML = "";

    data.groups.forEach((group) => {
        const names = data.grouped[group];
        const fs = document.createElement("div");
        fs.className = "fieldset";
        const legend = document.createElement("legend");
        legend.textContent = `📁 ${group}`;
        fs.appendChild(legend);

        names.forEach((name) => {
            const info = paramInfo[name];
            const val = data.values[name];
            const div = document.createElement("div");
            div.className = "form-group";

            const label = document.createElement("label");
            label.textContent = `${info.cn} (${name})${info.unit ? ` [${info.unit}]` : ""}`;
            label.title = info.desc;
            div.appendChild(label);

            const input = document.createElement("input");
            input.type = "number";
            input.id = `param-${name}`;
            input.step = info.type === "int" ? 1 : decideStep(val);
            input.value = val;
            div.appendChild(input);
            fs.appendChild(div);
        });

        container.appendChild(fs);
    });
}

function decideStep(val) {
    const v = Math.abs(Number(val) || 0);
    if (v <= 1) return 0.001;
    if (v < 100) return 0.01;
    return 1.0;
}

function collectParams() {
    const params = {};
    Object.keys(paramInfo).forEach((name) => {
        const el = document.getElementById(`param-${name}`);
        if (!el) return;
        if (paramInfo[name].type === "int") {
            params[name] = parseInt(el.value, 10);
        } else {
            params[name] = parseFloat(el.value);
        }
    });
    return params;
}

async function saveParams() {
    const params = collectParams();
    try {
        const res = await fetch("/api/params", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(params),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        showSidebarMsg("✅ 输入参数已保存到 data/Datain0.dat", "success");
    } catch (err) {
        showSidebarMsg(`保存失败: ${err.message}`, "error");
    }
}

// ---------------------------------------------------------------------------
// 运行模拟
// ---------------------------------------------------------------------------
async function runSimulation() {
    if (isPolling) return;
    const params = collectParams();

    document.getElementById("btn-run").disabled = true;
    document.getElementById("results-area").style.display = "none";
    document.getElementById("console-area").style.display = "none";
    document.getElementById("progress-card").style.display = "block";
    updateProgress(0, "正在启动模拟...");

    try {
        const res = await fetch("/api/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(params),
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.error || `HTTP ${res.status}`);
        }
        isPolling = true;
        showSidebarMsg("🚀 模拟已启动", "info");
        setTimeout(pollProgress, 300);
    } catch (err) {
        isPolling = false;
        document.getElementById("btn-run").disabled = false;
        updateProgress(0, `启动失败: ${err.message}`);
        showSidebarMsg(`启动失败: ${err.message}`, "error");
    }
}

async function pollProgress() {
    if (!isPolling) return;
    try {
        const res = await fetch("/api/progress");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const pct = Math.min(Number(data.progress) || 0, 1);
        const iter = data.iteration || 0;
        const maxIter = data.max_iterations || 0;
        const residuals = data.residuals || {};
        const residualParts = ["SUMFE", "SUMWE", "SUMX", "SUMT"]
            .map((k) => {
                const v = residuals[k];
                return v !== undefined ? `${k}=${Number(v).toExponential(2)}` : "";
            })
            .filter(Boolean);
        const text = `${data.message || ""} [${iter}/${maxIter}] ${residualParts.join(" | ")}`;
        updateProgress(pct * 100, text);

        if (data.running) {
            setTimeout(pollProgress, 500);
            return;
        }

        isPolling = false;
        document.getElementById("btn-run").disabled = false;

        if (data.returncode !== 0) {
            updateProgress(100, "模拟运行失败");
            showSidebarMsg("❌ 模拟运行失败", "error");
            showConsole(data.stdout + "\n" + data.stderr, true);
            return;
        }

        updateProgress(100, "模拟运行完成");
        showSidebarMsg("✅ 模拟运行完成", "success");
        if (data.stdout || data.stderr) showConsole(data.stdout + "\n" + data.stderr, false);
        await loadResults();
    } catch (err) {
        isPolling = false;
        document.getElementById("btn-run").disabled = false;
        updateProgress(0, `进度查询异常: ${err.message}`);
    }
}

function updateProgress(percent, text) {
    document.getElementById("progress-fill").style.width = `${percent}%`;
    document.getElementById("progress-text").textContent = text;
}

function showConsole(text, isError) {
    const area = document.getElementById("console-area");
    const out = document.getElementById("console-output");
    out.textContent = text || "（无输出）";
    area.style.display = "block";
}

// ---------------------------------------------------------------------------
// 结果加载与展示
// ---------------------------------------------------------------------------
async function loadResults() {
    try {
        const [resResults, resOutput] = await Promise.all([fetch("/api/results"), fetch("/api/output")]);
        if (!resResults.ok) throw new Error("结果尚未就绪");
        const result = await resResults.json();
        showResults(result);

        if (resOutput.ok) {
            const out = await resOutput.json();
            document.getElementById("raw-output").textContent = out.text;
        }
    } catch (err) {
        showSidebarMsg(`加载结果失败: ${err.message}`, "error");
    }
}

function showResults(result) {
    document.getElementById("results-area").style.display = "block";

    // 摘要
    const outlet = result.outlet || {};
    const hist = result.convergence_history || [];
    const lastIter = hist.length ? hist[hist.length - 1].Iter : 0;
    const converged = hist.length && hist[hist.length - 1].KONVER === 0 ? "✅ 已收敛" : "⚠️ 未收敛";
    document.getElementById("summary-grid").innerHTML = [
        { label: "出口温度", value: `${(outlet["Temperature(C)"] || 0).toFixed(2)} °C` },
        { label: "碳转化率", value: `${((outlet.CarbonConversion || 0) * 100).toFixed(2)}%` },
        { label: "收敛迭代", value: `${lastIter} 次` },
        { label: "收敛状态", value: converged },
    ]
        .map(
            (item) => `
        <div class="summary-item">
            <div class="label">${item.label}</div>
            <div class="value">${item.value}</div>
        </div>`
        )
        .join("");

    // 收敛历史
    renderTable(
        "history-table",
        ["Iter", "KONVER", "SUMFE", "SUMWE", "SUMX", "SUMT"],
        hist,
        {
            Iter: (v) => v,
            KONVER: (v) => v,
            SUMFE: (v) => Number(v).toExponential(4),
            SUMWE: (v) => Number(v).toExponential(4),
            SUMX: (v) => Number(v).toExponential(4),
            SUMT: (v) => Number(v).toExponential(4),
        }
    );
    plotHistory(hist);

    // 合成气
    const syngas = result.syngas_composition || {};
    const volume = result.volume_flow || {};
    renderObjectTable("syngas-table", syngas, (v) => Number(v).toFixed(4));
    renderObjectTable("volume-table", volume, (v) => Number(v).toFixed(4));
    plotBar("plot-syngas", syngas, "干煤气成分占比", "体积百分比 (%)");
    plotBar("plot-volume", volume, "各组分干基体积流量", "流量 (Nm³/s)");

    // 湿合成气
    const wet = result.wet_syngas;
    if (wet) {
        document.getElementById("wet-summary").innerHTML =
            `基于最后一个格子湿基气体组成（H₂O = <strong>${(wet.h2o_frac * 100).toFixed(3)}%</strong>）换算，湿基总流量 = ` +
            `<strong>${wet.total_wet_nmh.toFixed(1)} Nm³/h</strong>（${wet.total_wet_nms.toFixed(4)} Nm³/s）`;
        const wetRows = Object.keys(wet.wet_flow_nms).map((k) => ({
            组分: OUTPUT_LABELS[k] || k,
            "湿基流量 (Nm³/s)": wet.wet_flow_nms[k],
            "湿基流量 (Nm³/h)": wet.wet_flow_nmh[k],
            "湿基体积分数 (%)": wet.total_wet_nms > 0 ? (wet.wet_flow_nms[k] / wet.total_wet_nms) * 100 : 0,
        }));
        renderTable("wet-table", ["组分", "湿基流量 (Nm³/s)", "湿基流量 (Nm³/h)", "湿基体积分数 (%)"], wetRows, {
            "湿基流量 (Nm³/s)": (v) => Number(v).toFixed(4),
            "湿基流量 (Nm³/h)": (v) => Number(v).toFixed(2),
            "湿基体积分数 (%)": (v) => Number(v).toFixed(3),
        });
        plotBar("plot-wet", wet.wet_flow_nmh, "湿合成气各组分流量", "流量 (Nm³/h)");
    } else {
        document.getElementById("wet-summary").textContent = "缺少湿基气体分布数据，无法计算湿合成气组成。";
        document.getElementById("wet-table").innerHTML = "";
        document.getElementById("plot-wet").innerHTML = "";
    }

    // 沿炉膛分布
    const internal = result.internal_profile || [];
    const gasProf = result.gas_composition_profile || [];
    renderTable(
        "internal-table",
        ["I", "H(m)", "U0(m/s)", "ResidenceTime(s)", "WE(kg/s)", "T(C)", "X(%)"],
        internal,
        {
            I: (v) => v,
            "H(m)": (v) => Number(v).toFixed(4),
            "U0(m/s)": (v) => Number(v).toFixed(4),
            "ResidenceTime(s)": (v) => Number(v).toFixed(4),
            "WE(kg/s)": (v) => Number(v).toFixed(4),
            "T(C)": (v) => Number(v).toFixed(2),
            "X(%)": (v) => Number(v).toFixed(2),
        }
    );
    plotLine("plot-temp", internal, "I", ["T(C)"], "沿炉膛温度分布", "温度 (°C)");
    plotLine("plot-we", internal, "I", ["WE(kg/s)"], "沿炉膛碳质量流分布", "碳质量流 (kg/s)");
    plotLine("plot-x", internal, "I", ["X(%)"], "沿炉膛碳转化率分布", "碳转化率 (%)");
    plotLine("plot-u0", internal, "I", ["U0(m/s)"], "沿炉膛气体速度分布", "气体速度 (m/s)");

    renderTable(
        "gas-table",
        ["I", "O2", "CH4", "CO", "CO2", "H2S", "H2", "N2", "H2O"],
        gasProf,
        {
            I: (v) => v,
            O2: (v) => Number(v).toFixed(3),
            CH4: (v) => Number(v).toFixed(3),
            CO: (v) => Number(v).toFixed(3),
            CO2: (v) => Number(v).toFixed(3),
            H2S: (v) => Number(v).toFixed(3),
            H2: (v) => Number(v).toFixed(3),
            N2: (v) => Number(v).toFixed(3),
            H2O: (v) => Number(v).toFixed(3),
        }
    );
    plotLine(
        "plot-gas-main",
        gasProf,
        "I",
        ["CO", "CO2", "H2", "CH4"],
        "主要可燃/含碳组分沿炉膛分布",
        "体积百分比 (%)",
        true
    );
    plotLine(
        "plot-gas-other",
        gasProf,
        "I",
        ["O2", "H2O", "N2", "H2S"],
        "其他组分沿炉膛分布",
        "体积百分比 (%)",
        true
    );
}

// ---------------------------------------------------------------------------
// 表格与图表工具
// ---------------------------------------------------------------------------
function renderTable(containerId, columns, rows, formatters = {}) {
    const container = document.getElementById(containerId);
    if (!rows || rows.length === 0) {
        container.innerHTML = "<p>暂无数据</p>";
        return;
    }
    const thead = columns.map((c) => `<th>${OUTPUT_LABELS[c] || c}</th>`).join("");
    const tbody = rows
        .map((row) => {
            const cells = columns
                .map((c) => {
                    const raw = row[c];
                    const fmt = formatters[c];
                    const text = fmt ? fmt(raw) : raw;
                    return `<td>${text}</td>`;
                })
                .join("");
            return `<tr>${cells}</tr>`;
        })
        .join("");
    container.innerHTML = `<table><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>`;
}

function renderObjectTable(containerId, obj, formatter) {
    const container = document.getElementById(containerId);
    const keys = Object.keys(obj);
    if (keys.length === 0) {
        container.innerHTML = "<p>暂无数据</p>";
        return;
    }
    const rows = keys.map((k) => ({ 组分: OUTPUT_LABELS[k] || k, 数值: obj[k] }));
    renderTable(containerId, ["组分", "数值"], rows, { 数值: formatter });
}

function plotLine(containerId, rows, xKey, yKeys, title, yTitle, useColorMap = false) {
    const traces = yKeys.map((k, i) => ({
        x: rows.map((r) => r[xKey]),
        y: rows.map((r) => r[k]),
        mode: "lines+markers",
        name: OUTPUT_LABELS[k] || k,
        line: { width: 2.5, color: useColorMap ? GAS_COLORS[k] || COLOR_PALETTE[i % COLOR_PALETTE.length] : COLOR_PALETTE[i % COLOR_PALETTE.length] },
        marker: { size: 6 },
    }));
    const layout = {
        title: { text: title, font: { size: 16 } },
        xaxis: { title: OUTPUT_LABELS[xKey] || xKey },
        yaxis: { title: yTitle },
        legend: { orientation: "h", yanchor: "bottom", y: 1.02, xanchor: "right", x: 1 },
        hovermode: "x unified",
        template: "plotly_white",
        margin: { l: 60, r: 40, t: 70, b: 60 },
    };
    Plotly.newPlot(containerId, traces, layout, { responsive: true });
}

function plotBar(containerId, dataObj, title, yTitle) {
    const keys = Object.keys(dataObj);
    const values = keys.map((k) => dataObj[k]);
    const colors = keys.map((k) => GAS_COLORS[k]);
    const trace = {
        x: keys.map((k) => OUTPUT_LABELS[k] || k),
        y: values,
        type: "bar",
        marker: { color: colors },
        text: values.map((v) => Number(v).toFixed(4)),
        textposition: "outside",
    };
    const layout = {
        title: { text: title, font: { size: 16 } },
        xaxis: { title: "组分" },
        yaxis: { title: yTitle },
        template: "plotly_white",
        margin: { l: 60, r: 40, t: 70, b: 60 },
    };
    Plotly.newPlot(containerId, [trace], layout, { responsive: true });
}

function plotHistory(hist) {
    if (!hist.length) return;
    const x = hist.map((r) => r.Iter);
    const mainTraces = ["SUMFE", "SUMWE", "SUMX"].map((k, i) => ({
        x,
        y: hist.map((r) => r[k]),
        mode: "lines+markers",
        name: OUTPUT_LABELS[k] || k,
        line: { width: 2.5, color: COLOR_PALETTE[i % COLOR_PALETTE.length] },
        marker: { size: 5 },
    }));
    Plotly.newPlot(
        "plot-history-main",
        mainTraces,
        {
            title: { text: "气体组分 / 固体质量流 / 碳转化率 残差收敛曲线", font: { size: 16 } },
            xaxis: { title: "迭代次数" },
            yaxis: { title: "残差 (log 尺度)", type: "log" },
            legend: { orientation: "h", yanchor: "bottom", y: 1.02, xanchor: "right", x: 1 },
            hovermode: "x unified",
            template: "plotly_white",
            margin: { l: 60, r: 40, t: 70, b: 60 },
        },
        { responsive: true }
    );

    Plotly.newPlot(
        "plot-history-t",
        [
            {
                x,
                y: hist.map((r) => r.SUMT),
                mode: "lines+markers",
                name: OUTPUT_LABELS.SUMT,
                line: { width: 2.5, color: COLOR_PALETTE[3] },
                marker: { size: 5 },
            },
        ],
        {
            title: { text: "温度残差收敛曲线", font: { size: 16 } },
            xaxis: { title: "迭代次数" },
            yaxis: { title: "温度残差" },
            template: "plotly_white",
            margin: { l: 60, r: 40, t: 70, b: 60 },
        },
        { responsive: true }
    );
}
