# ====================================================== Phase 1 consolidated tables
# The shortened manuscript (2026-09-23) merges Tables 2/12/15 -> tab:imsdet,
# 5/6/8 -> tab:crossds, 7/23 -> tab:imsongc, 21/22 -> tab:mechanism and
# 16/17 -> tab:hyperparams, and moves Table 11 into the fig:conformal caption.
# Every printed value is re-derived here from the MANIFEST source files.
RUNLEVEL = {"XJTU-SY": "xjtu_sy_runlevel_test.csv",      # N-20 no-op dataset
            "FEMTO": "femto_runlevel_test_n20.csv",      # post-fix (N-20)
            "Ferrara": "ferrara_runlevel_test_n20.csv",  # post-fix (N-20)
            "IMS": "ims_runlevel_test_invariant.csv"}    # N-20 no-op, D-2 invariant schema
ONGC_ROW_KEYS = {"3sigma": "three_sigma", "ewma": "ewma", "cusum": "cusum",
                 "hotelling": "hotelling_t2", "isoforest": "isolation_forest",
                 "deepsvdd": "deep_svdd", "ocsvm": "one_class_svm", "lstmae": "lstm_ae",
                 "tcnae": "tcn", "transformerad": "transformer_ad", "rmstrend": "rms_trend"}


def _runlevel_src():
    src = {}
    for ds, fname in RUNLEVEL.items():
        for r in load(fname):
            k = key_of(r["method"])
            if k:
                src[(ds, k)] = dict(med=float(r["median_diff"]), npos=r["n_pos"], nneg=r["n_neg"],
                                    same=r["all_same_sign"] in ("True", "true"),
                                    p=float(r["sign_test_p"]), runs=r["run_diffs"])
    for r in load_holm_family():                 # one-class SVM rows, post-fix arm
        if key_of(r["method"]) == "ocsvm":
            src[(r["dataset"], "ocsvm")] = dict(
                med=float(r["median_diff_h"]), npos=r["n_pos"], nneg=r["n_neg"],
                same=r["all_same_sign"] in ("True", "true"), p=float(r["sign_test_p"]),
                runs=r["run_diffs"])
    return src


def _block_rows(label, ncols):
    """(block, cells) for a tabular whose blocks start with \\multicolumn{..}{l}{\\emph{name}}."""
    out, blk = [], None
    for line in table_block(label).split(chr(10)):
        line = line.strip()
        mm = re.match(r"\\multicolumn\{\d+\}\{l\}\{\\emph\{([^}]*)\}", line)
        if mm:
            blk = mm.group(1)
            continue
        if "&" not in line or (BS + BS) not in line:
            continue
        cells = [c.strip() for c in line.split(BS + BS)[0].split("&")]
        if len(cells) == ncols:
            out.append((blk, cells))
    return out


def _counts(cell):
    """'3/0$^{\\mathrm{s}}$' -> ('3', '0', sign-consistent marker present)."""
    marked = "mathrm{s}" in cell
    c = cell.replace("$^{" + BS + "mathrm{s}}$", "").replace("$^" + BS + "ast$", "")
    a, b = plain(c).split("/")
    return a.strip(), b.strip(), marked


