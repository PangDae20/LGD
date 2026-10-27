"""[5단계] 화면 출력 기준 모델 — 사양서 'Test Pattern Generator' 장을 그대로 옮긴 것.

레지스터 논리값 -> 기대 프레임 (width, height, [(R,G,B), ...] row-major)
"""
from typing import Dict, List, Tuple

BAR_COLORS = [
    (0xFF, 0xFF, 0xFF), (0xFF, 0xFF, 0x00), (0x00, 0xFF, 0xFF), (0x00, 0xFF, 0x00),
    (0xFF, 0x00, 0xFF), (0xFF, 0x00, 0x00), (0x00, 0x00, 0xFF), (0x00, 0x00, 0x00),
]
Pixel = Tuple[int, int, int]


def tpg_frame(v: Dict[str, int]) -> Tuple[int, int, List[Pixel]]:
    w = v["H_ACTIVE"] & 0x7FF
    h = v["V_ACTIVE"] & 0x7FF
    pat = v["TPG_MODE"] & 0x7
    fg = (v["FG_R"], v["FG_G"], v["FG_B"])
    n = v["CHECKER_SZ"] & 0x7
    invert = v["PIX_CTRL"] & 1
    rb_swap = (v["PIX_CTRL"] >> 1) & 1
    bw = max(w >> 3, 1)

    pix: List[Pixel] = []
    for y in range(h):
        for x in range(w):
            if pat == 0:
                p = fg
            elif pat == 1:
                p = BAR_COLORS[min(x // bw, 7)]
            elif pat == 2:
                ramp = (x * 4) & 0xFF
                p = (ramp & fg[0], ramp & fg[1], ramp & fg[2])
            elif pat == 3:
                p = fg if ((x >> n) ^ (y >> n)) & 1 else (0, 0, 0)
            else:
                p = (0, 0, 0)
            r, g, b = p
            if rb_swap:
                r, b = b, r
            if invert:
                r, g, b = 255 - r, 255 - g, 255 - b
            pix.append((r, g, b))
    return w, h, pix


if __name__ == "__main__":
    # 디버그: python -m core.golden_model [PATTERN] -> 기준 프레임을 PNG로 저장
    import sys
    from PIL import Image
    st = {"H_ACTIVE": 64, "V_ACTIVE": 48, "TPG_MODE": int(sys.argv[1]) if len(sys.argv) > 1 else 1,
          "FG_R": 0xFF, "FG_G": 0x80, "FG_B": 0x00, "CHECKER_SZ": 3, "PIX_CTRL": 0}
    w, h, px = tpg_frame(st)
    im = Image.new("RGB", (w, h))
    im.putdata(px)
    im.resize((w * 4, h * 4), Image.NEAREST).save("golden_preview.png")
    print(f"{w}x{h}, first pixels {px[:3]} -> golden_preview.png")
