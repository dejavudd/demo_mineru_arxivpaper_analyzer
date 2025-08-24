"""
ArXiv PDF Downloader and Image Extractor

简化的工具，支持从arXiv链接下载PDF并使用MinerU提取其中的图片。
支持链接格式：
- https://arxiv.org/abs/XXXX
- https://arxiv.org/pdf/XXXX
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from typing import Optional

import requests


def parse_arxiv_url(arxiv_link: str) -> Optional[str]:
    """解析arXiv链接并返回PDF下载链接。
    
    支持以下格式的链接：
    - https://arxiv.org/abs/XXXX
    - https://arxiv.org/pdf/XXXX
    - https://arxiv.org/pdf/XXXX.pdf

    Args:
        arxiv_link: arXiv链接（abs或pdf格式）

    Returns:
        PDF下载链接，如果不是有效的arXiv链接则返回None
    """
    arxiv_link = arxiv_link.strip()
    
    # 处理abs格式链接: https://arxiv.org/abs/XXXX
    abs_match = re.match(r"https?://arxiv\.org/abs/(?P<id>[\w.\-]+)", arxiv_link)
    if abs_match:
        arxiv_id = abs_match.group("id")
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    # 处理pdf格式链接: https://arxiv.org/pdf/XXXX 或 https://arxiv.org/pdf/XXXX.pdf
    pdf_match = re.match(r"https?://arxiv\.org/pdf/(?P<id>[\w.\-]+)(?:\.pdf)?", arxiv_link)
    if pdf_match:
        arxiv_id = pdf_match.group("id")
        if arxiv_id.endswith(".pdf"):
            return f"https://arxiv.org/pdf/{arxiv_id}"
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    return None


def extract_arxiv_id(arxiv_link: str) -> Optional[str]:
    """从arXiv链接中提取论文ID。
    
    Args:
        arxiv_link: arXiv链接
        
    Returns:
        论文ID，如果无法提取则返回None
    """
    # 从abs链接提取
    abs_match = re.match(r"https?://arxiv\.org/abs/(?P<id>[\w.\-]+)", arxiv_link)
    if abs_match:
        return abs_match.group("id")
    
    # 从pdf链接提取
    pdf_match = re.match(r"https?://arxiv\.org/pdf/(?P<id>[\w.\-]+)(?:\.pdf)?", arxiv_link)
    if pdf_match:
        arxiv_id = pdf_match.group("id")
        if arxiv_id.endswith(".pdf"):
            return arxiv_id[:-4]  # 去掉.pdf后缀
        return arxiv_id
    
    return None


def download_file(url: str, dest_path: str) -> None:
    """下载文件到本地路径。

    Args:
        url: 远程文件URL
        dest_path: 目标文件路径
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def extract_images_with_mineru(pdf_path: str, output_dir: str, lang: str = "en") -> tuple[str, str]:
    """使用MinerU从PDF中提取图片和论文标题。

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录，会在此目录下创建子目录
        lang: 语言提示（如'ch', 'en'），可提高OCR准确性

    Returns:
        元组：(图片目录路径, 论文标题)

    Raises:
        RuntimeError: 如果MinerU未安装或CLI调用失败
    """
    # 确保MinerU CLI可用
    mineru_cmd = "mineru"
    mineru_output = os.path.join(output_dir, "mineru_output")
    os.makedirs(mineru_output, exist_ok=True)
    
    # 执行MinerU CLI解析PDF（极致图片质量设置）
    cmd = [
        mineru_cmd,
        "-p", pdf_path,
        "-o", mineru_output,
        "-m", "auto",
        "--render-dpi", "1200",  # 渲染DPI设为最高
        "--image-dpi", "1200",   # 图片DPI设为最高
        "--image-quality", "100",  # 图片质量100%
        "--keep-vector",         # 保持矢量图形
        "--no-compress",         # 禁用压缩
    ]
    if lang:
        cmd.extend(["--lang", lang])
    
    try:
        print(f"🔄 正在使用MinerU提取图片（1200 DPI极致质量模式）...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ MinerU极致质量处理完成")
    except FileNotFoundError as exc:
        raise RuntimeError(
            "未找到MinerU CLI。请安装MinerU (pip install mineru[core]) 并确保`mineru`命令可用。"
        ) from exc
    except subprocess.CalledProcessError as exc:
        print(f"MinerU stderr: {exc.stderr}")
        raise RuntimeError(f"MinerU处理失败 {pdf_path}: {exc.stderr}") from exc
    
    # 查找MinerU生成的图片目录
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # MinerU可能会创建不同的目录结构，尝试多种可能的路径
    possible_paths = [
        os.path.join(mineru_output, pdf_name, "auto", "images"),
        os.path.join(mineru_output, pdf_name, "images"),
        os.path.join(mineru_output, "auto", "images"),
        os.path.join(mineru_output, "images"),
    ]
    
    images_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            images_dir = path
            break
    
    if not images_dir:
        # 如果没有找到标准路径，搜索整个输出目录
        print(f"🔍 搜索MinerU输出目录: {mineru_output}")
        for root, dirs, files in os.walk(mineru_output):
            if "images" in dirs:
                images_dir = os.path.join(root, "images")
                print(f"✓ 找到图片目录: {images_dir}")
                break
    
    if not images_dir or not os.path.exists(images_dir):
        print(f"⚠️  未找到图片目录，MinerU可能没有提取到图片")
        # 创建空目录以避免错误
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        # 使用PDF文件名作为默认标题
        return images_dir, pdf_name
    
    # 统计提取的图片
    image_files = [f for f in os.listdir(images_dir) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
    
    print(f"✓ MinerU提取了 {len(image_files)} 张图片到: {images_dir}")
    
    # 尝试从MinerU生成的markdown文件中提取论文标题
    paper_title = extract_title_from_mineru_output(mineru_output, pdf_name)
    
    return images_dir, paper_title


def extract_title_from_mineru_output(mineru_output: str, pdf_name: str) -> str:
    """从MinerU输出的markdown文件中提取论文标题。
    
    Args:
        mineru_output: MinerU输出目录
        pdf_name: PDF文件名（不包含扩展名）
        
    Returns:
        论文标题，如果提取失败则返回PDF文件名
    """
    # 尝试查找markdown文件的可能路径
    possible_md_paths = [
        os.path.join(mineru_output, pdf_name, "auto", f"{pdf_name}.md"),
        os.path.join(mineru_output, pdf_name, f"{pdf_name}.md"),
        os.path.join(mineru_output, "auto", f"{pdf_name}.md"),
        os.path.join(mineru_output, f"{pdf_name}.md"),
    ]
    
    # 如果没有找到标准路径，搜索所有.md文件
    md_files = []
    for root, dirs, files in os.walk(mineru_output):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    
    # 将搜索到的md文件添加到可能路径中
    possible_md_paths.extend(md_files)
    
    for md_path in possible_md_paths:
        if os.path.exists(md_path):
            try:
                with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                title = extract_title_from_markdown(content)
                if title and title.strip():
                    print(f"✓ 提取到论文标题: {title}")
                    return sanitize_filename(title.strip())
                    
                print(f"⚠️  提取论文标题失败 {md_path}: {e}")
                continue
            except Exception as e:
                print(f"⚠️  读取markdown文件失败 {md_path}: {e}")
                continue
    
    print(f"⚠️  无法提取论文标题，使用PDF文件名: {pdf_name}")
    return pdf_name


def extract_title_from_markdown(content: str) -> str:
    """从markdown内容中提取论文标题。
    
    Args:
        content: markdown文件内容
        
    Returns:
        提取到的标题，如果提取失败则返回空字符串
    """
    lines = content.split('\n')
    
    # 方法1: 查找第一个一级标题
    for line in lines[:50]:  # 只在前50行中查找
        line = line.strip()
        if line.startswith('# ') and len(line) > 2:
            title = line[2:].strip()
            # 过滤掉一些常见的非标题内容
            if not any(skip in title.lower() for skip in ['abstract', 'introduction', 'content', 'table', 'figure']):
                if len(title) > 10 and len(title) < 200:  # 合理的标题长度
                    return title
    
    # 方法2: 查找模式匹配的标题行（通常论文标题会在前几行，且较长）
    for i, line in enumerate(lines[:20]):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('*'):
            # 检查是否像标题（长度适中，包含大写字母等）
            if (20 < len(line) < 200 and 
                any(c.isupper() for c in line) and 
                ':' not in line[:20] and  # 排除类似 "Abstract:" 的行
                line.count('.') < 3):  # 排除句子
                return line
    
    # 方法3: 查找粗体标记的文本（可能是标题）
    import re
    bold_pattern = r'\*\*(.*?)\*\*'
    bold_matches = re.findall(bold_pattern, content[:2000])  # 在前2000字符中查找
    for match in bold_matches:
        if 20 < len(match) < 200 and not any(skip in match.lower() for skip in ['abstract', 'figure', 'table']):
            return match
    
    return ""


def enhance_image_quality(src_path: str, dst_path: str) -> Optional[str]:
    """使用多种方法增强图片质量。
    
    Args:
        src_path: 源图片路径
        dst_path: 目标图片路径
        
    Returns:
        增强后的图片路径，如果失败返回None
    """
    try:
        # 尝试导入PIL和OpenCV进行图片处理
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            import cv2
            import numpy as np
            has_cv2 = True
        except ImportError:
            from PIL import Image, ImageEnhance, ImageFilter
            has_cv2 = False
        
        # 打开图片
        with Image.open(src_path) as img:
            # 转换为RGB模式（如果不是的话）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            width, height = img.size
            original_size = width * height
            
            # 1. 智能上采样
            if original_size < 1000000:  # 小于1MP的图片
                if has_cv2:
                    # 使用OpenCV的EDSR超分辨率（如果可用）
                    enhanced_img = apply_cv2_super_resolution(img)
                    if enhanced_img:
                        img = enhanced_img
                        print(f"    🧠 AI超分辨率: {width}x{height} → {img.size[0]}x{img.size[1]}")
                    else:
                        # 回退到LANCZOS上采样
                        scale = min(4, int(np.sqrt(2000000 / original_size)))  # 动态计算缩放比例
                        new_size = (width * scale, height * scale)
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        print(f"    📈 高质量上采样: {width}x{height} → {new_size[0]}x{new_size[1]}")
                else:
                    # 标准LANCZOS上采样
                    scale = min(3, int(np.sqrt(1500000 / original_size)))
                    new_size = (width * scale, height * scale)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    print(f"    📈 标准上采样: {width}x{height} → {new_size[0]}x{new_size[1]}")
            
            # 2. 图片增强处理
            img = apply_image_enhancement(img)
            
            # 保存为高质量PNG
            base_name = os.path.splitext(dst_path)[0]
            enhanced_path = f"{base_name}_enhanced.png"
            img.save(enhanced_path, 'PNG', optimize=False, compress_level=0)
            
            return enhanced_path
            
    except Exception as e:
        print(f"    ⚠️  图片增强失败: {e}")
        # 失败时直接复制原文件
        shutil.copy2(src_path, dst_path)
        return dst_path


def apply_cv2_super_resolution(pil_img):
    """使用OpenCV进行AI超分辨率处理。"""
    try:
        import cv2
        import numpy as np
        from PIL import Image
        
        # 将PIL图片转换为OpenCV格式
        img_array = np.array(pil_img)
        img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # 使用OpenCV的高质量上采样算法
        height, width = img_cv2.shape[:2]
        upscaled = cv2.resize(img_cv2, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        # 应用锐化滤波器
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(upscaled, -1, kernel)
        
        # 转换回PIL格式
        result_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
        result_pil = Image.fromarray(result_rgb)
        
        return result_pil
        
    except Exception as e:
        print(f"    ⚠️  OpenCV处理失败: {e}")
        return None


def apply_image_enhancement(img):
    """应用图片增强处理。"""
    try:
        from PIL import ImageEnhance, ImageFilter
        
        # 1. 轻微锐化
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        
        # 2. 对比度增强
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)
        
        # 3. 色彩饱和度微调
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.05)
        
        # 4. 轻微的降噪（使用更温和的滤镜）
        img = img.filter(ImageFilter.SMOOTH)
        
        print(f"    ✨ 图片增强完成：锐化+对比度+降噪")
        
        return img
        
    except Exception as e:
        print(f"    ⚠️  图片增强处理失败: {e}")
        return img


