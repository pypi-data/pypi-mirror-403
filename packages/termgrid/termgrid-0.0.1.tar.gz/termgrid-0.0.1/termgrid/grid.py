from typing import List, Literal, Callable, Optional
from PIL import Image
from os import PathLike
import matplotlib.pyplot as plt
import numpy as np
import io

BinaryMatrix = List[List[Literal[0, 1]]]
ColorType = List[int, int, int]
ThresholdFunctionType = Callable[[tuple[int, int, int]], Literal[0, 1]]

GRID_DICT = {chr(code): [[1 if (code & c) else 0 for c in r] for r in [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]] for code in range(0x2800, 0x28FF + 1)}
DEFAULT_WIDTH = 100

class Grid:
    def __init__(self, binary_list: BinaryMatrix, color: Optional[ColorType] = None):
        self.binary_list = binary_list
        self.color = color

    def _binary_list_to_grid(self, binary_list: BinaryMatrix) -> str:
        grid_text = ""
        GRID_ROWS = 4  # 盲文点阵行数
        GRID_COLS = 2  # 盲文点阵列数
        
        total_rows = len(binary_list)
        if total_rows == 0:
            return ""
        total_cols = len(binary_list[0])

        # 先把字典反转成「点阵元组: 字符」的临时映射（仅做一次，提升效率）
        # 本质是用字典推导式实现"get"匹配的核心逻辑
        pattern_to_char = {tuple(tuple(row) for row in pat): char for char, pat in GRID_DICT.items()}

        # 按4行2列分块处理
        for row_start in range(0, total_rows, GRID_ROWS):
            # 读取/补全4行
            row_block = []
            for i in range(GRID_ROWS):
                if row_start + i < total_rows:
                    row_block.append(binary_list[row_start + i].copy())
                else:
                    row_block.append([0] * total_cols)
            
            # 按2列拆分，匹配字符
            for col_start in range(0, total_cols, GRID_COLS):
                # 提取/补全2列，生成4×2的点阵块
                grid_pattern = []
                for row in row_block:
                    col_slice: list = row[col_start:col_start + GRID_COLS]
                    while len(col_slice) < GRID_COLS:
                        col_slice.append(0)
                    grid_pattern.append(col_slice)
                
                # 转元组后用get匹配（核心！替代反向字典）
                pattern_tuple = tuple(tuple(row) for row in grid_pattern)
                grid_char = pattern_to_char.get(pattern_tuple, '⠀')  # 找不到则用空盲文
                grid_text += grid_char
            
            grid_text += "\n"  # 行块结束换行
        return grid_text
    
    def __str__(self):
        grid = self._binary_list_to_grid(self.binary_list)
        return f"\033[38;2;{self.color[0]};{self.color[1]};{self.color[2]}m{grid}\033[0m" if self.color else grid

class ImageGrid(Grid):
    def __init__(self, image: PathLike, threshold_fn: ThresholdFunctionType, width: int = DEFAULT_WIDTH, color: Optional[ColorType] = None):
        self.image = image
        self.threshold_fn = threshold_fn
        self.width = width
        self.color = color

    def _to_binary_list(self) -> BinaryMatrix:
        # 打开图片并转换为RGB模式
        img = Image.open(self.image).convert('RGB')
        
        # 计算目标尺寸：宽度为width*2，高度按原比例等比缩放
        original_width, original_height = img.size
        target_width = self.width * 2
        # 等比例计算高度，保留浮点数精度后转为整数
        target_height = int(original_height * (target_width / original_width))
        
        # 缩放图片（使用LANCZOS滤波器，缩放效果更清晰）
        img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 转换为numpy数组处理像素
        img_array = np.array(img_resized)
        h, w, _ = img_array.shape
        result = []
        
        # 遍历每个像素，通过阈值函数转为0/1
        for i in range(h):
            row = []
            for j in range(w):
                rgb_tuple = tuple(img_array[i, j])
                row.append(self.threshold_fn(rgb_tuple))
            result.append(row)
        
        return result

    def __str__(self):
        grid = self._binary_list_to_grid(self._to_binary_list())
        return f"\033[38;2;{self.color[0]};{self.color[1]};{self.color[2]}m{grid}\033[0m" if self.color else grid

class LaTeXGrid(ImageGrid):
    def __init__(self, latex: str, use_latex: bool = True, width: int = DEFAULT_WIDTH, color: Optional[ColorType] = None):
        super().__init__(
            image=self._generate_latex_image(latex, use_latex),
            threshold_fn=lambda rgb: 1 if (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) < 128 else 0,
            width=width,
            color=color
        )

    def _generate_latex_image(self, latex, use_latex) -> str:
        # 配置matplotlib以支持LaTeX渲染（如果启用）
        if use_latex:
            plt.rcParams['text.usetex'] = True
            plt.rcParams['font.family'] = 'serif'
            plt.rcParams['font.serif'] = ['Computer Modern Roman']
        else:
            plt.rcParams['text.usetex'] = False

        DPI = 300
        # 核心生成逻辑（直接执行，无函数封装）
        # 1. 创建绘图对象并渲染公式
        fig, ax = plt.subplots(figsize=(1, 1), dpi=DPI)
        fig.patch.set_facecolor('white')  # 白色背景
        ax.patch.set_facecolor('white')
        ax.axis('off')  # 隐藏坐标轴

        # 渲染LaTeX公式
        text = ax.text(0.5, 0.5, f'${latex}$',
                    ha='center', va='center',
                    fontsize=20, color='black')

        # 2. 精准计算公式边界（防止裁切）
        fig.canvas.draw()
        # 使用tightbbox获取更准确的公式边界
        bbox = text.get_tightbbox(fig.canvas.get_renderer())
        bbox = bbox.transformed(ax.transData.inverted())

        # 手动扩展边界，避免公式边缘被裁切
        expand_ratio = 0.05
        ax.set_xlim(bbox.xmin - expand_ratio, bbox.xmax + expand_ratio)
        ax.set_ylim(bbox.ymin - expand_ratio, bbox.ymax + expand_ratio)

        # 3. 将图片保存到内存（不写入文件）
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=DPI,
                    bbox_inches='tight', pad_inches=0,
                    transparent=False)  # 强制白色背景
        buf.seek(0)
        plt.close()  # 关闭绘图对象释放内存

        # 4. 裁剪图片到公式实际范围（带安全边距）
        img = Image.open(buf).convert('RGB')  # 转为RGB，去除Alpha通道
        img_array = np.array(img)

        # 找到所有非白色像素的区域
        non_white_pixels = np.any(img_array < 250, axis=2)
        # 获取非白色像素的行/列索引
        non_white_rows = np.where(np.any(non_white_pixels, axis=1))[0]
        non_white_cols = np.where(np.any(non_white_pixels, axis=0))[0]

        # 计算裁剪边界（应用安全边距）
        if len(non_white_rows) == 0 or len(non_white_cols) == 0:
            # 极端情况：无有效像素，直接保存原图
            cropped_img = img
        else:
            SAFE_MARGIN = 2
            y_min = max(0, non_white_rows[0] - SAFE_MARGIN)
            y_max = min(img.height, non_white_rows[-1] + SAFE_MARGIN)
            x_min = max(0, non_white_cols[0] - SAFE_MARGIN)
            x_max = min(img.width, non_white_cols[-1] + SAFE_MARGIN)
            # 裁剪图片
            cropped_img = img.crop((x_min, y_min, x_max, y_max))

        # 5. 保存最终图片
        IMAGE_NAME = "latex.png"
        cropped_img.save(IMAGE_NAME, dpi=(DPI, DPI))
        return IMAGE_NAME
