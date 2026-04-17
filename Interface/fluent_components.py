"""
Fluent Design 风格组件
"""
from PySide6.QtWidgets import (
    QWidget, QLabel, QFrame, QPushButton, QVBoxLayout, 
    QHBoxLayout, QStackedWidget, QComboBox, QCheckBox,
    QRadioButton, QGroupBox, QLineEdit, QSizePolicy, QScrollArea,QTextEdit
)
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QPalette

from .fluent_style import FluentStyle, FluentFonts, FluentCorners, FluentDurations, FluentSpacing

class FluentButton(QPushButton):
    """Fluent 风格按钮"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置按钮样式"""
        self.setFont(QFont(FluentFonts.FAMILY, 13))
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(32)
        
        style = f"""
            QPushButton {{
                background-color: {FluentStyle.PRIMARY};
                color: white;
                border: none;
                border-radius: {FluentCorners.MEDIUM};
                padding: 6px 10px;
                font-family: {FluentFonts.FAMILY};
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {FluentStyle.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: #005A9E;
            }}
            QPushButton:disabled {{
                background-color: {FluentStyle.SURFACE_HOVER};
                color: {FluentStyle.TEXT_DISABLED};
            }}
        """
        self.setStyleSheet(style)


class FluentComboBox(QComboBox):
    """Fluent 风格下拉框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
        
    def setup_style(self):
        """设置下拉框样式"""
        self.setFont(QFont(FluentFonts.FAMILY, 13))
        self.setMinimumHeight(32)
        
        style = f"""
            QComboBox {{
                background-color: {FluentStyle.SURFACE};
                border: 1px solid {FluentStyle.BORDER};
                border-radius: {FluentCorners.MEDIUM};
                padding: 4px 10px;
                font-family: {FluentFonts.FAMILY};
                font-size: 13px;
                min-height: 32px;
            }}
            QComboBox:hover {{
                border-color: {FluentStyle.TEXT_SECONDARY};
            }}
            QComboBox:focus {{
                border: 2px solid {FluentStyle.BORDER_FOCUS};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {FluentStyle.ICON_PRIMARY};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {FluentStyle.SURFACE};
                border: 1px solid {FluentStyle.BORDER};
                border-radius: {FluentCorners.MEDIUM};
                selection-background-color: {FluentStyle.SURFACE_HOVER};
            }}
        """
        self.setStyleSheet(style)


class FluentCheckBox(QCheckBox):
    """Fluent 风格复选框"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置复选框样式"""
        self.setFont(QFont(FluentFonts.FAMILY, 13))
        
        style = f"""
            QCheckBox {{
                spacing: 8px;
                font-family: {FluentFonts.FAMILY};
                font-size: 13px;
                color: {FluentStyle.TEXT_PRIMARY};
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 1px solid {FluentStyle.BORDER};
                border-radius: {FluentCorners.SMALL};
                background-color: {FluentStyle.SURFACE};
            }}
            QCheckBox::indicator:hover {{
                border-color: {FluentStyle.TEXT_SECONDARY};
            }}
            QCheckBox::indicator:checked {{
                background-color: {FluentStyle.PRIMARY};
                border-color: {FluentStyle.PRIMARY};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMzMgNEw2IDExLjMzMzNMMi42NjY2NyA4IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }}
            QCheckBox::indicator:disabled {{
                background-color: {FluentStyle.SURFACE_HOVER};
                border-color: {FluentStyle.BORDER};
            }}
        """
        self.setStyleSheet(style)


