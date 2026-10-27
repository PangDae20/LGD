"""[GUI] 수동 R/W: 레지스터 하나씩 쓰고 읽기, 화면 캡처."""
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from core import vector_i2c, vector_spi
from core.datatypes import Op, TestCase
from core.endian_detect import detect_byte_order
from core.golden_model import tpg_frame
from core.pipeline import make_backend
from core.vector_cmd import serialize


class ManualPanel:
    def _build_manual(self, f):
        from .panel_demo_dut import demo_banner
        bf0 = ttk.Frame(f)
        bf0.grid(row=0, column=0, columnspan=4, sticky="we")
        demo_banner(bf0, "실물 칩 대신 DUT RTL(또는 Python 모델)에 레지스터를 직접 쓰고 읽음")
        ttk.Label(f, text="레지스터 단위로 쓰고 읽기. 선택한 인터페이스의 트랜잭션으로 변환되어 인가됨.",
                  wraplength=420).grid(row=5, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ttk.Label(f, text="레지스터").grid(row=1, column=0, sticky="w")
        self.v_mreg = tk.StringVar()
        self.cb_mreg = ttk.Combobox(f, textvariable=self.v_mreg, state="readonly", width=14)
        self.cb_mreg.grid(row=1, column=1, sticky="w")
        ttk.Label(f, text="값(hex)").grid(row=2, column=0, sticky="w")
        self.v_mval = tk.StringVar(value="0")
        ttk.Entry(f, textvariable=self.v_mval, width=16).grid(row=2, column=1, sticky="w")
        bf = ttk.Frame(f)
        bf.grid(row=3, column=0, columnspan=4, sticky="w", pady=4)
        ttk.Button(bf, text="Write", command=lambda: self.manual("W")).pack(side="left")
        ttk.Button(bf, text="Read", command=lambda: self.manual("R")).pack(side="left", padx=4)
        ttk.Button(bf, text="화면 캡처", command=lambda: self.manual("F")).pack(side="left")
        ttk.Button(bf, text="리셋", command=self._reset_manual).pack(side="left", padx=4)
        self.txt_man = tk.Text(f, height=22, width=54, font=("Consolas", 9))
        self.txt_man.grid(row=4, column=0, columnspan=4, sticky="nsew")
        f.rowconfigure(4, weight=1)
        f.columnconfigure(3, weight=1)
        self.manual_writes = []
        self.manual_order = None

    def _reset_manual(self):
        self.manual_writes = []
        self.manual_order = None
        if hasattr(self, "txt_man"):
            self.txt_man.delete("1.0", "end")
            self.txt_man.insert("end", "-- 칩 리셋 상태 --\n")

    def manual(self, kind):
        if not self._need_saved():
            return
        reg = self.rm[self.v_mreg.get()]
        try:
            val = int(self.v_mval.get(), 16)
            addr = self._i2c_addr()
        except ValueError as e:
            messagebox.showerror("값 오류", str(e) if "I2C" in str(e) else "16진수로 입력하세요 (예: 3, 0x40)")
            return
        order, backend = self._demo_opts()
        iface, rm, ip = self.v_if.get(), self.rm, self.ip_dir

        def xfer(op, a, d):
            return vector_spi.describe(op, a, d) if iface == "spi" else vector_i2c.describe(addr, op, a, d)

        def work():
            try:
                be = make_backend(backend, rm, ip, iface, addr)
                if self.manual_order is None:
                    if order == "auto":
                        self.manual_order, msg = detect_byte_order(be, rm, self.log)
                        self.q.put(("man", "[자동 감지] " + msg))
                    else:
                        self.manual_order = order
                o = self.manual_order
                ops = [Op("RST")] + [Op("WREG", n, v) for n, v in self.manual_writes]
                if kind == "W":
                    ops.append(Op("WREG", reg.name, val))
                    self.manual_writes.append((reg.name, val))
                elif kind == "R":
                    ops.append(Op("RREG", reg.name, 0, reg.full_mask))
                else:
                    ops.append(Op("FRAME", label="manual", golden={}))
                raw = be.run(serialize([TestCase("M", "manual", "manual", ops)], rm, o), lambda m: None)
                w = reg.nbytes * 2
                if kind == "W":
                    lines = [f"W {reg.name} <- 0x{val:0{w}X}"]
                    lines += [f"    {xfer('W', a, d)}" for a, d in rm.split(reg, val, o)]
                elif kind == "R":
                    byt = {a: d for a, d, _ in raw.reads}
                    nack = any(n for _, _, n in raw.reads)
                    v = rm.join(reg, byt, o)
                    lines = [f"R {reg.name} -> " + ("NACK (장치 주소 확인)" if nack else f"0x{v:0{w}X}")]
                    lines += [f"    {xfer('R', a, byt[a])}" for a, _ in rm.byte_lanes(reg, o)]
                else:
                    cap = raw.frames[0]
                    if cap is None:
                        self.q.put(("man", "화면 출력 없음 (DISP_CTRL = 0x03 으로 표시 켜기)"))
                        return
                    st = {r.name: r.reset for r in rm.regs}
                    for n, v in self.manual_writes:
                        rr = rm[n]
                        if rr.access == "RW":
                            st[n] = (st[n] & ~rr.rw_mask) | (v & rr.rw_mask)
                    gw, gh, gold = tpg_frame(st)
                    same = len(gold) == len(cap) and all(a == b for a, b in zip(gold, cap))
                    self.q.put(("man", f"화면 캡처: {len(cap)} px, 기준 모델 {gw}x{gh} -> {'일치' if same else '불일치'}"))
                    self.q.put(("img", {"w": gw, "h": gh, "golden": gold, "captured": cap}))
                    return
                self.q.put(("man", "\n".join(lines)))
            except Exception as e:
                self.q.put(("error", str(e)))
        threading.Thread(target=work, daemon=True).start()
