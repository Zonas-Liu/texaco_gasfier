# 可复现运行示例

[文档总索引](README.md) · [输入协议](code_reference/05_INPUT_OUTPUT.md) · [验证说明](code_reference/09_VALIDATION_AND_LIMITATIONS.md)

以下Windows命令从仓库根目录运行，使用`.venv`。新实验优先放到独立目录，保留根目录正在展示的结果。

## 1. 安装与最短运行

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe src/main.py
```

最后一条使用`data/Datain0.dat`，在当前工作目录生成GASTEST/START/进度等。`main.py`没有输入文件命令行解析，**不能**依靠`python src/main.py another.dat`切换工况；自定义路径应调用Python的`main(data_path)`，见下一节。

返回码0表示内层收敛且启用的目标通过；2表示未收敛或设计失败；异常为其他非零。普通正算失败也可能写START，重要工况应先复制输入和重启数据再运行。

## 2. 隔离自定义正算：完整可执行示例

把以下Python代码放在仓库根目录临时脚本中，以`.venv\Scripts\python.exe <脚本名>`运行，或在PowerShell用here-string管道给`.venv\Scripts\python.exe -`。示例只写新的实验子目录；计算使用独立进程。

```python
from pathlib import Path
from datetime import datetime
import json
import os
import subprocess
import sys

root = Path.cwd().resolve()
if not (root / 'src/main.py').is_file():
    raise RuntimeError('请从仓库根目录运行')
sys.path.insert(0, str(root))
from web_backend.dataparser import parse_datain0, write_datain0, parse_gastest

case = root / 'numeric_test/python_output' / ('manual-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
case.mkdir(parents=True)
datain = case / 'Datain0.dat'
datain.write_bytes((root / 'data/Datain0.dat').read_bytes())
params = parse_datain0(datain)
params.update(KTRL=1, KMODEL=1, FEED_MODE=0, RSC_MODE=0,
              BSLURRY=14.0, FOXY=0.98, H_RSC=30.0)
write_datain0(datain, params)

driver = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
from main import main
raise SystemExit(main(sys.argv[2]))
'''
with (case / 'run.log').open('w', encoding='utf-8') as log:
    proc = subprocess.run([sys.executable, '-c', driver, str(root), str(datain)],
                          cwd=case, stdout=log, stderr=log,
                          env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
print('输出目录:', case, '退出码:', proc.returncode)
if proc.returncode != 0:
    raise RuntimeError('未通过，查看run.log和simulation_progress.json')
result = parse_gastest(case / 'GASTEST.DAT')
for section in result['outlet_sections']:
    print(section['label'], section['temperature_c'], section['ash_kg_h'])
(case / 'parsed-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
```

`write_datain0`接收Pa绝压/K，不能将MPaG/℃直接传入。典型新物性结果约1232.374℃/791.480℃，仅用于快速辨识工况；正式验收用完整状态与独立账。

## 3. 在独立输入上切换设计模式

替换上述`params.update(...)`，其他运行步骤相同：

```python
params.update(KTRL=1, KMODEL=1,
              FEED_MODE=1, T_CHAMBER_C=1228.0, EFFECTIVE_GAS_NMH=52000.0,
              FOXY=0.98, BSLURRY=14.0,
              FOXY_MIN=0.7, FOXY_MAX=1.3, SLURRY_MIN=5.0, SLURRY_MAX=30.0,
              RSC_MODE=1, T_RSC_OUT_C=780.0,
              H_RSC=30.0, H_RSC_MIN=1.0, H_RSC_MAX=120.0)
```

只求废锅高度时保留FEED_MODE=0；只求进料时保留RSC_MODE=0。有效气量为第30格CO+H₂的Nm³/h。成功结果中的FOXY/煤浆为解，原输入仍是搜索初值，不自动回写。

产汽量由同次壁面热量/IF97焓差求出，不是第三个独立目标。改变P_DRUM/T_FW影响产汽换算，当前有效壁温不随汽包状态自动更新。

## 4. 标准隔离验收

```powershell
.venv\Scripts\python.exe numeric_test/benchmark_solver.py --cases fixed texaco --output numeric_test/python_output/example-models
.venv\Scripts\python.exe numeric_test/check_element_balance.py --cases baseline --output numeric_test/python_output/example-elements
.venv\Scripts\python.exe numeric_test/check_feed_design.py --output numeric_test/python_output/example-feed
```

重复执行会覆盖同名案例，保留证据时改新目录名。benchmark的`state.npz`包含完整COMMON数值状态。其进程退出0不保证每个工况成功，检查summary的returncode。`--cases zero-volatiles`用于元素脚本的XVM=0诊断，目前未通过，不并入成功清单。

## 5. Web与Streamlit

```powershell
.venv\Scripts\python.exe web_backend/app.py
# 或（不要同时启动同目录计算）
.venv\Scripts\streamlit.exe run app.py
```

Web默认http://127.0.0.1:5000，Streamlit默认8501。Web编辑17行协议，Streamlit编辑前11行、保留扩展。界面统一MPaG/℃，文件和API仍为Pa绝压/K。

只读API：

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/params
Invoke-RestMethod http://127.0.0.1:5000/api/results
```

下列命令会改根目录参数/启动根目录计算，仅在明确操作该工况时执行：

```powershell
# 6.5e6 Pa绝压，即6.398675 MPaG；423.15 K即150℃
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/params -ContentType 'application/json' -Body '{"P_DRUM":6500000,"T_FW":423.15}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/run -ContentType 'application/json' -Body '{}'
Invoke-RestMethod http://127.0.0.1:5000/api/progress
```

启动HTTP200仅表示进程启动，需等returncode/最终状态并检查目标。运行中改参/重复启动返回409；JSON根必须对象，空请求不等于`{}`。服务锁不保护其他CLI或Flask进程。

## 6. 修改与提交前检查

```powershell
.venv\Scripts\python.exe scripts/check_docs.py --write-index
.venv\Scripts\python.exe scripts/check_docs.py
.venv\Scripts\python.exe -m unittest discover -s numeric_test -p "test_*.py" -v
git diff --check
git status --short
```

数值模型变化还需相应完整求解、独立守恒与目标失败测试。不要提交虚拟环境、本机日志或大量实验状态，保留命令和精简验收证据。
