import os
import json
import re
import argparse
import hashlib
import sys

# ==================== 配置区域 ====================
# 重命名文件黑名单（这些文件不会被重命名）
RENAME_FILE_BLACKLIST = [
    'manifest.json',
    'languages.json',
    'sounds.json',
    'contents.json'
]
RENAME_FILE_BLACKLIST_ENABLED = True  # 是否启用重命名文件黑名单

# 重命名文件夹黑名单（这些文件夹下的文件不会被重命名）
RENAME_FOLDER_BLACKLIST = []
RENAME_FOLDER_BLACKLIST_ENABLED = False  # 是否启用重命名文件夹黑名单

# 加密文件黑名单（这些文件不会被加密）
ENCRYPT_FILE_BLACKLIST = []
ENCRYPT_FILE_BLACKLIST_ENABLED = True  # 是否启用加密文件黑名单

# 加密文件夹黑名单（这些文件夹下的文件不会被加密）
ENCRYPT_FOLDER_BLACKLIST = ['render_controllers','particles']
ENCRYPT_FOLDER_BLACKLIST_ENABLED = True  # 是否启用加密文件夹黑名单

# 重命名文件白名单（这些文件会被重命名，当黑名单禁用时）
RENAME_FILE_WHITELIST = []
RENAME_FILE_WHITELIST_ENABLED = False  # 是否启用重命名文件白名单

# 重命名文件夹白名单（这些文件夹下的文件会被重命名，当黑名单禁用时）
RENAME_FOLDER_WHITELIST = ['animation_controllers','animations','attachables','entity','particles','render_controllers']
RENAME_FOLDER_WHITELIST_ENABLED = True  # 是否启用重命名文件夹白名单

# 加密文件白名单（这些文件会被加密，当黑名单禁用时）
ENCRYPT_FILE_WHITELIST = []
ENCRYPT_FILE_WHITELIST_ENABLED = False  # 是否启用加密文件白名单

# 加密文件夹白名单（这些文件夹下的文件会被加密，当黑名单禁用时）
ENCRYPT_FOLDER_WHITELIST = []
ENCRYPT_FOLDER_WHITELIST_ENABLED = False  # 是否启用加密文件夹白名单

# 混淆内容（在entity或ui文件夹下的文件会添加此内容）
CONFUSION_CONTENT = """,{[
"13":"\\u0071\\u0065\\u0077\\u0062\\u0074\\u0072\\u0077\\u0064","\\u201c\\u541b\\u5b50\\u52a0\\u5bc6\\u201d:\"\"\"},{"\\u563f\\u563f":"\\u55b5\\u9171\\u7684\\u817f\\u771f\\u597d\\u770b\\u55b5"},{"\\usdad\\udada\\udawda"}"ada"],"ada","aakks"]}}{}}}"""

# ==================== 函数定义 ====================

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

def is_in_blacklist(file_path, file_blacklist, folder_blacklist, file_blacklist_enabled, folder_blacklist_enabled):
    """检查文件是否在黑名单中"""
    if not file_blacklist_enabled and not folder_blacklist_enabled:
        return False
    
    file_name = os.path.basename(file_path)
    path_parts = file_path.split(os.sep)
    
    # 检查文件黑名单
    if file_blacklist_enabled and file_name in file_blacklist:
        return True
    
    # 检查文件夹黑名单
    if folder_blacklist_enabled and any(folder in path_parts for folder in folder_blacklist):
        return True
    
    return False

def is_in_whitelist(file_path, file_whitelist, folder_whitelist, file_whitelist_enabled, folder_whitelist_enabled):
    """检查文件是否在白名单中"""
    if not file_whitelist_enabled and not folder_whitelist_enabled:
        return False
    
    file_name = os.path.basename(file_path)
    path_parts = file_path.split(os.sep)
    
    # 检查文件白名单
    if file_whitelist_enabled and file_name in file_whitelist:
        return True
    
    # 检查文件夹白名单
    if folder_whitelist_enabled and any(folder in path_parts for folder in folder_whitelist):
        return True
    
    return False

