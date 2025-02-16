import feedparser
import json
import time
import datetime
import os
import requests
from dateutil import parser, tz

def fetch_rss_feed(url):
    """
    抓取 RSS feed, 使用 requests 设置超时.
    """
    try:
        response = requests.get(url, timeout=10)  # 超时设置为 10 秒
        response.raise_for_status()  # 检查 HTTP 状态码
        feed = feedparser.parse(response.content)
        return feed
    except requests.exceptions.RequestException as e:
        print(f"抓取 {url} 失败: {e}")
        return None  # 或者 raise 抛出异常

def process_entry(entry, source_name):
    """
    处理 RSS 条目，添加来源信息，并转换为统一格式。
    """
    published_time = None
    if hasattr(entry, 'published'):
        published_time = parser.parse(entry.published)
    elif hasattr(entry, 'updated'):
        published_time = parser.parse(entry.updated)

    if published_time:
        published_time = published_time.astimezone(tz.gettz('Asia/Shanghai'))  # 转换为东八区时间

    return {
        "title": entry.get('title', ''),
        "link": entry.get('link', ''),
        "summary": entry.get('summary', ''),
        "published": published_time.isoformat() if published_time else None,
        "source": source_name
    }

def main():
    """
    主程序: 抓取、汇总、保存数据
    """
    with open('config.json', 'r') as f:
        config = json.load(f)

    all_entries = []
    for feed_config in config['rss_feeds']:
        feed = fetch_rss_feed(feed_config['url'])
        if feed and feed.entries:
            for entry in feed.entries:
                processed_entry = process_entry(entry, feed_config['name'])
                all_entries.append(processed_entry)

    # 按发布时间排序（可选）
    all_entries.sort(key=lambda x: x['published'] or '', reverse=True)

    # 保存为 JSON Lines 格式, 并且只保留最近几天的数据
    today = datetime.date.today()
    retention_days = config.get('retention_days', 2)
    cutoff_date = today - datetime.timedelta(days=retention_days)

    with open(config['output_file'], 'w', encoding='utf-8') as outfile:
        for entry in all_entries:
            if entry['published']:
                published_date = datetime.datetime.fromisoformat(entry['published']).date()
                if published_date >= cutoff_date:  # 只保留限定日期之后的数据
                    json.dump(entry, outfile, ensure_ascii=False)
                    outfile.write('\n')

    print("数据抓取、汇总、保存完成。")


if __name__ == "__main__":
    main()
