#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 打开文本查看器技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill
import pandas as pd


def _skill_open_text_viewer(df: pd.DataFrame) -> pd.DataFrame:
    """
    打开文本查看器 - 在文本查看器窗口中显示数据内容

    Args:
        df: 要显示的数据框

    Returns:
        原始数据框（不修改数据）
    """
    # 优化：如果数据框包含'大模型返回内容'列，只显示该列的第一行内容
    if '大模型返回内容' in df.columns:
        if not df.empty:
            # 获取大模型返回内容列的第一行值
            content = df['大模型返回内容'].iloc[0]
            # 确保内容是字符串类型
            if not isinstance(content, str):
                content = str(content)
        else:
            # 空数据框，只显示提示信息
            content = ""  # 或者可以显示 "无结果" 等提示
    else:
        # 否则显示整个数据框的文本表示
        content = df.to_string(index=False)
    
    from core.viewer import PROGRAM_display_content_in_textbox
    PROGRAM_display_content_in_textbox(content, edit='n')
    
    return df


class OpenTextViewerPlugin:
    """打开文本查看器技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="open_text_viewer",
            category=SkillCategory.VISUALIZE,
            description="打开文本查看器 - 在文本查看器窗口中显示数据内容，支持复制、导出等功能",
            function=_skill_open_text_viewer,
            parameters=[],
            examples=["在文本查看器中查看数据", "以文本格式显示数据"]
        ))


# 自动注册技能
OpenTextViewerPlugin.register()
