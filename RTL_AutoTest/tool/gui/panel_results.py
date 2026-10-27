"""[GUI] ③ 전체 실행, 결과 표, 화면 출력 비교, 기대값(Pass 기준) 직접 지정."""
import os
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageTk

from core import workspace as ws
from core.golden_model import tpg_frame
from core.judge import judge_frame, judge_register, load_image_pixels
from core.pipeline import run_demo
from core.report import frame_images


class ResultsPanel:
    def _build_results(self, right):
        hdr = ttk.Frame(right)
        hdr.pack(fill="x")
        self.lbl_sum = ttk.Label(hdr, text="대기 중", style="Big.TLabel")
        self.lbl_sum.pack(side="left")
        self.v_failonly = tk.BooleanVar(value=False)
        ttk.Checkbutton(hdr, text="FAIL만 보기", variable=self.v_failonly,
                        command=lambda: self.last and self._fill_results()).pack(side="right")
        self.lbl_detect = ttk.Label(right, text="", foreground="#0050a0", wraplength=640)
        self.lbl_detect.pack(anchor="w")

        rp = ttk.PanedWindow(right, orient="vertical")
        rp.pack(fill="both", expand=True)
        f_res = ttk.Frame(rp)
        rp.add(f_res, weight=3)
        ttk.Label(f_res, text="항목 더블클릭 → 기대값(Pass 기준) 직접 지정", foreground="#666").pack(anchor="w")
        rcols = ("tid", "item", "exp", "src", "act", "res", "note")
        tf = ttk.Frame(f_res)
        tf.pack(fill="both", expand=True)
        self.tv_res = ttk.Treeview(tf, columns=rcols, show="headings")
        for c, w, t in zip(rcols, (38, 150, 82, 52, 82, 44, 200),
                           ("시험", "항목", "기대", "기대 출처", "실측", "판정", "비고")):
            self.tv_res.heading(c, text=t)
            self.tv_res.column(c, width=w, anchor="w")
        self.tv_res.tag_configure("ng", background="#ffdede")
        self.tv_res.tag_configure("ok", background="#eaf7ea")
        sb2 = ttk.Scrollbar(tf, command=self.tv_res.yview)
        self.tv_res.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.tv_res.pack(fill="both", expand=True)
        self.tv_res.bind("<<TreeviewSelect>>", self._on_select)
        self.tv_res.bind("<Double-1>", self._on_res_double)

        f_img = ttk.LabelFrame(rp, text="화면 출력 비교", padding=4)
        rp.add(f_img, weight=2)
        ctl = ttk.Frame(f_img)
        ctl.pack(fill="x")
        self.lbl_frame = ttk.Label(ctl, text="T07 항목 선택", width=18)
        self.lbl_frame.pack(side="left")
        ttk.Label(ctl, text="Pass 기준:").pack(side="left", padx=(4, 2))
        self.v_passref = tk.StringVar(value="기준 모델 (자동 계산)")
        self.cb_passref = ttk.Combobox(ctl, textvariable=self.v_passref, state="readonly", width=22,
                                       values=["기준 모델 (자동 계산)", "기대 이미지 파일 선택..."])
        self.cb_passref.pack(side="left")
        self.cb_passref.bind("<<ComboboxSelected>>", self._on_passref)
        ttk.Button(ctl, text="출력→기대값 저장", command=self._capture_as_expected).pack(side="left", padx=4)
        imgs = ttk.Frame(f_img)
        imgs.pack(fill="both", expand=True)
        self.img_labels = []
        for cap in ("기대 (Pass 기준)", "DUT 출력", "차이 (빨강 = 불일치)"):
            fr = ttk.Frame(imgs)
            fr.pack(side="left", padx=6)
            lb = ttk.Label(fr)
            lb.pack()
            ttk.Label(fr, text=cap).pack()
            self.img_labels.append(lb)
        self.cur_frame_idx = None

    # ------------------------------------------------------------------ run
    def _clear_results(self):
        self.tv_res.delete(*self.tv_res.get_children())
        self.lbl_sum.configure(text="대기 중", foreground="black")
        self.lbl_detect.configure(text="")
        self.cur_frame_idx = None
        for lb in self.img_labels:
            lb.configure(image="")

    def run_demo(self):
        if not self._need_saved():
            return
        order, backend = self._demo_opts()
        try:
            addr = self._i2c_addr()
        except ValueError as e:
            messagebox.showerror("설정", str(e))
            return
        iface, ip, files = self.v_if.get(), self.ip_dir, self.used_tv()
        if not files:
            messagebox.showinfo("인가·판정", "'사용' 표시된 테스트벡터 RTL이 없습니다.")
            return
        self.btn_run.state(["disabled"])
        self.lbl_sum.configure(text="실행 중...", foreground="black")

        def work():
            try:
                self.q.put(("done", run_demo(ip, iface, order, backend, addr, files, log=self.log)))
            except Exception as e:
                self.q.put(("error", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _show_results(self, r):
        self.btn_run.state(["!disabled"])
        self.last = r
        self._fill_results()
        self._update_summary()
        self.lbl_detect.configure(text=("엔디안 자동 감지: " + r["detect"]) if r["detect"] else "")
        if r["detect"] and r["order"] != self._conv_order():
            msg = (f"Demo 칩에서 감지된 바이트 순서({r['order']})가 변환 설정({self._conv_order()})과 다릅니다 "
                   f"→ 툴바 '바이트 순서'를 {r['order']}-endian 으로 바꾸고 ② 다시 변환")
            self.log("[확인] " + msg)
            self.status(msg)
        self.refresh_conversion()
        res = r["results"]
        first = next((i for i, x in enumerate(res) if x.frame and not x.passed), None)
        if first is None:
            first = next((i for i, x in enumerate(res) if x.frame), None)
        if first is not None:
            self._select_frame(first)

    def _update_summary(self):
        res = self.last["results"]
        npass = sum(x.passed for x in res)
        self.lbl_sum.configure(text=f"{npass} / {len(res)} PASS   ({self.v_if.get().upper()}, {self.last['order']}-endian)",
                               foreground="#0a7a2f" if npass == len(res) else "#c00000")

    def _fill_results(self):
        self.tv_res.delete(*self.tv_res.get_children())
        for i, x in enumerate(self.last["results"]):
            if self.v_failonly.get() and x.passed:
                continue
            self.tv_res.insert("", "end", iid=str(i), tags=("ok" if x.passed else "ng",),
                               values=(x.tid, x.item, x.expected, x.exp_src, x.actual,
                                       "PASS" if x.passed else "FAIL", x.note))

    def _refresh_row(self, i):
        x = self.last["results"][i]
        if self.tv_res.exists(str(i)):
            self.tv_res.item(str(i), tags=("ok" if x.passed else "ng",),
                             values=(x.tid, x.item, x.expected, x.exp_src, x.actual,
                                     "PASS" if x.passed else "FAIL", x.note))
        self._update_summary()

    def open_report(self):
        if self.last and self.last["report"]:
            webbrowser.open("file://" + os.path.abspath(self.last["report"]))
        else:
            self.open_sub(ws.RESULTS_DIR)

    # ------------------------------------------------------------------ expected value (Pass 기준)
    def _on_res_double(self, ev):
        iid = self.tv_res.identify_row(ev.y)
        if not iid or not self.last:
            return
        i = int(iid)
        x = self.last["results"][i]
        if x.frame:
            self._select_frame(i)
            self.cb_passref.focus_set()
            return
        s = simpledialog.askstring(
            "기대값 지정", f"{x.tid}  {x.item}\n실측 {x.actual} / 현재 기대 {x.expected} ({x.exp_src})\n\n"
                           f"Pass 기준으로 쓸 값을 hex로 입력 (비우면 자동 계산값으로 되돌림)",
            initialvalue=x.expected, parent=self)
        if s is None:
            return
        ov = ws.load_overrides(self.ip_dir)
        if s.strip() == "":
            ov.pop(x.key, None)
            judge_register(x, self._auto_expected(x))
            x.exp_src = "자동"
        else:
            try:
                v = int(s.strip(), 16)
            except ValueError:
                messagebox.showerror("기대값", "hex 값으로 입력하세요")
                return
            ov[x.key] = {"value": f"0x{v:X}"}
            judge_register(x, v)
            x.exp_src = "지정"
        if x.passed:
            x.note = ""
        ws.save_overrides(self.ip_dir, ov)
        self._refresh_row(i)
        self.log(f"기대값 지정: {x.key} -> {x.expected} ({'PASS' if x.passed else 'FAIL'}), 02_regmap/expected_overrides.yaml")

    def _auto_expected(self, x):
        for tc in self.last["cases"]:
            if tc.tid != x.tid:
                continue
            for op in tc.ops:
                if op.kind == "RREG" and f"{op.reg} {op.label}".strip() == x.item:
                    return op.value
        return 0

    def _auto_golden(self, x):
        for tc in self.last["cases"]:
            for op in tc.ops:
                if op.kind == "FRAME" and op.label == x.item:
                    return tpg_frame(op.golden)
        return 0, 0, []

    def _select_frame(self, i):
        self.cur_frame_idx = i
        x = self.last["results"][i]
        self.lbl_frame.configure(text=f"{x.tid} {x.item}: {'PASS' if x.passed else 'FAIL'}")
        self.v_passref.set("기준 모델 (자동 계산)" if x.exp_src == "자동" else x.exp_src)
        self._show_frame(x.frame)

    def _on_passref(self, _):
        if self.cur_frame_idx is None:
            return
        i = self.cur_frame_idx
        x = self.last["results"][i]
        ov = ws.load_overrides(self.ip_dir)
        if self.v_passref.get().startswith("기준 모델"):
            ov.pop(x.key, None)
            gw, gh, gold = self._auto_golden(x)
            x.exp_src = "자동"
        else:
            os.makedirs(ws.p_expected(self.ip_dir), exist_ok=True)
            p = filedialog.askopenfilename(initialdir=ws.p_expected(self.ip_dir),
                                           filetypes=[("PNG", "*.png"), ("이미지", "*.png *.bmp")])
            if not p:
                self.v_passref.set("기준 모델 (자동 계산)" if x.exp_src == "자동" else x.exp_src)
                return
            gw, gh, gold = load_image_pixels(p)
            rel = os.path.relpath(p, self.ip_dir).replace("\\", "/")
            ov[x.key] = {"image": rel}
            x.exp_src = "지정: " + rel
        judge_frame(x, gw, gh, gold)
        ws.save_overrides(self.ip_dir, ov)
        self._refresh_row(i)
        self._select_frame(i)
        self.log(f"Pass 기준 변경: {x.key} -> {x.exp_src} ({'PASS' if x.passed else 'FAIL'})")

    def _capture_as_expected(self):
        if self.cur_frame_idx is None:
            messagebox.showinfo("기대 이미지", "결과 표에서 화면 출력(T07) 항목을 선택하세요.")
            return
        i = self.cur_frame_idx
        x = self.last["results"][i]
        cap = x.frame["captured"]
        if not cap:
            messagebox.showinfo("기대 이미지", "DUT 출력이 없습니다.")
            return
        w = x.frame["w"] if x.frame["w"] and len(cap) == x.frame["w"] * x.frame["h"] else len(cap)
        h = len(cap) // w
        im = Image.new("RGB", (w, h))
        im.putdata(cap[:w * h])
        os.makedirs(ws.p_expected(self.ip_dir), exist_ok=True)
        rel = f"{ws.REGMAP_DIR}/expected/{x.item}.png"
        im.save(os.path.join(self.ip_dir, rel))
        ov = ws.load_overrides(self.ip_dir)
        ov[x.key] = {"image": rel}
        ws.save_overrides(self.ip_dir, ov)
        gw, gh, gold = load_image_pixels(os.path.join(self.ip_dir, rel))
        x.exp_src = "지정: " + rel
        judge_frame(x, gw, gh, gold)
        self._refresh_row(i)
        self._select_frame(i)
        self.log(f"현재 출력을 기대 이미지로 저장: {rel} (다음 실행부터 Pass 기준)")

    def _on_select(self, _):
        if not self.last:
            return
        sel = self.tv_res.selection()
        if sel and self.last["results"][int(sel[0])].frame:
            self._select_frame(int(sel[0]))

    def _show_frame(self, fr):
        scale = max(1, min(4, 210 // max(fr["w"], 1), 140 // max(fr["h"], 1)))
        self._imgs = [ImageTk.PhotoImage(im) for im in frame_images(fr, scale)]
        for lb, im in zip(self.img_labels, self._imgs):
            lb.configure(image=im)