def check_crossds(bad):
    """tab:crossds -- XJTU-SY (guard added 2026-09-23), FEMTO and Ferrara x 11 detectors:
    median, mean and 95% CI, n+/n-, sign-consistency marker, sign-test p."""
    src = _runlevel_src()
    eq = {k: v for k, v in index(load("n20_d15_bootstrap_new_11det.csv"), ds_field="dataset").items()
          if k[0] in ("XJTU-SY", "FEMTO", "Ferrara")}
    n, seen = 0, set()
    for ds, cells in _block_rows("tab:crossds", 5):
        k = key_of(cells[0])
        if k is None or ds not in ("XJTU-SY", "FEMTO", "Ferrara"):
            continue
        s, e = src.get((ds, k)), eq.get((ds, k))
        tag = "T5 %s %s" % (ds, k)
        if s is None or e is None:
            bad.append((tag + " missing in source", "row present", "absent"))
            continue
        seen.add((ds, k))
        n += cmp_cell(tag + " median", cells[1], s["med"], bad)
        got, d = nums(cells[2]), decimals(cells[2])
        exp = (float(e["mean_diff_h"]), float(e["ci_lo_h"]), float(e["ci_hi_h"]))
        if len(got) != 3:
            bad.append((tag + " mean/CI parse", str(got), "3 values"))
        for val, x, t in zip(got, exp, ("mean", "CI-lo", "CI-hi")):
            if not matches(val, x, d):
                bad.append((tag + " " + t, str(val), round(x, d)))
            n += 1
        if not (-1.0 < exp[1] and exp[2] < 1.0):
            bad.append((tag + " equivalent at delta=1 h", "claimed", "violated"))
        n += 1
        a, b, marked = _counts(cells[3])
        if (a, b) != (s["npos"], s["nneg"]):
            bad.append((tag + " n+/n-", a + "/" + b, s["npos"] + "/" + s["nneg"]))
        n += 1
        if marked != s["same"]:
            bad.append((tag + " sign-consistent marker", str(marked), str(s["same"])))
        n += 1
        n += cmp_cell(tag + " sign-test p", cells[4], s["p"], bad)
    if len(seen) != 33:
        bad.append(("T5 rows parsed", str(len(seen)), 33))
    widest = max(max(abs(float(r["ci_lo_h"])), abs(float(r["ci_hi_h"]))) for r in eq.values())
    if widest >= 0.6:
        bad.append(("T5 caption: no endpoint reaches 0.6 h", "%.3f" % widest, "< 0.6"))
    return n + 1


def check_imsongc(bad):
    """tab:imsongc -- IMS per-run differences, median, n+/n-, p; ONGC post-fix minutes."""
    src = _runlevel_src()
    ongc = {r["short_name"]: r for r in load(ONGC_MINUTES)}
    n, seen = 0, 0
    for _, cells in _block_rows("tab:imsongc", 6):
        k = key_of(cells[0])
        if k is None:
            continue
        s, tag = src[("IMS", k)], "T6 IMS %s" % k
        seen += 1
        got = nums(cells[1])
        actual = [float(x) for x in s["runs"].replace("+", "").split(",")]
        if len(got) != 3:
            bad.append((tag + " run diffs parse", str(got), "3 values"))
        for a, b in zip(got, actual):
            if abs(round(b, 1) - a) > 1e-9:
                bad.append((tag + " run diff", str(a), round(b, 1)))
            n += 1
        n += cmp_cell(tag + " median", cells[2], s["med"], bad)
        a, b, marked = _counts(cells[3])
        if (a, b) != (s["npos"], s["nneg"]):
            bad.append((tag + " n+/n-", a + "/" + b, s["npos"] + "/" + s["nneg"]))
        # published IMS convention: tied runs are not sign-consistent (Deep SVDD)
        ties = sum(1 for v in actual if round(v, 1) == 0)
        if marked != (s["same"] and ties == 0):
            bad.append((tag + " sign-consistent marker", str(marked), str(s["same"] and ties == 0)))
        n += 2
        n += cmp_cell(tag + " sign-test p", cells[4], s["p"], bad)
        n += cmp_cell("T6 ONGC %s minutes" % k, cells[5],
                      float(ongc[ONGC_ROW_KEYS[k]][ONGC_MINUTES_COL]), bad)
    if seen != 11:
        bad.append(("T6 rows parsed", str(seen), 11))
    new_max = max(abs(float(r[ONGC_MINUTES_COL])) for r in ongc.values())
    old_max = max(abs(float(r["old_min"])) for r in ongc.values())
    if new_max > 1.5:
        bad.append(("T6 caption: ONGC about a minute or less", "%.2f min" % new_max, "<= 1.5 min"))
    if old_max <= 1.5:      # provenance: the pre-fix column must still break the caption
        bad.append(("T6 N-20 provenance: old_min fingerprint", "%.2f min" % old_max, "> 1.5 min"))
    return n + 2


