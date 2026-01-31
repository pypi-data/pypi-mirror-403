# 功能：根据 Beer-Lambert 定律将 NIRS 光密度数据转换为血红蛋白浓度变化。

import os
from scipy.interpolate import interp1d
import numpy as np
import pandas as pd
from ..utils.helper import get_channel_columns


script_dir = os.path.dirname(os.path.abspath(__file__))
def raw_intensity_to_od(raw_df, base='base10'):
    """
    将指定波长列 (如 CHx(690), CHx(830)) 从光强 (It) 转换为光密度 (OD)。

    Parameters
    ----------
    df : pd.DataFrame
        原始强度数据（单位为 It）
    base: str
        'base10' - log10
        'natural' - ln

    Returns
    -------
    pd.DataFrame
        光密度（OD）DataFrame，其他列保持不变
    """
    ch_cols = get_channel_columns(raw_df)
    od_df = raw_df.copy()

    for col in ch_cols:
        signal = od_df[col].values
        # 使用第一行作为 reference 参考值
        ref = signal[0] 

        # 避免除以零或负值
        signal = np.clip(signal, a_min=1e-8, a_max=None)
        ref = max(ref, 1e-8)

        # 进行对数转换为光密度
        if base == 'base10':
            od_df[col] = -np.log10(signal / ref)
        elif base == 'natural':
            od_df[col] = -np.log(signal / ref)
        else:
            raise ValueError("base must be 'base10' or 'natural'")

    return od_df


def load_absorption(wavelengths, base='base10'):
    """
    根据输入波长加载HBO2和HB的吸收系数。

    Parameters
    ----------
    wavelengths : list 或 array-like
        包含两个波长值的列表或数组，例如 [690, 730]。

    base : str, 可选
        指定对数的底数单位，可为 'base10'（默认）或 'natural'。
        如果为 'natural'，则吸收系数将乘以 ln(10)。

    Returns
    -------
    np.ndarray
        一个 2x2 的 numpy 数组：
        - 第一行包含 wavelengths[0] 对应的 HBO2 和 HB 吸收系数。
        - 第二行包含 wavelengths[1] 对应的 HBO2 和 HB 吸收系数。
    """
    # 数据来源：Matcher, S. J., Elwell, C. E., Cooper, C. E., Cope, M., & Delpy, D. T. (1995). Performance comparison of several published tissue near-infrared spectroscopy algorithms. Analytical biochemistry, 227(1), 54-68.
    # 数据下载来源：https://github.com/fieldtrip/fieldtrip/blob/release/external/artinis/private/Cope_ext_coeff_table.txt#L198
    
    # 从 Cope 提供的吸收系数表中读取数据
    table_path = os.path.join(script_dir, "Cope_ext_coeff_table.txt")
    data = pd.read_csv(table_path, sep='\t', header=None)
    data.columns = ['lambda', 'Hb', 'HbO2', 'Water', 'Cytochrome']

    # 建立插值函数
    table_wavelengths = data['lambda'].values
    hbo2_interp = interp1d(table_wavelengths, data['HbO2'].values, kind='linear', bounds_error=True)
    hb_interp = interp1d(table_wavelengths, data['Hb'].values, kind='linear', bounds_error=True)

    # 检查输入波长是否在支持范围内
    min_wl, max_wl = table_wavelengths.min(), table_wavelengths.max()
    for wl in wavelengths:
        if wl < min_wl or wl > max_wl:
            raise ValueError(f"输入波长 {wl} 超出支持范围：{min_wl}–{max_wl} nm。")

    # 进行插值并构建消光系数结果：
    # [[HBO2{λ1}, HB{λ1}], 
    #  [HBO2{λ2}, HB{λ2}]]
    eps = []
    for wl in wavelengths:
        hbo2 = hbo2_interp(wl)
        hb = hb_interp(wl)
        eps.append([hbo2, hb])

    # 单位转换，从 OD * cm^-1 * mM^-1 转换为 OD * mm^-1 * mM^-1
    eps = np.array(eps) / 10.0  

    if base == 'natural':
        eps *= np.log(10)

    return eps