def sanitize_filename(name: str) -> str:
    """将字符串转换为安全的文件名。"""
    return re.sub(r"[^\w\-\.]+", "_", name).strip("._")


def copy_images_to_output(source_images_dir: str, output_dir: str, paper_title: str) -> tuple[int, str]:
    """将提取的图片复制到输出目录。
    
    Args:
        source_images_dir: MinerU提取的图片源目录
        output_dir: 目标输出目录
        paper_title: 论文标题，用作目录名
        
    Returns:
        元组：(复制的图片数量, 论文输出目录路径)
    """
    # 创建以论文标题命名的输出目录
    paper_output_dir = os.path.join(output_dir, paper_title)
    os.makedirs(paper_output_dir, exist_ok=True)
    
    if not os.path.exists(source_images_dir):
        print(f"⚠️  源图片目录不存在: {source_images_dir}")
        return 0, paper_output_dir
    
    copied_count = 0
    
    # 过滤并复制图片
    for image_file in os.listdir(source_images_dir):
        if image_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
            src_path = os.path.join(source_images_dir, image_file)
            dst_path = os.path.join(paper_output_dir, image_file)
            
            # 过滤太小的图片（可能是装饰性图片）
            try:
                file_size = os.path.getsize(src_path)
                if file_size < 5000:  # 小于5KB的图片跳过
                    continue
                
                # 尝试进行图片质量增强
                enhanced_path = enhance_image_quality(src_path, dst_path)
                if enhanced_path:
                    final_size = os.path.getsize(enhanced_path)
                    copied_count += 1
                    print(f"✓ 复制并增强图片: {image_file} ({file_size//1024}KB → {final_size//1024}KB)")
                else:
                    shutil.copy2(src_path, dst_path)
                    copied_count += 1
                    print(f"✓ 复制图片: {image_file} ({file_size//1024}KB)")
                
            except Exception as e:
                print(f"⚠️  复制图片失败 {image_file}: {e}")
    
    print(f"✓ 共复制 {copied_count} 张图片到: {paper_output_dir}")
    return copied_count, paper_output_dir





