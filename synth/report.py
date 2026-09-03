"""Render insights to markdown."""

from synth.agents import turn_ids


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
        ev = turn_ids(ins.get("evidence"))
        lines.append(f"**Evidence:** {', '.join(ev)}  ")
        ce = turn_ids(ins.get("counter_evidence"))
        lines.append(f"**Counter-evidence:** {', '.join(ce) if ce else 'none'}"
                     + (f" — {ins['counter_note']}" if ins.get("counter_note") else "") + "  ")
        lines.append(f"**Opportunity:** {ins.get('opportunity', '')}")
        lines.append("")
        lines.append("<details><summary>Cited turns</summary>")
        lines.append("")
        lines.append("```")
        for item in ins.get("evidence") or []:
            if isinstance(item, dict) and item.get("quote"):
                lines.append(f"  receipt {item['turn']}: \"{item['quote']}\"")
        lines.append(corpus.render_turns(ev))
        if ce:
            lines.append("--- counter ---")
            lines.append(corpus.render_turns(ce))
        lines.append("```")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines)
