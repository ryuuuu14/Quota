# Skill: Structural UI Layout & Styling Builder

## Context Trigger Words
- "layout", "grid", "flexbox", "canvas", "Stitch API", "components", "css", "theme", "color", "styling", "margin", "padding"

## Streamlit Styling Protocols
1. **Material Design 3 Token Enforcement:** All styling changes must utilize the defined CSS custom variables injected in `src/app.py` :root:
   - Primary Accent: `--md-primary` (`#0056B3`)
   - Surface color: `--md-surface` (`#f9f9ff`)
   - Container corners: `--radius-sm` (4px), `--radius-md` (8px), `--radius-lg` (12px), `--radius-xl` (16px), `--radius-full` (9999px)
   - Shadows: `--shadow-card` (ambient `rgba(0,0,0,0.05)`)
2. **Page Configuration Constraint:** Never call `st.set_page_config` in individual sub-page files (e.g., `src/pages/*.py`). It must only be invoked once in the entry point `src/app.py`. Sub-pages must reuse existing layout wrappers or custom headers to avoid runtime crashes.
3. **No Raw Inline Overrides:** Avoid hardcoding inline style attributes like `style="background: blue;"`. Implement styles cleanly via CSS variables and utility classes inside `<style>` blocks or update `src/components.py`.
4. **Stable Test Selectors:** When injecting custom HTML snippets (e.g. for status chips, badges, or grids), always attach explicit data attributes (`data-testid="badge-xyz"`) for local selenium/playwright testing stability.
5. **Viewport Safety:** Ensure all components specify overflow rules (`overflow: hidden` or `overflow-y: auto` for lists) to prevent Streamlit layout breaks.
