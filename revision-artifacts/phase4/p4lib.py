"""Shared helper for the Phase 4 prose-compression scripts.

Paragraphs in scada_ijphm.tex are single source lines, so a paragraph is replaced by
locating the ONE line that starts with a given prefix. Every edit asserts uniqueness;
save() refuses to write if a citation key disappeared or a new backslash-apostrophe
(LaTeX acute accent, renders wrong silently) was introduced.
"""
import pathlib, re

TEX = pathlib.Path(__file__).resolve().parents[2] / "paper/files/scada_ijphm.tex"
ACUTE = re.compile(r"\\'[A-Za-z]")


class Doc:
    def __init__(self):
        self.s = TEX.read_text(encoding="utf-8")
        self.cites0 = self.cites()
        self.acute0 = len(ACUTE.findall(self.s))

    def cites(self):
        return sorted({k.strip() for m in re.finditer(r"\\cite[A-Za-z]*\{([^}]*)\}", self.s)
                       for k in m.group(1).split(",")})

    def _line(self, prefix):
        lines = self.s.split("\n")
        hits = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
        assert len(hits) == 1, (len(hits), prefix[:70])
        return lines, hits[0]

    def para(self, prefix, new):
        """Replace the whole source line that starts with `prefix` (unique)."""
        lines, i = self._line(prefix)
        lines[i] = new
        self.s = "\n".join(lines)

    def drop(self, prefix):
        """Delete the paragraph line starting with `prefix` and one following blank line."""
        lines, i = self._line(prefix)
        del lines[i]
        if i < len(lines) and lines[i].strip() == "":
            del lines[i]
        self.s = "\n".join(lines)

    def sub(self, old, new):
        assert self.s.count(old) == 1, (self.s.count(old), old[:70])
        self.s = self.s.replace(old, new)

    def save(self):
        lost = set(self.cites0) - set(self.cites())
        assert not lost, "citations lost: %s" % sorted(lost)
        assert len(ACUTE.findall(self.s)) <= self.acute0, "new backslash-apostrophe introduced"
        TEX.write_text(self.s, encoding="utf-8")
        print("saved; citation keys kept:", len(self.cites()))
