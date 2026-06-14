# Theme "Huyết Mạch" — Design Specification

## Brand DNA
- **Inspiration:** Cờ Việt Nam (Đỏ - Vàng)
- **Personality:** Uy nghiêm, hiện đại, bản sắc dân tộc
- **Application:** Hệ thống Quản lý Chế độ Làm việc Nhà giáo T04
- **Platform:** Streamlit 1.58.0

## Color Palette

| Token | Hex | Role |
|-------|-----|------|
| `--md-surface` | `#FDF8F3` | Main content background (warm cream) |
| `--md-surface-dim` | `#F5F0EB` | Dimmed surface |
| `--md-primary` | `#FFC107` | Gold — buttons, links, active tabs |
| `--md-on-primary` | `#1A1A1A` | Text on gold |
| `--md-tertiary` | `#C9A84C` | Gold (tertiary) |
| Burgundy chrome | `#800020` | Sidebar, header, nav, timeline rank |
| `--md-secondary` | `#4A5D23` | Military Green — success, confirm, timeline dept |
| `--md-on-surface` | `#1A1A1A` | Primary text on cream |
| `--md-on-surface-variant` | `#5C5248` | Secondary text |
| `--md-outline` | `#D4C9BC` | Borders |
| `--md-outline-variant` | `#E8DED0` | Subtle borders |
| `--md-error` | `#DC2626` | Error / destructive |

## Typography
- **Headings:** Be Vietnam Pro (700/800 weight)
- **Body:** Be Vietnam Pro (400/500 weight)
- **Data:** JetBrains Mono (tabular-nums)

## Architecture
- **2-tone layout:** Burgundy chrome (sidebar/nav) + cream content area
- **Cards:** White `#FFFFFF` on cream surface, amber accent border on hover
- **Glassmorphism:** Removed (cross-browser Streamlit stability)
- **Login page:** Full burgundy bg, centered cream card

## Component Tokens
| Component | Style |
|-----------|-------|
| Card | `bg: #FFFFFF, border: 1px solid #E8DED0, radius: 18px` |
| Button Primary | `bg: #FFC107, text: #1A1A1A, radius: 12px` |
| Button Secondary | `bg: transparent, border: 1px solid #D4C9BC` |
| Button Danger | `bg: #DC2626, text: white` |
| Tab Active | `bg: rgba(255,193,7,0.15), text: #FFC107` |
| Tab Inactive | `bg: #F5F0EB, text: #5C5248` |
| Input | `bg: white, border: 1px solid #D4C9BC` |
| Sidebar | `bg: #800020, text: white, nav hover: gold` |
| Chip Primary | `bg: #FFC107, text: #1A1A1A` |
| Chip Green | `bg: #4A5D23, text: white` |
| Timeline Title | `#FFC107` — academic title |
| Timeline Dept | `#4A5D23` — department/unit |
| Timeline Position | `#C9A84C` — leadership role |
| Timeline Rank | `#800020` — military rank |
| Timeline Event | `#8A7F75` — neutral event |

## WCAG AA Compliance
| Pair | Ratio | Status |
|------|-------|--------|
| `#1A1A1A` on `#FDF8F3` | 10.5:1 | ✅ AAA |
| `#FFC107` on `#FFFFFF` | 1.5:1 | ⚠️ decorative only |
| `#FFFFFF` on `#800020` | 8.0:1 | ✅ AAA |
| `#1A1A1A` on `#FFC107` | 10.0:1+ | ✅ AAA |
| `#4A5D23` on `#FDF8F3` | 5.8:1 | ✅ AA |

## Decision Log
| Decision | Alternative | Rationale |
|----------|-------------|-----------|
| Burgundy chrome + cream content | Full red background | Usability for daily tool |
| Solid cards | Glassmorphism | Streamlit cross-browser stability |
| Amber primary | Gold metallic | Better contrast on dark |
| Be Vietnam Pro (keep) | Font change | Already in project, no added weight |
| Login page synced | Keep separate sage | Brand consistency |
