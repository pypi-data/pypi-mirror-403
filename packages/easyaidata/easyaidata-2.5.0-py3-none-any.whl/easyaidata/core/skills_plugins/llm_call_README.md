### llm_call

**分类**: 工具
**功能**: 调用大语言模型API，支持文本生成、表格生成等多种模式。

**参数**:

#### 基础参数
- `prompt` (str, required): 提示词
- `model` (str, optional): 模型名称
- `temperature` (float, optional): 温度参数，默认0.7，范围0-2

#### 高级参数（表格/行分析模式）
- `mode` (str, optional): 调用模式，支持三种模式：
  - `table`: 发送整个表格进行分析
  - `row`: 逐行分析表格数据（目前不启用）
  - `doc`: 文档分析模式（目前不启用）
- `selected_columns` (list, optional): 选择要分析的列名列表
- `token_1` (str, optional): API密钥
- `selected_model` (str, optional): 选择的模型名称
- `model_config` (dict, optional): 模型配置，包含以下字段：
  - `url`: API请求URL
  - `model_name`: 模型名称
  - `system_prompt`: 系统提示词
  - `temperature`: 温度参数
  - `max_tokens`: 最大生成 tokens
  - `top_p`: 核采样参数
  - `frequency_penalty`: 频率惩罚
  - `presence_penalty`: 存在惩罚
  - `stream`: 是否流式输出，一般选否
  - `enable_r1_thinking`: 是否启用思考链
  - `enable_web_search`: 是否启用网络搜索
  - `user_prompt`: 用户提示词（这个要重点修改）
  - `reference_material`: 参考材料
- `return_format_config` (dict, optional): 返回格式配置
- `system_prompt` (str, optional): 系统提示词
- `user_prompt` (str, optional): 用户提示词
- `reference_material` (str, optional): 参考材料
- `table_default_prompt_fixed` (str, optional): 表格分析默认提示词

**返回值**:
- str (LLM响应文本): 基础模式
- dict: 高级模式，包含result_type和data字段
  - `result_type`: 结果类型，"text"或"table"，请注意用户的需求，根据需求准确选择text或者table。
  - `data`: 结果数据，文本或数据框

**示例**:

#### 基础文本生成示例
```python
# 调用GPT进行文本分析
response = llm_call("分析这段文本的情感: 今天天气真好")

# 使用不同的模型
response = llm_call("总结这段文本", model="gpt-4")

# 调整温度参数
response = llm_call("生成创意文案", temperature=1.0)
```

#### 表格分析示例
```python
# 发送整个表格进行分析，返回文本结果
params = {
    'mode': 'table',
    'selected_columns': ['功能模块', '模块用途', '操作方法'],
    'token_1': 'bce******',
    'selected_model': 'DeepSeek',
    'model_config': {
        'url': 'https://qianfan.baidubce.com/v2/chat/completions',
        'model_name': 'deepseek-v3',
        'system_prompt': '你是一个数据分析师，要对一个数据表格进行分析。\n\n如果用户要求返回文本，请直接返回markdown格式的结果，确保使用正确的markdown语法。只返回纯粹的markdown内容，不添加任何额外的解释或说明。确保返回的markdown格式清晰易读，合理使用标题、列表、表格等markdown元素。如果用户要求返回表格（table),就直接返回一个json表格。\n\n特别注意排版要求：\n1. 标题必须加粗，使用不同级别的标题标记（#、##、###等）\n2. 各级标题要有层次感，字体大小应随着标题级别增加而减小\n3. 合理使用粗体、斜体等格式增强可读性\n4. 使用列表（有序或无序）来组织内容\n5. 对于表格数据，使用markdown表格 格式\n6. 确保整体排版整洁，段落分明',
        'temperature': 0.3,
        'max_tokens': 8000,
        'top_p': 0.9,
        'frequency_penalty': 1.0,
        'presence_penalty': 1.0,
        'stream': False,
        'enable_r1_thinking': False,
        'enable_web_search': False,
        'user_prompt': '请按要求分析。这是一个什么表格？',
        'reference_material': ''
    },
    'return_format_config': {
        'format_type': '返回markdown文档',
        'columns': ['行号','行有多少字符', '最后一个字符是什么'],
        'first_column': ['行1', '行2', '行3']
    },
    'system_prompt': '你是一个数据分析师，要对一个数据表格进行分析。',
    'user_prompt': '请按要求分析。这是一个什么表格？',
    'reference_material': '',
    'table_default_prompt_fixed': '\n        你是一个专业的数据分析助手，请根据以下要求分析输入数据并返回结果：\n        1. 输入数据中包含用户选择的列，每行数据都有一个唯一的 `数据链接代码`，格式为 `R + 数字`（例如：R1, R2, R3）。\n        2. 请根据数据内容进行专业的分析，确保结果准确可靠。\n        3. 如果要求返回文本，请直接返回markdown格式的结果，确保使用正确的markdown语法。如果要求返回表格，请确保json行列对应，能被后续转为Pd\n        4. 如果要求返回文本，只返回纯粹的markdown内容，不添加任何额外的解释或说明。如果要求返回表格，直接返回json表格，不添加任何额外的解释或说明。。\n        5. 确保返回的markdown格式清晰易读，合理使用标题、列表、表格（如果文本里头有表格）等markdown元素。\n        '
}

# 调用LLM分析表格
response = llm_call(df, **params)
```

**注意事项**:
- 基础模式下，prompt必须是非空字符串
- 高级模式下，需要提供完整的model_config配置
- table模式下，selected_columns指定要分析的列
- temperature越高，输出越随机
- 不同模型支持的参数可能有所不同，请参考对应模型的API文档
- 各项参数（如提示词、API密钥等）需要根据实际情况进行替换
- 返回结果处理：
  - 如果返回的是表格结果（result_type为"table"），后续会使用表格浏览器打开
  - 如果返回的是文本结果（result_type为"text"或者返'markdown文档'），后续会使用文本浏览器打开
- 模型配置与agent保持一致：
  - 默认模型与agent使用相同的获取方式，优先从settings/model_config.json文件中读取第一个模型
  - 支持与agent相同的模型配置格式，确保与agent的兼容性
  - 可以直接使用agent的默认模型配置，无需额外配置

---
