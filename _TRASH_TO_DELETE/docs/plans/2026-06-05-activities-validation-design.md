# Design Document: Category-Specific Validation for Bulk Activities Import

## Goal
To implement robust, category-aware validation for bulk-uploaded activity logs. Specifically, ensure that "Giảng dạy" (Teaching) activities have necessary class/student info and "NCKH" (Scientific Research) activities have necessary project level info. If these fields are missing, they should not be silently defaulted, but instead flagged as validation errors with row/key references.

## Proposed Changes

### 1. Update activity logs validation logic in `src/pipeline/validator.py`
- Modify `validate_activities_data` to pre-fetch all activity types with their flags (`is_teaching_activity`, `is_nckh_activity`) from the database.
- For each row, match the activity type name (with exact or fallback/fuzzy matching) to determine its category.
- Perform the following checks:
  - If the activity type is a **Teaching Activity (`is_teaching_activity == 1`)**:
    - Validate that `class_level` is present and not empty.
    - Validate that `class_type` is present and not empty.
    - Validate that `student_count` is present, not empty, and represents a positive integer greater than 0.
  - If the activity type is an **NCKH Activity (`is_nckh_activity == 1`)**:
    - Validate that `nckh_level` (Cấp đề tài) is present and not empty.
- If any check fails, append a detailed error message referencing the row number, the field name, and the activity type category.

### 2. Update Excel sheet importer in `src/pages/3_NhatKyHoatDong.py`
- Ensure that the uploader displays the validation errors cleanly.
- Verify that if errors are found, the upload process is stopped and the database is not modified.

## Verification Plan

### Automated Tests
- Run `pytest` or Python tests on the pipeline validation functions with mock data containing:
  - Valid teaching activity with all class details (should pass).
  - Teaching activity with missing class level / class type / student count (should fail and return flags).
  - Valid NCKH activity with project level (should pass).
  - NCKH activity with missing project level (should fail and return flags).
  - Valid NVK activity with no teaching/NCKH details (should pass).
