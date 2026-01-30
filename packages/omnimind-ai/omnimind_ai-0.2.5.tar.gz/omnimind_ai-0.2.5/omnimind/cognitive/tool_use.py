"""
OMNIMIND Tool Use (Function Calling)
Enable SSM models to use external tools through special tokens

Protocol:
1. Model outputs: <tool_code>call(arg1, arg2)</tool_code>
2. System executes: result = func(arg1, arg2)
3. System injects: <tool_output>result</tool_output>
4. Model continues...

Usage:
    tools = [weather_func, search_func]
    agent = ToolAgent(model, tools)
    agent.chat("What's the weather in Bangkok?")
"""
import re
import json
import ast
import inspect
from typing import List, Callable, Dict, Any, Union

class ToolRegistry:
    """Manages available tools and their schemas"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.schemas: List[Dict] = []
    
    def register(self, func: Callable):
        """Register a python function as a tool"""
        self.tools[func.__name__] = func
        
        # Generate schema from docstring/signature
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or "No description"
        
        params = {}
        for name, param in sig.parameters.items():
            params[name] = {
                "type": str(param.annotation) if param.annotation != inspect._empty else "string"
            }
            
        schema = {
            "name": func.__name__,
            "description": doc,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": [n for n, p in sig.parameters.items() if p.default == inspect._empty]
            }
        }
        self.schemas.append(schema)
        return func

class ToolAgent:
    """SSM Agent capable of Function Calling"""
    
    TOOL_START = "<tool_code>"
    TOOL_END = "</tool_code>"
    OUTPUT_START = "<tool_output>"
    OUTPUT_END = "</tool_output>"
    
    def __init__(self, model, tokenizer, tools: List[Callable]):
        self.model = model
        self.tokenizer = tokenizer
        self.registry = ToolRegistry()
        for t in tools:
            self.registry.register(t)
            
    def get_system_prompt(self) -> str:
        """Inject tool definitions into system prompt"""
        schemas_json = json.dumps(self.registry.schemas, indent=2)
        return (
            "You are an AI assistant with access to these tools:\n"
            f"{schemas_json}\n\n"
            "To use a tool, output valid Python code wrapped in tags:\n"
            f"{self.TOOL_START}tool_name(arg='value'){self.TOOL_END}\n"
        )

    def process_turn(self, user_input: str, history: List[Dict]) -> str:
        """Process a turn with automatic tool execution loop"""
        
        # 1. Prepare prompt
        prompt = ""
        # Add system prompt if start of convo
        if not history:
            prompt += f"<|im_start|>system\n{self.get_system_prompt()}<|im_end|>\n"
        
        # Add history
        for msg in history:
            prompt += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
            
        prompt += f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        
        # 2. Generate initial response
        response = self._generate(prompt)
        full_response = response
        
        # 3. Check for tool calls
        while self.TOOL_START in response:
            # Extract tool call
            start_idx = response.find(self.TOOL_START) + len(self.TOOL_START)
            end_idx = response.find(self.TOOL_END)
            
            if end_idx == -1: 
                break # Invalid format
                
            code = response[start_idx:end_idx].strip()
            print(f"🤖 Tool Call: {code}")
            
            # Execute tool (safer parsing)
            try:
                result = self._safe_execute_tool(code)
                result_str = str(result)
            except Exception as e:
                result_str = f"Error: {str(e)}"
                
            print(f"   ↳ Result: {result_str}")
            
            # output format
            tool_output_block = f"\n{self.OUTPUT_START}\n{result_str}\n{self.OUTPUT_END}\n"
            
            # Feed back to model
            full_response += tool_output_block
            prompt += f"{response}{tool_output_block}"
            
            # Continue generating
            response = self._generate(prompt)
            full_response += response
            
        return full_response

    def _safe_execute_tool(self, code: str) -> Any:
        """
        Safely execute tool call by parsing function name and arguments.
        
        Parses: tool_name(arg1='value', arg2=123)
        Instead of using dangerous eval()
        """
        import ast
        
        # Parse the code as an expression
        try:
            tree = ast.parse(code, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid tool call syntax: {e}")
        
        # Must be a Call expression
        if not isinstance(tree.body, ast.Call):
            raise ValueError("Tool call must be a function call")
        
        call = tree.body
        
        # Get function name
        if isinstance(call.func, ast.Name):
            func_name = call.func.id
        else:
            raise ValueError("Tool call must be a simple function name")
        
        # Check if function exists in registry
        if func_name not in self.registry.tools:
            available = list(self.registry.tools.keys())
            raise ValueError(f"Unknown tool: {func_name}. Available: {available}")
        
        # Parse positional arguments (only allow literals)
        args = []
        for arg in call.args:
            args.append(self._safe_eval_literal(arg))
        
        # Parse keyword arguments
        kwargs = {}
        for kw in call.keywords:
            kwargs[kw.arg] = self._safe_eval_literal(kw.value)
        
        # Execute the tool
        func = self.registry.tools[func_name]
        return func(*args, **kwargs)
    
    def _safe_eval_literal(self, node: ast.AST) -> Any:
        """Safely evaluate AST node as a literal value only."""
        import ast
        
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        elif isinstance(node, ast.Num):  # Python 3.7 compatibility
            return node.n
        elif isinstance(node, ast.List):
            return [self._safe_eval_literal(el) for el in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._safe_eval_literal(k): self._safe_eval_literal(v)
                for k, v in zip(node.keys, node.values)
            }
        elif isinstance(node, ast.Tuple):
            return tuple(self._safe_eval_literal(el) for el in node.elts)
        elif isinstance(node, ast.NameConstant):  # True, False, None (Python 3.7)
            return node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            # Handle negative numbers like -1
            return -self._safe_eval_literal(node.operand)
        else:
            raise ValueError(f"Unsupported argument type: {type(node).__name__}. Only literals allowed.")

    def _generate(self, prompt: str) -> str:
        """Helper to generate text"""
        # Simplified generation call
        if hasattr(self.model, 'generate_stream'):
            # Should be mobile inference
            text = ""
            for token in self.model.generate_stream(prompt, max_tokens=512):
                text += token
                if self.TOOL_END in text: # Early stop on tool call
                    break
            return text
        else:
            # Standard model
            input_ids = self.tokenizer.encode(prompt)
            # ... forward ...
            # Placeholder for brevity
            return " [Generation logic] "
