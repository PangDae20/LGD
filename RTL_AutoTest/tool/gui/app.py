"""[GUI] 메인 창.

왼쪽  (툴 본 기능)  테스트벡터 RTL → SPI / I2C 변환, 레지스터맵
오른쪽 (For Demo)   실물 칩 + 장비 대신 DUT RTL 시뮬레이션으로 인가·판정 — 툴바 체크박스로 보이기/숨기기

패널 파일
  panel_convert.py   IP 선택·생성, 테스트벡터 RTL 미리보기 ↔ SPI/I2C 변환 결과
  panel_regmap.py    ① 레지스터맵 추출·편집·저장
  panel_results.py   [For Demo] ③ 인가·판정, 화면 비교, 기대값 지정
  panel_demo_dut.py  [For Demo] DUT RTL 보기, Demo 배너
  panel_manual.py    [For Demo] 수동 R/W
  widgets.py         코드/벡터 뷰어, 폴더 열기
"""
import queue
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from core import workspace as ws
from core.sim_runner import find_iverilog

from .panel_convert import ConvertPanel
from .panel_demo_dut import DemoDutPanel, demo_banner
from .panel_manual import ManualPanel
from .panel_regmap import RegmapPanel
from .panel_results import ResultsPanel

ORDER_OPTS = {"레지스터맵 값 (사양서)": "spec", "big-endian": "big", "little-endian": "little"}
BACKEND_OPTS = {"DUT RTL 시뮬레이션 (iverilog)": "sim", "Python 모델 (시뮬레이터 없을 때)": "model"}


