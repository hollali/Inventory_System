import os
import re
import sys
import tkinter as tk
from tkinter import messagebox

DESIGN_W = 1920
DESIGN_H = 1080
FONT_FAMILY = 'times new roman'

PRIMARY = '#0f4d7d'
PRIMARY_DARK = '#010c48'
PRIMARY_HOVER = '#0d5a90'
ACCENT = '#009688'
ACCENT_HOVER = '#007a6b'
DANGER = '#c0392b'
DANGER_HOVER = '#a93226'
FIELD_BG = 'lightyellow'
HEADER_FG = 'white'

CARD_EMPLOYEE = '#2C3E50'
CARD_SUPPLIER = '#8E44AD'
CARD_CATEGORY = '#27AE68'
CARD_PRODUCT = '#2288EE'
CARD_SALES = '#8E444D'

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^\+?[\d\s()-]{7,20}$')


def resource_path(relative):
    base = getattr(sys, '_MEIPASS', None)
    if base is None:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


def screen_size(window):
    return window.winfo_screenwidth(), window.winfo_screenheight()


def scale(window):
    w, h = screen_size(window)
    return w / DESIGN_W, h / DESIGN_H


def setup_window(window, title):
    w, h = screen_size(window)
    window.geometry(f'{w}x{h}+0+0')
    window.resizable(True, True)
    window.title(title)


def px(sx, value):
    return int(round(value * sx))


def py(sy, value):
    return int(round(value * sy))


def pw(sx, value):
    return int(round(value * sx))


def ph(sy, value):
    return int(round(value * sy))


def fs(sy, size):
    return max(8, int(round(size * sy)))


def validate_email(value):
    return bool(EMAIL_RE.match(str(value).strip()))


def validate_phone(value):
    return bool(PHONE_RE.match(str(value).strip()))


def is_number(value, positive=False):
    try:
        number = float(str(value).strip().replace(',', ''))
    except (ValueError, TypeError):
        return False
    return number > 0 if positive else True


def is_positive_int(value):
    return str(value).strip().isdigit()


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.after_id = None
        widget.bind('<Enter>', self._enter)
        widget.bind('<Leave>', self._leave)
        widget.bind('<ButtonPress>', self._leave)

    def _enter(self, event=None):
        if self.after_id is not None:
            self.widget.after_cancel(self.after_id)
        self.after_id = self.widget.after(500, self._show)

    def _leave(self, event=None):
        if self.after_id is not None:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None

    def _show(self):
        self.after_id = None
        if self.tip is not None:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f'+{x}+{y}')
        tk.Label(self.tip, text=self.text, bg='#ffffe0', relief='solid',
                 borderwidth=1, font=(FONT_FAMILY, 10)).pack()


def button(master, text, command, danger=False, width=10, font_size=12, icon=None):
    bg = DANGER if danger else PRIMARY
    hover = DANGER_HOVER if danger else PRIMARY_HOVER
    return tk.Button(master, image=icon, compound=LEFT if icon else None, text=text,
                     font=(FONT_FAMILY, font_size), width=width, cursor='hand2',
                     fg='white', bg=bg, activebackground=hover, activeforeground='white',
                     bd=0, padx=10, command=command)


def export_to_csv(parent, columns, records, default_name):
    from tkinter import filedialog
    import csv
    filepath = filedialog.asksaveasfilename(
        parent=parent, defaultextension='.csv', initialfile=default_name,
        filetypes=[('CSV files', '*.csv'), ('All files', '*.*')])
    if not filepath:
        return
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(records)
        messagebox.showinfo('Success', f'Data exported to:\n{filepath}')
    except Exception as e:
        messagebox.showerror('Error', f'Export failed: {e}')
