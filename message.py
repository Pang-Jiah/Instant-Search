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
from PySide6.QtCore import Qt, QTimer, QRect, Signal, QPoint, QSize, QPropertyAnimation, QEasingCurve, QObject, QThread

import LLM.llm as agent
import LLM.Image_processing as img
from session_manager import SessionManager

class StreamWorker(QThread):
    """流式处理线程"""
    stream_data = Signal(str)  # 发送流式数据的信号
    stream_finished = Signal(str)  # 发送完整响应的信号
    
    def __init__(self, messages, image_base64, first_round):
        super().__init__()
        self.messages = messages
        self.image_base64 = image_base64
        self.first_round = first_round
    
    def run(self):
        """线程运行函数"""
        full_response = ""
        try:
            # 调用修改后的vision_acquire_information函数，获取生成器
            for chunk in agent.vision_acquire_information(
                messages=self.messages, 
                image_base64=self.image_base64, 
                first_round=self.first_round
            ):
                if chunk is None:
                    # 流式结束
                    break
                full_response += chunk
                self.stream_data.emit(chunk)
        except Exception as e:
            print(f"流式处理异常: {e}")
            self.stream_data.emit("⚠ Your API configuration has encountered an error.")
        finally:
            self.stream_finished.emit(full_response)


def clearLayout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


class MessageBubble(QFrame):
    # 信号：流式处理完成
    stream_complete = Signal(str)  # 发送完整响应的信号
    
    def __init__(self, text, image_base64, is_user=True, first_round=False, is_history=False):
        super().__init__()
        
        self.is_user = is_user
        self.image_base64 = image_base64
        self.text = text
        self.first_round = first_round
        self.is_history = is_history
        self.full_response = ""
        self.setup_ui()



    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.text_edit = QTextBrowser()
        self.text_edit.setReadOnly(True)
        
        # 设置字体
        font = QFont()
        font.setPointSize(11)
        self.text_edit.setFont(font)
        
        # 设置样式 - 去掉边框和滚动条
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setFrameStyle(QFrame.NoFrame)
        
        # 设置文本编辑器的背景透明
        self.text_edit.setStyleSheet("background: transparent;")
        # 设置自动调整大小
        self.text_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # 设置直接在外部浏览器中打开链接
        self.text_edit.setOpenExternalLinks(True)
        
        if self.is_user == True:
            self.text_edit.setText(self.text)
            self.text_edit.setStyleSheet("background: transparent; color: white;")
        else:
            self.text_edit.setStyleSheet("background: transparent; color: black;")
            if self.is_history:
                # 历史消息直接显示文本
                self.text_edit.setText(self.text)
            else:
                # 启动流式处理线程
                self.start_streaming()
        
        
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        
        # 设置样式
        self.setStyle()
        
        # 计算尺寸
        if self.is_history:
            # 历史消息直接计算尺寸
            self.adjust_size()
        else:
            # 流式消息延迟计算尺寸
            QTimer.singleShot(10, self.adjust_size)
    
    def start_streaming(self):
        """启动流式处理"""
        # 创建并启动线程
        self.worker = StreamWorker(
            messages=self.text, 
            image_base64=self.image_base64, 
            first_round=self.first_round
        )
        # 连接信号
        self.worker.stream_data.connect(self.update_text)
        self.worker.stream_finished.connect(self.stream_finished)
        # 启动线程
        self.worker.start()
    
    def update_text(self, chunk):
        """更新文本内容"""
        self.text_edit.insertPlainText(chunk)
        self.full_response += chunk
        # 实时调整大小
        self.adjust_size()
    
    def stream_finished(self, full_response):
        """流式处理完成"""
        # 转换为HTML格式
        self.text_edit.clear()
        self.text_edit.insertHtml(full_response)
        self.text_edit.insertHtml('\n')
        # 最后调整一次大小
        # 延迟调整大小，确保HTML内容完全渲染
        QTimer.singleShot(100, self.adjust_size)
        # 发射信号，通知PreviewWindow流式处理完成
        self.stream_complete.emit(full_response)

    


    def adjust_size(self):
        """根据内容调整大小"""
        doc = self.text_edit.document()

        # 使用字体度量精确计算文本尺寸
        font_metrics = self.text_edit.fontMetrics()
        
        # 计算文本的实际宽度（考虑最大宽度）
        text = self.text_edit.toPlainText()
        max_width = 350  # 增加最大宽度，确保内容有足够空间显示
        min_width = 40
        
        # 边距设置
        horizontal_margin = 24  # 左右边距总和
        vertical_margin = 20     # 上下边距总和
        
        # 按行分割文本，找出最长的一行
        lines = text.split('\n')
        max_line_width = 0
        for line in lines:
            # 计算每行文本的像素宽度
            line_width = font_metrics.horizontalAdvance(line) + horizontal_margin
            max_line_width = max(max_line_width, line_width)
            
        # 限制宽度
        if max_line_width > max_width:
            actual_width = max_width
            # 对于长文本，设置文本宽度并启用自动换行
            doc.setTextWidth(actual_width - horizontal_margin)
        else:
            actual_width = max(min_width, max_line_width)
            # 对于短文本，不设置文本宽度，让文本自然显示
            doc.setTextWidth(-1)  # 自动宽度
        
        doc.adjustSize()
        
        # 计算理想高度
        if max_line_width > max_width:
            # 长文本：基于设置的宽度计算高度
            ideal_height = doc.size().height() + vertical_margin
        else:
            # 短文本：基于实际内容计算高度
            # 考虑行数的影响
            line_height = font_metrics.height()
            ideal_height = line_height * len(lines) + vertical_margin
        
        # 确保最小高度
        ideal_height = max(50, ideal_height)
        
        # 设置气泡的尺寸
        self.setFixedSize(int(actual_width), int(ideal_height))
        
    def setStyle(self):
        if self.is_user:
            # 用户消息样式 - 绿色气泡，靠右
            style = """
            MessageBubble {
                background-color: #34C759;
                border-radius: 8px;
                border-bottom-right-radius: 4px;
                margin: 2px 0px;
            }
            """
        else:
            # 系统消息样式 - 灰色气泡，靠左
            style = """
            MessageBubble {
                background-color: #F2F2F7;
                border-radius: 8px;
                border-bottom-left-radius: 4px;
                margin: 2px 0px;
            }
            """
        
        self.setStyleSheet(style)