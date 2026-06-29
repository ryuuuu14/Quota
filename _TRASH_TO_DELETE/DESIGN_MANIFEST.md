# UI Overhaul & Activity History Integration

## 1. Aesthetic Framework (Researcher Output)
**Objective:** Transform the `2_QuanLyCanBo` page into a high-end, native-feeling enterprise application within Streamlit's constraints.
- **Visual Architecture:** High-end editorial layering. Clean separation of background, surface, and interactive elements.
- **Color Domain:** Deep, authoritative tones (Midnight Blues, Slate Grays) accented with high-contrast typography and subtle structural borders. Avoid overly bright or generic primary colors.
- **Component Logic:** Modular, reusable CSS-injected components. Forms and data grids must be wrapped in sophisticated surface cards.
- **Typography:** Crisp, sans-serif dominance (e.g., Inter, Roboto). Strict weight hierarchy (e.g., bold for metrics, medium for labels, regular for data).

## 2. Layout Configuration (Layout Engineer Output)
**Structural Blueprint for `2_QuanLyCanBo.py`:**
- **Global CSS Injection:** Inject a `<style>` block at the top of the file to override standard Streamlit padding, enforce border-radius on containers, and define the palette variables.
- **Horizontal Navigation Grid:** 
  - Use `st.tabs` with custom CSS to style the tab headers to look like a modern segmented control.
  - Tab 1: `📋 Danh sách & Tìm kiếm` (Grid & Search)
  - Tab 2: `➕ Cập nhật hồ sơ` (Manual Entry)
  - Tab 3: `📥 Nhập dữ liệu từ Excel` (Bulk Imports)
- **Tab 3 Configuration (Excel Imports):**
  - **Grid Split:** Use a 40/60 column split. Left column for file upload and configuration; right column for the interactive diff preview.
  - **Sub-sections:** Use styled `st.radio` or nested `st.tabs` to toggle between the two import engines: "Hồ sơ cán bộ" and "Nhật ký hoạt động".
  - **Feedback Surface:** Render validation feedback using color-coded HTML badges (`<span class="badge new">`, `<span class="badge update">`) instead of raw text.

## 3. Execution Phases
- [ ] **Phase 1:** Inject global CSS architecture and set up the 3-Tab horizontal layout in `2_QuanLyCanBo.py`.
- [ ] **Phase 2:** Migrate existing search, grid, and manual edit logic into Tab 1 and Tab 2.
- [ ] **Checkpoint A (Human in Loop):** Present the structural UI changes to the user. Do not proceed until human approves the layout and aesthetics.
- [ ] **Phase 3:** Build the 40/60 Layout in Tab 3 for the "Hồ sơ cán bộ" Excel import.
- [ ] **Phase 4:** Build the "Nhật ký hoạt động" Excel engine in Tab 3 (parsing dates, strictly matching Mã GV).
- [ ] **Checkpoint B (Human in Loop):** Present the Excel mapping engine and diff UI. Do not proceed until human approves.
- [ ] **Phase 5:** Update database schema (`staging_teachers` columns, `reduction_rules` for "Nghỉ có phép").
- [ ] **Phase 6:** Update `7_PheDuyet.py` to approve and commit the new history fields.
- [ ] **Checkpoint C (Human in Loop):** Final review of the database commits and T04 quota prorations. Do not finish until human signs off.