def check_list_config(file_blacklist_enabled, file_whitelist_enabled, folder_blacklist_enabled, folder_whitelist_enabled, list_type):
    """检查名单配置是否有效"""
    # 检查文件名单配置
    if file_blacklist_enabled and file_whitelist_enabled:
        print(f"错误: {list_type}文件 不能同时启用黑名单和白名单")
        return False
    if not file_blacklist_enabled and not file_whitelist_enabled:
        print(f"错误: {list_type}文件 不能同时禁用黑名单和白名单")
        return False
    
    # 检查文件夹名单配置
    if folder_blacklist_enabled and folder_whitelist_enabled:
        print(f"错误: {list_type}文件夹 不能同时启用黑名单和白名单")
        return False
    if not folder_blacklist_enabled and not folder_whitelist_enabled:
        print(f"错误: {list_type}文件夹 不能同时禁用黑名单和白名单")
        return False
    
    return True

def should_rename_file(file_path):
    """检查文件是否应该重命名"""
    # 检查配置是否有效
    if not check_list_config(
        RENAME_FILE_BLACKLIST_ENABLED,
        RENAME_FILE_WHITELIST_ENABLED,
        RENAME_FOLDER_BLACKLIST_ENABLED,
        RENAME_FOLDER_WHITELIST_ENABLED,
        "重命名"
    ):
        sys.exit(1)
    
    # 检查文件黑名单
    if RENAME_FILE_BLACKLIST_ENABLED:
        file_name = os.path.basename(file_path)
        if file_name in RENAME_FILE_BLACKLIST:
            return False
    
    # 检查文件夹黑名单
    if RENAME_FOLDER_BLACKLIST_ENABLED:
        path_parts = file_path.split(os.sep)
        if any(folder in path_parts for folder in RENAME_FOLDER_BLACKLIST):
            return False
    
    # 检查文件白名单
    if RENAME_FILE_WHITELIST_ENABLED:
        file_name = os.path.basename(file_path)
        if file_name in RENAME_FILE_WHITELIST:
            return True
        else:
            return False
    
    # 检查文件夹白名单
    if RENAME_FOLDER_WHITELIST_ENABLED:
        path_parts = file_path.split(os.sep)
        if any(folder in path_parts for folder in RENAME_FOLDER_WHITELIST):
            return True
        else:
            return False
    
    # 如果没有任何名单启用，默认重命名
    return True

def should_encrypt_file(file_path):
    """检查文件是否应该加密"""
    # 检查配置是否有效
    if not check_list_config(
        ENCRYPT_FILE_BLACKLIST_ENABLED,
        ENCRYPT_FILE_WHITELIST_ENABLED,
        ENCRYPT_FOLDER_BLACKLIST_ENABLED,
        ENCRYPT_FOLDER_WHITELIST_ENABLED,
        "加密"
    ):
        sys.exit(1)
    
    # 检查文件黑名单
    if ENCRYPT_FILE_BLACKLIST_ENABLED:
        file_name = os.path.basename(file_path)
        if file_name in ENCRYPT_FILE_BLACKLIST:
            return False
    
    # 检查文件夹黑名单
    if ENCRYPT_FOLDER_BLACKLIST_ENABLED:
        path_parts = file_path.split(os.sep)
        if any(folder in path_parts for folder in ENCRYPT_FOLDER_BLACKLIST):
            return False
    
    # 检查文件白名单
    if ENCRYPT_FILE_WHITELIST_ENABLED:
        file_name = os.path.basename(file_path)
        if file_name in ENCRYPT_FILE_WHITELIST:
            return True
        else:
            return False
    
    # 检查文件夹白名单
    if ENCRYPT_FOLDER_WHITELIST_ENABLED:
        path_parts = file_path.split(os.sep)
        if any(folder in path_parts for folder in ENCRYPT_FOLDER_WHITELIST):
            return True
        else:
            return False
    
    # 如果没有任何名单启用，默认加密
    return True

def calculate_file_md5(file_path):
    """计算文件的MD5值"""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def obfuscate_filename(file_path):
    """混淆文件名：将JSON文件名改为其MD5值"""
    try:
        # 检查是否应该重命名
        if not should_rename_file(file_path):
            return file_path
        
        # 计算MD5并重命名文件
        md5_hash = calculate_file_md5(file_path)
        dir_name = os.path.dirname(file_path)
        new_file_path = os.path.join(dir_name, f"{md5_hash}.json")
        
        # 如果新文件名与旧文件名不同，则重命名
        if file_path != new_file_path:
            os.rename(file_path, new_file_path)
            print(f"已重命名: {os.path.basename(file_path)} -> {md5_hash}.json")
            return new_file_path
        
        return file_path
    except Exception as e:
        print(f"重命名文件 {file_path} 时出错: {e}")
        return file_path

