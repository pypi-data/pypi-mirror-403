#!/usr/bin/env python
# -*- coding: utf-8 -*-
# LLM调用技能插件

from core.skills import Skill, SkillCategory, SkillParameter, register_skill, SkillResult

def _skill_llm_call(df, prompt: str = "", model: str = "gpt-3.5-turbo", 
                   temperature: float = 0.7, mode: str = "table", selected_columns: list = None, token_1: str = None, 
                   selected_model: str = None, model_config: dict = None, return_format_config: dict = None,
                   system_prompt: str = "", user_prompt: str = "", reference_material: str = "",
                   table_default_prompt_fixed: str = "", batch_size: int = 1, sample_size: int = None,
                   filter_condition: dict = None) -> dict:
    """
    LLM调用 - 调用大语言模型API，支持文本生成、表格分析等多种模式

    Args:
        df: 输入数据框，包含要分析的实际数据内容
        prompt: 提示词，用于指导LLM生成内容
        model: 模型名称（可选，默认为gpt-3.5-turbo，实际使用配置文件中的模型）
        temperature: 温度参数，控制输出随机性，范围0-2
        mode: 调用模式，支持三种模式：
            - table（整表分析）：发送整个表格内容进行分析
            - row（逐行分析）：逐行发送数据进行分析
            - doc（文档分析）：将表格作为文档进行分析
        selected_columns: 选择要分析的列名列表，空列表表示使用所有列
        token_1: API密钥，用于调用LLM API
        selected_model: 选择的模型名称，优先使用配置文件中的模型
        model_config: 模型配置字典，包含API URL、模型名称等
        return_format_config: 返回格式配置，控制LLM返回的结果格式
        system_prompt: 系统提示词，定义LLM的角色和行为
        user_prompt: 用户提示词，与prompt参数功能相同，优先级更高
        reference_material: 参考材料，提供给LLM的额外信息
        table_default_prompt_fixed: 表格分析默认提示词，用于指导LLM分析表格
        batch_size: 批量处理大小，仅在row模式下有效
        sample_size: 采样大小，用于限制发送给LLM的数据量
        filter_condition: 数据过滤条件，用于筛选要分析的数据行

    Returns:
        SkillResult包含LLM响应文本或分析结果
        - success: 调用是否成功
        - data: 包含result_type和data字段
            - result_type: 结果类型，"text"或"table"
            - data: 结果数据，文本或数据框
        - message: 调用结果的描述信息
    """
    import json
    import os
    import pandas as pd

    from core.llm2 import LLM_Functions

    # 1. 参数验证
    if not prompt and not user_prompt:
        return SkillResult(
            success=False,
            data=None,
            message="提示词不能为空，请提供prompt或user_prompt参数"
        )

    if df is None:
        return SkillResult(
            success=False,
            data=None,
            message="输入数据框不能为空"
        )

    if not isinstance(df, pd.DataFrame):
        return SkillResult(
            success=False,
            data=None,
            message="输入必须是DataFrame类型"
        )

    if df.empty:
        return SkillResult(
            success=False,
            data=None,
            message="输入数据框为空，无法进行分析"
        )

    # 2. 数据处理
    processed_df = df.copy()
    
    # 2.1 应用过滤条件
    if filter_condition:
        try:
            # 简单的列值过滤，支持等于、大于、小于等操作
            for col, condition in filter_condition.items():
                if isinstance(condition, dict):
                    for op, value in condition.items():
                        if op == 'eq':
                            processed_df = processed_df[processed_df[col] == value]
                        elif op == 'gt':
                            processed_df = processed_df[processed_df[col] > value]
                        elif op == 'lt':
                            processed_df = processed_df[processed_df[col] < value]
                        elif op == 'gte':
                            processed_df = processed_df[processed_df[col] >= value]
                        elif op == 'lte':
                            processed_df = processed_df[processed_df[col] <= value]
                        elif op == 'contains':
                            processed_df = processed_df[processed_df[col].str.contains(value, na=False)]
                else:
                    # 默认为等于操作
                    processed_df = processed_df[processed_df[col] == condition]
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                message=f"应用过滤条件失败: {str(e)}"
            )
    
    # 2.2 数据采样
    if sample_size and len(processed_df) > sample_size:
        processed_df = processed_df.sample(n=sample_size, random_state=42)
    
    # 2.3 列选择
    if selected_columns is None or not selected_columns:
        selected_columns = processed_df.columns.tolist()
    else:
        # 验证所选列是否存在
        missing_columns = [col for col in selected_columns if col not in processed_df.columns]
        if missing_columns:
            return SkillResult(
                success=False,
                data=None,
                message=f"所选列不存在: {', '.join(missing_columns)}"
            )
        # 选择指定列
        processed_df = processed_df[selected_columns]
    
    # 3. 模型配置处理
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'settings', 'model_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            models = config.get('models', [])
    except Exception as e:
        return SkillResult(
            success=False,
            data=None,
            message=f"读取模型配置文件失败: {str(e)}"
        )

    # 如果未提供selected_model，使用model参数
    if not selected_model:
        selected_model = model

    # 如果未提供model_config，从配置文件中获取，与agent保持一致
    if not model_config:
        # 与agent保持一致：先查找匹配模型，未找到则使用第一个模型
        selected_model_config = None
        
        # 1. 先根据selected_model或model参数查找匹配的模型配置
        for m in models:
            # 支持按名称或模型ID匹配，与agent保持一致
            if m.get('name') == selected_model or m.get('model') == selected_model:
                selected_model_config = m
                break
        
        # 2. 如果没有找到匹配的模型，使用第一个模型作为默认模型，与agent保持一致
        if not selected_model_config:
            if models:
                selected_model_config = models[0]
                selected_model = selected_model_config.get('name', '')
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    message="未找到任何已配置的模型，请先在设置中添加模型配置"
                )

        # 3. 构建model_config字典，与agent保持一致的配置格式
        model_config = {
            'url': selected_model_config.get('url', ''),
            'model_name': selected_model_config.get('model', ''),
            'temperature': temperature,
            'system_prompt': system_prompt,
            'max_tokens': selected_model_config.get('max_tokens', 8000),
            'top_p': selected_model_config.get('top_p', 0.9),
            'frequency_penalty': selected_model_config.get('frequency_penalty', 1.0),
            'presence_penalty': selected_model_config.get('presence_penalty', 1.0),
            'stream': selected_model_config.get('stream', False),
            'enable_r1_thinking': selected_model_config.get('enable_r1_thinking', False),
            'enable_web_search': selected_model_config.get('enable_web_search', False),
            'user_prompt': user_prompt,
            'reference_material': reference_material
        }
        
        # 4. 如果未提供token_1，从配置中获取，与agent保持一致
        if not token_1:
            token_1 = selected_model_config.get('api_key', '')
    else:
        # 如果提供了model_config，确保temperature参数被正确设置
        model_config['temperature'] = temperature

    # 4. 构建最终参数字典
    params = {
        'mode': mode,
        'selected_columns': selected_columns,
        'token_1': token_1,
        'selected_model': selected_model,
        'model_config': model_config,
        'return_format_config': return_format_config or {},
        'system_prompt': system_prompt,
        'user_prompt': user_prompt or prompt,
        'reference_material': reference_material,
        'table_default_prompt_fixed': table_default_prompt_fixed,
        'batch_size': batch_size
    }

    # 5. 调用LLM_Functions的process_data方法
    llm = LLM_Functions()
    result = llm.process_data(processed_df, params)

    # 6. 处理返回结果，确保始终返回表格类型
    # 如果llm2.py返回错误，直接返回错误结果
    if 'error' in result:
        return SkillResult(
            success=False,
            data=None,
            message=result['error']
        )
    
    # 确保返回结果包含result_type和data字段
    if 'result_type' not in result or 'data' not in result:
        return SkillResult(
            success=False,
            data=None,
            message="LLM返回格式不正确，缺少必要字段"
        )
    
    # 处理不同类型的结果
    if result['result_type'] == 'table':
        # 表格类型直接返回DataFrame，与其他技能保持一致
        return SkillResult(
            success=True,
            data=result['data'],
            message="LLM调用成功，返回表格结果"
        )
    elif result['result_type'] == 'text':
        # 文本类型转换为DataFrame，只有一列一行
        import pandas as pd
        text_data = result['data']
        # 创建只有一列一行的DataFrame
        text_df = pd.DataFrame([[text_data]], columns=['大模型返回内容'])
        return SkillResult(
            success=True,
            data=text_df,
            message="LLM调用成功，返回文本结果已转换为表格"
        )
    else:
        # 其他类型，转换为DataFrame
        import pandas as pd
        other_data = result['data']
        # 创建只有一列一行的DataFrame
        other_df = pd.DataFrame([[str(other_data)]], columns=['大模型返回内容'])
        return SkillResult(
            success=True,
            data=other_df,
            message="LLM调用成功，返回其他类型结果已转换为表格"
        )


