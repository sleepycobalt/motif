"""Render insights to markdown."""


def to_markdown(insights: list[dict], corpus, meta: dict) -> str:
    lines = [f"# Synthesis — {meta.get('condition', '')} run {meta.get('run_id', '')}", ""]
    lines.append(f"Transcripts: {', '.join(corpus.names)} ({corpus.words:,} words)  ")
    lines.append(f"Iterations: {meta.get('iterations', 0)}  Stop: {meta.get('stop_reason', '')}  ")
    lines.append("")
    for ins in insights:
        lines.append(f"## {ins.get('id', '?')} — {ins.get('title', '')}")
        lines.append(f"**Claim:** {ins.get('claim', '')}  ")
        lines.append(f"**Confidence:** {ins.get('confidence', '')}  ")
        lines.append(f"**Sources:** {', '.join(ins.get('sources', []))}  ")
        lines.append(f"**Evidence:** {', '.join(ins.get('evidence', []))}  ")
        ce = ins.get("counter_evidence") or []
        lines.append(f"**Counter-evidence:** {', '.join(ce) if ce else 'none'}"
                     + (f" — {ins['counter_note']}" if ins.get("counter_note") else "") + "  ")
        lines.append(f"**Opportunity:** {ins.get('opportunity', '')}")
        lines.append("")
        lines.append("<details><summary>Cited turns</summary>")
        lines.append("")
        lines.append("```")
        lines.append(corpus.render_turns(ins.get("evidence", [])))
        if ce:
            lines.append("--- counter ---")
            lines.append(corpus.render_turns(ce))
        lines.append("```")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines)
