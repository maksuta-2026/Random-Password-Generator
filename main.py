import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import json
import os
import string
from datetime import datetime

HISTORY_FILE = "history.json"
MIN_LEN = 4
MAX_LEN = 128

class PasswordGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Random Password Generator")
        self.geometry("720x480")
        self.resizable(False, False)
        self.history = []  # list of {"pw","length","chars","time"}
        self._load_history()
        self._build_ui()
        self._refresh_history()

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # Controls frame
        ctrl = ttk.LabelFrame(main, text="Параметры", padding=10)
        ctrl.pack(fill="x")

        # length slider
        ttk.Label(ctrl, text="Длина:").grid(row=0, column=0, sticky="w")
        self.length_var = tk.IntVar(value=12)
        length_slider = ttk.Scale(ctrl, from_=MIN_LEN, to=MAX_LEN, orient="horizontal",
                                  command=lambda v: self.length_var.set(int(float(v))))
        length_slider.set(12)
        length_slider.grid(row=0, column=1, sticky="we", padx=6)
        self.length_label = ttk.Label(ctrl, textvariable=self.length_var, width=4)
        self.length_label.grid(row=0, column=2, padx=(6,0))

        # checkboxes
        self.use_lower = tk.BooleanVar(value=True)
        self.use_upper = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=False)

        cb_frame = ttk.Frame(ctrl)
        cb_frame.grid(row=1, column=0, columnspan=3, pady=(8,0), sticky="w")

        ttk.Checkbutton(cb_frame, text="Lowercase (a-z)", variable=self.use_lower).grid(row=0, column=0, padx=4, sticky="w")
        ttk.Checkbutton(cb_frame, text="Uppercase (A-Z)", variable=self.use_upper).grid(row=0, column=1, padx=4, sticky="w")
        ttk.Checkbutton(cb_frame, text="Digits (0-9)", variable=self.use_digits).grid(row=0, column=2, padx=4, sticky="w")
        ttk.Checkbutton(cb_frame, text="Symbols (!@#...) ", variable=self.use_symbols).grid(row=0, column=3, padx=4, sticky="w")

        # generate button and output
        out_frame = ttk.Frame(main, padding=(0,10))
        out_frame.pack(fill="x")

        gen_btn = ttk.Button(out_frame, text="Сгенерировать", command=self.generate_password)
        gen_btn.grid(row=0, column=0, sticky="w")

        copy_btn = ttk.Button(out_frame, text="Копировать", command=self.copy_to_clipboard)
        copy_btn.grid(row=0, column=1, sticky="w", padx=(8,0))

        ttk.Label(out_frame, text="Пароль:").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.pw_var = tk.StringVar()
        pw_entry = ttk.Entry(out_frame, textvariable=self.pw_var, font=("Consolas", 12), width=50)
        pw_entry.grid(row=1, column=1, columnspan=3, sticky="w", padx=(6,0), pady=(8,0))
        pw_entry.bind("<Return>", lambda e: self.generate_password())

        # history table
        hist_frame = ttk.LabelFrame(main, text="История", padding=8)
        hist_frame.pack(fill="both", expand=True, pady=(8,0))

        cols = ("pw", "length", "chars", "time")
        self.tree = ttk.Treeview(hist_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("pw", text="Пароль")
        self.tree.heading("length", text="Дл.")
        self.tree.heading("chars", text="Символы")
        self.tree.heading("time", text="Время")
        self.tree.column("pw", width=350)
        self.tree.column("length", width=50, anchor="center")
        self.tree.column("chars", width=150)
        self.tree.column("time", width=140)

        vsb = ttk.Scrollbar(hist_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, side="left")

        # history buttons
        btns = ttk.Frame(main)
        btns.pack(fill="x", pady=(8,0))

        del_btn = ttk.Button(btns, text="Удалить выбранный", command=self.delete_selected)
        del_btn.pack(side="left")

        save_btn = ttk.Button(btns, text="Сохранить историю", command=self._save_history)
        save_btn.pack(side="right")

        load_btn = ttk.Button(btns, text="Загрузить историю...", command=self._load_from_dialog)
        load_btn.pack(side="right", padx=(0,8))

    def _build_charset(self):
        chars = ""
        if self.use_lower.get():
            chars += string.ascii_lowercase
        if self.use_upper.get():
            chars += string.ascii_uppercase
        if self.use_digits.get():
            chars += string.digits
        if self.use_symbols.get():
            # choose a safe subset of punctuation
            chars += "!@#$%^&*()-_=+[]{};:,.<>/?"
        return chars

    def generate_password(self):
        length = self.length_var.get()
        if not (MIN_LEN <= length <= MAX_LEN):
            messagebox.showwarning("Ошибка", f"Длина должна быть от {MIN_LEN} до {MAX_LEN}.")
            return
        charset = self._build_charset()
        if not charset:
            messagebox.showwarning("Ошибка", "Выберите хотя бы один набор символов.")
            return

        # ensure at least one character from each selected category for better strength
        parts = []
        categories = []
        if self.use_lower.get(): categories.append(string.ascii_lowercase)
        if self.use_upper.get(): categories.append(string.ascii_uppercase)
        if self.use_digits.get(): categories.append(string.digits)
        if self.use_symbols.get(): categories.append("!@#$%^&*()-_=+[]{};:,.<>/?")

        # if length < number of categories, just random choose
        if length >= len(categories):
            for cat in categories:
                parts.append(random.choice(cat))
            remaining = length - len(parts)
            parts += [random.choice(charset) for _ in range(remaining)]
            random.shuffle(parts)
            pw = "".join(parts)
        else:
            pw = "".join(random.choice(charset) for _ in range(length))

        self.pw_var.set(pw)
        record = {
            "pw": pw,
            "length": length,
            "chars": self._chars_description(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.insert(0, record)  # newest first
        self._refresh_history()
        self._save_history(autosave=True)

    def _chars_description(self):
        parts = []
        if self.use_lower.get(): parts.append("lower")
        if self.use_upper.get(): parts.append("upper")
        if self.use_digits.get(): parts.append("digits")
        if self.use_symbols.get(): parts.append("symbols")
        return ",".join(parts) if parts else "none"

    def copy_to_clipboard(self):
        pw = self.pw_var.get()
        if not pw:
            return
        self.clipboard_clear()
        self.clipboard_append(pw)
        messagebox.showinfo("Скопировано", "Пароль скопирован в буфер обмена.")

    def _refresh_history(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for rec in self.history:
            self.tree.insert("", "end", values=(rec["pw"], rec["length"], rec["chars"], rec["time"]))

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        # tree displayed newest first, same as history list
        try:
            del self.history[idx]
            self._refresh_history()
            self._save_history(autosave=True)
        except Exception:
            pass

    def _load_history(self):
        if not os.path.exists(HISTORY_FILE):
            self.history = []
            return
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # validate simple schema
            out = []
            for item in data:
                pw = str(item.get("pw",""))
                length = int(item.get("length",0)) if item.get("length",0) else 0
                chars = str(item.get("chars",""))
                time = str(item.get("time",""))
                if pw and length>0:
                    out.append({"pw":pw,"length":length,"chars":chars,"time":time})
            self.history = out
        except Exception:
            self.history = []

    def _save_history(self, autosave=False):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            if not autosave:
                messagebox.showinfo("Сохранено", f"История сохранена в {HISTORY_FILE}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {e}")

    def _load_from_dialog(self):
        path = filedialog.askopenfilename(title="Выберите JSON файл", filetypes=[("JSON files","*.json"),("All files","*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            added = 0
            for item in data:
                pw = str(item.get("pw",""))
                try:
                    length = int(item.get("length",0))
                except Exception:
                    continue
                chars = str(item.get("chars",""))
                time = str(item.get("time",""))
                if pw and length>0:
                    self.history.insert(0, {"pw":pw,"length":length,"chars":chars,"time":time})
                    added += 1
            if added:
                self._refresh_history()
                self._save_history(autosave=True)
                messagebox.showinfo("Загрузка", f"Добавлено {added} записей в историю.")
            else:
                messagebox.showinfo("Загрузка", "В файле нет подходящих записей.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")

if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()
