"""GUI 공용 도구: 폴더 열기, Verilog 미리보기(줄 번호 + 문법 색칠)."""
import os
import re
import subprocess
import sys
import tkinter as tk
import webbrowser
from tkinter import ttk

KEYWORDS = r"\b(module|endmodule|input|output|inout|wire|reg|integer|parameter|localparam|assign|always|initial|" \
           r"begin|end|if|else|case|endcase|default|posedge|negedge|or|and|not|task|endtask|function|endfunction|" \
           r"for|while|generate|endgenerate|genvar|tri1|tri|timescale)\b"
RE_TASK = re.compile(r"\b(chip_reset|reg_write|reg_read|frame_check)\b")
RE_KW = re.compile(KEYWORDS)
RE_NUM = re.compile(r"\b\d*'[sS]?[hHbBdD][0-9a-fA-F_xXzZ]+\b|\b\d+\b")
RE_STR = re.compile(r'"[^"\n]*"')
RE_DIR = re.compile(r"`\w+")


def _is_regdef(ln: str) -> bool:
    code = ln.split("//", 1)[0]
    return "localparam" in code and "ADDR_" in code


def open_path(p):
    if sys.platform.startswith("win"):
        os.startfile(p)  # noqa
    elif sys.platform == "darwin":
        subprocess.run(["open", p])
    else:
        webbrowser.open("file://" + os.path.abspath(p))


class CodeView(ttk.Frame):
    """읽기 전용 Verilog 뷰어. show(path), goto(line)"""

    def __init__(self, master, on_click=None, **kw):
        super().__init__(master, **kw)
        self.on_click = on_click
        self.title = ttk.Label(self, text="(파일을 선택하면 미리보기)", foreground="#0050a0")
        self.title.pack(anchor="w")
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.txt = tk.Text(body, font=("Consolas", 10), wrap="none", background="#fbfbfb", undo=False)
        sy = ttk.Scrollbar(body, command=self.txt.yview)
        sx = ttk.Scrollbar(body, orient="horizontal", command=self.txt.xview)
        self.txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.txt.pack(fill="both", expand=True)
        t = self.txt
        t.tag_configure("ln", foreground="#9a9a9a")
        t.tag_configure("kw", foreground="#0033b3")
        t.tag_configure("num", foreground="#1750eb")
        t.tag_configure("str", foreground="#067d17")
        t.tag_configure("dir", foreground="#9e880d")
        t.tag_configure("cmt", foreground="#8c8c8c")
        t.tag_configure("task", foreground="#a0329a", font=("Consolas", 10, "bold"))
        t.tag_configure("regdef", background="#fff6cc")          # 레지스터 정의 줄
        t.tag_configure("jump", background="#ffd27a")            # 이동한 줄
        t.tag_raise("jump")
        t.bind("<ButtonRelease-1>", self._click)
        self.path = None
        self.nlines = 0

    def show(self, path: str, rel: str = None):
        self.path = path
        t = self.txt
        t.configure(state="normal")
        t.delete("1.0", "end")
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except OSError as e:
            t.insert("end", str(e))
            t.configure(state="disabled")
            return
        self.nlines = len(lines)
        w = len(str(len(lines)))
        for i, ln in enumerate(lines, 1):
            t.insert("end", f"{i:>{w}} │ ", "ln")
            start = t.index("end-1c")
            t.insert("end", ln + "\n")
            self._highlight(i, len(f"{i:>{w}} │ "), ln)
            if _is_regdef(ln):
                t.tag_add("regdef", f"{i}.0", f"{i}.end")
        t.configure(state="disabled")
        nreg = sum(1 for ln in lines if _is_regdef(ln))
        self.title.configure(text=f"{rel or os.path.basename(path)}   ({len(lines)}줄"
                                  + (f", 레지스터 정의 {nreg}줄 노란색" if nreg else "") + ")")

    def _highlight(self, row, off, ln):
        t = self.txt
        code, _, cmt = ln.partition("//")
        for rx, tag in ((RE_KW, "kw"), (RE_NUM, "num"), (RE_STR, "str"), (RE_DIR, "dir"), (RE_TASK, "task")):
            for m in rx.finditer(code):
                t.tag_add(tag, f"{row}.{off + m.start()}", f"{row}.{off + m.end()}")
        if _ or cmt:
            c0 = off + len(code)
            t.tag_add("cmt", f"{row}.{c0}", f"{row}.end")

    def _click(self, _):
        if self.on_click:
            line = int(self.txt.index("insert").split(".")[0])
            self.on_click(line)

    def goto(self, line: int):
        t = self.txt
        t.tag_remove("jump", "1.0", "end")
        t.tag_add("jump", f"{line}.0", f"{line}.end")
        t.see(f"{max(line - 5, 1)}.0")
        t.see(f"{min(line + 8, max(self.nlines, 1))}.0")


class VectorView(ttk.Frame):
    """변환 결과(SPI/I2C) 표시. set(lines, srcs), mark_src(src) -> 해당 줄 강조, on_click(src)"""

    def __init__(self, master, on_click=None, **kw):
        super().__init__(master, **kw)
        self.on_click = on_click
        self.title = ttk.Label(self, text="변환 결과", foreground="#0050a0")
        self.title.pack(anchor="w")
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.txt = tk.Text(body, font=("Consolas", 9), wrap="none", background="#f7fbff")
        sy = ttk.Scrollbar(body, command=self.txt.yview)
        sx = ttk.Scrollbar(body, orient="horizontal", command=self.txt.xview)
        self.txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.txt.pack(fill="both", expand=True)
        self.txt.tag_configure("hdr", foreground="#7a7a7a")
        self.txt.tag_configure("sec", foreground="#7a3e00", font=("Consolas", 9, "bold"))
        self.txt.tag_configure("wr", foreground="#0b5394")
        self.txt.tag_configure("rd", foreground="#38761d")
        self.txt.tag_configure("jump", background="#ffd27a")
        self.txt.tag_raise("jump")
        self.txt.bind("<ButtonRelease-1>", self._click)
        self.srcs = []

    def set(self, title, lines, srcs):
        self.title.configure(text=title)
        t = self.txt
        t.configure(state="normal")
        t.delete("1.0", "end")
        for ln in lines:
            s = ln.strip()
            tag = "sec" if s.startswith("<!-- ##") else "hdr" if s.startswith(("<!--", "<?xml", "<aardvark", "</aardvark", "<configure", "<spi_config", "<spi_bitrate", "<i2c_bitrate")) else \
                  "rd" if ("expect" in s or "<i2c_read" in s or 'nostop="1"' in s) else "wr" if s.startswith(("<spi_write", "<i2c_write")) else None
            t.insert("end", ln + "\n", tag)
        t.configure(state="disabled")
        self.srcs = list(srcs)

    def message(self, title, text):
        self.set(title, [text], [None])

    def mark_src(self, src):
        t = self.txt
        t.tag_remove("jump", "1.0", "end")
        rows = [i + 1 for i, s in enumerate(self.srcs) if s == src]
        for r in rows:
            t.tag_add("jump", f"{r}.0", f"{r}.end")
        if rows:
            t.see(f"{rows[-1]}.0")
            t.see(f"{rows[0]}.0")
        return len(rows)

    def _click(self, _):
        row = int(self.txt.index("insert").split(".")[0])
        if self.on_click and 0 < row <= len(self.srcs) and self.srcs[row - 1]:
            self.mark_src(self.srcs[row - 1])
            self.on_click(self.srcs[row - 1])
