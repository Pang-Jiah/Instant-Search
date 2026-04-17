import time
import requests
import json
from PySide6.QtWidgets import (
    QApplication, QTextEdit,QTextBrowser
)
import os
# import sys, os
# sys.path.append(os.path.realpath(__file__))
try:
    from . import Image_processing as img
except ImportError:
    import Image_processing as img

def obtain_model_information(config_file="config.json"):
    
    current_file = os.path.abspath(__file__)
    # 获取file1.py所在的目录
    current_dir = os.path.dirname(current_file)
    # 获取项目根目录（folder1的父目录）
    project_root = os.path.dirname(current_dir)
    # 构建file2.json的完整路径
    json_path = os.path.join(project_root, 'config', config_file)

    default_config = {
            "llm_url": "",
            "llm_model": "",
            "api_key": "",
        }

    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # 合并默认配置和已保存的配置
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                return loaded_config
        else:
            print("未找到json file")
    except Exception as e:
        print(f"加载配置文件失败: {e}")

    return default_config
'''
Function list
'''
def vision_acquire_information(messages:str, image_base64:bytes, first_round:bool):
    config = obtain_model_information(config_file="config.json")
    url = config["llm_url"]
    api_key = config["api_key"]
    model = config["llm_model"]
    

    # ========== 基本配置 ==========
    url = url  # Local API address
    # ========== 请求参数 ==========
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+api_key # sjtu key
    }

    # print("message:", messages)
    if first_round == True:
        messages = [{"role": "system", 
                    "content": 
                        [
                        {"type": "text", "text": "你是一个图片信息检索助手, "},
                        ]
                    },
                    {"role": "user", 
                    "content": 
                        [{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        {"type": "text", "text": "请用50以内个词精炼描述一下这幅图片, "},
                        {"type": "text", "text": f"然后回复用户的询问:{messages}"},
                        {"type": "text", "text": f"然后对于这个图片提炼出3个关键词,根据图片信息和 用户信息:{messages} 列出5个最相关的网址并给出网址内容的描述(50个字以内)"},
                        {"type": "text", "text": f"输出的文本用HTML格式 (直接输出不要markdown格式)"}]
                    }]
    else:
        messages = [{"role": "system", 
                    "content": 
                        [
                        {"type": "text", "text": "你是一个图片信息检索助手, "},
                        ]
                    },
                    {"role": "user", 
                    "content": 
                        [{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        {"type": "text", "text": f"回复用户的询问:{messages}"},
                        {"type": "text", "text": f"输出的文本用HTML格式 (直接输出不要markdown格式)"}]
                    }]
    data = {
        "model":model,  #
        "messages": messages,
        "stream": True,  # 启用流式输出
        "do_sample": True,
        "repetition_penalty": 1.00,
        "temperature": 1e-5,
        "top_k": 20,
        "enable_search": True,
        }
    while True:
        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]  # 去掉 'data: ' 前缀
                            if line == '[DONE]':
                                break
                            try:
                                chunk = json.loads(line)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        # print(content, end='', flush=True)
                                        full_response += content
                                        yield content
                            except json.JSONDecodeError:
                                continue
                yield None  # 表示结束
                return full_response
            else:
                print(f"\n请求失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                # 检查是否需要重试
                time.sleep(5)
                continue
        except Exception as e:
            print(f"\n请求异常: {e}")
            yield "⚠ Your API configuration has encountered an error."
            yield None
            time.sleep(5)
            return
            

def acquire_information(messages:str, textbox: QTextEdit):
    config = obtain_model_information(config_file="config.json")
    url = config["llm_url"]
    api_key = config["api_key"]
    model = config["llm_model"]
    
    # ========== 基本配置 ==========
    url = url  # Local API address
    # ========== 请求参数 ==========
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+api_key # sjtu key
    }
    textbox.insertPlainText(f"User: {messages}\nagent:")
    messages = [{"role": "user", "content": f"{messages}"}]
    # print("message:", messages)
    data = {
        "messages": messages,
        "stream": True,  # 启用流式输出
        "do_sample": True,
        "repetition_penalty": 1.00,
        "temperature": 1e-5,
        "top_k": 20,
        "model": model,  # Model name
    }
    while True:
        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]  # 去掉 'data: ' 前缀
                            if line == '[DONE]':
                                break
                            try:
                                chunk = json.loads(line)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        # print(content, end='', flush=True)
                                        textbox.insertPlainText(content)
                                        full_response += content
                                        QApplication.processEvents()
                            except json.JSONDecodeError:
                                continue
                print()  # 换行
                textbox.insertPlainText('\n')
                return full_response
            else:
                print(f"\n请求失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                # 检查是否需要重试
                time.sleep(5)
                continue
        except Exception as e:
            print(f"\n请求异常: {e}")
            time.sleep(5)
            continue


'''
Test function list
'''

def query_stream(messages):
    config = obtain_model_information(config_file="config.json")
    url = config["llm_url"]
    api_key = config["api_key"]
    model = config["llm_model"]
    # ========== 基本配置 ==========
    url = url  # Local API address
    # ========== 请求参数 ==========
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+api_key # sjtu key
    }
    messages = [{"role": "user", "content": f"{messages}"}]
    print("message:", messages)
    data = {
        "messages": messages,
        "stream": True,  # 启用流式输出
        "do_sample": True,
        "repetition_penalty": 1.00,
        "temperature": 1e-5,
        "top_k": 20,
        "model": model,  # Model name
    }
    
    while True:
        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]  # 去掉 'data: ' 前缀
                            if line == '[DONE]':
                                break
                            try:
                                chunk = json.loads(line)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        print(content, end='', flush=True)
                                        full_response += content
                            except json.JSONDecodeError:
                                continue
                print()  # 换行
                return full_response
            else:
                print(f"\n请求失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                # 检查是否需要重试
                time.sleep(5)
                continue
        except Exception as e:
            print(f"\n请求异常: {e}")
            time.sleep(5)
            continue


def picture_input(image_base64:str):
    config = obtain_model_information(config_file="config.json")
    url = config["llm_url"]
    api_key = config["api_key"]
    model = config["llm_model"]
    # ========== 基本配置 ==========
    url = url  # Local API address
    # ========== 请求参数 ==========
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+api_key # sjtu key
    }

    # print("message:", messages)
    messages = [{"role": "user", 
                  "content": 
                    [{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                    {"type": "text", "text": "对于这个图片提炼出3个关键词"}]
                }]
    data = {
        "model": model,  # Model name
        "messages": messages,
        "stream": True,  # 启用流式输出
        "do_sample": True,
        "repetition_penalty": 1.00,
        "temperature": 1e-5,
        "top_k": 20,
        }

    
    while True:
        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]  # 去掉 'data: ' 前缀
                            if line == '[DONE]':
                                break
                            try:
                                chunk = json.loads(line)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        print(content, end='', flush=True)
                                        # textbox.insertPlainText(content)
                                        full_response += content
                                        QApplication.processEvents()
                            except json.JSONDecodeError:
                                continue
                print()  # 换行
                # textbox.insertPlainText('\n')
                return full_response
            else:
                print(f"\n请求失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                # 检查是否需要重试
                time.sleep(5)
                continue
        except Exception as e:
            print(f"\n请求异常: {e}")
            time.sleep(5)
            continue
# --- 主程序 ---
if __name__ == "__main__":
    # question = "请介绍下你自己？"
    # print("--- 开始提问 ---")
    # print(f"问题: {question}")
    
    # print("\n--- 模型答案 ---")
    # answer = query_stream(question)
    
    # print("\n--- 完整回答已接收 ---")

    '''
    Test the image loading function 
    '''
    image_base64 = img.image_to_base64(r"C:\JiahuanPang\project\NDSearch\Instant-Search-main\test\post.png")
    full_response = picture_input(image_base64= image_base64)
    # full_response = picture_input(picture_url= "file:///C:/PangJiahuan/PSearch/VSearch/UI/LLM/R-C.jpg")
    # print(full_response)