"""Final pass, Part 1 -- ONGC gating honesty.

The ONGC case study reported ungated (raw) lead as if it were detection quality. Verified from
n20_rerun_long_ONGC.csv (factor 1, aggregate) and ongc_onset_markers.csv:
  onset 2023-11-13 03:44:01, shutdown 09:46:00 -> 6.03 h
  valid at tau=10%: Hotelling T2 (30.37 h, pre-onset FAR 6.49%), RMS-trend (22.82 h, 0.14%)
  eight other alarming detectors invalid (guard caught a 'seven' in the first draft): pre-onset FAR 11.75% (Isolation Forest) .. 95.17% (CUSUM),
  their alarms 27.9-29.3 h before the estimated onset; Deep SVDD no alarm before failure.
The aggregate-vs-decimate contrast stays on raw lead (unaffected). Abstract, Introduction and
Conclusion make no ONGC detection-quality claim (checked), so they are unchanged.
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "phase4"))
from p4lib import Doc

d = Doc()
d.para("Nine of the eleven detectors alarm 30--35~h before the labeled failure",
       "On raw lead, nine of the eleven detectors alarm 30--35~h before the labeled failure (seven within 34.9--35.3~h, CUSUM at 33.9~h and Hotelling $T^2$ at 30.4~h), the naive RMS-trend baseline gives 22.8~h, and Deep SVDD does not alarm before failure. Under the gated metric, however, only Hotelling $T^2$ (pre-onset FAR 6.5\\%) and RMS-trend (0.1\\%) have valid alarms at $\\tau=10\\%$; the other eight alarming detectors exceed the budget, with pre-onset FAR from 11.7\\% (Isolation Forest) to 95.2\\% (CUSUM). The data-derived onset lies only ${\\sim}6$~h before the shutdown, so their first alarms fall 28--29~h before it and the windows they flag there count as pre-onset false alarms under the paper's own definition. That verdict is ambiguous here. The onset estimator is systematically late under gradual degradation (late by approximately $k\\sigma_b/m$; Algorithm~\\ref{alg:onset}), so some alarms that precede the estimated onset may be genuine early detection the estimator cannot credit; with $n=1$ and no ground-truth defect-initiation time, the case study cannot distinguish the two. The aggregate-vs-decimate contrast is computed on raw lead and is unaffected: the difference is at most about a minute for every detector (Table~\\ref{tab:imsongc}), so on data that already is a real historian stream the choice of logging mechanism does not materially change warning time---the cleanest possible illustration of the practical question, and consistent with ``averaging is not the enemy.'' Because ONGC is a single asset ($n=1$), we treat it as a descriptive case study and draw no statistical inference from it. Its conformal calibration (Figure~\\ref{fig:conformal}d) tracks the diagonal closely, consistent with a mostly-stationary normal region.")
d.para("\\emph{The single-asset turbine case study.}",
       "\\emph{The single-asset turbine case study.} The one real historian record, an ONGC gas-turbine low-pressure-compressor bearing logged at a 10~s SCADA rate and ending in a genuine operator shutdown, is the cleanest illustration of the practical question because it needs no simulated coarsening: the aggregate-vs-decimate difference in raw lead is at most about a minute for every detector. Its detection quality is less clear-cut. Nine of its eleven detectors raise a raw alarm 30--35~h ahead of the labeled failure (RMS-trend 22.8~h, and Deep SVDD not before failure at all), but under the gated metric at $\\tau=10\\%$ only Hotelling $T^2$ and RMS-trend are valid, because the others flag too many windows of a pre-onset region that ends only ${\\sim}6$~h before the shutdown; whether they are false alarms or genuine early detections that the late-biased onset cannot credit is undecidable at $n=1$ (Appendix~D.2). As a single asset it supports no inference and is excluded from the inferential family.")
d.save()

# machine-check the new ONGC wording (added to verify_tables.check_prose_additions)
vt = pathlib.Path(__file__).resolve().parents[2] / "paper" / "verify_tables.py"
s = vt.read_text(encoding="utf-8")
anchor = '    need("every detector achieves a long warning" not in body, "ONGC overclaim removed")\n'
assert s.count(anchor) == 1
guard = anchor + '''    # ONGC gating (final pass): only Hotelling T2 and RMS-trend are valid at tau = 10%
    ong = {r["short_name"]: r for r in load("n20_rerun_long_ONGC.csv")
           if float(r["factor"]) == 1 and r["mode"] == "aggregate"}
    valid = sorted(k for k, r in ong.items() if r["valid_alarm"] in ("True", "true", "1"))
    need(valid == ["hotelling_t2", "rms_trend"], "ONGC valid at tau=10%: Hotelling T2 and RMS-trend only", str(valid))
    far = {k: float(r["far_preonset_pct"]) for k, r in ong.items()}
    inval = [k for k in ong if k not in valid and float(ong[k]["lead_time_hours"]) > 0]
    need(len(inval) == 8, "ONGC eight alarming detectors invalid", str(len(inval)), 8)
    for v, label in ((far["hotelling_t2"], "6.5"), (far["rms_trend"], "0.1"),
                     (min(far[k] for k in inval), "11.7"), (max(far[k] for k in inval), "95.2")):
        need(abs(round(v, 1) - float(label)) < 1e-9, "ONGC pre-onset FAR " + label, "%.2f" % v, label)
    need(min(inval, key=lambda k: far[k]) == "isolation_forest" and max(inval, key=lambda k: far[k]) == "cusum",
         "ONGC FAR range endpoints Isolation Forest / CUSUM")
    gap = float(load("ongc_onset_markers.csv")[0]["max_lead_hours"])
    need(round(gap) == 6, "ONGC onset ~6 h before shutdown", "%.2f" % gap, 6)
    early = [float(ong[k]["lead_time_hours"]) - gap for k in inval]
    need(round(min(early)) == 28 and round(max(early)) == 29, "ONGC invalid alarms precede onset by 28-29 h",
         "%.1f-%.1f" % (min(early), max(early)), "28-29")
    need("only Hotelling $T^2$ (pre-onset FAR 6.5" in body, "ONGC gating sentence present (App. D.2)")
    need("only Hotelling $T^2$ and RMS-trend are valid" in body, "ONGC gating sentence present (Sec. 7.2)")
'''
vt.write_text(s.replace(anchor, guard), encoding="utf-8")
print("verify_tables ONGC gating guard added")
