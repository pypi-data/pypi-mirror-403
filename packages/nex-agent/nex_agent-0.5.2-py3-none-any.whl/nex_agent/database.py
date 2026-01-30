"""
NexAgent 数据库模块 - SQLite存储
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager


class Database:
    """SQLite数据库管理"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self.get_conn() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    user TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    user TEXT,
                    extra TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                
                CREATE TABLE IF NOT EXISTS providers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS models (
                    id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    thinking_model_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user);
                CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_id);
                
                CREATE TABLE IF NOT EXISTS personas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    avatar TEXT,
                    system_prompt TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS mcp_servers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    server_type TEXT DEFAULT 'sse',
                    headers TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS users (
                    name TEXT PRIMARY KEY
                );
            ''')
            # 检查并添加 sessions 的 persona_id 列（兼容旧数据库）
            try:
                conn.execute('SELECT persona_id FROM sessions LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE sessions ADD COLUMN persona_id INTEGER')
            # 检查并添加 extra 列（兼容旧数据库）
            try:
                conn.execute('SELECT extra FROM messages LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE messages ADD COLUMN extra TEXT')
            # 检查并添加 mcp_servers 的新列（兼容旧数据库）
            try:
                conn.execute('SELECT server_type FROM mcp_servers LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute("ALTER TABLE mcp_servers ADD COLUMN server_type TEXT DEFAULT 'sse'")
            try:
                conn.execute('SELECT headers FROM mcp_servers LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE mcp_servers ADD COLUMN headers TEXT')
            try:
                conn.execute('SELECT enabled FROM mcp_servers LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE mcp_servers ADD COLUMN enabled INTEGER DEFAULT 1')
            # 检查并添加 models 的 tags 列（兼容旧数据库）
            try:
                conn.execute('SELECT tags FROM models LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE models ADD COLUMN tags TEXT')
            # 检查并添加 models 的 model_type 列（兼容旧数据库）
            try:
                conn.execute('SELECT model_type FROM models LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute("ALTER TABLE models ADD COLUMN model_type TEXT DEFAULT 'chat'")
            # 检查并添加 personas 的参数列（兼容旧数据库）
            try:
                conn.execute('SELECT max_tokens FROM personas LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE personas ADD COLUMN max_tokens INTEGER')
            try:
                conn.execute('SELECT temperature FROM personas LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE personas ADD COLUMN temperature REAL')
            try:
                conn.execute('SELECT top_p FROM personas LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE personas ADD COLUMN top_p REAL')
            
            # 创建记忆表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    importance INTEGER DEFAULT 5,
                    source_session_id INTEGER,
                    source_message_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user)')
            
            # 创建OpenAPI配置表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS openapi_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_model_id TEXT NOT NULL UNIQUE,
                    internal_model_key TEXT NOT NULL,
                    persona_id INTEGER,
                    use_system_prompt INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE SET NULL
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_openapi_configs_api_model ON openapi_configs(api_model_id)')
    
    # ========== 会话管理 ==========
    def create_session(self, name: str, user: str) -> int:
        """创建新会话"""
        now = datetime.now().isoformat()
        with self.get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO sessions (name, user, created_at, updated_at) VALUES (?, ?, ?, ?)',
                (name, user, now, now)
            )
            return cursor.lastrowid
    
    def get_sessions(self, user: str = None, limit: int = None) -> List[Dict]:
        """获取会话列表"""
        with self.get_conn() as conn:
            sql = 'SELECT * FROM sessions WHERE is_active = 1'
            params = []
            if user:
                sql += ' AND user = ?'
                params.append(user)
            sql += ' ORDER BY updated_at DESC'
            if limit:
                sql += ' LIMIT ?'
                params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """获取单个会话"""
        with self.get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM sessions WHERE id = ? AND is_active = 1', (session_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_session(self, session_id: int, name: str = None) -> bool:
        """更新会话"""
        with self.get_conn() as conn:
            updates = ['updated_at = ?']
            params = [datetime.now().isoformat()]
            if name:
                updates.append('name = ?')
                params.append(name)
            params.append(session_id)
            result = conn.execute(
                f'UPDATE sessions SET {", ".join(updates)} WHERE id = ? AND is_active = 1',
                params
            )
            return result.rowcount > 0
    
    def delete_session(self, session_id: int) -> bool:
        """删除会话及其所有消息"""
        with self.get_conn() as conn:
            # 先删除会话的所有消息
            conn.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            # 再删除会话
            result = conn.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            return result.rowcount > 0
    
    def delete_all_sessions(self, user: str = None) -> int:
        """删除所有会话及其消息"""
        with self.get_conn() as conn:
            if user:
                # 获取用户的所有会话ID
                session_ids = [row['id'] for row in conn.execute(
                    'SELECT id FROM sessions WHERE user = ?', (user,)
                ).fetchall()]
                if session_ids:
                    placeholders = ','.join('?' * len(session_ids))
                    conn.execute(f'DELETE FROM messages WHERE session_id IN ({placeholders})', session_ids)
                    result = conn.execute('DELETE FROM sessions WHERE user = ?', (user,))
                else:
                    return 0
            else:
                conn.execute('DELETE FROM messages')
                result = conn.execute('DELETE FROM sessions')
            return result.rowcount
    
    # ========== 消息管理 ==========
    def add_message(self, session_id: int, role: str, content: str, user: str = None, extra: dict = None) -> int:
        """添加消息
        
        Args:
            session_id: 会话ID
            role: 角色 (user/assistant/tool)
            content: 消息内容
            user: 用户名（仅user角色）
            extra: 额外数据（如工具调用信息）
        """
        import json
        now = datetime.now().isoformat()
        extra_json = json.dumps(extra, ensure_ascii=False) if extra else None
        with self.get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO messages (session_id, role, content, user, extra, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (session_id, role, content, user, extra_json, now)
            )
            # 更新会话时间
            conn.execute(
                'UPDATE sessions SET updated_at = ? WHERE id = ?', (now, session_id)
            )
            return cursor.lastrowid
    
    def get_messages(self, session_id: int, limit: int = None) -> List[Dict]:
        """获取会话消息"""
        import json
        with self.get_conn() as conn:
            sql = 'SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC'
            params = [session_id]
            if limit:
                sql = f'SELECT * FROM (SELECT * FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?) ORDER BY id ASC'
                params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            result = []
            for row in rows:
                msg = dict(row)
                # 解析 extra JSON
                if msg.get('extra'):
                    try:
                        msg['extra'] = json.loads(msg['extra'])
                    except:
                        pass
                result.append(msg)
            return result
    
    def delete_message(self, message_id: int) -> bool:
        """删除单条消息"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM messages WHERE id = ?', (message_id,))
            return result.rowcount > 0
    
    def get_message(self, message_id: int) -> Optional[Dict]:
        """获取单条消息"""
        import json
        with self.get_conn() as conn:
            row = conn.execute('SELECT * FROM messages WHERE id = ?', (message_id,)).fetchone()
            if row:
                msg = dict(row)
                if msg.get('extra'):
                    try:
                        msg['extra'] = json.loads(msg['extra'])
                    except:
                        pass
                return msg
            return None
    
    def update_message(self, message_id: int, content: str) -> bool:
        """更新消息内容"""
        with self.get_conn() as conn:
            result = conn.execute(
                'UPDATE messages SET content = ? WHERE id = ?',
                (content, message_id)
            )
            return result.rowcount > 0
    
    def delete_messages_after(self, session_id: int, message_id: int) -> int:
        """删除指定消息之后的所有消息（用于重新生成）"""
        with self.get_conn() as conn:
            result = conn.execute(
                'DELETE FROM messages WHERE session_id = ? AND id > ?',
                (session_id, message_id)
            )
            return result.rowcount
    
    def get_last_user_message(self, session_id: int) -> Optional[Dict]:
        """获取会话中最后一条用户消息"""
        import json
        with self.get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM messages WHERE session_id = ? AND role = ? ORDER BY id DESC LIMIT 1',
                (session_id, 'user')
            ).fetchone()
            if row:
                msg = dict(row)
                if msg.get('extra'):
                    try:
                        msg['extra'] = json.loads(msg['extra'])
                    except:
                        pass
                return msg
            return None
    
    def delete_session_messages(self, session_id: int) -> int:
        """清空会话消息"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            return result.rowcount
    
    def get_message_count(self, session_id: int) -> int:
        """获取会话消息数量"""
        with self.get_conn() as conn:
            row = conn.execute(
                'SELECT COUNT(*) as count FROM messages WHERE session_id = ?', (session_id,)
            ).fetchone()
            return row['count']
    
    # ========== 设置管理 ==========
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """获取设置"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
            return row['value'] if row else default
    
    def set_setting(self, key: str, value: str) -> None:
        """保存设置"""
        with self.get_conn() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value)
            )
    
    def get_all_settings(self) -> Dict[str, str]:
        """获取所有设置"""
        with self.get_conn() as conn:
            rows = conn.execute('SELECT key, value FROM settings').fetchall()
            return {row['key']: row['value'] for row in rows}
    
    # ========== 兼容旧API ==========
    def get_history(self, limit: int = None) -> List[Dict]:
        """获取历史记录（兼容旧API）"""
        with self.get_conn() as conn:
            sql = '''
                SELECT m.id, m.content as message, m.user, m.created_at as time,
                       (SELECT content FROM messages WHERE session_id = m.session_id AND id = m.id + 1 AND role = 'assistant') as response
                FROM messages m
                WHERE m.role = 'user'
                ORDER BY m.id DESC
            '''
            if limit:
                sql += f' LIMIT {limit}'
            rows = conn.execute(sql).fetchall()
            result = []
            for row in rows:
                if row['response']:
                    result.append({
                        'id': row['id'],
                        'user': row['user'],
                        'message': row['message'],
                        'response': row['response'],
                        'time': row['time']
                    })
            return list(reversed(result))

    # ========== 服务商管理 ==========
    def create_provider(self, provider_id: str, name: str, api_key: str, base_url: str) -> bool:
        """创建服务商"""
        now = datetime.now().isoformat()
        with self.get_conn() as conn:
            try:
                conn.execute(
                    'INSERT INTO providers (id, name, api_key, base_url, created_at) VALUES (?, ?, ?, ?, ?)',
                    (provider_id, name, api_key, base_url, now)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_providers(self) -> List[Dict]:
        """获取所有服务商"""
        with self.get_conn() as conn:
            rows = conn.execute('SELECT * FROM providers ORDER BY created_at DESC').fetchall()
            return [dict(row) for row in rows]
    
    def get_provider(self, provider_id: str) -> Optional[Dict]:
        """获取单个服务商"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT * FROM providers WHERE id = ?', (provider_id,)).fetchone()
            return dict(row) if row else None
    
    def update_provider(self, provider_id: str, name: str = None, api_key: str = None, base_url: str = None) -> bool:
        """更新服务商"""
        with self.get_conn() as conn:
            updates = []
            params = []
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            if api_key is not None:
                updates.append('api_key = ?')
                params.append(api_key)
            if base_url is not None:
                updates.append('base_url = ?')
                params.append(base_url)
            if not updates:
                return False
            params.append(provider_id)
            result = conn.execute(
                f'UPDATE providers SET {", ".join(updates)} WHERE id = ?',
                params
            )
            return result.rowcount > 0
    
    def delete_provider(self, provider_id: str) -> bool:
        """删除服务商（同时删除关联的模型）"""
        with self.get_conn() as conn:
            # 先删除关联的模型
            conn.execute('DELETE FROM models WHERE provider_id = ?', (provider_id,))
            result = conn.execute('DELETE FROM providers WHERE id = ?', (provider_id,))
            return result.rowcount > 0
    
    # ========== 模型管理 ==========
    def create_model(self, model_key: str, provider_id: str, model_id: str, display_name: str, tags: List[str] = None, model_type: str = 'chat') -> bool:
        """创建模型
        
        Args:
            model_key: 模型唯一标识
            provider_id: 服务商ID
            model_id: 模型ID
            display_name: 显示名称
            tags: 标签列表
            model_type: 模型类型 (chat/embedding)
        """
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
        with self.get_conn() as conn:
            try:
                conn.execute(
                    'INSERT INTO models (id, provider_id, model_id, display_name, tags, model_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (model_key, provider_id, model_id, display_name, tags_json, model_type, now)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_models_list(self) -> List[Dict]:
        """获取所有模型（包含服务商信息）"""
        with self.get_conn() as conn:
            rows = conn.execute('''
                SELECT m.*, p.name as provider_name, p.api_key, p.base_url
                FROM models m
                JOIN providers p ON m.provider_id = p.id
                ORDER BY m.created_at DESC
            ''').fetchall()
            result = []
            for row in rows:
                m = dict(row)
                if m.get('tags'):
                    try:
                        m['tags'] = json.loads(m['tags'])
                    except:
                        m['tags'] = []
                else:
                    m['tags'] = []
                # 确保 model_type 有默认值
                if not m.get('model_type'):
                    m['model_type'] = 'chat'
                result.append(m)
            return result
    
    def get_model(self, model_key: str) -> Optional[Dict]:
        """获取单个模型（包含服务商信息）"""
        with self.get_conn() as conn:
            row = conn.execute('''
                SELECT m.*, p.name as provider_name, p.api_key, p.base_url
                FROM models m
                JOIN providers p ON m.provider_id = p.id
                WHERE m.id = ?
            ''', (model_key,)).fetchone()
            if row:
                m = dict(row)
                if m.get('tags'):
                    try:
                        m['tags'] = json.loads(m['tags'])
                    except:
                        m['tags'] = []
                else:
                    m['tags'] = []
                # 确保 model_type 有默认值
                if not m.get('model_type'):
                    m['model_type'] = 'chat'
                return m
            return None
    
    def get_models_by_provider(self, provider_id: str) -> List[Dict]:
        """获取服务商下的所有模型"""
        with self.get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM models WHERE provider_id = ? ORDER BY created_at DESC',
                (provider_id,)
            ).fetchall()
            result = []
            for row in rows:
                m = dict(row)
                if m.get('tags'):
                    try:
                        m['tags'] = json.loads(m['tags'])
                    except:
                        m['tags'] = []
                else:
                    m['tags'] = []
                result.append(m)
            return result
    
    def update_model(self, model_key: str, new_key: str = None, model_id: str = None, display_name: str = None, tags: List[str] = None, model_type: str = None) -> bool:
        """更新模型"""
        with self.get_conn() as conn:
            updates = []
            params = []
            
            # 如果要更新 key，先检查新 key 是否已存在
            if new_key is not None and new_key != model_key:
                existing = conn.execute('SELECT id FROM models WHERE id = ?', (new_key,)).fetchone()
                if existing:
                    return False  # 新 key 已存在
                updates.append('id = ?')
                params.append(new_key)
            
            if model_id is not None:
                updates.append('model_id = ?')
                params.append(model_id)
            if display_name is not None:
                updates.append('display_name = ?')
                params.append(display_name)
            if tags is not None:
                updates.append('tags = ?')
                params.append(json.dumps(tags, ensure_ascii=False) if tags else None)
            if model_type is not None:
                updates.append('model_type = ?')
                params.append(model_type)
            if not updates:
                return False
            params.append(model_key)
            result = conn.execute(
                f'UPDATE models SET {", ".join(updates)} WHERE id = ?',
                params
            )
            return result.rowcount > 0
    
    def delete_model(self, model_key: str) -> bool:
        """删除模型"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM models WHERE id = ?', (model_key,))
            return result.rowcount > 0

    # ========== MCP服务器管理 ==========
    def create_mcp_server(self, server_id: str, name: str, url: str, server_type: str = "sse", headers: Dict = None) -> bool:
        """创建MCP服务器"""
        now = datetime.now().isoformat()
        headers_json = json.dumps(headers, ensure_ascii=False) if headers else None
        with self.get_conn() as conn:
            try:
                conn.execute(
                    'INSERT INTO mcp_servers (id, name, url, server_type, headers, enabled, created_at) VALUES (?, ?, ?, ?, ?, 1, ?)',
                    (server_id, name, url, server_type, headers_json, now)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_mcp_servers(self) -> List[Dict]:
        """获取所有MCP服务器"""
        with self.get_conn() as conn:
            rows = conn.execute('SELECT * FROM mcp_servers ORDER BY created_at DESC').fetchall()
            result = []
            for row in rows:
                server = dict(row)
                if server.get('headers'):
                    try:
                        server['headers'] = json.loads(server['headers'])
                    except:
                        server['headers'] = {}
                else:
                    server['headers'] = {}
                # 转换 enabled 为布尔值
                server['enabled'] = bool(server.get('enabled', 1))
                result.append(server)
            return result
    
    def get_mcp_server(self, server_id: str) -> Optional[Dict]:
        """获取单个MCP服务器"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT * FROM mcp_servers WHERE id = ?', (server_id,)).fetchone()
            if row:
                server = dict(row)
                if server.get('headers'):
                    try:
                        server['headers'] = json.loads(server['headers'])
                    except:
                        server['headers'] = {}
                else:
                    server['headers'] = {}
                # 转换 enabled 为布尔值
                server['enabled'] = bool(server.get('enabled', 1))
                return server
            return None
    
    def update_mcp_server(self, server_id: str, name: str = None, url: str = None, server_type: str = None, headers: Dict = None, enabled: bool = None) -> bool:
        """更新MCP服务器"""
        with self.get_conn() as conn:
            updates = []
            params = []
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            if url is not None:
                updates.append('url = ?')
                params.append(url)
            if server_type is not None:
                updates.append('server_type = ?')
                params.append(server_type)
            if headers is not None:
                updates.append('headers = ?')
                params.append(json.dumps(headers, ensure_ascii=False) if headers else None)
            if enabled is not None:
                updates.append('enabled = ?')
                params.append(1 if enabled else 0)
            if not updates:
                return False
            params.append(server_id)
            result = conn.execute(
                f'UPDATE mcp_servers SET {", ".join(updates)} WHERE id = ?',
                params
            )
            return result.rowcount > 0
    
    def delete_mcp_server(self, server_id: str) -> bool:
        """删除MCP服务器"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM mcp_servers WHERE id = ?', (server_id,))
            return result.rowcount > 0

    # ========== 数据清理 ==========
    def get_cleanup_stats(self) -> Dict:
        """获取需要清理的数据统计"""
        with self.get_conn() as conn:
            # 已删除的会话（is_active = 0）
            inactive_sessions = conn.execute(
                'SELECT COUNT(*) as count FROM sessions WHERE is_active = 0'
            ).fetchone()['count']
            
            # 孤立的消息（会话已被删除或标记为删除）
            orphan_messages = conn.execute('''
                SELECT COUNT(*) as count FROM messages 
                WHERE session_id NOT IN (SELECT id FROM sessions WHERE is_active = 1)
            ''').fetchone()['count']
            
            return {
                'inactive_sessions': inactive_sessions,
                'orphan_messages': orphan_messages
            }
    
    def cleanup(self) -> Dict:
        """清理残留数据"""
        with self.get_conn() as conn:
            # 删除孤立的消息
            messages_result = conn.execute('''
                DELETE FROM messages 
                WHERE session_id NOT IN (SELECT id FROM sessions WHERE is_active = 1)
            ''')
            messages_deleted = messages_result.rowcount
            
            # 删除已标记删除的会话
            sessions_result = conn.execute('DELETE FROM sessions WHERE is_active = 0')
            sessions_deleted = sessions_result.rowcount
            
            return {
                'sessions_deleted': sessions_deleted,
                'messages_deleted': messages_deleted
            }

    # ========== 角色卡管理 ==========
    def create_persona(self, name: str, system_prompt: str, avatar: str = None, 
                       max_tokens: int = None, temperature: float = None, top_p: float = None) -> int:
        """创建角色卡"""
        now = datetime.now().isoformat()
        with self.get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO personas (name, avatar, system_prompt, max_tokens, temperature, top_p, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (name, avatar, system_prompt, max_tokens, temperature, top_p, now, now)
            )
            return cursor.lastrowid

    def get_personas(self) -> List[Dict]:
        """获取所有角色卡"""
        with self.get_conn() as conn:
            rows = conn.execute('SELECT * FROM personas ORDER BY updated_at DESC').fetchall()
            return [dict(row) for row in rows]

    def get_persona(self, persona_id: int) -> Optional[Dict]:
        """获取单个角色卡"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT * FROM personas WHERE id = ?', (persona_id,)).fetchone()
            return dict(row) if row else None

    def update_persona(self, persona_id: int, name: str = None, system_prompt: str = None, avatar: str = None,
                       max_tokens: int = None, temperature: float = None, top_p: float = None) -> bool:
        """更新角色卡"""
        with self.get_conn() as conn:
            updates = ['updated_at = ?']
            params = [datetime.now().isoformat()]
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            if system_prompt is not None:
                updates.append('system_prompt = ?')
                params.append(system_prompt)
            if avatar is not None:
                updates.append('avatar = ?')
                params.append(avatar)
            if max_tokens is not None:
                updates.append('max_tokens = ?')
                params.append(max_tokens if max_tokens > 0 else None)
            if temperature is not None:
                updates.append('temperature = ?')
                params.append(temperature if temperature >= 0 else None)
            if top_p is not None:
                updates.append('top_p = ?')
                params.append(top_p if top_p >= 0 else None)
            params.append(persona_id)
            result = conn.execute(
                f'UPDATE personas SET {", ".join(updates)} WHERE id = ?',
                params
            )
            return result.rowcount > 0

    def delete_persona(self, persona_id: int) -> bool:
        """删除角色卡"""
        with self.get_conn() as conn:
            # 将使用该角色卡的会话的 persona_id 设为 NULL
            conn.execute('UPDATE sessions SET persona_id = NULL WHERE persona_id = ?', (persona_id,))
            result = conn.execute('DELETE FROM personas WHERE id = ?', (persona_id,))
            return result.rowcount > 0

    def set_session_persona(self, session_id: int, persona_id: int = None) -> bool:
        """设置会话的角色卡"""
        with self.get_conn() as conn:
            result = conn.execute(
                'UPDATE sessions SET persona_id = ?, updated_at = ? WHERE id = ?',
                (persona_id, datetime.now().isoformat(), session_id)
            )
            return result.rowcount > 0

    def get_session_persona(self, session_id: int) -> Optional[Dict]:
        """获取会话的角色卡"""
        with self.get_conn() as conn:
            row = conn.execute('''
                SELECT p.* FROM personas p
                JOIN sessions s ON s.persona_id = p.id
                WHERE s.id = ?
            ''', (session_id,)).fetchone()
            return dict(row) if row else None

    # ========== 用户设置管理 ==========
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """获取设置值"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
            return row['value'] if row else default

    def set_setting(self, key: str, value: str) -> bool:
        """设置值"""
        with self.get_conn() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
            return True

    def delete_setting(self, key: str) -> bool:
        """删除设置"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM settings WHERE key = ?', (key,))
            return result.rowcount > 0

    # ========== 记忆管理 ==========
    def add_memory(self, user: str, content: str, embedding: List[float] = None, 
                   importance: int = 5, source_session_id: int = None, 
                   source_message_id: int = None) -> int:
        """添加记忆"""
        now = datetime.now().isoformat()
        embedding_json = json.dumps(embedding) if embedding else None
        with self.get_conn() as conn:
            cursor = conn.execute(
                '''INSERT INTO memories (user, content, embedding, importance, 
                   source_session_id, source_message_id, created_at, updated_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (user, content, embedding_json, importance, source_session_id, 
                 source_message_id, now, now)
            )
            return cursor.lastrowid

    def get_memories(self, user: str, limit: int = 50) -> List[Dict]:
        """获取用户的所有记忆"""
        with self.get_conn() as conn:
            rows = conn.execute(
                '''SELECT * FROM memories WHERE user = ? 
                   ORDER BY importance DESC, updated_at DESC LIMIT ?''',
                (user, limit)
            ).fetchall()
            result = []
            for row in rows:
                m = dict(row)
                if m.get('embedding'):
                    try:
                        m['embedding'] = json.loads(m['embedding'])
                    except:
                        m['embedding'] = None
                result.append(m)
            return result

    def get_memories_with_embedding(self, user: str) -> List[Dict]:
        """获取用户所有带向量的记忆"""
        with self.get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM memories WHERE user = ? AND embedding IS NOT NULL',
                (user,)
            ).fetchall()
            result = []
            for row in rows:
                m = dict(row)
                if m.get('embedding'):
                    try:
                        m['embedding'] = json.loads(m['embedding'])
                    except:
                        continue  # 跳过无效的向量
                result.append(m)
            return result
    
    def get_all_memories_with_embedding(self) -> List[Dict]:
        """获取所有用户的带向量的记忆"""
        with self.get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM memories WHERE embedding IS NOT NULL'
            ).fetchall()
            result = []
            for row in rows:
                m = dict(row)
                if m.get('embedding'):
                    try:
                        m['embedding'] = json.loads(m['embedding'])
                    except:
                        continue  # 跳过无效的向量
                result.append(m)
            return result

    def update_memory(self, memory_id: int, content: str = None, 
                      embedding: List[float] = None, importance: int = None) -> bool:
        """更新记忆"""
        with self.get_conn() as conn:
            updates = ['updated_at = ?']
            params = [datetime.now().isoformat()]
            if content is not None:
                updates.append('content = ?')
                params.append(content)
            if embedding is not None:
                updates.append('embedding = ?')
                params.append(json.dumps(embedding))
            if importance is not None:
                updates.append('importance = ?')
                params.append(importance)
            params.append(memory_id)
            result = conn.execute(
                f'UPDATE memories SET {", ".join(updates)} WHERE id = ?',
                params
            )
            return result.rowcount > 0

    def delete_memory(self, memory_id: int) -> bool:
        """删除记忆"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
            return result.rowcount > 0

    def delete_user_memories(self, user: str) -> int:
        """删除用户的所有记忆"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM memories WHERE user = ?', (user,))
            return result.rowcount

    def get_memory(self, memory_id: int) -> Optional[Dict]:
        """获取单条记忆"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT * FROM memories WHERE id = ?', (memory_id,)).fetchone()
            if row:
                m = dict(row)
                if m.get('embedding'):
                    try:
                        m['embedding'] = json.loads(m['embedding'])
                    except:
                        m['embedding'] = None
                return m
            return None

    # ========== OpenAPI 配置管理 ==========
    def get_openapi_configs(self) -> List[Dict]:
        """获取所有OpenAPI配置"""
        with self.get_conn() as conn:
            rows = conn.execute('''
                SELECT oc.*, p.name as persona_name, m.display_name as model_name
                FROM openapi_configs oc
                LEFT JOIN personas p ON oc.persona_id = p.id
                LEFT JOIN models m ON oc.internal_model_key = m.id
                ORDER BY oc.api_model_id
            ''').fetchall()
            return [dict(row) for row in rows]
    
    def get_openapi_config(self, api_model_id: str) -> Optional[Dict]:
        """根据API模型ID获取配置"""
        with self.get_conn() as conn:
            row = conn.execute('''
                SELECT oc.*, p.name as persona_name, p.system_prompt, m.display_name as model_name
                FROM openapi_configs oc
                LEFT JOIN personas p ON oc.persona_id = p.id
                LEFT JOIN models m ON oc.internal_model_key = m.id
                WHERE oc.api_model_id = ?
            ''', (api_model_id,)).fetchone()
            return dict(row) if row else None
    
    def create_openapi_config(self, api_model_id: str, internal_model_key: str, 
                             persona_id: int = None, use_system_prompt: bool = False) -> int:
        """创建OpenAPI配置"""
        now = datetime.now().isoformat()
        with self.get_conn() as conn:
            cursor = conn.execute('''
                INSERT INTO openapi_configs 
                (api_model_id, internal_model_key, persona_id, use_system_prompt, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (api_model_id, internal_model_key, persona_id, int(use_system_prompt), now, now))
            return cursor.lastrowid
    
    def update_openapi_config(self, api_model_id: str, internal_model_key: str = None,
                             persona_id: int = None, use_system_prompt: bool = None) -> bool:
        """更新OpenAPI配置"""
        updates = ['updated_at = ?']
        params = [datetime.now().isoformat()]
        
        if internal_model_key is not None:
            updates.append('internal_model_key = ?')
            params.append(internal_model_key)
        if persona_id is not None:
            updates.append('persona_id = ?')
            params.append(persona_id)
        if use_system_prompt is not None:
            updates.append('use_system_prompt = ?')
            params.append(int(use_system_prompt))
        
        params.append(api_model_id)
        
        with self.get_conn() as conn:
            conn.execute(
                f'UPDATE openapi_configs SET {", ".join(updates)} WHERE api_model_id = ?',
                params
            )
            return True
    
    def delete_openapi_config(self, api_model_id: str) -> bool:
        """删除OpenAPI配置"""
        with self.get_conn() as conn:
            conn.execute('DELETE FROM openapi_configs WHERE api_model_id = ?', (api_model_id,))
            return True
    
    def get_api_sessions(self, start_time=None, model_filter: str = ""):
        """获取API会话记录"""
        with self.get_conn() as conn:
            query = '''
                SELECT s.*, p.name as persona_name 
                FROM sessions s
                LEFT JOIN personas p ON s.persona_id = p.id
                WHERE s.user = 'api_user'
            '''
            params = []
            
            if start_time:
                query += ' AND s.created_at >= ?'
                params.append(start_time.isoformat())
            
            if model_filter:
                query += ' AND s.name LIKE ?'
                params.append(f'%{model_filter}%')
            
            query += ' ORDER BY s.created_at DESC'
            
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    # ========== 用户管理 ==========
    def get_users(self) -> List[Dict]:
        """获取所有用户"""
        with self.get_conn() as conn:
            rows = conn.execute('SELECT name FROM users ORDER BY name').fetchall()
            return [dict(row) for row in rows]
    
    def save_user(self, name: str) -> bool:
        """保存用户"""
        if not name or name.strip() == '':
            return False
        
        name = name.strip()
        
        with self.get_conn() as conn:
            # 使用 INSERT OR IGNORE 避免重复插入
            conn.execute('INSERT OR IGNORE INTO users (name) VALUES (?)', (name,))
            return True
    
    def delete_user(self, name: str) -> bool:
        """删除用户"""
        with self.get_conn() as conn:
            conn.execute('DELETE FROM users WHERE name = ?', (name,))
            return True
