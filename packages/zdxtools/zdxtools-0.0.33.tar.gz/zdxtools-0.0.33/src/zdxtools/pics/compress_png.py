import subprocess
import os
import sys

import subprocess
import os
from pathlib import Path



def compress_png_overwrite(file_path, quality='50-90'):
    """
    使用pngquant压缩PNG图片并覆盖原文件

    Args:
        file_path: PNG图片路径
        quality: 压缩质量范围，如'70-85'
    """
    if '.png' not in file_path:return False
    try:
        # 构建pngquant命令
        cmd = [
            'pngquant',
            '--force',  # 强制覆盖
            '--verbose',  # 强制覆盖
            '--ordered',  # 强制覆盖
            '--speed', '1', # 强制覆盖
            '--quality', quality,
            '--ext', '.png',  # 保持原扩展名
            '--skip-if-larger',  # 如果压缩后文件更大则跳过
            file_path
        ]

        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ 成功压缩: {file_path}")
            return True
        else:
            print(f"✗ 压缩失败 {file_path}: {result.stderr}")
            return False

    except FileNotFoundError:
        print("错误: 未找到pngquant，请先安装pngquant")
        return False
    except Exception as e:
        print(f"错误处理 {file_path}: {str(e)}")
        return False


def batch_compress_overwrite(directory, quality='70-85', recursive=True):
    """
    批量压缩目录中的所有PNG文件并覆盖原文件

    Args:
        directory: 目录路径
        quality: 压缩质量
        recursive: 是否递归处理子目录
    """
    directory = Path(directory)

    if recursive:
        # 递归查找所有PNG文件
        png_files = list(directory.rglob('*.png'))
    else:
        # 仅查找当前目录的PNG文件
        png_files = list(directory.glob('*.png'))

    print(f"找到 {len(png_files)} 个PNG文件")

    success_count = 0
    total_savings = 0

    for png_file in png_files:
        # 记录原始文件大小
        original_size = png_file.stat().st_size

        # 压缩文件
        if compress_png_overwrite(str(png_file), quality):
            # 计算节省的空间
            compressed_size = png_file.stat().st_size
            savings = original_size - compressed_size

            if savings > 0:
                total_savings += savings
                success_count += 1
                print(f"  节省: {savings / 1024:.2f} KB")
            else:
                print(f"  文件已优化或无变化")

    print(f"\n批量压缩完成!")
    print(f"成功处理: {success_count}/{len(png_files)} 个文件")
    print(f"总节省空间: {total_savings / 1024:.2f} KB")

if __name__ == '__main__':

    # 使用示例
    batch_compress_overwrite('./images', quality='65-80', recursive=True)
    # 使用示例
    compress_png_overwrite(r'D:\software\pngquant\bdea9717-1d06-474f-ab6f-e8d23910fb9b-176281179012.png', quality='50-90')