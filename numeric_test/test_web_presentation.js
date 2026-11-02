/* 展示层数值回归：node numeric_test/test_web_presentation.js */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
let plotted;
const context = vm.createContext({
  document: { addEventListener() {} },
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

// 分段着色不能改变60格的温度；交界格仅在两条线中共用。
run(`const profile=Array.from({length:60},(_,i)=>({I:i+1,'T(C)':1200.123-i*7.345}));
     plotLine('temperature',profile,['T(C)'],'温度 (°C)',{zones:true});`);
assert.equal(plotted[1][0].x.length, 30);
assert.equal(plotted[1][1].x.length, 31);
const displayed = [...plotted[1][0].y, ...plotted[1][1].y.slice(1)];
const original = JSON.parse(run("JSON.stringify(profile.map(row=>row['T(C)']))"));
assert.deepEqual(displayed, original);
assert.equal(plotted[1][0].line.shape, "linear");
console.log("Web presentation: numeric precision, missing data, units, CSV and all 60 chart points passed.");
