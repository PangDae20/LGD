"""[GUI · For Demo] 실물 칩 대신 쓰는 DUT RTL 보기 (demo_dut/rtl)."""
import os
import tkinter as tk
from tkinter import ttk

from core import workspace as ws
from core.pipeline import demo_top, dut_byte_order_hint
from core.sim_runner import locate_iverilog

from .widgets import CodeView


def demo_banner(parent, text):
    """For Demo 영역 표시 배너"""
    b = tk.Frame(parent, background="#ffe8cc", highlightbackground="#e69138", highlightthickness=1)
    b.pack(fill="x", pady=(0, 4))
    tk.Label(b, text="FOR DEMO", background="#e69138", foreground="white",
             font=("Malgun Gothic", 9, "bold"), padx=6).pack(side="left", fill="y")
    tk.Label(b, text=text, background="#ffe8cc", foreground="#7a3e00", anchor="w", justify="left",
             font=("Malgun Gothic", 9), wraplength=470).pack(side="left", fill="x", padx=6, pady=3)
    return b


class DemoDutPanel:
    def _build_dut_tab(self, f):
        demo_banner(f, "실제 업무에서는 변환한 SPI/I2C 벡터를 장비로 실물 칩에 인가한다. "
                       "여기서는 칩 대신 이 RTL을 시뮬레이터로 돌린다.")
        row = ttk.Frame(f)
        row.pack(fill="x")
        self.lb_dut = tk.Listbox(row, height=5, font=("Consolas", 10), exportselection=False)
        self.lb_dut.pack(side="left", fill="x", expand=True)
        self.lb_dut.bind("<<ListboxSelect>>", lambda e: self._show_dut())
        side = ttk.Frame(row)
        side.pack(side="left", padx=6, anchor="n")
        ttk.Button(side, text="DUT RTL 가져오기", command=lambda: self._import("dut")).pack(fill="x")
        self.lbl_dut = ttk.Label(f, text="", foreground="#0050a0", wraplength=640, justify="left")
        self.lbl_dut.pack(anchor="w", pady=2)
        self.dut_code = CodeView(f)
        self.dut_code.pack(fill="both", expand=True)

    def _fill_dut(self):
        self.lb_dut.delete(0, "end")
        self.dut_code.txt.configure(state="normal")
        self.dut_code.txt.delete("1.0", "end")
        if not self.ip_dir:
            return
        files = ws.list_dut(self.ip_dir)
        for fn in files:
            self.lb_dut.insert("end", fn)
        if not files:
            self.lbl_dut.configure(text=f"{ws.DEMO_DUT} 가 비어 있음 → Demo는 Python 모델로만 실행 가능")
            return
        t = locate_iverilog()
        hint = dut_byte_order_hint(self.ip_dir)
        self.lbl_dut.configure(text=f"top = {demo_top(self.ip_dir)}   |   DUT 바이트 순서 파라미터 = {hint or '없음'}"
                                    f"   |   시뮬레이터 = {t[2] if t else '없음 (Python 모델 사용)'}")
        pref = next((i for i, f in enumerate(files) if "reg" in f), 0)
        self.lb_dut.selection_set(pref)
        self._show_dut()

    def _show_dut(self):
        sel = self.lb_dut.curselection()
        if sel:
            rel = self.lb_dut.get(sel[0])
            self.dut_code.show(os.path.join(self.ip_dir, rel), rel)
