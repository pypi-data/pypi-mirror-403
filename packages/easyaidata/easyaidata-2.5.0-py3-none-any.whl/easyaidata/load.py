#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import platform
import threading
import subprocess
import requests
import json
import shutil

# 确保当前目录和pyds目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
pyds_dir = os.path.join(current_dir, 'pyds')

for path in [pyds_dir, current_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 确保settings文件夹存在
def ensure_settings_folder():
    settings_dir = os.path.join(current_dir, 'settings')
    if not os.path.exists(settings_dir):
        print("创建settings文件夹...")
        os.makedirs(settings_dir)
    
    # 确保SKILLS_README.md文件存在
    skills_readme_path = os.path.join(settings_dir, 'SKILLS_README.md')
    if not os.path.exists(skills_readme_path):
        print("创建SKILLS_README.md文件...")
        # 创建默认的SKILLS_README.md文件
        with open(skills_readme_path, 'w', encoding='utf-8') as f:
            f.write("# Skills README\n\nThis file contains information about the skills system.")
    
    return settings_dir

# 获取当前版本
current_version = "2.5"  # 与setup.py中的版本一致

# 检查更新的函数
def check_for_updates():
    print("检查easyaidata更新中...")
    try:
        # 使用pip检查最新版本
        import subprocess
        
        # 尝试从PyPI获取最新版本信息（不使用--format=json选项）
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", "easyaidata"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # 解析文本输出
            output = result.stdout
            if "Available versions:" in output:
                # 提取版本号列表
                versions_line = output.split("Available versions:")[1].strip()
                # 移除括号和逗号，分割版本号
                versions_str = versions_line.strip('()')
                versions = [v.strip() for v in versions_str.split(',')]
                
                if versions:
                    latest_version = versions[0]  # 第一个版本通常是最新的
                    print(f"当前版本: {current_version}")
                    print(f"最新版本: {latest_version}")
                    
                    # 比较版本号
                    def version_to_tuple(version):
                        return tuple(map(int, version.split('.')))
                    
                    if version_to_tuple(latest_version) > version_to_tuple(current_version):
                        print(f"发现新版本 {latest_version}，开始更新...")
                        return True, latest_version
                    else:
                        print("easyaidata已是最新版本，无需更新")
                        return False, current_version
                else:
                    print("无法获取版本信息，使用当前版本")
                    return False, current_version
            else:
                print("无法获取版本信息，使用当前版本")
                return False, current_version
        else:
            print("无法连接到PyPI，使用当前版本")
            return False, current_version
    except Exception as e:
        print(f"检查更新时出错: {e}")
        return False, current_version

# 下载并安装更新的函数
def download_and_update():
    print("正在下载并安装更新...")
    try:
        # 这里假设你有一个pip安装命令来更新
        # 实际使用时需要替换为真实的安装命令
        # 例如：subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "easyaidata"])
        # 或者从指定URL下载安装包并安装
        
        # 模拟更新过程
        print("更新中，请稍候...")
        # 实际更新命令
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "easyaidata"])
        print("更新完成！")
        return True
    except Exception as e:
        print(f"更新时出错: {e}")
        return False

# 尝试导入app模块，优先使用编译后的.pyd文件
def import_app():
    try:
        import app
        print("Successfully imported app module")
        return app
    except ImportError as e:
        print(f"Failed to import app module: {e}")
        sys.exit(1)

def main():
    # 确保settings文件夹存在
    ensure_settings_folder()
    
    # 检查更新
    has_update, version = check_for_updates()
    if has_update:
        # 下载并安装更新
        update_success = download_and_update()
        if update_success:
            print("更新成功，重启应用...")
            # 重新确保settings文件夹存在（更新后可能需要）
            ensure_settings_folder()
            # 重新导入app模块
            app = import_app()
        else:
            print("更新失败，使用当前版本启动...")
            app = import_app()
    else:
        app = import_app()
    
    # 创建TableProcessor实例并启动主循环
    import tkinter as tk
    root = tk.Tk()
    table_processor = app.TableProcessor(root)
    root.mainloop()

if __name__ == '__main__':
    main()
