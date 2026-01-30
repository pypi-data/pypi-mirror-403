"""
NexAgent 核心模块
"""
from openai import OpenAI
import os
import json
from datetime import datetime
import subprocess
import requests
from typing import Optional, Callable, Generator, Dict, List
from threading import Thread
from .database import Database
from .mcp_client import MCPManager
from .plugin_manager import PluginManager


class NexFramework:
    """AI 对话框架，支持多模型切换、工具调用、流式输出、多会话"""
    
    def __init__(
        self,
        work_dir: str,
        default_model: str = None,
    ):
        """
        初始化 NexFramework
        
        Args:
            work_dir: 工作目录，包含配置文件
            default_model: 默认使用的模型 key
        """
        self.work_dir = os.path.abspath(work_dir)
        
        # 文件路径
        self.db_file = os.path.join(self.work_dir, 'nex_data.db')
        self.tools_dir = os.path.join(self.work_dir, 'tools')
        self.plugins_dir = os.path.join(self.work_dir, 'plugins')
        
        # 默认系统提示词
        self._default_prompt = ""
        
        # 初始化数据库
        self.db = Database(self.db_file)
        
        # 当前会话ID
        self._current_session_id: Optional[int] = None
        
        # 初始化插件管理器
        self.plugin_manager = PluginManager(self.plugins_dir, self)
        # 在后台线程中加载插件，避免阻塞主线程
        self._init_plugins_async()
        
        # 初始化模型
        self.current_model_key = None
        self._init_model(default_model)
        self._init_tools()
        self._custom_tools: Dict[str, Callable] = {}
        self._load_custom_tools()
        
        # 初始化 MCP 管理器（后台异步，不阻塞启动）
        self.mcp_manager = MCPManager()
        self._init_mcp_servers_async()
    
    def _init_model(self, default_model: str = None):
        """初始化模型配置"""
        # 恢复上次使用的模型
        last_model = self.db.get_setting('last_model')
        models = self.db.get_models_list()
        
        if not models:
            # 没有配置任何模型
            self.current_model_key = None
            self.client = None
            self.model = None
            return
        
        # 确定使用哪个模型
        model_keys = [m['id'] for m in models]
        if default_model and default_model in model_keys:
            self.current_model_key = default_model
        elif last_model and last_model in model_keys:
            self.current_model_key = last_model
        else:
            self.current_model_key = model_keys[0]
        
        self._init_client()
    
    def _init_client(self):
        """初始化模型客户端"""
        if not self.current_model_key:
            self.client = None
            self.model = None
            return
        
        config = self.db.get_model(self.current_model_key)
        if not config:
            self.client = None
            self.model = None
            return
        
        self.client = OpenAI(api_key=config['api_key'], base_url=config['base_url'])
        self.model = config['model_id']
        self._current_model_config = config

    def _init_tools(self):
        """初始化内置工具"""
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_shell",
                    "description": "执行shell命令并返回结果",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string", "description": "要执行的shell命令"}},
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "http_request",
                    "description": "发送HTTP请求获取网页内容或API数据",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "请求的URL"},
                            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                            "headers": {"type": "object", "description": "请求头"},
                            "body": {"type": "string", "description": "请求体"}
                        },
                        "required": ["url"]
                    }
                }
            }
        ]
    
    def _load_custom_tools(self):
        """从 tools/ 目录加载自定义工具
        
        支持两种方式：
        1. JSON + Python: tool.json 定义 + tool.py 执行脚本
        2. 纯 Python: tool.py 中包含 TOOL_DEF 定义和 execute(args) 函数
        """
        if not os.path.exists(self.tools_dir):
            return
        
        loaded_tools = set()
        
        # 方式1: 加载 JSON 定义的工具
        for filename in os.listdir(self.tools_dir):
            if filename.endswith('.json'):
                tool_name = filename[:-5]  # 去掉 .json
                json_path = os.path.join(self.tools_dir, filename)
                py_path = os.path.join(self.tools_dir, f"{tool_name}.py")
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        tool_def = json.load(f)
                    
                    self.tools.append({"type": "function", "function": tool_def})
                    actual_name = tool_def.get("name", tool_name)
                    
                    # 如果有对应的 .py 文件，加载执行函数
                    if os.path.exists(py_path):
                        handler = self._load_py_handler(py_path, actual_name)
                        if handler:
                            self._custom_tools[actual_name] = handler
                    
                    loaded_tools.add(tool_name)
                except Exception as e:
                    print(f"[警告] 加载工具 {filename} 失败: {e}")
        
        # 方式2: 加载纯 Python 定义的工具
        for filename in os.listdir(self.tools_dir):
            if filename.endswith('.py'):
                tool_name = filename[:-3]
                if tool_name in loaded_tools:
                    continue  # 已经作为 JSON 工具的执行脚本加载过了
                
                py_path = os.path.join(self.tools_dir, filename)
                try:
                    tool_def, handler = self._load_py_tool(py_path)
                    if tool_def and handler:
                        self.tools.append({"type": "function", "function": tool_def})
                        self._custom_tools[tool_def["name"]] = handler
                except Exception as e:
                    print(f"[警告] 加载工具 {filename} 失败: {e}")
    
    def _load_py_handler(self, py_path: str, tool_name: str) -> Optional[Callable]:
        """从 Python 文件加载执行函数"""
        import importlib.util
        try:
            spec = importlib.util.spec_from_file_location(tool_name, py_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找 execute 函数
            if hasattr(module, 'execute'):
                return module.execute
            # 或者查找与工具同名的函数
            if hasattr(module, tool_name):
                return getattr(module, tool_name)
        except Exception as e:
            print(f"[警告] 加载 {py_path} 失败: {e}")
        return None
    
    def _load_py_tool(self, py_path: str) -> tuple:
        """从纯 Python 文件加载工具定义和执行函数"""
        import importlib.util
        tool_name = os.path.basename(py_path)[:-3]
        try:
            spec = importlib.util.spec_from_file_location(tool_name, py_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 需要有 TOOL_DEF 和 execute
            if hasattr(module, 'TOOL_DEF') and hasattr(module, 'execute'):
                return module.TOOL_DEF, module.execute
        except Exception as e:
            print(f"[警告] 加载 {py_path} 失败: {e}")
        return None, None

    def reload_custom_tools(self) -> dict:
        """热加载自定义工具，返回加载结果"""
        # 清除旧的自定义工具
        builtin_names = ["execute_shell", "http_request"]
        self.tools = [t for t in self.tools if t.get("function", {}).get("name") in builtin_names]
        self._custom_tools.clear()
        
        # 重新加载
        loaded = []
        errors = []
        
        if not os.path.exists(self.tools_dir):
            return {"loaded": loaded, "errors": errors}
        
        loaded_tools = set()
        
        # 方式1: 加载 JSON 定义的工具
        for filename in os.listdir(self.tools_dir):
            if filename.endswith('.json'):
                tool_name = filename[:-5]
                json_path = os.path.join(self.tools_dir, filename)
                py_path = os.path.join(self.tools_dir, f"{tool_name}.py")
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        tool_def = json.load(f)
                    
                    self.tools.append({"type": "function", "function": tool_def})
                    actual_name = tool_def.get("name", tool_name)
                    
                    if os.path.exists(py_path):
                        handler = self._load_py_handler(py_path, actual_name)
                        if handler:
                            self._custom_tools[actual_name] = handler
                    
                    loaded_tools.add(tool_name)
                    loaded.append(actual_name)
                except Exception as e:
                    errors.append({"file": filename, "error": str(e)})
        
        # 方式2: 加载纯 Python 定义的工具
        for filename in os.listdir(self.tools_dir):
            if filename.endswith('.py'):
                tool_name = filename[:-3]
                if tool_name in loaded_tools:
                    continue
                
                py_path = os.path.join(self.tools_dir, filename)
                try:
                    tool_def, handler = self._load_py_tool(py_path)
                    if tool_def and handler:
                        self.tools.append({"type": "function", "function": tool_def})
                        self._custom_tools[tool_def["name"]] = handler
                        loaded.append(tool_def["name"])
                except Exception as e:
                    errors.append({"file": filename, "error": str(e)})
        
        return {"loaded": loaded, "errors": errors}

    # ========== 工具注册 ==========
    def register_tool(self, name: str, description: str, parameters: Dict, handler: Callable) -> None:
        """注册自定义工具"""
        self.tools.append({
            "type": "function",
            "function": {"name": name, "description": description, "parameters": parameters}
        })
        self._custom_tools[name] = handler
    
    # ========== MCP 服务器管理 ==========
    def _init_mcp_servers_async(self):
        """在后台线程中初始化 MCP 服务器连接，不阻塞主线程"""
        def init_servers():
            servers = self.db.get_mcp_servers()
            for server in servers:
                if server.get('enabled'):
                    try:
                        # 使用同步方法，但在后台线程中执行
                        self.mcp_manager.add_server_sync(
                            server['id'], 
                            server['name'], 
                            server['url'],
                            server.get('server_type', 'sse'),
                            server.get('headers')
                        )
                    except Exception as e:
                        print(f"[MCP] 初始化服务器 {server['name']} 失败: {e}")
        
        # 启动后台线程
        thread = Thread(target=init_servers, daemon=True, name="MCP-Init")
        thread.start()
        print("[MCP] 后台初始化 MCP 服务器...")
    
    def _init_plugins_async(self):
        """在后台线程中初始化插件，但先同步加载以注册路由"""
        # 先同步加载插件以注册路由（不执行 init_plugin）
        self.plugin_manager.load_plugins(skip_init=True)
        print(f"[插件] 已加载 {len(self.plugin_manager.plugins)} 个插件（路由已注册）")
        
        # 在后台线程中执行插件初始化
        def init_plugins():
            try:
                self.plugin_manager.init_all_plugins()
                print(f"[插件] 插件初始化完成")
            except Exception as e:
                print(f"[插件] 插件初始化失败: {e}")
        
        # 启动后台线程
        thread = Thread(target=init_plugins, daemon=True, name="Plugin-Init")
        thread.start()
        print("[插件] 后台初始化插件...")
    
    def set_plugins_loaded_callback(self, callback):
        """设置插件加载完成的回调函数"""
        self._on_plugins_loaded = callback
    
    def get_mcp_servers(self) -> List[Dict]:
        """获取所有 MCP 服务器"""
        servers = self.db.get_mcp_servers()
        status = {s['id']: s for s in self.mcp_manager.get_server_status()}
        for server in servers:
            if server['id'] in status:
                server['connected'] = status[server['id']]['connected']
                server['tool_count'] = status[server['id']]['tool_count']
                server['has_headers'] = status[server['id']].get('has_headers', False)
                server['last_error'] = status[server['id']].get('last_error')
            else:
                server['connected'] = False
                server['tool_count'] = 0
                server['has_headers'] = bool(server.get('headers'))
                server['last_error'] = None
        return servers
    
    def add_mcp_server(self, server_id: str, name: str, url: str, server_type: str = "sse", headers: Dict = None) -> Dict:
        """添加 MCP 服务器（后台连接，快速返回）"""
        if not self.db.create_mcp_server(server_id, name, url, server_type, headers):
            return {"success": False, "error": "服务器ID已存在"}
        
        # 使用异步方式添加，快速返回
        connected = self.mcp_manager.add_server(server_id, name, url, server_type, headers)
        return {"success": True, "connected": connected, "message": "已添加，正在后台连接..." if not connected else None}
    
    def update_mcp_server(self, server_id: str, name: str = None, url: str = None, server_type: str = None, headers: Dict = None, enabled: bool = None) -> bool:
        """更新 MCP 服务器"""
        result = self.db.update_mcp_server(server_id, name, url, server_type, headers, enabled)
        if result:
            server = self.db.get_mcp_server(server_id)
            if server:
                if server['enabled']:
                    # 重新连接（后台异步）
                    self.mcp_manager.remove_server(server_id)
                    self.mcp_manager.add_server(
                        server_id, 
                        server['name'], 
                        server['url'],
                        server.get('server_type', 'sse'),
                        server.get('headers')
                    )
                else:
                    # 断开连接
                    self.mcp_manager.remove_server(server_id)
        return result
    
    def delete_mcp_server(self, server_id: str) -> bool:
        """删除 MCP 服务器"""
        self.mcp_manager.remove_server(server_id)
        return self.db.delete_mcp_server(server_id)
    
    def reconnect_mcp_server(self, server_id: str) -> bool:
        """重新连接 MCP 服务器（同步方式，用于手动重连）"""
        server = self.db.get_mcp_server(server_id)
        if not server or not server['enabled']:
            return False
        self.mcp_manager.remove_server(server_id)
        # 手动重连使用同步方式，让用户能看到结果
        return self.mcp_manager.add_server_sync(
            server_id, 
            server['name'], 
            server['url'],
            server.get('server_type', 'sse'),
            server.get('headers')
        )
    
    def get_mcp_tools(self) -> List[Dict]:
        """获取所有 MCP 工具"""
        return self.mcp_manager.get_all_tools()
    
    def get_all_tools(self) -> List[Dict]:
        """获取所有工具（内置 + 自定义 + MCP + 插件），过滤掉禁用的"""
        disabled_tools = json.loads(self.db.get_setting('disabled_tools', '[]'))
        all_tools = self.tools + self.mcp_manager.get_all_tools() + self.plugin_manager.get_plugin_tools()
        return [t for t in all_tools if t.get("function", {}).get("name") not in disabled_tools]
    
    # ========== 插件管理 ==========
    def reload_plugins(self):
        """重新加载所有插件"""
        self.plugin_manager.load_plugins()
    
    def get_plugins(self) -> List[Dict]:
        """获取所有插件"""
        return self.plugin_manager.get_all_plugins()
    
    # ========== 模型管理 ==========
    def switch_model(self, model_key: str) -> bool:
        model = self.db.get_model(model_key)
        if model:
            self.current_model_key = model_key
            self._init_client()
            self.db.set_setting('last_model', model_key)
            return True
        return False
    
    def get_models(self) -> List[Dict]:
        models = self.db.get_models_list()
        return [{
            "key": m['id'],
            "name": m['display_name'],
            "model": m['model_id'],
            "provider_id": m['provider_id'],
            "provider_name": m['provider_name'],
            "tags": m.get('tags', []),
            "model_type": m.get('model_type', 'chat')
        } for m in models]
    
    def get_current_model(self) -> Optional[Dict]:
        if not self.current_model_key:
            return None
        config = self.db.get_model(self.current_model_key)
        if not config:
            return None
        return {
            "key": self.current_model_key,
            "name": config['display_name'],
            "model": config['model_id'],
            "tags": config.get('tags', []),
            "model_type": config.get('model_type', 'chat')
        }
    
    def _get_actual_model(self) -> str:
        """获取实际使用的模型ID"""
        if not self.current_model_key:
            return None
        config = getattr(self, '_current_model_config', None)
        if not config:
            config = self.db.get_model(self.current_model_key)
        if not config:
            return None
        return config['model_id']
    
    # ========== 服务商管理 ==========
    def get_providers(self) -> List[Dict]:
        return self.db.get_providers()
    
    def get_provider(self, provider_id: str) -> Optional[Dict]:
        return self.db.get_provider(provider_id)
    
    def add_provider(self, provider_id: str, name: str, api_key: str, base_url: str) -> bool:
        return self.db.create_provider(provider_id, name, api_key, base_url)
    
    def update_provider(self, provider_id: str, name: str = None, api_key: str = None, base_url: str = None) -> bool:
        result = self.db.update_provider(provider_id, name, api_key, base_url)
        # 如果当前模型使用此服务商，重新初始化客户端
        if result and self.current_model_key:
            config = self.db.get_model(self.current_model_key)
            if config and config['provider_id'] == provider_id:
                self._init_client()
        return result
    
    def delete_provider(self, provider_id: str) -> bool:
        # 检查是否有模型使用此服务商
        models = self.db.get_models_by_provider(provider_id)
        if models:
            # 如果当前模型属于此服务商，需要切换
            if self.current_model_key in [m['id'] for m in models]:
                self.current_model_key = None
                self.client = None
                self.model = None
        return self.db.delete_provider(provider_id)
    
    def fetch_provider_models(self, provider_id: str) -> Dict:
        """获取供应商的模型列表（通过 /v1/models API）"""
        provider = self.db.get_provider(provider_id)
        if not provider:
            return {"success": False, "error": "服务商不存在"}
        
        try:
            client = OpenAI(api_key=provider['api_key'], base_url=provider['base_url'])
            models_response = client.models.list()
            
            models = []
            for model in models_response.data:
                model_info = {
                    "id": model.id,
                    "owned_by": getattr(model, 'owned_by', None),
                    "created": getattr(model, 'created', None),
                }
                
                # 解析模型能力（不同供应商可能有不同的字段名）
                # 检测是否是嵌入模型
                model_id_lower = model.id.lower()
                is_embedding = 'embed' in model_id_lower or 'embedding' in model_id_lower
                model_info['model_type'] = 'embedding' if is_embedding else 'chat'
                
                # 尝试从模型对象获取能力信息
                capabilities = []
                
                # 检查常见的能力字段
                # OpenAI 风格
                if hasattr(model, 'capabilities'):
                    caps = model.capabilities
                    if hasattr(caps, 'vision') and caps.vision:
                        capabilities.append('vision')
                    if hasattr(caps, 'function_calling') and caps.function_calling:
                        capabilities.append('tool')
                    if hasattr(caps, 'reasoning') and caps.reasoning:
                        capabilities.append('reasoning')
                
                # 检查其他常见字段名
                for attr in ['supports_vision', 'vision', 'supports_images']:
                    if getattr(model, attr, None):
                        if 'vision' not in capabilities:
                            capabilities.append('vision')
                        break
                
                for attr in ['supports_tools', 'supports_function_calling', 'function_calling', 'tool_use']:
                    if getattr(model, attr, None):
                        if 'tool' not in capabilities:
                            capabilities.append('tool')
                        break
                
                for attr in ['supports_reasoning', 'reasoning', 'extended_thinking']:
                    if getattr(model, attr, None):
                        if 'reasoning' not in capabilities:
                            capabilities.append('reasoning')
                        break
                
                # 基于模型名称推断能力（作为后备）
                if not capabilities and not is_embedding:
                    # 推理模型通常包含 o1, o3, reasoner, thinking 等关键词
                    if any(kw in model_id_lower for kw in ['o1', 'o3', 'o4', 'reasoner', 'thinking', 'qwq']):
                        capabilities.append('reasoning')
                    # 视觉模型通常包含 vision, vl, 4o 等关键词
                    if any(kw in model_id_lower for kw in ['vision', '-vl', '4o', '4v', 'gpt-4-turbo']):
                        capabilities.append('vision')
                    # 大多数现代对话模型支持工具调用
                    if any(kw in model_id_lower for kw in ['gpt-4', 'gpt-3.5', 'claude', 'gemini', 'qwen', 'glm', 'deepseek-chat', 'mistral', 'grok']):
                        capabilities.append('tool')
                
                model_info['capabilities'] = capabilities
                models.append(model_info)
            
            # 按 id 排序
            models.sort(key=lambda x: x['id'])
            
            return {"success": True, "models": models}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== 模型配置管理 ==========
    def add_model(self, model_key: str, provider_id: str, model_id: str, display_name: str, tags: list = None, model_type: str = 'chat') -> bool:
        result = self.db.create_model(model_key, provider_id, model_id, display_name, tags, model_type)
        # 如果是第一个对话模型，自动设为当前模型
        if result and not self.current_model_key and model_type == 'chat':
            self.current_model_key = model_key
            self._init_client()
        return result
    
    def update_model_config(self, model_key: str, new_key: str = None, model_id: str = None, display_name: str = None, tags: list = None, model_type: str = None) -> str:
        """更新模型配置，返回新的 key（如果有变更）或 None（失败）"""
        result = self.db.update_model(model_key, new_key, model_id, display_name, tags, model_type)
        if not result:
            return None
        
        # 确定最终的 key
        final_key = new_key if new_key else model_key
        
        # 如果是当前模型，更新 current_model_key 并重新初始化
        if model_key == self.current_model_key:
            self.current_model_key = final_key
            self._init_client()
        
        return final_key
    
    def delete_model_config(self, model_key: str) -> bool:
        if model_key == self.current_model_key:
            # 切换到其他模型
            models = self.db.get_models_list()
            other_models = [m for m in models if m['id'] != model_key]
            if other_models:
                self.current_model_key = other_models[0]['id']
                self._init_client()
            else:
                self.current_model_key = None
                self.client = None
                self.model = None
        return self.db.delete_model(model_key)
    
    def get_model_detail(self, model_key: str) -> Optional[Dict]:
        return self.db.get_model(model_key)
    
    # ========== 会话管理 ==========
    def create_session(self, name: str, user: str) -> int:
        """创建新会话"""
        session_id = self.db.create_session(name, user)
        self._current_session_id = session_id
        return session_id
    
    def get_sessions(self, user: str = None, limit: int = None) -> List[Dict]:
        """获取会话列表"""
        sessions = self.db.get_sessions(user, limit)
        for s in sessions:
            s['message_count'] = self.db.get_message_count(s['id'])
        return sessions
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """获取单个会话"""
        session = self.db.get_session(session_id)
        if session:
            session['message_count'] = self.db.get_message_count(session_id)
        return session
    
    def switch_session(self, session_id: int) -> bool:
        """切换当前会话"""
        session = self.db.get_session(session_id)
        if session:
            self._current_session_id = session_id
            return True
        return False
    
    def get_current_session(self) -> Optional[Dict]:
        """获取当前会话"""
        if self._current_session_id:
            return self.get_session(self._current_session_id)
        return None
    
    def update_session(self, session_id: int, name: str) -> bool:
        """更新会话名称"""
        return self.db.update_session(session_id, name)
    
    def delete_session(self, session_id: int) -> bool:
        """删除会话"""
        if self._current_session_id == session_id:
            self._current_session_id = None
        return self.db.delete_session(session_id)
    
    def get_session_messages(self, session_id: int, limit: int = None) -> List[Dict]:
        """获取会话消息"""
        return self.db.get_messages(session_id, limit)
    
    # ========== 工具执行 ==========
    def execute_shell(self, command: str) -> str:
        try:
            import sys
            import locale
            # Windows 下使用系统默认编码（通常是 GBK），其他系统使用 UTF-8
            if sys.platform == 'win32':
                encoding = locale.getpreferredencoding(False) or 'gbk'
            else:
                encoding = 'utf-8'
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, encoding=encoding, errors='replace')
            return (result.stdout or result.stderr or "(无输出)")[:2000]
        except subprocess.TimeoutExpired:
            return "命令执行超时(30秒)"
        except Exception as e:
            return f"执行失败: {e}"
    
    def _extract_text_from_html(self, html: str) -> str:
        """从 HTML 中提取正文内容"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # 移除无关标签
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                           'iframe', 'noscript', 'svg', 'form', 'button']):
                tag.decompose()
            
            # 尝试找主要内容区域
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '.post', '.article', '#content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                # 获取 body 内容
                body = soup.body
                text = body.get_text(separator='\n', strip=True) if body else soup.get_text(separator='\n', strip=True)
            
            # 清理多余空行
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
        except ImportError:
            # 没有 bs4，用简单正则处理
            import re
            # 移除 script 和 style
            text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
            text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
            # 移除所有标签
            text = re.sub(r'<[^>]+>', ' ', text)
            # 清理空白
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            return html
    
    def http_request(self, url: str, method: str = "GET", headers: Dict = None, body: str = None) -> str:
        try:
            if headers is None:
                headers = {}
            # 添加常见请求头避免被拒绝
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
            resp = requests.request(method.upper(), url, headers=headers, data=body, timeout=15)
            content_type = resp.headers.get('Content-Type', '')
            
            # 处理编码
            # 优先从 Content-Type 获取编码
            encoding = resp.encoding
            if encoding is None or encoding.lower() == 'iso-8859-1':
                # requests 默认用 ISO-8859-1，尝试从内容检测
                if 'charset=' in content_type.lower():
                    import re
                    match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
                    if match:
                        encoding = match.group(1)
                else:
                    # 尝试从 HTML meta 标签检测
                    content_start = resp.content[:1024].decode('ascii', errors='ignore').lower()
                    if 'charset=utf-8' in content_start or 'charset="utf-8"' in content_start:
                        encoding = 'utf-8'
                    elif 'charset=gbk' in content_start or 'charset=gb2312' in content_start:
                        encoding = 'gbk'
                    else:
                        # 默认尝试 utf-8
                        encoding = 'utf-8'
            
            # 解码内容
            try:
                text = resp.content.decode(encoding, errors='replace')
            except (LookupError, UnicodeDecodeError):
                text = resp.content.decode('utf-8', errors='replace')
            
            # 如果是 HTML，提取正文
            if 'text/html' in content_type:
                text = self._extract_text_from_html(text)
                return f"状态码: {resp.status_code}\n正文内容:\n{text[:5000]}"
            else:
                return f"状态码: {resp.status_code}\n内容:\n{text[:5000]}"
        except requests.Timeout:
            return "请求超时(15秒)"
        except requests.RequestException as e:
            return f"请求失败: {e}"
    
    def handle_tool_call(self, tool_call) -> str:
        if isinstance(tool_call, dict):
            name, args = tool_call["function"]["name"], json.loads(tool_call["function"]["arguments"])
        else:
            name, args = tool_call.function.name, json.loads(tool_call.function.arguments)
        
        if name == "execute_shell":
            return self.execute_shell(args["command"])
        elif name == "http_request":
            return self.http_request(args["url"], args.get("method", "GET"), args.get("headers"), args.get("body"))
        elif self.mcp_manager.is_mcp_tool(name):
            return self.mcp_manager.call_tool(name, args)
        elif name in self._custom_tools:
            try:
                return str(self._custom_tools[name](args))
            except Exception as e:
                return f"工具执行失败: {e}"
        elif name in self.plugin_manager.plugin_tools:
            # 插件工具
            try:
                return str(self.plugin_manager.execute_plugin_tool(name, args))
            except Exception as e:
                return f"插件工具执行失败: {e}"
        return "未知工具"

    # ========== 历史管理 ==========
    def get_history(self, limit: int = None) -> List[Dict]:
        """获取历史记录（兼容旧API）"""
        return self.db.get_history(limit)
    
    def delete_history(self, history_id: int = None) -> bool:
        """删除历史记录"""
        if history_id is None:
            # 清空所有会话
            self.db.delete_all_sessions()
            self._current_session_id = None
            return True
        return self.db.delete_message(history_id)
    
    def delete_message(self, message_id: int) -> bool:
        """删除单条消息"""
        return self.db.delete_message(message_id)
    
    def get_message(self, message_id: int) -> Optional[Dict]:
        """获取单条消息"""
        return self.db.get_message(message_id)
    
    def update_message(self, message_id: int, content: str) -> bool:
        """更新消息内容"""
        return self.db.update_message(message_id, content)
    
    def delete_messages_after(self, session_id: int, message_id: int) -> int:
        """删除指定消息之后的所有消息"""
        return self.db.delete_messages_after(session_id, message_id)
    
    def get_last_user_message(self, session_id: int) -> Optional[Dict]:
        """获取会话中最后一条用户消息"""
        return self.db.get_last_user_message(session_id)
    
    def clear_session_messages(self, session_id: int) -> int:
        """清空会话消息"""
        return self.db.delete_session_messages(session_id)
    
    def _get_default_prompt(self) -> str:
        """获取默认系统提示词"""
        return getattr(self, '_runtime_prompt', None) or self._default_prompt
    
    def set_prompt(self, prompt: str) -> None:
        """设置运行时提示词（用于 API 调用）"""
        self._runtime_prompt = prompt

    # ========== 对话功能 ==========
    def _ensure_session(self, user: str) -> int:
        """确保有当前会话"""
        if not self._current_session_id:
            self._current_session_id = self.create_session("新会话", user)
        return self._current_session_id
    
    def _build_messages(self, session_id: int, user: str = None, current_message: str = None, use_system_prompt: bool = False) -> tuple:
        """构建消息列表，返回 (messages, persona_params)"""
        # 获取会话的角色卡
        persona = self.db.get_session_persona(session_id)
        persona_params = {}
        
        if persona:
            system_prompt = persona.get('system_prompt') or self._get_default_prompt()
            # 提取角色卡参数
            if persona.get('max_tokens'):
                persona_params['max_tokens'] = persona['max_tokens']
            if persona.get('temperature') is not None:
                persona_params['temperature'] = persona['temperature']
            if persona.get('top_p') is not None:
                persona_params['top_p'] = persona['top_p']
        else:
            system_prompt = self._get_default_prompt()
        
        # 如果启用了系统提示词，注入到系统提示中
        if use_system_prompt:
            from .prompts import get_system_prompt
            builtin_prompt = get_system_prompt()
            system_prompt = f"{builtin_prompt}\n\n{system_prompt}"
        
        # 检查是否启用记忆功能
        memory_enabled = self.db.get_setting('memory_enabled', 'false') == 'true'
        memory_context = ""
        
        if memory_enabled and user and current_message:
            # 搜索相关记忆并注入
            memory_context = self.get_memory_context(user, current_message, max_memories=3)
        
        # 构建系统提示词（包含记忆上下文）
        full_system_prompt = system_prompt
        if memory_context:
            full_system_prompt = f"{system_prompt}\n\n{memory_context}"
        
        messages = [{"role": "system", "content": full_system_prompt}]
        history = self.db.get_messages(session_id, limit=None)
        for msg in history:
            if msg['role'] == 'user':
                messages.append({"role": "user", "content": f"用户名：{msg['user']}\n消息：{msg['content']}"})
            elif msg['role'] == 'assistant':
                messages.append({"role": "assistant", "content": msg['content']})
        return messages, persona_params
    
    def chat(self, user: str, message: str, session_id: int = None, save_history: bool = True, use_system_prompt: bool = False, model_key: str = None, reasoning_effort: str = None, thinking_mode: str = None) -> str:
        # 如果指定了 model_key，临时使用该模型
        if model_key:
            config = self.db.get_model(model_key)
            if not config:
                return f"错误：模型 {model_key} 不存在"
            client = OpenAI(api_key=config['api_key'], base_url=config['base_url'])
            actual_model = config['model_id']
        else:
            if not self.client:
                return "错误：未配置模型，请先添加服务商和模型"
            client = self.client
            actual_model = self._get_actual_model()
        
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        # 确定会话
        if session_id:
            self._current_session_id = session_id
        sid = self._ensure_session(user)
        
        prompt = f"【系统信息】\n当前时间: {now}\n【以下为输入内容】\n用户名：{user}\n消息：{message}"
        
        messages, persona_params = self._build_messages(sid, user, message, use_system_prompt=use_system_prompt)
        messages.append({"role": "user", "content": prompt})
        
        # 保存用户消息
        if save_history:
            self.db.add_message(sid, 'user', message, user)
        
        all_tool_calls = []  # 收集所有工具调用
        
        # 检查工具开关
        tools_enabled = self.db.get_setting('tools_enabled', 'true') == 'true'
        
        # 获取所有工具（内置 + 自定义 + MCP）
        all_tools = self.get_all_tools() if tools_enabled else []
        
        # 使用角色卡参数或默认值
        max_tokens = persona_params.get('max_tokens', 1000)
        temperature = persona_params.get('temperature', 0.7)
        top_p = persona_params.get('top_p')
        
        api_params = {
            "model": actual_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if all_tools:
            api_params["tools"] = all_tools
            api_params["tool_choice"] = "auto"
        if top_p is not None:
            api_params["top_p"] = top_p
        # 添加思考程度参数（仅在指定时传递）
        if reasoning_effort:
            api_params["reasoning_effort"] = reasoning_effort
        # 添加思考模式参数（使用 extra_body 传递非标准参数）
        if thinking_mode:
            api_params["extra_body"] = {"thinking": {"type": thinking_mode}}
        
        response = client.chat.completions.create(**api_params)
        assistant_message = response.choices[0].message
        
        while assistant_message.tool_calls:
            messages.append(assistant_message)
            for tc in assistant_message.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                result = self.handle_tool_call(tc)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                all_tool_calls.append({"name": name, "args": args, "result": result})
            response = client.chat.completions.create(**api_params)
            assistant_message = response.choices[0].message
        
        reply = assistant_message.content
        if save_history:
            extra = {"tool_calls": all_tool_calls} if all_tool_calls else None
            self.db.add_message(sid, 'assistant', reply, extra=extra)
        return reply

    def chat_stream(self, user: str, message: str, session_id: int = None, on_tool_call: Callable = None, save_history: bool = True, save_user_message: bool = True, on_thinking: Callable = None, use_system_prompt: bool = False, extra_tools: List[Dict] = None, model_key: str = None, reasoning_effort: str = None, thinking_mode: str = None) -> Generator[str, None, None]:
        # 如果指定了 model_key，临时使用该模型
        if model_key:
            config = self.db.get_model(model_key)
            if not config:
                yield f"错误：模型 {model_key} 不存在"
                return
            client = OpenAI(api_key=config['api_key'], base_url=config['base_url'])
            actual_model = config['model_id']
        else:
            if not self.client:
                yield "错误：未配置模型，请先添加服务商和模型"
                return
            client = self.client
            actual_model = self._get_actual_model()
        
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        # 确定会话
        if session_id:
            self._current_session_id = session_id
        sid = self._ensure_session(user)
        
        prompt = f"【系统信息】\n当前时间: {now}\n【以下为输入内容】\n用户名：{user}\n消息：{message}"
        
        messages, persona_params = self._build_messages(sid, user, message, use_system_prompt=use_system_prompt)
        messages.append({"role": "user", "content": prompt})
        
        # 保存用户消息（重新生成时不保存，因为用户消息已存在）
        if save_history and save_user_message:
            self.db.add_message(sid, 'user', message, user)
        
        # 使用内容流记录，保存工具调用位置
        content_parts = []  # [{"type": "text", "content": "..."}, {"type": "tool", ...}]
        # Token 统计
        total_tokens = {"prompt": 0, "completion": 0, "total": 0}
        
        # 思考过程
        thinking_content = ""
        
        # 检查工具开关
        tools_enabled = self.db.get_setting('tools_enabled', 'true') == 'true'
        
        # 获取所有工具（内置 + 自定义 + MCP + 额外传入的工具）
        all_tools = []
        if tools_enabled:
            all_tools = self.get_all_tools()
            if extra_tools:
                all_tools = all_tools + extra_tools
        
        # 使用角色卡参数或默认值
        max_tokens = persona_params.get('max_tokens', 4000)
        temperature = persona_params.get('temperature', 0.7)
        top_p = persona_params.get('top_p')
        
        while True:
            api_params = {
                "model": actual_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
                "stream_options": {"include_usage": True}
            }
            # 只有启用工具且有工具时才传
            if all_tools:
                api_params["tools"] = all_tools
                api_params["tool_choice"] = "auto"
            if top_p is not None:
                api_params["top_p"] = top_p
            # 添加思考程度参数（仅在指定时传递）
            if reasoning_effort:
                api_params["reasoning_effort"] = reasoning_effort
            # 添加思考模式参数（使用 extra_body 传递非标准参数）
            if thinking_mode:
                api_params["extra_body"] = {"thinking": {"type": thinking_mode}}
            
            stream = client.chat.completions.create(**api_params)
            
            content_buffer = ""
            tool_calls_buffer = {}
            thinking_started = False
            
            for chunk in stream:
                # 收集 token 使用量（在最后一个 chunk 中）
                if hasattr(chunk, 'usage') and chunk.usage:
                    total_tokens["prompt"] += chunk.usage.prompt_tokens or 0
                    total_tokens["completion"] += chunk.usage.completion_tokens or 0
                    total_tokens["total"] += chunk.usage.total_tokens or 0
                
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # 检查是否有 reasoning_content（思考过程）- 适用于 DeepSeek 等模型
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    if not thinking_started:
                        if on_thinking:
                            on_thinking("thinking_start", {})
                        thinking_started = True
                        yield ""  # yield 空字符串让事件有机会被处理
                    thinking_content += delta.reasoning_content
                    if on_thinking:
                        on_thinking("thinking", delta.reasoning_content)
                    yield ""  # yield 空字符串让事件有机会被处理
                    continue
                
                # 如果之前在思考，现在开始输出内容，标记思考结束
                if thinking_started and delta.content:
                    if on_thinking:
                        on_thinking("thinking_end", {})
                    thinking_started = False
                    yield ""  # yield 空字符串让事件有机会被处理
                
                if delta.content:
                    content_buffer += delta.content
                    yield delta.content
                    
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
            
            # 如果思考还没结束，在这里结束
            if thinking_started and on_thinking:
                on_thinking("thinking_end", {})
                yield ""  # yield 空字符串让事件有机会被处理
            
            if tool_calls_buffer:
                # 保存思考过程
                if thinking_content:
                    content_parts.append({"type": "thinking", "content": thinking_content})
                
                # 保存工具调用前的文本
                if content_buffer:
                    content_parts.append({"type": "text", "content": content_buffer})
                
                tool_calls_list = [{"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                                   for tc in [tool_calls_buffer[i] for i in sorted(tool_calls_buffer.keys())]]
                
                # 构建 assistant 消息，包含 reasoning_content（DeepSeek 思考模式工具调用需要）
                assistant_msg = {"role": "assistant", "content": content_buffer or None, "tool_calls": tool_calls_list}
                if thinking_content:
                    assistant_msg["reasoning_content"] = thinking_content
                messages.append(assistant_msg)
                
                for tc in tool_calls_list:
                    name, args = tc["function"]["name"], json.loads(tc["function"]["arguments"])
                    if on_tool_call:
                        on_tool_call("tool_start", {"name": name, "args": args})
                    yield ""  # yield 空字符串让 tool_start 事件有机会被处理
                    result = self.handle_tool_call(tc)
                    if on_tool_call:
                        on_tool_call("tool_end", {"name": name, "result": result})
                    yield ""  # yield 空字符串让 tool_end 事件有机会被处理
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
                    # 记录工具调用到内容流
                    content_parts.append({
                        "type": "tool",
                        "name": name,
                        "args": args,
                        "result": result
                    })
                continue
            else:
                # 保存思考过程
                if thinking_content:
                    content_parts.append({"type": "thinking", "content": thinking_content})
                # 保存最终文本
                if content_buffer:
                    content_parts.append({"type": "text", "content": content_buffer})
                break
        
        # 返回 tokens 信息
        self._last_tokens = total_tokens
        
        if save_history:
            # 构建完整内容和 extra
            full_content = ""
            for part in content_parts:
                if part["type"] == "text":
                    full_content += part["content"]
            
            extra = {"content_parts": content_parts}
            if total_tokens["total"] > 0:
                extra["tokens"] = total_tokens
            self.db.add_message(sid, 'assistant', full_content, extra=extra)
            
            # 自动提取记忆（如果启用）
            memory_enabled = self.db.get_setting('memory_enabled', 'false') == 'true'
            if memory_enabled:
                try:
                    result = self.extract_and_save_memory(user, sid, message, full_content)
                except Exception as e:
                    print(f"[Memory] 提取记忆失败: {e}")

    # ========== 角色卡管理 ==========
    def create_persona(self, name: str, system_prompt: str, avatar: str = None,
                       max_tokens: int = None, temperature: float = None, top_p: float = None) -> int:
        """创建角色卡"""
        return self.db.create_persona(name, system_prompt, avatar, max_tokens, temperature, top_p)

    def get_personas(self) -> List[Dict]:
        """获取所有角色卡"""
        return self.db.get_personas()

    def get_persona(self, persona_id: int) -> Optional[Dict]:
        """获取单个角色卡"""
        return self.db.get_persona(persona_id)

    def update_persona(self, persona_id: int, name: str = None, system_prompt: str = None, avatar: str = None,
                       max_tokens: int = None, temperature: float = None, top_p: float = None) -> bool:
        """更新角色卡"""
        return self.db.update_persona(persona_id, name, system_prompt, avatar, max_tokens, temperature, top_p)

    def delete_persona(self, persona_id: int) -> bool:
        """删除角色卡"""
        return self.db.delete_persona(persona_id)

    def set_session_persona(self, session_id: int, persona_id: int = None) -> bool:
        """设置会话的角色卡"""
        return self.db.set_session_persona(session_id, persona_id)

    def get_session_persona(self, session_id: int) -> Optional[Dict]:
        """获取会话的角色卡"""
        return self.db.get_session_persona(session_id)

    # ========== 用户设置管理 ==========
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """获取设置值"""
        return self.db.get_setting(key, default)

    def set_setting(self, key: str, value: str) -> bool:
        """设置值"""
        return self.db.set_setting(key, value)

    def get_all_settings(self) -> Dict[str, str]:
        """获取所有设置"""
        return self.db.get_all_settings()

    # ========== 嵌入模型和记忆功能 ==========
    def get_embedding_models(self) -> List[Dict]:
        """获取所有嵌入模型"""
        models = self.db.get_models_list()
        return [m for m in models if m.get('model_type') == 'embedding']

    def get_embedding_model(self) -> Optional[Dict]:
        """获取当前选择的嵌入模型"""
        # 先检查是否有指定的嵌入模型
        selected_model_key = self.db.get_setting('embedding_model')
        if selected_model_key:
            model = self.db.get_model(selected_model_key)
            if model and model.get('model_type') == 'embedding':
                return model
        
        # 否则返回第一个可用的嵌入模型
        models = self.get_embedding_models()
        return models[0] if models else None

    def create_embedding(self, text: str) -> Optional[List[float]]:
        """使用嵌入模型生成文本向量"""
        embed_model = self.get_embedding_model()
        if not embed_model:
            return None
        
        try:
            client = OpenAI(
                api_key=embed_model['api_key'],
                base_url=embed_model['base_url']
            )
            response = client.embeddings.create(
                model=embed_model['model_id'],
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[Memory] 生成向量失败: {e}")
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def add_memory(self, user: str, content: str, importance: int = 5,
                   source_session_id: int = None, source_message_id: int = None) -> Optional[int]:
        """添加记忆（自动生成向量）"""
        # 不在向量生成时添加用户前缀，让记忆可以跨用户检索
        # 用户信息存储在数据库的 user 字段中，用于管理和展示
        embedding = self.create_embedding(content)
        return self.db.add_memory(user, content, embedding, importance, 
                                  source_session_id, source_message_id)

    def search_memories(self, user: str, query: str, top_k: int = 5, 
                        threshold: float = 0.5) -> List[Dict]:
        """搜索相关记忆"""
        # 不添加用户前缀，允许检索到提及当前用户的其他用户的记忆
        query_embedding = self.create_embedding(query)
        if not query_embedding:
            # 如果无法生成向量，返回重要度最高的记忆
            all_memories = self.db.get_memories(user, limit=50)
            # 按重要度排序
            all_memories.sort(key=lambda x: x.get('importance', 5), reverse=True)
            return all_memories[:top_k]
        
        # 获取所有用户的记忆（允许跨用户检索）
        memories = self.db.get_all_memories_with_embedding()
        if not memories:
            return []
        
        # 计算相似度并排序
        scored_memories = []
        for m in memories:
            if m.get('embedding'):
                similarity = self._cosine_similarity(query_embedding, m['embedding'])
                if similarity >= threshold:
                    m['similarity'] = similarity
                    scored_memories.append(m)
        
        # 按相似度排序
        scored_memories.sort(key=lambda x: x['similarity'], reverse=True)
        return scored_memories[:top_k]

    def get_memories(self, user: str, limit: int = 50) -> List[Dict]:
        """获取用户的所有记忆"""
        return self.db.get_memories(user, limit)

    def get_memory(self, memory_id: int) -> Optional[Dict]:
        """获取单条记忆"""
        return self.db.get_memory(memory_id)

    def update_memory(self, memory_id: int, content: str = None, 
                      importance: int = None, regenerate_embedding: bool = False) -> bool:
        """更新记忆"""
        embedding = None
        if regenerate_embedding and content:
            embedding = self.create_embedding(content)
        return self.db.update_memory(memory_id, content, embedding, importance)

    def delete_memory(self, memory_id: int) -> bool:
        """删除记忆"""
        return self.db.delete_memory(memory_id)

    def delete_user_memories(self, user: str) -> int:
        """删除用户的所有记忆"""
        return self.db.delete_user_memories(user)

    def get_memory_context(self, user: str, query: str, max_memories: int = 3) -> str:
        """获取记忆上下文（用于注入到对话中）"""
        # 使用较低的阈值，让更多相关记忆能被检索到
        memories = self.search_memories(user, query, top_k=max_memories, threshold=0.25)
        
        # 如果向量搜索没有结果，尝试获取最近的重要记忆
        if not memories:
            recent_memories = self.db.get_memories(user, limit=max_memories)
            # 只返回重要度较高的记忆
            memories = [m for m in recent_memories if m.get('importance', 5) >= 6]
        
        if not memories:
            return ""
        
        memory_texts = []
        for m in memories:
            memory_texts.append(f"- {m['content']}")
        
        return "【用户相关记忆】\n" + "\n".join(memory_texts)

    def extract_and_save_memory(self, user: str, session_id: int, 
                                 user_message: str, ai_response: str) -> Optional[int]:
        """从对话中提取并保存重要记忆"""
        # 检查是否包含可能值得记忆的关键词
        memory_keywords = [
            '我是', '我叫', '我喜欢', '我讨厌', '我的', '记住', '别忘了', 
            '我住在', '我在', '我工作', '我学习', '我的生日', '我的爱好',
            '我今年', '我来自', '我会', '我不会', '我想', '我需要',
            '我的名字', '我的职业', '我的专业', '我擅长', '我不擅长',
            '请记住', '不要忘记', '我告诉你', '我跟你说'
        ]
        
        should_save = any(kw in user_message for kw in memory_keywords)
        
        if should_save:
            # 提取记忆内容
            memory_content = f"用户说: {user_message}"
            return self.add_memory(user, memory_content, importance=7, 
                                   source_session_id=session_id)
        
        return None

    # ========== 语音识别(STT)服务 ==========
    def get_stt_config(self) -> Optional[Dict]:
        """获取 STT 配置"""
        base_url = self.db.get_setting('stt_base_url')
        api_key = self.db.get_setting('stt_api_key')
        model = self.db.get_setting('stt_model')
        
        if not base_url or not model:
            return None
        
        return {
            'base_url': base_url,
            'api_key': api_key,
            'model': model
        }
    
    def set_stt_config(self, base_url: str, model: str, api_key: str = None) -> bool:
        """设置 STT 配置"""
        self.db.set_setting('stt_base_url', base_url)
        self.db.set_setting('stt_model', model)
        if api_key:
            self.db.set_setting('stt_api_key', api_key)
        return True
    
    def _convert_audio_to_wav(self, audio_data: bytes, input_format: str) -> Optional[bytes]:
        """
        将音频转换为 WAV 格式（需要 ffmpeg）
        
        Args:
            audio_data: 原始音频数据
            input_format: 输入格式 (webm, ogg, m4a 等)
            
        Returns:
            WAV 格式的音频数据，失败返回 None
        """
        import tempfile
        import shutil
        
        # 检查 ffmpeg 是否可用
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            print("[STT] ffmpeg 未安装，无法转换音频格式")
            return None
        
        print(f"[STT] 使用 ffmpeg 转换 {input_format} -> wav")
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=f'.{input_format}', delete=False) as input_file:
                input_file.write(audio_data)
                input_path = input_file.name
            
            output_path = input_path.rsplit('.', 1)[0] + '.wav'
            
            # 使用 ffmpeg 转换，添加更多参数确保兼容性
            result = subprocess.run(
                [ffmpeg_path, '-y', '-i', input_path, 
                 '-acodec', 'pcm_s16le',  # 16位 PCM
                 '-ar', '16000',           # 16kHz 采样率
                 '-ac', '1',               # 单声道
                 '-f', 'wav', 
                 output_path],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    wav_data = f.read()
                # 清理临时文件
                os.unlink(input_path)
                os.unlink(output_path)
                print(f"[STT] 转换成功，wav 大小: {len(wav_data)} bytes")
                return wav_data
            else:
                print(f"[STT] ffmpeg 转换失败: {result.stderr.decode() if result.stderr else 'unknown error'}")
                os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
        except Exception as e:
            print(f"[STT] 音频转换异常: {e}")
            return None
    
    def _convert_audio_to_mp3(self, audio_data: bytes, input_format: str) -> Optional[bytes]:
        """将音频转换为 MP3 格式"""
        import tempfile
        import shutil
        
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            return None
        
        try:
            with tempfile.NamedTemporaryFile(suffix=f'.{input_format}', delete=False) as input_file:
                input_file.write(audio_data)
                input_path = input_file.name
            
            output_path = input_path.rsplit('.', 1)[0] + '.mp3'
            
            result = subprocess.run(
                [ffmpeg_path, '-y', '-i', input_path, 
                 '-acodec', 'libmp3lame',
                 '-ar', '16000',
                 '-ac', '1',
                 '-b:a', '64k',
                 output_path],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    mp3_data = f.read()
                os.unlink(input_path)
                os.unlink(output_path)
                return mp3_data
            else:
                os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
        except Exception as e:
            print(f"[STT] MP3 转换异常: {e}")
            return None
    
    def transcribe_audio(self, audio_data: bytes, filename: str = "audio.webm", 
                         content_type: str = "audio/webm") -> Dict:
        """
        语音转文字
        
        Args:
            audio_data: 音频文件的二进制数据
            filename: 文件名
            content_type: MIME 类型
            
        Returns:
            {"success": True, "text": "识别结果"} 或 {"success": False, "error": "错误信息"}
        """
        config = self.get_stt_config()
        if not config:
            return {"success": False, "error": "请先配置 STT 设置"}
        
        # 获取文件扩展名
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'webm'
        original_ext = ext
        
        print(f"[STT] 收到音频文件: {filename}, 格式: {ext}, 大小: {len(audio_data)} bytes")
        
        # 如果是浏览器录音格式，尝试转换为 mp3
        if ext in ['webm', 'ogg', 'opus', 'm4a', 'mp4', 'aac']:
            # 优先尝试转换为 mp3（兼容性更好）
            mp3_data = self._convert_audio_to_mp3(audio_data, ext)
            if mp3_data:
                audio_data = mp3_data
                filename = 'audio.mp3'
                content_type = 'audio/mpeg'
                ext = 'mp3'
                print(f"[STT] 已将 {original_ext} 转换为 mp3 格式")
            else:
                # 尝试转换为 wav
                wav_data = self._convert_audio_to_wav(audio_data, ext)
                if wav_data:
                    audio_data = wav_data
                    filename = 'audio.wav'
                    content_type = 'audio/wav'
                    ext = 'wav'
                    print(f"[STT] 已将 {original_ext} 转换为 wav 格式")
                else:
                    print(f"[STT] 无法转换 {original_ext} 格式，请安装 ffmpeg")
                    return {"success": False, "error": f"不支持 {original_ext} 格式，请安装 ffmpeg 进行转换"}
        
        try:
            # 创建 OpenAI 客户端
            client = OpenAI(
                api_key=config['api_key'] or 'dummy-key',
                base_url=config['base_url']
            )
            
            # 使用元组方式传递文件: (filename, content, content_type)
            file_tuple = (filename, audio_data, content_type)
            
            print(f"[STT] 发送到 API: {filename}, content_type: {content_type}")
            
            # 调用转录 API
            transcription = client.audio.transcriptions.create(
                model=config['model'],
                file=file_tuple
            )
            
            return {"success": True, "text": transcription.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========== 语音合成(TTS)服务 ==========
    def get_tts_config(self) -> Optional[Dict]:
        """获取 TTS 配置"""
        base_url = self.db.get_setting('tts_base_url')
        api_key = self.db.get_setting('tts_api_key')
        model = self.db.get_setting('tts_model')
        voice = self.db.get_setting('tts_voice', 'alloy')
        
        if not base_url or not model:
            return None
        
        return {
            'base_url': base_url,
            'api_key': api_key,
            'model': model,
            'voice': voice
        }
    
    def set_tts_config(self, base_url: str, model: str, api_key: str = None, voice: str = None) -> bool:
        """设置 TTS 配置"""
        self.db.set_setting('tts_base_url', base_url)
        self.db.set_setting('tts_model', model)
        if api_key:
            self.db.set_setting('tts_api_key', api_key)
        if voice:
            self.db.set_setting('tts_voice', voice)
        return True
    
    def synthesize_speech(self, text: str) -> Dict:
        """
        文本转语音
        
        Args:
            text: 要合成的文本
            
        Returns:
            {"success": True, "audio": bytes} 或 {"success": False, "error": "错误信息"}
        """
        # 验证配置
        config = self.get_tts_config()
        
        if not config:
            return {"success": False, "error": "请先配置 TTS 设置"}
        
        # 验证必需字段
        if not config.get('api_key'):
            return {"success": False, "error": "TTS API Key 未配置"}
        
        if not config.get('base_url'):
            return {"success": False, "error": "TTS Base URL 未配置"}
        
        if not config.get('model'):
            return {"success": False, "error": "TTS 模型未配置"}
        
        if not config.get('voice'):
            return {"success": False, "error": "TTS 语音未配置"}
        
        # 验证文本
        if not text or not text.strip():
            return {"success": False, "error": "文本不能为空"}
        
        # 限制文本长度（避免过长的请求）
        max_length = 4000  # 字符数限制
        if len(text) > max_length:
            return {"success": False, "error": f"文本过长，最多支持 {max_length} 个字符"}
        
        try:
            # 创建 OpenAI 客户端 (复用 STT 的模式)
            client = OpenAI(
                api_key=config['api_key'],
                base_url=config['base_url']
            )
            
            # 调用 TTS API
            response = client.audio.speech.create(
                model=config['model'],
                voice=config['voice'],
                input=text.strip()
            )
            
            # 将响应内容写入字节流
            import io
            audio_bytes = io.BytesIO()
            for chunk in response.iter_bytes():
                audio_bytes.write(chunk)
            
            audio_data = audio_bytes.getvalue()
            
            # 验证音频数据
            if not audio_data or len(audio_data) == 0:
                return {"success": False, "error": "生成的音频数据为空"}
            
            # 检查是否是 PCM 数据（没有标准音频文件头）
            # MP3: FF FB/FF F3/49 44 33, WAV: 52 49 46 46, OGG: 4F 67 67 53
            if len(audio_data) > 4:
                header = audio_data[:4]
                # 检查是否有标准音频格式的魔数
                is_mp3 = header[:2] in [b'\xff\xfb', b'\xff\xf3'] or header[:3] == b'ID3'
                is_wav = header == b'RIFF'
                is_ogg = header == b'OggS'
                
                if not (is_mp3 or is_wav or is_ogg):
                    # 可能是 PCM 数据，需要包装成 WAV
                    print("Detected PCM data, converting to WAV...")
                    audio_data = self._pcm_to_wav(audio_data)
            
            return {"success": True, "audio": audio_data}
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"TTS Error: {error_detail}")
            
            # 提供更友好的错误信息
            error_msg = str(e)
            if "API key" in error_msg or "authentication" in error_msg.lower():
                return {"success": False, "error": "API Key 无效或已过期"}
            elif "timeout" in error_msg.lower():
                return {"success": False, "error": "请求超时，请稍后重试"}
            elif "connection" in error_msg.lower():
                return {"success": False, "error": "无法连接到 TTS 服务"}
            else:
                return {"success": False, "error": f"语音合成失败: {error_msg}"}
    
    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
        """
        将 PCM 数据转换为 WAV 格式
        
        Args:
            pcm_data: PCM 音频数据
            sample_rate: 采样率（默认 24000 Hz，OpenAI TTS 的默认值）
            channels: 声道数（1=单声道，2=立体声）
            sample_width: 采样宽度（字节数，2=16位）
            
        Returns:
            WAV 格式的音频数据
        """
        import struct
        
        # WAV 文件头
        data_size = len(pcm_data)
        
        # RIFF chunk
        riff_chunk = b'RIFF'
        file_size = 36 + data_size  # 文件大小 - 8
        riff_chunk += struct.pack('<I', file_size)
        riff_chunk += b'WAVE'
        
        # fmt chunk
        fmt_chunk = b'fmt '
        fmt_chunk += struct.pack('<I', 16)  # fmt chunk size
        fmt_chunk += struct.pack('<H', 1)   # audio format (1 = PCM)
        fmt_chunk += struct.pack('<H', channels)  # number of channels
        fmt_chunk += struct.pack('<I', sample_rate)  # sample rate
        byte_rate = sample_rate * channels * sample_width
        fmt_chunk += struct.pack('<I', byte_rate)  # byte rate
        block_align = channels * sample_width
        fmt_chunk += struct.pack('<H', block_align)  # block align
        fmt_chunk += struct.pack('<H', sample_width * 8)  # bits per sample
        
        # data chunk
        data_chunk = b'data'
        data_chunk += struct.pack('<I', data_size)
        data_chunk += pcm_data
        
        return riff_chunk + fmt_chunk + data_chunk
