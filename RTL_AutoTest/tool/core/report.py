"""[6단계] 결과 리포트 (CSV + HTML, 화면 비교 이미지 포함)."""
import base64
import csv
import html
import io
import os
from collections import OrderedDict
from datetime import datetime
from typing import List, Optional

from PIL import Image

from .datatypes import Result


def frame_images(fr: dict, scale: int = 4):
    """golden / captured / diff PIL 이미지"""
    w, h = fr["w"], fr["h"]
    gold = Image.new("RGB", (max(w, 1), max(h, 1)))
    if w and h:
        gold.putdata(fr["golden"])
    cap = Image.new("RGB", gold.size, (40, 40, 40))
    diff = Image.new("RGB", gold.size, (0, 0, 0))
    c = fr["captured"]
    if c and len(c) == w * h:
        cap.putdata(c)
        diff.putdata([(255, 0, 0) if a != b else (0, 90, 0) for a, b in zip(fr["golden"], c)])
    elif c:
        diff = Image.new("RGB", gold.size, (255, 0, 0))
    else:
        diff = Image.new("RGB", gold.size, (255, 0, 0))
    up = lambda im: im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    return up(gold), up(cap), up(diff)


def _b64(im) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def summarize(results: List[Result]):
    s = OrderedDict()
    for r in results:
        d = s.setdefault(r.tid, {"type": r.ttype, "pass": 0, "fail": 0})
        d["pass" if r.passed else "fail"] += 1
    return s


def write_reports(results: List[Result], outdir: str, meta: dict, vectors: Optional[List[str]] = None) -> str:
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "results.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["test", "type", "item", "expected", "expected_source", "actual", "result", "note"])
        for r in results:
            w.writerow([r.tid, r.ttype, r.item, r.expected, r.exp_src, r.actual, "PASS" if r.passed else "FAIL", r.note])
    if vectors:
        with open(os.path.join(outdir, "vectors.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(vectors) + "\n")

    total = len(results)
    npass = sum(r.passed for r in results)
    rows = []
    for tid, d in summarize(results).items():
        cls = "ok" if d["fail"] == 0 else "ng"
        rows.append(f"<tr class='{cls}'><td>{tid}</td><td>{d['type']}</td><td>{d['pass']}</td>"
                    f"<td>{d['fail']}</td><td>{'PASS' if d['fail'] == 0 else 'FAIL'}</td></tr>")
    detail = []
    for r in results:
        cls = "ok" if r.passed else "ng"
        detail.append(f"<tr class='{cls}'><td>{r.tid}</td><td>{html.escape(r.item)}</td><td>{r.expected}</td>"
                      f"<td>{html.escape(r.exp_src)}</td><td>{r.actual}</td><td>{'PASS' if r.passed else 'FAIL'}</td><td>{html.escape(r.note)}</td></tr>")
    frames = []
    for r in results:
        if r.frame:
            g, c, d = frame_images(r.frame)
            os.makedirs(os.path.join(outdir, "frames"), exist_ok=True)
            g.save(os.path.join(outdir, "frames", f"{r.item}_golden.png"))
            c.save(os.path.join(outdir, "frames", f"{r.item}_captured.png"))
            frames.append(
                f"<div class='fr'><h3>{html.escape(r.item)} — <span class='{'ok' if r.passed else 'ng'}'>"
                f"{'PASS' if r.passed else 'FAIL'}</span> <small>{html.escape(r.note)}</small></h3>"
                f"<div class='imgs'><figure><img src='data:image/png;base64,{_b64(g)}'><figcaption>기준 모델</figcaption></figure>"
                f"<figure><img src='data:image/png;base64,{_b64(c)}'><figcaption>DUT 출력</figcaption></figure>"
                f"<figure><img src='data:image/png;base64,{_b64(d)}'><figcaption>차이(빨강=불일치)</figcaption></figure></div></div>")
    meta_html = "".join(f"<li><b>{html.escape(k)}</b>: {html.escape(str(v))}</li>" for k, v in meta.items())
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>RTL Auto Test Report</title>
<style>
body{{font-family:-apple-system,"Malgun Gothic",sans-serif;margin:24px;color:#1d1d1f;background:#fafafa}}
h1{{margin:0 0 4px}} .big{{font-size:28px;font-weight:700}}
table{{border-collapse:collapse;width:100%;margin:12px 0;background:#fff;font-size:13px}}
td,th{{border:1px solid #ddd;padding:4px 8px;text-align:left}} th{{background:#eee}}
tr.ng td{{background:#ffecec}} .ok{{color:#0a7a2f}} .ng{{color:#c00}}
.imgs{{display:flex;gap:12px;flex-wrap:wrap}} figure{{margin:0}} img{{image-rendering:pixelated;border:1px solid #ccc;max-width:100%}}
figcaption{{font-size:12px;color:#555}}
</style></head><body>
<h1>{html.escape(str(meta.get('IP','')))} 레지스터/기능 자동 시험 리포트</h1>
<div class="big {'ok' if npass == total else 'ng'}">{npass} / {total} PASS</div>
<ul>{meta_html}<li><b>생성 시각</b>: {datetime.now():%Y-%m-%d %H:%M:%S}</li></ul>
<h2>요약</h2><table><tr><th>시험</th><th>유형</th><th>PASS</th><th>FAIL</th><th>판정</th></tr>{''.join(rows)}</table>
<h2>화면 출력 비교</h2>{''.join(frames)}
<h2>상세</h2><table><tr><th>시험</th><th>항목</th><th>기대</th><th>기대값 출처</th><th>실측</th><th>판정</th><th>비고</th></tr>{''.join(detail)}</table>
</body></html>"""
    path = os.path.join(outdir, "report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path