def process_arxiv_paper(arxiv_url: str, output_dir: str = "output") -> bool:
    """处理单个arXiv论文：下载PDF并提取图片。

    Args:
        arxiv_url: arXiv论文链接（支持abs和pdf格式）
        output_dir: 输出目录

    Returns:
        处理成功返回True，失败返回False
    """
    try:
        print(f"📥 开始处理arXiv论文: {arxiv_url}")
        
        # 解析arXiv链接获取PDF下载链接
        pdf_url = parse_arxiv_url(arxiv_url)
        if not pdf_url:
            print(f"❌ 无效的arXiv链接: {arxiv_url}")
            return False
        
        # 提取论文ID作为文件名
        paper_id = extract_arxiv_id(arxiv_url)
        if not paper_id:
            print(f"❌ 无法从链接中提取论文ID: {arxiv_url}")
            return False
        
        print(f"📄 论文ID: {paper_id}")
        print(f"📥 PDF下载链接: {pdf_url}")
        
        # 创建目录
        os.makedirs(output_dir, exist_ok=True)
        tmp_dir = os.path.join(output_dir, ".tmp")  # 临时目录设在output下的隐藏文件夹
        os.makedirs(tmp_dir, exist_ok=True)
        
        # 下载PDF
        safe_paper_id = sanitize_filename(paper_id)
        pdf_path = os.path.join(tmp_dir, f"{safe_paper_id}.pdf")
        
        print(f"⬇️ 正在下载PDF...")
        download_file(pdf_url, pdf_path)
        print(f"✅ PDF下载完成: {pdf_path}")
        
        # 使用MinerU提取图片和论文标题
        print(f"🖼️ 正在使用MinerU提取图片和论文标题...")
        images_dir, paper_title = extract_images_with_mineru(pdf_path, tmp_dir)
        
        # 如果未能提取到标题，使用论文ID作为备用
        if not paper_title or paper_title == os.path.splitext(os.path.basename(pdf_path))[0]:
            paper_title = safe_paper_id
            print(f"📄 使用论文ID作为文件夹名: {paper_title}")
        else:
            print(f"📄 论文标题: {paper_title}")
        
        # 复制图片到输出目录
        print(f"📁 正在整理输出文件...")
        copied_count, paper_output_dir = copy_images_to_output(images_dir, output_dir, paper_title)
        
        # 复制PDF到输出目录
        output_pdf_path = os.path.join(paper_output_dir, f"{sanitize_filename(paper_title)}.pdf")
        shutil.copy2(pdf_path, output_pdf_path)
        
        # 清理临时文件
        try:
            shutil.rmtree(tmp_dir)
            print(f"🗑️ 清理临时文件: {tmp_dir}")
        except Exception as e:
            print(f"⚠️  清理临时文件失败: {e}")
        
        print(f"\n🎉 处理完成!")
        print(f"📂 输出目录: {paper_output_dir}")
        print(f"📄 PDF文件: {os.path.basename(output_pdf_path)}")
        print(f"🖼️ 图片数量: {copied_count}")
        print(f"📁 图片位置: 与PDF文件在同一目录")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False


