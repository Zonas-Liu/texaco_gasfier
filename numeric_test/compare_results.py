#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比 Fortran 与 Python 两个案例的 GASTEST.DAT 结果
"""
import re
import os


def parse_gastest(path):
    """解析 GASTEST.DAT，按行号+格式提取关键数据（不依赖中文字符匹配）"""
    with open(path, 'r', encoding='gbk', errors='ignore') as f:
        lines = f.readlines()
    
    data = {}
    
    # 运行条件：按行号解析（Fortran/Python 文件结构一致）
    # 行号从0开始：第2行=水煤浆浓度，第3行=给煤量，第4行=氧煤比，第5行=氧气体积流量，第8行=二次氧气小室号
    try:
        data['coal_ratio'] = float(re.search(r'([\d.]+)\s*%', lines[2]).group(1))
        data['coal_flow'] = float(re.search(r'([\d.]+)\s*KG/S', lines[3]).group(1))
        data['oxy_ratio'] = float(re.search(r'([\d.]+)\s*KG O2', lines[4]).group(1))
        data['oxy_vol'] = float(re.search(r'([\d.]+)\s*NM3/S', lines[5]).group(1))
        m = re.search(r'(\d+)', lines[8])
        if m:
            data['n2fed'] = int(m.group(1))
    except Exception:
        pass
    
    # 收敛迭代：找到 KONVER=0 或 KONVER 0 的那一行
    for line in lines:
        line_strip = line.strip()
        # Fortran: "    64     0    0.3162E-05 ..."
        # Python: "    64        0   3.6225e-06 ..."
        if re.match(r'^\s*\d+\s+0\s+', line_strip):
            parts = line_strip.split()
            data['iter'] = int(parts[0])
            data['sumfe'] = float(parts[2])
            data['sumwe'] = float(parts[3])
            data['sumx'] = float(parts[4])
            data['sumt'] = float(parts[5])
    
    # 干煤气成分、体积流量、出口温度：按最后几行解析（避免中文编码问题）
    # 文件最后几行结构固定：
    #   ...干煤气成分: x x x x x x x
    #   ...体积流量: x x x x x x x
    #   ...出口温度: T C ...碳转化率: x
    if len(lines) >= 4:
        # 干煤气成分（倒数第4行，跳过可能的空行）
        for idx in [-4, -5, -6]:
            if abs(idx) <= len(lines):
                line = lines[idx]
                if ':' in line:
                    parts = line.split(':', 1)[1].split()
                    if len(parts) >= 7:
                        try:
                            data['dry_gas'] = [float(p) for p in parts[:7]]
                            break
                        except ValueError:
                            pass
        # 体积流量（倒数第3行）
        for idx in [-3, -4, -5]:
            if abs(idx) <= len(lines):
                line = lines[idx]
                if ':' in line:
                    parts = line.split(':', 1)[1].split()
                    if len(parts) >= 7:
                        try:
                            data['vol_flow'] = [float(p) for p in parts[:7]]
                            break
                        except ValueError:
                            pass
        # 出口温度和碳转化率（最后一行或倒数第二行）
        for idx in [-1, -2]:
            if abs(idx) <= len(lines):
                line = lines[idx]
                nums = re.findall(r'[\d.]+', line)
                if len(nums) >= 2:
                    # 第一个数字是出口温度，最后一个是碳转化率
                    data['out_temp'] = float(nums[0])
                    data['conv'] = float(nums[-1])
                    break
                elif len(nums) == 1:
                    data['conv'] = float(nums[0])
    
    return data


def main():
    files = {
        'Fortran Case1': 'fortran_output/case1_GASTEST.DAT',
        'Python Case1': 'python_output/case1_GASTEST.DAT',
        'Fortran Case2': 'fortran_output/case2_GASTEST.DAT',
        'Python Case2': 'python_output/case2_GASTEST.DAT',
    }
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results = {}
    for k, v in files.items():
        results[k] = parse_gastest(os.path.join(base_dir, v))
    
    # 同时输出到文件（UTF-8）和屏幕
    output_path = os.path.join(base_dir, 'comparison_summary.txt')
    f_out = open(output_path, 'w', encoding='utf-8')
    
    def write_line(s=''):
        print(s)
        f_out.write(s + '\n')
    
    write_line('=' * 100)
    write_line('TEXACO 气化炉数值测试对比')
    write_line('=' * 100)
    write_line()
    
    write_line('【运行条件】')
    write_line(f"{'参数':<25} {'F Case1':>14} {'P Case1':>14} {'F Case2':>14} {'P Case2':>14}")
    write_line('-' * 100)
    for key, label in [('coal_ratio', '水煤浆浓度 (%)'), ('coal_flow', '给煤量 (kg/s)'), 
                       ('oxy_ratio', '氧煤比'), ('oxy_vol', '氧气体积流量 (Nm3/s)'), ('n2fed', '二次氧气小室号')]:
        vals = [results[k].get(key, 'N/A') for k in results]
        write_line(f"{label:<25} {vals[0]:>14} {vals[1]:>14} {vals[2]:>14} {vals[3]:>14}")
    write_line()
    
    write_line('【收敛性】')
    write_line(f"{'指标':<25} {'F Case1':>14} {'P Case1':>14} {'F Case2':>14} {'P Case2':>14}")
    write_line('-' * 100)
    for key, label in [('iter', '收敛迭代次数'), ('sumfe', '最终 SUMFE'), ('sumwe', '最终 SUMWE'),
                       ('sumx', '最终 SUMX'), ('sumt', '最终 SUMT')]:
        vals = [results[k].get(key, 'N/A') for k in results]
        write_line(f"{label:<25} {vals[0]:>14.4e} {vals[1]:>14.4e} {vals[2]:>14.4e} {vals[3]:>14.4e}")
    write_line()
    
    write_line('【出口结果】')
    write_line(f"{'指标':<25} {'F Case1':>14} {'P Case1':>14} {'F Case2':>14} {'P Case2':>14}")
    write_line('-' * 100)
    for key, label in [('out_temp', '出口温度 (°C)'), ('conv', '碳转化率')]:
        vals = [results[k].get(key, 'N/A') for k in results]
        write_line(f"{label:<25} {vals[0]:>14.3f} {vals[1]:>14.3f} {vals[2]:>14.3f} {vals[3]:>14.3f}")
    
    gas_names = ['O2', 'CH4', 'CO', 'CO2', 'H2S', 'H2', 'N2']
    write_line()
    write_line('【干煤气成分 (%)】')
    write_line(f"{'组分':<25} {'F Case1':>14} {'P Case1':>14} {'F Case2':>14} {'P Case2':>14}")
    write_line('-' * 100)
    for i, name in enumerate(gas_names):
        vals = [results[k].get('dry_gas', [0]*7)[i] for k in results]
        write_line(f"{name:<25} {vals[0]:>14.4f} {vals[1]:>14.4f} {vals[2]:>14.4f} {vals[3]:>14.4f}")
    
    write_line()
    write_line('【体积流量 (Nm3/s)】')
    write_line(f"{'组分':<25} {'F Case1':>14} {'P Case1':>14} {'F Case2':>14} {'P Case2':>14}")
    write_line('-' * 100)
    for i, name in enumerate(gas_names):
        vals = [results[k].get('vol_flow', [0]*7)[i] for k in results]
        write_line(f"{name:<25} {vals[0]:>14.4f} {vals[1]:>14.4f} {vals[2]:>14.4f} {vals[3]:>14.4f}")
    
    write_line()
    write_line('【Python 相对 Fortran 的相对误差 (%) - Case 1】')
    write_line(f"{'指标':<25} {'误差':>14}")
    write_line('-' * 45)
    fc1, pc1 = results['Fortran Case1'], results['Python Case1']
    if 'out_temp' in fc1 and 'out_temp' in pc1:
        err = abs(pc1['out_temp'] - fc1['out_temp']) / fc1['out_temp'] * 100
        write_line(f"{'出口温度':<25} {err:>14.4f}")
    if 'dry_gas' in fc1 and 'dry_gas' in pc1:
        for i, name in enumerate(gas_names):
            if fc1['dry_gas'][i] > 1e-6:
                err = abs(pc1['dry_gas'][i] - fc1['dry_gas'][i]) / fc1['dry_gas'][i] * 100
                write_line(f"{name + ' (干气%)':<25} {err:>14.4f}")
    
    write_line()
    write_line('【Python 相对 Fortran 的相对误差 (%) - Case 2】')
    write_line(f"{'指标':<25} {'误差':>14}")
    write_line('-' * 45)
    fc2, pc2 = results['Fortran Case2'], results['Python Case2']
    if 'out_temp' in fc2 and 'out_temp' in pc2:
        err = abs(pc2['out_temp'] - fc2['out_temp']) / fc2['out_temp'] * 100
        write_line(f"{'出口温度':<25} {err:>14.4f}")
    if 'dry_gas' in fc2 and 'dry_gas' in pc2:
        for i, name in enumerate(gas_names):
            if fc2['dry_gas'][i] > 1e-6:
                err = abs(pc2['dry_gas'][i] - fc2['dry_gas'][i]) / fc2['dry_gas'][i] * 100
                write_line(f"{name + ' (干气%)':<25} {err:>14.4f}")
    
    write_line()
    write_line(f'对比摘要已保存到: {output_path}')
    f_out.close()


if __name__ == '__main__':
    main()
