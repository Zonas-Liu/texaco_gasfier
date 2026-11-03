/* 展示层数值回归：node numeric_test/test_web_presentation.js */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
let plotted;
const context = vm.createContext({
  document: { addEventListener() {}, getElementById() { return null; } },
  Plotly: { newPlot: (...args) => { plotted = args; } },
});
vm.runInContext(fs.readFileSync(path.join(__dirname, "../web/static/js/app.js"), "utf8"), context);
const run = (source) => vm.runInContext(source, context);

// 微量正/负值、真零与缺失值必须分开，显示不修改来源精度。
assert.match(run("numberCell(1.23e-9)"), /10<sup>-9<\/sup>/);
assert.match(run("numberCell(-1.23e-9)"), /-1.23/);
assert.match(run("numberCell(0)"), />0.000</);
assert.match(run("numberCell(null)"), /未记录/);
assert.match(run("numberCell(NaN)"), /未记录/);
assert.match(run("numberCell(1234.567891)"), /原始值 1234.567891/);
assert.equal(run("seriesUnit('SUMFE','修正量（对数）')"), "kmol/s");
assert.equal(run("seriesUnit('T(C)','温度 (°C)')"), "°C");

run(`const sample = {
  label:'燃烧室出口', molar_flow_kmol_h:{CO:123.4567890123},
  volume_flow:{CO:2}, total_wet_nms:3, total_molar_kmol_h:456.7890123,
  ash_kg_h:789.1234,
  dry_composition:{CO:40,H2:40,CO2:19,CH4:.5,N2:.3,H2S:.2,O2:0},
  wet_composition:{CO:32,H2:32,CO2:15.2,CH4:.4,N2:.24,H2S:.16,O2:0,H2O:20}
}; const sourceSnapshot=JSON.stringify(sample);`);
assert.equal(run("outletFlow(sample,'CO','kmol/h')"), 123.4567890123);
assert.equal(run("outletFlow(sample,'CO','Nm³/h')"), 7200);
assert.equal(run("outletFlow(sample,'CO','Nm³/s')"), 2);
assert.equal(run("outletFlow(sample,'CH4','Nm³/h')"), null);
assert.equal(run("outletTotal(sample,'Nm³/h')"), 10800);
assert.ok(Math.abs(run("compositionTotal(sample,'wet')") - 100) < 1e-10);
assert.equal(run("compositionTotal({dry_composition:{CO:20}},'dry')"), null);
const csv = run("outletCsv([sample],'kmol/h')");
assert.ok(csv.includes('"123.4567890123"'));
assert.ok(csv.includes('"灰质量流量 (kg/h)","","","789.1234"'));
assert.ok(csv.includes('"合计","100","100","456.7890123"'));
assert.equal(run("JSON.stringify(sample)===sourceSnapshot"), true);

// 表格的数字分层不能丢失小数或原值；不适用与缺失仍分别表达。
assert.equal(run("matrixNumber(1234.56789).replace(/<[^>]*>/g,'')"), "1,234.568");
assert.match(run("matrixNumber(1234.56789)"), /原始值 1234.56789/);
assert.match(run("matrixNumber(1.2e-9)"), /10<sup>-9<\/sup>/);
assert.match(run("matrixNumber(null)"), /未记录/);
const matrix = run("outletMatrixHtml([sample,{...sample,label:'辐射废锅出口',key:'rsc'}],'kmol/h')");
assert.equal((matrix.match(/class="not-applicable"/g) || []).length, 2);
assert.ok(matrix.includes('一氧化碳'));
assert.ok(matrix.includes('固相灰'));
assert.ok(matrix.includes('aria-label="摩尔流量 kmol/h"'));
assert.ok(run("outletMatrixHtml([sample],'Nm³/h')").includes('aria-label="标方流量 Nm³/h"'));
assert.equal(run("JSON.stringify(sample)===sourceSnapshot"), true);

// 分段着色不能改变60格的温度；交界格仅在两条线中共用。
run(`const profile=Array.from({length:60},(_,i)=>({I:i+1,'T(C)':1200.123-i*7.345}));
     plotLine('temperature',profile,['T(C)'],'温度 (°C)',{zones:true});`);
assert.equal(plotted[1][0].x.length, 30);
assert.equal(plotted[1][1].x.length, 31);
const displayed = [...plotted[1][0].y, ...plotted[1][1].y.slice(1)];
const original = JSON.parse(run("JSON.stringify(profile.map(row=>row['T(C)']))"));
assert.deepEqual(displayed, original);
assert.equal(plotted[1][0].line.shape, "linear");

