"""[GUI · 툴 본 기능] IP 선택·생성, 테스트벡터 RTL 미리보기 -> SPI / I2C 변환 결과 나란히 보기.

왼쪽 RTL 줄 클릭 -> 오른쪽에서 그 줄이 변환된 SPI/I2C 줄 강조 (반대도 가능)
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from core import workspace as ws
from core.pipeline import convert, load_regmap
from core.tv_parser import count, parse_file
from core.vector_export import export_with_map

from .widgets import CodeView, VectorView, open_path


class ConvertPanel:
    # ------------------------------------------------------------------ layout
    def _build_convert_tab(self, f):
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="01_input/testvector — 클릭: 미리보기·변환 / '사용' 칸: ② 일괄 변환 포함 여부",
                  foreground="#555").pack(anchor="w")
        lf = ttk.Frame(top)
        lf.pack(fill="x")
        cols = ("use", "file", "tid", "ops")
        self.tv_files = ttk.Treeview(lf, columns=cols, show="headings", height=6, selectmode="browse")
        for c, h, w in zip(cols, ("사용", "파일", "시험", "동작 (리셋/쓰기/읽기/화면)"), (40, 230, 150, 200)):
            self.tv_files.heading(c, text=h)
            self.tv_files.column(c, width=w, anchor="center" if c == "use" else "w", stretch=(c in ("file", "ops")))
        sb = ttk.Scrollbar(lf, command=self.tv_files.yview)
        self.tv_files.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv_files.pack(fill="x", expand=True)
        self.tv_files.bind("<ButtonRelease-1>", self._on_file_click)

        row = ttk.Frame(top)
        row.pack(fill="x", pady=2)
        ttk.Button(row, text="전체 사용", command=self._use_all).pack(side="left")
        ttk.Button(row, text="테스트벡터 가져오기", command=lambda: self._import("tv")).pack(side="left", padx=4)
        ttk.Button(row, text="사양서 가져오기", command=lambda: self._import("spec")).pack(side="left")
        ttk.Button(row, text="새로고침", command=self._fill_files).pack(side="left", padx=4)

        pw = ttk.PanedWindow(f, orient="horizontal")
        pw.pack(fill="both", expand=True, pady=(4, 0))
        self.code = CodeView(pw, on_click=self._on_rtl_line)
        pw.add(self.code, weight=1)
        self.vview = VectorView(pw, on_click=self._on_vec_line)
        pw.add(self.vview, weight=1)

        ttk.Label(f, text="파싱 경고 / 확인 필요").pack(anchor="w", pady=(4, 0))
        self.txt_warn = tk.Text(f, height=3, font=("Malgun Gothic", 9), wrap="word")
        self.txt_warn.pack(fill="x")
        self.cur_file = None

    # ------------------------------------------------------------------ IP
    def _browse_ip(self):
        d = filedialog.askdirectory(initialdir=ws.PROJECT_ROOT, title="IP 디렉토리 선택 (01_input/testvector 포함)")
        if d:
            self.v_ip.set(d)
            self.load_ip()

    def new_ip(self):
        name = simpledialog.askstring("새 IP", "IP 이름 (디렉토리 이름으로 사용)", parent=self)
        if not name:
            return
        try:
            ip = ws.create_ip(name)
        except Exception as e:
            messagebox.showerror("새 IP", str(e))
            return
        self.cb_ip["values"] = ws.list_ips()
        self.v_ip.set(ip)
        self.load_ip()
        self.log(f"IP 작업공간 생성: {name}/ (01_input/testvector, 02_regmap, 03_vectors, 04_results, demo_dut)")
        if messagebox.askyesno("새 IP", "테스트벡터 RTL과 레지스터 헤더(.vh)를 지금 가져올까요?"):
            self._import("tv")

    def _import(self, kind):
        if not self.ip_dir:
            return
        ft = {"tv": [("Verilog", "*.v *.sv *.vh *.svh")], "dut": [("Verilog", "*.v *.sv *.vh *.svh")],
              "spec": [("문서", "*.pdf *.md *.docx *.xlsx"), ("모든 파일", "*.*")]}[kind]
        files = filedialog.askopenfilenames(title="가져올 파일", filetypes=ft)
        if not files:
            return
        names = ws.import_files(self.ip_dir, list(files), kind)
        dst = {"tv": ws.INPUT_TV, "spec": ws.INPUT_SPEC, "dut": ws.DEMO_DUT}[kind]
        self.log(f"{len(names)}개 복사 -> {dst}: {', '.join(names)}")
        self._fill_files() if kind == "tv" else (self._fill_dut() if kind == "dut" else None)

    def load_ip(self):
        d = self.v_ip.get()
        if not ws.is_ip_dir(d):
            messagebox.showerror("IP 디렉토리", f"선택한 폴더에 {ws.INPUT_TV} 가 없습니다.")
            return
        self.ip_dir = d
        self.last = None
        self.rm = None
        if os.path.exists(ws.p_regmap(d)):
            try:
                self.rm = load_regmap(d)
            except Exception as e:
                messagebox.showerror("regmap.yaml 오류", str(e))
        self._fill_map()
        self._fill_files()
        self._clear_results()
        self._fill_dut()
        self.title(f"RTL Test Vector -> SPI / I2C Converter — {os.path.basename(d)}")
        self.log(f"IP 로드: {os.path.basename(d)} — 테스트벡터 {len(ws.list_tv(d))}개, "
                 + (f"레지스터 {len(self.rm.regs)}개" if self.rm else "레지스터맵 없음 → ① 추출 필요"))
        self._reset_manual()

    # ------------------------------------------------------------------ file list
    def _fill_files(self):
        if not self.ip_dir:
            return
        self.tv_files.delete(*self.tv_files.get_children())
        for fn in ws.list_tv_headers(self.ip_dir) + ws.list_tv(self.ip_dir):
            is_hdr = fn.endswith((".vh", ".svh"))
            tid, ops = ("헤더", "레지스터 정의" if "regmap" in fn else "공통 태스크") if is_hdr else ("", "")
            if not is_hdr and self.rm:
                tc, _ = parse_file(os.path.join(self.ip_dir, fn), self.rm, fn)
                if tc:
                    k = count(tc)
                    tid = f"{tc.tid} {tc.desc}"
                    ops = f"{k.get('RST', 0)} / {k.get('WREG', 0)} / {k.get('RREG', 0)} / {k.get('FRAME', 0)}"
            self.tv_files.insert("", "end", iid=fn, values=("" if is_hdr else "✔", fn.split("/")[-1], tid, ops))
        files = ws.list_tv(self.ip_dir)
        if files:
            self.show_file(files[0])

    def _on_file_click(self, ev):
        iid = self.tv_files.identify_row(ev.y)
        if not iid:
            return
        if self.tv_files.identify_column(ev.x) == "#1" and not iid.endswith((".vh", ".svh")):
            v = list(self.tv_files.item(iid, "values"))
            v[0] = "" if v[0] else "✔"
            self.tv_files.item(iid, values=v)
        self.show_file(iid)

    def _use_all(self):
        for iid in self.tv_files.get_children():
            if not iid.endswith((".vh", ".svh")):
                v = list(self.tv_files.item(iid, "values"))
                v[0] = "✔"
                self.tv_files.item(iid, values=v)

    def used_tv(self):
        return [i for i in self.tv_files.get_children()
                if not i.endswith((".vh", ".svh")) and self.tv_files.item(i, "values")[0]]

    # ------------------------------------------------------------------ preview + conversion
    def show_file(self, rel, line=None):
        self.cur_file = rel
        self.code.show(os.path.join(self.ip_dir, rel), rel)
        if self.tv_files.exists(rel):
            self.tv_files.selection_set(rel)
            self.tv_files.see(rel)
        self.refresh_conversion()
        if line:
            self.code.goto(line)

    def refresh_conversion(self):
        """현재 파일을 현재 설정(인터페이스·바이트 순서)으로 즉석 변환해 오른쪽에 표시"""
        if not self.cur_file:
            return
        iface = self.v_if.get()
        if self.cur_file.endswith((".vh", ".svh")):
            self.vview.message("변환 결과", "헤더 파일 — 변환 대상 아님 (레지스터맵 추출에 사용)")
            return
        if not self.rm:
            self.vview.message("변환 결과", "레지스터맵이 없습니다 → ① 레지스터맵 추출 후 저장")
            return
        try:
            order, addr = self._conv_order(), self._i2c_addr()
            tc, warns = parse_file(os.path.join(self.ip_dir, self.cur_file), self.rm, self.cur_file)
        except Exception as e:
            self.vview.message("변환 결과", f"오류: {e}")
            return
        self.txt_warn.delete("1.0", "end")
        self.txt_warn.insert("end", "\n".join(warns) if warns else "경고 없음")
        if not tc:
            self.vview.message("변환 결과", "레지스터 동작이 없습니다")
            return
        lines, srcs = export_with_map([tc], self.rm, order, iface, addr)
        n = sum(1 for ln in lines if "<spi_write" in ln or "<i2c_" in ln)
        self.vview.set(f"변환 결과 (Aardvark 배치) — {iface.upper()}, {order}-endian, 명령 {n}개   (RTL 줄 클릭 ↔ 변환 줄 클릭)", lines, srcs)

    def _on_rtl_line(self, line):
        src = f"{self.cur_file}:{line}"
        n = self.vview.mark_src(src)
        self.code.goto(line)
        if n:
            self.status(f"RTL {line}줄 → {self.v_if.get().upper()} {n}줄")

    def _on_vec_line(self, src):
        rel, line = src.rsplit(":", 1)
        if rel == self.cur_file:
            self.code.goto(int(line))

    # ------------------------------------------------------------------ ② 일괄 변환
    def convert_all(self):
        if not self._need_saved():
            return
        files = self.used_tv()
        if not files:
            messagebox.showinfo("변환", "'사용' 표시된 테스트벡터 RTL이 없습니다.")
            return
        try:
            c = convert(self.ip_dir, self.v_if.get(), self._conv_order(), self._i2c_addr(), files, self.rm)
        except Exception as e:
            messagebox.showerror("변환 오류", str(e))
            return
        for w in c["warns"]:
            self.log("[경고] " + w)
        self.log(f"② 변환 완료: 테스트벡터 RTL {len(c['cases'])}개 → {os.path.relpath(os.path.dirname(c['all']), self.ip_dir)}/ "
                 f"(파일별 {len(c['files'])}개 + {os.path.basename(c['all'])}, 트랜잭션 {c['n_xfer']}개, {c['order']}-endian)")

    def open_sub(self, sub):
        if self.ip_dir:
            p = os.path.join(self.ip_dir, sub)
            os.makedirs(p, exist_ok=True)
            open_path(p)

    def show_reg_source(self, name):
        """레지스터맵 -> 정의된 헤더 줄로 이동"""
        src = (self.rm.ip.get("reg_src") or {}).get(name) if self.rm else None
        if not src or ":" not in src:
            messagebox.showinfo("정의 위치", f"{name}: 위치 정보가 없습니다 (① 추출을 다시 하면 기록됨)")
            return
        rel, line = src.rsplit(":", 1)
        self.nb.select(0)
        self.show_file(rel, int(line))
