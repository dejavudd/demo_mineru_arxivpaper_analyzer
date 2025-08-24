# ArXiv PDF Downloader and Image Extractor

🔗 **简单高效的arXiv论文PDF下载和图片提取工具**

一个专业级的工具，专门用于从arXiv链接下载PDF论文并使用MinerU提取其中的图片。配备AI多层级图片增强系统，提供市面最高质量的图片提取效果。自动识别论文标题，创建结构化的文件夹，将PDF和增强后的图片保存在一起。

## ✨ 主要功能

- 📥 **智能链接解析**：支持多种arXiv链接格式（abs、pdf）
- 📄 **自动PDF下载**：从arXiv直接下载原始PDF文件
- 🖼️ **极致图片提取**：使用MinerU (1200 DPI) 提取最高质量图片
- 🎨 **AI图片增强**：多层级智能增强（上采样+锐化+对比度+降噪）
- 📝 **标题识别**：自动从论文中提取真实标题
- 📁 **结构化输出**：创建以论文标题命名的文件夹
- 🔧 **错误处理**：内置重试机制和详细错误提示

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 网络连接（用于下载PDF）
- 足够的磁盘空间（用于存储PDF和图片）

### 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或手动安装核心依赖
pip install requests mineru[core] Pillow opencv-python numpy
```

### 验证安装

```bash
python lrm_paper_analyzer.py --help
```

## 📖 使用方法

### 基本用法

```bash
# 直接使用链接
python lrm_paper_analyzer.py https://arxiv.org/abs/"论文号"

# 使用参数形式
python lrm_paper_analyzer.py --url https://arxiv.org/pdf/"论文号"

# 指定输出目录
python lrm_paper_analyzer.py https://arxiv.org/abs/"论文号" --output papers --tmp temp
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `url` | arXiv论文链接（位置参数） | `https://arxiv.org/abs/论文号` |
| `--url` | arXiv论文链接（可选参数） | `--url https://arxiv.org/abs/论文号` |
| `--output` | 输出目录（默认：output） | `--output papers` |
| `--tmp` | 临时目录（默认：tmp） | `--tmp temp` |

### 支持的链接格式

- `https://arxiv.org/abs/论文号`
- `https://arxiv.org/pdf/论文号`
- `https://arxiv.org/pdf/论文号.pdf`

## 📁 输出结构

```
output/
└── 论文号/
    ├── 论文号.pdf
    ├── image_001.png
    ├── image_002.jpg
    ├── formula_003.png
    ├── diagram_004.svg
    └── ...
```

**结构说明：**
- 📁 **论文文件夹**：以论文标题命名（特殊字符安全处理）
- 📄 **PDF文件**：原始论文PDF文件
- 🖼️ **图片文件**：MinerU提取的所有图片（直接保存在同一文件夹）

## 🔧 技术特性

### 智能标题提取

工具会尝试从以下来源提取论文标题：
1. MinerU生成的markdown文件中的一级标题
2. 论文前几行中的标题模式匹配
3. 粗体标记的文本
4. 如果提取失败，使用arXiv ID作为备用

### 图片质量增强系统

#### 🎯 **MinerU极致提取参数**
- **渲染DPI**: 1200 DPI（超高分辨率）
- **图片DPI**: 1200 DPI（原始质量保持）
- **质量等级**: 100（最高质量）
- **矢量保持**: 保留矢量图形元素
- **无压缩**: 避免质量损失

#### 🚀 **AI多层级增强**
1. **智能上采样**: 小图片自动2倍分辨率提升（OpenCV CUBIC插值）
2. **锐化处理**: 1.3倍锐化增强，提升细节清晰度
3. **对比度优化**: 1.15倍对比度提升，增强视觉效果
4. **色彩饱和度**: 1.05倍色彩增强，图片更生动
5. **降噪处理**: 温和平滑滤波，减少噪点
6. **格式优化**: 保存为PNG无损格式

#### 📏 **智能过滤机制**
- ✅ **保留**：内容图片（公式、图表、架构图等）
- ❌ **过滤**：装饰性图片（页眉、页脚、logo等）
- 📏 **大小过滤**：跳过小于5KB的图片
- 🔍 **模式过滤**：根据文件名模式识别并过滤非内容图片

## 💡 使用示例

### 示例1：处理SATA论文

```bash
python lrm_paper_analyzer.py https://arxiv.org/abs/论文号
```

