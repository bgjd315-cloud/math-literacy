"""把數學題目整理成純文字，供逐題判讀使用（輸出 work/stems.txt）。"""
import json, re
from pathlib import Path
R = Path(__file__).resolve().parents[1]
TESTS = {"m": "學測數學", "ma": "數A", "mb": "數B", "mj": "數甲", "mi": "數乙"}
def clean(t): return re.sub(r"\s+", " ", re.sub(r"[-]", "θ", t or "")).strip()
out = []
for f in sorted((R/"data/math").glob("1*.json")):
    d = json.loads(f.read_text("utf-8")); y = int(f.stem); ex = d["json:examData"]; ans = d["json:ansData"]
    out.append(f"##### 會考 {y}")
    for g in ex["g"]:
        out.append(f"  [組{g['a']}-{g['b']}] " + clean(g["t"])[:500])
    for i, (q, (c, lab)) in enumerate(zip(ex["q"], d["json:clsData"])):
        a = ans[i] if i < len(ans) else "非選"
        out.append(f"{q['n']}|{a}|{c}|{lab}|" + clean(q["t"])[:420])
for f in sorted((R/"data/xuece-math").glob("1*.json")):
    d = json.loads(f.read_text("utf-8")); y = int(f.stem)
    for t, ex in d["json:examData"].items():
        out.append(f"##### {TESTS[t]} {y} [{t}]")
        for g in ex.get("g", []):
            out.append(f"  [組{g.get('a')}-{g.get('b')}] " + clean(g.get("t"))[:500])
        for i, (q, row) in enumerate(zip(ex["q"], d["js:Q"][t])):
            out.append(f"{q['lab']}|{row[4]}|{row[2]}|{row[0]}/{row[1]}|{row[3]}|" + clean(q["t"])[:420])
(R/"work/stems.txt").write_text("\n".join(out), "utf-8")
print(len(out), "lines", sum(len(x) for x in out), "chars")
