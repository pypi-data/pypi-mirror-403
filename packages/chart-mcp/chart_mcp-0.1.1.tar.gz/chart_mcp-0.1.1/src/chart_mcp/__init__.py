"""
MCP Server for generating performance comparison charts
支持生成性能对比图表，包括简单柱状图和分组柱状图
"""
import asyncio
import base64
import io
from pathlib import Path
from typing import Any, Sequence

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import numpy as np
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 导出版本信息
__version__ = "0.1.0"
__all__ = ["main", "app"]

app = Server("chart-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="generate_bar_chart",
            description="生成简单柱状图，用于对比两个值的性能指标",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "图表标题"
                    },
                    "y_label": {
                        "type": "string",
                        "description": "Y轴标签（单位）"
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "类别名称列表，如 ['bcc.g8.c32m128', 'S9pro.8XLARGE128']"
                    },
                    "values": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "对应的数值列表，长度需与categories相同"
                    },
                    "colors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选，柱状图颜色列表，默认使用蓝色和黄色",
                        "default": ["#1f77b4", "#ff7f0e"]
                    },
                    "output_path": {
                        "type": "string",
                        "description": "可选，保存图片的路径，如果不提供则返回base64编码"
                    }
                },
                "required": ["title", "y_label", "categories", "values"]
            }
        ),
        Tool(
            name="generate_grouped_bar_chart",
            description="生成分组柱状图，用于对比多个指标的性能",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "图表标题"
                    },
                    "y_label": {
                        "type": "string",
                        "description": "Y轴标签（单位）"
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "主类别名称列表，如 ['bcc.g8.c32m128', 'S9pro.8XLARGE128']"
                    },
                    "series_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "数据系列标签列表，如 ['#forward across 100 steps', '#forward-backward across 100 steps']"
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "二维数组，第一维对应categories，第二维对应series_labels。例如：[[133, 297], [118, 265]]"
                    },
                    "colors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选，柱状图颜色列表，默认使用蓝色和橙色",
                        "default": ["#1f77b4", "#ff7f0e"]
                    },
                    "output_path": {
                        "type": "string",
                        "description": "可选，保存图片的路径，如果不提供则返回base64编码"
                    }
                },
                "required": ["title", "y_label", "categories", "series_labels", "data"]
            }
        ),
        Tool(
            name="generate_chart_from_template",
            description="根据预定义的模板生成图表，支持常见的性能测试图表类型",
            inputSchema={
                "type": "object",
                "properties": {
                    "template": {
                        "type": "string",
                        "enum": ["ffmpeg", "vray", "alexnet", "openssl", "redis", "spec_cpu", "unixbench", "stream", "mlc"],
                        "description": "图表模板类型"
                    },
                    "data": {
                        "type": "object",
                        "description": "图表数据，格式根据模板类型而定"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "可选，保存图片的路径"
                    }
                },
                "required": ["template", "data"]
            }
        )
    ]


