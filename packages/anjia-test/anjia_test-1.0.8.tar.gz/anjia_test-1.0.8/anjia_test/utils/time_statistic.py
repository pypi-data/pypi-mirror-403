import csv
import os
from bisect import bisect_right
from datetime import datetime
from typing import List, Optional, Union
from loguru import logger


def format_duration(seconds: Optional[float]) -> str:
    """将秒数格式化为更易读的字符串。"""
    if seconds is None:
        return "不出图"
    if seconds < 0.001:
        return f"{seconds * 1000000:.1f}μs"
    if seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes:.0f}min {remaining_seconds:.1f}s"


def format_stat_duration(seconds: Optional[float]) -> str:
    """统计指标用的耗时格式化。"""
    return "-" if seconds is None else format_duration(seconds)


def calculate_percentile(sorted_values: List[float], percentile: float) -> Optional[float]:
    """计算给定分位数（输入需已排序）。"""
    if not sorted_values:
        return None
    if percentile <= 0:
        return sorted_values[0]
    if percentile >= 100:
        return sorted_values[-1]
    position = (len(sorted_values) - 1) * (percentile / 100)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    return lower_value + (upper_value - lower_value) * (position - lower_index)


def format_range_label(lower: float, upper: Optional[float]) -> str:
    """生成区间展示文案。"""
    lower_str = "0s" if lower <= 0 else format_duration(lower)
    if upper is None:
        return f">={lower_str}"
    upper_str = format_duration(upper)
    return f"{lower_str}~{upper_str}"


def build_default_bucket_edges(overdue_time: int) -> List[float]:
    """生成默认区间分布的边界（秒）。"""
    base_edges = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    edges = [edge for edge in base_edges if edge < overdue_time]
    if overdue_time > 0:
        edges.append(float(overdue_time))
    if not edges:
        edges = base_edges[:]
    return sorted(set(edges))


def build_time_buckets(values: List[float], edges: List[float]) -> List[dict]:
    """根据边界生成区间统计。"""
    if not values:
        return []
    edges_sorted = sorted(set(edges))
    counts = [0] * (len(edges_sorted) + 1)
    for value in values:
        index = bisect_right(edges_sorted, value)
        counts[index] += 1
    total = len(values)
    buckets = []
    lower = 0.0
    for edge, count in zip(edges_sorted, counts[:-1]):
        rate = (count / total) * 100 if total > 0 else 0.0
        buckets.append({"label": format_range_label(lower, edge), "count": count, "rate": rate})
        lower = edge
    last_count = counts[-1]
    last_rate = (last_count / total) * 100 if total > 0 else 0.0
    buckets.append({"label": format_range_label(lower, None), "count": last_count, "rate": last_rate})
    return buckets


