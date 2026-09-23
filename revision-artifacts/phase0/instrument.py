"""Build an instrumented COPY of the manuscript for Phase 0 measurement.

Never touches paper/files/scada_ijphm.tex. Inserts \pdfsavepos markers:
  - heading markers are prepended to the FIRST PARAGRAPH after each heading
    (horizontal mode). A marker placed in vertical mode right after a heading
    creates a legal page break (whatsit followed by \parskip glue) and was
    measured to move Sec. 6.2's heading from p.9 to p.8, so that is avoided.
  - begin/end of every float environment (inside the float box: no effect on
    the main vertical list)
  - \AtEndDocument
Output lines in <job>.mpos: TAG;inputline;page;x_sp;y_sp
Validation: the instrumented PDF's per-page text must equal the real PDF's.
"""
import re, shutil, pathlib, sys

SRC = pathlib.Path(r"D:\scada\paper\files")
OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
for f in SRC.iterdir():
    if f.suffix in {".cls", ".bib", ".png", ".bst", ".sty"}:
        shutil.copy2(f, OUT / f.name)

lines = (SRC / "scada_ijphm.tex").read_text(encoding="utf-8").split("\n")

PREAMBLE = r"""
\usepackage{etoolbox}
\newwrite\mpfile
\immediate\openout\mpfile=\jobname.mpos
\newcommand\MP[1]{\pdfsavepos\edef\mptmp{\noexpand\write\noexpand\mpfile{#1;\the\inputlineno;\noexpand\thepage;\noexpand\the\noexpand\pdflastxpos;\noexpand\the\noexpand\pdflastypos}}\mptmp}
\newcounter{mpfl}
% \gdef adds no node to the main vertical list; the markers themselves are
% emitted INSIDE the float box (\@floatboxreset opens it; \AtEndEnvironment
% runs before the box closes), so they measure the float, not its anchor.
\AtBeginEnvironment{figure}{\gdef\mpenv{figure}}\AtEndEnvironment{figure}{\MP{FE-\mpenv-\arabic{mpfl}}}
\AtBeginEnvironment{figure*}{\gdef\mpenv{figure*}}\AtEndEnvironment{figure*}{\MP{FE-\mpenv-\arabic{mpfl}}}
\AtBeginEnvironment{table}{\gdef\mpenv{table}}\AtEndEnvironment{table}{\MP{FE-\mpenv-\arabic{mpfl}}}
\AtBeginEnvironment{table*}{\gdef\mpenv{table*}}\AtEndEnvironment{table*}{\MP{FE-\mpenv-\arabic{mpfl}}}
\AtBeginEnvironment{algorithm}{\gdef\mpenv{algorithm}}\AtEndEnvironment{algorithm}{\MP{FE-\mpenv-\arabic{mpfl}}}
\makeatletter
\g@addto@macro\@floatboxreset{\global\advance\c@mpfl by 1 \MP{FT-\mpenv-\arabic{mpfl}}}
\makeatother
\makeatletter\let\mpoldmc\@makecaption
\long\def\@makecaption#1#2{\MP{CB}\mpoldmc{#1}{#2}\MP{CE}}\makeatother
\AtEndDocument{\MP{END}\immediate\write\mpfile{PAGEHEIGHT;\the\pdfpageheight;TEXTHEIGHT;\the\textheight;COLW;\the\columnwidth;TEXTW;\the\textwidth}}
"""

sec_re = re.compile(r"^\s*\\(section|subsection|subsubsection)\*?\{")
float_begin = re.compile(r"^\s*\\begin\{(figure\*?|table\*?|algorithm)\}")
skip_prefix = ("%", r"\label", r"\section", r"\subsection", r"\subsubsection",
               r"\end{", r"\FloatBarrier", r"\clearpage")

# heading line (1-based) -> index of paragraph line that receives its marker
targets = {}
i = 0
n = len(lines)
while i < n:
    if sec_re.match(lines[i]):
        j = i + 1
        # a heading can carry its own first sentence on the same line
        # (e.g. "\subsection{...}\label{...}" then text on next line) -- scan on
        while j < n:
            s = lines[j].strip()
            m = float_begin.match(lines[j])
            if m:
                env = m.group(1)
                while j < n and ("\\end{%s}" % env) not in lines[j]:
                    j += 1
                j += 1
                continue
            if not s or s.startswith(skip_prefix) or sec_re.match(lines[j]):
                j += 1
                continue
            break
        targets.setdefault(j, []).append(i + 1)
    i += 1

out = []
for idx, ln in enumerate(lines):
    if ln.startswith(r"\begin{document}"):
        out.append(PREAMBLE)
    if idx in targets:
        marks = "".join(r"\MP{S-%d}" % h for h in targets[idx])
        ln = r"\leavevmode" + marks + ln if not ln.lstrip().startswith(r"\noindent") else \
             ln.replace(r"\noindent", r"\noindent" + marks, 1)
    out.append(ln)

(OUT / "scada_ijphm.tex").write_text("\n".join(out), encoding="utf-8")
for t, hs in sorted(targets.items()):
    print(hs, "->", t + 1, lines[t][:60].encode("ascii", "replace").decode())
