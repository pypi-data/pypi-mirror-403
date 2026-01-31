# termgrid

`termgrid` 是一个轻量级 Python 库，能够将图片、LaTeX 公式或自定义二进制矩阵转换为终端可显示的盲文点阵字符，让你在命令行中可视化图像和数学公式。

详见 [ZhuChongjing/termgrid](https://github.com/ZhuChongjing/termgrid)。

## 特性

- 将任意图片转换为终端盲文点阵
- 渲染 LaTeX 公式为终端盲文点阵
- 支持自定义终端显示颜色
- 可配置输出宽度和阈值函数
- 高效的点阵匹配算法，支持任意尺寸的输入

## 安装

### 前置依赖
确保你的系统已安装以下依赖包：

```bash
pip install pillow matplotlib numpy
```

> **注意**：如果需要渲染 LaTeX 公式，还需在系统中安装 LaTeX 环境（如 TeX Live、MikTeX 或 MacTeX）。

### 安装方式
使用 pip 安装 `termgrid`：

```bash
pip install termgrid
```

## 快速开始

### 1. 基础用法：图片转盲文点阵
```python
from termgrid import ImageGrid

# 定义灰度阈值函数（RGB转黑白）
def threshold(rgb):
    # 计算灰度值，小于128则为1（显示盲文点），否则为0
    gray = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return 1 if gray < 128 else 0

# 创建图片网格对象（指定图片路径、阈值函数、宽度、颜色）
img_grid = ImageGrid(
    image="your_image.png",
    threshold_fn=threshold,
    width=50,  # 输出宽度（盲文字符数）
    color=[255, 0, 0]  # 红色显示（RGB）
)

# 在终端打印盲文点阵
print(img_grid)
```

### 2. LaTeX 公式转盲文点阵
```python
from termgrid import LaTeXGrid

# 创建LaTeX网格对象
latex_grid = LaTeXGrid(
    latex=r"\sum_{i=1}^n i = \frac{n(n+1)}{2}",  # LaTeX公式
    use_latex=True,  # 启用LaTeX渲染（需系统安装LaTeX）
    width=80,        # 输出宽度
    color=[0, 255, 0]  # 绿色显示
)

# 打印LaTeX公式的盲文点阵
print(latex_grid)
```

### 3. 自定义二进制矩阵转盲文点阵
```python
from termgrid import Grid

# 自定义4x4二进制矩阵（1表示显示点，0表示不显示）
custom_matrix = [
    [1, 0, 1, 0],
    [0, 1, 0, 1],
    [1, 0, 1, 0],
    [0, 1, 0, 1]
]

# 创建网格对象
custom_grid = Grid(
    binary_list=custom_matrix,
    color=[0, 0, 255]  # 蓝色显示
)

# 打印自定义点阵
print(custom_grid)
```

## API 参考

### 核心类型
| 类型名 | 定义 | 说明 |
|--------|------|------|
| `BinaryMatrix` | `List[List[Literal[0, 1]]]` | 二进制矩阵，1表示显示点，0表示不显示 |
| `ColorType` | `List[int, int, int]` | RGB颜色值，范围0-255 |
| `ThresholdFunctionType` | `Callable[[tuple[int, int, int]], Literal[0, 1]]` | 阈值函数，接收RGB元组，返回0或1 |

### Grid 类（基础类）
#### 构造函数
```python
Grid(binary_list: BinaryMatrix, color: Optional[ColorType] = None)
```
- `binary_list`: 二进制矩阵数据
- `color`: 可选，RGB颜色值，用于终端彩色显示

#### 主要方法
- `__str__()`: 返回格式化的盲文点阵字符串（带颜色编码）
- `_binary_list_to_grid()`: 内部方法，将二进制矩阵转换为盲文字符串

### ImageGrid 类（图片处理）
继承自 `Grid` 类，用于处理图片转换。

#### 构造函数
```python
ImageGrid(image: PathLike, threshold_fn: ThresholdFunctionType, width: int = 100, color: Optional[ColorType] = None)
```
- `image`: 图片文件路径
- `threshold_fn`: 阈值函数，用于将RGB像素转换为0/1
- `width`: 输出宽度（盲文字符数），默认100
- `color`: 可选，RGB颜色值

#### 主要方法
- `_to_binary_list()`: 内部方法，将图片转换为二进制矩阵

### LaTeXGrid 类（LaTeX处理）
继承自 `ImageGrid` 类，用于处理LaTeX公式转换。

#### 构造函数
```python
LaTeXGrid(latex: str, use_latex: bool = True, width: int = 100, color: Optional[ColorType] = None)
```
- `latex`: LaTeX公式字符串（无需包裹$，内部会自动添加）
- `use_latex`: 是否启用LaTeX渲染，默认True
- `width`: 输出宽度，默认100
- `color`: 可选，RGB颜色值

#### 主要方法
- `_generate_latex_image()`: 内部方法，生成LaTeX公式的图片并保存为`latex.png`

## 高级用法

### 自定义阈值函数
你可以根据需求自定义阈值函数，实现不同的效果：

```python
# 只保留红色通道的阈值函数
def red_channel_threshold(rgb):
    # 只检测红色分量，大于150则显示点
    return 1 if rgb[0] > 150 else 0

# 反相显示的阈值函数
def invert_threshold(rgb):
    gray = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return 0 if gray < 128 else 1  # 反转黑白

# 使用自定义阈值函数
img_grid = ImageGrid(
    image="test.png",
    threshold_fn=red_channel_threshold,
    width=60
)
```

### 调整输出宽度
输出宽度决定了盲文点阵的精细程度，宽度越大，细节越丰富：

```python
# 低分辨率（快速显示）
low_res = ImageGrid("image.jpg", threshold, width=30)

# 高分辨率（细节丰富）
high_res = ImageGrid("image.jpg", threshold, width=120)
```

## 注意事项

1. **LaTeX 渲染**：
   - 启用 `use_latex=True` 时，需确保系统已安装LaTeX环境
   - 复杂公式可能需要调整 `fontsize` 参数（在 `_generate_latex_image` 方法中）
   - 生成的 `latex.png` 文件会覆盖同名文件

2. **终端兼容性**：
   - 部分终端可能不支持24位真彩色，颜色参数可能无效
   - 盲文字符显示效果因终端字体而异，建议使用支持Unicode的终端（如iTerm2、Windows Terminal）

3. **性能**：
   - 处理大尺寸图片或高宽度值时，转换时间会增加
   - 建议根据终端窗口大小调整宽度参数