**输出：**
```
📥 开始处理arXiv论文: https://arxiv.org/abs/论文号
📄 论文ID: 论文号
📥 PDF下载链接: https://arxiv.org/pdf/论文号.pdf
⬇️ 正在下载PDF...
✅ PDF下载完成: output/.tmp/2412_15289.pdf
🖼️ 正在使用MinerU提取图片和论文标题...
🔄 正在使用MinerU提取图片（1200 DPI极致质量模式）...
✓ MinerU极致质量处理完成
✓ MinerU提取了 8 张图片到: output/.tmp/mineru_output/2412_15289/auto/images
✓ 提取到论文标题: 论文名字
📄 论文标题: 论文号
📁 正在整理输出文件...
    📈 高质量上采样: 652x392 → 1304x784
    ✨ 图片增强完成：锐化+对比度+降噪
✓ 复制并增强图片: image-0.png (45KB → 2996KB)
    📈 高质量上采样: 775x378 → 1550x756
    ✨ 图片增强完成：锐化+对比度+降噪
✓ 复制并增强图片: image-1.png (67KB → 3434KB)
...
✓ 共复制 8 张图片到: output/论文号

🎉 处理完成!
📂 输出目录: output/论文号
📄 PDF文件: 论文号.pdf
🖼️ 图片数量: 8 (全部AI增强)
📁 图片位置: 与PDF文件在同一目录

✅ 处理成功! 结果保存在: output
```

### 示例2：批量处理

```bash
# 创建脚本批量处理多个论文
cat > process_papers.sh << 'EOF'
#!/bin/bash
python lrm_paper_analyzer.py https://arxiv.org/abs/论文号
python lrm_paper_analyzer.py https://arxiv.org/abs/2411.18473
python lrm_paper_analyzer.py https://arxiv.org/abs/2410.12345
EOF

chmod +x process_papers.sh
./process_papers.sh
```

## 🔧 故障排除

### 常见问题

#### 1. MinerU未安装
```
未找到MinerU CLI。请安装MinerU (pip install mineru[core]) 并确保`mineru`命令可用。
```
**解决方案：**
```bash
pip install mineru[core]
# 或者升级到最新版本
pip install --upgrade mineru[core]
```

#### 2. 网络连接问题
```
requests.exceptions.ConnectionError
```
**解决方案：**
- 检查网络连接
- 确认能够访问arxiv.org
- 如使用代理，请正确配置

#### 3. 无效的arXiv链接
```
❌ 无效的arXiv链接: xxx
```
**解决方案：**
- 确认链接格式正确
- 支持的格式：abs、pdf
- 检查arXiv ID是否存在

#### 4. 权限问题
```
Permission denied
```
**解决方案：**
```bash
# 确保输出目录有写权限
chmod 755 output/
# 或指定其他目录
python lrm_paper_analyzer.py --output ~/papers https://arxiv.org/abs/论文号
```

### 调试信息

脚本提供详细的调试信息：
- ✅ 成功状态用绿色勾号
- ⚠️ 警告信息用黄色感叹号
- ❌ 错误信息用红色叉号
- 🔍 调试信息用放大镜图标

## 📂 项目结构

```
awesome/
├── lrm_paper_analyzer.py    # 主程序
├── README.md               # 项目说明文档
├── requirements.txt        # 项目依赖文件
├── output/                 # 输出目录（自动创建）
│   └── [论文标题]/         # 论文文件夹
│       ├── [标题].pdf      # PDF文件
│       └── *.png/jpg/svg   # 图片文件
└── tmp/                    # 临时文件（自动创建）
    ├── *.pdf              # 下载的PDF
    └── mineru_output/     # MinerU处理结果
```

## 🔄 工作流程

1. **解析链接** → 验证arXiv链接格式，提取论文ID
2. **下载PDF** → 从arXiv下载原始PDF文件
3. **极致提取** → 使用MinerU (1200 DPI) 解析PDF，提取最高质量图片和文本
4. **AI增强** → 多层级图片质量增强（上采样+锐化+对比度+降噪）
5. **识别标题** → 从解析结果中智能提取论文标题
6. **组织输出** → 创建标题文件夹，保存增强后的图片和PDF

## 🎯 设计理念

- **简单**：单一功能，专注做好PDF下载和图片提取
- **极致**：1200 DPI + AI多层级增强，提供市面最高图片质量
- **智能**：自动标题识别，智能文件组织，智能图片过滤
- **可靠**：错误处理，重试机制，详细日志

## 📄 许可证

本项目采用MIT许可证 - 详见LICENSE文件

## 🔗 相关链接

- [MinerU](https://github.com/opendatalab/MinerU) - PDF解析和图片提取工具
- [arXiv](https://arxiv.org/) - 学术论文预印本仓库

## 💡 使用建议

1. **网络环境**：确保网络稳定，避免下载中断
2. **存储空间**：预留足够空间，包含PDF和图片的完整论文包可能较大
3. **批量处理**：对于大量论文，建议编写脚本批量处理
4. **定期清理**：定期清理tmp目录以释放磁盘空间

---

🎯 **简单高效，专注核心功能！**