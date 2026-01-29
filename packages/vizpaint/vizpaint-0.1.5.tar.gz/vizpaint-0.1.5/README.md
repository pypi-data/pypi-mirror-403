

# vizpaint

[![PyPI version](https://img.shields.io/pypi/v/vizpaint.svg)](https://pypi.org/project/vizpaint/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/vizpaint.svg)](https://pypi.org/project/vizpaint/)

**vizpaint** 是一个强大、易用、功能全面的 Python 数据可视化库。它基于 Matplotlib 构建，集成了从经典的 2D 图表到令人惊艳的 3D 图形在内的数十种绘图功能，旨在通过极简的 API 让数据可视化变得既简单又专业。

## ✨ 核心特性

*   **📊 丰富的图表类型**：一站式提供柱状图、饼图、散点图、雷达图、玫瑰图、热力图、3D曲面图、3D散点图、桑基图等数十种专业图表。
*   **🚀 极简的 API 设计**：大部分复杂图表只需一行核心代码即可生成，大幅降低学习与使用成本。
*   **🎨 深度的定制能力**：从颜色、标签到视角、光照，提供近乎所有可视化元素的参数控制，满足从探索到出版的全流程需求。
*   **🌌 卓越的 3D 支持**：内置多种 3D 绘图函数，并支持交互式视角调整，轻松创建三维数据可视化。
*   **🔄 无缝的生态集成**：完美兼容 `NumPy` 数组和 `Pandas` `DataFrame`，流畅融入你的数据分析工作流。

## 🆕 v0.2.0 新功能亮点


*   **增强版玫瑰图**: 支持生长动画、统计信息显示、智能高亮，让商业演示更具吸引力。
*   **桑基图 (Sankey)**: 全新图表类型，完美展示流程、能源或资金流动。

对于 v0.2.0 的新功能，建议同时安装 pandas 以获得最佳体验：

对于 v0.2.0 的新功能，建议同时安装 pandas 以获得最佳体验：


```bash
pip install vizpaint pandas
```
## 📦 安装

通过 pip 一键安装：

```bash
pip install vizpaint
```
## ⚡ 快速入门

1. 基础图表 (一行代码)

```python
import vizpaint
import numpy as np

# 绘制一个精美的南丁格尔玫瑰图
fig1, ax1, _ = vizpaint.rose_chart(
    values=[15, 22, 18, 25, 12, 30],
    categories=[\'A\', \'B\', \'C\', \'D\', \'E\', \'F\'''],
    title="销售数据玫瑰图"
)

# 绘制一个动态的 3D 正弦曲面
fig2, ax2, _ = paint.surface_3d(
    title="3D 正弦曲面",
    cmap=\'plasma\'
)

# 显示所有图表
paint.show_all()
```
2增强版玫瑰图 (新功能)

```python
import vizpaint

# 创建增强版玫瑰图，带动画和统计信息
fig, ax, wedges, anim = vizpaint.rose_chart_enhanced(
    values=[42, 35, 28, 50, 38, 45, 32],
    categories=[\'产品A\', \'产品B\', \'产品C\', \'产品D\', \'产品E\', \'产品F\', \'产品G\'],
    title="产品市场份额分布",
    animation=True,      # 启用生长动画
    duration=2,          # 动画时长2秒
    show_stats=True,     # 显示统计信息
    sort_by_value=True,  # 按值排序
    highlight_top=3,     # 高亮前3名
    explode=True         # 突出显示高亮项
)

# 保存动画（可选）
# anim.save(\'rose_chart_animation.gif\', writer=\'pillow\', fps=30)

vizpaint.show_all()
```
5. 桑基图 (新功能)

```python
import vizpaint

# 创建能源流动桑基图
fig, ax, sankey = vizpaint.create_simple_sankey()

# 或者创建自定义桑基图
flows = [1.0, -0.5, -0.3, -0.2, 0.5, -0.3, -0.2]
labels = [\'总预算\', \'研发\', \'市场\', \'运营\', \'研发预算\', \'人力\', \'设备\']

fig2, ax2, sankey2 = paint.sankey_diagram(
    flows=flows,
    labels=labels,
    title="公司预算分配流程图",
    color_palette=\'Set2\',
    margin=0.3
)

vizpaint.show_all()
```


# 基础图表


* 玫瑰图	展示周期性或类别数据	`Pandasvizpaint.rose_chart(values, categories)`
* 3D曲面图	三维函数可视化	`vizpaint.surface_3d()`
* 条形图	比较类别数据	`vizpaint.bar_chart(categories, values)`
* 散点图	展示数据分布与关系	`vizpaint.scatter_plot(x, y)`
# v0.2.0 新增图表


* 高级3D曲面	支持函数、线框、等高线	`vizpaint.surface_3d_advanced(func=my_func)`
* 增强玫瑰图	带动画和统计信息	`vizpaint.rose_chart_enhanced(animation=True)`
* 桑基图	流量与资源流动可视化	`vizpaint.sankey_diagram(flows, labels)`
# 📚 API 参考

## 主要函数：

### 基础图表

* `rose_chart(values, categories, title, colors)` - 绘制南丁格尔玫瑰图
* `surface_3d(x, y, z, title, cmap)` - 绘制3D曲面图
* `bar_chart(data, x, y, title, color)` - 绘制条形图（支持DataFrame）
* `scatter_3d(x, y, z, c, title)` - 绘制3D散点图
* `pie_chart(labels, sizes, title, colors)` - 绘制饼图
* `histogram(data, bins, title)` - 绘制直方图
* `box_plot(data_list, labels, title)` - 绘制箱线图
* `heatmap(data, title, cmap)` - 绘制热力图
* `radar_chart(categories, values, title)` - 绘制雷达图
### v0.2.0 新增函数

* `rose_chart_enhanced(values, categories, animation, show_stats)` - 增强版玫瑰图
* `sankey_diagram(flows, labels, title, color_palette)` - 桑基图

## 工具函数

* `show_all()` - 显示所有已创建的图表
* `set_style(style)` - 设置图表样式 ('default', 'dark', 'ggplot', 'seaborn')
* `save_figure`(fig, filename, dpi) - 保存图表到文件
* `clear_all()` - 清除所有图表
# 🔧 高级用法

### 图表定制与组合

```python
import vizpaint
import numpy as np

# 创建子图组合
fig, axes = vizpaint.create_subplots(2, 2, figsize=(14, 10))

# 子图1：3D曲面
ax1 = axes[0]
x = np.linspace(-5, 5, 100)
y = np.linspace(-5, 5, 100)
x, y = np.meshgrid(x, y)
z = np.sin(np.sqrt(x**2 + y**2))
ax1.plot_surface(x, y, z, cmap=\'viridis\')
ax1.set_title("3D曲面子图")

# 子图2：玫瑰图
ax2 = axes[1]
vizpaint.rose_chart([20, 30, 25, 15], ax=ax2)
ax2.set_title("玫瑰图子图")

# 设置整体标题
fig.suptitle("多图表组合展示", fontsize=16, fontweight=\'bold\')

vizpaint.show_all()
```
### 批量处理与导出

```python
import vizpaint
import pandas as pd
from pathlib import Path

# 批量生成图表
def generate_report(dataframes, output_dir="report"):
    Path(output_dir).mkdir(exist_ok=True)
    
    for i, df in enumerate(dataframes):
        # 创建多种图表
        fig1, _, _ = vizpaint.bar_chart(df, x=\'category\', y=\'value\')
        fig2, _, _ = vizpaint.rose_chart(df[\'value\'].tolist())
        
        # 保存图表
        fig1.savefig(f"{output_dir}/chart_{i}_bar.png", dpi=300, bbox_inches=\'tight\')
        fig2.savefig(f"{output_dir}/chart_{i}_rose.png", dpi=300, bbox_inches=\'tight\')
        
        vizpaint.clear_all()
    
    print(f"报告已生成到 {output_dir} 目录")
```
# 🛠️ 项目结构



```text
vizpaint/
├── __init__.py              # 包入口和主要API
├── bar_chart.py             # 条形图
├── pie_chart.py             # 饼图
├── scatter_plot.py          # 散点图
├── rose_chart.py            # 玫瑰图
├── rose_chart_enhanced.py   # 增强版玫瑰图 (v0.2.0)
├── surface_3d.py            # 3D曲面图
├── surface_3d_advanced.py   # 高级3D曲面图 (v0.2.0)
├── sankey_diagram.py        # 桑基图 (v0.2.0)
├── heatmap.py               # 热力图
├── histogram.py             # 直方图
├── box_plot.py              # 箱线图
├── radar_chart.py           # 雷达图
├── three_d_charts.py        # 其他3D图表
└── utils.py                 # 工具函数
```
# 🤝 如何贡献


我们欢迎所有形式的贡献！

* 1.报告问题：如果你发现了 Bug，或有新功能建议，请在 GitHub Issues 中提出。
* 2.提交代码：请 Fork 本仓库，创建功能分支，提交清晰的 Pull Request。
* 3.改进文档：即使是修正一个错别字也是非常有价值的贡献！
### 开发环境设置

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/vizpaint.git
cd vizpaint

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\\Scripts\\activate  # Windows

# 3. 安装开发依赖
pip install -e .[dev]  # 假设在setup.py中配置了extra_require
```