def save_time_statistics(
    time_statistics: List[Union[int, float, None]],
    device_name: str,
    file_path: str,
    file_format: str = "txt",
    time_unit: str = "seconds",
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    overdue_time: int = 30,
    weixin_version: Optional[str] = None,
) -> str:
    """保存包含 ``None`` 值的耗时统计结果。"""

    times_in_seconds = []
    for t in time_statistics:
        if t is None:
            times_in_seconds.append(None)
        else:
            if time_unit == "milliseconds":
                times_in_seconds.append(float(t) / 1000)
            else:
                times_in_seconds.append(float(t))

    total_count = len(times_in_seconds)
    none_count = times_in_seconds.count(None)
    valid_count = total_count - none_count
    none_rate = (none_count / total_count) * 100 if total_count > 0 else 0.0
    valid_rate = (valid_count / total_count) * 100 if total_count > 0 else 0.0

    valid_times = [t for t in times_in_seconds if t is not None]
    valid_times_sorted = sorted(valid_times)
    avg_time = sum(valid_times) / valid_count if valid_count > 0 else None
    max_time = max(valid_times) if valid_count > 0 else None
    min_time = min(valid_times) if valid_count > 0 else None
    total_valid_time = sum(valid_times) if valid_count > 0 else None
    median_time = calculate_percentile(valid_times_sorted, 50)
    q1_time = calculate_percentile(valid_times_sorted, 25)
    q3_time = calculate_percentile(valid_times_sorted, 75)
    p90_time = calculate_percentile(valid_times_sorted, 90)
    p95_time = calculate_percentile(valid_times_sorted, 95)
    std_dev = None
    if valid_count > 1 and avg_time is not None:
        variance = sum((value - avg_time) ** 2 for value in valid_times) / valid_count
        std_dev = variance ** 0.5
    bucket_edges = build_default_bucket_edges(overdue_time)
    buckets = build_time_buckets(valid_times, bucket_edges)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name, file_full = os.path.split(file_path)
    file_name, ext = os.path.splitext(file_full)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)

    if file_format == "txt" or ext == ".txt":
        new_file_name = f"{file_name}_{timestamp}.txt"
        file_path = os.path.join(dir_name, new_file_name) if dir_name else new_file_name
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("=== 视频出图耗时统计报告 ===\n")
            f.write(f"测试开始时间：{start_time} \n")
            f.write(f"测试结束时间：{end_time} \n")
            f.write(f"测试设备名称：{device_name} \n")
            f.write(f"微信版本：{weixin_version} \n")
            f.write(f"总测试次数：{total_count} 次\n")
            f.write(f"出图成功次数：{valid_count} 次\n")
            f.write(f"超时{overdue_time}秒不出图次数：{none_count} 次\n")
            f.write(f"超时{overdue_time}秒不出图率：{none_rate:.2f}%\n")
            f.write(f"出图成功率：{valid_rate:.2f}%\n")

            if valid_count > 0:
                f.write(f"有效耗时总计：{format_duration(total_valid_time)}\n")
                f.write(f"有效耗时平均值：{format_duration(avg_time)}\n")
                f.write(f"有效耗时最大值：{format_duration(max_time)}\n")
                f.write(f"有效耗时最小值：{format_duration(min_time)}\n")
                f.write(f"有效耗时中位数：{format_stat_duration(median_time)}\n")
                f.write(
                    f"有效耗时四分位数(Q1/Q3)：{format_stat_duration(q1_time)} / {format_stat_duration(q3_time)}\n"
                )
                f.write(f"有效耗时P90：{format_stat_duration(p90_time)}\n")
                f.write(f"有效耗时P95：{format_stat_duration(p95_time)}\n")
                f.write(f"有效耗时标准差：{format_stat_duration(std_dev)}\n")
            else:
                f.write("无有效出图耗时数据\n")

            if buckets:
                f.write("-" * 50 + "\n")
                f.write("有效耗时区间分布（仅成功样本）\n")
                f.write("区间\t次数\t占比\n")
                for bucket in buckets:
                    f.write(f"{bucket['label']}\t{bucket['count']}\t{bucket['rate']:.2f}%\n")

            f.write("-" * 50 + "\n")
            f.write("序号\t出图状态\t耗时\t原始值（秒）\n")
            f.write("-" * 50 + "\n")

            for idx, t in enumerate(times_in_seconds, 1):
                status = "成功" if t is not None else f"失败（超时{overdue_time}秒不出图）"
                duration_str = format_duration(t)
                raw_value = f"{t:.6f}" if t is not None else "-"
                f.write(f"{idx}\t{status}\t{duration_str}\t\t{raw_value}\n")

        logger.debug(f"纯文本格式统计已保存到：{file_path}")
        return file_path

    elif file_format == "csv" or ext == ".csv":
        new_file_name = f"{file_name}_{timestamp}.csv"
        file_path = os.path.join(dir_name, new_file_name) if dir_name else new_file_name
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["序号", "出图状态", "耗时", "原始值（秒）", "原始值（毫秒）"])

            for idx, t in enumerate(times_in_seconds, 1):
                if t is None:
                    status = f"失败（超时{overdue_time}秒不出图）"
                    duration_str = f"失败（超时{overdue_time}秒不出图）"
                    raw_second = "-"
                    raw_ms = "-"
                else:
                    status = "成功"
                    duration_str = format_duration(t)
                    raw_second = round(t, 6)
                    raw_ms = round(t * 1000, 3)
                writer.writerow([idx, status, duration_str, raw_second, raw_ms])

            writer.writerow([])
            writer.writerow(["统计摘要", "", "", "", ""])
            writer.writerow(["测试开始时间", start_time, "", "", ""])
            writer.writerow(["测试结束时间", end_time, "", "", ""])
            writer.writerow(["测试设备名称", device_name, "", "", ""])
            writer.writerow(["微信版本", weixin_version, "", "",""])
            writer.writerow(["总测试次数", total_count, "", "", ""])
            writer.writerow(["出图成功次数", valid_count, "", "", ""])
            writer.writerow([f"超时{overdue_time}秒不出图次数", none_count, "", "", ""])
            writer.writerow([f"超时{overdue_time}秒不出图率(%)", f"{none_rate:.2f}", "", "", ""])
            writer.writerow(["出图成功率(%)", f"{valid_rate:.2f}", "", "", ""])

            if valid_count > 0:
                writer.writerow(["有效耗时总计", format_duration(total_valid_time), "", "", ""])
                writer.writerow(["有效耗时平均值", format_duration(avg_time), "", "", ""])
                writer.writerow(["有效耗时最大值", format_duration(max_time), "", "", ""])
                writer.writerow(["有效耗时最小值", format_duration(min_time), "", "", ""])
                writer.writerow(["有效耗时中位数", format_stat_duration(median_time), "", "", ""])
                writer.writerow(
                    [
                        "有效耗时四分位数(Q1/Q3)",
                        f"{format_stat_duration(q1_time)}/{format_stat_duration(q3_time)}",
                        "",
                        "",
                        "",
                    ]
                )
                writer.writerow(["有效耗时P90", format_stat_duration(p90_time), "", "", ""])
                writer.writerow(["有效耗时P95", format_stat_duration(p95_time), "", "", ""])
                writer.writerow(["有效耗时标准差", format_stat_duration(std_dev), "", "", ""])

            if buckets:
                writer.writerow([])
                writer.writerow(["有效耗时区间分布（仅成功样本）", "", "", "", ""])
                writer.writerow(["区间", "次数", "占比(%)", "", ""])
                for bucket in buckets:
                    writer.writerow([bucket["label"], bucket["count"], f"{bucket['rate']:.2f}", "", ""])

        logger.debug(f"CSV格式统计已保存到：{file_path}")
        return file_path

    else:
        raise ValueError("file_format 仅支持 'txt' 或 'csv'")