class App(ConvertPanel, RegmapPanel, ResultsPanel, DemoDutPanel, ManualPanel, tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("RTL Test Vector -> SPI / I2C Converter")
        self.geometry("1440x920")
        self.minsize(1200, 760)
        self.q = queue.Queue()
        self.ip_dir = None
        self.rm = None
        self.dirty = False
        self.last = None
        self._imgs = []
        self._build()
        self.after(100, self._poll)
        ips = ws.list_ips()
        if ips:
            self.v_ip.set(ips[0])
            self.load_ip()

    # ------------------------------------------------------------------ layout
    def _build(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("Big.TLabel", font=("Malgun Gothic", 15, "bold"))
        st.configure("Treeview", rowheight=22)

        # ---------------- 툴바 (툴 본 기능)
        top = ttk.LabelFrame(self, text="설정 — 테스트벡터 RTL → SPI / I2C 변환", padding=8)
        top.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(top, text="IP").grid(row=0, column=0, sticky="w")
        self.v_ip = tk.StringVar()
        self.cb_ip = ttk.Combobox(top, textvariable=self.v_ip, values=ws.list_ips(), width=58)
        self.cb_ip.grid(row=0, column=1, columnspan=5, sticky="we", padx=4)
        self.cb_ip.bind("<<ComboboxSelected>>", lambda e: self.load_ip())
        ipb = ttk.Frame(top)
        ipb.grid(row=0, column=6, sticky="w")
        ttk.Button(ipb, text="찾기", command=self._browse_ip).pack(side="left")
        ttk.Button(ipb, text="새 IP 만들기", command=self.new_ip).pack(side="left", padx=4)

        ttk.Label(top, text="출력 포맷").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.v_if = tk.StringVar(value="spi")
        f_if = ttk.Frame(top)
        f_if.grid(row=1, column=1, sticky="w", pady=(6, 0))
        for t, v in (("SPI", "spi"), ("I2C", "i2c")):
            ttk.Radiobutton(f_if, text=t, value=v, variable=self.v_if, command=self._on_setting).pack(side="left", padx=(0, 8))
        ttk.Label(top, text="I2C 장치 주소 0x").grid(row=1, column=2, sticky="e", pady=(6, 0))
        self.v_i2c = tk.StringVar(value="3C")
        self.ent_i2c = ttk.Entry(top, textvariable=self.v_i2c, width=5)
        self.ent_i2c.grid(row=1, column=3, sticky="w", pady=(6, 0))
        self.ent_i2c.bind("<Return>", lambda e: self._on_setting())
        self.ent_i2c.bind("<FocusOut>", lambda e: self._on_setting())
        ttk.Label(top, text="바이트 순서").grid(row=1, column=4, sticky="e", padx=(16, 4), pady=(6, 0))
        self.v_order = tk.StringVar(value=list(ORDER_OPTS)[0])
        cb = ttk.Combobox(top, textvariable=self.v_order, values=list(ORDER_OPTS), state="readonly", width=20)
        cb.grid(row=1, column=5, sticky="w", pady=(6, 0))
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_setting())
        self.v_showdemo = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="For Demo 영역 보기", variable=self.v_showdemo,
                        command=self._toggle_demo).grid(row=1, column=6, sticky="w", padx=(12, 0), pady=(6, 0))
        top.columnconfigure(1, weight=1)

        btns = ttk.Frame(top)
        btns.grid(row=0, column=7, rowspan=2, padx=(16, 0), sticky="n")
        ttk.Button(btns, text="① 레지스터맵 추출 (헤더 .vh)", command=self.extract).pack(fill="x", pady=1)
        ttk.Button(btns, text="② Aardvark 배치 변환 → 03_vectors", command=self.convert_all).pack(fill="x", pady=1)
        bf = ttk.Frame(btns)
        bf.pack(fill="x", pady=1)
        ttk.Button(bf, text="변환 결과 폴더", command=lambda: self.open_sub(ws.VECTORS_DIR)).pack(side="left", fill="x", expand=True)
        ttk.Button(bf, text="IP 폴더", command=lambda: self.open_sub("")).pack(side="left", fill="x", expand=True)

        # ---------------- 로그 / 상태
        logf = ttk.LabelFrame(self, text="로그", padding=4)
        logf.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        self.lbl_status = ttk.Label(logf, text="", foreground="#0050a0")
        self.lbl_status.pack(anchor="w")
        self.txt_log = tk.Text(logf, height=4, font=("Consolas", 9))
        self.txt_log.pack(fill="x")

        # ---------------- 본문
        self.body = ttk.PanedWindow(self, orient="horizontal")
        self.body.pack(fill="both", expand=True, padx=8, pady=4)
        nb = ttk.Notebook(self.body)
        self.nb = nb
        self.body.add(nb, weight=6)
        for title, builder, pad in (("테스트벡터 RTL → SPI / I2C", self._build_convert_tab, 4),
                                    ("레지스터맵", self._build_map_tab, 6)):
            fr = ttk.Frame(nb, padding=pad)
            nb.add(fr, text=title)
            builder(fr)

        # ---------------- For Demo
        self.demo = ttk.LabelFrame(self.body, text="For Demo — 실물 칩 대신 DUT RTL 시뮬레이션으로 인가·판정", padding=6)
        self.body.add(self.demo, weight=5)
        demo_banner(self.demo, "실제 업무: 변환한 벡터를 SPI/I2C 장비로 실물 칩에 인가하고 결과 확인. "
                               "시연 환경에는 칩이 없으므로, 칩의 RTL(demo_dut/)을 시뮬레이터에서 돌려 같은 벡터를 파형 수준으로 인가한다.")
        ctl = ttk.Frame(self.demo)
        ctl.pack(fill="x", pady=(0, 4))
        ttk.Label(ctl, text="인가 대상").pack(side="left")
        has_sim = find_iverilog() is not None
        self.v_backend = tk.StringVar(value=list(BACKEND_OPTS)[0 if has_sim else 1])
        cb2 = ttk.Combobox(ctl, textvariable=self.v_backend, values=list(BACKEND_OPTS), state="readonly", width=30)
        cb2.pack(side="left", padx=4)
        cb2.bind("<<ComboboxSelected>>", lambda e: self._reset_manual())
        self.v_autodetect = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctl, text="엔디안 자동 감지", variable=self.v_autodetect,
                        command=self._reset_manual).pack(side="left", padx=6)
        ctl2 = ttk.Frame(self.demo)
        ctl2.pack(fill="x", pady=(0, 4))
        self.btn_run = ttk.Button(ctl2, text="③ 인가·판정 실행 (For Demo)", command=self.run_demo)
        self.btn_run.pack(side="left")
        ttk.Button(ctl2, text="리포트", command=self.open_report).pack(side="left", padx=4)
        ttk.Button(ctl2, text="결과 폴더", command=lambda: self.open_sub(ws.RESULTS_DIR)).pack(side="left")
        dnb = ttk.Notebook(self.demo)
        self.dnb = dnb
        dnb.pack(fill="both", expand=True)
        for title, builder, pad in (("인가·판정 결과", self._build_results, 4), ("DUT RTL", self._build_dut_tab, 4),
                                    ("수동 R/W", self._build_manual, 6)):
            fr = ttk.Frame(dnb, padding=pad)
            dnb.add(fr, text=title)
            builder(fr)
        self._on_iface_state()
        self.after(300, self._place_sash)

    def _place_sash(self):
        try:
            self.update_idletasks()
            self.body.sashpos(0, int(self.body.winfo_width() * 0.55))
        except tk.TclError:
            pass

    # ------------------------------------------------------------------ common
    def log(self, msg):
        self.q.put(("log", msg))

    def status(self, msg):
        self.lbl_status.configure(text=msg)

    def _poll(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    self.txt_log.insert("end", f"[{datetime.now():%H:%M:%S}] {payload}\n")
                    self.txt_log.see("end")
                elif kind == "done":
                    self._show_results(payload)
                elif kind == "error":
                    self.btn_run.state(["!disabled"])
                    self.lbl_sum.configure(text="오류", foreground="#c00000")
                    messagebox.showerror("오류", payload)
                elif kind == "man":
                    self.txt_man.insert("end", payload + "\n")
                    self.txt_man.see("end")
                elif kind == "img":
                    self._show_frame(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _conv_order(self):
        v = ORDER_OPTS[self.v_order.get()]
        return (self.rm.spec_byte_order if self.rm else "big") if v == "spec" else v

    def _demo_opts(self):
        order = "auto" if self.v_autodetect.get() else self._conv_order()
        return order, BACKEND_OPTS[self.v_backend.get()]

    def _i2c_addr(self):
        try:
            v = int(self.v_i2c.get(), 16)
            if not 0 <= v <= 0x7F:
                raise ValueError
            return v
        except ValueError:
            raise ValueError("I2C 장치 주소는 7비트 hex (00~7F)")

    def _on_iface_state(self):
        self.ent_i2c.state(["!disabled"] if self.v_if.get() == "i2c" else ["disabled"])

    def _on_setting(self):
        self._on_iface_state()
        self._reset_manual()
        self.refresh_conversion()

    def _toggle_demo(self):
        if self.v_showdemo.get():
            self.body.add(self.demo, weight=5)
            self.after(100, self._place_sash)
        else:
            self.body.forget(self.demo)