class LlmCallPlugin:
    """LLM调用技能插件"""

    author = "Randy"
    version = "1.0.0"

    @staticmethod
    def register() -> None:
        """注册技能"""
        register_skill(Skill(
            name="llm_call",
            category=SkillCategory.UTILITY,
            description="LLM调用 - 调用大语言模型API，支持文本生成、表格分析等多种模式，可发送完整表格内容进行分析",
            function=_skill_llm_call,
            parameters=[
                SkillParameter("prompt", "str", "提示词，用于指导LLM生成内容", False, ""),
                SkillParameter("model", "str", "模型名称，实际使用配置文件中的模型", False, "gpt-3.5-turbo"),
                SkillParameter("temperature", "float", "温度参数，控制输出随机性，范围0-2", False, 0.7),
                SkillParameter("mode", "str", "调用模式：table（整表分析）、row（逐行分析）、doc（文档分析）", False, "table"),
                SkillParameter("selected_columns", "list", "选择要分析的列名列表，空列表表示使用所有列", False, None),
                SkillParameter("token_1", "str", "API密钥，用于调用LLM API", False, None),
                SkillParameter("selected_model", "str", "选择的模型名称，优先使用配置文件中的模型", False, None),
                SkillParameter("model_config", "dict", "模型配置字典，包含API URL、模型名称等", False, None),
                SkillParameter("return_format_config", "dict", "返回格式配置，控制LLM返回的结果格式", False, None),
                SkillParameter("system_prompt", "str", "系统提示词，定义LLM的角色和行为", False, ""),
                SkillParameter("user_prompt", "str", "用户提示词，与prompt参数功能相同，优先级更高", False, ""),
                SkillParameter("reference_material", "str", "参考材料，提供给LLM的额外信息", False, ""),
                SkillParameter("table_default_prompt_fixed", "str", "表格分析默认提示词，用于指导LLM分析表格", False, ""),
                SkillParameter("batch_size", "int", "批量处理大小，仅在row模式下有效", False, 1),
                SkillParameter("sample_size", "int", "采样大小，用于限制发送给LLM的数据量", False, None),
                SkillParameter("filter_condition", "dict", "数据过滤条件，用于筛选要分析的数据行", False, None)
            ],
            examples=[
                "调用GPT进行文本分析", 
                "使用LLM生成摘要", 
                "分析表格数据并返回结果",
                "发送完整表格内容进行分析"
            ]
        ))


# 自动注册技能
LlmCallPlugin.register()
