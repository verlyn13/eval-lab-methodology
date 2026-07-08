#!/usr/bin/env python3
"""Regenerate the figures from evidence/data.json — standard library only.

Two figures:
  1. promotion-gate-decision.svg — paired success delta (candidate minus
     incumbent) with the seeded bootstrap CI, for both worked examples. Shows
     why each is a NO-GO: the representative case's interval touches zero; the
     live case's interval sits entirely below zero.
  2. capability-by-class.svg — the representative capability ranking, incumbent
     vs candidate, per task-class plus overall.

Deterministic: the SVG is a pure function of data.json. No third-party deps.

    python3 figures/generate.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE.parent / "evidence" / "data.json").read_text(encoding="utf-8"))

INK = "#1f2933"
GRID = "#c7ccd1"
ZERO = "#111827"
INCUMBENT = "#2563eb"  # blue
CANDIDATE = "#d97706"  # amber
LIVE = "#b91c1c"  # red
FONT = "font-family='ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif'"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x: float, y: float, s: str, *, size: int = 13, anchor: str = "start",
         fill: str = INK, weight: str = "normal") -> str:
    return (
        f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}' "
        f"fill='{fill}' font-weight='{weight}' {FONT}>{esc(s)}</text>"
    )


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = GRID,
         width: float = 1.0, dash: str | None = None) -> str:
    d = f" stroke-dasharray='{dash}'" if dash else ""
    return (
        f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
        f"stroke='{stroke}' stroke-width='{width}'{d}/>"
    )


def rect(x: float, y: float, w: float, h: float, fill: str) -> str:
    return f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{fill}'/>"


def svg(width: int, height: int, body: list[str]) -> str:
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        f"viewBox='0 0 {width} {height}' role='img'>"
        f"<rect width='{width}' height='{height}' fill='#ffffff'/>"
        + "".join(body)
        + "</svg>\n"
    )


def gate_figure() -> str:
    w, h = 780, 300
    left, right, top, bot = 70, 40, 84, 64
    x0, x1 = left, w - right
    band = DATA["tolerance_band"]

    def px(delta: float) -> float:
        return x0 + (delta + 1.0) / 2.0 * (x1 - x0)

    body: list[str] = []
    body.append(text(left, 34, "Promotion gate decision", size=18, weight="bold"))
    body.append(text(left, 56, "Paired success delta (candidate minus incumbent) with seeded bootstrap 95% CI",
                     size=13, fill="#52606d"))

    # axis ticks
    for tick in (-1.0, -0.5, 0.0, 0.5, 1.0):
        xt = px(tick)
        body.append(line(xt, top, xt, h - bot, stroke=GRID, width=1.0))
        body.append(text(xt, h - bot + 20, f"{tick:+.1f}", size=12, anchor="middle", fill="#52606d"))
    # zero + band
    body.append(line(px(0.0), top, px(0.0), h - bot, stroke=ZERO, width=2.0))
    body.append(text(px(0.0), top - 8, "0", size=12, anchor="middle", fill=ZERO, weight="bold"))
    for b in (band, -band):
        body.append(line(px(b), top, px(b), h - bot, stroke="#9aa5b1", width=1.0, dash="4 3"))
    body.append(text(px(band), h - bot + 38, "band +0.10 (promote requires delta > band AND CI low > 0)",
                     size=11, anchor="middle", fill="#7b8794"))

    cases = DATA["promotion_gate_cases"]
    rows_y = [top + 40, top + 110]
    for case, cy in zip(cases, rows_y):
        color = CANDIDATE if "representative" in case["provenance"] else LIVE
        lo, hi, pt = px(case["ci_low"]), px(case["ci_high"]), px(case["paired_delta"])
        body.append(line(lo, cy, hi, cy, stroke=color, width=3.0))
        for cx in (lo, hi):
            body.append(line(cx, cy - 7, cx, cy + 7, stroke=color, width=3.0))
        body.append(f"<circle cx='{pt:.1f}' cy='{cy:.1f}' r='6' fill='{color}'/>")
        label = "Representative (stubbed harness)" if "representative" in case["provenance"] else "Live smoke (small-n)"
        body.append(text(left, cy - 14, label, size=13, weight="bold"))
        detail = (
            f"delta {case['paired_delta']:+.3f}, CI [{case['ci_low']:g}, {case['ci_high']:g}]  ->  NO-GO"
        )
        body.append(text(x1, cy - 14, detail, size=12, anchor="end", fill=color))
    return svg(w, h, body)


def capability_figure() -> str:
    cap = DATA["capability_representative"]
    classes = [c.replace("_", " ") for c in cap["classes"]] + ["overall"]
    inc = cap["incumbent"]["by_class"] + [cap["incumbent"]["overall"]]
    cand = cap["candidate"]["by_class"] + [cap["candidate"]["overall"]]

    w, h = 780, 380
    left, right, top, bot = 60, 30, 96, 96
    x0, x1, y0, y1 = left, w - right, top, h - bot

    def py(val: float) -> float:
        return y1 - val * (y1 - y0)

    body: list[str] = []
    body.append(text(left, 34, "Capability by task-class (representative data)", size=18, weight="bold"))
    body.append(text(left, 56, "Stubbed harness, representative data. Design behavior, not a live A/B.",
                     size=13, fill="#b45309"))

    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        yy = py(frac)
        body.append(line(x0, yy, x1, yy, stroke=GRID, width=1.0))
        body.append(text(x0 - 8, yy + 4, f"{int(frac * 100)}%", size=12, anchor="end", fill="#52606d"))

    n = len(classes)
    group_w = (x1 - x0) / n
    bar_w = group_w * 0.30
    for i, cls in enumerate(classes):
        gx = x0 + i * group_w + group_w / 2
        bi = gx - bar_w - 3
        bc = gx + 3
        body.append(rect(bi, py(inc[i]), bar_w, y1 - py(inc[i]), INCUMBENT))
        body.append(rect(bc, py(cand[i]), bar_w, y1 - py(cand[i]), CANDIDATE))
        body.append(text(bi + bar_w / 2, py(inc[i]) - 6, f"{int(inc[i] * 100)}", size=11, anchor="middle", fill=INCUMBENT))
        body.append(text(bc + bar_w / 2, py(cand[i]) - 6, f"{int(cand[i] * 100)}", size=11, anchor="middle", fill=CANDIDATE))
        body.append(text(gx, y1 + 20, cls, size=11, anchor="middle", fill=INK))

    ly = h - 34
    body.append(rect(left, ly - 10, 14, 14, INCUMBENT))
    body.append(text(left + 20, ly + 2, cap["incumbent"]["label"], size=12))
    body.append(rect(left + 250, ly - 10, 14, 14, CANDIDATE))
    body.append(text(left + 270, ly + 2, cap["candidate"]["label"], size=12))
    rr = cap["role_recommendation"]
    body.append(text(x1, 56, f"role rec: switch, +{rr['margin']:g} ({rr['confidence']})",
                     size=12, anchor="end", fill="#b45309"))
    return svg(w, h, body)


def main() -> None:
    (HERE / "promotion-gate-decision.svg").write_text(gate_figure(), encoding="utf-8")
    (HERE / "capability-by-class.svg").write_text(capability_figure(), encoding="utf-8")
    print("wrote figures/promotion-gate-decision.svg, figures/capability-by-class.svg")


if __name__ == "__main__":
    main()
