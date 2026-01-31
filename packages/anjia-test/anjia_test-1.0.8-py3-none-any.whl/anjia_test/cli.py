from __future__ import annotations

import argparse
from gc import enable
import os
import sys

import uiautomator2 as u2
from datetime import datetime
from .utils.time_count import time_statistics
from .utils.time_statistic import save_time_statistics
from .utils.notify_wx import send_wecom_text_for_file
from .utils.config import CONFIG
from .utils.config import export_default_config
from .utils.config import load_config
from .utils.logger_config import setup_loguru

logger = None


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="anjia-test",
        description="出图耗时统计脚本",
        epilog="示例：anjia-test -c 10 -n '单目摄像头A' -t 30 -f csv -i 5 -j 0.5 -o result/test.txt -w <wecom_webhook>",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-c", "--count", type=int, default=2, help="测试次数")
    parser.add_argument("-n", "--camera_name", type=str, help="摄像头名称")
    parser.add_argument("-t", "--overdue_time", type=float, default=10, help="超时时间")
    parser.add_argument("-f", "--file_format", type=str, default="text", help="文件格式,支持text,csv")
    parser.add_argument("-w", "--wx_webhook", type=str, help="微信webhook地址")
    parser.add_argument("-q", "--quiet", action="store_false", help="是否静默模式,不添加则不限制推送企微通知，添加则不推送")
    parser.add_argument("-s", "--serial", type=str, help="设备序列号")
    parser.add_argument("-i", "--interval", type=float, default=5, help="测试间隔")
    parser.add_argument("-j", "--judge_interval",type=float,default=0.5,help="预览画面判断间隔")
    parser.add_argument("-o", "--output_path", type=str, help="输出路径")
    parser.add_argument("-k", "--keep_time",type=float,default=0,help="保持预览画面时间")
    parser.add_argument("-e", "--element_enable", action="store_true", help="是否启用元素定位")
    parser.add_argument("-C", "--config", type=str, help="指定自定义配置文件路径（默认读取当前目录 anjia_config.yaml）")
    parser.add_argument("-l", "--load_time", type=float, default=1.5, help="从设备列表入口进入后等待时间预览界面加载的时间")
    parser.add_argument("-A", "--agora", action="store_false", help="是否不使用Agora声网服务")
    return parser.parse_args()


def _config_command(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(
        prog="anjia-test config",
        description="导出默认配置文件到当前目录",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="如果配置文件已存在则覆盖",
    )
    args = parser.parse_args(argv)

    try:
        path = export_default_config(force=args.force)
    except FileExistsError as e:
        print(f"❌ 配置文件已存在：{e}")
        print("   如需覆盖请使用：anjia-test config --force")
        raise SystemExit(1)

    print(f"✅ 已导出默认配置文件：{path}")


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "config":
        _config_command(sys.argv[2:])
        return

    args = get_args()

    if args.config:
        try:
            load_config(args.config)
        except (FileNotFoundError, ValueError) as exc:
            print(exc)
            raise SystemExit(1)

    global logger
    logger = setup_loguru(name="anjia-test")

    if args.serial:
        d = u2.connect(args.serial)
    else:
        d = u2.connect()

    # 获取微信版本
    weixin_info = d.app_info("com.tencent.mm")
    weixin_version = weixin_info['versionName']
    logger.info(f"微信版本：{weixin_version}")

    count = args.count
    element_enable = args.element_enable
    if args.camera_name is None:
    
        if element_enable: 
            if CONFIG['element']['camera_name']:
                camera_name = CONFIG['element']['camera_name']
            else:
                try:         
                    # camera_name = d.xpath("(//android.view.View)[19]/*[1]").get_text()
                    camera_name = d.xpath(CONFIG['element']['xpath_first_camera_name']).get_text()
                    logger.info(f"获取第一个摄像头名称成功：{camera_name}")

                except Exception:
                    raise RuntimeError("使用元素定位：获取摄像头名称失败，请通过 -n/--camera_name 手动输入")
        else: 
            if CONFIG['coords']['camera_name']:
                camera_name = CONFIG['coords']['camera_name']
            else:
                raise RuntimeError("使用坐标定位：未设置摄像头名称，请在配置文件中设置，或通过命令行参数 -n/--camera_name 设置")

        
    else:
        camera_name = args.camera_name

    logger.info(f"当前测试的摄像头名称为：{camera_name}")
    
    overdue_time = args.overdue_time
    file_format = args.file_format
    agora_enable = args.agora

    if args.output_path is None:
        output_path = f"result/{camera_name}_time_statistics.txt"
    else:
        output_path = args.output_path
    interval_time = args.interval
    judge_interval = args.judge_interval
    keep_time = args.keep_time
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    load_time = args.load_time
    time_data = time_statistics(device=d, count=count, camera_name=camera_name, overdue_time=overdue_time, interval=interval_time, judge_interval=judge_interval, keep_time=keep_time, element_enable=element_enable, load_time=load_time, agora_enable=agora_enable)
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_file_path = save_time_statistics(
        device_name=camera_name,
        time_statistics=time_data,
        file_path=output_path,
        file_format=file_format,
        start_time=start_time,
        end_time=end_time,
        overdue_time=overdue_time,
        weixin_version=weixin_version
    )

    webhook = os.getenv("WX_WEBHOOK_URL") or args.wx_webhook
    if webhook and args.quiet:
        send_wecom_text_for_file(webhook_url=webhook, file_path=final_file_path)


if __name__ == "__main__":
    main()
