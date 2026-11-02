"""晋华炉目标温度设计：外层高度搜索，内层仍使用原 DMAT 能量/组分方程。"""
import io
import json
import math


def search_height(evaluate, target, initial, lower, upper, tolerance=0.5, max_evaluations=18):
    """有界扩展 + 保守割线搜索；仅接受内层收敛且温差满足容差的候选。"""
    samples = []

    def sample(height):
        row = dict(evaluate(height))
        row["height_m"] = height
        samples.append(row)
        if not math.isfinite(row["temperature_c"]):
            raise ValueError("废锅设计计算得到非有限温度")
        return row["temperature_c"] - target

    def finish(success, message):
        return {"success": success, "message": message, "target_temperature_c": target,
                "tolerance_c": tolerance, "height_min_m": lower, "height_max_m": upper,
                "evaluations": len(samples), "trials": samples, **samples[-1]}

    height = min(upper, max(lower, initial))
    error = sample(height)
    bracket = None
    while True:
        if not samples[-1].get("converged", False):
            return finish(False, "候选高度的内层计算未收敛，停止目标温度搜索")
        if abs(error) <= tolerance:
            return finish(True, "目标出口温度已达到，高度、热负荷与产汽量已同步更新")
        if len(samples) >= max_evaluations:
            return finish(False, "已达到高度搜索次数上限，目标出口温度尚未达到")
        if bracket is None:
            next_height = min(upper, height * 1.7) if error > 0 else max(lower, height / 1.7)
            if next_height == height:
                return finish(False, f"在高度范围 {lower:g}–{upper:g} m 内未找到满足目标的解，请调整目标或高度范围")
            previous_height, previous_error = height, error
            height = next_height
            error = sample(height)
            if previous_error * error < 0:
                bracket = sorted([(previous_height, previous_error), (height, error)])
        else:
            (a, fa), (b, fb) = bracket
            secant = a - fa * (b - a) / (fb - fa)
            height = min(b - 0.15 * (b - a), max(a + 0.15 * (b - a), secant))
            error = sample(height)
            bracket = [(a, fa), (height, error)] if fa * error <= 0 else [(height, error), (b, fb)]


def run_target_design(output_file, iterate):
    """每个高度重算全炉；回收热量与蒸汽量始终取同一收敛状态。"""
    from common.common_data import common
    from common.progress import write_progress
    from functions.steam_props import steam_production
    from subroutines.initialization import geometry
    from subroutines.output_results import write_start

    latest_output = None
    count = 0

    def evaluate(height):
        nonlocal latest_output, count
        count += 1
        common.H_RSC = height
        geometry()
        latest_output = io.StringIO()
        label = f"废锅设计第 {count} 轮 · 高度 {height:.3f} m"
        code = iterate(latest_output, trial_label=label)
        q_rsc = sum(common.QKW[common.NZRC + 1:common.NZRE + 1])
        q_wall = sum(common.QKW[common.NZRA:common.NZRC + 1])
        return {"temperature_c": float(common.T[common.NZRE] - 273.15),
                "converged": code == 0, "iterations": common.ITERAT,
                "heat_rsc_mw": float(q_rsc / 1e6),
                "steam_rsc_tph": float(steam_production(q_rsc, common.P_DRUM, common.T_FW) * 3.6),
                "steam_total_tph": float(steam_production(q_rsc + q_wall, common.P_DRUM, common.T_FW) * 3.6)}

    result = search_height(evaluate, common.T_RSC_OUT_C, common.H_RSC,
                           common.H_RSC_MIN, common.H_RSC_MAX)
    result["mode"] = "target_temperature"
    result["temperature_error_c"] = result["temperature_c"] - common.T_RSC_OUT_C
    output_file.write(latest_output.getvalue())
    output_file.write("\n    6. 辐射废锅目标温度设计\n")
    output_file.write(f"      目标出口温度: {common.T_RSC_OUT_C:.3f} C\n")
    output_file.write(f"      计算有效高度: {common.H_RSC:.4f} m\n")
    output_file.write(f"      目标温差: {result['temperature_error_c']:+.4f} C\n")
    output_file.write(f"      设计状态: {result['message']}\n")
    output_file.write("RSC_DESIGN_JSON: " + json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
    if result["success"]:
        write_start(output_file)
    write_progress(common.ITERAT, common.ITMAX,
                   status="completed" if result["success"] else "not_converged",
                   message=result["message"])
    return 0 if result["success"] else 2
