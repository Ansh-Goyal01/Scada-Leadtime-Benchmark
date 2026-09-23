# Renumbering map (old 30-page build -> new 22-page build)

| Old | Label | New | Note |
|---|---|---|---|
| Table 1 | `tab:datasets` | Table 1 |  |
| Algorithm 1 | `alg:onset` | Algorithm 1 |  |
| Table 2 | `tab:imslead` | merged into Table 2 | tab:imsdet |
| Figure 1 | `fig:health` | Figure 1 |  |
| Table 3 | `tab:onset` | Table 3 |  |
| Table 4 | `tab:robust` | Table 4 |  |
| Table 5 | `tab:crossds` | Table 5 |  |
| Table 6 | `tab:equiv` | merged into Table 5 | tab:crossds |
| Figure 2 | `fig:crossdataset` | Figure 2 |  |
| Figure 3 | `fig:sweep` | Figure 3 |  |
| Table 7 | `tab:imssweep` | merged into Table 6 | tab:imsongc |
| Table 8 | `tab:holm` | merged into Table 5 | tab:crossds (caption) |
| Table 9 | `tab:perbearing` | Table 7 | renumbered |
| Table 10 | `tab:gatedcontrast` | Table 8 | renumbered |
| Table 11 | `tab:conformal` | merged into Figure 4 | fig:conformal (caption) |
| Figure 4 | `fig:conformal` | Figure 4 |  |
| Figure 5 | `fig:tradeoffs` | Figure 5 |  |
| Table 12 | `tab:farbudget` | merged into Table 2 | tab:imsdet |
| Table 13 | `tab:tradeoff` | Table 9 | renumbered |
| Table 14 | `tab:ablation_general` | Table 10 | renumbered |
| Table 15 | `tab:phrank` | merged into Table 2 | tab:imsdet |
| Figure 6 | `fig:mintrain` | Figure 6 |  |
| Table 16 | `tab:hyperparams` | Table 11 | renumbered |
| Table 17 | `tab:compute` | merged into Table 11 | tab:hyperparams (b) |
| Table 18 | `tab:deeparch` | Table 12 | renumbered |
| Table 19 | `tab:basestats` | Table 13 | renumbered |
| Table 20 | `tab:d17label` | Table 14 | renumbered |
| Table 21 | `tab:noise` | merged into Table 15 | tab:mechanism (a) |
| Table 22 | `tab:denoise` | merged into Table 15 | tab:mechanism (b) |
| Table 23 | `tab:ongc` | merged into Table 6 | tab:imsongc |

Sections: unchanged numbering (no section added or removed); Section 7.1 condensed.
Counts: tables 23 -> 15, figures 6 -> 6, algorithm 1 -> 1.

## Response-to-Review lines citing a number that has changed

Old numbering in the letter refers to the 30-page build unless stated; check each line.

- L27: Table 8 -> Table 5 (tab:crossds (caption))  | `> 3. **The claim that "decimation is never better" has been removed** throughout, because it was never supported. It is replaced by a bound `
- L49: Table 16 -> Table 11  | `> "the deep reconstruction models are stated to have no valid operating point 'regardless of threshold' (Section 6.1) but are omitted from t`
- L51: Table 16 -> Table 11  | `**Response.** Correct, and the claim was unsupported as written. We have run the three deep reconstruction models through the same threshold`
- L52: Table 16 -> Table 11  | `**Change.** Table 16 (three rows added); §6.1 ⟦…⟧.`
- L58: Table 11 -> Figure 4 (fig:conformal (caption))  | `**Change.** §4.5; Table 11 recomputed at N = 44; §6.4 family size and FWER; result tables gain the one-class SVM row.`
- L79: Table 21 -> Table 15 (tab:mechanism (a))  | `### D14 / D15. Tables 21 and 23`
- L80: Table 21 -> Table 15 (tab:mechanism (a)); Table 23 -> Table 6 (tab:imsongc)  | `> "Table 21 may be unnecessary: its results are true by construction and already described in the text. Table 23 duplicates the Figure 10 re`
- L83: Table 21 -> Table 15 (tab:mechanism (a))  | `**Change.** Tables 21 and 23 deleted; §6.12 ⟦…⟧; §6.13 ⟦…⟧.`
- L103: Table 8 -> Table 5 (tab:crossds (caption))  | `### D19. "Decimation is never better" contradicted by Table 8`
- L104: Table 8 -> Table 5 (tab:crossds (caption))  | `> "the introduction's 'decimation is never better' is contradicted by the paper's own Table 8 (Isolation Forest on FEMTO, negative in six of`
- L110: Table 8 -> Table 5 (tab:crossds (caption))  | `*Second, the specific counterexample the reviewer identified was an artifact of a defect in our pipeline, which we found and fixed while ans`
- L113: Table 8 -> Table 5 (tab:crossds (caption)); Table 9 -> Table 7; Table 11 -> Figure 4 (fig:conformal (caption))  | `**Change.** Abstract; §1 (finding, contribution 4); §6.4 and Table 8; §6.5 and Table 9; Table 11; §7 (discussion, summary); §9; Appendix D.2`
- L128: Table 21 -> Table 15 (tab:mechanism (a)); Table 23 -> Table 6 (tab:imsongc)  | `> "the paper is much longer than needed: the headline finding is restated many times, Table 21 and Table 23 can be cut, Section 7.4 duplicat`
- L130: Table 21 -> Table 15 (tab:mechanism (a)); Table 15 -> Table 2 (tab:imsdet)  | `**Response.** §7.4 has been deleted in full, Tables 21 and 23 removed, and ⟦Tables 15 and 20 moved to the appendix⟧. Occurrences of the phra`
- L182: Table 15 -> Table 2 (tab:imsdet); Table 21 -> Table 15 (tab:mechanism (a))  | `**Response.** ⟦Tables 15 and 20 have been moved to the appendix; Tables 21 and 23 removed entirely per Reviewer D.⟧ The main text now carrie`
- L188: Table 11 -> Figure 4 (fig:conformal (caption)); Table 16 -> Table 11  | `**Response.** Table 11 is now grouped by dataset with rule separators, and the uniformly-"no" rejection column has been replaced by a single`
- L189: Table 11 -> Figure 4 (fig:conformal (caption))  | `**Change.** Tables 11, 16, 19, 24.`

## CAVEAT on the letter lines above
IJPHM-response-letter-draft.md cites table numbers in an OLDER numbering than the 30-page
build (IJPHM-PROGRESS.md: author-facing numbers ran about +4 ahead of the compiled PDF --
stale pre-Group-B numbering). Example: the letter's "Table 16 (three rows added)" is the
trade-off table (`tab:tradeoff`, now Table 9), not `tab:hyperparams`. The 17 flagged lines
are therefore the lines that MUST be re-mapped, but each must be re-mapped by label, by
reading what the sentence describes, not by the arithmetic in the flag. No line cites
180.3, 75.7, "34-35 h" or a page count.