class FluentRadioButton(QRadioButton):
    """Fluent 风格单选按钮"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置单选按钮样式"""
        self.setFont(QFont(FluentFonts.FAMILY, 13))
        
        style = f"""
            QRadioButton {{
                spacing: 8px;
                font-family: {FluentFonts.FAMILY};
                font-size: 13px;
                color: {FluentStyle.TEXT_PRIMARY};
            }}
            QRadioButton::indicator {{
                width: 20px;
                height: 20px;
                border: 1px solid {FluentStyle.BORDER};
                border-radius: {FluentCorners.CIRCLE};
                background-color: {FluentStyle.SURFACE};
            }}
            QRadioButton::indicator:hover {{
                border-color: {FluentStyle.TEXT_SECONDARY};
            }}
            QRadioButton::indicator:checked {{
                border: 6px solid {FluentStyle.PRIMARY};
            }}
            QRadioButton::indicator:disabled {{
                background-color: {FluentStyle.SURFACE_HOVER};
                border-color: {FluentStyle.BORDER};
            }}
        """
        self.setStyleSheet(style)


class FluentCard(QFrame):
    """Fluent 风格卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
        
    def setup_style(self):
        """设置卡片样式"""
        self.setFrameShape(QFrame.StyledPanel)
        
        style = f"""
            QFrame {{
                background-color: {FluentStyle.SURFACE};
                border: 0px solid {FluentStyle.BORDER};
                border-radius: {FluentCorners.LARGE};
                padding: 6px;
            }}
        """
        self.setStyleSheet(style)


class FluentTitleLabel(QLabel):
    """Fluent 风格标题标签"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置标题样式"""
        font = QFont(FluentFonts.FAMILY, 28)
        font.setWeight(QFont.Weight.Bold)  # 修复这里，使用 QFont.Weight.Bold
        self.setFont(font)
        self.setStyleSheet(f"color: {FluentStyle.TEXT_PRIMARY};")


class FluentSubtitleLabel(QLabel):
    """Fluent 风格副标题标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置副标题样式"""
        font = QFont(FluentFonts.FAMILY, 13)
        self.setFont(font)
        self.setStyleSheet(f"color: {FluentStyle.TEXT_SECONDARY};")


class FluentBodyLabel(QLabel):
    """Fluent 风格正文标签"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置正文样式"""
        font = QFont(FluentFonts.FAMILY, 13)
        self.setFont(font)
        self.setStyleSheet(f"color: {FluentStyle.TEXT_PRIMARY};")


