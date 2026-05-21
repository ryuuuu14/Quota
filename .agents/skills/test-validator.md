# Skill: Local Test Suite Verification & Integrity Checking

## Context Trigger Words
- "test", "pytest", "validate", "calculations", "verify", "mock", "assert", "sqlite", "database", "schema"

## Verification Protocols
1. **Mocking External Contexts:** Streamlit and pandas must be mocked when running tests headlessly outside of the app environment:
   ```python
   import sys
   from unittest import mock
   sys.modules['streamlit'] = mock.MagicMock()
   sys.modules['pandas'] = mock.MagicMock()
   ```
2. **Schema Integrity Check:** Every test cycle must verify the database schema alignment. Ensure all queries reference:
   - `base_conversion_rate` instead of the deprecated `conversion_rate` column in the `activity_types` table.
3. **Execution Commands:** Run the test suite using:
   - Logic tests: `python test_logic.py`
   - Capping tests: `python test_auto_capping.py`
   - QA Scenario simulations: `python qa_tests.py`
4. **Calculations Compliance:** Ensure all changes to `calculations.py` are regression-tested to confirm T04 hours rules (like proportional calculation for partial years or limit bounds for NCKH/Giờ chuẩn conversion) do not shift.
