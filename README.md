# Pain-Based Predictive Outreach Agent (Scaffold)

This bundle contains:
- **Clay table CSVs** with two columns: `Column`, `Formula_or_Prompt` (second column is paste-ready for Clay formulas/prompts).
- **Python code templates** (from your implementation guide + maritime vertical stubs).
- **n8n workflow JSONs** extracted verbatim from your guide.
- **Templates & prompts** (Jinja + Clay-AI prompts).
- **Configs** (YAML sequence examples) and an `.env.sample`.

## Quick Start
1) Create a virtualenv, then:
   ```bash
   pip install -r requirements.txt
   ```
2) Copy `.env.sample` → `.env` and add your keys.
3) Open `clay_tables/*.csv` to create tables in Clay (copy formulas/prompts from the 2nd column).
4) Import `n8n/*.json` workflows into n8n.
5) Use `templates/*` in your outbound sequence tool or Clay AI.
6) Extend the stubs under `src/verticals/maritime` to connect USCG/Paris MOU data sources.

## Notes
- Some Python blocks provided in `docs/bta-outreach-implementation.md` were partial; they are preserved as templates.
- If you have additional Laasy or other instruction files to include, drop them into `docs/` and we can wire them next.
- EDP score formula implemented per spec: `0.4*urgency + 0.2*meas + 0.2*action + 0.1*universality + 0.1*defensibility`.
