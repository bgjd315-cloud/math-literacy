#!/usr/bin/env python3
"""把逐題判讀（reading_cls.py）與 data/ 的題目合成數學素養頁面用的資料。

由 build.py 呼叫：
  build_reading(root) → {"items": [...]}，item =
    [考試, 年度, 題號, 考點, 答案, 歷程, 錯誤, 提示, 題目文字, 策略, 試卷, 原題連結參數]
  build_practice(root) → 練習卷用資料（只收選擇題，附試卷圖片裁切範圍）
考試：0 = 會考數學（data/math），1 = 學測數學（m、ma、mb），2 = 分科數學（mj、mi）。
"""
import json
import re
import sys
from pathlib import Path

TESTS = {"math": (0, "會考"), "m": (1, "學測數學"), "ma": (1, "數A"), "mb": (1, "數B"), "mj": (2, "數甲"), "mi": (2, "數乙")}
ORDER = ["math", "m", "ma", "mb", "mj", "mi"]
MAXLEN = 240


def _clean(t):
    t = re.sub(r"[-]", "θ", t or "")
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"^\d{1,2}\s*[\.．]\s*", "", t)


def _years(root, subj):
    for f in sorted((root / "data" / subj).glob("1[0-9][0-9].json")):
        yield int(f.stem), json.loads(f.read_text("utf-8"))


def _rows(root):
    """逐題產生 (測驗代號, 年度, 索引, 題目, 題組, 考點, 答案, 原題連結參數, 試卷頁資料)。"""
    for y, d in _years(root, "math"):
        ex, ans = d["json:examData"], d["json:ansData"]
        for i, (q, (_, lab)) in enumerate(zip(ex["q"], d["json:clsData"])):
            g = next((g for g in ex["g"] if g["a"] <= q["n"] <= g["b"]), None)
            a = ans[i] if i < len(ans) else "非選"
            page = [ex["w"], ex["h"], ex["x0"], ex["xw"], f"math/math-pages/{y}-"]
            yield "math", y, i, q, g, lab, a, f"{y},{q['n']}", str(q["n"]), page
    for y, d in _years(root, "xuece-math"):
        for t, ex in d["json:examData"].items():
            for i, (q, row) in enumerate(zip(ex["q"], d["js:Q"][t])):
                g = next((g for g in ex.get("g", []) if g.get("a") and g["a"] <= _num(q["lab"]) <= g["b"]), None)
                a = row[4]
                if row[1] in ("非選擇題",) or a in ("／", ""):
                    a = "非選"
                page = [ex["w"], ex["h"], 56, 486, f"xuece-math/pages/{y}{t}-"]
                yield t, y, i, q, g, row[3], a, f"{y},{t},{i}", q["lab"], page


def _num(lab):
    m = re.match(r"\d+", str(lab))
    return int(m.group()) if m else -1


def build_reading(root):
    root = Path(root)
    sys.path.insert(0, str(root / "tools"))
    from reading_cls import CLS

    rows = list(_rows(root))
    items = []
    for key in ORDER:
        exam, tname = TESTS[key]
        kr = [r for r in rows if r[0] == key]
        for y in sorted({r[1] for r in kr}):
            yr = [r for r in kr if r[1] == y]
            hints = CLS[key][y].split("｜")
            if len(hints) != len(yr):
                raise SystemExit(f"[錯誤] {key} {y}：題數 {len(yr)}、判讀 {len(hints)} 不一致")
            for (t, _, i, q, g, lab, a, args, shown, _), h in zip(yr, hints):
                proc, strat, err, hint = h.split(" ", 3)
                text = _clean(q.get("t")) or (_clean(g["t"]) if g else "")
                no = shown if key == "math" else f"{tname} {shown}"
                items.append([exam, y, no, lab, a, proc, err, hint, text[:MAXLEN], strat, t, args])
    return {"items": items}


def build_practice(root):
    """練習卷用資料：只收單選、多選（會考 A–D，學測與分科 1–5）。

    回傳 {"items": [...]}，item = [考試, 年度, 題號, 答案, 歷程, 錯誤, 提示, 考點, 題目裁切, 題組裁切, 選項字元, 策略, 頁面資料, 題庫代號]
    頁面資料 = [寬, 高, x0, xw, 圖片路徑前綴]；裁切 = [頁, 上, 下, 裁切框, 遮罩]。
    """
    root = Path(root)
    reading = {(it[10], it[1], it[11]): it for it in build_reading(root)["items"]}
    items = []

    def norm(sl):
        return [list(s[:3]) + [s[3] if len(s) > 3 else [], s[4] if len(s) > 4 else []] for s in sl]

    for t, y, i, q, g, lab, a, args, shown, page in _rows(root):
        it = reading[(t, y, args)]
        if t == "math":
            if not re.fullmatch(r"[A-D]", a):
                continue
            opts, ans = "ABCD", a
        else:
            ans = a.replace(",", "").replace(" ", "")
            if not re.fullmatch(r"[1-5]+", ans) or ("選填" in lab) or ("," not in a and len(ans) > 1):
                continue
            opts = "12345"
        if not q.get("s"):
            continue
        gs = norm(g["s"]) if g and g.get("s") else []
        items.append([it[0], y, it[2], ans, it[5], it[6], it[7], lab, norm(q["s"]), gs, opts, it[9], page,
                      f"{t}-{args.replace(',', '-')}"])
    return {"items": items}


if __name__ == "__main__":
    from collections import Counter
    R = Path(__file__).resolve().parents[1]
    idx = build_reading(R)
    print(len(idx["items"]), "題", Counter(it[0] for it in idx["items"]))
    p = build_practice(R)
    print("練習卷", len(p["items"]), "題", Counter((it[0], len(it[3]) > 1) for it in p["items"]))
