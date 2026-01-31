import tkinter as tk
from tkinter import font, messagebox, ttk
from PIL import Image, ImageTk
import json
import os

# --- 스타일 및 경로 설정 ---
BASE_DIR = os.path.dirname(__file__)
STYLE_DIR = os.path.join(BASE_DIR, "styles")


def load_style(name):
    if not name: return {}
    if not name.endswith(".json"): name += ".json"
    path = os.path.join(STYLE_DIR, name) if not os.path.isabs(name) else name
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- 핵심 Setter 클래스 (디자인/애니메이션 제어) ---
class _Setter:
    def __init__(self, widget):
        self.widget = widget
        try:
            current_font = widget.cget("font")
            if isinstance(current_font, str):
                self._font = font.Font(font=font.nametofont(current_font))
            else:
                self._font = font.Font(font=current_font)
            widget.config(font=self._font)
        except:
            self._font = None

    def size(self, w, h=None):
        if isinstance(self.widget, ttk.Progressbar):
            self.widget.config(length=w)
        else:
            self.widget.place_configure(width=w, height=h)
        return self

    def color(self, bg=None, fg=None):
        if bg:
            try:
                self.widget.config(bg=bg)
            except:
                pass
        if fg:
            try:
                self.widget.config(fg=fg)
            except:
                pass
        return self

    def bold(self, value=True):
        if self._font: self._font.configure(weight="bold" if value else "normal")
        return self

    def pos(self, x, y):
        self.widget.place(x=x, y=y)
        return self

    def text(self, value):
        if hasattr(self.widget, 'config') and 'text' in self.widget.config():
            self.widget.config(text=value)
        return self

    def text_size(self, value):
        if self._font: self._font.configure(size=value)
        return self

    def hover(self, bg=None, fg=None):
        try:
            n_bg = self.widget.cget("bg")
            n_fg = self.widget.cget("fg")
            self.widget.bind("<Enter>", lambda e: self.color(bg, fg))
            self.widget.bind("<Leave>", lambda e: self.color(n_bg, n_fg))
        except:
            pass
        return self


# --- 위젯별 클래스 정의 ---
class UIElement:
    def __init__(self, widget):
        self.widget = widget
        self.set = _Setter(widget)
        self._required, self._name = False, None

    def hide(self):
        self.widget.place_forget()

    def show(self):
        self.widget.place()

    def destroy(self):
        self.widget.destroy()

    def required(self, name=None):
        self._required, self._name = True, name
        return self

    def on_click(self, action):
        if hasattr(self.widget, 'config') and 'command' in self.widget.config():
            self.widget.config(command=action)
        else:
            self.widget.bind("<Button-1>", lambda e: action())
        return self


class TextBox(UIElement):
    def __init__(self, entry, var):
        super().__init__(entry)
        self.var = var
        self._placeholder = None

    @property
    def text(self):
        v = self.var.get()
        return "" if v == self._placeholder else v

    @text.setter
    def text(self, val):
        self.var.set(val)

    @property
    def input(self):
        return self.text

    def set_placeholder(self, text, color="#999"):
        self._placeholder = text
        self.var.set(text)
        self.widget.config(fg=color)

        def on_focus_in(e):
            if self.var.get() == text:
                self.var.set("")
                self.widget.config(fg="black")

        def on_focus_out(e):
            if not self.var.get():
                self.var.set(text)
                self.widget.config(fg=color)

        self.widget.bind("<FocusIn>", on_focus_in)
        self.widget.bind("<FocusOut>", on_focus_out)


class CheckBox(UIElement):
    def __init__(self, cb, var):
        super().__init__(cb)
        self.var = var

    @property
    def checked(self): return bool(self.var.get())


class RadioButton(UIElement):
    def __init__(self, rb, var, value):
        super().__init__(rb)
        self.var = var
        self.value = value

    @property
    def checked(self): return self.var.get() == self.value


class ImageBox(UIElement):
    def __init__(self, label):
        super().__init__(label)
        self._img_ref = None

    def load(self, path, w=None, h=None):
        try:
            img = Image.open(path)
            if not w: w = self.widget.winfo_width()
            if not h: h = self.widget.winfo_height()
            if w > 1 and h > 1:
                img = img.resize((w, h), Image.Resampling.LANCZOS)
            self._img_ref = ImageTk.PhotoImage(img)
            self.widget.config(image=self._img_ref, text="")
        except Exception as e:
            print(f"Image Error: {e}")


