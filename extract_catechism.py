#!/usr/bin/env python3
"""
Extract the Q&As from your copy of "To Be a Christian" (Approved Edition PDF)
into catechism.json for The Abbey Daily app.

Usage:
    pip install pypdf
    python3 extract_catechism.py To-Be-a-Christian.pdf

This produces catechism.json in the same folder. Upload it to the root of
your GitHub Pages repository, next to index.html.
"""

import json
import re
import sys

KEEP_HYPHEN_PREFIXES = (
    "self", "god", "christ", "non", "co", "all", "well", "ever",
    "life", "cross", "spirit", "sin", "one", "law", "faith",
)


def extract_text(pdf_path):
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def is_noise(line):
    s = line.strip()
    if not s:
        return True
    if re.fullmatch(r"\d{1,3}(\s+\d{1,3})*", s):     # page numbers / printer keys
        return True
    if re.fullmatch(r"part[\s ]*[ivx]+", s.lower().replace("\u00a0", " ")):
        return True
    if re.fullmatch(r"[ivxlcdm]{1,6}", s.lower()):  # roman-numeral folios
        return True
    toks = s.split()
    # Letter-spaced part titles, e.g. "b e l i e v i n g"
    if len(toks) >= 4 and all(len(t) <= 2 for t in toks) and s == s.lower():
        return True
    # Running heads with a page number, e.g. "the ten commandments  91"
    if re.fullmatch(r"[a-z\u2019' \u2013-]{4,60}\s+\d{1,3}", s) and s == s.lower():
        return True
    if re.fullmatch(r"\d{1,3}\s+[a-z\u2019' \u2013-]{4,60}", s) and s == s.lower():
        return True
    return False


def join_wrapped(parts):
    """Join line fragments, repairing end-of-line hyphenation."""
    out = ""
    for part in parts:
        p = part.replace("\u00a0", " ").replace("\u00ad", "-").strip()
        if not p:
            continue
        if out.endswith("-"):
            stem = out.rstrip("-")
            word = stem.rsplit(" ", 1)[-1].lower()
            if word in KEEP_HYPHEN_PREFIXES:
                out = out + p                     # keep the hyphen
            else:
                out = stem + p                    # de-hyphenate the wrap
        elif re.search(r"\s-$", out):
            out = re.sub(r"\s-$", "", out) + p    # "con -" + "cerned"
        else:
            out = (out + " " + p) if out else p
    return re.sub(r"\s+", " ", out).strip()


DIGIT_PAREN = re.compile(r"\([^()]*\d[^()]*\)")
POLLUTION_STARTS = ("Concluding Prayer", "A Prayer", "A Historic", "An Ancient", "Prayers of", "Prayers for")

# pypdf occasionally splits words across kerning boundaries; repair known cases
RESPACE = [
    (re.compile(r"Co\s?rin\s?thi\s?ans"), "Corinthians"),
    (re.compile(r"Reve\s?la\s?tion"), "Revelation"),
    (re.compile(r"Roma\s?ns\b"), "Romans"),
    (re.compile(r"Roman\s+s\b"), "Romans"),
    (re.compile(r"Jo\s+hn\b"), "John"),
    (re.compile(r"Thes\s?sa\s?lo\s?nians"), "Thessalonians"),
]


BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
    "Judges", "Ruth", "Samuel", "Kings", "Chronicles", "Ezra", "Nehemiah",
    "Esther", "Job", "Psalms", "Psalm", "Proverbs", "Ecclesiastes",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea",
    "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", "Mark",
    "Luke", "John", "Acts", "Romans", "Corinthians", "Galatians",
    "Ephesians", "Philippians", "Colossians", "Thessalonians", "Timothy",
    "Titus", "Philemon", "Hebrews", "James", "Peter", "Jude", "Revelation",
]
BOOK_PATS = [
    (re.compile(r"\s?".join(re.escape(c) for c in b) + r"(?=\s*\d)"), b)
    for b in BOOKS
]


def respace(text):
    for pat, rep in RESPACE:
        text = pat.sub(rep, text)
    for pat, rep in BOOK_PATS:
        text = pat.sub(rep, text)
    return text


def trim_answer(raw):
    """Every answer ends with proof texts in parentheses (or, for recited
    texts, simply ends). Anything after that — chapter headings, section
    intros, concluding prayers — belongs to the book's flow, not the answer.
    Scan parenthetical groups from last to first: cut after the first one
    whose tail is empty or looks like page furniture."""
    raw = raw.strip()
    parens = list(DIGIT_PAREN.finditer(raw))
    # Forward: the first reference group followed by a lowercase heading or a
    # concluding-prayer block marks the true end of the answer.
    for m in parens:
        tail = raw[m.end():].strip()
        if re.match(r"^[.,]?\s*[a-z\u201c]", tail) or tail.startswith(POLLUTION_STARTS):
            return raw[: m.end()]
    if parens and raw[parens[-1].end():].strip() == "":
        return raw[: parens[-1].end()]
    # No terminal reference group: strip a trailing all-lowercase heading
    m2 = re.match(r"^(.*[.\u201d)?!])\s+[a-z\u201c][^A-Z]*$", raw, re.S)
    if m2:
        return m2.group(1).strip()
    return raw


def parse(text):
    lines = text.split("\n")
    entries, expected, i, n = [], 1, 0, len(lines)
    while i < n:
        line = lines[i].strip()
        m = re.match(r"^(\d{1,3})\.\s*(.*)$", line)
        if m and int(m.group(1)) == expected:
            def q_done(parts):
                q = join_wrapped(parts)
                if q.endswith("?"):
                    return True
                # Short imperative prompts: "Recite the Ten Commandments."
                return q.endswith(".") and len(q) <= 80
            qparts = [m.group(2)] if m.group(2).strip() else []
            j = i + 1
            while j < n and not q_done(qparts):
                if not is_noise(lines[j]):
                    qparts.append(lines[j])
                j += 1
                if len(qparts) > 5:
                    break
            question = join_wrapped(qparts)
            if not q_done([question]):
                i += 1
                continue                            # false positive
            aparts, k = [], j
            next_pat = re.compile(r"^%d\.\s" % (expected + 1))
            next_pat_bare = re.compile(r"^%d\.$" % (expected + 1))
            while k < n:
                nxt = lines[k].strip()
                if next_pat.match(nxt) or next_pat_bare.match(nxt):
                    break
                if not is_noise(nxt):
                    aparts.append(nxt)
                k += 1
                if k - j > 200:
                    break
            answer = respace(trim_answer(join_wrapped(aparts)))
            question = respace(question)
            entries.append({"n": expected, "q": question, "a": answer})
            expected += 1
            i = k
        else:
            i += 1
    return entries


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    text = extract_text(sys.argv[1])
    entries = parse(text)
    print(f"Found {len(entries)} questions.")
    if entries:
        print(f"First: {entries[0]['n']}. {entries[0]['q']}")
        print(f"Last:  {entries[-1]['n']}. {entries[-1]['q']}")
    with open("catechism.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    print("Wrote catechism.json — upload it next to index.html in your repo.")


if __name__ == "__main__":
    main()
