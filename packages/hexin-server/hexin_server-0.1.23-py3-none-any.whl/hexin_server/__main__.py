"""
FastAPI server that proxies OpenAI API endpoints using the hexin_engine backend.
"""
import copy
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import uuid
import httpx
import httpx_sse
import requests
import argparse
from typing_extensions import List, Optional, Dict, Any, Union, AsyncGenerator, Literal
from contextlib import asynccontextmanager
from urllib.parse import urlencode

import uvicorn
from datetime import datetime
from requests import Response
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger
import threading
import fcntl
from openai.types.chat.chat_completion import ChatCompletion, ChatCompletionMessage, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice as ChunkChoice, ChoiceDelta, ChoiceDeltaToolCall, ChoiceDeltaFunctionCall, ChoiceDeltaToolCallFunction
from openai.types.completion_usage import CompletionUsage
from openai.types.model import Model
from openai.types.create_embedding_response import CreateEmbeddingResponse, Embedding, Usage
from pydantic import BaseModel, Field

from xlin import xmap_async

TIMEOUT = 60

# Global API logger instance (will be initialized in main if --log-dir is provided)
API_LOGGER: Optional["APILogger"] = None


class APILogger:
    """
    API日志记录器，按接口和日期分文件夹存储，每100条日志新开一个文件。
    文件格式为jsonlist（每行一个JSON对象）。
    """

    def __init__(self, log_dir: str, max_entries_per_file: int = 100):
        self.log_dir = Path(log_dir)
        self.max_entries_per_file = max_entries_per_file
        self._lock = threading.Lock()
        # 缓存当前文件的条目计数: {endpoint: {date: count}}
        self._entry_counts: Dict[str, Dict[str, int]] = {}
        # 缓存当前文件路径: {endpoint: {date: filepath}}
        self._current_files: Dict[str, Dict[str, Path]] = {}

    def _get_log_folder(self, endpoint: str, date_str: str) -> Path:
        """获取日志文件夹路径: log_dir/endpoint/date/"""
        folder = self.log_dir / endpoint / date_str
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _get_next_file_path(self, endpoint: str, date_str: str) -> Path:
        """获取下一个日志文件路径，文件名按时间保序"""
        folder = self._get_log_folder(endpoint, date_str)
        timestamp = datetime.now().strftime("%H%M%S_%f")
        return folder / f"{timestamp}.rollout.jsonl"

    def _get_or_create_file(self, endpoint: str) -> Path:
        """获取或创建当前日志文件"""
        date_str = datetime.now().strftime("%Y-%m-%d")

        if endpoint not in self._current_files:
            self._current_files[endpoint] = {}
            self._entry_counts[endpoint] = {}

        # 检查日期是否变化或文件是否需要轮转
        if date_str not in self._current_files[endpoint]:
            # 新的一天，创建新文件
            self._current_files[endpoint][date_str] = self._get_next_file_path(endpoint, date_str)
            self._entry_counts[endpoint][date_str] = 0
        elif self._entry_counts[endpoint].get(date_str, 0) >= self.max_entries_per_file:
            # 当前文件已满，创建新文件
            self._current_files[endpoint][date_str] = self._get_next_file_path(endpoint, date_str)
            self._entry_counts[endpoint][date_str] = 0

        return self._current_files[endpoint][date_str]

    def log(
        self,
        endpoint: str,
        input_messages: List[Dict[str, Any]],
        output_messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        request_headers: Optional[Dict[str, Any]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        **extra_params
    ):
        """
        记录一条API日志。

        Args:
            endpoint: 接口名称（如 "chat_completions", "embeddings", "responses", "messages"）
            input_messages: 输入消息列表
            output_messages: 输出消息列表
            tools: 工具定义列表（可选）
            model: 模型名称（可选）
            request_headers: 原始请求头（可选）
            request_body: 原始请求体（可选）
            **extra_params: 其他参数
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "input_messages": input_messages,
            "output_messages": output_messages,
        }
        if tools:
            log_entry["tools"] = tools
        if model:
            log_entry["model"] = model
        if request_headers:
            log_entry["request_headers"] = request_headers
        if request_body:
            log_entry["request_body"] = request_body
        log_entry.update(extra_params)

        with self._lock:
            file_path = self._get_or_create_file(endpoint)
            # 使用文件锁确保多进程安全
            with open(file_path, "a", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # 更新计数
            date_str = datetime.now().strftime("%Y-%m-%d")
            self._entry_counts[endpoint][date_str] = self._entry_counts[endpoint].get(date_str, 0) + 1


class StreamLogBuffer:
    """流式响应的日志缓冲器，在流结束时记录完整日志"""

    def __init__(
        self,
        api_logger: "APILogger",
        endpoint: str,
        input_messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **extra_params
    ):
        self.api_logger = api_logger
        self.endpoint = endpoint
        self.input_messages = input_messages
        self.tools = tools
        self.model = model
        self.extra_params = extra_params
        self.chunks: List[str] = []
        self.content_buffer = ""
        self.tool_calls_buffer: List[Dict[str, Any]] = []
        self.role = "assistant"

    def add_chunk(self, chunk_data: str):
        """添加一个流式块"""
        self.chunks.append(chunk_data)

    def add_content(self, content: str):
        """累积内容"""
        if content:
            self.content_buffer += content

    def add_tool_call(self, tool_call: Dict[str, Any]):
        """添加工具调用"""
        self.tool_calls_buffer.append(tool_call)

    def finalize(self):
        """流结束时，记录完整日志"""
        output_message: Dict[str, Any] = {
            "role": self.role,
            "content": self.content_buffer if self.content_buffer else None,
        }
        if self.tool_calls_buffer:
            output_message["tool_calls"] = self.tool_calls_buffer

        self.api_logger.log(
            endpoint=self.endpoint,
            input_messages=self.input_messages,
            output_messages=[output_message],
            tools=self.tools,
            model=self.model,
            stream=True,
            **self.extra_params
        )


def log_api_request(
    endpoint: str,
    input_messages: List[Dict[str, Any]],
    output_messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    model: Optional[str] = None,
    request_headers: Optional[Dict[str, Any]] = None,
    request_body: Optional[Dict[str, Any]] = None,
    **extra_params
):
    """便捷函数：如果启用了日志记录则记录API请求"""
    if API_LOGGER:
        API_LOGGER.log(
            endpoint=endpoint,
            input_messages=input_messages,
            output_messages=output_messages,
            tools=tools,
            model=model,
            request_headers=request_headers,
            request_body=request_body,
            **extra_params
        )


def sanitize_headers_for_logging(headers: Dict[str, str]) -> Dict[str, str]:
    """移除敏感信息的请求头，用于日志记录"""
    sensitive_keys = {'authorization', 'x-api-key', 'cookie', 'set-cookie'}
    return {
        k: ('***' if k.lower() in sensitive_keys else v)
        for k, v in headers.items()
    }


def get_userid_and_token(
    app_url,
    app_id,
    app_secret,
):
    d = {"app_id": app_id, "app_secret": app_secret}
    h = {"Content-Type": "application/json"}
    r = requests.post(app_url, json=d, headers=h)
    data = r.json()
    if "data" not in data:
        raise ValueError(f"Authentication failed: {data}")
    data = data["data"]
    return data["user_id"], data["token"]


def retry_request(func):
    def wrapper(*args, **kwargs):
        max_retry = kwargs.get("max_retry", 3)
        debug = kwargs.get("debug", False)
        for i in range(max_retry):
            try:
                result = func(*args, **kwargs)
                if not result:
                    if debug:
                        logger.error(f"Function {func.__name__} returned None, retrying {i + 1}/{max_retry}...")
                    continue
                # logger.debug(f"Function {func.__name__} succeeded on attempt {i + 1}.")
                return result
            except Exception as e:
                if debug:
                    logger.error(f"Request failed: {e}, retrying {i + 1}/{max_retry}...")
        if debug:
            logger.error("Max retries reached, returning None.")
        return None

    return wrapper


def api_request(
    url: str,
    params: dict,
    headers: dict,
    timeout: int = 100,
):
    res = requests.post(
        url,
        json=params,
        headers=headers,
        timeout=timeout,
    )
    return res


def prepare_api_request_params(
    user_id: str,
    token: str,
    messages: List[Dict[str, Any]],
    model: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    n: int,
    stream: bool = False,
    multi_modal: bool = False,
    tools: Optional[List[Dict[str, Any]]] = None,
    functions: Optional[List[Dict[str, Any]]] = None,
    function_call: Optional[Union[str, Dict[str, Any]]] = None,
    reasoning_effort: Optional[str] = None,
    thinking: Optional[Dict[str, Any]] = None,
) -> tuple[str, dict, dict, int]:
    """Prepare parameters for api_request based on model type"""

    # Base parameters
    params = {
        "messages": messages,
        "temperature": temperature,
        "model": model,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "n": n,
        "stream": stream,
    }

    if tools:
        params["tools"] = tools
    if functions:
        params["functions"] = functions
    if function_call:
        params["function_call"] = function_call
    if reasoning_effort:
        params["reasoning_effort"] = reasoning_effort
    if thinking:
        params["thinking"] = thinking

    rollout_n = None
    version = "v3"

    # Model-specific handling (copied from hexin_engine.py)
    if model == "claude" or model.startswith("claude-"):
        symbol = "claude"
        # Map Claude model names to backend model IDs
        # Backend supports these models:
        # - us.anthropic.claude-3-5-sonnet-20241022-v2:0
        # - us.anthropic.claude-3-7-sonnet-20250219-v1:0
        # - us.anthropic.claude-sonnet-4-20250514-v1:0
        # - us.anthropic.claude-opus-4-20250514-v1:0
        # - us.anthropic.claude-sonnet-4-5-20250929-v1:0
        # - global.anthropic.claude-opus-4-5-20251101-v1:0
        if "4.5" in model or "4-5" in model:
            # Claude 4.5 series
            if "opus" in model.lower():
                params["model"] = "global.anthropic.claude-opus-4-5-20251101-v1:0"
            elif "sonnet" in model.lower():
                params["model"] = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
            elif "haiku" in model.lower():
                params["model"] = "us.anthropic.claude-sonnet-4-20250514-v1:0"
            else:
                params["model"] = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        elif "4" in model and ("opus" in model.lower() or "sonnet" in model.lower()):
            # Claude 4 series
            if "opus" in model.lower():
                params["model"] = "us.anthropic.claude-opus-4-20250514-v1:0"
            else:
                params["model"] = "us.anthropic.claude-sonnet-4-20250514-v1:0"
        elif "3.7" in model or "3-7" in model:
            # Claude 3.7 series
            params["model"] = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        elif "3.5" in model or "3-5" in model:
            # Claude 3.5 series
            params["model"] = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        else:
            # Default to latest sonnet
            params["model"] = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

        # Bedrock API 使用 bedrock-2023-05-31 而不是 vertex-2023-10-16
        params["anthropic_version"] = "bedrock-2023-05-31"

        # Bedrock 不允许同时指定 temperature 和 top_p
        # 优先使用 temperature，如果没有则使用 top_p
        if temperature is not None and top_p is not None and top_p != 1.0:
            # 如果两者都指定了，删除 top_p
            params.pop("top_p", None)

        version = "v3"
        rollout_n = params.pop("n", None)
    elif "doubao" in model or model in [
        "ep-20250204210426-gclbn",
        "ep-20250410151344-fzm9z",
        "ep-20250410145517-rpbrz",
        "deepseek-reasoner",
        "deepseek-chat",
    ] or model.startswith("ep-"):
        symbol = "doubao"
        version = "v3"
        if "r1" in model or "reasoner" in model:
            params["model"] = "ep-20250410145517-rpbrz"
            rollout_n = params.pop("n", None)
        elif "v3" in model or "chat" in model:
            params["model"] = "ep-20250410151344-fzm9z"
    elif model == "r1-qianfan":
        symbol = "qianfan"
        params["model"] = "deepseek-r1"
        rollout_n = params.pop("n", None)
    elif model == "gemini":
        symbol = "gemini"
        params["model"] = "gemini-2.5-pro-preview-03-25"
    elif "qwen" in model:
        symbol = "qianwen"
        version = "v1"
    elif model in ["gpt-4o-mini", "o3", "o4-mini"] or model.startswith("gpt-") or re.match(r"^o[34](\-mini)?$", model):
        del params["max_tokens"]
        params["max_completion_tokens"] = max_tokens
        symbol = "chatgpt"
        if model in ["o3", "o4-mini"] or re.match(r"^o[34](\-mini)?$", model):
            del params["temperature"]
    else:
        symbol = "chatgpt"

    # Build URL
    if multi_modal:
        chat_url = "https://arsenal-openai.10jqka.com.cn:8443/vtuber/ai_access/chatgpt/v1/picture/chat/completions"
    elif symbol == "claude":
        # Claude 使用 Bedrock API 格式
        backend_model = params["model"]
        chat_url = f"https://arsenal-openai.10jqka.com.cn:8443/vtuber/ai_access/claude/model/{backend_model}/invoke"
        # Bedrock doesn't want 'model' in the request body (it's already in the URL)
        del params["model"]
    else:
        chat_url = f"https://arsenal-openai.10jqka.com.cn:8443/vtuber/ai_access/{symbol}/{version}/chat/completions"

    # Build headers
    headers = {"Content-Type": "application/json", "userId": user_id, "token": token}

    return chat_url, params, headers, rollout_n


def process_api_response(res: Response, url: str, model: str, debug: bool, rollout_n: Optional[int] = None):
    resp = res.json()
    if not rollout_n:
        rollout_n = 1

    # Helper function to check for error response
    def check_error_response(data: dict) -> None:
        """Check if response indicates an error and raise ValueError if so"""
        if not isinstance(data, dict):
            return
        # Check for success=False pattern
        if data.get("success") is False:
            error_msg = data.get("status_msg", "Unknown error")
            error_code = data.get("status_code", -1)
            logger.error(f"Backend API returned error (code: {error_code}): {error_msg}")
            raise ValueError(f"Backend API error (code: {error_code}): {error_msg}")
        # Check for error field pattern (common in some APIs)
        if "error" in data and isinstance(data["error"], dict):
            error_type = data["error"].get("type", "unknown_error")
            error_msg = data["error"].get("message", "Unknown error")
            logger.error(f"Backend API returned error ({error_type}): {error_msg}")
            raise ValueError(f"Backend API error ({error_type}): {error_msg}")

    # 检查后端是否返回错误
    check_error_response(resp)

    if "data" in resp:
        resp = resp["data"]

    # 再次检查解包后的数据是否是错误响应
    check_error_response(resp)

    if debug or "choices" not in resp:
        logger.debug(f"API request to {repr(url)} returned: {json.dumps(resp, ensure_ascii=False, indent=2)}")
    if rollout_n is not None:
        if model == "claude" and "content" in resp:
            if isinstance(resp["content"], list) and len(resp["content"]) == 1 and resp["content"][0].get("type") == "text":
                resp["content"] = resp["content"][0]["text"]

            # 处理 Bedrock 返回的 usage 信息
            usage_data = resp.get("usage", {})
            input_tokens = usage_data.get("input_tokens", 0)
            output_tokens = usage_data.get("output_tokens", 0)

            # Bedrock 可能包含缓存相关的 tokens
            cache_creation_tokens = usage_data.get("cache_creation_input_tokens", 0)
            cache_read_tokens = usage_data.get("cache_read_input_tokens", 0)

            # 总 input tokens = 常规 input + 缓存创建 + 缓存读取
            total_input = input_tokens + cache_creation_tokens + cache_read_tokens

            resp = ChatCompletion(
                id=resp["id"],
                choices=[
                    Choice(
                        index=0,
                        message=ChatCompletionMessage(
                            role=resp["role"],
                            content=resp["content"]
                        ),
                        finish_reason=resp.get("stop_reason") if resp.get("stop_reason") in ["stop", "length", "tool_calls", "content_filter", "function_call"] else "stop",
                        logprobs=resp.get("logprobs"),
                    )
                ],
                created=int(time.time()),
                model=resp["model"],
                object="chat.completion",
                usage= CompletionUsage(
                    prompt_tokens=total_input,
                    completion_tokens=output_tokens,
                    total_tokens=total_input + output_tokens,
                )
            ).model_dump()
    choices: list = resp.get("choices", [])
    if debug:
        logger.debug(f"API request to {repr(url)} returned choices: {json.dumps(choices, ensure_ascii=False, indent=2)}")

    for i in range(min(rollout_n, len(choices))):
        item = choices[i]
        if "message" in item:
            message = item["message"]
            content = message.get("content", "")
            reasoning_content = message.get("reasoning_content", "")

            # Handle reasoning content
            if reasoning_content:
                content = f"<think>\n{reasoning_content}\n</think>\n{content}"

            message["content"] = content
        elif "text" in item:
            content = item["text"]
            item["message"] = {
                "role": "assistant",
                "content": content,
            }

    # Fill remaining slots with None if needed
    if len(choices) < rollout_n:
        choices += [None] * (rollout_n - len(choices))

    resp["choices"] = choices

    # Final validation: ensure response has required fields for ChatCompletion
    # If the response still looks like an error, raise an exception now
    if isinstance(resp, dict):
        # Check for error indicators that might have slipped through
        if resp.get("success") is False:
            error_msg = resp.get("status_msg", "Unknown backend error")
            raise ValueError(f"Backend API error: {error_msg}")
        # For Claude models, ensure we have valid choices (not all None)
        if model and (model == "claude" or model.startswith("claude-")):
            if all(c is None for c in resp.get("choices", [])):
                # This likely means the Claude API returned an error we didn't catch
                logger.error(f"Claude API returned invalid response (no valid choices): {json.dumps(resp, ensure_ascii=False)[:500]}")
                raise ValueError(f"Claude API returned invalid response - no valid choices generated")

    logger.debug(f"Processed API response: {json.dumps(resp, ensure_ascii=False, indent=2)}")
    return resp


def prepare_embedding_request_params(
    user_id: str,
    token: str,
    input_text: Union[str, List[str]],
    model: str,
) -> tuple[str, dict, dict, dict]:
    """Prepare parameters for embedding API request"""
    # Prepare request parameters - try different parameter formats for hexin API
    # Let's try various formats that the API might expect
    params = {
        "input": input_text,  # Original format
        "model": model,
    }

    embedding_url = "https://arsenal-openai.10jqka.com.cn:8443/vtuber/ai_access/chatgpt/v1/embeddings"

    # Build headers
    headers = {
        # "Content-Type": "application/json",
        'Content-Type': 'application/x-www-form-urlencoded',
        "userId": user_id,
        "token": token
    }

    return embedding_url, params, headers

def print_embedding_info(response: CreateEmbeddingResponse) -> None:
    """打印embedding响应信息"""
    print(f"- Object: {response.object}")
    print(f"- Model: {response.model}")
    print(f"- Data count: {len(response.data)}")

    if response.data:
        for first in response.data:
            print(f"- embedding: {first.object}, index={first.index}, vector_length={len(first.embedding)}")
            print(f"- few values: {first.embedding[:5]}")

    if response.usage:
        print(f"- Usage: prompt_tokens={response.usage.prompt_tokens}, total_tokens={response.usage.total_tokens}")

def process_embedding_response(res: Response, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Process embedding API response"""
    try:
        resp = res.json()

        # if debug:

            # logger.debug(f"Embedding API response: {json.dumps(resp, ensure_ascii=False, indent=2)}")

        # Extract data from hexin response format
        # Try different possible response structures
        if "data" in resp:
            data = resp["data"]
            # Case 1: {"data": {"data": [...], "usage": {...}}}
            if "data" in data:
                return data
            # Case 2: {"data": [...]} where data is directly the embeddings array
            elif isinstance(data, list):
                return {"data": data}
            # Case 3: {"data": {...}} where data contains the complete response
            else:
                return data

        # Case 4: Direct response format without "data" wrapper
        elif "embeddings" in resp or ("object" in resp and resp.get("object") == "list"):
            return resp

        if debug:
            logger.warning(f"Unexpected embedding response format: {resp}")
        return None

    except Exception as e:
        if debug:
            logger.error(f"Error processing embedding response: {e}")
        return None


def create_embedding_response(
    embedding_data: Dict[str, Any],
    model: str,
    input_text: Union[str, List[str]],
) -> CreateEmbeddingResponse:
    """Create OpenAI-compatible embedding response"""

    # Convert input to list for consistent processing
    if isinstance(input_text, str):
        input_list = [input_text]
    else:
        input_list = input_text

    # Extract embeddings from response data
    embeddings_list = []
    if "data" in embedding_data:
        for item in embedding_data["data"]:
            embedding = Embedding(
                object="embedding",
                index=item.get("index", 0),
                embedding=item.get("embedding", [])
            )
            embeddings_list.append(embedding)

    # Create usage information
    usage_data = embedding_data.get("usage", {})
    usage = Usage(
        prompt_tokens=usage_data.get("prompt_tokens", len(" ".join(input_list))),
        total_tokens=usage_data.get("total_tokens", len(" ".join(input_list)))
    )

    return CreateEmbeddingResponse(
        object="list",
        data=embeddings_list,
        model=model,
        usage=usage
    )


def prepare_response_request_params(
    user_id: str,
    token: str,
    model: str,
    input_data: Union[str, List[Dict[str, Any]]],
    reasoning: Optional[Dict[str, Any]] = None,
    text: Optional[Dict[str, Any]] = None,
    instructions: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    temperature: Optional[float] = 1.0,
    top_p: Optional[float] = 1.0,
    stream: bool = False,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = "auto",
    parallel_tool_calls: Optional[bool] = True,
    store: Optional[bool] = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> tuple[str, dict, dict]:
    """Prepare parameters for responses API request"""

    # Base parameters according to OpenAI responses API spec
    params = {
        "model": model,
        "input": input_data,
    }

    # Add optional parameters
    if reasoning:
        params["reasoning"] = reasoning
    if text:
        params["text"] = text
    if instructions:
        params["instructions"] = instructions
    if max_output_tokens:
        params["max_output_tokens"] = max_output_tokens
    if temperature != 1.0:
        params["temperature"] = temperature
    if top_p != 1.0:
        params["top_p"] = top_p
    if stream:
        params["stream"] = stream
    if tools:
        params["tools"] = tools
    if tool_choice != "auto":
        params["tool_choice"] = tool_choice
    if parallel_tool_calls is not None:
        params["parallel_tool_calls"] = parallel_tool_calls
    if store is not None:
        params["store"] = store
    if metadata:
        params["metadata"] = metadata

    # Build URL - according to the documentation
    response_url = os.getenv("HITHINK_RESPONSE_URL")
    logger.debug(f"response_url: {response_url}")

    # Build headers
    headers = {
        "Content-Type": "application/json",
        "userId": user_id,
        "token": token
    }

    return response_url, params, headers


def process_response_api_response(res: Response, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Process responses API response"""
    try:
        resp = res.json()

        if debug:
            logger.debug(f"Responses API response: {json.dumps(resp, ensure_ascii=False, indent=2)}")

        # 检查是否返回了错误状态
        if "success" in resp and resp["success"] is False:
            error_msg = resp.get("status_msg", "Unknown error")
            error_code = resp.get("status_code", -1)
            logger.error(f"Backend API returned error (code: {error_code}): {error_msg}")
            raise ValueError(f"后端API错误 (代码: {error_code}): {error_msg}")

        # Extract data from hexin response format
        if "data" in resp:
            return resp["data"]
        else:
            return resp

    except Exception as e:
        if debug:
            logger.error(f"Error processing responses API response: {e}")
        return None


async def create_response_stream(
    response_data: Dict[str, Any],
    request_id: str,
) -> AsyncGenerator[str, None]:
    """Create streaming response for responses API"""

    # For streaming responses, we need to follow the SSE format from the documentation
    # The actual streaming would come from the backend API
    # This is a simplified version that yields the complete response as chunks

    # Send response.created event
    created_event = {
        "type": "response.created",
        "response": {
            "id": response_data.get("id", request_id),
            "object": "response",
            "created_at": response_data.get("created_at", int(time.time())),
            "status": "in_progress",
            "model": response_data.get("model"),
            "output": []
        }
    }
    yield f"event: response.created\ndata: {json.dumps(created_event)}\nretry: 300\n\n"

    # Send response.in_progress event
    progress_event = {
        "type": "response.in_progress",
        "response": created_event["response"]
    }
    yield f"event: response.in_progress\ndata: {json.dumps(progress_event)}\nretry: 300\n\n"

    # Process output items
    output_items = response_data.get("output", [])
    for i, item in enumerate(output_items):
        # Send output_item.added event
        added_event = {
            "type": "response.output_item.added",
            "output_index": i,
            "item": {
                "id": item.get("id"),
                "type": item.get("type"),
                "summary": item.get("summary", []) if item.get("type") == "reasoning" else None
            }
        }
        if added_event["item"]["summary"] is None:
            del added_event["item"]["summary"]
        yield f"event: response.output_item.added\ndata: {json.dumps(added_event)}\nretry: 300\n\n"

        # For reasoning items, send summary parts
        if item.get("type") == "reasoning" and "summary" in item:
            for j, summary_part in enumerate(item["summary"]):
                summary_event = {
                    "type": "response.reasoning_summary_part.added",
                    "item_id": item.get("id"),
                    "output_index": i,
                    "summary_index": j,
                    "part": summary_part
                }
                yield f"event: response.reasoning_summary_part.added\ndata: {json.dumps(summary_event)}\nretry: 300\n\n"

        # Send output_item.done event
        done_event = {
            "type": "response.output_item.done",
            "output_index": i,
            "item": item
        }
        yield f"event: response.output_item.done\ndata: {json.dumps(done_event)}\nretry: 300\n\n"

    # Send final completed event
    completed_event = {
        "type": "response.completed",
        "response": response_data
    }
    yield f"event: response.completed\ndata: {json.dumps(completed_event)}\nretry: 300\n\n"


# Global variables for authentication
USER_ID: Optional[str] = None
TOKEN: Optional[str] = None

# Fixed API key for client authentication
FIXED_API_KEY = "sk-fastapi-proxy-key-12345"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize authentication on startup"""
    global USER_ID, TOKEN

    app_url = os.getenv("HITHINK_APP_URL")
    app_id = os.getenv("HITHINK_APP_ID")
    app_secret = os.getenv("HITHINK_APP_SECRET")

    if not app_id or not app_secret:
        raise ValueError("HITHINK_APP_ID and HITHINK_APP_SECRET must be set in environment variables.")

    try:
        USER_ID, TOKEN = get_userid_and_token(app_url=app_url, app_id=app_id, app_secret=app_secret)
        logger.info(f"Authentication successful. User ID: {USER_ID}")
    except Exception as e:
        logger.error(f"Failed to authenticate: {e}")
        raise

    yield

    # Cleanup (if needed)
    logger.info("Shutting down FastAPI server")


app = FastAPI(
    title="OpenAI API Proxy",
    description="A FastAPI server that proxies OpenAI API endpoints using hexin_engine backend",
    version="1.0.0",
    lifespan=lifespan
)


def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use 'Bearer <api_key>'")

    api_key = authorization[7:]  # Remove "Bearer " prefix
    if api_key != FIXED_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


# Pydantic models for request/response
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.6
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, Any]]] = None
    reasoning_effort: Optional[str] = None  # 支持 "low", "medium", "high"
    debug: Optional[bool] = True


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: Optional[str] = "text-embedding-ada-002"
    user: Optional[str] = None
    debug: Optional[bool] = True


