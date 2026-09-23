"""Phase 5 (layout, template-safe): remove \\FloatBarrier before the headings listed in
argv. A barrier forces every pending float out before the next heading and strands text
(pp. 20-24 rendered 40-60% empty). The barrier after the bibliography (before Appendix A)
stays, so appendix floats cannot drift into the references.

Usage: python apply_p5_barriers.py "Appendix B" "Appendix C" ...
"""
import pathlib, sys

TEX = pathlib.Path(__file__).resolve().parents[2] / "paper/files/scada_ijphm.tex"
s = TEX.read_text(encoding="utf-8")
for head in sys.argv[1:]:
    star = head.startswith(("Appendix", "Ack"))
    old = "\\FloatBarrier\n\\section%s{%s" % ("*" if star else "", head)
    assert s.count(old) == 1, (s.count(old), head)
    s = s.replace(old, old.split("\n", 1)[1])
    print("removed barrier before", head)
TEX.write_text(s, encoding="utf-8")
