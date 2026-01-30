"""
NexAgent CLI - 命令行工具
"""
import click
import os
import json
from ._version import __version__


@click.group()
@click.version_option(version=__version__, prog_name="nex")
def cli():
    """NexAgent 命令行工具"""
    pass


@cli.command()
@click.option('--port', '-p', default=6321, help='服务端口')
@click.option('--host', '-h', default='0.0.0.0', help='监听地址 (IPv6用::)')
@click.option('--dir', '-d', default='.', help='工作目录')
@click.option('--dev', is_flag=True, help='开发模式（文件变更自动重启）')
def serve(port, host, dir, dev):
    """启动 WebServer (API + 前端)"""
    dir = os.path.abspath(dir)
    
    # 检查数据库文件是否存在
    db_file = os.path.join(dir, 'nex_data.db')
    if not os.path.exists(db_file):
        click.echo("错误: 数据库文件不存在")
        click.echo(f"当前目录: {dir}")
        click.echo("\n提示: 请先运行以下命令初始化:")
        click.echo(f"   nex init -d {dir}")
        return
    
    # 自动创建 tools 目录
    tools_dir = os.path.join(dir, 'tools')
    os.makedirs(tools_dir, exist_ok=True)
    
    # 自动创建 plugins 目录
    plugins_dir = os.path.join(dir, 'plugins')
    os.makedirs(plugins_dir, exist_ok=True)
    
    os.chdir(dir)
    import uvicorn
    import socket
    
    mode_text = "开发模式" if dev else "生产模式"
    click.echo(f"启动 NexAgent WebServer ({mode_text})")
    click.echo(f"工作目录: {os.getcwd()}")
    
    # 显示监听地址
    if ':' in host:
        click.echo(f"监听: [{host}]:{port}")
    else:
        click.echo(f"监听: {host}:{port}")
    
    # 获取访问地址
    click.echo(f"访问:")
    if host in ('0.0.0.0', '::'):
        click.echo(f"   http://localhost:{port}")
        # 获取所有网卡IP
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                # 过滤：0.0.0.0监听只显示IPv4，::监听只显示IPv6
                if host == '0.0.0.0' and ':' not in ip:
                    click.echo(f"   http://{ip}:{port}")
                elif host == '::' and ':' in ip:
                    click.echo(f"   http://[{ip}]:{port}")
        except:
            pass
    else:
        if ':' in host:
            click.echo(f"   http://[{host}]:{port}")
        else:
            click.echo(f"   http://{host}:{port}")
    
    if dev:
        click.echo("\n开发模式已启用，文件变更将自动重启服务")
        # 开发模式：监控 nex_agent 包目录
        import nex_agent
        package_dir = os.path.dirname(os.path.abspath(nex_agent.__file__))
        click.echo(f"监控目录: {package_dir}")
        
        uvicorn.run(
            "nex_agent.webserver:app",
            host=host, 
            port=port,
            reload=True,
            reload_dirs=[package_dir]  # 监控 nex_agent 包目录
        )
    else:
        # 生产模式：直接使用应用对象
        from .webserver import app
        uvicorn.run(app, host=host, port=port)


@cli.command()
@click.option('--dir', '-d', default='.', help='项目目录')
def init(dir):
    """初始化工作目录"""
    dir = os.path.abspath(dir)
    os.makedirs(dir, exist_ok=True)
    
    # 初始化数据库
    db_file = os.path.join(dir, 'nex_data.db')
    if os.path.exists(db_file):
        click.echo(f"数据库已存在，跳过初始化")
    else:
        from .database import Database
        db = Database(db_file)
        click.echo(f"初始化数据库文件")
    
    click.echo(f"\n初始化完成！目录: {dir}")
    click.echo("\n下一步:")
    click.echo("   1. 运行 nex serve 启动服务")
    click.echo("   2. 打开 http://localhost:6321")
    click.echo("   3. 在设置中添加服务商、模型和角色卡")
    click.echo("\n自定义工具和更多用法请查看:")
    click.echo("   https://gitee.com/candy_xt/NexAgent")


@cli.command()
@click.option('--dir', '-d', default='.', help='工作目录')
def tools(dir):
    """列出所有可用工具"""
    dir = os.path.abspath(dir)
    tools_dir = os.path.join(dir, 'tools')
    
    click.echo("内置工具:")
    click.echo("   • execute_shell - 执行shell命令")
    click.echo("   • http_request - 发送HTTP请求")
    
    if not os.path.exists(tools_dir):
        click.echo("\n警告: tools/ 目录不存在，运行 nex init 创建")
        return
    
    click.echo("\n自定义工具:")
    
    loaded = set()
    # JSON 定义的工具
    for f in os.listdir(tools_dir):
        if f.endswith('.json'):
            name = f[:-5]
            json_path = os.path.join(tools_dir, f)
            py_path = os.path.join(tools_dir, f"{name}.py")
            try:
                with open(json_path, 'r', encoding='utf-8') as file:
                    tool_def = json.load(file)
                tool_name = tool_def.get("name", name)
                desc = tool_def.get("description", "无描述")
                has_py = "[有脚本]" if os.path.exists(py_path) else "[仅定义]"
                click.echo(f"   • {has_py} {tool_name} - {desc}")
                loaded.add(name)
            except Exception as e:
                click.echo(f"   • {name} [错误] - {e}")
    
    # 纯 Python 工具
    for f in os.listdir(tools_dir):
        if f.endswith('.py') and f[:-3] not in loaded:
            py_path = os.path.join(tools_dir, f)
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f[:-3], py_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'TOOL_DEF') and hasattr(module, 'execute'):
                    tool_def = module.TOOL_DEF
                    click.echo(f"   • [完整] {tool_def['name']} - {tool_def.get('description', '无描述')}")
                else:
                    click.echo(f"   • {f[:-3]} [?] - 缺少 TOOL_DEF 或 execute")
            except Exception as e:
                click.echo(f"   • {f[:-3]} [错误] - {e}")
    
    click.echo("\n说明: [有脚本]=有执行脚本  [仅定义]=仅定义无执行  [完整]=格式完整")


@cli.command()
@click.option('--dir', '-d', default='.', help='工作目录')
@click.option('--yes', '-y', is_flag=True, help='跳过确认')
def cleanup(dir, yes):
    """清理数据库中的残留数据（已删除的会话和孤立消息）"""
    dir = os.path.abspath(dir)
    db_path = os.path.join(dir, 'nex_data.db')
    
    if not os.path.exists(db_path):
        click.echo(f"错误: 数据库文件不存在: {db_path}")
        return
    
    from .database import Database
    db = Database(db_path)
    
    # 统计残留数据
    stats = db.get_cleanup_stats()
    
    if stats['inactive_sessions'] == 0 and stats['orphan_messages'] == 0:
        click.echo("数据库很干净，没有需要清理的数据")
        return
    
    click.echo("发现以下残留数据:")
    if stats['inactive_sessions'] > 0:
        click.echo(f"   • {stats['inactive_sessions']} 个已删除的会话")
    if stats['orphan_messages'] > 0:
        click.echo(f"   • {stats['orphan_messages']} 条孤立的消息")
    
    if not yes:
        if not click.confirm('\n确定要清理这些数据吗？'):
            click.echo("已取消")
            return
    
    # 执行清理
    result = db.cleanup()
    click.echo(f"\n清理完成:")
    click.echo(f"   • 删除了 {result['sessions_deleted']} 个会话")
    click.echo(f"   • 删除了 {result['messages_deleted']} 条消息")


def main():
    cli()


if __name__ == '__main__':
    main()
