import re
from typing import List, Tuple
import pandas as pd
from mne.preprocessing.nirs import temporal_derivative_distribution_repair
import mne


def od_df_to_raw_od(
    od_df: pd.DataFrame, 
    sfreq: float, 
    wavelengths=(690, 830)
) -> Tuple[mne.io.RawArray, List[str]]:
    """
    将 OD DataFrame (含 CHxx(λ) 列) 转成 MNE 的 Raw(fnirs_od)。

    - 识别所有以 'CH' 开头、括号内带数字的列，例如 CH27(690)、CH27(830nm)
    - 通道名映射为 'S1_D{ch_id} {wl}'，同时在 info["chs"][i]["loc"][9] 写入 wl
    """

    ch_cols: List[str] = []
    ch_ids: List[int] = []
    wls: List[int] = []

    for col in od_df.columns:
        col_str = str(col)
        if not col_str.startswith("CH"):
            continue

        # 抽取通道号：CH27(690nm) -> 27
        m_id = re.match(r"^CH(\d+)\(", col_str)
        if not m_id:
            continue
        ch_id = int(m_id.group(1))

        # 抽取波长：CH27(690nm) -> 690
        m_wl = re.search(r"\((\d+)", col_str)
        if not m_wl:
            continue
        wl = int(m_wl.group(1))

        ch_cols.append(col_str)
        ch_ids.append(ch_id)
        wls.append(wl)

    if not ch_cols:
        raise ValueError("❌ 在 od_df 中没有找到形如 CHxx(λ) 的通道列。")

    # 构造 MNE 期望的通道名：S1_D{ch_id} {wl}
    mapped_names: List[str] = []
    for ch_id, wl in zip(ch_ids, wls):
        s = 1      # 你现在没有 source / detector 的真实信息，就统一用 S1
        d = ch_id  # 用通道号当作 detector id
        mapped_names.append(f"S{s}_D{d} {wl}")

    # 检查波长集合是否符合预期
    uniq_wls = sorted(set(wls))
    exp_wls = sorted(set(wavelengths))
    if uniq_wls != exp_wls:
        print(f"⚠ 检测到的波长集合为 {uniq_wls}，与期望 {exp_wls} 不完全一致，请检查。")

    # 数据：shape (n_channels, n_times)
    data = od_df[ch_cols].to_numpy(dtype=float).T

    info = mne.create_info(
        ch_names=mapped_names,
        sfreq=sfreq,
        ch_types=["fnirs_od"] * len(mapped_names),
    )
    raw_od = mne.io.RawArray(data, info, verbose=False)

    # 在 loc[9] 填写波长 —— 这是 MNE 识别 fNIRS 波长的关键字段
    for idx, wl in enumerate(wls):
        raw_od.info["chs"][idx]["loc"][9] = float(wl)

    return raw_od, ch_cols


def od_tddr(
    od_df: pd.DataFrame,
    sfreq: float,
) -> pd.DataFrame:
    """
    对 OD DataFrame 应用 MNE 官方 TDDR，并返回修复后的 DataFrame。
    - 输入：列名形如 CHxx(690)、CHxx(830)
    - 输出：同样形如 CHxx(λ) 的 DataFrame，只是数值被 TDDR 修复
    """

    raw_od, ch_cols = od_df_to_raw_od(od_df, sfreq=sfreq)

    # 在 OD 上跑 TDDR
    raw_tddr = temporal_derivative_distribution_repair(raw_od, verbose=False)

    repaired = od_df.copy()
    repaired[ch_cols] = raw_tddr.get_data().T

    return repaired
