import feedparser
import json
from datetime import datetime, timedelta
import os
import pytz

# 配置项
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "latest_news.json")
CUTOFF_HOURS = 24  # 保留24小时内的快讯

def get_utc_time():
    return datetime.now(pytz.utc)

def parse_feed(url):
    """抓取并解析单个 RSS 源"""
    feed = feedparser.parse(url)
    entries = []
    cutoff_time = get_utc_time() - timedelta(hours=CUTOFF_HOURS)
    
    for entry in feed.entries:
        # 清洗数据并统一时区
        pub_time = datetime.fromisoformat(entry.published).astimezone(pytz.utc)
        if pub_time < cutoff_time:
            continue
        
        entries.append({
            "id": entry.get("id", entry.link),
            "title": entry.title,
            "content": entry.description,
            "source": url,
            "publish_time": pub_time.isoformat(),
            "link": entry.link
        })
    return entries

def merge_news():
    """合并所有快讯并去重"""
    all_entries = []
    
    with open("feeds.txt", "r") as f:
        urls = [line.strip() for line in f]
    
    for url in urls:
        try:
            all_entries.extend(parse_feed(url))
        except Exception as e:
            print(f"抓取失败: {url}, 错误: {e}")
    
    # 去重逻辑（按id）
    seen = set()
    unique_entries = []
    for entry in all_entries:
        if entry["id"] not in seen:
            seen.add(entry["id"])
            unique_entries.append(entry)
    
    # 保留最近24小时
    cutoff_time = get_utc_time() - timedelta(hours=CUTOFF_HOURS)
    filtered_entries = [
        e for e in unique_entries 
        if datetime.fromisoformat(e["publish_time"]) >= cutoff_time
    ]
    
    # 按时间排序
    filtered_entries.sort(key=lambda x: x["publish_time"], reverse=True)
    
    # 保存为JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump({
            "last_updated": get_utc_time().isoformat(),
            "count": len(filtered_entries),
            "news": filtered_entries
        }, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    merge_news()
