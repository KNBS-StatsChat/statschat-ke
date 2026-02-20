from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document
from docx.shared import Pt


@dataclass
class QuestionBlock:
    section: str
    qid: str
    prompt_lines: list[str] = field(default_factory=list)
    type_line: str | None = None
    option_lines: list[str] = field(default_factory=list)
    code_blocks: list[str] = field(default_factory=list)

    def question_text(self) -> str:
        text = " ".join(x.strip() for x in self.prompt_lines if x.strip())
        text = re.sub(r"\s+", " ", text).strip()
        return f"{self.qid}. {text}" if text else f"{self.qid}."

    def is_choice(self) -> bool:
        if not self.type_line:
            return False
        tl = self.type_line.lower()
        return "multiple choice" in tl or "checkbox" in tl or "choice" in tl

    def is_multi_answer(self) -> bool:
        if not self.type_line:
            return False
        tl = self.type_line.lower()
        return "checkbox" in tl or "multiple answers" in tl


QUESTION_RE = re.compile(r"^\*\*(?P<qid>[A-Z]\d+)\.\s*(?P<prompt>.+?)\*\*\s*$")
HEADING_RE = re.compile(r"^##\s+(?P<h>.+?)\s*$")
BULLET_RE = re.compile(r"^\s*-\s+(?P<item>.+?)\s*$")
TYPE_RE = re.compile(r"^\s*Type\s*:\s*(?P<t>.+?)\s*$", re.IGNORECASE)
CODE_FENCE_RE = re.compile(r"^\s*```")


def parse_markdown(md_text: str) -> tuple[str, list[str], list[QuestionBlock]]:
    lines = md_text.splitlines()

    title = "StatsChat Participant Pre-Course Questionnaire"
    intro_lines: list[str] = []
    blocks: list[QuestionBlock] = []

    # Title
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Intro text: between "## Intro text" and first "---"
    in_intro = False
    for line in lines:
        if line.strip() == "## Intro text":
            in_intro = True
            continue
        if in_intro:
            if line.strip().startswith("---"):
                break
            if line.strip():
                intro_lines.append(line.strip())

    current_section = ""
    current: QuestionBlock | None = None
    in_code = False
    code_buf: list[str] = []

    def flush() -> None:
        nonlocal current
        if not current:
            return
        # Drop empty blocks
        if current.qid and (
            current.prompt_lines or current.option_lines or current.code_blocks
        ):
            blocks.append(current)
        current = None

    for line in lines:
        if line.strip().startswith("# Internal scoring rubric"):
            break

        m_head = HEADING_RE.match(line)
        if m_head:
            flush()
            h = m_head.group("h").strip()
            if not h.lower().startswith("intro"):
                current_section = h
            continue

        if CODE_FENCE_RE.match(line):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                if current is not None and code_buf:
                    current.code_blocks.append("\n".join(code_buf).strip("\n"))
            continue

        if in_code:
            code_buf.append(line.rstrip("\n"))
            continue

        m_q = QUESTION_RE.match(line.strip())
        if m_q:
            flush()
            current = QuestionBlock(
                section=current_section,
                qid=m_q.group("qid"),
                prompt_lines=[m_q.group("prompt").strip()],
            )
            continue

        if current is None:
            continue

        m_type = TYPE_RE.match(line)
        if m_type:
            current.type_line = m_type.group("t").strip()
            continue

        m_b = BULLET_RE.match(line)
        if m_b:
            item = m_b.group("item").strip().strip("`")
            # Only treat bullets as options if this question is a choice-type.
            # Otherwise, bullets are explanatory examples and should stay in prompt.
            if current.is_choice():
                current.option_lines.append(item)
            else:
                current.prompt_lines.append(item)
            continue

        # Ignore empty lines
        if not line.strip():
            continue

        # Ignore Markdown separators
        if line.strip().startswith("---"):
            continue

        # Ignore "Type" lines without colon (e.g., "Type text box")
        if line.strip().lower().startswith("type"):
            current.type_line = line.strip()
            continue

        # Otherwise it's continuation text for the prompt
        current.prompt_lines.append(line.strip())

    flush()
    return title, intro_lines, blocks


def build_docx(
    title: str, intro_lines: list[str], blocks: list[QuestionBlock], out_path: Path
) -> None:
    doc = Document()

    # Base font
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)

    doc.add_heading(title, level=1)
    if intro_lines:
        for line in intro_lines:
            doc.add_paragraph(line)

    current_section = None
    for block in blocks:
        if block.section and block.section != current_section:
            current_section = block.section
            doc.add_heading(current_section, level=2)

        # Question
        doc.add_paragraph(block.question_text())

        # Code blocks (e.g., C1)
        for code in block.code_blocks:
            doc.add_paragraph("Code:")
            p = doc.add_paragraph(code)
            for run in p.runs:
                run.font.name = "Consolas"
                run.font.size = Pt(10)

        # Options
        if block.option_lines:
            for opt in block.option_lines:
                doc.add_paragraph(opt, style="List Bullet")

        # Blank line between questions improves import readability
        doc.add_paragraph("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))


def main() -> None:
    src = Path("docs/training/participant_assessment.md")
    out = Path("docs/training/participant_assessment_import.docx")

    md_text = src.read_text(encoding="utf-8")
    title, intro_lines, blocks = parse_markdown(md_text)

    # Minor tweak: ensure example bullets under A4 don't become options.
    # Because A4 has a "Type" line after examples, those bullets were already treated as prompt lines.
    build_docx(title=title, intro_lines=intro_lines, blocks=blocks, out_path=out)
    print(f"Wrote {out.resolve()} ({len(blocks)} questions)")


if __name__ == "__main__":
    main()
