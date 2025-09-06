# -*- coding: utf-8 -*-
"""
Created on Sat Sep  6 13:30:47 2025

@author: Administrator
"""

import sys
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QDateTimeEdit, QMessageBox, QProgressBar, QHeaderView, QSpinBox
)
from PyQt6.QtCore import QDateTime, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QBrush, QPixmap, QPalette

TODO_FILE = "todos.json"
SETTINGS_FILE = "settings.json"  # فایل برای ذخیره تنظیمات

# ---------- Theme definitions ----------
THEMES = {
    "Pink": {
        "bg": "#ffe6f0", 
        "button": "#ffb3d9", 
        "done": "#b3ffcc",      # سبز برای انجام شده
        "pending": "#fff0b3",   # زرد برای در حال انتظار  
        "late": "#ffcccc",      # قرمز برای overdue
        "bg_image": "bg_pink.jpg",
        "progress": "#d9b3ff"   # بنفش برای نوار پیشرفت
    },
    "Blue": {
        "bg": "#e6f0ff", 
        "button": "#b3d9ff", 
        "done": "#b3ffcc",      # سبز برای انجام شده
        "pending": "#fff0b3",   # زرد برای در حال انتظار
        "late": "#ffcccc",      # قرمز برای overdue
        "bg_image": "bg_blue.jpg",
        "progress": "#d9b3ff"   # بنفش برای نوار پیشرفت
    },
    "Neutral": {
        "bg": "#f0f0f0", 
        "button": "#d9d9d9", 
        "done": "#b3ffcc",      # سبز برای انجام شده
        "pending": "#fff0b3",   # زرد برای در حال انتظار
        "late": "#ffcccc",      # قرمز برای overdue
        "bg_image": "bg_neutral.jpg",
        "progress": "#d9b3ff"   # بنفش برای نوار پیشرفت
    }
}

CATEGORY_ICONS = {
    "Math": "icons/math.png",
    "Science": "icons/science.png",
    "Language": "icons/language.png",
    "Sports": "icons/sports.png",
    "General": "icons/general.png"
}

# ---------- File I/O ----------
def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, "r", encoding="utf-8") as f:
        todos = json.load(f)
    return todos

def save_todos(todos):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=4, ensure_ascii=False)

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"theme": "Neutral"}  # تم پیش‌فرض
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)
    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

def calculate_progress(todos):
    if not todos:
        return 0
    done_count = sum(1 for t in todos if t.get("done", False))
    return int((done_count / len(todos)) * 100)

