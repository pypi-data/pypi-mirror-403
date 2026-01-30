"""
NexAgent OpenAPI Server - 兼容OpenAI格式的API服务器
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import time
from .framework import NexFramework
from ._version import __version__

router = APIRouter(prefix="/v1", tags=["OpenAPI"])


class Message(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


class ToolFunction(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Tool(BaseModel):
    type: str = "function"
    function: ToolFunction


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Any] = None


def create_chat_completion_response(content: str, model: str, finish_reason: str = "stop", tool_calls: List[Dict] = None):
    """创建聊天补全响应"""
    message = {
        "role": "assistant",
        "content": content
    }
    if tool_calls:
        message["tool_calls"] = tool_calls
    
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": finish_reason
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


def create_chat_completion_chunk(content: str, model: str, finish_reason: Optional[str] = None, tool_calls: List[Dict] = None):
    """创建流式聊天补全chunk"""
    delta = {}
    if content:
        delta["content"] = content
    if tool_calls:
        delta["tool_calls"] = tool_calls
    
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": delta,
            "finish_reason": finish_reason
        }]
    }


@router.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    """OpenAI兼容的聊天补全接口"""
    from datetime import datetime
    
    nex: NexFramework = request.app.state.nex
    
    # 获取API模型配置
    config = nex.db.get_openapi_config(req.model)
    if not config:
        raise HTTPException(status_code=404, detail=f"Model '{req.model}' not found")
    
    # 切换到配置的内部模型
    original_model = nex.current_model_key
    nex.current_model_key = config['internal_model_key']
    
    try:
        # 获取模型配置
        model_config = nex.db.get_model(config['internal_model_key'])
        if not model_config:
            raise HTTPException(status_code=500, detail="Internal model not configured")
        
        from openai import OpenAI
        client = OpenAI(api_key=model_config['api_key'], base_url=model_config['base_url'])
        actual_model = model_config['model_id']
        
        # 构建消息列表
        messages = []
        
        # 添加系统提示词
        system_prompt = ""
        if config['persona_id']:
            persona = nex.db.get_persona(config['persona_id'])
            if persona:
                system_prompt = persona.get('system_prompt', '')
        
        if config['use_system_prompt']:
            from .prompts import get_system_prompt
            builtin_prompt = get_system_prompt()
            system_prompt = f"{builtin_prompt}\n\n{system_prompt}" if system_prompt else builtin_prompt
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加时间信息
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        # 转换请求消息
        for msg in req.messages:
            if msg.role == "system":
                # 合并系统消息
                if messages and messages[0]["role"] == "system":
                    messages[0]["content"] += f"\n\n{msg.content}"
                else:
                    messages.insert(0, {"role": "system", "content": msg.content})
            elif msg.role == "user":
                messages.append({
                    "role": "user",
                    "content": f"【系统信息】\n当前时间: {now}\n【以下为输入内容】\n{msg.content}"
                })
            elif msg.role == "assistant":
                if msg.tool_calls:
                    messages.append({
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": msg.tool_calls
                    })
                else:
                    messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == "tool":
                messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content or ""
                })
        
        # 收集Nex内置工具名和远程工具名
        # 检查工具调用总开关
        tools_enabled = nex.db.get_setting('tools_enabled', 'true') == 'true'
        
        nex_tools = nex.get_all_tools() if tools_enabled else []
        nex_tool_names = set(t["function"]["name"] for t in nex_tools)
        remote_tool_names = set()
        
        # 合并工具列表
        all_tools = list(nex_tools)  # 复制一份
        
        if req.tools:
            for tool in req.tools:
                tool_name = tool.function.name
                remote_tool_names.add(tool_name)
                # 只添加不与Nex工具重名的远程工具
                if tool_name not in nex_tool_names:
                    all_tools.append({
                        "type": tool.type,
                        "function": {
                            "name": tool_name,
                            "description": tool.function.description or "",
                            "parameters": tool.function.parameters or {"type": "object", "properties": {}}
                        }
                    })
        
        if req.stream:
            # 流式响应
            def generate():
                nonlocal messages
                
                while True:
                    api_params = {
                        "model": actual_model,
                        "messages": messages,
                        "stream": True
                    }
                    if all_tools:
                        api_params["tools"] = all_tools
                        api_params["tool_choice"] = "auto"
                    
                    stream = client.chat.completions.create(**api_params)
                    
                    content_buffer = ""
                    tool_calls_buffer = {}
                    
                    for chunk in stream:
                        if not chunk.choices:
                            continue
                        
                        delta = chunk.choices[0].delta
                        
                        if delta.content:
                            content_buffer += delta.content
                            data = create_chat_completion_chunk(delta.content, req.model)
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        
                        if delta.tool_calls:
                            for tc in delta.tool_calls:
                                idx = tc.index
                                if idx not in tool_calls_buffer:
                                    tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                                if tc.id:
                                    tool_calls_buffer[idx]["id"] = tc.id
                                if tc.function:
                                    if tc.function.name:
                                        tool_calls_buffer[idx]["name"] = tc.function.name
                                    if tc.function.arguments:
                                        tool_calls_buffer[idx]["arguments"] += tc.function.arguments
                    
                    if not tool_calls_buffer:
                        # 没有工具调用，结束
                        break
                    
                    # 处理工具调用
                    tool_calls_list = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": tc["arguments"]}
                        }
                        for tc in [tool_calls_buffer[i] for i in sorted(tool_calls_buffer.keys())]
                    ]
                    
                    # 检查是否有远程工具调用（在远程列表中，优先返回给客户端）
                    remote_calls = [tc for tc in tool_calls_list 
                                   if tc["function"]["name"] in remote_tool_names]
                    
                    if remote_calls:
                        # 有远程工具调用，返回给客户端处理
                        # 发送工具调用chunk
                        tool_chunk = create_chat_completion_chunk("", req.model, tool_calls=[
                            {"index": i, "id": tc["id"], "type": "function", "function": tc["function"]}
                            for i, tc in enumerate(remote_calls)
                        ])
                        yield f"data: {json.dumps(tool_chunk, ensure_ascii=False)}\n\n"
                        
                        # 结束流，让客户端处理工具调用
                        data = create_chat_completion_chunk("", req.model, "tool_calls")
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    
                    # 只有Nex内置工具调用，执行它们
                    messages.append({
                        "role": "assistant",
                        "content": content_buffer or None,
                        "tool_calls": tool_calls_list
                    })
                    
                    for tc in tool_calls_list:
                        name = tc["function"]["name"]
                        args = json.loads(tc["function"]["arguments"])
                        
                        # 输出工具调用标记
                        tool_text = f"\n[NexTools:{name}]\n"
                        data = create_chat_completion_chunk(tool_text, req.model)
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        
                        # 执行工具
                        result = nex.handle_tool_call(tc)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result
                        })
                
                # 发送结束标记
                data = create_chat_completion_chunk("", req.model, "stop")
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # 非流式响应
            content_parts = []
            
            while True:
                api_params = {
                    "model": actual_model,
                    "messages": messages
                }
                if all_tools:
                    api_params["tools"] = all_tools
                    api_params["tool_choice"] = "auto"
                
                response = client.chat.completions.create(**api_params)
                assistant_message = response.choices[0].message
                
                if assistant_message.content:
                    content_parts.append(assistant_message.content)
                
                if not assistant_message.tool_calls:
                    # 没有工具调用，结束
                    break
                
                # 检查是否有远程工具调用
                tool_calls_list = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in assistant_message.tool_calls
                ]
                
                # 检查是否有远程工具调用（在远程列表中，优先返回给客户端）
                remote_calls = [tc for tc in tool_calls_list 
                               if tc["function"]["name"] in remote_tool_names]
                
                if remote_calls:
                    # 有远程工具调用，返回给客户端处理
                    return create_chat_completion_response(
                        ''.join(content_parts) if content_parts else None,
                        req.model,
                        "tool_calls",
                        remote_calls
                    )
                
                # 只有Nex内置工具调用，执行它们
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": tool_calls_list
                })
                
                for tc in assistant_message.tool_calls:
                    name = tc.function.name
                    
                    # 添加工具调用标记
                    content_parts.append(f"\n[NexTools:{name}]\n")
                    
                    # 执行工具
                    result = nex.handle_tool_call(tc)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
            
            return create_chat_completion_response(''.join(content_parts), req.model)
    
    finally:
        nex.current_model_key = original_model


@router.get("/models")
async def list_models(request: Request):
    """OpenAI兼容的模型列表接口"""
    nex: NexFramework = request.app.state.nex
    
    # 获取所有OpenAPI配置
    configs = nex.db.get_openapi_configs()
    
    models = []
    for config in configs:
        models.append({
            "id": config['api_model_id'],
            "object": "model",
            "created": int(time.time()),
            "owned_by": "nexagent",
            "permission": [],
            "root": config['api_model_id'],
            "parent": None
        })
    
    return {
        "object": "list",
        "data": models
    }
