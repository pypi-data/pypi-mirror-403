"""
OMNIMIND API Server
OpenAI-compatible API server for easy integration

Endpoints:
- POST /v1/chat/completions
- POST /v1/completions
- POST /v1/models
- GET /health

Usage:
    python -m omnimind.server --model micro --port 8000
"""
import os
import asyncio
import time
import uuid
import json
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

import torch
from pydantic import BaseModel, Field

# FastAPI imports with fallback
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("⚠️ FastAPI not installed. Run: pip install fastapi uvicorn")

# High-performance libs (optional)
try:
    import uvloop
    import orjson
    from fastapi.responses import ORJSONResponse
    HAS_OPTIMIZED_LIBS = True
except ImportError:
    HAS_OPTIMIZED_LIBS = False
    if HAS_FASTAPI:
        from fastapi.responses import JSONResponse as ORJSONResponse
    else:
        ORJSONResponse = None
    print("⚠️ High-performance libs (uvloop, orjson) not found. Falling back to standard libs.")

# Tokenizer import
from .training.multilingual_tokenizer import MultilingualTokenizer


# ==================== Pydantic Models ====================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "omnimind-micro"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: float = 0.7
    top_p: float = 0.9
    stream: bool = False

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: dict

class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: dict
    finish_reason: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]


# ==================== Server Setup ====================

# ThreadPool for non-blocking inference
executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)

# Create FastAPI app only if available
if HAS_FASTAPI:
    app = FastAPI(title="OMNIMIND API", version="1.0.0", default_response_class=ORJSONResponse if ORJSONResponse else None)
else:
    app = None

# Install uvloop if available
if HAS_OPTIMIZED_LIBS:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# CORS (only if FastAPI available)
if HAS_FASTAPI and app is not None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Global state
class ServerState:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.mobile_inference = None
        self.omnimind = None
        self.device = "cpu"

state = ServerState()

