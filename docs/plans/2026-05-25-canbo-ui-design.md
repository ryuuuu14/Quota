# Cán Bộ UI Design
Date: 2026-05-25

## Problem
UI snippet for Teacher summary card currently stacks the employment type chip and the 12-month salary vertically. The salary format uses commas (`2,530,000 đ`) which is not standard for Vietnamese UI (should use dots `2.530.000 đ`).

## Proposed Solution
1. **Layout**: Change the container `div` wrapping the chip and salary to use a flex layout (`display: flex; justify-content: space-between; align-items: center;`). This aligns the chip on the left and the salary on the right on the same row.
2. **Formatting**: Update the string formatting in python. Convert the comma separator to a dot separator for thousands. E.g. `f"{sal:,.0f} đ".replace(',', '.')`.

## Components
- `src/pages/2_QuanLyCanBo.py`: Modify the `salary_info` string creation and the `st.markdown` HTML block.