def check_holm(bad):
    """The N=44 Holm family (now a tab:crossds caption sentence): the printed sign-test
    p of all 44 cells equals the post-fix family's raw p, every adjusted p is 1.00,
    nothing is rejected, and the smallest raw p is 0.125 (FEMTO, Transformer-AD)."""
    rows = load_holm_family()
    fam = {(r["dataset"], key_of(r["method"])): float(r["sign_test_p"]) for r in rows}
    printed = {}
    for ds, cells in _block_rows("tab:crossds", 5):
        if key_of(cells[0]):
            printed[(ds, key_of(cells[0]))] = cells[4]
    for _, cells in _block_rows("tab:imsongc", 6):
        if key_of(cells[0]):
            printed[("IMS", key_of(cells[0]))] = cells[4]
    n = 0
    for key, p in fam.items():
        if key not in printed:
            bad.append(("Holm family cell %s %s printed" % key, "absent", "present"))
            continue
        n += cmp_cell("Holm raw p %s %s" % key, printed[key], p, bad)
    for cond, label in ((len(rows) == 44, "family size N=44"),
                        (all(abs(float(r["holm_p"]) - 1.0) < 1e-12 for r in rows), "all adjusted p == 1.00"),
                        (not any(r["holm_reject"] == "True" for r in rows), "no hypothesis rejected"),
                        (not [r for r in rows if float(r["sign_test_p"]) < 0.05], "no raw p < 0.05")):
        if not cond:
            bad.append(("Holm caption: " + label, "claimed", "violated"))
        n += 1
    lo = min((float(r["sign_test_p"]), r["dataset"], r["method"]) for r in rows)
    if abs(lo[0] - 0.125) > 1e-12 or lo[1] != "FEMTO" or "Transformer" not in lo[2]:
        bad.append(("Holm N-20 provenance: smallest raw p", "%.3f %s %s" % lo, "0.125 FEMTO Transformer-AD"))
    return n + 1


def _imslead_src():
    src = {}
    for r in load("benchmark_IMS_leadtime_ci_invariant.csv"):
        if r["mode"] == "aggregate" and float(r["factor"]) == 1 and key_of(r["method"]):
            src[key_of(r["method"])] = r
    for r in load("d3_ocsvm_leadtime_ci.csv"):
        if (r["dataset"] == "IMS" and r["mode"] == "aggregate" and float(r["factor"]) == 1
                and key_of(r["method"]) == "ocsvm"):
            src["ocsvm"] = r
    return src


TRADEOFF_SOURCES = ("tradeoff_IMS.csv", "tradeoff_IMS_deepmodels.csv", "d3_ocsvm_tradeoff.csv")


def _tradeoff_src():
    src = {}
    for fn in TRADEOFF_SOURCES:
        for r in load(fn):
            k = key_of(r["method"])
            if k and r.get("dataset", "IMS") == "IMS":
                src[(k, float(r["percentile"]))] = (float(r["lead_time_hours_mean"]),
                                                    float(r["far_preonset_pct_mean"]))
    return src


def check_imsdet(bad):
    """tab:imsdet (old Tables 2, 12 and 15): raw lead + CI, PH, L at tau=.05/.10/.20 for all
    eleven IMS detectors. PH and L are ALSO re-derived from the threshold sweep, so the
    d9 file cannot drift from the trade-off table it summarises."""
    lead, trade = _imslead_src(), _tradeoff_src()
    d9 = {key_of(r["method"]): r for r in load("d9_tables_14_22_eleven.csv")}
    n, order = 0, []
    for cells in rows_of("tab:imsdet"):
        if len(cells) != 7 or key_of(cells[0]) is None:
            continue
        k = key_of(cells[0])
        tag, ld, r = "T2 %s" % k, lead[k], d9[k]
        order.append((k, float(r["PH_h"])))
        n += cmp_cell(tag + " raw lead", cells[1], float(ld["lead_time_hours_mean"]), bad)
        got, d = nums(cells[2]), decimals(cells[2])
        for val, x, t in zip(got, (float(ld["lead_time_hours_lo"]), float(ld["lead_time_hours_hi"])), ("lo", "hi")):
            if not matches(val, x, d):
                bad.append((tag + " CI-" + t, str(val), round(x, d)))
            n += 1
        sweep = [trade[(k, p)] for p in (95.0, 99.0, 99.5)]
        ph = max(x for x, _ in sweep)
        n += cmp_cell(tag + " PH", cells[3], float(r["PH_h"]), bad)
        if abs(ph - float(r["PH_h"])) > 1e-9:
            bad.append((tag + " PH != max swept lead", r["PH_h"], ph))
        n += 1
        for j, (col, tau) in enumerate((("L_tau05_h", 5), ("L_tau10_h", 10), ("L_tau20_h", 20))):
            n += cmp_cell(tag + " L tau=%d%%" % tau, cells[4 + j], float(r[col]), bad)
            ok = [x for x, far in sweep if far <= tau]
            if abs((max(ok) if ok else 0.0) - float(r[col])) > 1e-9:
                bad.append((tag + " L tau=%d%% re-derivation" % tau, r[col], max(ok) if ok else 0.0))
            n += 1
        if ("dagger" in cells[0]) != (float(r["L_tau10_h"]) == 0.0):
            bad.append((tag + " dagger iff no valid point at tau=0.10", cells[0], r["L_tau10_h"]))
        n += 1
    if len(order) != 11:
        bad.append(("T2 rows parsed", str(len(order)), 11))
    if [x for _, x in order] != sorted((x for _, x in order), reverse=True):
        bad.append(("T2 rows in PH order", str([k for k, _ in order]), "descending PH"))
    if [i for i, (k, _) in enumerate(order, 1) if k == "3sigma"] != [8]:
        bad.append(("T2 3-sigma is PH's eighth", str([k for k, _ in order]), "3sigma at 8"))
    if any(float(d9[k]["L_tau10_h"]) != 0.0 for k, _ in order[:7]):
        bad.append(("T2 top seven by PH all score L=0", "claimed", "violated"))
    return n + 3


