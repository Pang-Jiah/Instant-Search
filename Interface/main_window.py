"""
主窗口实现
"""
import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QSpacerItem,
    QHBoxLayout, QStackedWidget, QSizePolicy, QLabel,QPushButton,QScrollArea,QLineEdit,
    QComboBox, QFrame, QListWidget, QListWidgetItem, QTextBrowser, QFileDialog, QMessageBox, QInputDialog, QGridLayout
)
# QSwitch已移除，将使用自定义按钮实现开关功能
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QFont, QPalette, QColor, QPixmap

from .fluent_style import FluentStyle, FluentFonts, FluentCorners
# 在文件顶部添加导入
from .fluent_components import *
path_of_this_file = os.path.split(__file__)[0]
sys.path.append(path_of_this_file)

# 导入会话管理器
from session_manager import SessionManager 
# 导入历史记录页面
from .history_page import HistoryPage

class NavigationBar(QWidget):
    """左侧导航栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()
        self.setup_style()
        
    def setup_ui(self):
        """设置导航栏界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)  # 添加上下边距
        layout.setSpacing(8)
        
        # 顶部图标区域
        top_layout = QVBoxLayout()
        top_layout.setSpacing(8)
        
        # 添加LOGO图片
        logo_path = os.path.join(os.path.dirname(__file__), 'Icon', 'LOGO.jpg')
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            # 缩放LOGO到合适大小
            logo_pixmap = logo_pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            top_layout.addWidget(logo_label)
        
        # 添加自定义设置图标按钮
        self.settings_btn = FluentIconButton()
        self.settings_btn.setText("⚙️")
        self.settings_btn.setToolTip("自定义参数配置")
        self.settings_btn.clicked.connect(lambda: self.parent_window.switch_page(0))
        self.settings_btn.setup_style(False)
        
        # 添加历史记录图标按钮
        self.history_btn = FluentIconButton()
        self.history_btn.setText("📋")
        self.history_btn.setToolTip("查看历史记录")
        self.history_btn.clicked.connect(lambda: self.parent_window.switch_page(1))
        self.history_btn.setup_style(False)

        top_layout.addWidget(self.settings_btn)
        top_layout.addWidget(self.history_btn)

        top_layout.addStretch()
        
        # 底部图标区域
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(8)
        
        # GitHub图标按钮
        self.github_btn = FluentIconButton()
        self.github_btn.setText("🐙")
        self.github_btn.setToolTip("GitHub repo")
        
        # 反馈图标按钮
        self.feedback_btn = FluentIconButton()
        self.feedback_btn.setText("💬")
        self.feedback_btn.setToolTip("Send feedback")
        
        bottom_layout.addWidget(self.github_btn)
        bottom_layout.addWidget(self.feedback_btn)
        
        # 修改布局结构：去掉中间的 addStretch，让顶部和底部自然分布
        layout.addLayout(top_layout)
        layout.addStretch()  # 中间添加弹性空间
        layout.addLayout(bottom_layout)
        
    def setup_style(self):
        """设置导航栏样式"""
        self.setFixedWidth(68)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 添加高度扩展策略
        self.setStyleSheet(
            '''QWidget {
                background-color: ''' + FluentStyle.SURFACE + ''';
                border-right: 1px solid ''' + FluentStyle.BORDER + ''';
            }'''
        )
    
    def set_active_button(self, index):
        """设置活动按钮"""
        self.settings_btn.setup_style(index == 0)
        self.history_btn.setup_style(index == 1)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config_file_path = config_file
        self.config = self.load_config()
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "llm_url": "",
            "llm_model": "",
            "api_key": "",
        }

        current_file = os.path.abspath(__file__)
        # 获取file1.py所在的目录
        current_dir = os.path.dirname(current_file)
        # 获取项目根目录（folder1的父目录）
        project_root = os.path.dirname(current_dir)
        # 构建file2.json的完整路径
        json_path = os.path.join(project_root, 'config', self.config_file)
            
        self.config_file_path = json_path
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和已保存的配置
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
            else:
                print("未找到json file")
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        
        return default_config
    
    def save_config(self, config_data):
        """保存配置文件"""
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value





