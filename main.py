import sys
import os
import tempfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, 
    QLabel, QHBoxLayout, QFrame, QFileDialog, QTextEdit,
    QSpacerItem, QSizePolicy, QSystemTrayIcon, QMenu,QTextBrowser,QScrollArea
)
from PySide6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QFont, QIcon, 
    QScreen, QGuiApplication, QMouseEvent, QImage, 
    QAction, QKeySequence, QShortcut,QPainterPath, QRegion
)
from PySide6.QtCore import Qt, QTimer, QRect, Signal, QPoint, QSize, QPropertyAnimation, QEasingCurve, QObject, Signal, QEventLoop
from PIL import Image, ImageDraw, ImageQt

# 尝试导入keyboard模块，如果失败则设置为None
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    keyboard = None
    KEYBOARD_AVAILABLE = False

from message import *
import LLM.llm as agent
import LLM.Image_processing as img
import Interface.main_window as mw
from Interface.fluent_components import *
from session_manager import SessionManager


class GlobalHotkeyManager(QObject):
    """全局热键管理器"""
    screenshot_triggered = Signal()
    cancel_triggered = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_hotkeys()
    
    def setup_hotkeys(self):
        # 只有在keyboard模块可用时才设置热键
        if KEYBOARD_AVAILABLE:
            try:
                # 设置截图热键
                keyboard.add_hotkey('ctrl+alt+a', self.on_screenshot_hotkey)
                # 设置取消热键
                keyboard.add_hotkey('esc', self.on_cancel_hotkey)
            except Exception as e:
                print(f"设置热键失败: {e}")
    
    def on_screenshot_hotkey(self):
        """截图热键回调"""
        # 检查截图功能是否可用
        if check_screenshot_active():
            print("截图热键触发，开始截图")
            # 立即将截图功能状态设置为不可用
            set_screenshot_active(False)
            self.screenshot_triggered.emit()
        else:
            print("截图功能当前不可用，忽略热键操作")
    
    def on_cancel_hotkey(self):
        """取消热键回调"""
        self.cancel_triggered.emit()