def check_tradeoff(bad):
    src = _tradeoff_src()
    n, rows = 0, 0
    for cells in rows_of("tab:tradeoff"):
        if len(cells) != 7 or key_of(cells[0]) is None:
            continue
        k, rows = key_of(cells[0]), rows + 1
        for j, pct in enumerate((95.0, 99.0, 99.5)):
            ld, far = src[(k, pct)]
            n += cmp_cell("T12 %s p%g Ld" % (k, pct), cells[1 + 2 * j], ld, bad)
            n += cmp_cell("T12 %s p%g FAR" % (k, pct), cells[2 + 2 * j], far, bad)
            if ("dagger" in cells[2 + 2 * j]) != (far > 10.0):
                bad.append(("T12 %s p%g dagger" % (k, pct), cells[2 + 2 * j], far))
            n += 1
    if rows != 11:
        bad.append(("T12 rows parsed (eleven incl. one-class SVM)", str(rows), 11))
    return n


def check_gatedcontrast(bad):
    n, seen = 0, 0
    stats = {"raw": _gated_stats("raw"), "gated_D7": _gated_stats("gated_D7")}
    for cells in rows_of("tab:gatedcontrast"):
        if len(cells) != 7 or cells[0] not in GATED_ORDER:
            continue
        seen += 1
        for metric, off in (("raw", 1), ("gated_D7", 4)):
            med, npos, nneg, nzero, neff, ndet = stats[metric][cells[0]]
            tag = "T10 %s %s" % (metric, cells[0])
            n += cmp_cell(tag + " median", cells[off], med, bad)
            if plain(cells[off + 1]) != "%d/%d/%d" % (npos, nneg, nzero):
                bad.append((tag + " n+/n-/0", plain(cells[off + 1]), "%d/%d/%d" % (npos, nneg, nzero)))
            n += 1
            n += cmp_cell(tag + " n_eff", cells[off + 2], neff, bad)
            if ndet != 11:
                bad.append((tag + " detector count", str(ndet), 11))
            n += 1
    if seen != 4:
        bad.append(("T10 rows parsed", str(seen), 4))
    return n


DENOISE = {"Aggregate": "aggregate", "Decimate (raw)": "decimate", "Decimate + median": "median",
           "Decimate + moving avg": "moving_average", "Decimate + Kalman": "kalman",
           "Decimate + wavelet": "wavelet"}
MAG4 = {"three_sigma", "ewma", "cusum", "hotelling_t2"}


