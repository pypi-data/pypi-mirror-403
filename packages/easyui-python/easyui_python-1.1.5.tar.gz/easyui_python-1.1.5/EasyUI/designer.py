import tkinter as tk
from tkinter import colorchooser, ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
import json
import os

# --- 1. 오브젝트 스펙 정의 ---
OBJECT_SPECS = {
    "Button": {
        "class": tk.Button,
        "props": ["text", "width", "height", "bg", "fg", "font_size", "bold"]
    },
    "Label": {
        "class": tk.Label,
        "props": ["text", "fg", "font_size", "bold"]
    },
    "Entry": {
        "class": tk.Entry,
        "props": ["width", "bg", "fg", "font_size"]
    },
    "ProgressBar": {
        "class": ttk.Progressbar,
        "props": ["width", "height"]
    },
    "CheckBox": {
        "class": tk.Checkbutton,
        "props": ["text", "fg", "font_size", "bold"]
    },
    "RadioButton": {
        "class": tk.Radiobutton,
        "props": ["text", "fg", "font_size", "bold"]
    },
    "ImageLabel": {
        "class": tk.Label,
        "props": ["width", "height", "bg", "image_path"]
    }
}


class DesignerApp:
    def __init__(self, root):
        # ⚠️ 중요: 여기서 Tk()를 새로 만들지 않고 전달받은 root를 사용합니다.
        self.root = root
        self.root.title("EasyUI Designer Pro (DnD & Delete Support)")
        self.root.geometry("1200x800")

        self.current_widget = None
        self.current_type = None
        self.widget_data = {}
        self.image_refs = {}

        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # 단축키 설정
        self.root.bind("<Delete>", lambda e: self.delete_current_widget())

        self.build_top()
        self.build_layout()
        self.build_object_list()
        self.build_property_panel()
        self.refresh_style_list()

    def build_top(self):
        top = tk.Frame(self.root, bg="#2b2b2b", height=50)
        top.pack(fill="x")

        left_menu = tk.Frame(top, bg="#2b2b2b")
        left_menu.pack(side="left", padx=10)

        tk.Button(left_menu, text="새로 만들기", command=self.new_design, bg="#444", fg="white", padx=10).pack(side="left",
                                                                                                          padx=5)
        tk.Button(left_menu, text="저장", width=10, command=self.save_style, bg="#28a745", fg="white").pack(side="left",
                                                                                                          padx=5)

        size_menu = tk.Frame(top, bg="#2b2b2b")
        size_menu.pack(side="right", padx=10)

        tk.Label(size_menu, text="창 크기:", bg="#2b2b2b", fg="white").pack(side="left")
        self.canvas_w_ent = tk.Entry(size_menu, width=5)
        self.canvas_w_ent.insert(0, "500")
        self.canvas_w_ent.pack(side="left", padx=2)
        tk.Label(size_menu, text="x", bg="#2b2b2b", fg="white").pack(side="left")
        self.canvas_h_ent = tk.Entry(size_menu, width=5)
        self.canvas_h_ent.insert(0, "400")
        self.canvas_h_ent.pack(side="left", padx=2)
        tk.Button(size_menu, text="적용", command=self.apply_canvas_size).pack(side="left", padx=5)

    def build_layout(self):
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)

        self.left = tk.Frame(main, width=220, bg="#eeeeee")
        self.left.pack(side="left", fill="y")

        self.center = tk.Frame(main, bg="#cccccc")
        self.center.pack(side="left", fill="both", expand=True)

        self.right = tk.Frame(main, width=280, bg="#f5f5f5")
        self.right.pack(side="right", fill="y")

        self.preview = tk.Frame(self.center, bg="white", width=500, height=400, relief="solid", bd=1)
        self.preview.place(relx=0.5, rely=0.5, anchor="center")

    def build_object_list(self):
        tk.Label(self.left, text="불러오기", bg="#ddd", font=("Arial", 10, "bold")).pack(fill="x", pady=(10, 0))
        self.style_listbox = tk.Listbox(self.left, height=10)
        self.style_listbox.pack(fill="x", padx=10, pady=5)
        self.style_listbox.bind("<<ListboxSelect>>", self.on_style_select)

        tk.Frame(self.left, height=2, bg="#bbb").pack(fill="x", pady=10)

        tk.Label(self.left, text="오브젝트 추가", bg="#eeeeee", font=("Arial", 11, "bold")).pack(pady=5)
        for name in OBJECT_SPECS:
            tk.Button(self.left, text=name, command=lambda n=name: self.create_object(n)).pack(fill="x", padx=15,
                                                                                               pady=3)

    def apply_canvas_size(self):
        try:
            w = int(self.canvas_w_ent.get())
            h = int(self.canvas_h_ent.get())
            self.preview.config(width=w, height=h)
        except ValueError:
            messagebox.showerror("오류", "숫자만 입력 가능합니다.")

    def create_object(self, name, loaded_data=None):
        cls = OBJECT_SPECS[name]["class"]

        if name == "ProgressBar":
            w = cls(self.preview, length=150)
        elif name == "Entry":
            w = cls(self.preview)
        elif name == "ImageLabel":
            w = cls(self.preview, text="[ Drop Image ]", relief="solid", bd=1)
            w.drop_target_register(DND_FILES)
            w.dnd_bind('<<Drop>>', lambda e: self.handle_image_drop(e, w))
        else:
            txt = loaded_data.get("text", name) if loaded_data else name
            w = cls(self.preview, text=txt)

        x, y = (loaded_data.get("x", 50), loaded_data.get("y", 50)) if loaded_data else (50, 50)
        w.place(x=x, y=y)
        w.bind("<Button-1>", self.start_drag)
        w.bind("<B1-Motion>", self.dragging)

        if loaded_data:
            self.widget_data[w] = loaded_data
            if loaded_data.get("image_path"):
                self.load_image_to_widget(w, loaded_data["image_path"])
            self.select_widget(w, name)
            for k, v in loaded_data.items():
                self.apply_property(k, v)
        else:
            self.widget_data[w] = {
                "type": name, "name": f"{name.lower()}_{len(self.widget_data) + 1}",
                "x": x, "y": y, "width": 120, "height": 30, "font_size": 10, "bold": False, "image_path": ""
            }
            if name == "ImageLabel":
                self.widget_data[w].update({"width": 100, "height": 100})
            self.select_widget(w, name)

    def handle_image_drop(self, event, widget):
        file_path = event.data.strip('{}')
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            self.widget_data[widget]["image_path"] = file_path
            self.load_image_to_widget(widget, file_path)
        else:
            messagebox.showwarning("지원 안 함", "이미지 파일만 드롭해주세요.")

    def load_image_to_widget(self, widget, path):
        try:
            data = self.widget_data[widget]
            w, h = int(data.get("width", 100)), int(data.get("height", 100))
            img = Image.open(path)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            widget.config(image=photo, text="")
            self.image_refs[widget] = photo
        except Exception as e:
            print(f"Image Load Error: {e}")

    def delete_current_widget(self):
        """현재 선택된 위젯을 삭제"""
        if self.current_widget:
            # 데이터 제거
            if self.current_widget in self.widget_data:
                del self.widget_data[self.current_widget]
            if self.current_widget in self.image_refs:
                del self.image_refs[self.current_widget]

            # 위젯 제거 및 속성창 초기화
            self.current_widget.destroy()
            self.current_widget = None
            self.current_type = None
            self.build_property_panel()

    def save_style(self):
        if not self.current_widget:
            messagebox.showwarning("오류", "선택된 오브젝트가 없습니다.")
            return
        data = self.widget_data[self.current_widget]
        name = data.get("name", "").strip()
        if not name:
            messagebox.showwarning("오류", "오브젝트 이름을 입력해주세요.")
            return

        style_dir = os.path.join(os.path.dirname(__file__), "styles")
        os.makedirs(style_dir, exist_ok=True)

        style = {"type": self.current_type, "props": data}
        with open(os.path.join(style_dir, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(style, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("저장", f"{name}.json 저장 완료")
        self.refresh_style_list()

    def refresh_style_list(self):
        self.style_listbox.delete(0, tk.END)
        style_dir = os.path.join(os.path.dirname(__file__), "styles")
        if os.path.exists(style_dir):
            for f in os.listdir(style_dir):
                if f.endswith(".json"): self.style_listbox.insert(tk.END, f.replace(".json", ""))

    def on_style_select(self, event):
        sel = self.style_listbox.curselection()
        if not sel: return

        # 선택한 파일 이름 가져오기
        filename = self.style_listbox.get(sel[0])
        style_dir = os.path.join(os.path.dirname(__file__), "styles")
        path = os.path.join(style_dir, f"{filename}.json")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 중요: 새로 불러오기 전에 캔버스를 깨끗이 비워줍니다.
            for child in self.preview.winfo_children():
                child.destroy()
            self.widget_data.clear()
            self.image_refs.clear()

            # 저장된 데이터로 오브젝트 복구
            self.create_object(data["type"], loaded_data=data["props"])

        except Exception as e:
            print(f"Error details: {e}")  # 터미널에서 구체적인 에러 확인용
            messagebox.showerror("오류", f"파일을 불러오지 못했습니다.\n{e}")

    def apply_property(self, key, val):
        if not self.current_widget: return
        data = self.widget_data[self.current_widget]
        data[key] = val
        try:
            if key == "text" and "text" in self.current_widget.config():
                self.current_widget.config(text=val)
            elif key in ("width", "height"):
                if self.current_type == "ProgressBar" and key == "width":
                    self.current_widget.config(length=int(val))
                else:
                    self.current_widget.place_configure(**{key: int(val)})
                if self.current_type == "ImageLabel" and data.get("image_path"):
                    self.load_image_to_widget(self.current_widget, data["image_path"])
            elif key in ("bg", "fg") and self.current_type != "ProgressBar":
                self.current_widget.config(**{key: val})
            elif key in ("font_size", "bold") and "font" in self.current_widget.config():
                size = int(data.get("font_size", 10))
                weight = "bold" if data.get("bold") else "normal"
                self.current_widget.config(font=("Arial", size, weight))
        except:
            pass

    def start_drag(self, event):
        self.drag_offset_x, self.drag_offset_y = event.x, event.y
        self.select_widget(event.widget, self.widget_data[event.widget]["type"])

    def dragging(self, event):
        x = event.x_root - self.preview.winfo_rootx() - self.drag_offset_x
        y = event.y_root - self.preview.winfo_rooty() - self.drag_offset_y
        event.widget.place(x=x, y=y)
        self.widget_data[event.widget].update({"x": x, "y": y})

    def select_widget(self, widget, wtype):
        self.current_widget, self.current_type = widget, wtype
        self.build_property_panel()

    def build_property_panel(self):
        for c in self.right.winfo_children(): c.destroy()
        if not self.current_widget:
            tk.Label(self.right, text="선택된 오브젝트 없음", fg="gray", bg="#f5f5f5").pack(expand=True)
            return

        tk.Label(self.right, text=f"속성 ({self.current_type})", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(pady=10)
        data = self.widget_data[self.current_widget]

        self.make_entry("오브젝트 이름 (스타일명)", "name", data)
        for p in OBJECT_SPECS[self.current_type]["props"]:
            if p in ("text", "width", "height", "font_size"):
                self.make_entry(p.upper(), p, data)
            elif p in ("bg", "fg"):
                self.make_color(p.upper(), p, data)
            elif p == "bold":
                self.make_bold(data)

        # 삭제 버튼 추가
        tk.Frame(self.right, height=2, bg="#ddd").pack(fill="x", pady=20)
        tk.Button(self.right, text="오브젝트 삭제", bg="#dc3545", fg="white",
                  command=self.delete_current_widget).pack(fill="x", padx=20)

    def make_entry(self, label, key, data):
        tk.Label(self.right, text=label, bg="#f5f5f5").pack(anchor="w", padx=10)
        ent = tk.Entry(self.right)
        ent.pack(fill="x", padx=10, pady=2)
        ent.insert(0, str(data.get(key, "")))
        ent.bind("<KeyRelease>", lambda e: self.apply_property(key, ent.get()))

    def make_color(self, label, key, data):
        tk.Button(self.right, text=f"색상 선택: {label}", command=lambda: self.pick_color(key)).pack(fill="x", padx=10,
                                                                                                 pady=4)

    def pick_color(self, key):
        c = colorchooser.askcolor()[1]
        if c: self.apply_property(key, c)

    def make_bold(self, data):
        var = tk.BooleanVar(value=data.get("bold", False))
        tk.Checkbutton(self.right, text="Bold (굵게)", variable=var, bg="#f5f5f5",
                       command=lambda: self.apply_property("bold", var.get())).pack(anchor="w", padx=10)

    def new_design(self):
        if messagebox.askyesno("새로 만들기", "캔버스를 비우겠습니까?"):
            for child in self.preview.winfo_children(): child.destroy()
            self.widget_data.clear()
            self.image_refs.clear()
            self.current_widget = None
            self.build_property_panel()

    def start(self):
        self.root.mainloop()


if __name__ == "__main__":

    root = TkinterDnD.Tk()

    app = DesignerApp(root)


    app.start()