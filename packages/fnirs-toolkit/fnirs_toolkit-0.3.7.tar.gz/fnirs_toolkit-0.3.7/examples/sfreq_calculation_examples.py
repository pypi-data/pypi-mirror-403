import pandas as pd
from fnirs_toolkit.utils.helper import get_sfreq, detect_time_discontinuities

# 示例1: 正常连续数据
df_normal = pd.DataFrame({
    'Time': ['00:00:00.000', '00:00:00.100', '00:00:00.200', '00:00:00.300'],
    'CH1(690)': [1, 2, 3, 4]
})

# 示例2: 包含中断的数据
df_interrupted = pd.DataFrame({
    'Time': ['00:00:00.000', '00:00:00.100', '00:00:00.200',  # 正常
             '00:05:00.000', '00:05:00.100', '00:05:00.200'],  # 中断后重新开始
    'CH1(690)': [1, 2, 3, 4, 5, 6]
})

# 不同方法计算采样率
print("正常数据:")
print(f"前100个样本法: {get_sfreq(df_normal, method='first_n', n_samples=3):.2f} Hz")
print(f"中位数差值法: {get_sfreq(df_normal, method='median_diff'):.2f} Hz")
print(f"稳健估计法: {get_sfreq(df_normal, method='robust'):.2f} Hz")

print("\n中断数据:")
print(f"前100个样本法: {get_sfreq(df_interrupted, method='first_n', n_samples=3):.2f} Hz")
print(f"中位数差值法: {get_sfreq(df_interrupted, method='median_diff'):.2f} Hz")
print(f"稳健估计法: {get_sfreq(df_interrupted, method='robust'):.2f} Hz")

# 检测时间不连续点
discontinuities = detect_time_discontinuities(df_interrupted)
print(f"\n检测到的不连续点: {discontinuities}")