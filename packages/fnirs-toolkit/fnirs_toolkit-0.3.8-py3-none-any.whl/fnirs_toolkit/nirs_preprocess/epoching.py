import pandas as pd
import numpy as np
from ..utils.helper import classify_columns


def get_task_mark(df: pd.DataFrame):
    """
    分析 'Mark' 列，提取所有任务事件的起止索引。

    参数
    ----------
    df : pd.DataFrame
        必须包含 'Mark' 列。Mark 列应为字符串类型 (如 '0', 'VFT', '1')。

    返回
    -------
    events_df : pd.DataFrame
        包含以下列的 DataFrame:
        - task_name: 任务名称 (Mark 值)
        - start_idx: 任务开始的行索引 (包含)
        - end_idx:   任务结束的行索引 (不包含，即 Python 切片的 stop)
        - duration:  持续点数 (samples)
    """
    if 'Mark' not in df.columns:
        raise ValueError("DataFrame 中缺少 'Mark' 列")

    # 数据清洗：填充空值，转为字符串
    mask = ~df['Mark'].fillna('0').astype(str).isin(['0', '0.0', 'baseline', 'rest'])

    # 提取所有非零 Mark 的索引和名称
    events = df.loc[mask, ['Mark']].copy()
    events = events.rename(columns={'Mark': 'task_name'})

    # 将原本的 DataFrame 索引变为一列数据
    events['start_idx'] = events.index
    events = events.reset_index(drop=True)

    # 计算结束索引
    events['end_idx'] = events['start_idx'].shift(-1)

    # 处理最后一个事件
    events['end_idx'] = events['end_idx'].fillna(len(df)).astype(int)

    # 计算持续时间 (Duration)
    events['duration'] = events['end_idx'] - events['start_idx']
    return events[['task_name', 'start_idx', 'end_idx', 'duration']]


def cut_task_part(df: pd.DataFrame, start: int, end: int, pre_n: int=0, post_n: int=0):
    """
    根据索引切取数据片段，并包含前后的缓冲段 (Pre/Post)。

    参数
    ----------
    df : pd.DataFrame
        原始数据。
    start : int
        任务本身的开始索引 (from get_task_mark)。
    end : int
        任务本身的结束索引 (from get_task_mark)。
    pre_n : int, default 0
        向前扩充的采样点数 (通常用于基线校正)。
    post_n : int, default 0
        向后扩充的采样点数 (通常用于观察恢复期)。

    返回
    -------
    df_cut : pd.DataFrame
        切片后的新 DataFrame (Copy)。
    """
    # 计算扩充后的起止点
    slice_start = start - pre_n
    slice_end = end + post_n

    # 边界检查和修正
    real_start = max(0, slice_start)
    real_end = min(len(df), slice_end)

    if real_start >= real_end:
        raise ValueError(f"切片无效: start({real_start}) >= end({real_end})")

    # 执行切片
    df_cut = df.iloc[real_start : real_end].copy()
    return df_cut


def baseline_correct(df: pd.DataFrame, pre_n: int) -> pd.DataFrame:
    """
    对 fNIRS 数据块进行基线校正 (Baseline Correction)。
    
    该函数通过计算每个血红蛋白信号通道前 `pre_n` 个采样点的平均值作为基线，
    并从该通道的整个时间序列中减去该基线值 (Delta Concentration)。

    参数
    ----------
    df : pd.DataFrame
        包含 fNIRS 数据的 DataFrame，通常是一个截取好的 Task Block)
    pre_n : int
        用于计算基线的起始采样点数量
    
    返回
    -------
    pd.DataFrame
        基线校正后的新 DataFrame (副本)。
        - 信号列：数值已减去基线。
        - 非信号列 (如 Mark, Time)：保持原样。
    """
    df_copy = df.copy()

    # 提取信号列
    cols_map = classify_columns(df_copy)
    if cols_map["signals"]:
        signal_cols = cols_map["signals"]
    else:
        raise ValueError("未检测到符合命名规则的 CHx(oxy/deOxy) 通道。")

    if pre_n is None or pre_n <= 1 or pre_n > len(df_copy):
        raise ValueError(f"pre_n invalid: {pre_n}, len={len(df_copy)}")

    for c in signal_cols:
        x = pd.to_numeric(df_copy[c], errors="coerce").to_numpy(dtype=float)
        baseline_val = np.nanmean(x[:pre_n])
        df_copy[c] = x - baseline_val

    # 裁剪 pre_n 的数据
    df_result = df_copy.iloc[pre_n:].reset_index(drop=True)
    return df_result
