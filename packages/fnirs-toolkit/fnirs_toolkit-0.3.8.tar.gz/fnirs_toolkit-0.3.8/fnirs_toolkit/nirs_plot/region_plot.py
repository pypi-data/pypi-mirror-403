def hb_region_plot(region_df, file_name, output_path, title=None, mode='oxy', path_corrected=False, ylim=None):
    """
    可视化脑区的 HbO2 / HbR 波形均值

    参数
    ----------
    region_df : pd.DataFrame
        宽格式脑区数据（列为脑区名，行为时间点，需包含 'Probe1'）
    file_name : str
        文件名或样本标识符
    output_path : str
        图片保存目录
    title : str, optional
        图像主标题。若不指定，则使用 file_name
    mode : str, optional
        'oxy', 'deOxy', or 'both'，控制绘制的类型
    path_corrected : bool, optional
        决定 y 轴单位是 'mM' 还是 'mM·mm'
    ylim : tuple, optional
        y 轴范围
    """
    if mode not in ['oxy', 'deOxy', 'both']:
        raise ValueError("mode 必须为 'oxy'、'deOxy' 或 'both'")

    os.makedirs(output_path, exist_ok=True)
    unit = "mM" if path_corrected else "mM·mm"
    ylabel = f"ΔConcentration ({unit})"

    # 准备数据
    time_col = 'Probe1'
    value_cols = [col for col in region_df.columns if col != time_col]

    # 转换为长格式
    df_long = region_df.melt(id_vars=time_col, var_name="Region", value_name="Value")

    # 绘图
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df_long, x=time_col, y="Value", hue="Region", linewidth=1.5)

    plt.title(title or f"{file_name} Region-level Hb {mode}", fontsize=16)
    plt.xlabel("Time Point")
    plt.ylabel(ylabel)
    if ylim is not None:
        plt.ylim(ylim)

    plt.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # 保存图像
    output_file_path = os.path.join(output_path, f"{file_name}_region_{mode}.png")
    plt.savefig(output_file_path, dpi=300, bbox_inches='tight')
    plt.close()