// 逐点读数与悬浮读数不得把微量值显示成零；对数轴显式断开非正值。
assert.equal(run("chartNumber(0)"), "0.00");
assert.equal(run("chartNumber(1.23e-12)"), "1.230e-12");
assert.equal(run("chartNumber(-1.23e-12)"), "-1.230e-12");
assert.equal(run("chartNumber(null)"), "—");
run(`const convergence=[{Iter:1,SUMFE:12.123456789},{Iter:2,SUMFE:0},{Iter:3,SUMFE:-1e-12},{Iter:4,SUMFE:null},{Iter:5,SUMFE:2.3456789e-14}];
const historyBefore=JSON.stringify(convergence);
plotLine('log-test',convergence,['SUMFE'],'气体组分修正量 (kmol/s)',{x:'Iter',log:true});`);
assert.deepEqual(Array.from(plotted[1][0].y), [12.123456789,null,null,null,2.3456789e-14]);
assert.equal(plotted[1][0].customdata[4], "2.3456789e-14");
assert.equal(plotted[1][0].connectgaps, false);
assert.equal(plotted[1][0].line.simplify, false);
assert.equal(plotted[2].yaxis.type, "log");
assert.equal(run("JSON.stringify(convergence)===historyBefore"), true);

// 组分颜色和线型跨图固定；非有限值以间断表示，不补零、不裁掉网格。
run(`const chemistry=[{I:1,CO:30,H2:20,CO2:10,H2O:40},{I:2,CO:NaN,H2:21,CO2:9,H2O:40},{I:3,CO:31,H2:22,CO2:8,H2O:39}];
plotLine('gas-test',chemistry,['CO','H2','CO2','H2O'],'体积分数 (%)');`);
assert.deepEqual(Array.from(plotted[1][0].y), [30,null,31]);
assert.equal(new Set(plotted[1].map((trace) => trace.line.dash)).size, 4);
assert.equal(new Set(plotted[1].map((trace) => trace.line.color)).size, 4);
const gasCoColor = plotted[1][0].line.color;
run("plotBar('bar-test',{CO:40,H2:35,CO2:20,CH4:1,N2:3,H2S:1,O2:1.23456789e-15},'%',true)");
assert.equal(plotted[1][0].marker.color[0], gasCoColor);
assert.equal(plotted[1][0].x[6], 1.23456789e-15);
assert.equal(plotted[1][0].customdata[6], "1.23456789e-15");
assert.match(plotted[2].annotations[6].text, /e-15/);
run("plotBar('missing-bar',{CO:0},'%',true)");
assert.equal(plotted[1][0].x[0], 0);
assert.equal(plotted[1][0].x[1], null);
assert.equal(plotted[2].annotations[1].text, "—");

// 实际四个收敛图分别传入各自单位，不把不同量纲曲线放在同一轴。
const plotCalls = [];
context.Plotly.newPlot = (...args) => { plotted = args; plotCalls.push(args); };
run(`renderTable = () => {}; state.result={convergence_history:convergence}; renderTab('tab-history');`);
assert.deepEqual(plotCalls.map((call) => call[0]), ['plot-history-main','plot-history-we','plot-history-x','plot-history-t']);
assert.deepEqual(plotCalls.map((call) => call[2].annotations[0].text), ['kmol/s','kg/s','（无量纲）','K']);
assert.ok(plotCalls.every((call) => call[1].length === 1));

// 双出口干湿基切换仍使用原数组；仅新增图案，原值和物种顺序不变。
context.document.querySelectorAll = () => [];
context.document.getElementById = (id) => id === 'composition-basis-note' ? {} : null;
run(`const outlets=[sample,{...sample,key:'rsc',label:'辐射废锅出口'}]; const outletsBefore=JSON.stringify(outlets);
state.outletBasis='dry'; renderOutletChart(outlets);`);
assert.equal(plotted[1][0].x.length, 7);
assert.equal(plotted[1][1].marker.pattern.fillmode, 'overlay');
assert.equal(plotted[1][1].marker.pattern.shape, '/');
run("state.outletBasis='wet'; renderOutletChart(outlets)");
assert.equal(plotted[1][0].x.length, 8);
assert.equal(plotted[1][0].x[7], 20);
assert.equal(run("JSON.stringify(outlets)===outletsBefore"), true);
console.log("Web presentation: precision, units, CSV, 60 raw grid points, log gaps, chart colors and outlet basis passed.");