def save_chart_to_base64(fig) -> str:
    """将图表保存为base64编码的字符串"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return img_base64


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent]:
    """处理工具调用"""
    
    if name == "generate_bar_chart":
        return await generate_bar_chart(**arguments)
    elif name == "generate_grouped_bar_chart":
        return await generate_grouped_bar_chart(**arguments)
    elif name == "generate_chart_from_template":
        return await generate_chart_from_template(**arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def generate_bar_chart(
    title: str,
    y_label: str,
    categories: list[str],
    values: list[float],
    colors: list[str] | None = None,
    output_path: str | None = None
) -> Sequence[TextContent | ImageContent]:
    """生成简单柱状图"""
    if len(categories) != len(values):
        raise ValueError("categories和values的长度必须相同")
    
    # 使用更鲜艳的颜色，接近原始图片
    if colors is None:
        colors = ["#4472C4", "#FFC000"]  # 蓝色和金黄色
    
    # 确保有足够的颜色
    while len(colors) < len(categories):
        colors.extend(["#4472C4", "#FFC000"])
    
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='white')
    
    # 设置边框
    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1)
    
    bars = ax.bar(categories, values, color=colors[:len(categories)], width=0.6, edgecolor='none')
    
    # 在柱状图内部显示数值（居中显示）
    for i, (bar, value) in enumerate(zip(bars, values)):
        height = bar.get_height()
        # 统一使用黑色字体
        text_color = 'black'
        # 格式化数值，不简写
        if value == int(value):
            value_str = str(int(value))
        else:
            value_str = f'{value:.2f}'
        # 在柱状图内部居中显示（高度的一半位置）
        ax.text(bar.get_x() + bar.get_width()/2., height/2,
                value_str,
                ha='center', va='center', fontsize=12, fontweight='normal', color=text_color, family='sans-serif')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel(y_label, fontsize=11)
    ax.set_xlabel('')
    ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5, color='gray')
    ax.set_axisbelow(True)
    
    # 设置Y轴范围，留出一些空间
    y_max = max(values) * 1.15
    if y_max < max(values) + (max(values) - min(values)) * 0.2:
        y_max = max(values) + (max(values) - min(values)) * 0.2
    ax.set_ylim(0, y_max)
    
    # 设置Y轴刻度，自动调整间隔
    y_interval = max(5, int((y_max - 0) / 7))
    ax.set_yticks(range(0, int(y_max) + y_interval, y_interval))
    
    # 移除X轴刻度线
    ax.tick_params(axis='x', which='both', bottom=False, top=False)
    ax.tick_params(axis='y', which='both', left=True, right=False)
    
    # 添加图例在底部（居中）
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=colors[i], edgecolor='black', linewidth=0.5, label=cat) 
                      for i, cat in enumerate(categories)]
    # 使用 lower center 将图例放在底部
    legend = ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.15), 
                       ncol=len(categories), frameon=False, fontsize=10)
    
    # 调整布局，为底部图例留出空间，并确保图例不被裁剪
    plt.tight_layout(rect=[0, 0.12, 1, 0.98])
    
    if output_path:
        # 使用 bbox_extra_artists 确保图例不被裁剪
        fig.savefig(output_path, dpi=100, bbox_inches='tight', bbox_extra_artists=[legend], facecolor='white')
        plt.close(fig)
        return [TextContent(type="text", text=f"图表已保存到: {output_path}")]
    else:
        img_base64 = save_chart_to_base64(fig)
        plt.close(fig)
        return [ImageContent(type="image", data=img_base64, mimeType="image/png")]


async def generate_grouped_bar_chart(
    title: str,
    y_label: str,
    categories: list[str],
    series_labels: list[str],
    data: list[list[float]],
    colors: list[str] | None = None,
    output_path: str | None = None
) -> Sequence[TextContent | ImageContent]:
    """生成分组柱状图"""
    if len(data) != len(categories):
        raise ValueError("data的长度必须与categories相同")
    
    for row in data:
        if len(row) != len(series_labels):
            raise ValueError("data中每一行的长度必须与series_labels相同")
    
    # 使用更鲜艳的颜色
    if colors is None:
        colors = ["#4472C4", "#FFC000"]  # 蓝色和金黄色
    
    # 确保有足够的颜色
    while len(colors) < len(series_labels):
        colors.extend(["#70AD47", "#C00000", "#7030A0", "#8B4513"])
    
    x = np.arange(len(categories))
    n_series = len(series_labels)
    width = 0.35  # 柱状图宽度
    
    # 调整宽度以适应多个系列
    if n_series > 2:
        width = 0.7 / n_series
    
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    
    # 设置边框
    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1)
    
    # 计算每个系列的偏移量
    offsets = np.linspace(-width * (n_series - 1) / 2, width * (n_series - 1) / 2, n_series)
    
    bars_list = []
    for i, (label, color) in enumerate(zip(series_labels, colors[:n_series])):
        values = [row[i] for row in data]
        bars = ax.bar(x + offsets[i], values, width, label=label, color=color, 
                     edgecolor='none')
        bars_list.append(bars)
        
        # 在柱状图内部显示数值（居中显示）
        for j, (bar, value) in enumerate(zip(bars, values)):
            height = bar.get_height()
            # 统一使用黑色字体
            text_color = 'black'
            # 格式化数值，不简写
            if value == int(value):
                value_str = str(int(value))
            else:
                value_str = f'{value:.2f}'
            # 在柱状图内部居中显示
            ax.text(bar.get_x() + bar.get_width()/2., height/2,
                    value_str,
                    ha='center', va='center', fontsize=11, fontweight='normal', color=text_color, family='sans-serif')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel(y_label, fontsize=11)
    ax.set_xlabel('')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5, color='gray')
    ax.set_axisbelow(True)
    
    # 设置Y轴范围
    all_values = [val for row in data for val in row]
    y_max = max(all_values) * 1.2
    ax.set_ylim(0, y_max)
    
    # 设置Y轴刻度
    y_interval = max(5, int((y_max - 0) / 7))
    ax.set_yticks(range(0, int(y_max) + y_interval, y_interval))
    
    # 移除X轴刻度线
    ax.tick_params(axis='x', which='both', bottom=False, top=False)
    ax.tick_params(axis='y', which='both', left=True, right=False)
    
    # 添加图例在底部（居中）
    legend = ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=len(series_labels), 
                       frameon=False, fontsize=10)
    
    # 调整布局，为底部图例留出空间，并确保图例不被裁剪
    plt.tight_layout(rect=[0, 0.12, 1, 0.98])
    
    if output_path:
        # 使用 bbox_extra_artists 确保图例不被裁剪
        fig.savefig(output_path, dpi=100, bbox_inches='tight', bbox_extra_artists=[legend], facecolor='white')
        plt.close(fig)
        return [TextContent(type="text", text=f"图表已保存到: {output_path}")]
    else:
        img_base64 = save_chart_to_base64(fig)
        plt.close(fig)
        return [ImageContent(type="image", data=img_base64, mimeType="image/png")]


async def generate_chart_from_template(
    template: str,
    data: dict[str, Any],
    output_path: str | None = None
) -> Sequence[TextContent | ImageContent]:
    """根据模板生成图表"""
    templates = {
        "ffmpeg": {
            "title": "#ffmpeg编解码fps(单位: fps)",
            "y_label": "fps",
            "type": "bar"
        },
        "vray": {
            "title": "V-Ray视频离线渲染耗时(单位: second)",
            "y_label": "second",
            "type": "bar"
        },
        "alexnet": {
            "title": "alexnet性能(v2.10)",
            "y_label": "ms",
            "type": "grouped"
        },
        "openssl": {
            "title": "openssl加解密性能",
            "y_label": "ops",
            "type": "grouped"
        },
        "redis": {
            "title": "redis性能",
            "y_label": "rps",
            "type": "grouped"
        }
    }
    
    if template not in templates:
        raise ValueError(f"不支持的模板类型: {template}")
    
    template_config = templates[template]
    
    if template_config["type"] == "bar":
        return await generate_bar_chart(
            title=template_config["title"],
            y_label=template_config["y_label"],
            categories=data.get("categories", []),
            values=data.get("values", []),
            colors=data.get("colors"),
            output_path=output_path
        )
    elif template_config["type"] == "grouped":
        return await generate_grouped_bar_chart(
            title=template_config["title"],
            y_label=template_config["y_label"],
            categories=data.get("categories", []),
            series_labels=data.get("series_labels", []),
            data=data.get("data", []),
            colors=data.get("colors"),
            output_path=output_path
        )


async def async_main():
    """异步主函数 - MCP 服务器入口点"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """同步入口点 - 供命令行调用"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
