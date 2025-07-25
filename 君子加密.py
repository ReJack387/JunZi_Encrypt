import os
import json
import re
import argparse

def remove_comments(json_str):
    """删除JSON字符串中的注释"""
    json_str = re.sub(r'//.*', '', json_str)  # 删除单行注释
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)  # 删除多行注释
    return json_str.strip()

def unicode_escape_all(c):
    """将字符转换为Unicode转义序列，但保留JSON结构字符"""
    if c in '{}[]",:':  # 保留JSON结构字符
        return c
    return f'\\u{ord(c):04x}'

def encrypt_json_string(s):
    """加密字符串（不包括两边的引号）"""
    return ''.join(unicode_escape_all(c) for c in s)

def encrypt_json_data(obj):
    """递归处理JSON数据"""
    if isinstance(obj, dict):
        return {encrypt_json_string(k): encrypt_json_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [encrypt_json_data(item) for item in obj]
    elif isinstance(obj, str):
        return encrypt_json_string(obj)
    else:
        return obj

def should_add_confusion(file_path):
    """检查文件路径是否在entity或ui文件夹下"""
    path_parts = file_path.split(os.sep)
    return 'entity' in path_parts or 'ui' in path_parts

def process_json_file(file_path):
    """处理单个JSON文件"""
    try:
        # 检查是否在render_controllers文件夹中
        if 'render_controllers' in file_path.split(os.sep):
            print(f"跳过render_controllers文件夹中的文件: {file_path}")
            return
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 删除注释
        content_no_comments = remove_comments(content)
        
        # 解析JSON以确保格式正确
        data = json.loads(content_no_comments)
        
        # 加密JSON数据
        encrypted_data = encrypt_json_data(data)
        
        # 检查是否需要添加混淆内容
        confusion_content = ""
        if should_add_confusion(file_path):
            confusion_content = """,{[
"13":"\\u0071\\u0065\\u0077\\u0062\\u0074\\u0072\\u0077\\u0064",
"
\\u201c\\u541b\\u5b50\\u52a0\\u5bc6\\u201d:\"\"\"
}]]}"""

        # 写回文件（保持紧凑格式）
        with open(file_path, 'w', encoding='utf-8') as f:
            json_str = json.dumps(encrypted_data, ensure_ascii=False, separators=(',', ':'))
            f.write(json_str.encode('utf-8').decode('unicode-escape') + confusion_content)
            
        print(f"已完全加密: {file_path}")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误 {file_path}: {e}")
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")

def process_directory(directory):
    """递归处理目录中的所有JSON文件"""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.json'):
                file_path = os.path.join(root, file)
                process_json_file(file_path)

def main():
    parser = argparse.ArgumentParser(description='完全Unicode加密JSON工具')
    parser.add_argument('--data-dir', default='data', help='要处理的目录路径')
    args = parser.parse_args()
    
    if not os.path.exists(args.data_dir):
        print(f"目录不存在: {args.data_dir}")
        return
    
    print(f"开始处理目录: {args.data_dir}")
    process_directory(args.data_dir)
    print("处理完成，所有字符已转换为Unicode转义序列")

if __name__ == '__main__':
    main()