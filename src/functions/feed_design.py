"""燃烧室双目标反算：有界阻尼牛顿法，内层仍为原 Fortran 移植模型。"""
import io
import json
import numpy as np


def search_feed(evaluate, target_temperature, target_flow, initial, lower, upper,
                temperature_tolerance=0.5, flow_relative_tolerance=0.001, max_evaluations=40):
    """以 ln(氧煤比)、ln(水煤浆量) 为变量；有限差分雅可比与回溯控制步长。

    失败时重算当前最佳已收敛候选，保证返回结果和模型状态一致（最多额外一次）。
    达到内层收敛和两个物理量容差才算成功，不以步长趋零判定成功。
    """
    lo, hi = np.log(lower), np.log(upper)
    flow_tolerance = max(1.0, target_flow * flow_relative_tolerance)
    scales = np.array([temperature_tolerance, flow_tolerance])
    target = np.array([target_temperature, target_flow])
    trials = []

    def sample(x):
        oxy, slurry = np.clip(np.exp(x), lower, upper)
        row = dict(evaluate(float(oxy), float(slurry)))
        row.update(oxygen_coal_ratio=float(oxy), slurry_kg_s=float(slurry))
        values = np.array([row['temperature_c'], row['effective_gas_nmh']])
        if not np.all(np.isfinite(values)):
            raise ValueError('燃烧室反算得到非有限温度或气量')
        trials.append(row)
        return row, (values - target) / scales

    x = np.clip(np.log(initial), lo, hi)
    current, residual = sample(x)

    def finish(success, message):
        nonlocal current, residual
        if trials[-1] is not current:
            current, residual = sample(x)
        success = bool(success and current['converged'] and np.max(np.abs(residual)) <= 1)
        return {**current, 'success': success, 'message': message,
                'target_temperature_c': target_temperature, 'target_effective_gas_nmh': target_flow,
                'temperature_tolerance_c': temperature_tolerance, 'flow_tolerance_nmh': flow_tolerance,
                'temperature_error_c': current['temperature_c'] - target_temperature,
                'flow_error_nmh': current['effective_gas_nmh'] - target_flow,
                'evaluations': len(trials), 'trials': trials}

    while True:
        if not current['converged']:
            return finish(False, '初始进料工况未收敛，请调整初值或迭代上限')
        if np.max(np.abs(residual)) <= 1:
            return finish(True, '燃烧室温度与有效气量均已达到目标')
        if len(trials) + 3 > max_evaluations:
            return finish(False, '已达到进料反算次数上限，双目标尚未达到')
        jacobian = np.zeros((2, 2))
        for j in range(2):
            delta = min(0.005, (hi[j] - lo[j]) / 4)
            # 温度已在容差内时向低氧侧求差分；一个方向内层失败时尝试反向。
            direction = 1 if (j == 1 or residual[0] < -1) else -1
            usable = False
            for sign in (direction, -direction):
                probe = x.copy()
                probe[j] += sign * delta
                if probe[j] < lo[j] or probe[j] > hi[j] or probe[j] == x[j]:
                    continue
                if len(trials) >= max_evaluations:
                    break
                row, perturbed = sample(probe)
                if row['converged']:
                    jacobian[:, j] = (perturbed - residual) / (probe[j] - x[j])
                    usable = True
                    break
            if not usable:
                return finish(False, '扰动工况未收敛，无法可靠计算反算方向')
        try:
            step = np.linalg.solve(jacobian, -residual)
        except np.linalg.LinAlgError:
            return finish(False, '目标对进料的响应退化，请调整初值或目标')
        if not np.all(np.isfinite(step)):
            return finish(False, '反算方向无效，请调整初值或目标')
        # 单轮限制氧煤比和负荷变化，降低试算落入非物理解的概率。
        step /= max(1.0, abs(step[0]) / 0.15, abs(step[1]) / 0.30)
        accepted = False
        for damping in (1.0, 0.5, 0.25, 0.125, 0.0625):
            candidate = np.clip(x + damping * step, lo, hi)
            if np.max(np.abs(candidate - x)) < 1e-10 or len(trials) >= max_evaluations:
                break
            row, candidate_residual = sample(candidate)
            if row['converged'] and np.linalg.norm(candidate_residual) < np.linalg.norm(residual):
                x, current, residual = candidate, row, candidate_residual
                accepted = True
                break
        if not accepted:
            return finish(False, '给定范围内未找到改善双目标的进料工况，请调整目标或搜索范围')