def od_beerlambert(od_df, wavelengths, base='base10', path_corrected=False, dist=0.03, dpf_corrected=True, dpf=6.0):
    """
    根据 Beer-Lambert 定律将 NIRS 光密度数据转换为血红蛋白浓度变化。
    参考：https://github.com/fieldtrip/fieldtrip/blob/release/external/artinis/ft_nirs_prepare_ODtransformation.m

    Parameters
    ----------
    od_df : pd.DataFrame
        已经从光强转换后的光密度数据，列为不同通道的测量值，列名格式为 CH1(760nm)，命名暂时只适配ZLHK
    wavelengths : list 或 array-like
        包含两个波长（单位：nm），如 [690, 830]。
    base : str, 可选
        转换底数，'base10'（默认）或 'natural'。
    path_corrected : bool, 可选
        是否进行探头距离校正，默认 False。
    dist : float, 可选
        光源与探测器之间的距离（单位：米），默认 0.03 m（3 cm）。
    dpf_corrected : bool, 可选
        是否进行路径长度因子 DPF 校正，默认 True。
    dpf : float, 可选
        Differential Pathlength Factor，默认 6.0。

    Returns
    -------
    pd.DataFrame
        包含氧合与脱氧血红蛋白浓度变化的 DataFrame。
    """
    # 获取单位转换后的吸收系数矩阵，单位：OD * mm^-1 * mM^-1
    eps = load_absorption(wavelengths, base=base)  # shape: 2x2

    # 根据探头距离和 DPF 校正因子，确定校正系数
    if path_corrected and dpf_corrected:
        dist_factors = dpf * dist * 1000  # 单位：mm
    elif dpf_corrected:
        dist_factors = dpf
    else:
        dist_factors = 1

    # 提取消光系数
    eps_HHB_lambda1  = eps[0][1]
    eps_HHB_lambda2  = eps[1][1]
    eps_O2HB_lambda1 = eps[0][0]
    eps_O2HB_lambda2 = eps[1][0]

    # 找通道列
    ch_cols = get_channel_columns(od_df)
    ch_start_idx = od_df.columns.get_loc(ch_cols[0])
    ch_end_idx = od_df.columns.get_loc(ch_cols[-1]) + 1

    ahead_cols = od_df.iloc[:, :ch_start_idx]
    ch_data = od_df[ch_cols]
    last_cols = od_df.iloc[:, ch_end_idx:]

    result_data = []

    for i in range(0, ch_data.shape[1], 2):
        raw_segment = ch_data.iloc[:, i:i+2].values

        v1 = raw_segment[:, 0]
        v2 = raw_segment[:, 1]

        # Beer Lambert Law 转换
        o2hb = (eps_HHB_lambda2 * v1 - eps_HHB_lambda1 * v2) / (eps_HHB_lambda2 * eps_O2HB_lambda1 - eps_HHB_lambda1 * eps_O2HB_lambda2) / dist_factors
        hhb = (eps_O2HB_lambda2 * v1 - eps_O2HB_lambda1 * v2) / (eps_HHB_lambda1 * eps_O2HB_lambda2 - eps_HHB_lambda2 * eps_O2HB_lambda1) / dist_factors

        # 构造 ΔOD / (DPF · L)
        conc_change  = np.vstack([o2hb, hhb]) # shape: 2 x n_time

        # 转置为 n_time x 2
        result_data.append(conc_change.T)

    # 组装结果表格
    hameo_df = pd.DataFrame(np.hstack(result_data), columns=[
        f"CH{ch+1}(oxy)" if j % 2 == 0 else f"CH{ch+1}(deOxy)"
        for ch in range(len(result_data)) for j in range(2)
    ])

    final_df = pd.concat([ahead_cols, hameo_df, last_cols], axis=1)
    return final_df