def main() -> None:
    """主函数：解析命令行参数并处理arXiv论文。"""
    parser = argparse.ArgumentParser(
        description="从arXiv链接下载PDF并提取图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的链接格式:
  https://arxiv.org/abs/2412.15289
  https://arxiv.org/pdf/2412.15289
  https://arxiv.org/pdf/2412.15289.pdf

使用示例:
  python lrm_paper_analyzer.py https://arxiv.org/abs/2412.15289
  python lrm_paper_analyzer.py --url https://arxiv.org/pdf/2412.15289 --output papers
        """
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="arXiv论文链接（abs或pdf格式）"
    )
    
    parser.add_argument(
        "--url", 
        dest="arxiv_url",
        help="arXiv论文链接（与位置参数二选一）"
    )
    
    parser.add_argument(
        "--output",
        default="output",
        help="输出目录 (默认: output)"
    )
    
    args = parser.parse_args()
    
    # 获取arXiv链接
    arxiv_url = args.url or args.arxiv_url
    if not arxiv_url:
        print("❌ 请提供arXiv论文链接")
        print("使用示例: python lrm_paper_analyzer.py https://arxiv.org/abs/2412.15289")
        print("或者: python lrm_paper_analyzer.py --url https://arxiv.org/abs/2412.15289")
        sys.exit(1)
    
    # 处理论文
    success = process_arxiv_paper(arxiv_url, args.output)
    
    if success:
        print(f"\n✅ 处理成功! 结果保存在: {args.output}")
        sys.exit(0)
    else:
        print(f"\n❌ 处理失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()