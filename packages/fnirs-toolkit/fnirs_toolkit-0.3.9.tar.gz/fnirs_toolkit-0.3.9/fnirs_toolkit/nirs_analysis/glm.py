# fNIRS GLM 运算，包括构建一级设计矩阵和运行 GLM

import pandas as pd
import numpy as np
from nilearn.glm.first_level import make_first_level_design_matrix, run_glm

def make_task_matrix(events, hb_task_blocks, sfreq=10.0) -> pd.DataFrame:
    """
    基于任务信息和 fNIRS 数据长度，构建用于 GLM 分析的一级设计矩阵。

    参数
    ----------
    events : pd.DataFrame
        任务列表，必须包含 'onset', 'duration', 'trial_type' 三列。
        初始单位假定为“采样点数”(Samples)，函数内会将其转换为“秒”(Seconds)。
    hb_task_blocks : pd.DataFrame
        包含 fNIRS 数据的 DataFrame，主要用于确定时间轴的总长度。
    sfreq : float, default=10.0
        采样率 (Hz)，用于将采样点转换为时间秒数。

    返回
    -------
    X : pd.DataFrame
        生成的设计矩阵 (Design Matrix)。
        行数为时间点，列为回归因子 (Regressor)，包括任务条件、漂移项和截距。
    """
    # 将任务的起始点和持续时间从“采样点”转换为“秒”
    task_events = events.copy()
    task_events["duration"] = task_events["duration"] / sfreq
    task_events["onset"] = task_events["onset"] / sfreq

    # 构造设计矩阵
    n_times = len(hb_task_blocks)
    frame_times = np.arange(n_times) / sfreq
    X = make_first_level_design_matrix(frame_times, task_events, drift_model=None,hrf_model='spm')

    return X


def get_glm_betas(
    hb_task_blocks: pd.DataFrame,
    X: pd.DataFrame,
    Task: list,
    regions: bool = False
) -> dict:
    """
    运行一般线性模型 (GLM) 并提取指定任务的回归系数 Beta 值。

    参数
    ----------
    hb_task_blocks : pd.DataFrame
        预处理后的 fNIRS 浓度数据。
        如果 regions=False，列名应包含 '(oxy)' 或 '(deOxy)'。
        如果 regions=True，列名应为脑区名称。
    X : pd.DataFrame
        任务设计矩阵，通常由 make_task_matrix 生成。
    Task : list
        需要提取 Beta 值的任务名称列表 (如 ['VFT1', 'VFT2'])。
        这些名称必须对应设计矩阵 X 中的列名或顺序。
    regions : bool, default=False
        指示输入数据是否已经是脑区平均数据。
        True: 脑区模式 (ROI)，匹配包含 'oxy'/'deOxy' 的所有列 (如 'rDLPFC(oxy)')
        False: 仅提取包含 'oxy'/'deOxy' 的通道数据。

    返回
    -------
    beta_df : pd.DataFrame
        包含提取结果的 DataFrame。
        - 列 'Channel': 通道或脑区名称。
        - 其他列: 对应 Task 列表中各任务的 Beta 值。
    """
    #  列表去重并保持顺序
    Task = list(dict.fromkeys(Task))

    # 确定通道列名
    if regions:
        channel_cols = [
            col for col in hb_task_blocks.columns 
            if 'oxy' in col or 'deOxy' in col
        ]
    else:
        channel_cols = [
            col for col in hb_task_blocks.columns 
            if 'CH' in col and ('oxy' in col or 'deOxy' in col)
        ]

    # 对齐行数
    n_samples_data = hb_task_blocks.shape[0]
    n_samples_design = X.shape[0]
    if n_samples_data != n_samples_design:
        min_samples = min(n_samples_data, n_samples_design)

        #
        hb_task_blocks = hb_task_blocks.iloc[:min_samples].copy()

        # 截断设计矩阵
        X = X.iloc[:min_samples].copy()

    # 运行 GLM
    labels, glm_estimates = run_glm(
        hb_task_blocks[channel_cols].values, X,
        noise_model='ar1', n_jobs=1
    )

    # 从结果中提取每个通道，每个任务的 beta 值
    n_regressors = X.shape[1]
    n_channels = len(channel_cols)
    full_betas = np.zeros((n_regressors, n_channels))
    unique_labels = np.unique(labels)
    
    for label in unique_labels:
        indices = np.where(labels == label)[0]
        group_betas = glm_estimates[label].theta
        full_betas[:, indices] = group_betas
    
    # 构造结果并返回
    beta_dict = {} 
    beta_dict["Channel"] = channel_cols
    x_columns_list = X.columns.tolist()
    for task in Task:
        # 检查任务是否真的在设计矩阵中
        if task not in x_columns_list:
            raise ValueError(f"Task '{task}' not found in design matrix.")
        col_idx = x_columns_list.index(task)

        # 显式对齐任务范式
        beta_dict[task] = full_betas[col_idx]
    beta_df = pd.DataFrame(beta_dict)
    return(beta_df)
