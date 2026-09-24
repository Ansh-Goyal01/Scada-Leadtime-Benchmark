# IJPHM revision — submission checklist

Everything below is for the author to do. Nothing has been pushed, released or uploaded.
Local state when this was written (2026-09-24, after the final submission pass):

- `main` contains the merged `ijphm-shorten` work plus the final submission pass (Eq. 5 validity counts,
  internal IDs removed, abstract and factual corrections, figures/bibliography/layout, letter).
  Annotated tag **`v1.3.0`** is on the final commit of that pass. It was first created on the merge commit
  on 2026-09-23, was never pushed to either remote, and was recreated on the final commit (2026-09-24).
- `v1.3.0` exists on neither remote (re-checked 2026-09-24 with `git ls-remote --tags` against `origin` and `gitlab`).
- Remote `main` (`92bb8a7`) is an ancestor of local `main`, so the push below is a fast-forward.
- `CITATION.cff` says `version: 1.3.0`, `date-released: "2026-09-24"`. If you release on a later
  day, update the date first; after the tag is pushed, do not move it (tags are never reused).

## Files in this folder

| File | What it is |
|---|---|
| `scada_ijphm_revised.pdf` | Revised manuscript: 22 pages, 15 tables, 6 figures (byte-identical to `paper/files/scada_ijphm.pdf` at the tag) |
| `response_to_review.pdf` | Response to Review, 13 pages (13 disclosure items), built from `IJPHM-Response-to-Review-FINAL.md` (author box removed) |

Rebuild both with `python revision-artifacts/final/make_submission.py` if the sources change.

## 1. Pre-flight (read-only)

- [ ] `git log --oneline -3 main` shows the merge commit, and `git describe --tags main` prints `v1.3.0`.
- [ ] `python paper/verify_tables.py` ends with "All checked table numbers match their source files." (1040 values).
- [ ] `python -m src.eq5_validity` regenerates the `eq5_*.csv` files with no diff (validity counts under Eq. 5).
- [ ] `python revision-artifacts/phase1/negative_tests.py` exits 0 (all 9 guards RED).
- [ ] `python revision-artifacts/final2/negative_tests_final2.py` exits 0 (the 3 final-pass guards RED).
- [ ] `python -m pytest -q` shows 181 tests with one known failure,
      `test_metropt_loads_with_expected_parameters` (it expects the fixture, and the real MetroPT3 CSV is present locally).
      A clean clone without the real CSV should pass all 181.

## 2. Push `main`

- [ ] `git push origin main`
- [ ] `git push gitlab main` (mirror)
- [ ] On GitHub, confirm `results/tables/` and the ONGC derived files named in the Data Availability section are present on `main`.

## 3. Push the tag

- [ ] `git push origin v1.3.0`
- [ ] `git push gitlab v1.3.0`
- [ ] `git ls-remote --tags origin v1.3.0` returns the same object as `git rev-parse v1.3.0`.

## 4. Create the GitHub Release on `v1.3.0`

- [ ] GitHub → Releases → *Draft a new release* → choose the existing tag `v1.3.0` (do **not** create a new tag).
- [ ] Title: `v1.3.0 — IJPHM revision (shortened, 22 pages)`. Publish, not draft. Zenodo mints only on a published Release, not on a bare tag push.

## 5. Confirm Zenodo minted the new version

- [ ] Open the concept DOI `10.5281/zenodo.20719076` and confirm a new version `v1.3.0` is listed, with its own version DOI.
- [ ] Confirm the archive contains `results/tables/` (earlier Zenodo versions had none) and no ONGC raw or processed data.
- [ ] If no version appears within ~15 minutes, check GitHub → Settings → Webhooks for the Zenodo hook's delivery log,
      and Zenodo → GitHub for whether the repository toggle is still on.
- [ ] The paper cites the concept DOI, which always resolves to the latest version, so no manuscript change is needed.

## 6. Upload to the EXISTING IJPHM submission

- [ ] Log in to the IJPHM system and open the **existing** submission for this manuscript. Do **not** start a new submission.
- [ ] Upload `scada_ijphm_revised.pdf` as the revised manuscript.
- [ ] Upload `response_to_review.pdf` as the response to reviewers.
- [ ] Before submitting, confirm that the repository URL and tag the letter cites (`v1.3.0`) resolve publicly (steps 2–5 done).
