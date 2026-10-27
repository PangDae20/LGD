"""[GUI] 레지스터맵 표 편집·저장 (IP별 02_regmap/regmap.yaml)."""
import os
import tkinter as tk
from tkinter import messagebox, ttk

from core import workspace as ws
from core.pipeline import extract_regmap, load_regmap
from core.regmap import RegMap, Register

MAP_COLS = ("name", "addr", "width", "access", "reset", "rw_mask", "volatile", "desc")
MAP_HEAD = ("이름", "주소", "비트", "접근", "리셋값", "RW마스크", "가변", "설명")


class RegmapPanel:
    def _build_map_tab(self, f):
        meta = ttk.Frame(f)
        meta.pack(fill="x")
        ttk.Label(meta, text="IP 이름").grid(row=0, column=0, sticky="w")
        self.v_ipname = tk.StringVar()
        ttk.Entry(meta, textvariable=self.v_ipname, width=14).grid(row=0, column=1, sticky="w")
        ttk.Label(meta, text="바이트 순서(사양서)").grid(row=0, column=2, sticky="e", padx=(10, 2))
        self.v_specorder = tk.StringVar(value="big")
        ttk.Combobox(meta, textvariable=self.v_specorder, values=["big", "little"], state="readonly",
                     width=7).grid(row=0, column=3, sticky="w")
        ttk.Label(meta, text="ID 레지스터").grid(row=1, column=0, sticky="w")
        self.v_idreg = tk.StringVar()
        self.cb_idreg = ttk.Combobox(meta, textvariable=self.v_idreg, state="readonly", width=12)
        self.cb_idreg.grid(row=1, column=1, sticky="w")
        self.lbl_hint = ttk.Label(meta, text="", foreground="#b05000")
        self.lbl_hint.grid(row=1, column=2, columnspan=3, sticky="w", padx=(10, 0))
        for v in (self.v_ipname, self.v_specorder, self.v_idreg):
            v.trace_add("write", lambda *a: self._mark_dirty())

        ttk.Label(f, text="셀 더블클릭: 수정 / 행 선택 후 '정의 위치 보기': 헤더(.vh)의 정의 줄로 이동", foreground="#666").pack(anchor="w", pady=(6, 0))
        tf = ttk.Frame(f)
        tf.pack(fill="both", expand=True)
        self.tv_map = ttk.Treeview(tf, columns=MAP_COLS, show="headings", selectmode="browse")
        for c, h, w in zip(MAP_COLS, MAP_HEAD, (90, 44, 36, 40, 62, 66, 36, 170)):
            self.tv_map.heading(c, text=h)
            self.tv_map.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(tf, command=self.tv_map.yview)
        self.tv_map.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv_map.pack(fill="both", expand=True)
        self.tv_map.bind("<Double-1>", self._edit_cell)
        row = ttk.Frame(f)
        row.pack(fill="x", pady=4)
        ttk.Button(row, text="정의 위치 보기", command=self._goto_src).pack(side="left")
        ttk.Button(row, text="행 추가", command=self._add_row).pack(side="left", padx=4)
        ttk.Button(row, text="행 삭제", command=self._del_row).pack(side="left")
        ttk.Button(row, text="저장", command=self.save_regmap).pack(side="left", padx=4)
        ttk.Button(row, text="되돌리기", command=self._reload_regmap).pack(side="left")
        self.lbl_dirty = ttk.Label(row, text="", foreground="#c00000")
        self.lbl_dirty.pack(side="left", padx=6)

    # ------------------------------------------------------------------ ① 추출
    def extract(self):
        if not self.ip_dir:
            return
        files = __import__("core.workspace", fromlist=["x"]).list_tv_headers(self.ip_dir)
        if not files:
            messagebox.showinfo("레지스터맵", "01_input/testvector 에 레지스터 정의 헤더(.vh)가 없습니다.")
            return
        rm, warns = extract_regmap(self.ip_dir, files, self.rm)
        self.rm = rm
        self._fill_map()
        self._mark_dirty(True)
        self.txt_warn.delete("1.0", "end")
        self.txt_warn.insert("end", f"레지스터 {len(rm.regs)}개 추출 ({', '.join(f.split('/')[-1] for f in files)}), "
                                    f"I2C 주소 = 0x{rm.i2c_addr:02X}\n" + "\n".join("• " + w for w in warns)
                                    + "\n→ 레지스터맵 탭에서 사양서와 대조·수정 후 저장")
        self.nb.select(1)
        self.log(f"① 레지스터 정의 헤더에서 {len(rm.regs)}개 추출 (확인 필요 {len(warns)}건) → 저장 필요")

    # ------------------------------------------------------------------
    def _mark_dirty(self, flag=True):
        self.dirty = flag
        if hasattr(self, "lbl_dirty"):
            self.lbl_dirty.configure(text="● 저장 안 됨" if flag else "")

    def _need_saved(self):
        if self.rm is None or not self.rm.regs:
            messagebox.showinfo("레지스터맵", "먼저 ① RTL에서 레지스터맵을 추출하고 저장하세요.")
            return False
        if self.dirty:
            if not messagebox.askyesno("저장", "레지스터맵 수정 내용을 저장하고 진행할까요?"):
                return False
            return self.save_regmap()
        return True

    def _fill_map(self):
        self.tv_map.delete(*self.tv_map.get_children())
        if not self.rm:
            for v in (self.v_ipname, self.v_idreg):
                v.set("")
            self.cb_idreg["values"] = []
            self.cb_mreg["values"] = []
            self.lbl_hint.configure(text="")
            self._mark_dirty(False)
            return
        for r in self.rm.regs:
            w = r.nbytes * 2
            self.tv_map.insert("", "end", values=(r.name, f"0x{r.addr:02X}", r.width, r.access,
                                                  f"0x{r.reset:0{w}X}", f"0x{r.rw_mask:0{w}X}",
                                                  "Y" if r.volatile else "", r.desc))
        names = [r.name for r in self.rm.regs]
        self.cb_idreg["values"] = names
        self.cb_mreg["values"] = names
        if names:
            self.v_mreg.set("TPG_MODE" if "TPG_MODE" in names else names[0])
        self.v_ipname.set(self.rm.name)
        self.v_specorder.set(self.rm.spec_byte_order)
        self.v_idreg.set(self.rm.id_register or "")
        self.v_i2c.set(f"{self.rm.i2c_addr:02X}")
        self.lbl_hint.configure(text=f"출처: {', '.join(x.split('/')[-1] for x in self.rm.ip.get('source_files', []))}")
        self._mark_dirty(False)

    def _table_to_regmap(self) -> RegMap:
        regs = []
        for iid in self.tv_map.get_children():
            v = self.tv_map.item(iid, "values")
            if not str(v[0]).strip():
                raise ValueError("이름이 빈 행이 있습니다")
            regs.append(Register(name=str(v[0]).strip(), addr=int(str(v[1]), 0), width=int(v[2]),
                                 access=str(v[3]).upper(), reset=int(str(v[4]), 0), rw_mask=int(str(v[5]), 0),
                                 volatile=str(v[6]).upper() in ("Y", "1", "TRUE"), desc=str(v[7])))
        meta = dict(self.rm.ip) if self.rm else {}
        meta["name"] = self.v_ipname.get().strip() or os.path.basename(self.ip_dir)
        meta["byte_order"] = self.v_specorder.get()
        meta["id_register"] = self.v_idreg.get()
        meta["i2c_addr"] = self._i2c_addr()
        rm = RegMap(meta, regs, ws.p_regmap(self.ip_dir))
        rm.validate()
        return rm

    def save_regmap(self):
        try:
            rm = self._table_to_regmap()
        except Exception as e:
            messagebox.showerror("레지스터맵 오류", str(e))
            return False
        os.makedirs(os.path.dirname(rm.path), exist_ok=True)
        rm.save()
        self.rm = rm
        self._fill_map()
        self.log(f"레지스터맵 저장: {os.path.relpath(rm.path, self.ip_dir)} ({len(rm.regs)}개)")
        self._reset_manual()
        self._fill_files()
        return True

    def _reload_regmap(self):
        if os.path.exists(ws.p_regmap(self.ip_dir)):
            self.rm = load_regmap(self.ip_dir)
        self._fill_map()

    def _goto_src(self):
        sel = self.tv_map.selection()
        if not sel:
            messagebox.showinfo("RTL 위치", "레지스터 행을 선택하세요.")
            return
        self.show_reg_source(self.tv_map.item(sel[0], "values")[0])

    def _add_row(self):
        self.tv_map.insert("", "end", values=("NEW_REG", "0x7F", 8, "RW", "0x00", "0xFF", "", ""))
        self._mark_dirty()

    def _del_row(self):
        for iid in self.tv_map.selection():
            self.tv_map.delete(iid)
        self._mark_dirty()

    def _edit_cell(self, ev):
        iid = self.tv_map.identify_row(ev.y)
        col = self.tv_map.identify_column(ev.x)
        if not iid or not col:
            return
        ci = int(col[1:]) - 1
        x, y, w, h = self.tv_map.bbox(iid, col)
        vals = list(self.tv_map.item(iid, "values"))
        var = tk.StringVar(value=vals[ci])
        cname = MAP_COLS[ci]
        if cname in ("access", "volatile", "width"):
            opts = {"access": ["RO", "RW"], "volatile": ["", "Y"], "width": ["8", "16", "24", "32"]}[cname]
            ed = ttk.Combobox(self.tv_map, textvariable=var, values=opts, state="readonly")
        else:
            ed = ttk.Entry(self.tv_map, textvariable=var)
        ed.place(x=x, y=y, width=max(w, 70), height=h)
        ed.focus_set()

        def commit(_=None):
            vals[ci] = var.get()
            self.tv_map.item(iid, values=vals)
            ed.destroy()
            self._mark_dirty()
        ed.bind("<Return>", commit)
        ed.bind("<FocusOut>", commit)
        ed.bind("<Escape>", lambda e: ed.destroy())
        if isinstance(ed, ttk.Combobox):
            ed.bind("<<ComboboxSelected>>", commit)