class ScreenshotTool:
    def __init__(self):
        self.temp_dir = os.path.join(os.getcwd(), 'TEMP')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # 初始化会话管理器
        self.session_manager = SessionManager(self.temp_dir)
        
        # 使用已经创建的 QApplication 实例
        self.app = QApplication.instance()
        # 设置应用图标
        app_icon = self.create_icon()
        self.app.setWindowIcon(app_icon)
        
        # 设置系统托盘
        self.setup_tray_icon()
        
        # 设置全局热键
        self.setup_global_hotkeys()
        
        # 创建截图覆盖层
        self.screen_overlay = ScreenOverlay()
        self.screen_overlay.screenshotTaken.connect(self.prepare_preview)
        self.screen_overlay.cancelled.connect(self.cancel_screenshot)
        
        # 创建预览窗口
        self.preview_window = PreviewWindow(self.session_manager)
        # 连接会话保存完成信号
        self.preview_window.session_saved.connect(self.refresh_history)
        
        # 初始化截图状态
        self.screenshot_mode = False
        self.current_screenshot = None

        self.mainwindow = mw.MainWindow()
        # 设置窗口图标
        app_icon = self.create_icon()
        self.mainwindow.setWindowIcon(app_icon)
        # 连接历史记录页面的会话选择信号
        self.mainwindow.history_page.session_selected.connect(self.open_session_from_history)
        # 重写关闭事件，使其隐藏而不是退出应用
        self.mainwindow.closeEvent = self.window_close_event
        self.mainwindow.show()



    def setup_global_hotkeys(self):
        """设置全局热键"""
        self.hotkey_manager = GlobalHotkeyManager()
        self.hotkey_manager.screenshot_triggered.connect(self.start_screenshot)
        self.hotkey_manager.cancel_triggered.connect(self.cancel_screenshot)

    def setup_tray_icon(self):
        """使用Qt原生系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("系统托盘不可用")
            return
            
        self.tray_icon = QSystemTrayIcon(self.create_icon())
        self.tray_icon.setToolTip("截图工具")
        
        # 创建右键菜单
        tray_menu = QMenu()
        
        screenshot_action = QAction("截图 (Ctrl+Alt+A)", self.app)
        screenshot_action.triggered.connect(self.start_screenshot)
        tray_menu.addAction(screenshot_action)
        

        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self.app)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
        
        # 显示托盘消息
        self.tray_icon.showMessage(
            "截图工具", 
            "截图工具已启动，使用 Ctrl+Alt+A 截图",
            QSystemTrayIcon.Information, 
            3000
        )

    def on_tray_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.mainwindow.show()

    def create_icon(self):
        """创建应用图标"""
        # 使用LOGO.jpg作为应用图标
        logo_path = os.path.join(os.path.dirname(__file__), 'Interface', 'Icon', 'LOGO.jpg')
        if os.path.exists(logo_path):
            # 加载图片
            pixmap = QPixmap(logo_path)
            # 缩放图片到64x64
            pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            return QIcon(pixmap)
        else:
            # 如果图片不存在，创建默认图标
            # 创建一个64x64的透明图像
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 绘制相机图标
            draw.rectangle([15, 10, 49, 44], outline="#3370ff", width=3)
            draw.ellipse([25, 20, 39, 34], outline="#3370ff", width=3)
            draw.rectangle([40, 15, 45, 20], fill="#3370ff")
            
            # 将PIL图像转换为QImage
            qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGBA8888)
            
            # 创建QPixmap并返回QIcon
            pixmap = QPixmap.fromImage(qimage)
            return QIcon(pixmap)

    def start_screenshot(self):
        """开始截图流程"""
        print("开始截图")
        self.screenshot_mode = True
        # 确保截图界面在最前面
        if hasattr(self, 'screen_overlay') and self.screen_overlay:
            QTimer.singleShot(100, self.screen_overlay.start)



    def prepare_preview(self, pixmap, screenshot_pos):
        """准备并显示预览浮窗"""
        self.screenshot_mode = False
        self.current_screenshot = pixmap.copy()
        
        # 创建新会话
        session_id = self.session_manager.create_session()
        
        # 生成文件名
        import time
        timestamp = int(time.time())
        image_filename = f"screenshot_{timestamp}.jpg"
        session_path = os.path.join(self.session_manager.sessions_dir, session_id)
        self.temp_file_path = os.path.join(session_path, image_filename)
        
        # 确保会话文件夹存在并立即保存图片
        print(f"保存截图到: {self.temp_file_path}")
        os.makedirs(session_path, exist_ok=True)
        pixmap.save(self.temp_file_path, "jpg", quality=100)
        print("截图保存成功")
        
        # 显示预览窗口，传递截图区域坐标和会话ID
        self.preview_window.set_screenshot(pixmap, self.temp_file_path, session_id)
        self.preview_window.show_preview(screenshot_pos)
        # self.preview_window.show_preview(QPoint(2874, 512))



    def cancel_screenshot(self):
        """取消截图"""
        self.screenshot_mode = False
        if hasattr(self, 'screen_overlay') and self.screen_overlay and self.screen_overlay.isVisible():
            self.screen_overlay.close()
        print("截图已取消")
        # 重置截图功能状态为可用
        set_screenshot_active(True)
        print("截图功能已恢复可用状态")

    def quit_app(self):
        """退出应用"""
        # 清理热键
        if hasattr(self, 'hotkey_manager') and KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all()
            except:
                pass
                
        if hasattr(self, 'preview_window') and self.preview_window:
            self.preview_window.hide()
        if hasattr(self, 'screen_overlay') and self.screen_overlay:
            self.screen_overlay.close()
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
        
        # 更新环境变量为false
        update_env_variable("IS_APP_STARTED", "false")
        # 确保截图功能状态为可用
        set_screenshot_active(True)
            
        self.app.quit()

    def run(self):
        """运行应用"""
        sys.exit(self.app.exec())

    def window_close_event(self, event):
        """窗口关闭事件处理 - 隐藏而不是退出"""
        event.ignore()  # 忽略默认的关闭行为
        self.mainwindow.hide()  # 隐藏窗口
        # print("MainWindow已隐藏到系统托盘")
    
    def open_session_from_history(self, session_id, session_data):
        """从历史记录中打开会话"""
        try:
            # 设置截图功能状态为不可用
            set_screenshot_active(False)
            print("历史记录已打开，截图功能暂时不可用")
            
            print(f"选择了会话: {session_id}")
            print(f"会话数据: {session_data}")
            
            # 加载会话数据
            session_path = os.path.join(self.session_manager.sessions_dir, session_id)
            image_path = os.path.join(session_path, session_data.get('image_path', ''))
            print(f"图片路径: {image_path}")
            
            if os.path.exists(image_path):
                print("图片存在，开始加载图片")
                # 加载图片
                pixmap = QPixmap(image_path)
                print(f"图片加载完成，尺寸: {pixmap.width()} × {pixmap.height()}")
                
                # 显示预览窗口
                print("开始设置截图")
                self.preview_window.set_screenshot(pixmap, image_path, session_id)
                print("截图设置完成")
                
                # 获取消息列表，限制只显示最近50条
                all_messages = session_data.get('messages', [])
                print(f"总消息数量: {len(all_messages)}")
                messages_to_show = all_messages[-50:] if len(all_messages) > 50 else all_messages
                print(f"显示消息数量: {len(messages_to_show)}")
                self.preview_window.messages = messages_to_show
                
                # 清空消息布局
                from message import clearLayout
                clearLayout(self.preview_window.message_layout)
                print("消息布局清空完成")
                
                # 先显示预览窗口
                print("开始显示预览窗口")
                self.preview_window.show_preview(QPoint(100, 100))
                self.preview_window.scroll_area.show()
                print("预览窗口显示完成")
                
                # 使用QTimer异步添加消息，避免UI卡住
                print("开始添加消息")
                for i, message in enumerate(messages_to_show):
                    print(f"添加第{i+1}条消息: {message.get('content', '')}")
                    QTimer.singleShot(i * 10, lambda msg=message: self.preview_window.add_message(
                        msg.get('content', ''),
                        None,
                        msg.get('role', 'user') == 'user',
                        False,
                        True  # 标记为历史消息，不触发流式处理
                    ))
                print("消息添加完成")
            else:
                print(f"图片不存在: {image_path}")
        except Exception as e:
            print(f"处理历史记录时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_history(self):
        """刷新历史记录页面"""
        print("刷新历史记录页面")
        if hasattr(self, 'mainwindow') and hasattr(self.mainwindow, 'history_page'):
            self.mainwindow.history_page.load_sessions()
            print("历史记录页面刷新完成")
    


class ScreenOverlay(QWidget):
    # 修改信号，同时传递截图区域坐标
    screenshotTaken = Signal(QPixmap, QPoint)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Popup
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        
        self.start_point = None
        self.end_point = None
        self.setCursor(Qt.CursorShape.CrossCursor)

    def start(self):
        """开始截图流程，支持多显示器"""
        screens = QGuiApplication.screens()
        if not screens:
            self.cancelled.emit()
            return
        combined_geometry = QRect(0, 0, 0, 0)
        # physical_size = QSize(0, 0)
        # 转换为物理坐标
        x=0 #这里专注于X的拼接
        maxmum_height = 0
        for screen in screens:
            dpr = screen.devicePixelRatio()
            if x > 0:
            # 计算当前屏幕与前一个屏幕之间的间隔
                combined_geometry = combined_geometry.united(
                    QRect(
                        x,
                        0,
                        int((screen.geometry().x() - x)/dpr),# 间隔宽度（加入到拼接图的时候需要是逻辑像素）,
                        int(screen.geometry().height())
                    )
                )
                x += int((screen.geometry().x() - x)/dpr)
            
            combined_geometry = combined_geometry.united(
                QRect(
                    x,
                    screen.geometry().y(),
                    int(screen.geometry().width()),
                    int(screen.geometry().height())
                )
            ) 
            x += int(screen.geometry().width())
            maxmum_height = max(maxmum_height, int(screen.geometry().height())) 

        # 创建全屏覆盖层（使用全局坐标系尺寸）
        self.setGeometry(combined_geometry)
        self.show()
        self.raise_()
        self.activateWindow()

        self.screen_group = []
        screen_x = 0

        for i, screen in enumerate(screens):
            screen_dpr = screen.devicePixelRatio()
            screen_pixmap = screen.grabWindow(0)
            screen_geo = screen.geometry()
            if screen_x > 0:
                target_rect = QRect(
                    screen_x,
                    int(screen_geo.y()),
                    int(screen_geo.width()+(screen_geo.x()-screen_x)/screen_dpr),#加上间隙
                    int(maxmum_height)
                )
            else:
                target_rect = QRect(
                    screen_x,
                    int(screen_geo.y()),
                    int(screen_geo.width()),
                    int(maxmum_height)
                )
            self.screen_group.append((screen_pixmap, target_rect))
            screen_x += int(screen_geo.width())
        

    def paintEvent(self, event):

        """绘制截图区域"""
        painter = QPainter(self)
        # 绘制全屏截图
        if len(self.screen_group) == len(QGuiApplication.screens()):
            # print("HI")
            for screen_pixmap, target_rect in self.screen_group:
                # painter.drawPixmap(QRect(target_rect.x(), target_rect.y(), target_rect.width(), target_rect.height()), screen_pixmap)
                painter.drawPixmap(target_rect, screen_pixmap)
            # 绘制全局截图边框
            painter.setPen(QPen(QColor("#ff0000"), 2))  # 红色边框
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
            
        if self.start_point and self.end_point:
            # 计算选择区域
            rect = QRect(self.start_point, self.end_point).normalized()
            # 只在选择区域以外绘制半透明覆盖层
            # 创建完整窗口的区域
            full_rect = self.rect()
            # 创建选择区域的路径
            selection_path = QPainterPath()
            selection_path.addRect(rect)
            # 创建选择区域以外的路径
            painter.setClipRegion(QRegion(full_rect).subtracted(QRegion(rect)))
            # 在选择区域以外绘制半透明覆盖层
            painter.fillRect(full_rect, QColor(0, 0, 0, 120))
            # 重置裁剪区域
            painter.setClipping(False)
            
            
            
            # 绘制边框
            painter.setPen(QPen(QColor("#3370ff"), 2))
            painter.drawRect(rect)
            
            
            
            
            # 绘制尺寸信息
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QPen(Qt.GlobalColor.white))
            info = f"{rect.width()} × {rect.height()}"
            text_rect = painter.fontMetrics().boundingRect(info)
            
            
            

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件 - PySide6兼容"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            print(f"鼠标按下：窗口内坐标={self.start_point}")
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - PySide6兼容"""
        if self.start_point:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件 - PySide6兼容"""
        if event.button() == Qt.MouseButton.LeftButton and self.start_point:
            self.end_point = event.position().toPoint()
            self.captureSelectedArea()


    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.captureSelectedArea()



    def captureSelectedArea(self):
        """捕获选定区域"""
        if self.start_point and self.end_point:
            # 获取用户选择的逻辑区域
            # print(f"self.start_point={self.start_point}, self.end_point={self.end_point}")
            logic_rect = QRect(self.start_point, self.end_point).normalized()
            topleft_x = 0
            topleft_y = 0
            topleft_flag = True
            # 确保区域有效（逻辑坐标）
            if logic_rect.width() > 5 and logic_rect.height() > 5:
                # 创建最终截图的QPixmap（逻辑尺寸）
                final_screenshot = QPixmap(logic_rect.size())
                final_screenshot.fill(Qt.GlobalColor.transparent)
                
                # 创建painter来绘制最终截图
                final_painter = QPainter(final_screenshot)
                # print(f"[调试0] final_screenshot={final_screenshot.size()}")
                # 遍历所有屏幕截图，查找与选择区域相交的部分
                for screen_pixmap, target_rect in self.screen_group:
                    # 计算选择区域与当前屏幕区域的交集
                    intersect_rect = logic_rect.intersected(target_rect)
                    # print(f"[调试1] 交集区域: {intersect_rect}, 屏幕区域: {target_rect}, 逻辑选择区域: {logic_rect}, 屏幕PIX: {screen_pixmap.size()}")
                    if not intersect_rect.isEmpty():
                        # 获取屏幕截图的DPR
                        screen_dpr = screen_pixmap.devicePixelRatio() if hasattr(screen_pixmap, 'devicePixelRatio') else 1

                        scale_factor = screen_pixmap.size().width()/target_rect.width() 
                        # print(f"screen {screen_pixmap.size()}")
                        # print(f"target {target_rect}")
                        # print(f"ratio1 {screen_pixmap.size().width()/target_rect.width() } ratio2 {screen_pixmap.size().height()/target_rect.height() }")
                        # 计算在屏幕截图中的源区域（需要考虑DPR）
                        source_x = int((intersect_rect.x() - target_rect.x()) * scale_factor)
                        source_y = int((intersect_rect.y() - target_rect.y()) * scale_factor)
                        source_width = int(intersect_rect.width()*scale_factor)
                        source_height = int(intersect_rect.height() * scale_factor)
                        
                        # 计算在最终截图中的目标位置
                        target_x = intersect_rect.x() - logic_rect.x()
                        target_y = intersect_rect.y() - logic_rect.y()
                        
                        # 从屏幕截图中复制对应的部分到最终截图
                        screen_source_rect = QRect(source_x, source_y, source_width, source_height)
                        final_target_rect = QRect(target_x, target_y, intersect_rect.width(), intersect_rect.height())
                        
                        # print(f"[调试2] source rect={screen_source_rect} 最终目标区域: {final_target_rect}")
                        # 计算左上角坐标
                        
                        topleft_x += int((intersect_rect.x() - target_rect.x())*scale_factor/screen_dpr) #完整屏幕的物理坐标，加上选中屏幕的逻辑坐标
                        topleft_y = int((intersect_rect.y()- target_rect.y())*scale_factor/screen_dpr)
                        
                        topleft_flag = False
                    

                        # sub_screen_pixmap = screen_pixmap.copy(screen_source_rect)
                        sub_screen_pixmap = screen_pixmap.copy(screen_source_rect)
                        # print(f"[调试] 子截图区域: {sub_screen_pixmap.size()}")
                        # sub_screen_pixmap.setDevicePixelRatio(screen_dpr) #!!!!!有待考虑
                        final_painter.drawPixmap(final_target_rect, sub_screen_pixmap)

                    elif topleft_flag == True:
                        topleft_x += screen_pixmap.size().width()

                final_painter.end()
                
                
                # 发送信号时同时传递截图区域左上角坐标
                # self.screenshotTaken.emit(final_screenshot, logic_rect.topLeft())
                self.screenshotTaken.emit(final_screenshot, QPoint(int(topleft_x),int(topleft_y)))
                # print(f"左上坐标{QPoint(int(topleft_x),int(topleft_y))},逻辑左上坐标{logic_rect.topLeft()}")
            else:
                self.cancelled.emit()
                
            self.close()
            self.start_point = None
            self.end_point = None
    
class PreviewWindow(QWidget):
    # 信号：会话保存完成
    session_saved = Signal()  # 会话保存完成的信号
    
    def __init__(self, session_manager):
        super().__init__()
        self.session_manager = session_manager
        self.session_id = None
        self.messages = []
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: {FluentCorners.LARGE};
                border: 0px solid #e0e0e0;
            }}
            QLabel {{
                color: #333;
                font-size: 16px;
            }}
        """)
        
        # Remove fixed size constraint
        # self.setFixedSize(360, 480)
        self.init_ui()
        
        # 初始位置
        self.target_position = QPoint()
        self.animation = None

    def init_ui(self):
        # 主布局改为垂直布局，使文本输入框在图片预览区域正下方
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 图片预览区域
        left_layout = QVBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet(f"""
            border-radius: {FluentCorners.LARGE};
            border: 2px solid white;
            background: transparent;
        """)
        self.preview_label.setContentsMargins(3, 3, 3, 3)

        left_layout.addWidget(self.preview_label)

        # 在图片预览区域正下方添加文本输入框
        self.input_textbox = FluentTextEdit()
        self.input_textbox.setPlaceholderText("请输入想提问的关于这个图片的信息...")
        self.input_textbox.setMaximumHeight(80)  # 限制高度
       
        # 安装事件过滤器，用于捕获回车键事件
        
        self.input_textbox.installEventFilter(self)
        left_layout.addWidget(self.input_textbox)

        # 添加垂直弹簧
        left_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addLayout(left_layout, Qt.AlignmentFlag.AlignTop)
       
       
        # 右侧：文本框垂直布局（带弹簧）
        right_layout = QVBoxLayout()
        # 设置对话框
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(2)
        
        # 创建滚动区域
        self.scroll_area = FluentScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setFixedSize(400, 425) 
        self.scroll_area.setStyleSheet(f"""
            border-radius: {FluentCorners.LARGE};
            background-color: white;
            border: 1px solid white;
        """)
        # 创建消息容器
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setAlignment(Qt.AlignTop)
        self.message_layout.setSpacing(4)
        self.message_layout.setContentsMargins(8, 8, 8, 8) 
        self.message_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 0px solid white;
                padding: 2px;
            }
        """)
        self.scroll_area.setWidget(self.message_container)
        right_layout.addWidget(self.scroll_area)

        self.scroll_area.hide()


        # 添加垂直弹簧
        right_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.right_layout = right_layout  # 保存引用
        main_layout.addLayout(right_layout, Qt.AlignmentFlag.AlignTop)      
        self.setLayout(main_layout)
        # # 设置窗口尺寸为0
        # self.setFixedSize(0, 0)

    def add_message(self, text, image_based64, is_user, first_round, is_history=False):
        # 创建消息气泡
        bubble = MessageBubble(text, image_based64, is_user, first_round, is_history)
        
        # 创建气泡容器用于对齐
        bubble_container = QWidget()
        bubble_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bubble_layout = QHBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        
        if is_user:
            # 用户消息靠右
            bubble_layout.addStretch()
            # bubble_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            bubble_layout.addWidget(bubble)
        else:
            # 系统消息靠左
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()
            # bubble_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        
        self.message_layout.addWidget(bubble_container)
        if not is_history:
            self.scroll_to_bottom()
        
        # 记录消息到列表
        import datetime
        if not is_history:  # 只记录非历史消息
            if is_user:
                # 用户消息直接添加
                message = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'role': 'user',
                    'content': text
                }
                self.messages.append(message)
            else:
                # 系统消息，等待流式处理完成后添加
                # 连接信号
                bubble.stream_complete.connect(lambda full_response: self.on_stream_complete(full_response))
    
    def on_stream_complete(self, full_response):
        """流式处理完成回调"""
        # 记录系统消息到列表
        import datetime
        message = {
            'timestamp': datetime.datetime.now().isoformat(),
            'role': 'assistant',
            'content': full_response
        }
        self.messages.append(message)
    
    def keyPressEvent(self, event):
        """键盘事件处理：ESC键取消，回车键处理其他功能"""
        if event.key() == Qt.Key.Key_Escape:
            self.close_preview()

    def set_screenshot(self, pixmap, temp_path, session_id):
        """设置截图和临时路径"""
        print("开始设置截图")
        self.screenshot = pixmap
        self.temp_path = temp_path
        self.session_id = session_id
        self.messages = []  # 清空消息列表
        
        # device_ratio = QGuiApplication.primaryScreen().devicePixelRatio()

        # 获取原始图片尺寸
        original_width = pixmap.width()
        original_height = pixmap.height()
        print(f"原始图片尺寸: {original_width} × {original_height}")

        with_reference = 300
        #显示预览
        try:
            if original_width > 0:
                scaled_width = original_width*2 if original_width*2 < with_reference and original_height*2 < with_reference*original_height/original_width else with_reference
                scaled_height = original_height*2 if original_width*2 < with_reference and original_height*2 < with_reference*original_height/original_width else with_reference*original_height/original_width
                print(f"缩放后尺寸: {scaled_width} × {scaled_height}")
            else:
                scaled_width = with_reference
                scaled_height = with_reference
                print("原始宽度为0，使用默认尺寸")
        except Exception as e:
            print(f"计算尺寸时出错: {e}")
            scaled_width = with_reference
            scaled_height = with_reference

        preview = pixmap.scaled(
            int(scaled_width),
            int(scaled_height), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )


        # print(f"原始尺寸: {original_width} × {original_height}")
        # print(f"缩放尺寸: {scaled_width/device_ratio} × {scaled_height/device_ratio}")
        self.preview_label.setFixedSize(int(scaled_width), int(scaled_height))
        self.preview_label.setPixmap(preview)
        self.input_textbox.setMaximumWidth(int(scaled_width))
        self.setMaximumWidth(int(scaled_width)+self.scroll_area.width()+2)
        # 显示操作提示
        # print("操作提示: 按Enter保存，按Q取消")

    def show_preview(self, screenshot_pos=None):
        """显示预览窗口，默认在屏幕右上角，传入坐标则与截图区域左上角对齐"""
        print("开始显示预览窗口")
        try:
            if screenshot_pos:
                # 如果提供了截图位置，使用该位置
                x = screenshot_pos.x()
                y = screenshot_pos.y()
                print(f"使用提供的位置: ({x}, {y})")
            else:
                # 否则使用默认位置（屏幕右上角）
                # 获取屏幕尺寸
                screen = QGuiApplication.primaryScreen().geometry()
                screen_width = screen.width()
                # 计算窗口位置
                x = screen_width - 800  # 固定宽度
                y = 50
                print(f"使用默认位置: ({x}, {y})")
            
            print(f"窗口尺寸: ({self.width()}, {self.height()})")
            
            # 直接移动到目标位置并显示，不使用动画
            print(f"移动窗口到目标位置: ({x}, {y})")
            self.move(x, y)
            print("显示窗口")
            self.show()
            print(f"窗口显示状态: {self.isVisible()}")
            
            # 获取焦点
            self.activateWindow()
            self.setFocus()
            print("预览窗口显示完成")
        except Exception as e:
            print(f"显示预览窗口时出错: {e}")
            import traceback
            traceback.print_exc()
    
    '''
    Acquire information
    '''

    def acquire_picture_information(self, first_round=False):
        """调用ds模块的acquire_information函数"""
        try:
            # # 检查图片文件是否存在，如果不存在则保存图片
            # if not os.path.exists(self.temp_path):
            #     print(f"图片文件不存在，正在保存: {self.temp_path}")
            #     if self.screenshot and not self.screenshot.isNull():
            #         # 确保会话文件夹存在
            #         os.makedirs(os.path.dirname(self.temp_path), exist_ok=True)
            #         # 保存图片
            #         self.screenshot.save(self.temp_path, "jpg", quality=100)
            #         print("图片保存成功")
            #     else:
            #         print("截图对象为空，无法保存图片")
            #         return
            
            image_base64 = img.image_to_base64(self.temp_path)
            messages = self.user_reference_info
            self.add_message(text=messages, image_based64=image_base64, is_user=False, first_round=first_round)
            self.scroll_to_bottom()

        except Exception as e:
            print(f"调用ds.时出错: {e}")

    def close_preview(self):
        """关闭预览窗口"""
        if self.animation and self.animation.state() == QPropertyAnimation.State.Running:
            return
        
        # 保存会话数据
        if self.session_id and self.messages:
            try:
                # 保存图片到会话文件夹
                if self.screenshot and not self.screenshot.isNull():
                    self.screenshot.save(self.temp_path, "jpg", quality=100)
                # 保存会话数据
                self.session_manager.save_session_data(self.session_id, self.temp_path, self.messages)
                # 发射会话保存完成信号
                self.session_saved.emit()
            except Exception as e:
                print(f"保存会话数据失败: {e}")
        else:
            # 如果没有对话，删除会话文件夹
            if self.session_id:
                session_path = os.path.join(self.session_manager.sessions_dir, self.session_id)
                if os.path.exists(session_path):
                    import shutil
                    shutil.rmtree(session_path)
                    print(f"删除未使用的会话文件夹: {session_path}")
        
        # 隐藏文本框，为下次截图做准备
        self.scroll_area.hide()
        clearLayout(self.message_layout)
        
        # 重置截图功能状态为可用
        from main import set_screenshot_active
        set_screenshot_active(True)
        print("截图功能已恢复可用状态")

        self.input_textbox.clear()
        # 创建关闭动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.x(), -self.height()))
        self.animation.setEasingCurve(QEasingCurve.Type.InQuad)
        self.animation.finished.connect(self.hide)
        self.animation.start()
        
    def save_screenshot(self):
        """保存截图到文件"""
        if not self.screenshot or self.screenshot.isNull():
            return
            
        # # 设置默认文件名
        # import time
        # default_filename = f"screenshot_{int(time.time())}.jpg"
        # default_path = os.path.join(os.path.expanduser("~"), "Pictures", default_filename)
        
        # file_path, _ = QFileDialog.getSaveFileName(
        #     self,
        #     "保存截图",
        #     default_path,
        #     "PNG图像 (*.png);;JPEG图像 (*.jpg *.jpeg)"
        # )
        file_path = self.temp_path
        if file_path:
            # 根据文件扩展名选择保存格式
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                self.screenshot.save(file_path, 'JPEG', quality=95)
            else:
                self.screenshot.save(file_path, 'PNG')
            
            # 更新文件信息
            # self.file_info.setText(f"已保存到: {os.path.basename(file_path)}")
            
            # 5秒后关闭预览窗口
            QTimer.singleShot(1000, self.close_preview)

    def mousePressEvent(self, event):
        """鼠标按下事件 - 拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖动窗口"""
        if hasattr(self, 'old_pos'):
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def eventFilter(self, obj, event):
        """事件过滤器，用于处理文本输入框的回车键事件"""
    
        if event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # 读取文本输入框内容
                user_input = self.input_textbox.toPlainText().strip()
                if user_input:
                    # print(f"用户输入的参考信息: {user_input}")
                    # 保存用户输入的参考信息
                    self.user_reference_info = user_input
                    
                    # 清空输入框并移除焦点
                    self.input_textbox.clear()
                    self.input_textbox.clearFocus()
                    # # 同时显示右侧文本框 !!!!!!!!!!!!!!!! 不够精简这里的代码
                    if self.scroll_area.isHidden():
                        self.scroll_area.show()
                        # 更新布局
                        self.right_layout.update()
                        self.layout().update()
                        # 调用信息获取函数
                        self.add_message(text=user_input,image_based64=None,is_user=True, first_round=False)
                        self.scroll_to_bottom() 
                        QTimer.singleShot(100, lambda: self.acquire_picture_information(first_round=True))
                    else:
                        self.add_message(text=user_input,image_based64=None,is_user=True, first_round=False)
                        self.scroll_to_bottom()
                        QTimer.singleShot(100, lambda: self.acquire_picture_information(first_round=False))
                        pass
                else:
                    # print("请输入有效的参考信息")
                    self.close_preview()
                # 阻止默认的换行行为
                return True        
        # 其他事件继续正常处理
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        self.scroll_area.hide()
        event.accept()

    def scroll_to_bottom(self):
        # 延迟滚动到底部，确保消息已经添加
        QTimer.singleShot(50, self._do_scroll)
    
    def _do_scroll(self):
        # 获取滚动区域并滚动到底部
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_bar = scroll_area.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())


  
def get_env_variable(key, default=None):
    """获取环境变量值
    
    Args:
        key: 环境变量键名
        default: 默认值
    
    Returns:
        环境变量值或默认值
    """
    env_file_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith(f'{key}='):
                        value = line.strip().split('=')[1]
                        return value
        except Exception as e:
            print(f"读取环境变量文件时出错: {e}")
    return default

def update_env_variable(key, value):
    """更新环境变量文件
    
    Args:
        key: 环境变量键名
        value: 要设置的环境变量值
    """
    env_file_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    if os.path.exists(env_file_path):
        try:
            # 读取文件内容
            with open(env_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 更新环境变量值
            updated_lines = []
            found = False
            for line in lines:
                if line.startswith(f'{key}='):
                    updated_lines.append(f'{key}={value}\n')
                    found = True
                else:
                    updated_lines.append(line)
            
            # 如果没有找到键，添加新行
            if not found:
                updated_lines.append(f'{key}={value}\n')
            
            # 写回文件
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            print(f"环境变量{key}已设置为{value}")
        except Exception as e:
            print(f"更新环境变量文件时出错: {e}")

def check_app_status():
    """检查应用是否已经启动
    
    Returns:
        bool: 如果应用已经启动返回True，否则返回False
    """
    value = get_env_variable('IS_APP_STARTED')
    return value and value.lower() == 'true'

def check_screenshot_active():
    """检查截图功能是否可用
    
    Returns:
        bool: 如果截图功能可用返回True，否则返回False
    """
    value = get_env_variable('SCREENSHOT_SESSION_ACTIVE', 'true')
    return value.lower() == 'true'

def set_screenshot_active(active):
    """设置截图功能状态
    
    Args:
        active: bool，截图功能是否可用
    """
    value = 'true' if active else 'false'
    update_env_variable('SCREENSHOT_SESSION_ACTIVE', value)

if __name__ == "__main__":
    # 检查应用是否已经启动
    if check_app_status():
        print("应用程序已经启动，请勿重复启动")
        sys.exit(1)
    
    # 创建并运行截图工具
    print("开始启动应用程序")
    app = QApplication(sys.argv)
    print("QApplication创建成功")
    tool = ScreenshotTool()
    print("ScreenshotTool创建成功")
    print("开始运行应用程序")
    # 更新环境变量为true
    update_env_variable("IS_APP_STARTED", "true")
    # 确保截图功能状态为可用
    set_screenshot_active(True)
    tool.run()
    # 程序退出时，确保截图功能状态为可用
    set_screenshot_active(True)
    update_env_variable("IS_APP_STARTED", "false")