def run_feed_design(output_file, data_path, iterate):
    """完整重建每轮进料源项；只有双目标及可选废锅设计全部通过才写 START。"""
    from common.common_data import common
    from common.progress import write_progress
    from subroutines.initialization import eingab
    from subroutines.output_results import write_start
    from functions.rsc_design import run_target_design

    settings = dict(target_temperature=common.T_CHAMBER_C, target_flow=common.EFFECTIVE_GAS_NMH,
                    initial=[common.FOXY, common.BSLURRY],
                    lower=[common.FOXY_MIN, common.SLURRY_MIN], upper=[common.FOXY_MAX, common.SLURRY_MAX])
    latest, header, count = None, None, 0
    converged_states = []

    def outlet():
        return dict(temperature_c=float(common.T[common.NZRC] - 273.15),
                    effective_gas_nmh=float((common.FEMF[3, common.NZRC] + common.FEMF[6, common.NZRC]) * common.VM_NORMAL * 3600))

    def evaluate(oxy, slurry):
        nonlocal latest, header, count
        count += 1
        header = io.StringIO()
        eingab(data_path, header, overrides={'FOXY': oxy, 'BSLURRY': slurry, 'KTRL': 1})
        if converged_states:
            # 仅复用本次反算中最近的已收敛解作初值，进料源项仍全部由 EINGAB 重建。
            # 按负荷缩放气/固流量；最终结果必须重新通过原牛顿收敛判据。
            prior = min(converged_states, key=lambda s: np.linalg.norm(
                np.log([oxy / s['oxy'], slurry / s['slurry']])))
            scale = slurry / prior['slurry']
            common.FEMF[:] = prior['gas'] * scale
            common.WE[:] = prior['solid'] * scale
            common.X[:] = prior['fraction']
            common.T[:] = prior['temperature']
            common.FEM[:] = common.FEMF[1:9].sum(axis=0)
        latest = io.StringIO()
        code = iterate(latest, trial_label=f'燃烧室反算第 {count} 轮 · 氧煤比 {oxy:.4f} · 煤浆 {slurry:.3f} kg/s')
        if code == 0:
            converged_states.append(dict(oxy=oxy, slurry=slurry, gas=common.FEMF.copy(),
                                         solid=common.WE.copy(), fraction=common.X.copy(), temperature=common.T.copy()))
        return {**outlet(), 'converged': code == 0, 'iterations': common.ITERAT}

    result = search_feed(evaluate, **settings)
    rsc_ok = True
    if result['success'] and common.RSC_MODE == 1:
        latest = io.StringIO()
        rsc_ok = run_target_design(latest, iterate, finalize=False) == 0
        # 联算后的最终截面必须仍满足燃烧室双目标。
        result.update(outlet())
        result['temperature_error_c'] = result['temperature_c'] - settings['target_temperature']
        result['flow_error_nmh'] = result['effective_gas_nmh'] - settings['target_flow']
        result['success'] = (abs(result['temperature_error_c']) <= result['temperature_tolerance_c']
                             and abs(result['flow_error_nmh']) <= result['flow_tolerance_nmh'])
        if not result['success']:
            result['message'] = '废锅联算后燃烧室双目标偏离容差，请调整工况'
    result['overall_success'] = bool(result['success'] and rsc_ok)
    result['dry_coal_kg_h'] = float(common.BSMS * 3600)
    result['pure_oxygen_kg_h'] = float(common.FOXY * common.BSWAF * 3600)
    result['bounds'] = {'oxygen_coal_ratio': [common.FOXY_MIN, common.FOXY_MAX],
                        'slurry_kg_s': [common.SLURRY_MIN, common.SLURRY_MAX]}
    output_file.write(header.getvalue() + latest.getvalue())
    output_file.write('\n    燃烧室目标工况反算\n')
    output_file.write(f"      氧煤比: {common.FOXY:.6f} kg O2/kg BSWAF\n")
    output_file.write(f"      水煤浆总进料: {common.BSLURRY:.6f} kg/s\n")
    output_file.write(f"      燃烧室 CO+H2: {result['effective_gas_nmh']:.3f} Nm3/h\n")
    output_file.write(f"      反算状态: {result['message']}\n")
    output_file.write('FEED_DESIGN_JSON: ' + json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
    if result['overall_success']:
        write_start(output_file)
    message = result['message'] if rsc_ok else '燃烧室双目标已达到，但废锅目标温度未达到'
    write_progress(common.ITERAT, common.ITMAX,
                   status='completed' if result['overall_success'] else 'not_converged', message=message)
    return 0 if result['overall_success'] else 2
