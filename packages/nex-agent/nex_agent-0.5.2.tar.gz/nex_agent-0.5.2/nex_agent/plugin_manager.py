"""
NexAgent 插件管理器
"""
import os
import sys
import json
import importlib.util
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
from functools import wraps


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugins_dir: str, nex_instance=None):
        self.plugins_dir = plugins_dir
        self.nex = nex_instance
        self.plugins: Dict[str, Dict] = {}
        self.plugin_routes = []  # 存储插件注册的路由
        self.plugin_tools: Dict[str, Dict] = {}  # 存储插件注册的工具 {tool_name: {definition, handler, plugin_id}}
        
    def load_plugins(self, skip_init: bool = False) -> List[Dict]:
        """加载所有插件
        
        Args:
            skip_init: 如果为 True，只加载插件模块和注册路由，不执行 init_plugin
        """
        self.plugins.clear()
        self.plugin_routes.clear()
        self.plugin_tools.clear()
        
        if not os.path.exists(self.plugins_dir):
            return []
        
        for item in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, item)
            if os.path.isdir(plugin_path):
                self._load_plugin(item, plugin_path, skip_init=skip_init)
        
        return list(self.plugins.values())
    
    def init_all_plugins(self):
        """初始化所有已加载的插件（执行 init_plugin 函数）"""
        for plugin_id, plugin_info in self.plugins.items():
            if plugin_info.get('module') and not plugin_info.get('initialized'):
                try:
                    module = plugin_info['module']
                    if hasattr(module, 'init_plugin'):
                        module.init_plugin(plugin_info['api'])
                        plugin_info['initialized'] = True
                        print(f"[插件] {plugin_id} 初始化完成")
                except Exception as e:
                    print(f"[插件] {plugin_id} 初始化失败: {e}")
    
    def _load_plugin(self, plugin_id: str, plugin_path: str, skip_init: bool = False):
        """加载单个插件
        
        Args:
            plugin_id: 插件ID
            plugin_path: 插件路径
            skip_init: 如果为 True，不执行 init_plugin 函数
        """
        main_file = os.path.join(plugin_path, '__main__.py')
        if not os.path.exists(main_file):
            return
        
        # 检查插件是否被禁用
        if self.nex:
            disabled = self.nex.db.get_setting('disabled_plugins', '[]')
            try:
                disabled_list = json.loads(disabled)
                if plugin_id in disabled_list:
                    print(f"插件 {plugin_id} 已被禁用，跳过加载")
                    # 仍然添加到插件列表，但不执行初始化
                    self.plugins[plugin_id] = {
                        'id': plugin_id,
                        'name': plugin_id,
                        'description': '已禁用',
                        'tools': [],
                        'module': None,
                        'path': plugin_path,
                        'api': None,
                        'initialized': False
                    }
                    return
            except:
                pass
        
        try:
            # 创建插件API实例
            plugin_api = PluginAPI(self.nex, plugin_id, self)
            
            # 动态导入插件模块
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_id}", main_file)
            if not spec or not spec.loader:
                return
            
            module = importlib.util.module_from_spec(spec)
            
            # 注入api到模块的全局命名空间
            module.api = plugin_api
            
            sys.modules[f"plugin_{plugin_id}"] = module
            spec.loader.exec_module(module)
            
            # 获取插件信息
            plugin_info = {
                'id': plugin_id,
                'name': getattr(module, 'PLUGIN_NAME', plugin_id),
                'description': getattr(module, 'PLUGIN_DESCRIPTION', ''),
                'tools': [],  # 将在注册工具时更新
                'module': module,
                'path': plugin_path,
                'api': plugin_api,
                'initialized': False
            }
            
            self.plugins[plugin_id] = plugin_info
            
            # 如果不跳过初始化且插件有初始化函数，调用它
            if not skip_init and hasattr(module, 'init_plugin'):
                module.init_plugin(plugin_api)
                plugin_info['initialized'] = True
            
            # 更新工具列表
            plugin_info['tools'] = [
                name for name, info in self.plugin_tools.items() 
                if info['plugin_id'] == plugin_id
            ]
                
        except Exception as e:
            print(f"加载插件 {plugin_id} 失败: {e}")
            import traceback
            traceback.print_exc()
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict]:
        """获取插件信息"""
        return self.plugins.get(plugin_id)
    
    def get_all_plugins(self) -> List[Dict]:
        """获取所有插件信息（不包含module对象）"""
        enabled_plugins = self._get_enabled_plugins()
        return [{
            'id': p['id'],
            'name': p['name'],
            'description': p['description'],
            'tools': p['tools'],
            'enabled': p['id'] in enabled_plugins
        } for p in self.plugins.values()]
    
    def register_route(self, plugin_id: str, method: str, path: str, handler, **kwargs):
        """注册插件路由"""
        # 确保路径有插件前缀
        if not path.startswith(f'/plugin/{plugin_id}'):
            if path.startswith('/'):
                path = f'/plugin/{plugin_id}{path}'
            else:
                path = f'/plugin/{plugin_id}/{path}'
        
        self.plugin_routes.append({
            'plugin_id': plugin_id,
            'method': method.upper(),
            'path': path,
            'handler': handler,
            'kwargs': kwargs
        })
        
        return path
    
    def register_tool(self, plugin_id: str, name: str, description: str, 
                     parameters: Dict, handler: Callable) -> str:
        """注册插件工具
        
        Args:
            plugin_id: 插件ID
            name: 工具名称
            description: 工具描述
            parameters: 参数定义（JSON Schema格式）
            handler: 执行函数
            
        Returns:
            完整的工具名称
        """
        # 工具名称添加插件前缀，避免冲突
        full_name = f"plugin_{plugin_id}_{name}"
        
        # 构建工具定义（OpenAI格式）
        tool_def = {
            "type": "function",
            "function": {
                "name": full_name,
                "description": f"[{plugin_id}] {description}",
                "parameters": parameters
            }
        }
        
        self.plugin_tools[full_name] = {
            'definition': tool_def,
            'handler': handler,
            'plugin_id': plugin_id,
            'original_name': name
        }
        
        return full_name
    
    def get_plugin_tools(self) -> List[Dict]:
        """获取所有插件工具定义（只返回启用的插件的工具）"""
        enabled_plugins = self._get_enabled_plugins()
        return [
            info['definition'] 
            for name, info in self.plugin_tools.items() 
            if info['plugin_id'] in enabled_plugins
        ]
    
    def _get_enabled_plugins(self) -> set:
        """获取启用的插件ID集合"""
        if not self.nex:
            return set(self.plugins.keys())
        
        disabled = self.nex.db.get_setting('disabled_plugins', '[]')
        try:
            disabled_list = json.loads(disabled)
        except:
            disabled_list = []
        
        return set(p for p in self.plugins.keys() if p not in disabled_list)
    
    def is_plugin_enabled(self, plugin_id: str) -> bool:
        """检查插件是否启用"""
        return plugin_id in self._get_enabled_plugins()
    
    def set_plugin_enabled(self, plugin_id: str, enabled: bool):
        """设置插件启用状态"""
        if not self.nex:
            return
        
        disabled = self.nex.db.get_setting('disabled_plugins', '[]')
        try:
            disabled_list = json.loads(disabled)
        except:
            disabled_list = []
        
        if enabled:
            # 启用：从禁用列表中移除
            disabled_list = [p for p in disabled_list if p != plugin_id]
        else:
            # 禁用：添加到禁用列表
            if plugin_id not in disabled_list:
                disabled_list.append(plugin_id)
        
        self.nex.db.set_setting('disabled_plugins', json.dumps(disabled_list))
    
    def execute_plugin_tool(self, tool_name: str, arguments: Dict) -> Any:
        """执行插件工具"""
        if tool_name not in self.plugin_tools:
            raise ValueError(f"工具 {tool_name} 不存在")
        
        tool_info = self.plugin_tools[tool_name]
        
        # 检查插件是否启用
        plugin_id = tool_info['plugin_id']
        if not self.is_plugin_enabled(plugin_id):
            raise ValueError(f"插件 {plugin_id} 已被禁用")
        
        handler = tool_info['handler']
        
        # 执行工具
        return handler(arguments)


