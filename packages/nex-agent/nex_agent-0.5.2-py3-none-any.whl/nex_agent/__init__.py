"""
NexAgent - AI 对话框架
支持多模型切换、工具调用、流式输出、多会话管理、MCP服务器、角色卡系统

主要功能：
- 多模型管理：支持多个AI服务商和模型配置
- 会话管理：多会话支持，每个会话独立的上下文
- 角色卡系统：为会话设置不同的AI角色和参数
- 工具调用：内置工具、自定义工具、MCP工具、插件工具
- 流式输出：支持流式对话和工具调用
- 向量记忆：基于向量相似度的长期记忆
- 语音功能：STT语音识别和TTS语音合成

使用示例：
    from nex_agent import NexFramework
    
    # 初始化框架（指定工作目录）
    nex = NexFramework(work_dir=".")
    
    # 对话
    response = nex.chat(user="user1", message="你好")
    
    # 流式对话
    for chunk in nex.chat_stream(user="user1", message="讲个故事"):
        print(chunk, end='', flush=True)
    
    # 会话管理
    session_id = nex.create_session(name="我的会话", user="user1")
    nex.switch_session(session_id)
    
    # 角色卡管理
    persona_id = nex.create_persona(
        name="Python专家",
        system_prompt="你是一个专业的Python开发专家..."
    )
    nex.set_session_persona(session_id, persona_id)

工作目录说明：
    work_dir/
    ├── nex_data.db          # 数据库文件（自动创建）
    ├── tools/               # 自定义工具目录（可选）
    │   ├── my_tool.json     # 工具定义文件
    │   └── my_tool.py       # 工具处理函数
    └── plugins/             # 插件目录（可选）
        └── my_plugin/       # 插件文件夹
            ├── __init__.py
            └── plugin.json
"""

from .framework import NexFramework
from .database import Database
from .mcp_client import MCPClient, MCPManager
from .plugin_manager import PluginManager
from ._version import __version__


def get_webserver_app():
    """
    获取 FastAPI webserver 应用实例
    
    用于启动 Web 服务器：
        from nex_agent import get_webserver_app
        import uvicorn
        
        app = get_webserver_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    
    Returns:
        FastAPI: Web 服务器应用实例
    """
    from .webserver import app
    return app


# 导出主要类和函数
__all__ = [
    # 核心框架
    'NexFramework',
    
    # 数据库
    'Database',
    
    # MCP 客户端
    'MCPClient',
    'MCPManager',
    
    # 插件管理
    'PluginManager',
    
    # Web 服务器
    'get_webserver_app',
    
    # 版本信息
    '__version__',
]

__author__ = "3w4e"
__license__ = "MIT"
__description__ = "AI对话框架，支持多模型、工具调用、流式输出、会话管理"
