"""
OMNIMIND Chat Template Library
Comprehensive support for modern LLM chat formats (ChatML, Llama-3, Phi, Gemma, Zephyr, etc.)
"""

from dataclasses import dataclass
from typing import Dict, Optional, List, Any

# ==============================================================================
# 1. Standard ChatML (OpenAI, Qwen, Yi, DeepSeek)
# ==============================================================================
CHATML_TEMPLATE = """{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"""

# ==============================================================================
# 2. Llama-3 (Meta)
# ==============================================================================
LLAMA3_TEMPLATE = """{% set loop_messages = messages %}{% for message in loop_messages %}{% set content = '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'+ message['content'] | trim + '<|eot_id|>' %}{% if loop.index0 == 0 %}{% set content = bos_token + content %}{% endif %}{{ content }}{% endfor %}{% if add_generation_prompt %}{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}{% endif %}"""

# ==============================================================================
# 3. Llama-2 (Meta)
# ==============================================================================
LLAMA2_TEMPLATE = """{% for message in messages %}{% if message['role'] == 'user' %}{{ '[INST] ' + message['content'] + ' [/INST]' }}{% elif message['role'] == 'system' %}{{ '<<SYS>>\n' + message['content'] + '\n<</SYS>>\n\n' }}{% else %}{{ message['content'] + ' ' }}{% endif %}{% endfor %}"""

# ==============================================================================
# 4. Mistral / Zephyr
# ==============================================================================
MISTRAL_TEMPLATE = """{{ bos_token }}{% for message in messages %}{% if (message['role'] == 'user') != (loop.index0 % 2 == 0) %}{{ raise_exception('Conversation roles must alternate user/assistant/user/assistant/...') }}{% endif %}{% if message['role'] == 'user' %}{{ '[INST] ' + message['content'] + ' [/INST]' }}{% elif message['role'] == 'assistant' %}{{ message['content'] + eos_token + ' ' }}{% else %}{{ raise_exception('Only user and assistant roles are supported!') }}{% endif %}{% endfor %}"""

# ==============================================================================
# 5. Gemma (Google)
# ==============================================================================
GEMMA_TEMPLATE = """{{ bos_token }}{% if messages[0]['role'] == 'system' %}{{ raise_exception('System role not supported in Gemma') }}{% endif %}{% for message in messages %}{% if (message['role'] == 'user') != (loop.index0 % 2 == 0) %}{{ raise_exception('Conversation roles must alternate user/assistant/user/assistant/...') }}{% endif %}{% if message['role'] == 'user' %}{{ '<start_of_turn>user\n' + message['content'] | trim + '<end_of_turn>\n' }}{% elif message['role'] == 'assistant' %}{{ '<start_of_turn>model\n' + message['content'] | trim + '<end_of_turn>\n' }}{% else %}{{ raise_exception('Only user and assistant roles are supported!') }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<start_of_turn>model\n' }}{% endif %}"""

# ==============================================================================
# 6. Phi-3 (Microsoft)
# ==============================================================================
PHI3_TEMPLATE = """{{ bos_token }}{% for message in messages %}{% if message['role'] == 'system' %}{{'<|system|>\n' + message['content'] + '<|end|>\n'}}{% elif message['role'] == 'user' %}{{'<|user|>\n' + message['content'] + '<|end|>\n'}}{% elif message['role'] == 'assistant' %}{{'<|assistant|>\n' + message['content'] + '<|end|>\n'}}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '<|assistant|>\n' }}{% endif %}"""

# ==============================================================================
# 7. Vicuna (LMSYS)
# ==============================================================================
VICUNA_TEMPLATE = """{% for message in messages %}{% if message['role'] == 'system' %}{{ message['content'] + ' ' }}{% elif message['role'] == 'user' %}{{ 'USER: ' + message['content'] + ' ' }}{% elif message['role'] == 'assistant' %}{{ 'ASSISTANT: ' + message['content'] + ' ' }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ 'ASSISTANT:' }}{% endif %}"""

# ==============================================================================
# 8. Alpaca
# ==============================================================================
ALPACA_TEMPLATE = """{% for message in messages %}{% if message['role'] == 'system' %}{{ message['content'] + '\n\n' }}{% elif message['role'] == 'user' %}{{ '### Instruction:\n' + message['content'] + '\n\n' }}{% elif message['role'] == 'assistant' %}{{ '### Response:\n' + message['content'] + '\n\n' }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ '### Response:\n' }}{% endif %}"""

# ==============================================================================
# 9. OMNIMIND (Ours - Advanced)
# ==============================================================================
OMNIMIND_CHAT_TEMPLATE = """{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"""