class PluginAPI:
    """插件API - 提供给插件使用的接口，支持FastAPI风格的装饰器"""
    
    def __init__(self, nex_instance, plugin_id: str, plugin_manager):
        self.nex = nex_instance
        self.plugin_id = plugin_id
        self.plugin_manager = plugin_manager
    
    # ========== FastAPI风格的路由装饰器 ==========
    def get(self, path: str, **kwargs):
        """GET请求装饰器
        
        Example:
            @api.get("/hello")
            async def hello():
                return {"message": "Hello"}
                
            @api.get("/users/{user_id}", response_model=User)
            async def get_user(user_id: int):
                return {"id": user_id}
        """
        def decorator(func):
            self.plugin_manager.register_route(
                self.plugin_id, 'GET', path, func, **kwargs
            )
            return func
        return decorator
    
    def post(self, path: str, **kwargs):
        """POST请求装饰器
        
        Example:
            @api.post("/items", status_code=201)
            async def create_item(item: Item):
                return item
        """
        def decorator(func):
            self.plugin_manager.register_route(
                self.plugin_id, 'POST', path, func, **kwargs
            )
            return func
        return decorator
    
    def put(self, path: str, **kwargs):
        """PUT请求装饰器"""
        def decorator(func):
            self.plugin_manager.register_route(
                self.plugin_id, 'PUT', path, func, **kwargs
            )
            return func
        return decorator
    
    def delete(self, path: str, **kwargs):
        """DELETE请求装饰器"""
        def decorator(func):
            self.plugin_manager.register_route(
                self.plugin_id, 'DELETE', path, func, **kwargs
            )
            return func
        return decorator
    
    def patch(self, path: str, **kwargs):
        """PATCH请求装饰器"""
        def decorator(func):
            self.plugin_manager.register_route(
                self.plugin_id, 'PATCH', path, func, **kwargs
            )
            return func
        return decorator
    
    def route(self, path: str, methods: List[str] = None, **kwargs):
        """通用路由装饰器，支持多个HTTP方法
        
        Example:
            @api.route("/data", methods=["GET", "POST"])
            async def handle_data(request: Request):
                if request.method == "GET":
                    return {"data": []}
                else:
                    body = await request.json()
                    return {"created": body}
        """
        if methods is None:
            methods = ['GET']
        
        def decorator(func):
            for method in methods:
                self.plugin_manager.register_route(
                    self.plugin_id, method.upper(), path, func, **kwargs
                )
            return func
        return decorator
    
    # ========== 数据库操作 ==========
    def get_setting(self, key: str, default: str = '') -> str:
        """获取设置"""
        return self.nex.db.get_setting(f'plugin_{self.plugin_id}_{key}', default)
    
    def set_setting(self, key: str, value: str):
        """保存设置"""
        self.nex.db.set_setting(f'plugin_{self.plugin_id}_{key}', value)
    
    def get_session_messages(self, session_id: int) -> List[Dict]:
        """获取会话消息"""
        return self.nex.db.get_session_messages(session_id)
    
    def add_message(self, session_id: int, role: str, content: str, extra: Dict = None):
        """添加消息"""
        return self.nex.db.add_message(session_id, role, content, extra=extra)
    
    def get_sessions(self, user: str = None) -> List[Dict]:
        """获取会话列表"""
        return self.nex.db.get_sessions(user)
    
    def create_session(self, name: str, user: str) -> int:
        """创建会话"""
        return self.nex.db.create_session(name, user)
    
    # ========== 模型操作 ==========
    def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        return self.nex.current_model_key
    
    def switch_model(self, model_key: str) -> bool:
        """切换模型"""
        return self.nex.switch_model(model_key)
    
    def get_models(self) -> List[Dict]:
        """获取所有模型"""
        return self.nex.get_models()
    
    def chat(self, user: str, message: str, session_id: int = None, **kwargs) -> str:
        """发送对话消息"""
        return self.nex.chat(user, message, session_id, **kwargs)
    
    def chat_stream(self, user: str, message: str, session_id: int = None, **kwargs):
        """流式对话"""
        return self.nex.chat_stream(user, message, session_id, **kwargs)
    
    # ========== 工具操作 ==========
    def get_all_tools(self) -> List[Dict]:
        """获取所有工具"""
        return self.nex.get_all_tools()
    
    def execute_tool(self, tool_name: str, arguments: Dict) -> Any:
        """执行工具"""
        return self.nex.execute_tool(tool_name, arguments)
    
    def tool(self, name: str, description: str, parameters: Dict = None):
        """工具注册装饰器
        
        Example:
            @api.tool(
                name="get_weather",
                description="获取天气信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称"}
                    },
                    "required": ["city"]
                }
            )
            def get_weather(args):
                city = args["city"]
                return f"{city}的天气是晴天"
        """
        if parameters is None:
            parameters = {"type": "object", "properties": {}}
        
        def decorator(func):
            self.plugin_manager.register_tool(
                self.plugin_id, name, description, parameters, func
            )
            return func
        return decorator
    
    # ========== 文件操作 ==========
    def get_plugin_dir(self) -> str:
        """获取插件目录"""
        plugin = self.plugin_manager.get_plugin(self.plugin_id)
        return plugin['path'] if plugin else ''
    
    def read_file(self, filename: str) -> str:
        """读取插件目录下的文件"""
        file_path = os.path.join(self.get_plugin_dir(), filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, filename: str, content: str):
        """写入插件目录下的文件"""
        file_path = os.path.join(self.get_plugin_dir(), filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        file_path = os.path.join(self.get_plugin_dir(), filename)
        return os.path.exists(file_path)
    
    def list_files(self, pattern: str = '*') -> List[str]:
        """列出插件目录下的文件"""
        from glob import glob
        plugin_dir = self.get_plugin_dir()
        files = glob(os.path.join(plugin_dir, pattern))
        return [os.path.basename(f) for f in files]

