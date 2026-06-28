# Council of App Status — Pixel-Accurate Baseline

## Global CSS (components.py)
**File:** inject_premium_css()
**Total rules:** 48 selectors, ~175 declarations

### Token Inventory
- 44 tokens defined in `:root`
- 10 tokens NEVER USED: `--sp-4/8/12/16/20/24/32/40`, `--brand-primary`, `--brand-secondary`
- 6 additional tokens never referenced: `--md-tertiary-container`, `--md-secondary-container`, `--md-on-primary-container`, `--md-on-error`, `--md-on-error-container`, `--md-surface-container-highest`, `--radius-xl`
- `--md-*` prefix (MD3-inspired) conflicts with standard naming convention

### Inconsistencies Found
1. **Transition timing** — 3 different standards across components (0.2s ease, 0.3s ease, 0.3s cubic-bezier)
2. **Hardcoded radii** — 6 locations use hardcoded px values matching `--radius-*` tokens (8px, 12px)
3. **Card padding override** — CSS `.md-card { padding: 24px }` but inline in `render_metric_card` uses `20px !important`
4. **Missing CSS class** — `.md-chip-tertiary` referenced in `render_chip()` but no CSS rule defined
5. **!important inconsistency** — 4 declarations lack !important while all others use it
6. **Gradient on primary buttons** — `.stButton > button[kind="primary"]` uses gradient bg, but solid bg would be more "enterprise"

## Dashboard (1_Dashboard.py)
**File:** 376 lines

### Layout
- 5-column metric cards (equal ratio)
- Status filter + search text input stacked vertically
- 10 default columns selected out of 24 available
- Only 2 columns pinned (ID, Họ và tên)
- Expandable conversion section below table

### Issues
- Filter and search are separate widgets (could be combined)
- No column width persistence across sessions
- No sort indicator text (only icons)
- Conversion cards use `st.columns([3, 7])` ratio — button takes 30%

## Taste Council — Verdict

### Evaluated Design Systems
| System | Rating | Verdict |
|--------|--------|---------|
| professional/ | 3/10 | Yellow primary (#FECE14) conflicts with navy+teal identity |
| modern/ | 2/10 | Purple (#553F83) + serif font — wrong direction |
| clean/ | 6/10 | Blue primary (#3B82F6) too close to current but Roboto is generic |
| linear-app/ | 8/10 | Dark theme incompatible, but typography philosophy + spacing + border system are gold standard |

### Council Recommendation
**Adopt patterns from Linear, keep current colors.**
- Linear's typographic precision (weight hierarchy, letter-spacing rules)
- Linear's border system (ultra-thin semi-transparent, step-based)
- Linear's elevation model (luminance stepping, not shadows)
- Clean/ spacing scale (8pt baseline)
- Reject: dark theme, Inter font (keep Be Vietnam Pro), indigo accent

### Priority Loop Queue
1. Fix transition timing consistency (all → 0.2s ease)
2. Replace hardcoded radii with `--radius-*` tokens
3. Remove unused tokens, add missing `.md-chip-tertiary` CSS
4. Standardize card padding (24px everywhere)
5. Remove gradient from primary buttons (solid #1e3a8a)