class SettingPage(QWidget):
    """自定义设置页面"""
    def __init__(self, parent=None):
        super().__init__()
        self.config_manager = ConfigManager()
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """设置导航栏界面"""
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
        title = FluentTitleLabel("Parameter Configuration (参数配置)")
        scroll_layout.addWidget(title)

         # 描述
        desc = FluentSubtitleLabel("Configure the parameters for the application. (配置应用程序的各种参数和设置选项。)")
        scroll_layout.addWidget(desc)

        # 分隔线
        divider = FluentDivider()
        scroll_layout.addWidget(divider)


        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(12)
        
        
        
        '''
        API
        '''
        """读取folder2/file2.json文件"""
        # 获取当前文件(file1.py)的绝对路径
        current_file = os.path.abspath(__file__)
        # 获取file1.py所在的目录(folder1)
        current_dir = os.path.dirname(current_file)
        # 构建file2.json的完整路径
        icon_path = os.path.join(current_dir, 'Icon', 'API_KEY.jpg')
        # 创建带下拉功能的设置组
        cubo_result = self.create_settings_group(
            "下拉菜单",
            "点击右侧按钮可以展开下拉菜单，配置你的模型。",
            icon=icon_path,
            enable_dropdown=True
        )
        
        # 解包返回的卡片和下拉框
        api_dropdown_container, api_cubo_group, dropdown_frame = cubo_result
        
        # 为下拉框创建布局
        dropdown_layout = QVBoxLayout(dropdown_frame)
        dropdown_layout.setSpacing(8)
        

        # 子栏1：URL
        model_url_layout = QVBoxLayout()
        self.url_input = FluentLineEdit()
        self.url_input.setPlaceholderText("请输入模型的URL")
        model_url_layout.addWidget(self.url_input)
        model_url_group = self.create_settings_group(
            "Model URL",
            "配置应用程序使用的模型URL。",
            right_layout=model_url_layout,
            sub_group=True
        )
        
        # 子栏2：model name
        model_name_layout = QVBoxLayout()
        self.model_name = FluentLineEdit()
        self.model_name.setPlaceholderText("请输入模型的名称")
        model_name_layout.addWidget(self.model_name)
        model_name_group = self.create_settings_group(
            "Model Name",
            "配置应用程序使用的模型名称。",
            right_layout=model_name_layout,
            sub_group=True
        )
        
        # 子栏3：小组件设置
        api_key_input_layout = QHBoxLayout()
    
        self.api_key_input = FluentLineEdit()
        self.api_key_input.setPlaceholderText("请输入您的API密钥")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        # 可见性切换按钮
        self.toggle_visibility_btn = QPushButton("👁️")
        self.toggle_visibility_btn.setFixedSize(30, 30)
        self.toggle_visibility_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_visibility_btn.setStyleSheet(
            '''QPushButton {
                background-color: ''' + FluentStyle.SURFACE + ''';
                border: 0px solid ''' + FluentStyle.BORDER + ''';
                border-radius: ''' + FluentCorners.MEDIUM + ''';
                font-size: 13px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: ''' + FluentStyle.SURFACE_HOVER + ''';
            }
            QPushButton:pressed {
                background-color: ''' + FluentStyle.SURFACE_PRESSED + ''';
            }'''
        )
        self.toggle_visibility_btn.clicked.connect(self.toggle_api_key_visibility)


        api_key_input_layout.addWidget(self.api_key_input)
        api_key_input_layout.addWidget(self.toggle_visibility_btn)
        api_key_group = self.create_settings_group(
            "API Key",
            "配置应用程序使用的API密钥。",
            right_layout=api_key_input_layout,
            sub_group=True
        )
        
        # 将所有子栏添加到下拉布局
        dropdown_layout.addWidget(model_url_group)
        dropdown_layout.addWidget(model_name_group)
        dropdown_layout.addWidget(api_key_group)


        # 初始隐藏下拉框
        dropdown_frame.hide()
        
    
        # 将容器添加到主设置布局
        settings_layout.addWidget(api_dropdown_container)

        '''
        ###
        操作按钮
        ###
        '''
        buttons_layout = QHBoxLayout()
        self.save_btn = FluentButton("保存设置")
        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet(
            '''QPushButton {
                background-color: transparent;
                color: ''' + FluentStyle.TEXT_SECONDARY + ''';
                border: 1px solid ''' + FluentStyle.BORDER + ''';
                border-radius: ''' + FluentCorners.MEDIUM + ''';
                padding: 6px 10px;
                font-family: ''' + FluentFonts.FAMILY + ''';
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: ''' + FluentStyle.SURFACE_HOVER + ''';
            }'''
        )
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addStretch()
        settings_layout.addLayout(buttons_layout)



        settings_layout.addStretch()
        scroll_layout.addLayout(settings_layout)

        # 设置滚动内容的最小高度
        scroll_content.setMinimumHeight(800)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        # 设置页面尺寸策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        
        # 连接信号和槽
        self.connect_signals()

    def toggle_api_key_visibility(self):
        """切换API密钥的可见性"""
        if self.api_key_input.echoMode() == QLineEdit.Password:
            # 当前是密码模式，切换到可见模式
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.toggle_visibility_btn.setText("🙈")
        else:
            # 当前是可见模式，切换到密码模式
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.toggle_visibility_btn.setText("👁️")
    
    def toggle_dropdown(self, group_id):
        """切换下拉菜单的显示/隐藏状态"""
        # 确保字典存在
        if not hasattr(self, 'dropdown_buttons'):
            self.dropdown_buttons = {}
        if not hasattr(self, 'dropdown_frames'):
            self.dropdown_frames = {}
            
        # 检查按钮和框架是否在字典中
        if group_id in self.dropdown_buttons and group_id in self.dropdown_frames:
            dropdown_btn = self.dropdown_buttons[group_id]
            dropdown_frame = self.dropdown_frames[group_id]
            
            # 切换显示/隐藏状态
            is_visible = dropdown_frame.isVisible()
            dropdown_frame.setVisible(not is_visible)
            
            # 更新按钮文本（箭头方向）
            dropdown_btn.setText("▲" if not is_visible else "▼")
    
    def create_settings_group(self, title, description, icon=None, right_layout=None, enable_dropdown=False, sub_group=False):
            """创建设置分组，支持左侧图标、中间标题和描述、右侧可配置模块或下拉按钮"""
            group_card = FluentCard()
            group_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # 主水平布局
            main_layout = QHBoxLayout(group_card)
            main_layout.setContentsMargins(8, 8, 8, 8)
            main_layout.setSpacing(5)
            
            # 1. 左侧图标区域
            icon_layout = QVBoxLayout()
            icon_layout.setAlignment(Qt.AlignCenter)  # 设置为居中对齐
            # 图标标签
            icon_label = QLabel()
            if icon:
                if isinstance(icon, str):
                    # 假设是图标路径
                    icon_label.setPixmap(QIcon(icon).pixmap(24, 24))
                elif hasattr(icon, 'pixmap'):
                    # 如果是QPixmap或QIcon
                    icon_label.setPixmap(icon)
            else:
                # 默认占位符
                icon_label.setFixedSize(24, 24)
            
            icon_layout.addWidget(icon_label)
            main_layout.addLayout(icon_layout)
            
            # 2. 中间标题和描述区域
            content_layout = QVBoxLayout()
            content_layout.setSpacing(0)
            
            # 分组标题
            title_label = FluentBodyLabel(title)

            title_label.setStyleSheet(
                '''QLabel {
                    font-weight: 600;
                    font-size: 18px;
                    padding: 2px;  /* 将内边距设为0，最小化文字与边框距离 */
                                    /* 或者更精细地控制：padding: 1px 2px 1px 2px; */
                }'''
            )
            content_layout.addWidget(title_label)
            
            # 分组描述
            desc_label = FluentBodyLabel(description)
            desc_label.setStyleSheet(
                '''QLabel {
                    font-weight: 100;
                    font-size: 13px;
                    color: rgba(0, 0, 0, 0.7); /* 70%透明度的黑色文本 */
                    padding: 2px;  
                }'''
            )

            content_layout.addWidget(desc_label)
            
            # 内容区域占据剩余空间
            # content_layout.addStretch()
            main_layout.addLayout(content_layout, 1)  # 1表示伸展因子
            
            # 3. 右侧区域
            if right_layout:
                main_layout.addLayout(right_layout, 2)


            elif enable_dropdown:
                # 创建下拉按钮
                self.dropdown_buttons = getattr(self, 'dropdown_buttons', {})
                self.dropdown_frames = getattr(self, 'dropdown_frames', {})
                
                # 为每个下拉组创建唯一标识符
                group_id = f"dropdown_{len(self.dropdown_buttons)}"
                
                # 下拉按钮
                dropdown_btn = FluentButton("▼")
                dropdown_btn.setFixedSize(30, 30)
                dropdown_btn.setCursor(Qt.PointingHandCursor)
               
                # 保存按钮引用
                self.dropdown_buttons[group_id] = dropdown_btn
                
                # 将按钮添加到布局
                main_layout.addWidget(dropdown_btn)
                
                # 创建下拉frame，初始隐藏
                dropdown_frame = QFrame()
                dropdown_frame.setStyleSheet(
                    '''QFrame {
                        background-color: ''' + FluentStyle.SURFACE + ''';
                        border: 2px solid ''' + FluentStyle.BORDER + ''';
                        border-radius: ''' + FluentCorners.MEDIUM + ''';
                        padding: 0px;
                    }'''
                )
                
                # 保存frame引用
                self.dropdown_frames[group_id] = dropdown_frame
                
                # 为按钮连接点击事件
                dropdown_btn.clicked.connect(lambda _, gid=group_id: self.toggle_dropdown(gid))
                

                # 创建一个专用的垂直布局容器来精确控制卡片和下拉框之间的间距
                dropdown_container_layout = QVBoxLayout()
                dropdown_container_layout.setSpacing(0)  # 容器内默认无边距
                
                # 添加卡片到容器布局
                dropdown_container_layout.addWidget(group_card)
                
                # 在容器内精确控制卡片和下拉框之间的间距
                dropdown_container_layout.addSpacing(0)  # 这个值仅控制卡片和下拉框之间的间距
            
                # 添加下拉框到容器布局
                dropdown_container_layout.addWidget(dropdown_frame)
                
                # 创建一个QWidget作为容器，设置布局
                dropdown_container = QWidget()
                dropdown_container.setLayout(dropdown_container_layout)
        


                # 返回一个包含卡片和下拉框的元组
                return (dropdown_container,group_card, dropdown_frame)
            

            if sub_group:
                group_card.setStyleSheet(
                    '''QFrame {
                        background-color: ''' + FluentStyle.SURFACE + ''';
                        border: 0px solid ''' + FluentStyle.BORDER + ''';
                        border-radius: ''' + FluentCorners.LARGE + ''';
                        padding: 6px;
                    }'''
                )
                title_label.setStyleSheet(
                    '''QLabel {
                        font-weight: 300;
                        font-size: 16px;
                        padding: 2px;  /* 将内边距设为0，最小化文字与边框距离 */
                                        /* 或者更精细地控制：padding: 1px 2px 1px 2px; */
                    }'''
                )
                desc_label.setStyleSheet(
                    '''QLabel {
                        font-weight: 100;
                        font-size: 10px;
                        color: rgba(0, 0, 0, 0.7); /* 70%透明度的黑色文本 */
                        padding: 2px;  
                    }'''
                )
            return group_card

    def load_settings(self):
        """加载设置"""
        # 加载API密钥
        self.config_manager.load_config()
        llm_url = self.config_manager.get("llm_url", "")
        self.url_input.setText(llm_url)
        llm_model = self.config_manager.get("llm_model", "")
        self.model_name.setText(llm_model)

        api_key = self.config_manager.get("api_key", "")
        self.api_key_input.setText(api_key)
        
        

    def save_settings(self):
        """保存设置"""
        # 收集所有设置数据
        config_data = {
            "llm_url": self.url_input.text(),
            "llm_model": self.model_name.text(),
            "api_key": self.api_key_input.text(),
        }
        # 保存到配置文件
        if self.config_manager.save_config(config_data):
            print("设置保存成功！")
        else:
            print("设置保存失败！")
    
    def reset_settings(self):
        """恢复默认设置"""
        self.api_key_input.clear()
        self.keywords_list = []
        self.update_keywords_display()
        print("已恢复默认设置")

    def connect_signals(self):
        """signal and slot"""
        # 连接保存按钮点击事件
        self.save_btn.clicked.connect(self.save_settings)
        # 连接恢复默认按钮点击事件
        self.reset_btn.clicked.connect(self.reset_settings)