async def run_in_executor(func, *args):
    """Run blocking function in thread pool to keep event loop free (Bun-like non-blocking I/O)"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)

def load_model(model_name: str, quantization: str = "none", device: str = "auto"):
    """Load model into global state"""
    print(f"📥 Loading model: {model_name}...")
    
    state.tokenizer = MultilingualTokenizer()
    
    # Create unified Omnimind model
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    state.device = device
    
    # Initialize Omnimind
    from omnimind import Omnimind, MobileConfig, MobileInference
    
    if quantization != "none":
        print(f"⚠️ Loading Omnimind in {quantization} mode (Experimental)")
        omni = Omnimind(size=model_name, device="cpu")
        config = MobileConfig(quantization=quantization)
        state.mobile_inference = MobileInference(omni.core, config)
        state.model = state.mobile_inference.model
        state.omnimind = omni
    else:
        # Standard load
        omni = Omnimind(size=model_name, device=device)
        state.omnimind = omni
        state.model = omni.core

        if device == "cuda":
            from omnimind import optimize_model, GPUConfig
            omni.core = optimize_model(omni.core, GPUConfig(dtype="bf16", compile_model=True))
            state.model = omni.core
        
    print(f"✅ Unified OMNIMIND loaded on {device}")


@app.on_event("startup")
async def startup_event():
    # Only load if not already loaded (allows testing)
    if state.model is None:
        model_name = os.getenv("OMNIMIND_MODEL", "micro")
        quant = os.getenv("OMNIMIND_QUANT", "none")
        load_model(model_name, quant)


@app.get("/health")
async def health():
    return {"status": "ok", "device": state.device}


@app.get("/v1/models")
async def list_models():
    from omnimind import list_available_sizes
    # Offload potentially slow file I/O or calculations
    sizes = await run_in_executor(list_available_sizes)
    return {
        "object": "list",
        "data": [
            {"id": size, "object": "model", "created": int(time.time()), "owned_by": "omnimind"}
            for size in sizes
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if state.model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Format prompt (simplified ChatML)
    prompt = ""
    for msg in request.messages:
        prompt += f"<|im_start|>{msg.role}\n{msg.content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    
    # Generation parameters
    max_new_tokens = request.max_tokens or 512
    temperature = request.temperature
    top_p = request.top_p
    
    request_id = f"chatcmpl-{uuid.uuid4()}"
    created = int(time.time())
    
    # Stream response
    if request.stream:
        return StreamingResponse(
            stream_generator(prompt, request_id, created, request.model, max_new_tokens, temperature),
            media_type="text/event-stream"
        )
    
    # Non-stream response: EXECUTE IN THREAD POOL to avoid blocking loop
    # This enables high concurrency (Bun-like)
    
    if state.mobile_inference:
        output_text = await run_in_executor(
            state.mobile_inference.generate, prompt, max_new_tokens
        )
    elif hasattr(state, 'omnimind') and state.omnimind:
        # Use Unified Agent
        if not request.messages:
            output_text = ""
        else:
            user_input = request.messages[-1].content
            history = [
                {"role": m.role, "content": m.content} 
                for m in request.messages[:-1] 
                if m.role != "system"
            ]
            
            # Run robust agent process in background thread
            output_text = await run_in_executor(
                state.omnimind.agent.process_turn, user_input, history
            )
            
    else:
        # Fallback standard inference
        def _fallback_generate():
            input_ids = state.tokenizer.encode(prompt)
            input_tensor = torch.tensor([input_ids]).to(state.device)
            with torch.no_grad():
                output_tensor = state.model.generate(
                    input_tensor, 
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p
                )
            new_tokens = output_tensor[0][len(input_ids):]
            return state.tokenizer.decode(new_tokens.tolist())

        output_text = await run_in_executor(_fallback_generate)
    
    return ChatCompletionResponse(
        id=request_id,
        created=created,
        model=request.model,
        choices=[
            ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=output_text),
                finish_reason="stop"
            )
        ],
        usage={"prompt_tokens": len(prompt), "completion_tokens": len(output_text), "total_tokens": 0}
    )


async def stream_generator(prompt, request_id, created, model_name, max_tokens, temperature):
    """Generator for streaming responses"""
    # Streaming is trickier with run_in_executor because we need an iterator.
    # Ideally, we push tokens to a queue from a thread and pop them here.
    # For now, we will maintain the existing logic but keep it async-aware where possible.
    
    if state.mobile_inference:
        # Iterate over synchronous generator (this might block, ideally we'd thread it differently)
        # But handling async iterator from threaded generator is complex.
        # Keeping direct call for streaming for now or wrapping standard iterator.
        iterator = state.mobile_inference.generate_stream(prompt, state.tokenizer, max_tokens=max_tokens)
    else:
        # Fallback pseudo-streaming
        full_text = "Streaming not fully implemented for standard model in this view."
        iterator = list(full_text)
    
    for token in iterator:
        chunk = ChatCompletionChunk(
            id=request_id,
            created=created,
            model=model_name,
            choices=[
                ChatCompletionChunkChoice(
                    index=0,
                    delta={"content": token},
                    finish_reason=None
                )
            ]
        )
        # Use orjson dumps for speed if available
        json_str = orjson.dumps(chunk.dict()).decode() if HAS_OPTIMIZED_LIBS else chunk.json()
        yield f"data: {json_str}\n\n"
        await asyncio.sleep(0.01)  # Yield control
    
    # Final 'done' chunk
    chunk = ChatCompletionChunk(
        id=request_id,
        created=created,
        model=model_name,
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta={},
                finish_reason="stop"
            )
        ]
    )
    json_str = orjson.dumps(chunk.dict()).decode() if HAS_OPTIMIZED_LIBS else chunk.json()
    yield f"data: {json_str}\n\n"
    yield "data: [DONE]\n\n"


def run_server(model: str = "micro", port: int = 8000, quant: str = "none"):
    """Run the API server"""
    if not HAS_FASTAPI or app is None:
        print("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
        return
        
    import uvicorn
    
    os.environ["OMNIMIND_MODEL"] = model
    os.environ["OMNIMIND_QUANT"] = quant
    
    print(f"🚀 Starting OMNIMIND Server")
    print(f"   Model: {model}")
    print(f"   Port: {port}")
    print(f"   URL: http://localhost:{port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OMNIMIND API Server")
    parser.add_argument("--model", type=str, default="micro", help="Model size")
    parser.add_argument("--port", type=int, default=8000, help="Port")
    parser.add_argument("--quant", type=str, default="none", help="Quantization (int4, int8)")
    args = parser.parse_args()
    
    run_server(args.model, args.port, args.quant)
