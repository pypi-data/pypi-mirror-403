#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBuild 测试运行器
一键运行所有测试文件
支持命令行参数指定测试文件或目录
"""

import os
import sys
import subprocess
import argparse

# 获取项目根目录路径（当前脚本所在目录）
project_root = os.path.dirname(os.path.abspath(__file__))

# 将项目根目录添加到Python路径，确保能找到cbuild模块
sys.path.insert(0, project_root)

def run_test_file(file_path):
    """运行单个测试文件"""
    print(f"\n{'='*60}")
    print(f"运行测试: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    try:
        # 设置环境变量，将项目根目录添加到Python路径
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{project_root};{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = project_root
        
        # 运行测试文件
        result = subprocess.run([sys.executable, file_path], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.path.dirname(file_path),
                              env=env)
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print(f"\n[ERROR] 错误输出:")
            print(result.stderr)
        
        # 输出返回码
        if result.returncode == 0:
            print(f"\n[OK] 测试通过: {os.path.basename(file_path)}")
        else:
            print(f"\n[ERROR] 测试失败: {os.path.basename(file_path)} (返回码: {result.returncode})")
        
        return result.returncode
    except Exception as e:
        print(f"\n[ERROR] 运行测试时发生错误: {e}")
        return 1

def find_test_files(test_path, recursive=False):
    """查找测试文件
    
    Args:
        test_path: 测试文件或目录路径
        recursive: 是否递归查找子目录中的测试文件
        
    Returns:
        测试文件列表
    """
    test_files = []
    
    # 转换为绝对路径，确保正确处理相对路径
    abs_test_path = os.path.abspath(test_path)
    
    # 如果是文件，直接添加
    if os.path.isfile(abs_test_path):
        if abs_test_path.endswith('.py') and (os.path.basename(abs_test_path).startswith('test_') or 'test' in os.path.basename(abs_test_path).lower()):
            test_files.append(abs_test_path)
        else:
            print(f"⚠️  跳过非测试文件: {test_path}")
    # 如果是目录，查找其中的测试文件
    elif os.path.isdir(abs_test_path):
        for root, dirs, files in os.walk(abs_test_path):
            for file in files:
                if file.endswith('.py') and file.startswith('test_'):
                    test_files.append(os.path.join(root, file))
            if not recursive:
                break
    else:
        print(f"❌ 测试路径不存在: {test_path}")
    
    return test_files

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="CBuild 测试运行器")
    parser.add_argument('--test-path', '-p', type=str, help="指定测试文件或目录路径")
    parser.add_argument('--recursive', '-r', action='store_true', help="递归查找子目录中的测试文件")
    parser.add_argument('--verbose', '-v', action='store_true', help="显示详细输出")
    args = parser.parse_args()
    
    print("CBuild 一键测试运行器")
    print(f"项目根目录: {project_root}")
    
    # 确定测试目录或文件路径
    test_path = args.test_path or os.path.join(project_root, 'tests')
    
    # 查找测试文件
    test_files = find_test_files(test_path, args.recursive)
    
    # 按文件名排序
    test_files.sort()
    
    if not test_files:
        print(f"❌ 未找到测试文件，路径: {test_path}")
        sys.exit(1)
    
    print(f"\n找到 {len(test_files)} 个测试文件:")
    for i, test_file in enumerate(test_files, 1):
        print(f"  {i}. {os.path.relpath(test_file, project_root)}")
    
    # 运行所有测试
    failed_tests = 0
    total_tests = len(test_files)
    
    for test_file in test_files:
        return_code = run_test_file(test_file)
        if return_code != 0:
            failed_tests += 1
    
    # 打印测试总结
    print(f"\n{'='*60}")
    print(f"测试总结: {total_tests} 个测试")
    print(f"通过: {total_tests - failed_tests}")
    print(f"失败: {failed_tests}")
    print(f"{'='*60}")
    
    if failed_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()