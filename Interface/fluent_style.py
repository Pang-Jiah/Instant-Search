"""
Fluent Design 样式定义
"""

class FluentStyle:
    # 主题色
    PRIMARY = "#0078D4"
    PRIMARY_DARK = "#106EBE"
    
    # 中性色
    BACKGROUND = "#FAF9F8"
    SURFACE = "#FFFFFF"
    SURFACE_HOVER = "#F3F2F1"
    SURFACE_PRESSED = "#EDEBE9"
    
    # 边框
    BORDER = "#EDEBE9"
    BORDER_FOCUS = "#0078D4"
    
    # 文本
    TEXT_PRIMARY = "#201F1E"
    TEXT_SECONDARY = "#605E5C"
    TEXT_DISABLED = "#A19F9D"
    
    # 状态色
    SUCCESS = "#107C10"
    WARNING = "#D83B01"
    ERROR = "#A4262C"
    
    # 图标
    ICON_PRIMARY = "#605E5C"
    ICON_SECONDARY = "#A19F9D"
    ICON_HOVER = "#201F1E"
    ICON_ACTIVE = "#0078D4"
    
    # 滚动条 - 使用 Fluent Design 的亚克力效果
    SCROLLBAR_BG = "#F3F2F180"  # 半透明背景
    SCROLLBAR_HANDLE = "#C8C6C4"
    SCROLLBAR_HANDLE_HOVER = "#8A8886"
    SCROLLBAR_HANDLE_PRESSED = "#605E5C"
    SCROLLBAR_WIDTH = 10
    SCROLLBAR_RADIUS = 2
    SCROLLBAR_MARGIN = 0

# 字体定义
class FluentFonts:
    FAMILY = "Arial, Helvetica, 'Microsoft YaHei', 'Source Han Sans', sans-serif"
    
    # 字体大小
    TITLE = "28px"
    HEADLINE = "20px"
    SUBTITLE = "18px"
    BODY_LARGE = "14px"
    BODY = "13px"
    CAPTION = "12px"
    
    # 字重
    LIGHT = 300
    REGULAR = 400
    SEMIBOLD = 600
    BOLD = 700

# 间距定义
class FluentSpacing:
    SMALL = "4px"
    MEDIUM = "8px"
    LARGE = "12px"
    XLARGE = "16px"
    XXLARGE = "20px"
    XXXLARGE = "24px"

# 圆角定义
class FluentCorners:
    SMALL = "2px"
    MEDIUM = "4px"
    LARGE = "6px"
    X_LARGE = "8px"
    CIRCLE = "50%"

# 动画时间
class FluentDurations:
    FAST = "100ms"
    NORMAL = "167ms"
    SLOW = "267ms"