# fNIRS 信号滤波（带通滤波器）

import re
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
from functools import partial
from scipy import signal
from ..utils.helper import get_channel_columns, classify_columns

def fnirs_bandpass_filt(data_matrix, fs, hpf = 0.01, lpf=0.2):
    """
    带通滤波
    y: 数组信号
    fs: 采样频率 (默认为 10Hz)
    hpf: 高通截止频率 (默认为 0.01 Hz)
    lpf: 低通截止频率 (默认为 0.2 Hz)
    """

    # 低通滤波 (LPF)
    # FilterOrder = 3
    w_lpf = lpf / (fs / 2)
    b_low, a_low = signal.butter(N=3, Wn=w_lpf, btype='low')

    # 执行双向低通滤波 (零相位偏移)
    ylpf = signal.filtfilt(b_low, a_low, data_matrix, axis=0)

    # 高通滤波 (HPF)
    if hpf != 0:
        w_hpf = hpf / (fs / 2)
        b_high, a_high = signal.butter(N=5, Wn=w_hpf, btype='high')
        y2 = signal.filtfilt(b_high, a_high, ylpf, axis=0)

        # 在低通结果的基础上执行双向高通滤波
        y2 = signal.filtfilt(b_high, a_high, ylpf, axis=0)
    else:
        y2 = ylpf

    return y2


def fnirs_filter(df: pd.DataFrame, sfreq: float, low_cut: float = 0.01, high_cut: float = 0.2) -> pd.DataFrame:
    """
    对 fNIRS 数据中的信号进行带通滤波, 包括光密度和血氧数据。

    Parameters
    ----------
    df : pd.DataFrame
        原始 fNIRS 数据，包括 CHx/CHx 通道，适配光密度和血氧数据。
    sfreq : float
        数据采样率 (Hz)。
    low_cut : float
        高通滤波器截止频率 (Hz)，默认 0.01。
    high_cut : float
        低通滤波器截止频率 (Hz)，默认 0.2。

    Returns
    -------
    pd.DataFrame
        滤波后的 fNIRS 数据（结构与原数据相同）。
    """
    filtered_df = df.copy()

    # 提取通道列（CHx(oxy)/CHx(deOxy)）
    cols_map = classify_columns(filtered_df)
    if cols_map["signals"]:
        signal_cols = cols_map["signals"]
    else:
        raise ValueError("未检测到符合命名规则的 CHx(oxy/deOxy) 通道。")
  
    # 提取数据矩阵
    data_matrix = filtered_df[signal_cols].values.astype(float)

    # 批量执行滤波处理
    filtered_matrix = fnirs_bandpass_filt(data_matrix, sfreq, low_cut, high_cut)
    filtered_df[signal_cols] = filtered_matrix

    return filtered_df
