import re
from typing import Optional
import numpy as np
import pandas as pd
from fractions import Fraction
from datetime import datetime, timedelta
from functools import partial

from scipy.signal import resample_poly
from typing import List, Optional, Tuple, Union
from ..utils.helper import get_channel_columns, classify_columns

def _parse_time_any(s: str) -> datetime:
    s = str(s)
    fmts = ("%H:%M:%S.%f", "%H:%M:%S", "%M:%S.%f", "%M:%S", "%S.%f", "%S")
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # last resort: pandas mixed-format inference
    try:
        return pd.to_datetime(s, format="mixed").to_pydatetime()
    except Exception:
        raise ValueError(f"无法解析时间格式：{s!r}")


def _resample_signals_poly(df:pd.DataFrame, freq_in:int, freq_out:int, n_out:int) -> pd.DataFrame:
    """
    数值信号抗混叠重采样, 适用于：OD 数据、Hb 数据
    """
    # 处理整个矩阵比循环处理单列要快
    resampled_data = resample_poly(df.values, freq_in, freq_out, axis=0)
    # 截断可能多出的尾部点，确保长度对齐
    resampled_data = resampled_data[:n_out]
    return pd.DataFrame(resampled_data, columns=df.columns)


def _resample_categorical_agg(df: pd.DataFrame, n_out: int, agg_func: dict) -> pd.DataFrame:
    """
    分类/离散数据聚合, 适用于：Mark, Time, Probe1, BodyMovement, RemovalMark, PreScan
    将原索引划分到 n_out 个区间，对每个区间应用特定的聚合函数
    """
    # 创建分组索引, 将原数据的 Index 映射到新的 0 ~ n_out-1 的 bins 中
    bins = np.linspace(0, len(df), n_out + 1)
    groups = pd.cut(df.index, bins, right=False, labels=False)
    
    # 处理边界可能产生的 NaN
    if np.isnan(groups[-1]):
        groups[-1] = n_out - 1
        
    # 执行聚合并重置索引
    resampled = df.groupby(groups).agg(agg_func)
    resampled.index = range(len(resampled))

    return resampled


def _get_priority_mark(series: pd.Series) -> str:
    """
    Mark 聚合, 返回窗口内第一个非空、非纯数字的有效 Mark。
    如果没有有效 Mark，返回空字符串。
    """
    # 遍历窗口内的所有值
    for x in series:
        # 转字符串并去空格
        s = str(x).strip()
        
        # 过滤空值, NaN, 0 或者 0.0
        if not s or s.lower() == 'nan' or s.lower() == 'none':
            continue
        if s == '0' or s == '0.0':
            continue
            
        # 找到第一个有效值，直接返回
        return s
        
    # 如果整个窗口全是 0 或 NaN，返回空字符串
    return ""

def fnirs_resample(df: pd.DataFrame, fs_in: float, fs_out: float, device_type: str = "ZLHK") -> pd.DataFrame:
    """
    对 fNIRS 数据进行降采样，自动处理信号抗混叠与 Mark 保护。

    参数
    ----------
    df : pd.DataFrame
        原始数据框，可以是 od 或者 hb 数据
    fs_in : float
        输入采样率
    fs_out : float
        目标采样率

    返回
    -------
    pd.DataFrame
        降采样后的数据框
    """
    # 边界检查
    if abs(fs_in - fs_out) < 1e-6:
        return df.copy()
    if fs_out > fs_in:
        raise ValueError("目标采样率不能大于原始采样率 (暂不支持升采样)")

    # 计算重采样比例
    ratio = Fraction(fs_out / fs_in).limit_denominator(1000)
    up, down = ratio.numerator, ratio.denominator
    n_in = len(df)
    n_out = int(np.ceil(n_in * fs_out / fs_in))

    # 提取列并分类
    cols_map = classify_columns(df, device_type)
    result_parts = []

    # 处理信号列
    if cols_map["signals"]:
        df_sig = df[cols_map["signals"]]
        resampled_sig = _resample_signals_poly(df_sig, up, down, n_out)
        result_parts.append(resampled_sig)

    # 处理非信号列
    # 定义不同列的聚合策略
    agg_strategies = {}
    
    # Mark 列
    for col in cols_map["marks"]:
        agg_strategies[col] = _get_priority_mark
        
    # Meta 列（Probe1, Time, Mark, BodyMovement, RemovalMark, PreScan)
    for col in cols_map["meta"]:
        if "Time" in col:
            agg_strategies[col] = 'first' 
        elif "BodyMovement" in col:
            agg_strategies[col] = 'max'
        else:
            agg_strategies[col] = 'first'

    # 提取需要聚合的列
    cols_to_agg = cols_map["marks"] + cols_map["meta"]
    if cols_to_agg:
        df_meta = df[cols_to_agg]
        resampled_meta = _resample_categorical_agg(df_meta, n_out, agg_strategies)
        result_parts.append(resampled_meta)

    # 合并结果并整理顺序
    df_out = pd.concat(result_parts, axis=1)
    ordered_cols = cols_map["meta"] + cols_map["signals"] + cols_map["marks"]
    ordered_cols = [c for c in ordered_cols if c in df_out.columns]

    return df_out[ordered_cols]