def check_mechanism(bad):
    """tab:mechanism (old Tables 21-22): noise-injection run-level diffs and the denoisers.
    Denoiser 'mean lead' is over ALL twelve chart-runs, valid or not (published convention);
    the aggregate and Kalman means are 75.6469 h, i.e. 75.6 -- the 75.7 once printed was a
    double rounding (defect N-29)."""
    noise = {("None (native)" if r["snr_db"] == "inf" else "%d dB" % float(r["snr_db"])): r
             for r in load("noise_snr_IMS_runlevel.csv")}
    den_rows = load("denoising_IMS.csv")
    n, seen = 0, 0
    for cells in rows_of("tab:mechanism"):
        if len(cells) == 4 and cells[0] in noise:
            r, tag, seen = noise[cells[0]], "T21 " + cells[0], seen + 1
            for a, b in zip(nums(cells[1]), [float(x) for x in r["run_diffs"].replace("+", "").split(",")]):
                if abs(round(b, 2) - a) > 1e-9:
                    bad.append((tag + " run diff", str(a), round(b, 2)))
                n += 1
            n += cmp_cell(tag + " mean", cells[2], float(r["mean_diff"]), bad)
            if plain(cells[3]) != "%s/3" % r["n_pos"]:
                bad.append((tag + " sign", plain(cells[3]), r["n_pos"] + "/3"))
            n += 1
        elif len(cells) == 3:
            key = next((v for lab, v in DENOISE.items() if cells[0].startswith(lab)), None)
            if key is None:
                continue
            sub = [r for r in den_rows if r["denoiser"] == key and r["short_name"] in MAG4]
            seen += 1
            n += cmp_cell("T22 %s mean lead" % key, cells[1],
                          statistics.mean(float(r["lead_time_hours"]) for r in sub), bad)
            nv = sum(1 for r in sub if r["valid_alarm"] == "True")
            if plain(cells[2]) != "%d/12" % nv or len(sub) != 12:
                bad.append(("T22 %s valid" % key, plain(cells[2]), "%d/12" % nv))
            n += 1
    if seen != 10:
        bad.append(("T21-22 rows parsed", str(seen), 10))
    return n


def _fmt_train(sec):
    if sec < 0.001:
        return "<1 ms"
    if sec < 0.1:
        return "%d ms" % round(sec * 1000)
    return ("%.2f s" if sec < 10 else "%.1f s") % sec


def check_compute(bad):
    """tab:hyperparams panel (b), old Table 17: training time and inference cost."""
    src = {}
    for fn in ("compute_cost_IMS_invariant.csv", "compute_cost_IMS_extra_invariant.csv"):
        for r in load(fn):
            src[key_of(r["method"])] = r
    n, seen = 0, 0
    for cells in rows_of("tab:hyperparams"):
        if len(cells) != 6:
            continue
        for off in (0, 3):
            k = key_of(cells[off]) if cells[off] else None
            if k is None or k not in src:
                continue
            r, seen = src[k], seen + 1
            if plain(cells[off + 1]) != _fmt_train(float(r["train_seconds"])):
                bad.append(("T17 %s train" % k, plain(cells[off + 1]), _fmt_train(float(r["train_seconds"]))))
            n += 1
            us = float(r["inference_us_per_window"])
            printed = nums(cells[off + 2])[0]
            if abs(printed - (round(us, 1) if us < 10 else round(us))) > 1e-9:
                bad.append(("T17 %s inference" % k, str(printed), us))
            n += 1
    if seen != 11:
        bad.append(("T17 detectors parsed", str(seen), 11))
    return n


def check_conformal_ims(bad):
    """fig:conformal caption, panel (a) values (old Table 11) from calibration_IMS.csv."""
    txt = (TEX.parent / "gen" / "conformal_values.tex").read_text(encoding="utf-8")
    if BS + "ConformalPanelA" not in tex_source().split(BS + "begin{document}")[1]:
        bad.append(("Fig4 caption uses the generated panel-(a) values", "absent", "present"))
    rows = load("calibration_IMS.csv")
    n = 1
    for run, lab in (("1st_test", "test 1"), ("2nd_test", "test 2"), ("3rd_test", "test 3")):
        seg = txt.split(lab, 1)[1].split(";")[0]
        got = [float(x) for x in re.findall(r"\d+\.\d+", seg)]
        exp = [next(float(r["empirical_far"]) for r in rows
                    if r["run"] == run and abs(float(r["alpha"]) - a) < 1e-9)
               for a in (0.01, 0.05, 0.10, 0.20)]
        if len(got) != 4:
            bad.append(("Fig4a %s parse" % lab, str(got), "4 values"))
        for g, e in zip(got, exp):
            if not matches(g, e, 2):
                bad.append(("Fig4a %s FAR" % lab, str(g), round(e, 2)))
            n += 1
    return n