# ==============================================================================
OMNIMIND_TEMPLATE = """{%- if tools %}
    {{- '<|im_start|>system\n' }}
    {%- if messages[0].role == 'system' %}
        {{- messages[0].content + '\n\n' }}
    {%- else %}
        {{- 'You are OMNIMIND, an advanced AI with infinite memory and state-space processing capabilities.\n\n' }}
    {%- endif %}
    {{- "# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>" }}
    {%- for tool in tools %}
        {{- "\n" }}
        {{- tool | tojson }}
    {%- endfor %}
    {{- "\n</tools>\n\nTo use a tool, output valid Python code wrapped in <tool_code> tags:\n<tool_code>tool_name(arg='value')</tool_code>\n\nUsage examples:\n<tool_code>search(query='AI news')</tool_code>\n<tool_code>calculate(expression='2+2')</tool_code><|im_end|>\n" }}
{%- else %}
    {%- if messages[0].role == 'system' %}
        {{- '<|im_start|>system\n' + messages[0].content + '<|im_end|>\n' }}
    {%- endif %}
{%- endif %}
{%- for message in messages %}
    {%- if message.role == "user" %}
        {{- '<|im_start|>user\n' + message.content + '<|im_end|>\n' }}
    {%- elif message.role == "assistant" %}
        {{- '<|im_start|>assistant\n' + message.content + '<|im_end|>\n' }}
    {%- elif message.role == "tool" %}
        {{- '<|im_start|>tool\n' + message.content + '<|im_end|>\n' }}
    {%- elif message.role == "memory" %}
        {{- '<|im_start|>memory\n' + message.content + '<|im_end|>\n' }}
    {%- endif %}
{%- endfor %}
{%- if add_generation_prompt %}
    {{- '<|im_start|>assistant\n' }}
    {%- if enable_thinking %}
        {{- '<think>\n' }}
    {%- endif %}
{%- endif %}
"""

# ==============================================================================
# Registry
# ==============================================================================

TEMPLATES = {
    "chatml": CHATML_TEMPLATE,
    "llama3": LLAMA3_TEMPLATE,
    "llama2": LLAMA2_TEMPLATE,
    "mistral": MISTRAL_TEMPLATE,
    "zephyr": MISTRAL_TEMPLATE,
    "gemma": GEMMA_TEMPLATE,
    "phi3": PHI3_TEMPLATE,
    "vicuna": VICUNA_TEMPLATE,
    "alpaca": ALPACA_TEMPLATE,
    "omnimind": OMNIMIND_TEMPLATE,
}

def get_chat_template(tokenizer, chat_template: str = None, mapping: Dict[str, str] = None) -> str:
    """
    Smartly select/apply a chat template to a tokenizer.
    
    Args:
        tokenizer: The tokenizer to modify
        chat_template: Explicit template name (e.g., "chatml", "llama3")
        mapping: Optional custom mapping
    
    Returns:
        The Jinja2 template string
    """
    
    # 1. User specified explicit template
    if chat_template is not None:
        if chat_template in TEMPLATES:
            template = TEMPLATES[chat_template]
            tokenizer.chat_template = template
            return template
        else:
            print(f"Warning: Unknown template '{chat_template}', using defaults.")

    # 2. Auto-detect from tokenizer/model name (Unsloth style)
    model_name = getattr(tokenizer, "name_or_path", "").lower()
    
    if "llama-3" in model_name:
        template = LLAMA3_TEMPLATE
    elif "gemma" in model_name:
        template = GEMMA_TEMPLATE
    elif "phi-3" in model_name:
        template = PHI3_TEMPLATE
    elif "mistral" in model_name or "zephyr" in model_name:
        template = MISTRAL_TEMPLATE
    elif "qwen" in model_name or "yi" in model_name or "deepseek" in model_name:
        template = CHATML_TEMPLATE
    else:
        # Default to ChatML (Modern standard)
        template = CHATML_TEMPLATE
    
    # Apply
    tokenizer.chat_template = template
    
    # Add special tokens if needed
    if "llama-3" in model_name:
        _add_special_tokens(tokenizer, ["<|start_header_id|>", "<|end_header_id|>", "<|eot_id|>"])
    elif "phi-3" in model_name:
        _add_special_tokens(tokenizer, ["<|system|>", "<|user|>", "<|assistant|>", "<|end|>"])
    elif template == CHATML_TEMPLATE:
        _add_special_tokens(tokenizer, ["<|im_start|>", "<|im_end|>"])

    return template

def _add_special_tokens(tokenizer, tokens: List[str]):
    """Helper to safely add tokens"""
    special_tokens_dict = {'additional_special_tokens': tokens}
    tokenizer.add_special_tokens(special_tokens_dict)

# Formatter helper functions
def format_markdown_code(code: str, language: str = "python") -> str:
    return f"```{language}\n{code}\n```"

def format_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format a list of lists as a markdown table"""
    header_row = "| " + " | ".join(headers) + " |"
    sep_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    data_rows = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_row, sep_row] + data_rows)

def format_multimodal_message(content: str, **kwargs) -> dict:
    return {"role": "user", "content": content, **kwargs}