class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_style()
        
    def setup_ui(self):
        """设置主窗口界面"""
        # 设置窗口属性
        self.setWindowTitle("Fluent Gallery")
        self.resize(1000, 700)
        
        # 设置窗口最小尺寸
        self.setMinimumSize(600, 400)  # 调整为更小的最小尺寸
        
        # 创建中央部件
        central_widget = QWidget()
        central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航栏
        self.nav_bar = NavigationBar(self)
        main_layout.addWidget(self.nav_bar)
        
        # 右侧内容区域
        self.content_area = QStackedWidget()
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.content_area)
        
        # 添加页面
        self.settings_page = SettingPage()
        self.history_page = HistoryPage()

        # 连接会话选择信号
        self.history_page.session_selected.connect(self.on_session_selected)

        self.content_area.addWidget(self.settings_page)
        self.content_area.addWidget(self.history_page)
        
        # 设置初始页面
        self.switch_page(0)
        
    def setup_style(self):
        """设置窗口样式"""
        # 设置应用全局字体
        font = QFont(FluentFonts.FAMILY, 10)
        QApplication.setFont(font)
        
        # 设置窗口背景色
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(FluentStyle.BACKGROUND))
        self.setPalette(palette)
        
    def switch_page(self, index):
        """切换页面"""
        self.content_area.setCurrentIndex(index)
        self.nav_bar.set_active_button(index)
        # 如果切换到历史记录页面，刷新会话列表
        if index == 1:
            self.history_page.refresh_sessions()
    
    def on_session_selected(self, session_id, session_data):
        """处理会话选择事件"""
        # 加载会话数据
        session_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'TEMP', 'sessions', session_id)
        image_path = os.path.join(session_path, session_data.get('image_path', ''))
        
        if os.path.exists(image_path):
            # 加载图片
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(image_path)
            
            # 显示预览窗口
            # 这里需要调用 main.py 中的 PreviewWindow 来展示会话
            # 由于 PreviewWindow 是在 main.py 中定义的，这里我们需要通过信号来通知主应用
            print(f"选择了会话: {session_id}")
            print(f"会话数据: {session_data}")
            print(f"图片路径: {image_path}")




def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建并显示窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