# ---------- Main App ----------
class ToDoNXG(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📌 ToDo NXG")
        self.setGeometry(100, 100, 1100, 700)
        self.todos = load_todos()
        
        # بارگذاری تنظیمات و انتخاب تم
        settings = load_settings()
        self.current_theme = settings.get("theme", "Neutral")
        self.editing_index = -1
        
        # تعریف theme_buttons قبل از استفاده
        self.theme_buttons = {}

        # Fonts
        self.font_input = QFont("Arial", 10)
        self.font_table = QFont("Arial", 11)
        self.font_header = QFont("Arial", 12, QFont.Weight.Bold)

        # Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # ---------- Header Section (Logo and Title) ----------
        header_layout = QHBoxLayout()
        
        # لوگو و عنوان برنامه
        logo_label = QLabel("📌")
        logo_label.setFont(QFont("Arial", 24))
        
        title_label = QLabel("ToDo NXG")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # اضافه کردن دکمه‌های تم به هدر
        for name in THEMES.keys():
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, n=name: self.set_theme(n))
            self.theme_buttons[name] = btn
            header_layout.addWidget(btn)
        
        self.layout.addLayout(header_layout)

        # ---------- Progress Section ----------
        progress_layout = QHBoxLayout()
        
        # نوار پیشرفت با نمایش متن
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        self.layout.addLayout(progress_layout)

        # ---------- Filter Section (4 Comboboxes) ----------
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        # Combobox 1: Status Filter
        status_label = QLabel("Status:")
        status_label.setFixedWidth(50)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Done", "Pending"])
        self.status_filter.setFont(self.font_input)
        self.status_filter.currentTextChanged.connect(self.refresh_table)
        
        # Combobox 2: Category Filter
        category_label = QLabel("Category:")
        category_label.setFixedWidth(60)
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All Categories"] + list(CATEGORY_ICONS.keys()))
        self.category_filter.setFont(self.font_input)
        self.category_filter.currentTextChanged.connect(self.refresh_table)
        
        # Combobox 3: Priority Filter
        priority_label = QLabel("Priority:")
        priority_label.setFixedWidth(50)
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All Priorities", "High", "Normal", "Low"])
        self.priority_filter.setFont(self.font_input)
        self.priority_filter.currentTextChanged.connect(self.refresh_table)
        
        # Combobox 4: Date Filter
        date_label = QLabel("Date:")
        date_label.setFixedWidth(35)
        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Dates", "Today", "This Week", "This Month", "Overdue"])
        self.date_filter.setFont(self.font_input)
        self.date_filter.currentTextChanged.connect(self.refresh_table)
        
        # اضافه کردن Combobox ها به لایه با فاصله کمتر
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(category_label)
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(priority_label)
        filter_layout.addWidget(self.priority_filter)
        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self.date_filter)
        
        self.layout.addLayout(filter_layout)

        # ---------- Search ----------
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Task Title or Category...")
        self.search_input.textChanged.connect(self.refresh_table)
        search_layout.addWidget(self.search_input)
        
        self.layout.addLayout(search_layout)

        # ---------- Task Table ----------
        self.table = QTableWidget(0, 7)  # 7 ستون با اضافه شدن ساعت مطالعه
        # تغییر ترتیب ستون‌ها: Deadline قبل از Study Hours
        self.table.setHorizontalHeaderLabels(["Status", "Title", "Category", "Priority", "Deadline", "Study Hours", "Actions"])
        
        # تنظیم عرض ستون‌ها
        self.table.setColumnWidth(0, 120)   # ستون Status
        self.table.setColumnWidth(1, 200)   # ستون Title
        self.table.setColumnWidth(2, 100)   # ستون Category
        self.table.setColumnWidth(3, 100)   # ستون Priority
        self.table.setColumnWidth(4, 150)   # ستون Deadline (جابجا شده)
        self.table.setColumnWidth(5, 100)   # ستون Study Hours (جابجا شده)
        self.table.setColumnWidth(6, 220)   # ستون Actions
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # تنظیم ارتفاع سطرها
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().setMinimumSectionSize(70)
        
        # فعال کردن ToolTip
        self.table.setMouseTracking(True)
        self.table.itemEntered.connect(self.show_tooltip)
        
        self.layout.addWidget(self.table)

        # ---------- Add/Edit Task Form ----------
        form_layout = QHBoxLayout()
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task Title")
        self.title_input.setFont(self.font_input)
        self.title_input.setFixedHeight(60)  # ارتفاع یکسان

        self.category_input = QComboBox()
        self.category_input.addItems(list(CATEGORY_ICONS.keys()))
        self.category_input.setFont(self.font_input)
        self.category_input.setFixedHeight(60)  # ارتفاع یکسان

        self.priority_input = QComboBox()
        self.priority_input.addItems(["High", "Normal", "Low"])
        self.priority_input.setFont(self.font_input)
        self.priority_input.setFixedHeight(60)  # ارتفاع یکسان

        # ابتدا Deadline سپس Study Hours
        self.datetime_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.datetime_input.setFont(self.font_input)
        self.datetime_input.setFixedHeight(60)  # ارتفاع یکسان
        self.datetime_input.setCalendarPopup(True)  # افزودن تقویم برای یکسانی ظاهر

        # SpinBox برای ساعت مطالعه
        self.study_hours_input = QSpinBox()
        self.study_hours_input.setMinimum(0)
        self.study_hours_input.setMaximum(100)
        self.study_hours_input.setSuffix(" hours")
        self.study_hours_input.setFont(self.font_input)
        self.study_hours_input.setFixedHeight(60)  # ارتفاع یکسان
        self.study_hours_input.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)  # فلش‌های یکسان

        self.add_button = QPushButton("➕ ADD TASK")
        self.add_button.clicked.connect(self.add_task)
        self.add_button.setFont(self.font_input)
        self.add_button.setFixedHeight(60)  # ارتفاع یکسان

        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.cancel_button.setFont(self.font_input)
        self.cancel_button.setFixedHeight(60)  # ارتفاع یکسان
        self.cancel_button.hide()

        for widget in [self.title_input, self.category_input, self.priority_input, 
                      self.datetime_input, self.study_hours_input, self.add_button, self.cancel_button]:
            form_layout.addWidget(widget)

        self.layout.addLayout(form_layout)

        # ---------- Reminder Timer ----------
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(60 * 1000)

        # ---------- Apply Theme ----------
        self.set_theme(self.current_theme)
        self.refresh_table()

    # ---------- ToolTip for table cells ----------
    def show_tooltip(self, item):
        if item is not None:
            self.table.setToolTip(item.text())
        else:
            self.table.setToolTip("")

    # ---------- Theme ----------
    def set_theme(self, theme_name):
        self.current_theme = theme_name
        t = THEMES[theme_name]
        
        # ذخیره تم انتخاب شده
        settings = {"theme": theme_name}
        save_settings(settings)
        
        # تنظیم پس‌زمینه با تصویر
        palette = self.palette()
        if os.path.exists(t["bg_image"]):
            palette.setBrush(QPalette.ColorRole.Window, QBrush(QPixmap(t["bg_image"])))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor(t['bg']))
        self.setPalette(palette)
        
        # استایل یکسان برای همه دکمه‌ها
        button_style = f"""
            QPushButton {{
                background-color: {t['button']};
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
                border: none;
                color: #333;
                min-height: 60px;
            }}
            QPushButton:hover {{
                background-color: {t['pending']};
                transform: scale(1.5);
            }}
            QPushButton:pressed {{
                background-color: {t['late']};
            }}
        """
        
        # اعمال استایل برای تمام دکمه‌ها
        for btn in self.theme_buttons.values():
            btn.setStyleSheet(button_style)
            btn.setFixedHeight(40)  # ارتفاع یکسان
        
        self.add_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)
        
        # استایل برای دکمه‌های داخل جدول
        table_button_style = f"""
            QPushButton {{
                background-color: {t['button']};
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
                border: none;
                color: #333;
                margin: 2px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {t['pending']};
            }}
            QPushButton:pressed {{
                background-color: {t['late']};
            }}
        """
        
        # استایل برای فیلدهای ورودی و combobox ها
        input_style = f"""
            QLineEdit, QComboBox, QDateTimeEdit, QSpinBox {{
                border: 2px solid {t['button']};
                border-radius: 8px;
                padding: 8px;
                background-color: #fff;
                min-height: 40px;
                font-size: 14px;
            }}
            QLineEdit:hover, QComboBox:hover, QDateTimeEdit:hover, QSpinBox:hover {{
                border: 2px solid {t['pending']};
            }}
            QComboBox::drop-down {{
                border: 0px;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
                width: 16px;
                height: 16px;
            }}
            QDateTimeEdit::drop-down {{
                border: 0px;
                width: 30px;
            }}
            QDateTimeEdit::down-arrow {{
                image: url(down_arrow.png);
                width: 16px;
                height: 16px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 30px;
                border: none;
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                width: 16px;
                height: 16px;
            }}
        """
        
        # اعمال استایل برای فیلدهای ورودی
        self.title_input.setStyleSheet(input_style)
        self.category_input.setStyleSheet(input_style)
        self.priority_input.setStyleSheet(input_style)
        self.datetime_input.setStyleSheet(input_style)
        self.study_hours_input.setStyleSheet(input_style)
        self.search_input.setStyleSheet(input_style)
        
        # اعمال استایل برای combobox های فیلتر
        self.status_filter.setStyleSheet(input_style)
        self.category_filter.setStyleSheet(input_style)
        self.priority_filter.setStyleSheet(input_style)
        self.date_filter.setStyleSheet(input_style)
        
        # استایل برای نوار پیشرفت (بنفش)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {t['progress']};
                border-radius: 10px;
                text-align: center;
                height: 30px;
                font-weight: bold;
                color: #333;
                background-color: rgba(255, 255, 255, 150);
            }}
            QProgressBar::chunk {{
                background-color: {t['progress']};
                border-radius: 10px;
            }}
        """)
        
        # استایل ساده‌تر برای جدول
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border-radius: 8px;
                gridline-color: rgba(200, 200, 200, 100);
                border: 1px solid {t['button']};
            }}
            QHeaderView::section {{
                background-color: {t['button']};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        # ذخیره استایل دکمه‌های جدول
        self.table_button_style = table_button_style
        self.refresh_table()

    # ---------- Table ----------
    def refresh_table(self):
        self.table.setRowCount(0)
        now = datetime.now()
        search = self.search_input.text().lower()
        
        # دریافت فیلترها
        status_filter = self.status_filter.currentText()
        category_filter = self.category_filter.currentText()
        priority_filter = self.priority_filter.currentText()
        date_filter = self.date_filter.currentText()
        
        # فیلتر کردن و مرتب‌سازی تسک‌ها بر اساس ددلاین
        filtered_todos = []
        for task in self.todos:
            # فیلتر جستجو
            if search and search not in task.get("title","").lower() and search not in task.get("category","").lower():
                continue
                
            # فیلتر وضعیت
            if status_filter == "Done" and not task.get("done", False):
                continue
            if status_filter == "Pending" and task.get("done", False):
                continue
                
            # فیلتر دسته‌بندی
            if category_filter != "All Categories" and task.get("category","") != category_filter:
                continue
                
            # فیلتر اولویت
            if priority_filter != "All Priorities" and task.get("priority","") != priority_filter:
                continue
                
            # فیلter تاریخ
            if date_filter != "All Dates":
                try:
                    due_date = datetime.strptime(task.get("due_date",""), "%Y-%m-%d %H:%M")
                    if date_filter == "Today" and due_date.date() != now.date():
                        continue
                    if date_filter == "This Week" and due_date.isocalendar()[1] != now.isocalendar()[1]:
                        continue
                    if date_filter == "This Month" and due_date.month != now.month:
                        continue
                    if date_filter == "Overdue" and (due_date >= now or task.get("done", False)):
                        continue
                except:
                    continue
            
            filtered_todos.append(task)
        
        # مرتب‌سازی بر اساس ددلاین (تاریخ و زمان)
        try:
            filtered_todos.sort(key=lambda x: datetime.strptime(x.get("due_date", "9999-12-31 23:59"), "%Y-%m-%d %H:%M"))
        except:
            # اگر تاریخ معتبر نبود، بدون مرتب‌سازی ادامه بده
            pass
                
        for index, task in enumerate(filtered_todos):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # تنظیم ارتفاع سطر
            self.table.setRowHeight(row, 60)

            # تعیین رنگ بر اساس وضعیت
            if task.get("done", False):
                # سبز برای کارهای انجام شده
                row_color = QColor(THEMES[self.current_theme]['done'])
            else:
                try:
                    due_date = datetime.strptime(task.get("due_date",""), "%Y-%m-%d %H:%M")
                    if due_date < now:
                        # قرمز برای کارهای overdue
                        row_color = QColor(THEMES[self.current_theme]['late'])
                    else:
                        # زرد برای کارهای در حال انتظار
                        row_color = QColor(THEMES[self.current_theme]['pending'])
                except:
                    # زرد برای کارهای بدون تاریخ
                    row_color = QColor(THEMES[self.current_theme]['pending'])

            # Status
            status_btn = QPushButton("✅ Done" if task.get("done", False) else "❌ Pending")
            status_btn.setFont(self.font_table)
            status_btn.setStyleSheet(self.table_button_style)
            status_btn.setFixedHeight(40)
        
            # پیدا کردن ایندکس اصلی تسک در لیست اصلی
            original_index = next((i for i, t in enumerate(self.todos) if t == task), -1)
            status_btn.clicked.connect(lambda checked, idx=original_index: self.toggle_status(idx))
            
            # ایجاد ویجت برای سلول Status و تنظیم رنگ پس‌زمینه
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.addWidget(status_btn)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # وسط چین افقی
            status_layout.setContentsMargins(5, 10, 5, 10)  # حاشیه مناسب
            status_widget.setStyleSheet(f"background-color: {row_color.name()};")
            self.table.setCellWidget(row, 0, status_widget)

            # Title
            title_item = QTableWidgetItem(task.get("title",""))
            title_item.setFont(self.font_table)
            title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            title_item.setToolTip(task.get("title",""))
            title_item.setBackground(row_color)
            self.table.setItem(row, 1, title_item)

            # Category
            cat_item = QTableWidgetItem(task.get("category",""))
            cat_item.setFont(self.font_table)
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cat_item.setToolTip(task.get("category",""))
            cat_item.setBackground(row_color)
            self.table.setItem(row, 2, cat_item)

            # Priority
            pri_item = QTableWidgetItem(task.get("priority",""))
            pri_item.setFont(self.font_table)
            pri_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pri_item.setToolTip(task.get("priority",""))
            pri_item.setBackground(row_color)
            self.table.setItem(row, 3, pri_item)

            # Deadline (ستون 4)
            dead_item = QTableWidgetItem(task.get("due_date",""))
            dead_item.setFont(self.font_table)
            dead_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dead_item.setToolTip(task.get("due_date",""))
            dead_item.setBackground(row_color)
            self.table.setItem(row, 4, dead_item)

            # Study Hours (ستون 5)
            study_hours = task.get("study_hours", 0)
            study_item = QTableWidgetItem(f"{study_hours} hours")
            study_item.setFont(self.font_table)
            study_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            study_item.setToolTip(f"{study_hours} hours")
            study_item.setBackground(row_color)
            self.table.setItem(row, 5, study_item)


            # Actions (Edit and Delete buttons)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 10, 5, 10)  # حاشیه مناسب
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # وسط چین افقی
            
            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setFont(self.font_table)
            edit_btn.setStyleSheet(self.table_button_style)
            edit_btn.setFixedHeight(40)
            edit_btn.clicked.connect(lambda checked, idx=original_index: self.edit_task(idx))
            
            delete_btn = QPushButton("🗑️ Delete")
            delete_btn.setFont(self.font_table)
            delete_btn.setStyleSheet(self.table_button_style)
            delete_btn.setFixedHeight(40)
            delete_btn.clicked.connect(lambda checked, idx=original_index: self.delete_task(idx))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_widget.setLayout(actions_layout)
            
            # ستون Actions را رنگ نکنیم
            self.table.setCellWidget(row, 6, actions_widget)

        # بروزرسانی درصد پیشرفت
        progress = calculate_progress(self.todos)
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{progress}%")

    # ---------- Add Task ----------
    def add_task(self):
        title = self.title_input.text().strip()
        category = self.category_input.currentText()
        priority = self.priority_input.currentText()
        due_date = self.datetime_input.dateTime().toString("yyyy-MM-dd HH:mm")
        study_hours = self.study_hours_input.value()
        
        if not title:
            QMessageBox.warning(self, "⚠️ Error", "Task title cannot be empty.")
            return
            
        if self.editing_index >= 0:
            # حالت ویرایش
            self.todos[self.editing_index] = {
                "title": title, 
                "category": category, 
                "priority": priority, 
                "due_date": due_date, 
                "study_hours": study_hours,
                "done": self.todos[self.editing_index].get("done", False)
            }
            self.editing_index = -1
            self.add_button.setText("➕ ADD TASK")
            self.cancel_button.hide()
        else:
            # حالت افزودن جدید
            task = {
                "title": title, 
                "category": category, 
                "priority": priority, 
                "due_date": due_date, 
                "study_hours": study_hours,
                "done": False
            }
            self.todos.append(task)
            
        save_todos(self.todos)
        self.title_input.clear()
        self.study_hours_input.setValue(0)
        self.refresh_table()

    # ---------- Edit Task ----------
    def edit_task(self, index):
        task = self.todos[index]
        self.title_input.setText(task.get("title", ""))
        
        category_index = self.category_input.findText(task.get("category", ""))
        if category_index >= 0:
            self.category_input.setCurrentIndex(category_index)
            
        priority_index = self.priority_input.findText(task.get("priority", ""))
        if priority_index >= 0:
            self.priority_input.setCurrentIndex(priority_index)
            
        try:
            due_date = QDateTime.fromString(task.get("due_date", ""), "yyyy-MM-dd HH:mm")
            self.datetime_input.setDateTime(due_date)
        except:
            pass
            
        # تنظیم ساعت مطالعه
        self.study_hours_input.setValue(task.get("study_hours", 0))
            
        self.editing_index = index
        self.add_button.setText("💾 UPDATE TASK")
        self.cancel_button.show()

    def cancel_edit(self):
        self.editing_index = -1
        self.title_input.clear()
        self.study_hours_input.setValue(0)
        self.add_button.setText("➕ ADD TASK")
        self.cancel_button.hide()

    # ---------- Delete Task ----------
    def delete_task(self, index):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    "Are you sure you want to delete this task?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.todos[index]
            save_todos(self.todos)
            self.refresh_table()

    # ---------- Toggle Status ----------
    def toggle_status(self, index):
        self.todos[index]["done"] = not self.todos[index].get("done", False)
        save_todos(self.todos)
        self.refresh_table()

    # ---------- Reminder ----------
    def check_reminders(self):
        now = datetime.now()
        for task in self.todos:
            if not task.get("done", False):
                try:
                    due_date = datetime.strptime(task.get("due_date",""), "%Y-%m-%d %H:%M")
                except:
                    continue
                minutes_left = int((due_date - now).total_seconds() // 60)
                if 0 < minutes_left <= 60:
                    QMessageBox.information(self, "⏰ Reminder",
                                            f"Task '{task.get('title','')}' is due in {minutes_left} minutes!")

# ---------- Run ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToDoNXG()
    window.show()
    sys.exit(app.exec())