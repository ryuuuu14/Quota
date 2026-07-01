# Guest Lecturer Workflow for Administrative Staff

## Context & Purpose
According to Điều 7.8, administrative staff who hold a "Nhà giáo" (Teacher/Lecturer) title but work in a non-teaching department (Phòng/Trung tâm) must fulfill a minimum teaching quota equivalent to 40% of standard teaching hours. Pure administrative staff (e.g., Chuyên viên) do not have this quota, but their teaching activities can still be recorded as extra hours (vượt định mức).

This document outlines the system workflow to accurately track these cross-departmental teaching activities while maintaining strict departmental data isolation.

## The Workflow

### 1. Linking Staff to a Teaching Department (Central Admin)
- Because department isolation is strictly enforced, Heads of Teaching Departments (Host Khoa) cannot arbitrarily search the global directory for administrative staff.
- The **Central Admin** must explicitly link the administrative staff member to the Host Khoa for the current semester/year as a "Guest Lecturer" (Giảng viên thỉnh giảng nội bộ).
- Once linked, the staff member becomes visible to the Host Khoa for teaching assignments, without being permanently transferred from their Home Phòng.

### 2. Recording Teaching Hours (Host Khoa)
- The **Head of the Host Khoa** logs in and views their department's teaching records.
- They will now see the linked administrative staff member in a dedicated "Guest Lecturers" section.
- The Head of Khoa inputs the teaching activities (hours, subjects taught, etc.) just as they would for their regular staff.
- The submission is forwarded to the Central Admin for final approval.

### 3. Review and Approval (Central Admin)
- The **Central Admin** reviews the submitted teaching hours to ensure validity.
- Upon approval, the system calculates the impact on the staff member's quota based on their official Title (Chức danh):
  - **If Title = "Giảng viên" (or other teaching title):** The hours count towards their 40% quota. Their base (250/270) is determined by the `Khối môn học` assigned in their profile.
  - **If Title = "Chuyên viên" (or non-teaching title):** Their base quota is 0, and the approved hours are logged strictly as extra teaching hours (vượt định mức).

## Key Assumptions & Constraints
- We rely on the staff member's `Chức danh` (Title) to differentiate between those who have a 40% quota and those who have a 0 quota.
- The `Khối môn học` fallback value configured in the "Thêm mới Hồ sơ" form defines whether the base is 250 or 270 for administrative "Nhà giáo".
- Department isolation remains intact; Heads of Khoa can only see non-department staff if an Admin has explicitly authorized the link.