class ProgressBar(UIElement):
    def set_value(self, val): self.widget['value'] = val


# --- Form (입력 검증) 클래스 ---
class Form:
    def __init__(self, *fields):
        self.fields = fields

    def __bool__(self):
        for f in self.fields:
            if getattr(f, "_required", False):
                if isinstance(f, TextBox) and not f.text: return False
                if isinstance(f, CheckBox) and not f.checked: return False
        return True

    def submit(self, btn_el, func):
        def wrapped():
            if self:
                func()
            else:
                messagebox.showwarning("입력 오류", "필수 항목을 모두 채워주세요.")

        btn_el.on_click(wrapped)


# --- 메인 생성 클래스 ---
class _Create:
    def __init__(self):
        self.root = None
        self.content = None
        self._radio_vars = {}

    def alert(self, title, message):
        """간편한 알림창 띄우기"""
        messagebox.showinfo(title, message)

    def warn(self, title, message):
        """간편한 경고창 띄우기"""
        messagebox.showwarning(title, message)

    def window(self, title, size):
        if not self.root: self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(size)
        self.content = tk.Frame(self.root)
        self.content.pack(fill="both", expand=True)

    def _apply_designer(self, element, style):
        data = load_style(style)
        if not data: return
        p = data.get("props", {})
        s = element.set
        if "x" in p and "y" in p: s.pos(p["x"], p["y"])
        if "width" in p: s.size(p["width"], p.get("height"))
        if "text" in p: s.text(p["text"])
        if "font_size" in p: s.text_size(int(p["font_size"]))
        if p.get("bold"): s.bold(True)
        if "bg" in p: s.color(bg=p["bg"])
        if "fg" in p: s.color(fg=p["fg"])
        # 이미지 자동 로드
        if data.get("type") == "ImageLabel" and p.get("image_path") and isinstance(element, ImageBox):
            element.load(p["image_path"], p.get("width"), p.get("height"))

    def label(self, text="", style=None):
        lbl = tk.Label(self.content, text=text)
        el = UIElement(lbl)
        self._apply_designer(el, style) if style else lbl.pack()
        return el

    def button(self, text="Button", style=None):
        btn = tk.Button(self.content, text=text)
        el = UIElement(btn)
        self._apply_designer(el, style) if style else btn.pack()
        return el

    def textbox(self, style=None):
        v = tk.StringVar()
        e = tk.Entry(self.content, textvariable=v)
        el = TextBox(e, v)
        self._apply_designer(el, style) if style else e.pack()
        return el

    def checkbox(self, text="Check", style=None):
        v = tk.IntVar()
        cb = tk.Checkbutton(self.content, text=text, variable=v)
        el = CheckBox(cb, v)
        self._apply_designer(el, style) if style else cb.pack()
        return el

    def radiobutton(self, text="Radio", group="default", value=1, style=None):
        if group not in self._radio_vars: self._radio_vars[group] = tk.IntVar(value=1)
        v = self._radio_vars[group]
        rb = tk.Radiobutton(self.content, text=text, variable=v, value=value)
        el = RadioButton(rb, v, value)
        self._apply_designer(el, style) if style else rb.pack()
        return el

    def image(self, style=None):
        lbl = tk.Label(self.content)
        el = ImageBox(lbl)
        if style:
            self._apply_designer(el, style)
        else:
            lbl.pack()
        return el

    def progressbar(self, max_v=100, style=None):
        pb = ttk.Progressbar(self.content, maximum=max_v)
        el = ProgressBar(pb)
        self._apply_designer(el, style) if style else pb.pack()
        return el

    def form(self, *fields):
        return Form(*fields)

    def start(self):
        if self.root: self.root.mainloop()

def run_designer():
    from .designer import DesignerApp # designer.py가 같은 폴더에 있어야 함
    import tkinter as tk
    root = tk.Tk()
    app = DesignerApp(root)
    root.mainloop()

create = _Create()