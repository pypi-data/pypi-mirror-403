from PIL import Image
import os


def convert_webp_to_jpg(input_path, output_path=None, quality=85,DELETE = False):
    """
    使用Pillow将WebP转换为JPG

    参数：
    input_path: 输入的WebP文件路径
    output_path: 输出的JPG文件路径（可选）
    quality: JPG质量，1-100
    """
    try:
        # 打开WebP图片
        with Image.open(input_path) as img:
            # 如果是RGBA模式，转换为RGB（JPG不支持透明度）
            if img.mode in ('RGBA', 'LA'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img, mask=img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 设置输出路径
            if output_path is None:
                output_path = os.path.splitext(input_path)[0] + '.jpg'

            # 保存为JPG
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            print(f"转换成功: {input_path} -> {output_path}")
            if DELETE:
                os.remove(input_path)
            return output_path

    except Exception as e:
        print(f"转换失败: {e}")
        return None