def process_json_file(file_path):
    """处理单个JSON文件"""
    try:
        # 检查是否应该加密
        if not should_encrypt_file(file_path):
            print(f"跳过加密: {file_path}")
            # 即使跳过加密，仍然可能进行文件名混淆
            obfuscate_filename(file_path)
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
            confusion_content = CONFUSION_CONTENT

        # 写回文件（保持紧凑格式）
        with open(file_path, 'w', encoding='utf-8') as f:
            json_str = json.dumps(encrypted_data, ensure_ascii=False, separators=(',', ':'))
            f.write(json_str.encode('utf-8').decode('unicode-escape') + confusion_content)
            
        print(f"已完全加密: {file_path}")
        
        # 文件名混淆（在内容加密后进行）
        obfuscate_filename(file_path)
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误 {file_path}: {e}")
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")

def process_directory(directory):
    """递归处理目录中的所有JSON文件"""
    json_files = []
    
    # 首先收集所有JSON文件
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.json'):
                file_path = os.path.join(root, file)
                json_files.append(file_path)
    
    # 处理每个文件
    for file_path in json_files:
        process_json_file(file_path)

def print_config():
    """打印当前配置"""
    print("=" * 50)
    print("当前配置:")
    print(f"重命名文件黑名单: {RENAME_FILE_BLACKLIST} (启用: {RENAME_FILE_BLACKLIST_ENABLED})")
    print(f"重命名文件夹黑名单: {RENAME_FOLDER_BLACKLIST} (启用: {RENAME_FOLDER_BLACKLIST_ENABLED})")
    print(f"加密文件黑名单: {ENCRYPT_FILE_BLACKLIST} (启用: {ENCRYPT_FILE_BLACKLIST_ENABLED})")
    print(f"加密文件夹黑名单: {ENCRYPT_FOLDER_BLACKLIST} (启用: {ENCRYPT_FOLDER_BLACKLIST_ENABLED})")
    print(f"重命名文件白名单: {RENAME_FILE_WHITELIST} (启用: {RENAME_FILE_WHITELIST_ENABLED})")
    print(f"重命名文件夹白名单: {RENAME_FOLDER_WHITELIST} (启用: {RENAME_FOLDER_WHITELIST_ENABLED})")
    print(f"加密文件白名单: {ENCRYPT_FILE_WHITELIST} (启用: {ENCRYPT_FILE_WHITELIST_ENABLED})")
    print(f"加密文件夹白名单: {ENCRYPT_FOLDER_WHITELIST} (启用: {ENCRYPT_FOLDER_WHITELIST_ENABLED})")
    print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description='完全Unicode加密JSON工具')
    parser.add_argument('--data-dir', default='data', help='要处理的目录路径')
    parser.add_argument('--no-rename', action='store_true', help='跳过文件名重命名')
    parser.add_argument('--no-encrypt', action='store_true', help='跳过文件内容加密')
    parser.add_argument('--show-config', action='store_true', help='显示当前配置')
    args = parser.parse_args()
    
    if args.show_config:
        print_config()
        return
    
    if not os.path.exists(args.data_dir):
        print(f"目录不存在: {args.data_dir}")
        return
    
    print_config()
    print(f"开始处理目录: {args.data_dir}")
    
    # 如果指定了不重命名，临时修改重命名函数
    if args.no_rename:
        global obfuscate_filename
        original_obfuscate = obfuscate_filename
        
        def no_rename(file_path):
            return file_path
        
        obfuscate_filename = no_rename
        print("跳过文件名重命名")
    
    # 如果指定了不加密，临时修改处理函数
    if args.no_encrypt:
        global process_json_file
        original_process = process_json_file
        
        def no_encrypt_process(file_path):
            try:
                # 只进行文件名混淆，不加密内容
                obfuscate_filename(file_path)
                print(f"已跳过加密: {file_path}")
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
        
        process_json_file = no_encrypt_process
        print("跳过文件内容加密")
    
    process_directory(args.data_dir)
    print("处理完成")

if __name__ == '__main__':
    main()