class FluentDivider(QFrame):
    """Fluent 风格分隔线"""
    
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(parent)
        if orientation == Qt.Horizontal:
            self.setFrameShape(QFrame.HLine)
        else:
            self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {FluentStyle.BORDER};
            }}
        """)


class FluentIconButton(QPushButton):
    """Fluent 风格图标按钮"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(48, 48)  # 改为 setMinimumSize 而不是 setFixedSize
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
    def setup_style(self, is_active=False):
        """设置图标按钮样式"""
        if is_active:
            style = f"""
                QPushButton {{
                    background-color: {FluentStyle.SURFACE_HOVER};
                    border: none;
                    border-radius: {FluentCorners.MEDIUM};
                }}
                QPushButton:hover {{
                    background-color: {FluentStyle.SURFACE_PRESSED};
                }}
            """
        else:
            style = f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: {FluentCorners.MEDIUM};
                }}
                QPushButton:hover {{
                    background-color: {FluentStyle.SURFACE_HOVER};
                }}
            """
        self.setStyleSheet(style)

class FluentScrollArea(QScrollArea):
    """Fluent 风格滚动区域，鼠标触碰时显示滚动条"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
        # 安装事件过滤器以监听鼠标进入和离开事件
        self.installEventFilter(self)
        
    def setup_style(self):
        """设置滚动区域样式"""
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        
        # 设置滚动区域整体样式
        self.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
        """)
        
        # 初始化时设置滚动条为几乎透明
        self._update_scrollbar_style(transparent=True)
    
    def _update_scrollbar_style(self, transparent=False):
        """更新滚动条样式"""
        # 根据是否透明选择不同的背景颜色
        handle_color = "rgba(0, 0, 0, 0.1)" if transparent else FluentStyle.SCROLLBAR_HANDLE
        
        scrollbar_style = f"""
            /* 垂直滚动条 */
            QScrollBar:vertical {{
                background-color: transparent;
                width: {FluentStyle.SCROLLBAR_WIDTH}px;
                margin: {FluentStyle.SCROLLBAR_MARGIN}px;
                border: none; /* 无边框 */
                border-radius: {FluentStyle.SCROLLBAR_RADIUS}px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {handle_color};
                min-height: 30px;
                border-radius: {FluentStyle.SCROLLBAR_RADIUS}px;
                margin: 2px;
                border: none;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {FluentStyle.SCROLLBAR_HANDLE_HOVER};
            }}
            
            QScrollBar::handle:vertical:pressed {{
                background-color: {FluentStyle.SCROLLBAR_HANDLE_PRESSED};
            }}
            
            QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }}
            
            QScrollBar::add-line:vertical {{
                border: none;
                background: none;
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             /* 水平滚动条（虽然我们禁用了，但保持样式完整） */
            QScrollBar:horizontal {{
                background-color: transparent;
                height: {FluentStyle.SCROLLBAR_WIDTH}px;
                margin: {FluentStyle.SCROLLBAR_MARGIN}px;
                border-radius: {FluentCorners.SMALL};
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {FluentStyle.SCROLLBAR_HANDLE};
                min-width: 30px;
                border-radius: {FluentStyle.SCROLLBAR_RADIUS}px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {FluentStyle.SCROLLBAR_HANDLE_HOVER};
            }}
            
            QScrollBar::handle:horizontal:pressed {{
                background-color: {FluentStyle.SCROLLBAR_HANDLE_PRESSED};
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background-color: {FluentStyle.SCROLLBAR_BG};
                border-radius: {FluentStyle.SCROLLBAR_RADIUS + 2}px;
            }}
            
            QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
                height: 0px;
            }}
            
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
                border: none;
                background: none;
            }}
        """
        
        vertical_scrollbar = self.verticalScrollBar()
        if vertical_scrollbar:
            vertical_scrollbar.setStyleSheet(scrollbar_style)
    
    def eventFilter(self, obj, event):
        """事件过滤器，监听鼠标进入和离开事件"""
        if obj == self:
            if event.type() == QEvent.Enter:
                # 鼠标进入时，使滚动条完全可见
                self._update_scrollbar_style(transparent=False)
            elif event.type() == QEvent.Leave:
                # 鼠标离开时，使滚动条几乎透明但保持功能
                self._update_scrollbar_style(transparent=True)
        return super().eventFilter(obj, event)

class FluentTextEdit(QTextEdit):
    """Fluent 输入标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置正文样式"""
        font = QFont(FluentFonts.FAMILY, 13)
        self.setFont(font)
        self.setStyleSheet(f"""
            QTextEdit {{
                border: 2 solid #ccc;
                border-radius: {FluentCorners.MEDIUM};
                padding: 5px;
                font-size: 12px;
                background-color: white;
            }}


            QTextEdit:focus {{
                border: 1px solid #3370ff;
            }}

            QScrollBar:vertical {{
                background-color: rgba(240, 240, 240, 180);
                width: 10px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: rgba(100, 100, 100, 150);
                border-radius: 5px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: rgba(80, 80, 80, 200);
            }}
            
            QScrollBar:horizontal {{
                background-color: rgba(240, 240, 240, 180);
                height: 10px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: rgba(100, 100, 100, 150);
                border-radius: 5px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: rgba(80, 80, 80, 200);
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                height: 0px;
                width: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)

class FluentLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {FluentStyle.SURFACE};
                border: 1px solid {FluentStyle.BORDER};
                border-radius: {FluentCorners.MEDIUM};
                padding: {FluentSpacing.MEDIUM};
                font-size: {FluentFonts.BODY};
                color: {FluentStyle.TEXT_PRIMARY};
                font-family: {FluentFonts.FAMILY};
            }}
            QLineEdit:focus {{
                border: 2px solid {FluentStyle.BORDER_FOCUS};
            }}
        """)