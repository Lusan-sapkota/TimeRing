#!/usr/bin/env python3
"""
Custom Checkbox Widget for TimeRing
Provides a glass-style checkbox with proper tick marks using Unicode symbols
"""

from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFont, QColor, QPen, QBrush, QLinearGradient

class GlassCheckBox(QCheckBox):
    """Custom checkbox with glass styling and Unicode tick marks"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QCheckBox {
                font-weight: 500;
                spacing: 8px;
                color: #1D1D1F;
            }
            
            QCheckBox[darkTheme="true"] {
                color: #F5F5F7;
            }
            
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 8px;
            }
        """)
    
    def paintEvent(self, event):
        """Custom paint event to draw glass checkbox with Unicode tick"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get checkbox rect
        option = self.styleOption()
        rect = self.style().subElementRect(self.style().SE_CheckBoxIndicator, option, self)
        
        # Determine if dark theme
        is_dark = self.property("darkTheme") == True
        
        # Draw background
        if is_dark:
            bg_color = QColor(45, 55, 72, 102)  # rgba(45, 55, 72, 0.4)
            border_color = QColor(255, 255, 255, 51)  # rgba(255, 255, 255, 0.2)
        else:
            bg_color = QColor(255, 255, 255, 51)  # rgba(255, 255, 255, 0.2)
            border_color = QColor(255, 255, 255, 102)  # rgba(255, 255, 255, 0.4)
        
        # Create gradient for checked state
        if self.isChecked():
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            if is_dark:
                gradient.setColorAt(0, QColor(92, 170, 197, 229))  # rgba(92, 170, 197, 0.9)
                gradient.setColorAt(1, QColor(92, 205, 213, 229))  # rgba(92, 205, 213, 0.9)
                border_color = QColor(92, 170, 197, 204)  # rgba(92, 170, 197, 0.8)
            else:
                gradient.setColorAt(0, QColor(60, 101, 160, 229))  # rgba(60, 101, 160, 0.9)
                gradient.setColorAt(1, QColor(92, 170, 197, 229))  # rgba(92, 170, 197, 0.9)
                border_color = QColor(60, 101, 160, 204)  # rgba(60, 101, 160, 0.8)
            
            painter.setBrush(QBrush(gradient))
        else:
            painter.setBrush(QBrush(bg_color))
        
        # Draw border
        pen = QPen(border_color, 2)
        painter.setPen(pen)
        
        # Draw rounded rectangle
        painter.drawRoundedRect(rect, 8, 8)
        
        # Draw checkmark if checked
        if self.isChecked():
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            font = QFont()
            font.setPixelSize(14)
            font.setBold(True)
            painter.setFont(font)
            
            # Draw Unicode checkmark
            painter.drawText(rect, Qt.AlignCenter, "✓")
        
        # Draw the text
        if self.text():
            text_rect = self.rect()
            text_rect.setLeft(rect.right() + 8)  # 8px spacing
            painter.setPen(QPen(QColor(29, 29, 31) if not is_dark else QColor(245, 245, 247)))
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.text())
    
    def styleOption(self):
        """Get style option for the checkbox"""
        from PyQt5.QtWidgets import QStyleOptionButton
        option = QStyleOptionButton()
        option.initFrom(self)
        option.text = self.text()
        option.state = self.style().State_Enabled
        if self.isChecked():
            option.state |= self.style().State_On
        else:
            option.state |= self.style().State_Off
        return option


def apply_glass_checkbox_style():
    """Apply the glass checkbox style globally"""
    return """
        /* Enhanced Checkbox with Unicode Checkmarks */
        QCheckBox {
            font-weight: 500;
            spacing: 10px;
            color: #1D1D1F;
        }
        
        QCheckBox[darkTheme="true"] {
            color: #F5F5F7;
        }
        
        QCheckBox::indicator {
            width: 24px;
            height: 24px;
            border-radius: 8px;
            border: 2px solid rgba(255, 255, 255, 0.4);
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        QCheckBox::indicator:hover {
            border: 2px solid rgba(60, 101, 160, 0.6);
            background-color: rgba(255, 255, 255, 0.3);
        }
        
        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 rgba(60, 101, 160, 0.95),
                                       stop:1 rgba(92, 170, 197, 0.9));
            border: 2px solid rgba(60, 101, 160, 0.8);
        }
        
        /* Unicode checkmark using content property */
        QCheckBox::indicator:checked:after {
            content: "✓";
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding-left: 4px;
            padding-top: 2px;
        }
        
        /* Dark theme checkbox */
        QWidget[darkTheme="true"] QCheckBox::indicator {
            border: 2px solid rgba(255, 255, 255, 0.2);
            background-color: rgba(45, 55, 72, 0.4);
        }
        
        QWidget[darkTheme="true"] QCheckBox::indicator:hover {
            border: 2px solid rgba(92, 170, 197, 0.6);
            background-color: rgba(45, 55, 72, 0.6);
        }
        
        QWidget[darkTheme="true"] QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 rgba(92, 170, 197, 0.95),
                                       stop:1 rgba(92, 205, 213, 0.9));
            border: 2px solid rgba(92, 170, 197, 0.8);
        }
    """


if __name__ == "__main__":
    # Test the custom checkbox
    import sys
    from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    layout = QVBoxLayout(window)
    
    # Add custom checkboxes
    cb1 = GlassCheckBox("Light theme checkbox")
    cb2 = GlassCheckBox("Dark theme checkbox")
    cb2.setProperty("darkTheme", True)
    cb2.setChecked(True)
    
    layout.addWidget(cb1)
    layout.addWidget(cb2)
    
    window.show()
    sys.exit(app.exec_())
