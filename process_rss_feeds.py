import requests
from lxml import etree
from datetime import datetime
import pytz
import json
import os # 导入 os 模块

# 从环境变量中安全地获取 API 密钥
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
YOUR_SITE_URL = os.environ.get("YOUR_SITE_URL")
YOUR_SITE_NAME = os.environ.get("YOUR_SITE_NAME")

def fetch_rss(url):
    """抓取单个RSS源的内容"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content  # 返回字节流
    except requests.exceptions.RequestException as e:
        print(f"抓取失败: {url} - {e}")
        return None

def parse_rss(xml_content):
    """解析单个 RSS 源的内容，返回条目列表"""
    if xml_content is None:
        return []

    try:
        tree = etree.fromstring(xml_content)
        items = tree.xpath("//item")  # 使用 xpath 查找所有 item
        entries = []
        for item in items:
            entry = {}
            entry['title'] = item.xpath("string(./title)")
            #Do not save link   entry['link'] = item.xpath("string(./link)")
            entry['description'] = item.xpath("string(./description)")
            pub_date = item.xpath("string(./pubDate)")  # 获取发布时间字符串
            if pub_date:
                # 尝试解析时间字符串 (根据实际情况修改时间格式)
                try:
                    dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                    # Convert to UTC and format as string
                    utc_timezone = pytz.utc
                    dt_utc = dt.replace(tzinfo=pytz.timezone(dt.tzinfo.zone)).astimezone(utc_timezone) if dt.tzinfo else utc_timezone.localize(dt)
                    entry['published'] = dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC") # Format as string and use UTC
                except ValueError as e:
                    print(f"时间格式不匹配：{e} , 原时间字符串为: {pub_date}")
                    entry['published'] = None
            else:
                entry['published'] = None
            entries.append(entry)
        return entries
    except etree.XMLSyntaxError as e:
        print(f"XML 解析出错: {e}")
        return []

def process_rss_feeds(rss_urls, filename="rss_output.json"):
    """处理多个 RSS 源，并保存为 JSON 格式，不保存 link"""
    all_entries = []
    for url in rss_urls:
        xml_content = fetch_rss(url)
        entries = parse_rss(xml_content)
        all_entries.extend(entries)

    """将条目保存为 JSON 格式"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_entries, f, ensure_ascii=False, indent=2)
        print(f"成功将条目保存到 JSON 文件: {filename}")
    except Exception as e:
        print(f"保存 JSON 文件时出错: {e}")

# 示例用法
rss_urls = [
    "https://rsshub.app/jin10",
    "https://rsshub.app/telegram/channel/Financial_Express",  # 添加更多 RSS 源
]

process_rss_feeds(rss_urls) #  

