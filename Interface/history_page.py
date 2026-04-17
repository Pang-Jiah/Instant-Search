"""历史记录页面"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QMessageBox, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from .fluent_components import FluentScrollArea, FluentCard, FluentButton, FluentTitleLabel, FluentSubtitleLabel, FluentBodyLabel, FluentDivider, FluentLineEdit, FluentFonts, FluentStyle, FluentCorners
from session_manager import SessionManager

class HistoryPage(QWidget):
    """历史记录页面"""
    
    # 信号：选择会话
    session_selected = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__()
        # 初始化会话管理器
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'TEMP')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        self.session_manager = SessionManager(self.temp_dir)
        self.current_session = None
        # 存储选中的会话ID
        self.selected_sessions = set()
        # 存储卡片和会话ID的映射
        self.card_session_map = {}
        self.init_ui()
        self.load_sessions("", "全部")
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建 Fluent 风格滚动区域
        scroll_area = FluentScrollArea()
         # 创建滚动内容容器
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(30, 30, 30, 30)
        scroll_layout.setSpacing(20)

        # 标题
        title = FluentTitleLabel("历史记录")
        scroll_layout.addWidget(title)

         # 描述
        desc = FluentSubtitleLabel("查看和管理您的搜索历史记录。")
        scroll_layout.addWidget(desc)

        # 分隔线
        divider = FluentDivider()
        scroll_layout.addWidget(divider)

        # 搜索和筛选栏
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        # 搜索框
        self.search_input = FluentLineEdit()
        self.search_input.setPlaceholderText("搜索会话...")
        self.search_input.textChanged.connect(self.filter_sessions)
        top_layout.addWidget(self.search_input, 1)
        
        # 筛选下拉框
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "收藏", "最近7天", "最近30天"])
        self.filter_combo.currentTextChanged.connect(self.filter_sessions)
        top_layout.addWidget(self.filter_combo)
        
        # 排序下拉框
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按时间倒序", "按时间正序", "按名称排序"])
        self.sort_combo.currentTextChanged.connect(self.sort_sessions)
        top_layout.addWidget(self.sort_combo)
        
        # 全选复选框
        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        top_layout.addWidget(self.select_all_checkbox)
        
        # 删除选中按钮
        self.delete_selected_button = FluentButton("删除选中")
        self.delete_selected_button.clicked.connect(self.delete_selected_sessions)
        self.delete_selected_button.setEnabled(False)
        top_layout.addWidget(self.delete_selected_button)
        
        # 存储容量显示
        self.storage_label = FluentBodyLabel()
        self.update_storage_info()
        top_layout.addWidget(self.storage_label)
        
        # 清理按钮已移除，只保留批量清理功能
        
        scroll_layout.addLayout(top_layout)
        
        # 会话卡片容器（采用网格布局，类似小红书）
        self.session_container = QWidget()
        self.session_layout = QGridLayout(self.session_container)
        self.session_layout.setSpacing(20)
        self.session_layout.setContentsMargins(0, 0, 0, 0)
        # 设置网格布局靠左对齐
        self.session_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        scroll_layout.addWidget(self.session_container)

        scroll_layout.addStretch()
        
        # 设置滚动内容的最小高度
        scroll_content.setMinimumHeight(800)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        # 设置页面尺寸策略
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def refresh_sessions(self):
        """刷新会话列表"""
        self.load_sessions("", "全部")
    
    def load_sessions(self, search_text="", filter_option="全部"):
        """加载会话列表
        
        Args:
            search_text: 搜索关键词
            filter_option: 筛选条件
        """
        # 清空容器
        for i in reversed(range(self.session_layout.count())):
            widget = self.session_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 清空映射和选中集合
        self.card_session_map.clear()
        self.selected_sessions.clear()
        # 禁用删除按钮
        self.delete_selected_button.setEnabled(False)
        
        sessions = self.session_manager.get_all_sessions()
        
        # 1. 搜索筛选
        if search_text:
            filtered_sessions = []
            for session in sessions:
                # 检查会话名称
                name = session.get('name', '').lower()
                if search_text in name:
                    filtered_sessions.append(session)
                    continue
                # 检查消息内容
                messages = session.get('messages', [])
                for message in messages:
                    content = message.get('content', '').lower()
                    if search_text in content:
                        filtered_sessions.append(session)
                        break
            sessions = filtered_sessions
        
        # 2. 时间筛选
        if filter_option == "最近7天":
            from datetime import datetime, timedelta
            seven_days_ago = datetime.now() - timedelta(days=7)
            filtered_sessions = []
            for session in sessions:
                created_at = session.get('created_at', '')
                if created_at:
                    try:
                        session_time = datetime.fromisoformat(created_at)
                        if session_time >= seven_days_ago:
                            filtered_sessions.append(session)
                    except:
                        pass
            sessions = filtered_sessions
        elif filter_option == "最近30天":
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            filtered_sessions = []
            for session in sessions:
                created_at = session.get('created_at', '')
                if created_at:
                    try:
                        session_time = datetime.fromisoformat(created_at)
                        if session_time >= thirty_days_ago:
                            filtered_sessions.append(session)
                    except:
                        pass
            sessions = filtered_sessions
        elif filter_option == "收藏":
            filtered_sessions = [session for session in sessions if session.get('favorited', False)]
            sessions = filtered_sessions
        
        # 3. 排序
        sort_option = self.sort_combo.currentText()
        if sort_option == "按时间倒序":
            sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_option == "按时间正序":
            sessions.sort(key=lambda x: x.get('created_at', ''))
        elif sort_option == "按名称排序":
            sessions.sort(key=lambda x: x.get('name', '').lower())
        # 默认按时间倒序排序
        else:
            sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 使用固定列数 3
        column_count = 3
        
        # 确保会话容器有足够的高度
        self.session_container.setMinimumHeight(800)
        
        for i, session in enumerate(sessions):
            # 创建会话卡片
            card = FluentCard()
            card.setFixedWidth(300)
            card.setFixedHeight(400)
            card.setStyleSheet("""
                FluentCard {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
                FluentCard:hover {
                    background-color: #f5f5f5;
                }
                FluentCard:pressed {
                    background-color: #e8e8e8;
                }
                FluentCard[selected="true"] {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                }
            """)
            # 初始化卡片属性
            card.setProperty("selected", "false")
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(0)
            
            # 图片预览
            image_label = QLabel()
            image_label.setFixedHeight(200)
            image_label.setScaledContents(True)
            image_label.setStyleSheet("background-color: #f8f8f8;")
            
            # 加载会话图片
            image_path = session.get('image_path', '')
            if image_path:
                session_dir = os.path.join(self.session_manager.sessions_dir, session.get('session_id', ''))
                full_image_path = os.path.join(session_dir, image_path)
                if os.path.exists(full_image_path):
                    pixmap = QPixmap(full_image_path)
                    image_label.setPixmap(pixmap)
            
            card_layout.addWidget(image_label)
            
            # 卡片内容
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(16, 12, 16, 16)
            content_layout.setSpacing(10)
            
            # 消息预览
            messages = session.get('messages', [])
            if messages:
                last_message = messages[-1]
                preview_text = last_message.get('content', '')[:80]
                if len(last_message.get('content', '')) > 80:
                    preview_text += "..."
                preview_label = FluentBodyLabel(preview_text)
                preview_label.setFont(QFont(FluentFonts.FAMILY, 12))
                preview_label.setStyleSheet("color: #555;")
                preview_label.setWordWrap(True)
                content_layout.addWidget(preview_label)
            
            # 时间
            created_at = session.get('created_at', '')
            if created_at:
                try:
                    from datetime import datetime
                    date_time = datetime.fromisoformat(created_at)
                    time_label = FluentBodyLabel(date_time.strftime('%Y-%m-%d %H:%M'))
                    time_label.setFont(QFont(FluentFonts.FAMILY, 11))
                    time_label.setStyleSheet("color: #666;")
                    content_layout.addWidget(time_label)
                except:
                    pass
            
            # 操作按钮
            buttons_layout = QHBoxLayout()
            
            open_button = FluentButton("查看")
            open_button.setFixedSize(60, 28)
            open_button.clicked.connect(lambda _, s=session: self.on_session_clicked(s))
            buttons_layout.addWidget(open_button)
            
            buttons_layout.addStretch()
            
            # 收藏按钮
            favorite_button = FluentButton("⭐" if session.get('favorited', False) else "☆")
            favorite_button.setFixedSize(28, 28)
            favorite_button.clicked.connect(lambda _, s=session: self.toggle_favorite(s))
            buttons_layout.addWidget(favorite_button)
            
            content_layout.addLayout(buttons_layout)
            
            card_layout.addWidget(content_widget)
            
            # 存储卡片和会话ID的映射
            session_id = session.get('session_id')
            self.card_session_map[card] = session_id
            
            # 添加点击事件，实现选择功能
            # 使用 lambda 函数的默认参数来捕获当前的 session_id 和 card
            def create_mouse_press_event(current_card, current_session_id):
                def mouse_press_event(event):
                    # 切换选中状态
                    if current_card in self.card_session_map:
                        if current_session_id in self.selected_sessions:
                            # 取消选中
                            self.selected_sessions.remove(current_session_id)
                            # 恢复卡片的默认样式
                            current_card.setStyleSheet("""
                                FluentCard {
                                    background-color: white;
                                    border-radius: 8px;
                                    border: 1px solid #e0e0e0;
                                }
                                FluentCard:hover {
                                    background-color: #f5f5f5;
                                }
                                FluentCard:pressed {
                                    background-color: #e8e8e8;
                                }
                            """)
                        else:
                            # 选中
                            self.selected_sessions.add(current_session_id)
                            # 设置卡片的选中样式
                            current_card.setStyleSheet("""
                                FluentCard {
                                    background-color: #e3f2fd;
                                    border-radius: 8px;
                                    border: 2px solid #2196f3;
                                }
                                FluentCard:hover {
                                    background-color: #e3f2fd;
                                }
                                FluentCard:pressed {
                                    background-color: #bbdefb;
                                }
                            """)
                        # 更新删除按钮状态
                        self.delete_selected_button.setEnabled(len(self.selected_sessions) > 0)
                        # 重置全选复选框状态
                        if len(self.selected_sessions) == len(self.card_session_map):
                            self.select_all_checkbox.setChecked(True)
                        else:
                            self.select_all_checkbox.setChecked(False)
                return mouse_press_event
            
            card.mousePressEvent = create_mouse_press_event(card, session_id)
            
            # 添加到网格布局
            row = i // column_count
            col = i % column_count
            self.session_layout.addWidget(card, row, col)
    
    def on_session_clicked(self, session):
        """会话点击事件"""
        self.current_session = session
        # 触发会话选择信号
        self.session_selected.emit(session.get('session_id'), session)
    
    def toggle_favorite(self, session):
        """切换收藏状态"""
        try:
            self.session_manager.toggle_favorite(session.get('session_id'))
            # 保持当前的搜索和筛选状态
            search_text = self.search_input.text().lower()
            filter_option = self.filter_combo.currentText()
            self.load_sessions(search_text, filter_option)
        except Exception as e:
            QMessageBox.warning(self, "操作失败", f"切换收藏状态时出错: {e}")
    
    def filter_sessions(self):
        """筛选会话"""
        # 获取搜索关键词
        search_text = self.search_input.text().lower()
        # 获取筛选条件
        filter_option = self.filter_combo.currentText()
        # 加载并筛选会话
        self.load_sessions(search_text, filter_option)
    
    def sort_sessions(self):
        """排序会话"""
        # 获取搜索关键词
        search_text = self.search_input.text().lower()
        # 获取筛选条件
        filter_option = self.filter_combo.currentText()
        # 加载并排序会话
        self.load_sessions(search_text, filter_option)
    
    def update_storage_info(self):
        """更新存储信息"""
        usage = self.session_manager.get_storage_usage()
        self.storage_label.setText(f"存储: {usage['total_size_human']} ({usage['session_count']} 个会话)")

    def delete_selected_sessions(self):
        """删除选中的会话"""
        if not self.selected_sessions:
            return
        
        # 保存选中的会话数量
        deleted_count = len(self.selected_sessions)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {deleted_count} 个会话吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除选中的会话
                for session_id in list(self.selected_sessions):  # 使用列表副本避免迭代时修改集合
                    self.session_manager.delete_session(session_id)
                
                # 重新加载会话列表
                search_text = self.search_input.text().lower()
                filter_option = self.filter_combo.currentText()
                self.load_sessions(search_text, filter_option)
                
                self.current_session = None
                self.update_storage_info()
                QMessageBox.information(self, "删除成功", f"已删除 {deleted_count} 个会话")
            except Exception as e:
                QMessageBox.warning(self, "删除失败", f"删除会话时出错: {e}")

    def toggle_select_all(self, state):
        """切换全选状态"""
        checked = state == 2  # Qt.CheckState.Checked 的值是 2
        
        # 遍历所有卡片，设置选中状态
        for card, session_id in self.card_session_map.items():
            if checked:
                self.selected_sessions.add(session_id)
                # 直接修改卡片的样式
                card.setStyleSheet("""
                    FluentCard {
                        background-color: #e3f2fd;
                        border-radius: 8px;
                        border: 2px solid #2196f3;
                    }
                    FluentCard:hover {
                        background-color: #e3f2fd;
                    }
                    FluentCard:pressed {
                        background-color: #bbdefb;
                    }
                """)
            else:
                if session_id in self.selected_sessions:
                    self.selected_sessions.remove(session_id)
                # 恢复卡片的默认样式
                card.setStyleSheet("""
                    FluentCard {
                        background-color: white;
                        border-radius: 8px;
                        border: 1px solid #e0e0e0;
                    }
                    FluentCard:hover {
                        background-color: #f5f5f5;
                    }
                    FluentCard:pressed {
                        background-color: #e8e8e8;
                    }
                """)
        
        # 更新删除按钮状态
        self.delete_selected_button.setEnabled(len(self.selected_sessions) > 0)

    def resizeEvent(self, event):
        """窗口大小改变时重新加载会话列表"""
        super().resizeEvent(event)
        # 重新加载会话列表，调整列数
        search_text = self.search_input.text().lower()
        filter_option = self.filter_combo.currentText()
        self.load_sessions(search_text, filter_option)
    
    def clean_sessions(self):
        """清理所有会话"""
        reply = QMessageBox.question(
            self, "确认清理", 
            "确定要清理所有会话吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除所有会话
                sessions = self.session_manager.get_all_sessions()
                for session in sessions:
                    self.session_manager.delete_session(session.get('session_id'))
                
                self.load_sessions("", "全部")
                self.current_session = None
                self.update_storage_info()
                QMessageBox.information(self, "清理成功", "所有会话已清理")
            except Exception as e:
                QMessageBox.warning(self, "清理失败", f"清理会话时出错: {e}")
