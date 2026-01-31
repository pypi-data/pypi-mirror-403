"""
fNIRS 血氧浓度可视化

- 支持 HBO2 / HbR 时间序列每个通道的数据可视化，以及任务范式 Mark 标记添加
"""

import os
import re
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
from ..utils.helper import get_sfreq

script_dir = os.path.dirname(os.path.abspath(__file__))

matplotlib.use('Agg')

# 设置全局字体为中文可用字体（根据系统选择）
matplotlib.rcParams['font.family'] = 'SimHei'  # Windows：黑体

# 避免负号无法显示
matplotlib.rcParams['axes.unicode_minus'] = False


def channel_plot(
    data: pd.DataFrame, 
    file_name: str, 
    output_path: str, 
    plot_type: str = 'hb',
    title: str = None, 
    output_suffix: str = "", 
    add_task: bool = True,
    time_range: list = None,
    ylim: tuple = None,
    decimate_factor: int = None
):
    """
    可视化血氧或者光密度波形图

    参数
    ----------
    data : pd.DataFrame
        包含 CH 通道数据的 DataFrame，列名应包含 '(oxy)' 或 '(deOxy)'
    file_name : str
        文件或样本标识符，用于输出文件命名
    output_path : str
        图像保存路径
    plot_type: str
        可选 'hb', 'od'，控制绘制内容。默认 'hb'
    title : str, optional
        图像主标题，默认使用 file_name
    mode : str, optional
        可选 'oxy', 'deoxy', 'both'，控制绘制内容。默认 'both'
    path_corrected : bool, optional
        如果为 True，y 轴单位为 'mM'，否则为 'mM·mm'
    add_task : bool, optional
        是否在图中添加任务开始标注（Mark != 0 的点）
    time_range : list or None, optional
        [start_time, end_time]，仅绘制该范围的数据
    ylim : tuple or list, optional  ### UPDATE 2: Add docstring
        (min, max) 用于固定所有子图的 Y 轴范围，例如 (-0.5, 0.5)
    """

    # 根据数据类型选择
    if plot_type == 'hb':
        y_label_text = "ΔConcentration (mM·mm)"
        color_1, color_2 = 'crimson', 'blue' 
        suffix_1, suffix_2 = '(oxy)', '(deOxy)'
    elif plot_type == 'od':
        y_label_text = "Optical Density (OD)"
        color_1, color_2 = 'darkred', 'darkblue' 
    else:
        raise ValueError("plot_type must be 'hb' or 'od'")

    # 获取采样率
    sfreq = get_sfreq(data)

    # 时间过滤
    df_plot = data.copy(deep=False)
    if time_range is not None:
        start_probe = int(time_range[0] * sfreq) + 1
        end_probe = int(time_range[1] * sfreq) + 1
        mask = (df_plot["Probe1"] >= start_probe) & (df_plot["Probe1"] <= end_probe)
        df_plot = df_plot.loc[mask]

    # 降采样以进行提速
    n_points = len(df_plot)
    if decimate_factor is None:
        if n_points > 5000: decimate_factor = 10
        elif n_points > 2000: decimate_factor = 5
        else: decimate_factor = 1
    idx_slice = slice(None, None, decimate_factor)

    # 提取 x 轴数据
    x_data = df_plot["Probe1"].values[idx_slice]

    # 准备任务标记点
    task_points = []
    if add_task and 'Mark' in df_plot.columns:
        marks = df_plot['Mark'].astype(str).values
        mask = marks != "0"
        if np.any(mask):
            task_points = np.unique(df_plot.loc[mask, 'Probe1'].values)
            if time_range:
                task_points = task_points[(task_points >= start_probe) & (task_points <= end_probe)]
            if len(task_points) > 50: 
                task_points = task_points[:50]

    # 根据数据类型获取成对通道
    paired_channels = []
    if plot_type == 'hb':
        oxy_cols = [c for c in df_plot.columns if '(oxy)' in c]
        for c1 in oxy_cols:
            c2 = c1.replace('(oxy)', '(deOxy)')
            if c2 in df_plot.columns:
                paired_channels.append((c1, c2))
    elif plot_type == 'od':
        pattern = re.compile(r'(CH\d+)\(.*\)')
        groups = {}
        for col in df_plot.columns:
            match = pattern.match(col.strip())
            if match:
                ch_id = match.group(1)
                if ch_id not in groups: groups[ch_id] = []
                groups[ch_id].append(col)

        for ch_id, cols in groups.items():
            if len(cols) == 2:
                cols.sort()
                paired_channels.append(tuple(cols))
        paired_channels.sort(key=lambda x: int(re.search(r'\d+', x[0]).group()))

    if not paired_channels:
        print(f"Warning: No valid {plot_type} channel pairs found.")
        return

    # 开始绘图  
    cols_per_row = 8  # TODO: 自适配通道数量
    n_plots = len(paired_channels)
    rows = (n_plots + cols_per_row - 1) // cols_per_row

    fig, axes = plt.subplots(
        rows, cols_per_row,
        figsize=(4 * cols_per_row, 3 * rows),
        sharex=True, sharey=True
    )

    if n_plots == 1: axes = np.array([axes])
    axes_flat = axes.flatten()
    fig.text(0.5, 0.98, title or f'{file_name} {plot_type.upper()} Waveforms', ha='center', fontsize=16)

    for i, (c1, c2) in enumerate(paired_channels):
        ax = axes_flat[i]
        
        y1 = df_plot[c1].values[idx_slice]
        y2 = df_plot[c2].values[idx_slice]
        
        # 确定标签
        if plot_type == 'hb':
            lbl1, lbl2 = "HbO", "HbR"
        else:
            lbl1 = c1.split('(')[-1].strip(')') + " nm"
            lbl2 = c2.split('(')[-1].strip(')') + " nm"

        # 绘制线条
        ax.plot(x_data, y1, color=color_1, linewidth=1.2, label=lbl1)
        ax.plot(x_data, y2, color=color_2, linewidth=1.2, label=lbl2)

        # 绘制任务标记
        if len(task_points) > 0:
            ax.vlines(
                task_points, 0, 1, 
                transform=ax.get_xaxis_transform(),
                colors='green', linestyles='--', alpha=0.4, linewidth=0.8
            )

        # 设置标题和图例
        ch_name = c1.split('(')[0]
        ax.set_title(ch_name, fontsize=10, pad=2)

        # 只在第一个图展示图例
        if i == 0:
            ax.legend(loc='upper right', fontsize=8, frameon=False)

    axes_flat[0].set_ylabel(y_label_text)

    # 设定统一观察窗
    if ylim is not None:
        axes_flat[0].set_ylim(ylim)

    # 清理不用的子图
    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].axis('off')
    plt.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.03, wspace=0.1, hspace=0.2)

    # 保存图像
    suffix_part = f"_{output_suffix}" if output_suffix else ""
    out_name = f"{file_name}_{plot_type}{suffix_part}.png"
    save_path = os.path.join(output_path, out_name)
    os.makedirs(output_path, exist_ok=True)
    plt.savefig(save_path, dpi=200)
    plt.close(fig)
