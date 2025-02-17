import os
import json
import glob
from datetime import datetime, timedelta
import requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")  # 从环境变量安全地获取 API 密钥
YOUR_SITE_URL = os.environ.get("YOUR_SITE_URL")
YOUR_SITE_NAME = os.environ.get("YOUR_SITE_NAME")

def aggregate_rss_data(input_filename= "rss_output.json" ,output_filename="llm_analysis.txt"): #设置入参，设置读取的json文件名称，和输出的文件名称
    """
    读取json文件去重
    然后将内容传给llm
    """
    try:
        with open(input_filename, "r", encoding="utf-8") as f:
            entries = json.load(f)
        print(f"从 {input_filename} 成功加载新闻条目。")
    except FileNotFoundError:
        print(f"文件未找到: {input_filename}")
        return
    except json.JSONDecodeError:
        print(f"JSON 文件解析出错: {input_filename}")
        return
    # 构建发送给LLM的内容 封装到一起
    content = "请对以下财经新闻进行总结、分类、分析和总体评价：\n\n" # prompt
    for entry in entries: # 循环所有的条目
        content += f"标题: {entry.get('title', '无标题')}\n" # 拼接标题
        content += f"描述: {entry.get('description', '无描述')}\n" #描述不能丢
        content += f"发布时间: {entry.get('published', '无时间')}\n"
        content += "---\n" # 分割线
    send_to_llm(OPENROUTER_API_KEY,YOUR_SITE_URL,YOUR_SITE_NAME,content,output_filename) # 函数的参数放到上面 方便调整，和查看

def send_to_llm(OPENROUTER_API_KEY,YOUR_SITE_URL,YOUR_SITE_NAME,content, output_filename):
    """将content发送给大模型"""
    headers = { # 请求头
        "Authorization": f"Bearer {OPENROUTER_API_KEY}", # Bearer key
        "HTTP-Referer": YOUR_SITE_URL, # 网站
        "X-Title": YOUR_SITE_NAME,   # 名字
        "Content-Type": "application/json" #格式
    }

    data = { # 数据
        "model": "deepseek/deepseek-r1:free", # 模型
        "messages": [{"role": "user", "content": content}] # 消息
    }
    try: # 异常处理，如果没有网络 就会500
        response = requests.post( # post请求
            url="https://openrouter.ai/api/v1/chat/completions", # 地址
            headers=headers, # 添加请求头
            data=json.dumps(data, ensure_ascii=False) # 转换为json
        )
        response.raise_for_status() # 如果不是200 就报错
        llm_response = response.json() # 解析为json 方便使用
        llm_text = llm_response["choices"][0]["message"]["content"] #内容

        with open(output_filename, "w",encoding="utf-8") as f: # 写入文件
            f.write(llm_text) # 写入大模型返回的内容
        print(f"大模型分析结果已保存到: {output_filename}") # 提示已经写入
    except requests.exceptions.RequestException as e: # 捕获请求异常
        print(f"调用大模型 API 出错: {e}") # 打印异常
    except (KeyError, TypeError) as e: # 捕获键值异常和类型异常
        print(f"获取大模型数据失败，请检查数据结构: {e}")
    except Exception as e: # 其他类型的异常
        print(f"发生未知错误: {e}")  # 打印异常

if __name__ == "__main__":
    aggregate_rss_data()  # 调用函数
