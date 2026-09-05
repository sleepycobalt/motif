# Spec — Motif for Figma (v2: the commercial surface)

*Supersedes the v1 FigJam plugin spec. The MCP server (shipped) is the free developer channel; this plugin is the surface designers find in the Community and the one that can be paid for. Next build after part 2; before the v3 eval.*

## Purpose
A Figma Community plugin, editor types **FigJam** (primary) and **Figma Design**, that turns transcripts into a Motif board — the same output the MCP demo produced — without a terminal. Free on your own key; paid credits if you'd rather not manage a key.

## Tiers
**Free — bring your own key.** The user pastes an Anthropic key once; it's stored in `figma.clientStorage`, sent only to Anthropic, never to ETOT. Unlimited runs. This is the engine, which is MIT anyway. ETOT's key is never involved.

**Paid — credits.** Prepaid bundles bought through Figma's payments (or Stripe via the plugin UI if Figma's payments don't fit — decide during build). Runs are proxied through ETOT's hosted engine with ETOT's key. Exposure is bounded by what was prepaid: a $20 bundle buys runs priced above their API cost (target ≥ 2× cost; a 15-transcript run cost $4.88 on the MCP surface, so ~$10 in credits). No unpaid runs on ETOT's key ever — no trial allowance, no free runs, no exceptions. If a trial is needed, it's a coupon for credits.

What the paid tier is actually selling: no key management, an invoice, a licence, and support. Team features later.

## Prerequisites before the paid tier switches on
- Business entity and bank account (the LLC question, now with a date).
- Payment rails decided and tested.
- A support address and a stated response time in the listing.
- Terms and privacy: transcripts processed for the run and discarded; nothing stored.

## Architecture
- **Plugin UI** (TypeScript, Figma plugin API): transcript drop (.docx/.txt/.md), research question, tier switch, progress with the loop's own log lines, "build board" step.
- **Engine, two paths:**
  - BYOK: plugin calls Anthropic directly? *No* — the engine is Python. BYOK path calls the **hosted engine with the user's key forwarded per request**, never logged. Same service as paid; the key is the only difference.
  - Paid: hosted engine with ETOT's key, metered against the user's credit balance before the run starts.
- **Hosted engine:** the existing engine module behind one HTTP endpoint, small deployment, streaming progress. Shared with the MCP server's future remote mode.
- **Board output:** the plugin writes stickies itself via the plugin API (it doesn't need Figma's MCP). Same layout the `motif_board` tool produces: claim sticky coloured by confidence, receipt stickies with turn IDs, counter-evidence wired with "contested by" connectors, opportunity, violet contested sticky. Palette pinned to colours that round-trip.

## Listing (Figma Community)
- Name: **Motif** by ETOT. Icon: the field thumbnail, reduced. Cover: the I-09 board section.
- One line: "Research synthesis that shows what survived."
- Body in the register of the best-performing listings: what it does, three ways to use it, a receipts-and-contested explanation, FAQ (keys, privacy, cost), links to the case studies and repo.
- Screenshots: the board overview, one contested section, the plugin UI, the critique verdict.
- Category: Research / Whiteboarding.

## Scope
- In: both tiers, docx/txt/md, one question, condition C, board output, run card on the board, the `motif_critique` mode on pasted text (paste a summary → verdict as stickies).
- Out for v1: editing rules in the plugin (link to docs), storage, team features, Miro.

## Success criteria
- Install → board in under ten minutes on the free tier.
- Listed; first 10 installs and 3 pieces of feedback logged in `docs/part3-notes.md`.
- Paid tier live only after the prerequisites above; first paid credit purchase logged.

## Case study
Part 3: the plugin as product — the UI decisions, the tier design, first users, first revenue. Written from `docs/part3-notes.md`.

## Working discipline (applies to every ETOT chat)
- **Notes as you go.** Append to `docs/part3-notes.md` after every session; create it in the first.
- **Log as you go.** `docs/log.md`, three lines per session.
- **Record, don't reconstruct.** Numbers and quotes copied from files with paths.
- **Full commands** every time, including where the file goes and the git sequence. Commit only in the repo the session was opened in; give `mv` commands for anything belonging elsewhere.
- **Silence is never approval.** Missing verdicts, empty results, and parse failures are hard failures.
- **QA gate.** Nothing is presented as done until it has been tried end to end in a fresh Figma file and, for any web or UI surface, checked for clipped, overflowing, or broken elements at desktop and phone widths.
