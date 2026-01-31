"""
计算 fNIRS 任务态统计指标 

- 支持积分值和质心值
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from scipy.stats import kurtosis, skew
from scipy.signal import find_peaks, peak_widths
from typing import Tuple
from ..utils.helper import classify_columns


def get_integral(
    signal: np.ndarray, 
    sfreq: float, 
    time_range: tuple[float, float] | None = None
) -> float:
    """
    计算积分值 (Area Under Curve).
    
    参数
    ----------
    signal: 1D 数组
    sfreq: 采样率
    time_range: (start_time, end_time) 也就是 (t_min, t_max)，单位秒。
      如果是 None，则计算整个 signal 的积分。
      这里的 time 都是相对于 signal[0] 为 0时刻 的相对时间。
    """
    signal = np.asarray(signal)
    if len(signal) == 0: return np.nan
    
    # 确定要计算的切片索引
    if time_range is not None:
        t_start, t_end = time_range
        idx_start = int(t_start * sfreq)
        idx_end = int(t_end * sfreq)
        # 边界保护
        idx_start = max(0, idx_start)
        idx_end = min(len(signal), idx_end)
        
        # 如果范围无效
        if idx_start >= idx_end: return np.nan
        
        y_slice = signal[idx_start:idx_end]
    else:
        # 计算全长
        y_slice = signal

    # 使用梯形法则计算积分 (dx = 1/sfreq)
    auc = np.trapezoid(y_slice, dx=1.0/sfreq)
    return float(auc)


def get_centroid(
    signal: np.ndarray, 
    sfreq: float, 
    time_range: tuple[float, float] | None = None,
    clip_negative: bool = True
) -> float:
    """
    计算时间质心 (Temporal Centroid)：t_c = (∫t*y(t)dt) / (∫y(t)dt)，建议对基线校正后的正半部分计算
                该指标表示“能量”或“激活”在时间轴上集中在哪个位置，可以用来评估激活延迟、持续时间等动态特征。

    """
    signal = np.asarray(signal)
    if len(signal) == 0: return np.nan

    # 确定要计算的切片索引
    if time_range is not None:
        t_start, t_end = time_range
        idx_start = int(t_start * sfreq)
        idx_end = int(t_end * sfreq)
        idx_start = max(0, idx_start)
        idx_end = min(len(signal), idx_end)
        if idx_start >= idx_end: return np.nan

        y_slice = signal[idx_start:idx_end]
    else:
        y_slice = signal

    if clip_negative:
        y_slice = np.clip(y_slice, 0, None)

    # 构建时间轴
    t_axis = np.arange(len(y_slice)) / sfreq 

    # 积分计算
    area_total = np.trapezoid(y_slice, t_axis)
    if np.isclose(area_total, 0.0):
        return np.nan

    area_weighted = np.trapezoid(y_slice * t_axis, t_axis)
    centroid = area_weighted / area_total

    return float(centroid)


def get_fwhm(signal: np.ndarray, sfreq: float) -> float:
    """
    计算半峰全宽 (Full Width at Half Maximum).
    逻辑：找到最大峰，计算其半高处的宽度。
    """
    signal = np.asarray(signal)
    if len(signal) < 3: return np.nan
    peak_idx = np.argmax(signal)
    if signal[peak_idx] <= 0: return np.nan
    try:
        # rel_height=0.5 即半高宽
        widths, _, _, _ = peak_widths(signal, [peak_idx], rel_height=0.5)
        if len(widths) > 0:
            return float(widths[0] / sfreq)
    except:
        pass
    return np.nan

def get_slope(signal: np.ndarray, sfreq: float) -> float:
    """
    计算线性拟合斜率(单位: value/s)
    """
    signal = np.asarray(signal)
    n = len(signal)
    if n < 2: return np.nan
    x = np.arange(n) / sfreq
    try:
        slope, _ = np.polyfit(x, signal, 1)
        return float(slope)
    except:
        return np.nan


def get_statistics(
    df_block: pd.DataFrame, 
    sfreq: float, 
    task_duration: float, 
    include: list[str] = [
        "integral", "centroid", "peak", 
        "slope", "skewness", "kurtosis", "fwhm"
    ]
) -> pd.Series:
    """
    一次性计算多个指标，自动处理不同的时间窗口逻辑。
    
    参数:
        df_block: 包含信号的 DataFrame (通常是一个已经切好的 Block，从 0 秒开始)
        sfreq: 采样率
        task_duration: 任务持续时长（秒）。用于界定积分计算的范围。
        include: 需要计算的指标列表。
    """
    signal_cols = classify_columns(df_block)["signals"]
    results_list = []

    for col in signal_cols:
        full_signal = df_block[col].values
        total_len = len(full_signal)

        # 获取任务期信号
        idx_task_end = int(task_duration * sfreq)
        idx_task_end = min(idx_task_end, total_len)
        task_signal = full_signal[:idx_task_end]

        row_data = {"Channel": col}

        # 用于 Peak指标、Slope分界、FWHM
        if len(full_signal) > 0:
            peak_idx = np.argmax(full_signal) # 找最大值索引
            peak_val = full_signal[peak_idx]
            peak_time = peak_idx / sfreq
        else:
            peak_idx = 0
            peak_val, peak_time = np.nan, np.nan

        # 指标计算

        # Integral (积分) 
        if "integral" in include:
            row_data["Integral"] = get_integral(task_signal, sfreq)

        # Centroid (质心) 
        if "centroid" in include:
            row_data["Centroid"] = get_centroid(full_signal, sfreq, clip_negative=True)

        # Mean (均值) 
        if "mean" in include:
            row_data["Mean"] = float(np.mean(full_signal)) if len(full_signal) > 0 else np.nan

        # Peak (峰值) 
        if "peak" in include:
            row_data["Peak_Val"] = peak_val
            row_data["Peak_Time"] = peak_time
        
        # Slope (斜率) 
        if "slope" in include:
            # Rising Slope: Start -> Global Peak
            if peak_idx > 1:
                y_rise = full_signal[:peak_idx+1]
                row_data["Rising_Slope"] = get_slope(y_rise, sfreq)
            else:
                row_data["Rising_Slope"] = np.nan

            # Falling Slope: Global Peak -> Block End
            if peak_idx < total_len - 1:
                y_fall = full_signal[peak_idx:]
                row_data["Falling_Slope"] = get_slope(y_fall, sfreq)
            else:
                row_data["Falling_Slope"] = np.nan
        
        # FWHM (半峰宽) 
        if "fwhm" in include:
            row_data["FWHM"] = get_fwhm(full_signal, sfreq)

        # 统计矩 (偏度/峰度) 
        if "skewness" in include:
            row_data["Skewness"] = float(skew(full_signal, nan_policy='omit'))
        if "kurtosis" in include:
            row_data["Kurtosis"] = float(kurtosis(full_signal, nan_policy='omit'))

        results_list.append(row_data)

    return pd.DataFrame(results_list)
