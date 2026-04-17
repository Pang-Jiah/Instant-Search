import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional

class SessionManager:
    """会话管理器"""
    
    def __init__(self, base_dir: str = None):
        """初始化会话管理器
        
        Args:
            base_dir: 会话存储的基础目录，默认为TEMP目录
        """
        if base_dir is None:
            self.base_dir = os.path.join(os.getcwd(), 'TEMP')
        else:
            self.base_dir = base_dir
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        
        # 会话存储目录
        self.sessions_dir = os.path.join(self.base_dir, 'sessions')
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
    
    def create_session(self) -> str:
        """创建新会话
        
        Returns:
            会话ID
        """
        # 生成会话ID：YYYYMMDD_HHMMSS_随机标识符
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_id = str(random.randint(1000, 9999))
        session_id = f"{timestamp}_{random_id}"
        
        # 创建会话文件夹
        session_path = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_path)
        
        # 创建会话元数据文件
        metadata = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'name': f'会话 {timestamp}',
            'favorited': False,
            'messages': []
        }
        
        self._save_metadata(session_id, metadata)
        
        return session_id
    
    def save_session_data(self, session_id: str, image_path: str, messages: List[Dict]):
        """保存会话数据
        
        Args:
            session_id: 会话ID
            image_path: 图片路径
            messages: 消息列表
        """
        session_path = os.path.join(self.sessions_dir, session_id)
        if not os.path.exists(session_path):
            raise Exception(f"会话 {session_id} 不存在")
        
        # 图片已经直接保存到会话文件夹中，不需要复制
        image_filename = os.path.basename(image_path)
        
        # 更新元数据
        metadata = self._load_metadata(session_id)
        metadata['last_modified'] = datetime.now().isoformat()
        metadata['image_path'] = image_filename
        metadata['messages'] = messages
        
        self._save_metadata(session_id, metadata)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，如果会话不存在则返回None
        """
        try:
            return self._load_metadata(session_id)
        except:
            return None
    
    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话
        
        Returns:
            会话列表，按最后修改时间倒序排列
        """
        sessions = []
        
        for session_id in os.listdir(self.sessions_dir):
            session_path = os.path.join(self.sessions_dir, session_id)
            if os.path.isdir(session_path):
                try:
                    metadata = self._load_metadata(session_id)
                    sessions.append(metadata)
                except:
                    pass
        
        # 按最后修改时间倒序排列
        sessions.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
        
        return sessions
    
    def update_session_name(self, session_id: str, name: str):
        """更新会话名称
        
        Args:
            session_id: 会话ID
            name: 新名称
        """
        metadata = self._load_metadata(session_id)
        metadata['name'] = name
        metadata['last_modified'] = datetime.now().isoformat()
        self._save_metadata(session_id, metadata)
    
    def toggle_favorite(self, session_id: str):
        """切换会话收藏状态
        
        Args:
            session_id: 会话ID
        """
        metadata = self._load_metadata(session_id)
        metadata['favorited'] = not metadata.get('favorited', False)
        metadata['last_modified'] = datetime.now().isoformat()
        self._save_metadata(session_id, metadata)
    
    def delete_session(self, session_id: str):
        """删除会话
        
        Args:
            session_id: 会话ID
        """
        session_path = os.path.join(self.sessions_dir, session_id)
        if os.path.exists(session_path):
            import shutil
            shutil.rmtree(session_path)
    
    def export_session(self, session_id: str, export_path: str) -> str:
        """导出会话
        
        Args:
            session_id: 会话ID
            export_path: 导出路径
            
        Returns:
            导出文件路径
        """
        metadata = self._load_metadata(session_id)
        session_path = os.path.join(self.sessions_dir, session_id)
        
        # 导出为JSON文件
        export_file = os.path.join(export_path, f"session_{session_id}.json")
        
        # 读取图片为base64
        if 'image_path' in metadata:
            image_path = os.path.join(session_path, metadata['image_path'])
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    import base64
                    metadata['image_base64'] = base64.b64encode(f.read()).decode('utf-8')
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return export_file
    
    def get_storage_usage(self) -> Dict:
        """获取存储使用情况
        
        Returns:
            存储使用情况
        """
        total_size = 0
        session_count = 0
        
        for session_id in os.listdir(self.sessions_dir):
            session_path = os.path.join(self.sessions_dir, session_id)
            if os.path.isdir(session_path):
                session_count += 1
                for root, dirs, files in os.walk(session_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
        
        return {
            'session_count': session_count,
            'total_size': total_size,
            'total_size_human': self._format_size(total_size)
        }
    
    def _load_metadata(self, session_id: str) -> Dict:
        """加载会话元数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            元数据
        """
        metadata_path = os.path.join(self.sessions_dir, session_id, 'metadata.json')
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_metadata(self, session_id: str, metadata: Dict):
        """保存会话元数据
        
        Args:
            session_id: 会话ID
            metadata: 元数据
        """
        metadata_path = os.path.join(self.sessions_dir, session_id, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小
        
        Args:
            size: 字节数
            
        Returns:
            格式化后的大小
        """
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        current_size = size
        
        while current_size >= 1024 and unit_index < len(units) - 1:
            current_size /= 1024
            unit_index += 1
        
        return f"{current_size:.2f} {units[unit_index]}"
