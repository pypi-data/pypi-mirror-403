from gc import enable
import io
import time

from PIL import Image
from .config import CONFIG
from loguru import logger


def readable_time(ts):
    """将时间戳转换为可读字符串。"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def is_black_screen(img):
    """判断截图是否为黑屏。"""
    gray_img = img.convert("L")
    pixels = list(gray_img.getdata())
    avg_brightness = sum(pixels) / len(pixels)
    return avg_brightness < 10


def time_count(device, overdue_time=30, judge_interval=0.5, keep_time=3, load_time=1.5, element_enable: bool=False, agora_enable: bool=True):
    """测量播放按钮触发到画面出现的时间。"""
    d = device

    # preview_area = d.xpath('//*[@resource-id="camera"]')
    # play_btn = d.xpath('(//android.widget.Image)[9]')

    if element_enable:
        try:
            preview_area = d.xpath(CONFIG['element']['xpath_preview_area'])            
            preview_bounds = preview_area.get().bounds

            if agora_enable:
                pass
            else:
                play_btn = d.xpath(CONFIG['element']['xpath_play_btn'])
                play_btn.click()
        except Exception as e:
            logger.error("元素定位报错:", e)
    else:
        try:
            preview_bounds = (CONFIG['coords']['preview_area_coord'])
            if agora_enable:
                pass
            else:
                d.click(*CONFIG['coords']['play_btn_coord'])
        except Exception as e:
            logger.error("坐标定位报错：",e)


    start_time = time.time()
    time.sleep(load_time)

    logger.debug(f"点击播放时间为：{readable_time(start_time)}")

    cost_time = None
    n = 0
    time_endline = start_time + overdue_time
    while time.time() < time_endline:
        screenshot_bytes = d.screenshot()
        if isinstance(screenshot_bytes, bytes):
            full_img = Image.open(io.BytesIO(screenshot_bytes))
        else:
            full_img = screenshot_bytes
        preview_img = full_img.crop(preview_bounds)
        n += 1

        if not is_black_screen(preview_img):
            end_time = time.time()
            logger.debug(f"第{n}次截图判断：")
            logger.success(f"出图时间为：{readable_time(end_time)}")
            cost_time = end_time - start_time
            time.sleep(keep_time)
            break

        logger.debug(f"第{n}次截图判断：未出图  {readable_time(time.time())}")
        time.sleep(judge_interval)
        
    return cost_time


def time_statistics(device, count: int, camera_name: str, overdue_time=30, interval=5, judge_interval=0.5, keep_time=3, element_enable:bool=False, load_time=1.5, agora_enable:bool=True):
    """多次执行出图检测并汇总耗时。"""
    d = device
    time_statistic = []

    for i in range(count):
        for _attempt in range(3):
            try:
                if element_enable:
                    d.xpath(f'//*[@text="{camera_name}"]/../following-sibling::*[1]').click()
                    logger.debug("进入预览界面成功")
                else:
                    device_entry_coord = CONFIG['coords']['device_entry_coord']
                    d.click(*device_entry_coord)
                    logger.debug("点击进入预览界面:",device_entry_coord)
                    # time.sleep(load_time)
                break
            except Exception as e:
                logger.error("进入预览界面失败:",e)
                logger.info("请尝试切换元素/坐标定位方式")

        time_track = time_count(device=d, overdue_time=overdue_time, judge_interval=judge_interval, keep_time=keep_time, load_time=load_time, element_enable=element_enable, agora_enable=agora_enable)
        if time_track:
            logger.success(f"第{i + 1}次测试耗时：{time_track:.2f}秒")
        else:
            logger.warning(f"第{i + 1}次测试耗时：超过{overdue_time}秒未出图")
        time_statistic.append(time_track)
        d.press("back")
        time.sleep(interval)

    return time_statistic
