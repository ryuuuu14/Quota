# DESIGN.md – Brand DNA for T04 ANND Management App

## 1. Visual Theme & Atmosphere

- **Core atmosphere:** Institutional authority, precision, and trust. The UI should feel like an internal command‑center: clear, disciplined, and reliable. 
- **Mood:** Calm confidence, low visual noise, with a subtle sense of hierarchy that mirrors the academic ranks (Giáo sư > Phó Giáo sư > Giảng viên chính > Giảng viên > Trợ giảng).
- **Density:** **Score 9/10** – the application displays dense tabular data, KPI cards, and timeline charts; visual hierarchy is essential.
- **Variance:** **Score 2/10** – a utilitarian, consistent look across screens; creativity is limited to functional polish.
- **Motion:** **Score 2/10** – only purposeful micro‑animations (hover lifts, progress‑bar fills) to reinforce feedback without distraction.

## 2. Color Palette & Roles

| Role | Hex | Usage |
|------|------|-------|
| **Base Dark** | `#1E2A38` | Primary background for sidebars and footers; establishes seriousness.
| **Base Light** | `#F5F7FA` | Main canvas/background for content area; high readability.
| **Neutral Gray** | `#D1D9E0` | Borders, dividers, secondary text.
| **Accent (Primary)** | `#0056B3` *(saturation ≈ 70 %)* | Buttons, active tabs, KPI highlights, links.
| **Success** | `#28A745` | Positive status (quota met).
| **Warning** | `#FFC107` | Near‑limit warnings.
| **Error** | `#DC3545` | Violations, overdue items.

**Constraints:** – Single accent color (`#0056B3`). – No neon, no pure black. – Accent saturation kept below 80 %.

## 3. Typography Rules

- **Primary Font:** **Outfit** (Google Font) – modern, legible, slightly geometric, conveys professionalism.
- **Headings:** `font-weight: 600; line-height: 1.2;` – size hierarchy: H1 = 24 px, H2 = 20 px, H3 = 18 px.
- **Body Text:** `font-weight: 400; font-size: 14 px; line-height: 1.5;` – emphasizes readability in dense tables.
- **Monospace (code/ids):** `font-family: "Roboto Mono", monospace; font-size: 13 px;` for identifiers like faculty IDs.
- **No Inter, no decorative fonts.**

## 4. Component Stylings

| Component | Style Summary |
|-----------|---------------|
| **Sidebar Navigation** | Fixed 240 px width, background `#1E2A38`, vertical list with left‑aligned icons, active item accent background `#0056B3` (10 % opacity) and white text. Hover lifts 2 px, subtle shadow.
| **KPI Card** | Rounded 8 px, background `#F5F7FA`, border `1px solid #D1D9E0`. Title in `Outfit 14 px` gray, value in `Outfit 24 px` accent color. Progress bar: track `#D1D9E0`, fill `#0056B3` with 0.3 s width transition.
| **Data Table** | Full‑width, alternating row background (`#FAFCFE` / `#F5F7FA`). Header dark gray `#2C3E50` with white text. Sort icons accent‑colored. Cell padding 12 px.
| **Form Input** | Outline `1px solid #D1D9E0`, focus border `#0056B3`. Labels `Outfit 13 px` gray, required *asterisk* red. Submit button primary accent, disabled state 40 % opacity.
| **Tabs** | Horizontal bar, active tab accent background, inactive tabs light gray. Underline animation on switch.
| **Toast / Notification** | Small banner, background based on status (success = green, warning = yellow, error = red), accent‑colored left stripe for brand identity.

## 5. Layout Principles

- **Grid System:** 12‑column flexible grid, 24 px gutter. Content area max‑width 1440 px.
- **Master‑Detail Pattern:** Sidebar → main panel; secondary panels (e.g., faculty timeline) appear as collapsible cards within the main area.
- **Responsive Breakpoints:**
  - `≥1200 px`: full sidebar + content.
  - `992‑1199 px`: collapsed sidebar (icons only), tooltip labels.
  - `<992 px`: top‑drawer navigation for tablets.
- **Hierarchy Emphasis:** Larger headings and accent colors for higher‑rank roles (Giáo sư, Phó Giáo sư) in roster tables; lower‑rank rows use lighter gray.
- **Spacing:** Consistent 16 px padding, 8 px margin for dense data sections.

## 6. Motion & Interaction

- **Micro‑animations:**
  - Hover lift (2 px) on cards and buttons.
  - Progress‑bar fill animation (0.3 s linear).
  - Sidebar item slide‑in on collapse/expand (0.2 s).
- **Feedback:** Instant visual change on form validation (border turns accent or error red).
- **No heavy motion:** No auto‑play carousels, no large background transitions.

## 7. Anti‑Patterns (Banned)

- Pure black backgrounds (breaks brand seriousness).
- Neon or overly saturated accent colors.
- Centered hero sections – the app is data‑centric, not marketing.
- Excessive gradients or drop‑shadows that add visual noise.
- Overly rounded elements (radius > 12 px) – keep a professional, defined look.
- Decorative fonts (script, display) – stick to Outfit.
- Auto‑scrolling content – user must control data navigation.

---

**Brand DNA Summary**

The institution projects **trust, authority, and precision**. We translate that into a sober dark‑light palette anchored by navy and a single deep‑blue accent, a clean geometric sans‑serif (Outfit), and a high‑density, low‑variance layout that respects the strict hierarchy of academic ranks. Subtle motion reinforces feedback without distracting from the core compliance data. All decisions converge on a premium, government‑grade interface that feels both modern and unmistakably institutional.
