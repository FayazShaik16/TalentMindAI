import os

class SimplePDFExporter:
    """
    Zero-dependency PDF stream generator.
    Creates structured, standard-compliant PDF files containing candidate explanations.
    """

    def generate_candidate_report(self, filepath: str, title: str, narrative: str, strengths: list, weaknesses: list, interview_plan: dict) -> str:
        """
        Creates a valid basic PDF report document.
        """
        # Format text lines
        lines = [
            f"RECRUITER AUDIT REPORT: {title}",
            "=" * 50,
            "",
            "HIRING ASSIGNMENT NARRATIVE:",
            narrative,
            "",
            "KEY PROFESSIONAL STRENGTHS:",
        ]
        
        for s in strengths[:4]:
            lines.append(f"  - [{s.get('category')}] {s.get('name')}: {s.get('evidence')} (Impact: {s.get('impact')})")

        lines.append("")
        lines.append("IDENTIFIED GAPS & RISKS:")
        if weaknesses:
            for w in weaknesses[:3]:
                lines.append(f"  - [{w.get('category')}] {w.get('name')}: {w.get('evidence')} (Severity: {w.get('severity')})")
        else:
            lines.append("  - No significant risks or capability gaps detected.")

        lines.append("")
        lines.append("RECOMMENDED INTERVIEW QUESTIONS:")
        focus_areas = interview_plan.get("interview_focus_areas", [])
        for area in focus_areas[:2]:
            lines.append(f"  Topic: {area.get('topic')}")
            for q in area.get("questions", []):
                lines.append(f"    Q: {q}")

        # Escape parenthesis for Content Stream syntax
        escaped_lines = []
        for line in lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            escaped_lines.append(escaped)

        # Format content stream
        content_parts = [
            "BT",
            "/F1 14 Tf",
            "50 780 Td",
            "(TALENTMIND AI - CANDIDATE INTUITIVE AUDIT REPORT) Tj",
            "0 -25 Td",
            "/F1 10 Tf"
        ]

        # Standard A4 size is 595 x 842 points. Margin is 50.
        # Draw each line and wrap if length is > 85 chars
        y_pos = 755
        for line in escaped_lines:
            words = line.split(" ")
            current_line = []
            for word in words:
                if len(" ".join(current_line + [word])) > 85:
                    content_parts.append(f"({' '.join(current_line)}) Tj")
                    content_parts.append("0 -15 Td")
                    y_pos -= 15
                    current_line = [word]
                else:
                    current_line.append(word)
            if current_line:
                content_parts.append(f"({' '.join(current_line)}) Tj")
                content_parts.append("0 -15 Td")
                y_pos -= 15

            # If page is close to overflow, we can just stop or draw on next page
            # To keep it simple and clean, we limit lines to fit 1 page
            if y_pos < 50:
                break

        content_parts.append("ET")
        content_stream = "\n".join(content_parts)
        stream_len = len(content_stream)

        # PDF object definitions
        obj1 = "<< /Type /Catalog /Pages 2 0 R >>"
        obj2 = "<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
        obj3 = "<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 595 842] /Contents 5 0 R >>"
        obj4 = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
        obj5 = f"<< /Length {stream_len} >>\nstream\n{content_stream}\nendstream"

        objects = [obj1, obj2, obj3, obj4, obj5]

        # Calculate byte offsets
        header = "%PDF-1.4\n"
        offsets = []
        current_offset = len(header)

        for i, obj in enumerate(objects):
            offsets.append(current_offset)
            obj_text = f"{i+1} 0 obj\n{obj}\nendobj\n"
            current_offset += len(obj_text)

        startxref = current_offset

        # Build xref table
        xref_lines = [
            "xref",
            f"0 {len(objects)+1}",
            "0000000000 65535 f "
        ]
        for offset in offsets:
            xref_lines.append(f"{offset:010d} 00000 n ")

        xref_table = "\n".join(xref_lines)
        trailer = f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF"

        # Save file
        with open(filepath, "w", encoding="ascii", errors="ignore") as f:
            f.write(header)
            for i, obj in enumerate(objects):
                f.write(f"{i+1} 0 obj\n{obj}\nendobj\n")
            f.write(xref_table + "\n")
            f.write(trailer)

        return filepath
