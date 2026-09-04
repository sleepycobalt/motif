# ETOT website — case-study notes

- 2026-09-04 · Chassis refactor: tokens.json + chassis.py extracted from motif-build.py; empty-diff check passed for both variants before any other change (scripts/check-chassis.sh in etot-site).
- 2026-09-04 · Found: css_fill() uses str.replace, so the hardening block's "100%%" reached the live page verbatim — four max-width rules invalid. Fixed in chassis.py as a separate, named change; diff is exactly those 4 lines.
- 2026-09-04 · Decision: home hero on chassis ground, field in ink and blue; blue panel dropped. Archivo retired; site is Instrument Serif / Space Grotesk / IBM Plex Mono per tokens.json.
- 2026-09-04 · Decision: mark = the ring, regenerated as a field (letters sized by distance to a curve — the Motif thumbnail's mechanism). scripts/mark.py, seed 7.
- 2026-09-04 · Decision: one site-wide theme switch, case-study copies included; ericfrye.info keeps fixed variants via css_fixed().
- 2026-09-04 · Decision: no subdomain for Motif yet (spec: once there are two). Pricing shown as free/MIT, hosted tier "not yet decided".
- 2026-09-04 · Open: Vienna partner name in site/studio.json; og.png export; hello@ forwarding; case-study repo link in Motif README still points at ericfrye.info.
