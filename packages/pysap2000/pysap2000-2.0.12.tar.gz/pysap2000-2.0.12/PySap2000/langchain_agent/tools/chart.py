# -*- coding: utf-8 -*-
"""
通用绑图工具 - 支持多种图表类型和风格
"""

from langchain.tools import tool
import json


@tool
def draw_chart(
    data: str,
    chart_type: str = "bar",
    title: str = "",
    style: str = "default",
    show_values: bool = True,
    show_legend: bool = True,
    x_label: str = "",
    y_label: str = ""
) -> str:
    """
    通用绑图工具，根据数据绑制各种图表。
    
    Args:
        data: JSON 格式的数据，格式为 [{"name": "类别1", "value": 100}, {"name": "类别2", "value": 200}, ...]
        chart_type: 图表类型 - "bar"(柱状图), "pie"(饼图), "line"(折线图), "hbar"(横向柱状图)
        title: 图表标题
        style: 风格 - "default"(默认), "dark"(深色), "colorful"(多彩), "minimal"(简约)
        show_values: 是否在图表上显示数值标签
        show_legend: 是否显示图例
        x_label: X 轴标签（柱状图/折线图）
        y_label: Y 轴标签（柱状图/折线图）
    
    Returns:
        包含图表图片的 JSON，前端会自动显示
    
    示例:
        draw_chart(data='[{"name":"A","value":10},{"name":"B","value":20}]', chart_type="bar", title="示例图表")
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO
        
        # 解析数据
        try:
            chart_data = json.loads(data)
        except:
            return json.dumps({"错误": "数据格式错误，需要 JSON 数组"}, ensure_ascii=False)
        
        if not chart_data or not isinstance(chart_data, list):
            return json.dumps({"错误": "数据为空或格式不正确"}, ensure_ascii=False)
        
        names = [d.get("name", str(i)) for i, d in enumerate(chart_data)]
        values = [d.get("value", 0) for d in chart_data]
        
        # 风格配置
        styles = {
            "default": {
                "colors": ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'],
                "bg": "white",
                "text": "black",
                "grid": "#e5e7eb"
            },
            "dark": {
                "colors": ['#34d399', '#60a5fa', '#fbbf24', '#f87171', '#a78bfa', '#f472b6', '#22d3ee', '#a3e635'],
                "bg": "#1f2937",
                "text": "white",
                "grid": "#374151"
            },
            "colorful": {
                "colors": ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40', '#c9cbcf', '#7bc225'],
                "bg": "white",
                "text": "black",
                "grid": "#e5e7eb"
            },
            "minimal": {
                "colors": ['#6b7280', '#9ca3af', '#d1d5db', '#e5e7eb', '#f3f4f6', '#f9fafb', '#4b5563', '#374151'],
                "bg": "white",
                "text": "#374151",
                "grid": "#f3f4f6"
            }
        }
        s = styles.get(style, styles["default"])
        
        # 设置字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor(s["bg"])
        ax.set_facecolor(s["bg"])
        
        colors = [s["colors"][i % len(s["colors"])] for i in range(len(names))]
        
        # 绘制不同类型的图表
        if chart_type == "bar":
            bars = ax.bar(names, values, color=colors, edgecolor='white', linewidth=1)
            if show_values:
                for bar, val in zip(bars, values):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                           f'{val}', ha='center', va='bottom', fontsize=10, color=s["text"])
            if x_label:
                ax.set_xlabel(x_label, fontsize=11, color=s["text"])
            if y_label:
                ax.set_ylabel(y_label, fontsize=11, color=s["text"])
            ax.tick_params(colors=s["text"])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            for spine in ax.spines.values():
                spine.set_color(s["grid"])
                
        elif chart_type == "hbar":
            bars = ax.barh(names, values, color=colors, edgecolor='white', linewidth=1)
            if show_values:
                for bar, val in zip(bars, values):
                    ax.text(bar.get_width() + max(values)*0.02, bar.get_y() + bar.get_height()/2,
                           f'{val}', ha='left', va='center', fontsize=10, color=s["text"])
            if x_label:
                ax.set_xlabel(x_label, fontsize=11, color=s["text"])
            if y_label:
                ax.set_ylabel(y_label, fontsize=11, color=s["text"])
            ax.tick_params(colors=s["text"])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            for spine in ax.spines.values():
                spine.set_color(s["grid"])
                
        elif chart_type == "pie":
            wedges, texts, autotexts = ax.pie(
                values, 
                labels=names if show_legend else None,
                autopct='%1.1f%%' if show_values else None,
                colors=colors,
                startangle=90
            )
            for text in texts + autotexts:
                text.set_color(s["text"])
            if show_legend and len(names) > 8:
                ax.legend(wedges, [f"{n}: {v}" for n, v in zip(names, values)],
                         loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9)
                         
        elif chart_type == "line":
            ax.plot(names, values, marker='o', color=s["colors"][0], linewidth=2, markersize=8)
            if show_values:
                for i, (n, v) in enumerate(zip(names, values)):
                    ax.text(i, v + max(values)*0.03, f'{v}', ha='center', fontsize=10, color=s["text"])
            if x_label:
                ax.set_xlabel(x_label, fontsize=11, color=s["text"])
            if y_label:
                ax.set_ylabel(y_label, fontsize=11, color=s["text"])
            ax.tick_params(colors=s["text"])
            ax.grid(True, alpha=0.3, color=s["grid"])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            for spine in ax.spines.values():
                spine.set_color(s["grid"])
        else:
            return json.dumps({"错误": f"不支持的图表类型: {chart_type}"}, ensure_ascii=False)
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', color=s["text"])
        
        plt.tight_layout()
        
        # 保存为 base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight', facecolor=s["bg"])
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        
        print(f"[draw_chart] 图表已生成: type={chart_type}, style={style}, 数据点={len(names)}")
        
        return json.dumps({
            "结果": "图表已生成",
            "类型": chart_type,
            "数据点数": len(names),
            "__image__": f"data:image/png;base64,{img_base64}"
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"错误": f"绑图失败: {str(e)}"}, ensure_ascii=False)