def check_prose_additions(bad):
    """Numbers stated in prose by the shortening pass (G3, D18, ONGC, N-29)."""
    body = tex_source()
    n = 0

    def need(cond, label, printed="", expected=""):
        nonlocal n
        n += 1
        if not cond:
            bad.append(("prose: " + label, printed, expected))

    g3 = load("rg3_raw_invariance.csv")
    need(len(g3) == 99, "G3 99 dataset x detector x indicator cells", str(len(g3)), 99)
    need(max(abs(float(r["max_abs_dev_run_diff_h"])) for r in g3) == 0.0, "G3 max |deviation| 0.000 h")
    need(sum(int(r["row_nan_mismatch"]) for r in g3) == 0, "G3 no NaN mismatch")
    need("0.000~h across all 99 dataset" in body, "G3 sentence present")
    # D18: Hotelling T2 on IMS across the five gap draws
    gaps = load("d18_gap_injection_multiseed.csv")
    base = {r["run"]: float(r["lead"]) for r in gaps
            if r["dataset"] == "IMS" and r["short_name"] == "hotelling_t2" and float(r["gap"]) == 0.0}
    per = {}
    for r in gaps:
        if r["dataset"] == "IMS" and r["short_name"] == "hotelling_t2" and float(r["gap"]) == 0.2:
            per.setdefault(r["gap_seed"], {})[r["run"]] = (float(r["lead"]), r["valid"] == "True")
    means = [statistics.mean(v for v, ok in d.values() if ok) for d in per.values()]
    collapsed = [s for s, d in per.items() if abs(d["3rd_test"][0] - base["3rd_test"]) > 1.0]
    changed = {run for d in per.values() for run, (v, _) in d.items() if abs(v - base[run]) > 1e-9}
    need(len(collapsed) == 2 and len(per) == 5, "D18 collapses in 2 of 5 draws", str(len(collapsed)), 2)
    need(changed == {"3rd_test"}, "D18 driven by a single run", str(changed), "{3rd_test}")
    for v, label in ((statistics.mean(means), "134.9"), (min(means), "58.0"), (max(means), "186.1"),
                     (base["3rd_test"], "315.9"), (min(d["3rd_test"][0] for d in per.values()), "59.7")):
        need(abs(round(v, 1) - float(label)) < 1e-9, "D18 value " + label, "%.1f" % v, label)
    worst, frozen = 0.0, []
    for det in ("three_sigma", "ewma", "cusum", "hotelling_t2", "isolation_forest"):
        b = gap_cell("IMS", det, 0.0)
        seeds = {}
        for r in gaps:
            if (r["dataset"] == "IMS" and r["short_name"] == det and float(r["gap"]) == 0.05
                    and r["valid"] == "True"):
                seeds.setdefault(r["gap_seed"], []).append(float(r["lead"]))
        dev = max(abs(statistics.mean(v) - b) for v in seeds.values())
        worst = max(worst, dev)
        if dev == 0.0:
            frozen.append(det)
    need(sorted(frozen) == ["ewma", "hotelling_t2"], "D18 5%: Hotelling and EWMA unchanged", str(frozen))
    need(abs(round(worst, 2) - 0.83) < 1e-9, "D18 5%: max per-draw deviation 0.83 h", "%.3f" % worst, "0.83")
    need("collapses in 2 of the 5 draws" in body, "D18 sentence present")
    # ONGC case study: factor-1 leads from the post-fix rerun (factor 1 is N-20-invariant anyway)
    lead = {r["short_name"]: float(r["lead_time_hours"]) for r in load("n20_rerun_long_ONGC.csv")
            if float(r["factor"]) == 1 and r["mode"] == "aggregate"}
    need(len(lead) == 11 and len([v for v in lead.values() if 30.0 <= round(v, 1) <= 35.5]) == 9,
         "ONGC nine of eleven alarm 30-35 h")
    need(len([v for v in lead.values() if 34.9 <= round(v, 1) <= 35.3]) == 7, "ONGC seven within 34.9-35.3 h")
    for k, v in (("cusum", 33.9), ("hotelling_t2", 30.4), ("rms_trend", 22.8), ("deep_svdd", 0.0)):
        need(abs(round(lead[k], 1) - v) < 1e-9, "ONGC %s lead %.1f h" % (k, v), "%.1f" % lead[k], v)
    need("every detector achieves a long warning" not in body, "ONGC overclaim removed")
    need("aggregation's 75.6~h" in body and "75.7" not in body, "N-29 corrected 75.6 in prose")
    return n
