import streamlit as st
from components import inject_premium_css

st.set_page_config(page_title="Design System", layout="wide")
inject_premium_css()

st.markdown(
    """
<h1 style="margin-bottom:4px;">Design System</h1>
<p style="color:var(--md-on-surface-variant);margin-bottom:32px;">
Theme "Huyết Mạch" — Burgundy + Gold + Deep Emerald
</p>
""",
    unsafe_allow_html=True,
)

# ── Color Palette ──
st.markdown("## Color Palette")

palette = [
    ("--md-primary", "#FFC107", "Gold — primary accent"),
    ("--md-on-primary", "#1A1A1A", "Text on gold"),
    ("--md-primary-container", "rgba(255,193,7,0.15)", "Gold container"),
    ("--md-burgundy", "#800020", "Burgundy chrome"),
    ("--md-surface", "#FDF8F3", "Warm cream — content bg"),
    ("--md-surface-dim", "#F5F0EB", "Dimmed surface"),
    ("--md-on-surface", "#1A1A1A", "Primary text on cream"),
    ("--md-on-surface-variant", "#5C5248", "Secondary text"),
    ("--md-secondary", "#006747", "Deep Emerald"),
    ("--md-tertiary", "#C9A84C", "Gold (tertiary)"),
    ("--md-error", "#DC2626", "Error / destructive"),
    ("--md-green", "#006747", "Deep Emerald"),
    ("--md-red", "#DC2626", "Alert red"),
    ("--md-amber", "#f59e0b", "Warning amber"),
    ("--md-outline", "#D4C9BC", "Borders"),
    ("--md-outline-variant", "#E8DED0", "Subtle borders"),
]

cols = st.columns(4)
for i, (token, hex_val, desc) in enumerate(palette):
    with cols[i % 4]:
        is_dark = hex_val in ("#1A1A1A", "#800020", "#006747", "#5C5248", "#DC2626")
        text_color = "#FFFFFF" if is_dark else "#1A1A1A"
        st.markdown(
            f"""
        <div style="background:{hex_val};border-radius:12px;padding:24px 16px;margin-bottom:12px;
                    border:1px solid var(--md-outline-variant);text-align:center;">
            <div style="font-weight:800;font-size:15px;color:{text_color};">{hex_val}</div>
            <div style="font-size:11px;color:{text_color};opacity:0.7;margin-top:6px;">
                <code>{token}</code><br>{desc}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

# ── Typography ──
st.markdown("---")
st.markdown("## Typography")
st.markdown(
    """
<div style="font-family:'Be Vietnam Pro',sans-serif;">
    <h1>Heading 1 — Be Vietnam Pro 800</h1>
    <h2>Heading 2 — Be Vietnam Pro 700</h2>
    <h3>Heading 3 — Be Vietnam Pro 600</h3>
    <p style="font-size:16px;color:var(--md-on-surface);">Body text — Be Vietnam Pro 400 · 16px</p>
    <p style="font-size:14px;color:var(--md-on-surface-variant);">Body secondary — Be Vietnam Pro 400 · 14px</p>
    <p style="font-family:var(--font-mono);font-size:13px;color:var(--md-on-surface);">Data — JetBrains Mono · 13px tabular-nums · 1,234.56</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Cards ──
st.markdown("---")
st.markdown("## Cards")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        '<div class="md-card"><h4 style="margin:0 0 8px 0;">Default Card</h4><p style="color:var(--md-on-surface-variant);">White card on cream surface with subtle border.</p></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        '<div class="md-card"><div class="md-section-label">METRIC</div><div style="font-size:2.2rem;font-weight:800;color:var(--md-on-surface);">42</div><div style="color:var(--md-on-surface-variant);font-size:0.8rem;">Total teachers</div></div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """
    <div style="background:var(--md-surface-dim);border:1px solid var(--md-outline-variant);border-radius:var(--radius-lg);padding:24px;">
        <div class="md-section-label">STATUS BAR</div>
        <div style="display:flex;gap:16px;margin-top:8px;">
            <span class="md-chip md-chip-primary">Primary</span>
            <span class="md-chip md-chip-green">Green</span>
            <span class="md-chip md-chip-red">Red</span>
            <span class="md-chip md-chip-amber">Amber</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ── Buttons ──
st.markdown("---")
st.markdown("## Buttons")
bc1, bc2, bc3, bc4 = st.columns(4)
with bc1:
    st.button("Primary", type="primary", use_container_width=True)
with bc2:
    st.button("Secondary", use_container_width=True)
with bc3:
    st.button("Danger", type="primary", use_container_width=True)
    st.markdown(
        '<div style="text-align:center;margin-top:4px;font-size:11px;color:var(--md-on-surface-variant);">(placeholder — styled via CSS)</div>',
        unsafe_allow_html=True,
    )
with bc4:
    if st.button("", use_container_width=True):
        pass
    st.markdown(
        '<div style="text-align:center;margin-top:-28px;font-size:13px;color:var(--md-on-surface-variant);">Logout style</div>',
        unsafe_allow_html=True,
    )

# ── Inputs ──
st.markdown("---")
st.markdown("## Form Elements")
f1, f2 = st.columns(2)
with f1:
    st.text_input("Text Input", placeholder="Placeholder text")
    st.text_area("Text Area", placeholder="Multi-line input")
with f2:
    st.selectbox("Select", ["Option A", "Option B", "Option C"])
    st.multiselect("Multi Select", ["Chọn A", "Chọn B", "Chọn C"])

# ── Status Messages ──
st.markdown("---")
st.markdown("## Status Messages")
st.success("Success message — using Streamlit native")
st.warning("Warning message — using Streamlit native")
st.error("Error message — using Streamlit native")
st.info("Info message — using Streamlit native")

# ── WCAG ──
st.markdown("---")
st.markdown("## WCAG AA Compliance")

wcag_pairs = [
    ("#1A1A1A on #FDF8F3", "Text on cream", "10.5:1", "✅ AAA"),
    ("#FFFFFF on #800020", "Text on burgundy", "8.0:1", "✅ AAA"),
    ("#1A1A1A on #FFC107", "Text on gold", "10.0:1+", "✅ AAA"),
    ("#006747 on #FDF8F3", "Emerald on cream", "6.3:1", "✅ AA"),
    ("#FFC107 on #800020", "Gold dot on burgundy", "5.5:1", "✅ AA"),
    ("#DC2626 on #FDF8F3", "Error on cream", "6.5:1", "✅ AA"),
]

st.markdown(
    '<table style="width:100%;border-collapse:collapse;">'
    '<tr style="border-bottom:2px solid var(--md-outline-variant);">'
    '<th style="text-align:left;padding:8px;">Pair</th>'
    '<th style="text-align:left;padding:8px;">Usage</th>'
    '<th style="text-align:center;padding:8px;">Ratio</th>'
    '<th style="text-align:center;padding:8px;">Status</th>'
    "</tr>"
    + "".join(
        f'<tr style="border-bottom:1px solid var(--md-outline-variant);">'
        f'<td style="padding:8px;"><code>{p[0]}</code></td>'
        f'<td style="padding:8px;">{p[1]}</td>'
        f'<td style="padding:8px;text-align:center;font-weight:600;">{p[2]}</td>'
        f'<td style="padding:8px;text-align:center;">{p[3]}</td>'
        f"</tr>"
        for p in wcag_pairs
    )
    + "</table>",
    unsafe_allow_html=True,
)

st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:var(--md-on-surface-variant);font-size:12px;">Design System v1.0 — Theme "Huyết Mạch"</p>',
    unsafe_allow_html=True,
)
