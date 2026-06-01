import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys

# Try importing markitdown
try:
    from markitdown import MarkItDown
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markitdown[all]"])
    from markitdown import MarkItDown

# Try tkinterdnd2 for drag & drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# ── Colors ──────────────────────────────────────────────────────────────────
BG        = "#0f0f0f"
SURFACE   = "#1a1a1a"
SURFACE2  = "#242424"
BORDER    = "#2e2e2e"
ACCENT    = "#4f8ef7"
ACCENT2   = "#6fa3ff"
TEXT      = "#f0f0f0"
MUTED     = "#888888"
SUCCESS   = "#4caf82"
ERROR     = "#e05c5c"
WARNING   = "#e0a550"
FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_BIG  = ("Segoe UI", 13, "bold")
FONT_MONO = ("Consolas", 9)


class MarkItDownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MarkItDown GUI")
        self.root.geometry("860x660")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG)

        self.md_engine = MarkItDown()
        self.files = []       # list of file paths
        self.results = {}     # path -> {"md": ..., "error": ...}
        self.active_file = None
        self.converting = False

        self._build_ui()
        self._style_ttk()

    # ── UI Build ─────────────────────────────────────────────────────────────

    def _style_ttk(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TScrollbar", background=SURFACE2, troughcolor=SURFACE,
                         bordercolor=BORDER, arrowcolor=MUTED, relief="flat")
        style.configure("Vertical.TScrollbar", width=8)

    def _build_ui(self):
        # ── Header ─────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG, pady=0)
        hdr.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(hdr, text="MarkItDown", font=("Segoe UI", 18, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(hdr, text="  File → Markdown converter", font=("Segoe UI", 11),
                 bg=BG, fg=MUTED).pack(side="left", pady=(4, 0))

        # ── Drop Zone ──────────────────────────────────────────────────────
        self.drop_frame = tk.Frame(self.root, bg=SURFACE, bd=0,
                                   highlightthickness=2,
                                   highlightbackground=BORDER,
                                   highlightcolor=ACCENT)
        self.drop_frame.pack(fill="x", padx=20, pady=14)

        inner = tk.Frame(self.drop_frame, bg=SURFACE, pady=22)
        inner.pack(fill="x")

        tk.Label(inner, text="⬇  ফাইল এখানে ড্র্যাগ করো  ⬇",
                 font=("Segoe UI", 13, "bold"), bg=SURFACE, fg=ACCENT).pack()
        tk.Label(inner,
                 text="PDF · DOCX · PPTX · XLSX · CSV · JSON · HTML · TXT · EPUB · Images",
                 font=("Segoe UI", 9), bg=SURFACE, fg=MUTED).pack(pady=(4, 0))

        browse_btn = tk.Button(inner, text="  ফাইল বেছে নাও  ",
                               font=FONT_BOLD, bg=ACCENT, fg="#fff",
                               relief="flat", bd=0, padx=14, pady=6,
                               cursor="hand2", activebackground=ACCENT2,
                               activeforeground="#fff",
                               command=self._browse_files)
        browse_btn.pack(pady=(12, 0))

        # Register DnD if available
        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)
            inner.drop_target_register(DND_FILES)
            inner.dnd_bind("<<Drop>>", self._on_drop)

        # ── Main area (file list + output) ─────────────────────────────────
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        # Left: file list
        left = tk.Frame(main, bg=SURFACE, width=220,
                        highlightthickness=1, highlightbackground=BORDER)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        lhdr = tk.Frame(left, bg=SURFACE2, pady=7)
        lhdr.pack(fill="x")
        tk.Label(lhdr, text="ফাইল তালিকা", font=FONT_BOLD,
                 bg=SURFACE2, fg=TEXT).pack(side="left", padx=10)
        tk.Button(lhdr, text="✕ সব মুছো", font=("Segoe UI", 8),
                  bg=SURFACE2, fg=MUTED, relief="flat", bd=0,
                  cursor="hand2", activebackground=SURFACE,
                  command=self._clear_all).pack(side="right", padx=8)

        self.list_canvas = tk.Canvas(left, bg=SURFACE, bd=0,
                                     highlightthickness=0)
        list_scroll = ttk.Scrollbar(left, orient="vertical",
                                    command=self.list_canvas.yview)
        self.list_canvas.configure(yscrollcommand=list_scroll.set)
        list_scroll.pack(side="right", fill="y")
        self.list_canvas.pack(side="left", fill="both", expand=True)

        self.list_inner = tk.Frame(self.list_canvas, bg=SURFACE)
        self.list_canvas.create_window((0, 0), window=self.list_inner,
                                       anchor="nw", tags="inner")
        self.list_inner.bind("<Configure>",
            lambda e: self.list_canvas.configure(
                scrollregion=self.list_canvas.bbox("all")))

        # Right: output
        right = tk.Frame(main, bg=SURFACE,
                         highlightthickness=1, highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True)

        # Output toolbar
        otb = tk.Frame(right, bg=SURFACE2, pady=7)
        otb.pack(fill="x")
        self.out_label = tk.Label(otb, text="আউটপুট", font=FONT_BOLD,
                                  bg=SURFACE2, fg=TEXT)
        self.out_label.pack(side="left", padx=10)

        btn_cfg = dict(font=("Segoe UI", 8), bg=SURFACE2, fg=MUTED,
                       relief="flat", bd=0, cursor="hand2",
                       activebackground=SURFACE)
        tk.Button(otb, text="📋 কপি", activeforeground=TEXT,
                  command=self._copy_output, **btn_cfg).pack(side="right", padx=4)
        tk.Button(otb, text="💾 সেভ করো", activeforeground=TEXT,
                  command=self._save_output, **btn_cfg).pack(side="right", padx=4)
        tk.Button(otb, text="🗑 মুছো", activeforeground=TEXT,
                  command=self._clear_output, **btn_cfg).pack(side="right", padx=4)

        # Text area
        txt_frame = tk.Frame(right, bg=SURFACE)
        txt_frame.pack(fill="both", expand=True)

        self.output_text = tk.Text(
            txt_frame, bg=SURFACE, fg=TEXT, font=FONT_MONO,
            bd=0, relief="flat", wrap="word",
            insertbackground=TEXT, selectbackground=ACCENT,
            padx=12, pady=10, state="disabled"
        )
        out_scroll = ttk.Scrollbar(txt_frame, orient="vertical",
                                   command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=out_scroll.set)
        out_scroll.pack(side="right", fill="y")
        self.output_text.pack(side="left", fill="both", expand=True)

        self._set_output_placeholder()

        # ── Bottom bar ─────────────────────────────────────────────────────
        bot = tk.Frame(self.root, bg=SURFACE2,
                       highlightthickness=1, highlightbackground=BORDER)
        bot.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar(value="প্রস্তুত")
        tk.Label(bot, textvariable=self.status_var, font=("Segoe UI", 9),
                 bg=SURFACE2, fg=MUTED).pack(side="left", padx=14, pady=6)

        self.convert_btn = tk.Button(
            bot, text="  ▶  Convert করো  ",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT, fg="#fff", relief="flat", bd=0,
            padx=16, pady=6, cursor="hand2",
            activebackground=ACCENT2, activeforeground="#fff",
            command=self._start_convert
        )
        self.convert_btn.pack(side="right", padx=14, pady=6)

        self.progress = ttk.Progressbar(bot, length=140, mode="indeterminate")
        self.progress.pack(side="right", padx=(0, 8), pady=8)

    # ── File Handling ────────────────────────────────────────────────────────

    def _browse_files(self):
        paths = filedialog.askopenfilenames(
            title="ফাইল বেছে নাও",
            filetypes=[
                ("সব সাপোর্টেড ফাইল",
                 "*.pdf *.docx *.pptx *.xlsx *.xls *.csv *.json *.xml "
                 "*.html *.htm *.txt *.md *.epub *.zip *.jpg *.jpeg *.png *.gif *.webp"),
                ("সব ফাইল", "*.*")
            ]
        )
        if paths:
            self._add_files(list(paths))

    def _on_drop(self, event):
        raw = event.data
        # tkinterdnd2 returns paths wrapped in braces for paths with spaces
        import re
        paths = re.findall(r'\{[^}]+\}|[^\s]+', raw)
        paths = [p.strip("{}") for p in paths]
        self._add_files(paths)

    def _add_files(self, paths):
        added = 0
        for p in paths:
            p = p.strip()
            if p and os.path.isfile(p) and p not in self.files:
                self.files.append(p)
                added += 1
        if added:
            self._render_file_list()
            self.status_var.set(f"{len(self.files)} টি ফাইল লোড হয়েছে")

    def _clear_all(self):
        self.files.clear()
        self.results.clear()
        self.active_file = None
        self._render_file_list()
        self._set_output_placeholder()
        self.status_var.set("সব মুছে গেছে")

    def _remove_file(self, path):
        if path in self.files:
            self.files.remove(path)
        self.results.pop(path, None)
        if self.active_file == path:
            self.active_file = None
            self._set_output_placeholder()
        self._render_file_list()

    # ── File List Rendering ──────────────────────────────────────────────────

    def _ext_icon(self, path):
        ext = os.path.splitext(path)[1].lower()
        icons = {
            ".pdf": "📄", ".docx": "📝", ".doc": "📝",
            ".pptx": "📊", ".ppt": "📊",
            ".xlsx": "📈", ".xls": "📈", ".csv": "📋",
            ".json": "{ }", ".xml": "</>", ".html": "🌐", ".htm": "🌐",
            ".txt": "📃", ".md": "✍", ".epub": "📚",
            ".zip": "🗜", ".jpg": "🖼", ".jpeg": "🖼",
            ".png": "🖼", ".gif": "🖼", ".webp": "🖼",
        }
        return icons.get(ext, "📁")

    def _render_file_list(self):
        for w in self.list_inner.winfo_children():
            w.destroy()

        if not self.files:
            tk.Label(self.list_inner, text="কোনো ফাইল নেই",
                     font=("Segoe UI", 9), bg=SURFACE, fg=MUTED,
                     pady=20).pack()
            return

        for path in self.files:
            name = os.path.basename(path)
            r = self.results.get(path)
            if r is None:
                color, dot = MUTED, "○"
            elif "error" in r:
                color, dot = ERROR, "✕"
            else:
                color, dot = SUCCESS, "✓"

            is_active = (path == self.active_file)
            bg = SURFACE2 if is_active else SURFACE

            row = tk.Frame(self.list_inner, bg=bg, pady=5,
                           highlightthickness=0, cursor="hand2")
            row.pack(fill="x", padx=0, pady=1)

            tk.Label(row, text=self._ext_icon(path),
                     font=("Segoe UI", 11), bg=bg, fg=TEXT,
                     width=3).pack(side="left", padx=(6, 0))

            info = tk.Frame(row, bg=bg)
            info.pack(side="left", fill="x", expand=True, padx=4)
            disp = name if len(name) <= 22 else name[:20] + "…"
            tk.Label(info, text=disp, font=("Segoe UI", 8, "bold"),
                     bg=bg, fg=TEXT, anchor="w").pack(fill="x")
            sz = os.path.getsize(path)
            size_str = f"{sz/1024:.1f} KB" if sz < 1048576 else f"{sz/1048576:.1f} MB"
            tk.Label(info, text=size_str, font=("Segoe UI", 7),
                     bg=bg, fg=MUTED, anchor="w").pack(fill="x")

            tk.Label(row, text=dot, font=("Segoe UI", 10, "bold"),
                     bg=bg, fg=color, width=2).pack(side="left")

            tk.Button(row, text="✕", font=("Segoe UI", 8),
                      bg=bg, fg=MUTED, relief="flat", bd=0,
                      cursor="hand2", activebackground=SURFACE2,
                      command=lambda p=path: self._remove_file(p)
                      ).pack(side="right", padx=4)

            row.bind("<Button-1>", lambda e, p=path: self._show_result(p))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, p=path: self._show_result(p))

    # ── Conversion ───────────────────────────────────────────────────────────

    def _start_convert(self):
        if self.converting:
            return
        pending = [f for f in self.files if f not in self.results or "error" in self.results[f]]
        if not pending:
            messagebox.showinfo("MarkItDown", "সব ফাইল ইতিমধ্যে convert হয়েছে!")
            return
        if not self.files:
            messagebox.showwarning("MarkItDown", "আগে ফাইল যোগ করো।")
            return
        self.converting = True
        self.convert_btn.configure(state="disabled", bg="#333")
        self.progress.start(10)
        threading.Thread(target=self._convert_worker, args=(pending,),
                         daemon=True).start()

    def _convert_worker(self, pending):
        for i, path in enumerate(pending):
            name = os.path.basename(path)
            self.root.after(0, lambda n=name, i=i, t=len(pending):
                self.status_var.set(f"Converting {i+1}/{t}: {n}"))
            try:
                result = self.md_engine.convert(path)
                self.results[path] = {"md": result.text_content}
            except Exception as e:
                self.results[path] = {"error": str(e)}
            self.root.after(0, self._render_file_list)

        self.root.after(0, self._on_convert_done)

    def _on_convert_done(self):
        self.converting = False
        self.progress.stop()
        self.convert_btn.configure(state="normal", bg=ACCENT)
        done = sum(1 for r in self.results.values() if "md" in r)
        errs = sum(1 for r in self.results.values() if "error" in r)
        self.status_var.set(f"সম্পন্ন — {done} টি সফল, {errs} টি ব্যর্থ")
        # Auto-show first successful result
        for f in self.files:
            if f in self.results and "md" in self.results[f]:
                self._show_result(f)
                break

    # ── Output ───────────────────────────────────────────────────────────────

    def _show_result(self, path):
        self.active_file = path
        self._render_file_list()
        r = self.results.get(path)
        if r is None:
            self._set_output("এই ফাইল এখনো convert হয়নি।\n\nনিচে 'Convert করো' বাটন চাপো।",
                             color=MUTED)
            return
        if "error" in r:
            self._set_output(f"❌ Error:\n\n{r['error']}", color=ERROR)
            self.out_label.configure(fg=ERROR)
            return
        self._set_output(r["md"], color=TEXT)
        self.out_label.configure(
            text=f"আউটপুট — {os.path.basename(path)}", fg=TEXT)

    def _set_output(self, text, color=TEXT):
        self.output_text.configure(state="normal", fg=color)
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")

    def _set_output_placeholder(self):
        self._set_output("ফাইল যোগ করো এবং 'Convert করো' চাপো।\nআউটপুট এখানে দেখা যাবে।",
                         color=MUTED)
        self.out_label.configure(text="আউটপুট", fg=TEXT)

    def _copy_output(self):
        text = self.output_text.get("1.0", "end").strip()
        if not text or text == "ফাইল যোগ করো এবং 'Convert করো' চাপো।\nআউটপুট এখানে দেখা যাবে।":
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("ক্লিপবোর্ডে কপি হয়েছে ✓")

    def _save_output(self):
        if not self.active_file:
            messagebox.showwarning("MarkItDown", "আগে একটি ফাইল সিলেক্ট করো।")
            return
        r = self.results.get(self.active_file)
        if not r or "md" not in r:
            return
        base = os.path.splitext(os.path.basename(self.active_file))[0]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            initialfile=base + ".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("সব ফাইল", "*.*")]
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(r["md"])
            self.status_var.set(f"সেভ হয়েছে: {os.path.basename(save_path)} ✓")

    def _clear_output(self):
        self._set_output_placeholder()
        self.active_file = None
        self._render_file_list()


# ── Entry Point ──────────────────────────────────────────────────────────────

def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    root.tk_setPalette(background=BG)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = MarkItDownApp(root)

    if not HAS_DND:
        # Show one-time notice
        root.after(500, lambda: messagebox.showinfo(
            "Drag & Drop",
            "Drag & Drop সুবিধার জন্য একবার এটা run করো:\n\n"
            "pip install tkinterdnd2\n\n"
            "এখন 'ফাইল বেছে নাও' বাটন দিয়ে কাজ করো।"
        ))

    root.mainloop()


if __name__ == "__main__":
    main()