class ReasoningConfig(BaseModel):
    effort: Optional[str] = "medium"  # "low", "medium", "high"
    summary: Optional[str] = "detailed"  # "brief", "detailed"


class ResponseRequest(BaseModel):
    model: str
    input: Union[str, List[Dict[str, Any]]]  # Can be string or messages array
    reasoning: Optional[ReasoningConfig] = None
    text: Optional[Dict[str, Any]] = None
    instructions: Optional[str] = None
    max_output_tokens: Optional[int] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = "auto"
    parallel_tool_calls: Optional[bool] = True
    store: Optional[bool] = True
    metadata: Optional[Dict[str, Any]] = None
    debug: Optional[bool] = True


def simplify_params_for_logging(params: Dict[str, Any]) -> Dict[str, Any]:
    """简化 params 用于日志打印，将 tools 参数简化为只显示个数和名称"""
    if not params:
        return params

    simplified = copy.deepcopy(params)

    # 简化 tools 参数
    if "tools" in simplified and simplified["tools"]:
        tools = simplified["tools"]
        tool_names = []
        for tool in tools:
            if isinstance(tool, dict):
                # OpenAI format: {"type": "function", "function": {"name": "..."}}
                if "function" in tool and "name" in tool["function"]:
                    tool_names.append(tool["function"]["name"])
                # Anthropic format: {"name": "..."}
                elif "name" in tool:
                    tool_names.append(tool["name"])
        simplified["tools"] = f"<{len(tools)} tools: {', '.join(tool_names)}>"

    return simplified


class ListModelsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: List[Model]


# Available models mapping
AVAILABLE_MODELS = [
    {
        "id": "gpt-3.5-turbo",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
    {
        "id": "gpt-4o",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
    {
        "id": "gpt-4o-mini",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
    {
        "id": "o3",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
    {
        "id": "o4-mini",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
    {
        "id": "gpt4",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
    {
        "id": "claude",
        "object": "model",
        "created": 1677610602,
        "owned_by": "anthropic",
    },
    {
        "id": "gemini",
        "object": "model",
        "created": 1677610602,
        "owned_by": "google",
    },
    {
        "id": "doubao-deepseek-r1",
        "object": "model",
        "created": 1677610602,
        "owned_by": "bytedance",
    },
    {
        "id": "ep-20250204210426-gclbn",
        "object": "model",
        "created": 1677610602,
        "owned_by": "bytedance",
    },
    {
        "id": "deepseek-reasoner",
        "object": "model",
        "created": 1677610602,
        "owned_by": "deepseek",
    },
    {
        "id": "doubao-deepseek-v3",
        "object": "model",
        "created": 1677610602,
        "owned_by": "bytedance",
    },
    {
        "id": "ep-20250410145517-rpbrz",
        "object": "model",
        "created": 1677610602,
        "owned_by": "bytedance",
    },
    {
        "id": "deepseek-chat",
        "object": "model",
        "created": 1677610602,
        "owned_by": "deepseek",
    },
    {
        "id": "r1-qianfan",
        "object": "model",
        "created": 1677610602,
        "owned_by": "baidu",
    },
    # Embedding models
    {
        "id": "text-embedding-ada-002",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
    {
        "id": "text-embedding-3-small",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
    {
        "id": "text-embedding-3-large",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
    },
]




def create_chat_completion_response(
    resp: dict,
) -> ChatCompletion:
    result = ChatCompletion.model_validate(resp)
    return result


async def create_chat_completion_stream(
    resp: dict,
) -> AsyncGenerator[str, None]:
    """Create streaming response for chat completion"""
    result = ChatCompletion.model_validate(resp)
    choices = []
    for c in result.choices:
        tool_calls = c.message.tool_calls if hasattr(c.message, 'tool_calls') else None
        function_call = c.message.function_call if hasattr(c.message, 'function_call') else None
        refusal = c.message.refusal if hasattr(c.message, 'refusal') else None
        delta_tool_calls = None
        if tool_calls:
            delta_tool_calls = []
            for i, tool_call in enumerate(tool_calls):
                delta_tool_calls.append(ChoiceDeltaToolCall(
                    index=i,
                    id=tool_call.id,
                    type=tool_call.type,
                    function=ChoiceDeltaToolCallFunction(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    )
                ))
        if function_call:
            function_call = ChoiceDeltaFunctionCall(
                name=function_call.name,
                arguments=function_call.arguments,
            )
        chunk_delta = ChoiceDelta(
            role=c.message.role,
            content=c.message.content,
            tool_calls=delta_tool_calls,
            function_call=function_call,
            refusal=refusal,
        )
        chunk_choice = ChunkChoice(
            index=c.index,
            delta=chunk_delta,
            finish_reason=c.finish_reason,
            logprobs=c.logprobs,
        )
        choices.append(chunk_choice)
    chunk = ChatCompletionChunk(
        id=result.id,
        choices=choices,
        created=result.created,
        model=result.model,
        object="chat.completion.chunk",
        service_tier=result.service_tier,
        system_fingerprint=result.system_fingerprint,
        usage=result.usage,
    )
    yield f"data: {chunk.model_dump_json()}\n\n"
    yield "data: [DONE]\n\n"


@app.get("/v1/models", response_model=ListModelsResponse)
async def list_models(api_key: str = Header(None, alias="authorization")):
    """List available models"""
    verify_api_key(api_key)
    models = [Model(**model_data) for model_data in AVAILABLE_MODELS]
    return ListModelsResponse(data=models)


@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest, authorization: Optional[str] = Header(None), request_original: Request = None):
    """Create a chat completion"""
    # Verify API key
    verify_api_key(authorization)

    global USER_ID, TOKEN

    if not USER_ID or not TOKEN:
        raise HTTPException(status_code=500, detail="Server authentication not initialized")

    # 保存原始请求用于日志记录
    log_request_headers = sanitize_headers_for_logging(dict(request_original.headers)) if request_original else None
    log_request_body = await request_original.json() if request_original else None

    # Extract parameters
    model = request.model
    messages = request.messages
    max_tokens = request.max_tokens or 1000
    temperature = request.temperature or 0.6
    top_p = request.top_p or 1.0
    n = request.n or 1
    stream = request.stream or False
    tools = request.tools
    functions = request.functions
    function_call = request.function_call
    reasoning_effort = request.reasoning_effort
    request_original_json = log_request_body or {}
    thinking = request_original_json.get('thinking', None)
    debug = request.debug or False
    # Validate model
    # available_model_ids = [m["id"] for m in AVAILABLE_MODELS]
    # if model not in available_model_ids:
    #     raise HTTPException(status_code=400, detail=f"Model {model} not available")

    request_id = f"chatcmpl-{uuid.uuid4().hex}"

    try:
        # Prepare API request parameters
        chat_url, params, headers, rollout_n = prepare_api_request_params(
            user_id=USER_ID,
            token=TOKEN,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=n,
            tools=tools,
            functions=functions,
            function_call=function_call,
            reasoning_effort=reasoning_effort,
            thinking=thinking,
        )

        logger.info(f"Chat completion request ID: {request_id}\nrollout_n = {rollout_n}\n{json.dumps(params, ensure_ascii=False, indent=2)}")

        if rollout_n and rollout_n > 1:
            logger.warning(f"Model {model} does not support n-sampling, manually requesting {rollout_n} completions.")
            async def async_request(i):
                # Call the backend API directly
                res = api_request(
                    url=chat_url,
                    params=params,
                    headers=headers,
                    timeout=TIMEOUT,
                )
                res.raise_for_status()

                resp = process_api_response(
                    res,
                    url=chat_url,
                    model=model,
                    debug=debug,
                    rollout_n=1,
                )
                return resp
            resp_list = await xmap_async(list(range(rollout_n)), async_request, is_async_work_func=True)
            resp = resp_list[0]
            resp["choices"] = sum([resp_item["choices"] for resp_item in resp_list], [])
        else:
            # Call the backend API directly
            res = api_request(
                url=chat_url,
                params=params,
                headers=headers,
                timeout=TIMEOUT,
            )
            res.raise_for_status()

            resp = process_api_response(
                res,
                url=chat_url,
                model=model,
                debug=debug,
                rollout_n=rollout_n,
            )

        if stream:
            # 流式响应 - 使用包装器收集内容用于日志
            async def logged_stream():
                stream_buffer = None
                if API_LOGGER:
                    stream_buffer = StreamLogBuffer(
                        api_logger=API_LOGGER,
                        endpoint="chat_completions",
                        input_messages=messages,
                        tools=tools,
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        n=n,
                    )

                async for chunk in create_chat_completion_stream(resp):
                    # 解析chunk提取内容用于日志
                    if stream_buffer and chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                        try:
                            chunk_json = json.loads(chunk[6:])
                            for choice in chunk_json.get("choices", []):
                                delta = choice.get("delta", {})
                                if delta.get("content"):
                                    stream_buffer.add_content(delta["content"])
                                if delta.get("tool_calls"):
                                    for tc in delta["tool_calls"]:
                                        stream_buffer.add_tool_call(tc)
                        except json.JSONDecodeError:
                            pass
                    yield chunk

                # 流结束时记录日志
                if stream_buffer:
                    stream_buffer.finalize()

            return StreamingResponse(
                logged_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # Non-streaming response
            completion = create_chat_completion_response(resp)

            # 记录日志
            if API_LOGGER:
                output_messages = []
                for choice in completion.choices:
                    msg = choice.message
                    output_msg: Dict[str, Any] = {
                        "role": msg.role,
                        "content": msg.content,
                    }
                    if msg.tool_calls:
                        output_msg["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                }
                            }
                            for tc in msg.tool_calls
                        ]
                    output_messages.append(output_msg)

                # 提取 usage 信息
                usage_dict = None
                if completion.usage:
                    usage_dict = {
                        "prompt_tokens": completion.usage.prompt_tokens,
                        "completion_tokens": completion.usage.completion_tokens,
                        "total_tokens": completion.usage.total_tokens,
                    }

                log_api_request(
                    endpoint="chat_completions",
                    input_messages=messages,
                    output_messages=output_messages,
                    tools=tools,
                    model=model,
                    request_headers=log_request_headers,
                    request_body=log_request_body,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    n=n,
                    stream=False,
                    usage=usage_dict,
                )

            return completion

    except Exception as e:
        logger.error(f"Error in chat completion: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest, authorization: Optional[str] = Header(None)):
    """Create embeddings for the given input"""
    # Verify API key
    verify_api_key(authorization)

    global USER_ID, TOKEN

    if not USER_ID or not TOKEN:
        raise HTTPException(status_code=500, detail="Server authentication not initialized")

    # Extract parameters
    input_text = request.input
    model = request.model or "text-embedding-ada-002"
    debug = request.debug if request.debug is not None else True

    # Validate model - check if it's a supported embedding model
    # embedding_models = ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]
    # if model not in embedding_models:
    #     raise HTTPException(status_code=400, detail=f"Embedding model {model} not supported. Available models: {embedding_models}")

    try:
        # Prepare API request parameters
        embedding_url, params, headers = prepare_embedding_request_params(
            user_id=USER_ID,
            token=TOKEN,
            input_text=input_text,
            model=model,
        )

        if debug:
            logger.debug(f"Embedding request URL: {embedding_url}")
            logger.debug(f"Embedding request params: {json.dumps(simplify_params_for_logging(params), ensure_ascii=False, indent=2)}")

        # Try primary request first
        res = requests.post(
            embedding_url,
            data=urlencode(params),
            headers=headers,
            timeout=TIMEOUT,
        )
        res.raise_for_status()

        # Process the response
        embedding_data = process_embedding_response(res, debug=debug)

        if not embedding_data:
            raise HTTPException(status_code=500, detail="Failed to get valid embedding response from backend")

        # Create OpenAI-compatible response
        embedding_response = create_embedding_response(
            embedding_data=embedding_data,
            model=model,
            input_text=input_text,
        )

        return embedding_response

    except Exception as e:
        logger.error(f"Error in embedding creation: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/responses")
async def create_response(request: ResponseRequest, authorization: Optional[str] = Header(None), request_original: Request = None):
    """Create a response using OpenAI's responses API"""
    # Verify API key
    verify_api_key(authorization)

    global USER_ID, TOKEN

    if not USER_ID or not TOKEN:
        raise HTTPException(status_code=500, detail="Server authentication not initialized")

    # 保存原始请求用于日志记录
    log_request_headers = sanitize_headers_for_logging(dict(request_original.headers)) if request_original else None
    log_request_body = await request_original.json() if request_original else None

    # Extract parameters
    model = request.model
    input_data = request.input
    reasoning = request.reasoning.model_dump() if request.reasoning else None
    text = request.text
    instructions = request.instructions
    max_output_tokens = request.max_output_tokens
    temperature = request.temperature or 1.0
    top_p = request.top_p or 1.0
    stream = request.stream or False
    tools = request.tools
    tool_choice = request.tool_choice or "auto"
    parallel_tool_calls = request.parallel_tool_calls
    store = request.store
    metadata = request.metadata
    debug = request.debug if request.debug is not None else True

    session_id = request_original.headers.get('X-Session-ID', None) if request_original else None

    # Validate model - responses API supports specific models
    # supported_models = ["o3", "o4-mini"]
    # if model not in supported_models:
    #     raise HTTPException(status_code=400, detail=f"Model {model} not supported for responses API. Supported models: {supported_models}")

    try:
        # Prepare API request parameters
        response_url, params, headers = prepare_response_request_params(
            user_id=USER_ID,
            token=TOKEN,
            model=model,
            input_data=input_data,
            reasoning=reasoning,
            text=text,
            instructions=instructions,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=stream,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            store=store,
            metadata=metadata,
        )
        # 同一个session_id会打到同一个微软节点
        if not session_id:
            session_id = str(uuid.uuid4())
        headers["arsenal-openai-hash"] = session_id
        headers["X-Trace-Id"] = session_id

        if debug:
            logger.debug(f"session_id: {session_id}")
            logger.debug(f"headers: {headers}")
            logger.debug(f"Responses request URL: {response_url}")
            logger.debug(f"Responses request params: {json.dumps(simplify_params_for_logging(params), ensure_ascii=False, indent=2)}")

        # 构建用于日志的输入消息
        if isinstance(input_data, str):
            log_input_messages = [{"role": "user", "content": input_data}]
        else:
            log_input_messages = input_data

        # Call the backend API
        if stream:
            # Create a streaming response that forwards SSE events
            def forward_sse_stream_with_logging():
                client = httpx.Client()
                content_buffer = ""
                tool_calls_buffer: List[Dict[str, Any]] = []

                with client.stream("POST", response_url, json=params, headers=headers, timeout=TIMEOUT) as res:
                    # Check if the response is actually an SSE stream
                    content_type = res.headers.get("content-type", "")
                    if "text/event-stream" not in content_type:
                        # Upstream returned non-SSE response (likely an error as JSON)
                        error_body = res.read().decode("utf-8")
                        logger.error(f"Upstream returned non-SSE response (status={res.status_code}, content-type={content_type}): {error_body}")
                        # Yield an error event to the client
                        error_event = {
                            "type": "error",
                            "error": {
                                "type": "upstream_error",
                                "message": f"Upstream error (status={res.status_code}): {error_body}"
                            }
                        }
                        yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
                        return
                    for event in httpx_sse.EventSource(res).iter_sse():
                        sse_text = f"event: {event.event}\ndata: {event.data}\n\n"
                        yield sse_text

                        # 解析 SSE 事件收集内容用于日志
                        if API_LOGGER and event.event in ["response.output_text.delta", "response.output_item.done"]:
                            try:
                                event_data = json.loads(event.data)
                                if event.event == "response.output_text.delta":
                                    content_buffer += event_data.get("delta", "")
                                elif event.event == "response.output_item.done":
                                    item = event_data.get("item", {})
                                    if item.get("type") == "function_call":
                                        tool_calls_buffer.append({
                                            "id": item.get("call_id"),
                                            "type": "function",
                                            "function": {
                                                "name": item.get("name"),
                                                "arguments": item.get("arguments"),
                                            }
                                        })
                            except json.JSONDecodeError:
                                pass

                # 流结束时记录日志
                if API_LOGGER:
                    output_msg: Dict[str, Any] = {
                        "role": "assistant",
                        "content": content_buffer if content_buffer else None,
                    }
                    if tool_calls_buffer:
                        output_msg["tool_calls"] = tool_calls_buffer

                    log_api_request(
                        endpoint="responses",
                        input_messages=log_input_messages,
                        output_messages=[output_msg],
                        tools=tools,
                        model=model,
                        request_headers=log_request_headers,
                        request_body=log_request_body,
                        max_output_tokens=max_output_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        stream=True,
                    )

            return StreamingResponse(
                forward_sse_stream_with_logging(),
                media_type="text/event-stream",
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )
        else:
            # Non-streaming request with retry logic
            max_retries = 3
            retry_delay = 2  # 秒
            last_error = None

            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        logger.warning(f"Retrying responses API call (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay * attempt)  # 递增延迟

                    res = requests.post(
                        response_url,
                        json=params,
                        headers=headers,
                        timeout=TIMEOUT,
                    )
                    res.raise_for_status()

                    # Process the response
                    response_data = process_response_api_response(res, debug=debug)

                    if not response_data:
                        raise ValueError("后端返回的响应数据为空")

                    # 记录日志
                    if API_LOGGER:
                        output_messages = []
                        for output_item in response_data.get("output", []):
                            if output_item.get("type") == "message":
                                for content_item in output_item.get("content", []):
                                    if content_item.get("type") == "output_text":
                                        output_messages.append({
                                            "role": "assistant",
                                            "content": content_item.get("text"),
                                        })
                            elif output_item.get("type") == "function_call":
                                output_messages.append({
                                    "role": "assistant",
                                    "content": None,
                                    "tool_calls": [{
                                        "id": output_item.get("call_id"),
                                        "type": "function",
                                        "function": {
                                            "name": output_item.get("name"),
                                            "arguments": output_item.get("arguments"),
                                        }
                                    }]
                                })

                        if not output_messages:
                            # fallback: 直接使用 response_data
                            output_messages = [{"role": "assistant", "content": json.dumps(response_data.get("output", []), ensure_ascii=False)}]

                        # 提取 usage 信息 (responses API 格式)
                        usage_dict = None
                        usage_data = response_data.get("usage")
                        if usage_data:
                            usage_dict = {
                                "input_tokens": usage_data.get("input_tokens"),
                                "output_tokens": usage_data.get("output_tokens"),
                                "total_tokens": usage_data.get("total_tokens"),
                            }

                        log_api_request(
                            endpoint="responses",
                            input_messages=log_input_messages,
                            output_messages=output_messages,
                            tools=tools,
                            model=model,
                            request_headers=log_request_headers,
                            request_body=log_request_body,
                            max_output_tokens=max_output_tokens,
                            temperature=temperature,
                            top_p=top_p,
                            stream=False,
                            usage=usage_dict,
                        )

                    # Return the response directly (it should already be in OpenAI format)
                    return response_data

                except ValueError as e:
                    # ValueError 是由 process_response_api_response 抛出的业务错误
                    last_error = e
                    error_msg = str(e)
                    if "Connection reset" in error_msg or "SocketException" in error_msg:
                        logger.warning(f"连接被重置，尝试重试... ({attempt + 1}/{max_retries})")
                        continue
                    else:
                        # 其他业务错误不重试
                        raise HTTPException(status_code=500, detail=str(e))

                except requests.exceptions.Timeout as e:
                    last_error = e
                    logger.warning(f"请求超时，尝试重试... ({attempt + 1}/{max_retries})")
                    continue

                except requests.exceptions.ConnectionError as e:
                    last_error = e
                    logger.warning(f"连接错误，尝试重试... ({attempt + 1}/{max_retries})")
                    continue

                except Exception as e:
                    last_error = e
                    logger.error(f"请求失败: {e}\n{traceback.format_exc()}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        break

            # 如果所有重试都失败了
            error_detail = f"在 {max_retries} 次重试后仍然失败: {str(last_error)}"
            logger.error(error_detail)
            raise HTTPException(status_code=500, detail=error_detail)

    except Exception as e:
        logger.error(f"Error in response creation: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error in response creation: {e}\n{traceback.format_exc()}")


def verify_claude_api_key(x_api_key: Optional[str] = None, authorization: Optional[str] = None):
    """Verify API key from x-api-key or Authorization header"""
    logger.info(f"Received x-api-key: {x_api_key}")
    logger.info(f"Received authorization: {authorization}")
    logger.info(f"Expected API key: {FIXED_API_KEY}")

    # Try x-api-key first
    api_key = x_api_key

    # If no x-api-key, try Authorization Bearer
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]  # Remove "Bearer " prefix
            logger.info(f"Extracted API key from Authorization header: {api_key}")

    if not api_key:
        logger.error("No API key found in x-api-key or Authorization header")
        raise HTTPException(
            status_code=401,
            detail={"type": "error", "error": {"type": "authentication_error", "message": "API key required (use x-api-key header or Authorization: Bearer)"}}
        )

    if api_key != FIXED_API_KEY:
        logger.error(f"Invalid API key. Received: {api_key}, Expected: {FIXED_API_KEY}")
        raise HTTPException(
            status_code=401,
            detail={"type": "error", "error": {"type": "authentication_error", "message": "invalid API key"}}
        )

    logger.info("API key verification successful")
    return api_key


@app.post("/v1/messages")
async def create_message(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    request_obj: Request = None
):
    """Create a message using Anthropic Messages API format"""
    # 保存原始请求用于日志记录
    log_request_headers = None
    log_request_body = None
    body = {}

    # Log all headers for debugging
    if request_obj:
        log_request_headers = sanitize_headers_for_logging(dict(request_obj.headers))
        body = await request_obj.json()
        log_request_body = body

    # Verify API key (supports both x-api-key and Authorization: Bearer)
    verify_claude_api_key(x_api_key=x_api_key, authorization=authorization)

    global USER_ID, TOKEN

    if not USER_ID or not TOKEN:
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "error": {"type": "api_error", "message": "Server authentication not initialized"}}
        )

    # Extract parameters from request body (support all Anthropic SDK parameters)
    model = body.get("model")
    max_tokens = body.get("max_tokens", 4096)
    temperature = body.get("temperature")
    top_p = body.get("top_p")
    top_k = body.get("top_k")
    stream = body.get("stream", False)
    messages = body.get("messages", [])
    system = body.get("system")
    stop_sequences = body.get("stop_sequences")
    tools = body.get("tools")
    tool_choice = body.get("tool_choice")
    metadata = body.get("metadata")
    thinking = body.get("thinking")

    request_id = f"msg_{uuid.uuid4().hex}"

    # 构建用于日志的 input_messages，包含 system
    log_input_messages = []
    if system:
        log_input_messages.append({"role": "system", "content": system})
    log_input_messages.extend(messages)

    try:
        # 转换消息格式 (使用 SDK 类型，转换为字典)
        hexin_messages = messages


        # Map Claude model names to backend model IDs
        # Backend supports these models:
        # - us.anthropic.claude-3-5-sonnet-20241022-v2:0
        # - us.anthropic.claude-3-7-sonnet-20250219-v1:0
        # - us.anthropic.claude-sonnet-4-20250514-v1:0
        # - us.anthropic.claude-opus-4-20250514-v1:0
        # - us.anthropic.claude-sonnet-4-5-20250929-v1:0
        # - global.anthropic.claude-opus-4-5-20251101-v1:0

        # If model already has the full prefix, use it directly
        if model.startswith("us.anthropic.") or model.startswith("global.anthropic."):
            backend_model = model
            # Ensure it has the version suffix
            if not backend_model.endswith(":0"):
                backend_model += ":0"
        else:
            # Map common model names to backend models
            backend_model = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"  # Default

            if "4.5" in model or "4-5" in model:
                # Claude 4.5 series
                if "opus" in model.lower():
                    backend_model = "global.anthropic.claude-opus-4-5-20251101-v1:0"
                elif "sonnet" in model.lower():
                    backend_model = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
                elif "haiku" in model.lower():
                    backend_model = "us.anthropic.claude-sonnet-4-20250514-v1:0"
                else:
                    backend_model = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
            elif "4" in model and ("opus" in model.lower() or "sonnet" in model.lower()):
                # Claude 4 series
                if "opus" in model.lower():
                    backend_model = "us.anthropic.claude-opus-4-20250514-v1:0"
                else:
                    backend_model = "us.anthropic.claude-sonnet-4-20250514-v1:0"
            elif "3.7" in model or "3-7" in model:
                # Claude 3.7 series
                backend_model = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
            elif "3.5" in model or "3-5" in model or model.startswith("claude-3-5"):
                # Claude 3.5 series
                backend_model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

        # Set appropriate max_tokens limit based on model
        if "3-5-sonnet" in backend_model or "3.5" in model:
            # Claude 3.5 Sonnet has max 8192 tokens
            if max_tokens > 8192:
                max_tokens = 8192
        elif max_tokens > 32000:
            # Other models have higher limits
            max_tokens = 32000

        # 准备请求参数 (Amazon Bedrock 格式)
        params = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": hexin_messages,
        }
        if system:
            params["system"] = system

        # 添加可选参数
        # 注意：Bedrock Claude 不允许同时指定 temperature 和 top_p
        # 优先使用 temperature，如果没有则使用 top_p
        if temperature is not None:
            params["temperature"] = temperature
        elif top_p is not None:
            params["top_p"] = top_p

        if top_k is not None:
            params["top_k"] = top_k

        if stop_sequences:
            params["stop_sequences"] = stop_sequences

        # 添加工具调用支持
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice

        # 添加元数据和思考配置支持
        if metadata:
            params["metadata"] = metadata
        if thinking:
            params["thinking"] = thinking

        # API URL (Bedrock 格式：model ID 在 URL 中)
        # 流式调用使用 invoke-with-response-stream，非流式使用 invoke
        if stream:
            chat_url = f"https://arsenal-openai.10jqka.com.cn:8443/vtuber/ai_access/claude/model/{backend_model}/invoke-with-response-stream"
        else:
            chat_url = f"https://arsenal-openai.10jqka.com.cn:8443/vtuber/ai_access/claude/model/{backend_model}/invoke"

        # Headers (Bedrock 使用 token 或 Authorization)
        headers = {
            "Content-Type": "application/json",
            "token": TOKEN,
        }

        logger.info(f"Claude Messages API request ID: {request_id}\nModel: {model}\nMessages: {len(hexin_messages)}\nStream: {stream}")
        logger.debug(f"Request params: {json.dumps(simplify_params_for_logging(params), ensure_ascii=False, indent=2)}")

        if stream:
            # 流式调用：转发 SSE 事件，转换格式以兼容 Anthropic SDK
            def forward_claude_stream_with_logging():
                """
                转发 Claude Bedrock 流式响应并记录日志。

                后端返回格式：
                    data:{"type":"message_start",...}
                    retry:300
                    (空行)

                Anthropic SDK 期望格式：
                    event: message_start
                    data: {"type":"message_start",...}
                    (空行)

                需要添加 event: 行，SDK 依赖它来过滤和处理事件。
                """
                content_buffer = ""
                tool_calls_buffer: List[Dict[str, Any]] = []

                try:
                    with httpx.Client(timeout=120.0) as client:
                        with client.stream("POST", chat_url, json=params, headers=headers) as response:
                            # 检查是否为 SSE 流
                            content_type = response.headers.get("content-type", "")
                            if "text/event-stream" not in content_type:
                                error_body = response.read().decode("utf-8")
                                logger.error(f"Backend returned non-SSE response (status={response.status_code}): {error_body}")
                                error_event = {
                                    "type": "error",
                                    "error": {
                                        "type": "upstream_error",
                                        "message": f"Backend error (status={response.status_code}): {error_body}"
                                    }
                                }
                                yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
                                return

                            if response.status_code != 200:
                                error_body = response.read().decode("utf-8")
                                logger.error(f"Backend returned error (status={response.status_code}): {error_body}")
                                error_event = {
                                    "type": "error",
                                    "error": {
                                        "type": "api_error",
                                        "message": f"Backend error (status={response.status_code}): {error_body}"
                                    }
                                }
                                yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
                                return

                            # 处理流式响应 - 转换 Bedrock 格式为 Anthropic SSE 格式
                            for line in response.iter_lines():
                                # 跳过空行和 retry 指令
                                if not line or line.startswith("retry:"):
                                    continue

                                # 处理 data 行: "data:{json}" -> "event: {type}\ndata: {json}\n\n"
                                if line.startswith("data:"):
                                    json_str = line[5:]  # 移除 "data:" 前缀
                                    try:
                                        data = json.loads(json_str)
                                        event_type = data.get("type", "unknown")

                                        # 收集内容用于日志
                                        if event_type == "content_block_delta":
                                            delta = data.get("delta", {})
                                            if delta.get("type") == "text_delta":
                                                content_buffer += delta.get("text", "")
                                        elif event_type == "content_block_start":
                                            # 检查是否有 tool_use
                                            content_block = data.get("content_block", {})
                                            if content_block.get("type") == "tool_use":
                                                tool_calls_buffer.append({
                                                    "id": content_block.get("id"),
                                                    "type": "function",
                                                    "function": {
                                                        "name": content_block.get("name"),
                                                        "arguments": "",
                                                    }
                                                })

                                        # 输出转换后的 SSE 格式
                                        yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                                    except json.JSONDecodeError:
                                        # 非 JSON 数据，原样输出
                                        yield f"data: {json_str}\n\n"
                                    continue

                                # 处理 event 行（如果已有则原样输出）
                                if line.startswith("event:"):
                                    yield f"{line}\n"
                                    continue

                                # 尝试解析为原始 JSON（兜底）
                                try:
                                    data = json.loads(line)
                                    event_type = data.get("type", "unknown")
                                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                                except json.JSONDecodeError:
                                    # 未知格式，跳过
                                    pass

                    # 流结束时记录日志
                    if API_LOGGER:
                        output_msg: Dict[str, Any] = {
                            "role": "assistant",
                            "content": content_buffer if content_buffer else None,
                        }
                        if tool_calls_buffer:
                            output_msg["tool_calls"] = tool_calls_buffer

                        log_api_request(
                            endpoint="messages",
                            input_messages=log_input_messages,
                            output_messages=[output_msg],
                            tools=tools,
                            model=model,
                            request_headers=log_request_headers,
                            request_body=log_request_body,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            top_p=top_p,
                            stream=True,
                        )

                except httpx.TimeoutException:
                    logger.error("Claude streaming request timed out")
                    error_event = {
                        "type": "error",
                        "error": {"type": "timeout_error", "message": "Request timed out"}
                    }
                    yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
                except Exception as e:
                    logger.error(f"Claude streaming error: {e}\n{traceback.format_exc()}")
                    error_event = {
                        "type": "error",
                        "error": {"type": "api_error", "message": str(e)}
                    }
                    yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

            return StreamingResponse(
                forward_claude_stream_with_logging(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
                }
            )
        else:
            # 非流式调用：直接返回响应
            res = api_request(
                url=chat_url,
                params=params,
                headers=headers,
                timeout=60,
            )

            # 处理响应
            hexin_response = res.json()
            logger.debug(f"Hexin response: {json.dumps(hexin_response, ensure_ascii=False, indent=2)}")

            # 检查后端是否返回错误
            if isinstance(hexin_response, dict) and hexin_response.get("success") is False:
                error_msg = hexin_response.get("status_msg", "Unknown error")
                error_code = hexin_response.get("status_code", -1)
                logger.error(f"Backend API error (code: {error_code}): {error_msg}")
                raise HTTPException(
                    status_code=502,  # Bad Gateway - 后端服务错误
                    detail={
                        "type": "error",
                        "error": {
                            "type": "api_error",
                            "message": f"Backend error: {error_msg} (code: {error_code})"
                        }
                    }
                )

            # 记录日志
            if API_LOGGER:
                output_messages = []
                content_items = hexin_response.get("content", [])
                content_text = ""
                tool_calls = []

                for item in content_items:
                    if item.get("type") == "text":
                        content_text += item.get("text", "")
                    elif item.get("type") == "tool_use":
                        tool_calls.append({
                            "id": item.get("id"),
                            "type": "function",
                            "function": {
                                "name": item.get("name"),
                                "arguments": json.dumps(item.get("input", {}), ensure_ascii=False),
                            }
                        })

                output_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": content_text if content_text else None,
                }
                if tool_calls:
                    output_msg["tool_calls"] = tool_calls

                # 提取 usage 信息 (Anthropic Messages API 格式)
                usage_dict = None
                usage_data = hexin_response.get("usage")
                if usage_data:
                    usage_dict = {
                        "input_tokens": usage_data.get("input_tokens"),
                        "output_tokens": usage_data.get("output_tokens"),
                    }

                log_api_request(
                    endpoint="messages",
                    input_messages=log_input_messages,
                    output_messages=[output_msg],
                    tools=tools,
                    model=model,
                    request_headers=log_request_headers,
                    request_body=log_request_body,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stream=False,
                    usage=usage_dict,
                )

            # 返回标准响应
            return JSONResponse(content=hexin_response)
    except Exception as e:
        logger.error(f"Error in create message: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={"type": "error", "error": {"type": "api_error", "message": str(e)}}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "authenticated": USER_ID is not None and TOKEN is not None}


def main():
    """Main entry point for the hexin_server module"""
    global API_LOGGER

    parser = argparse.ArgumentParser(
        description="Run the FastAPI server for OpenAI API proxy",
        prog="python -m hexin_server"
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8777, help="Port to bind to (default: 8777)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", type=str, default="info", choices=["debug", "info", "warning", "error"], help="Log level (default: info)")
    parser.add_argument("--env-file", type=str, default=".env", help="Path to environment file (default: .env)")
    parser.add_argument("--log-dir", type=str, default="output/logs", help="Directory to store API logs in jsonlist format (default: output/logs)")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (default: 1)")

    args = parser.parse_args()

    print(f"Loading environment variables from {Path(args.env_file).resolve()}")
    load_dotenv(args.env_file)
    print(f"Starting Hexin Server on {args.host}:{args.port}")
    print(f"Log level: {args.log_level}")
    if args.reload:
        print("Auto-reload enabled")

    # Initialize API logger
    API_LOGGER = APILogger(log_dir=args.log_dir)
    print(f"API logging enabled: {Path(args.log_dir).resolve()}")
    print(f"  - Logs are stored in jsonlist format")
    print(f"  - Structure: <log_dir>/<endpoint>/<date>/<timestamp>.rollout.jsonl")
    print(f"  - Each file contains up to 100 entries")

    print(f"BASE_URL = \"http://{args.host}:{args.port}\"")
    print(f"API_KEY = \"{FIXED_API_KEY}\"")

    try:
        uvicorn.run(
            "hexin_server.__main__:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            workers=args.workers,
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
