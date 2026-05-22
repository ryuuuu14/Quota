# Database Dump

## Teachers

```
 id           name       subject_group  is_female
 49   Nguyễn Văn A Chính trị/Nghiệp vụ          0
 50     Trần Văn B Chính trị/Nghiệp vụ          0
 51     Phạm Thị C Chính trị/Nghiệp vụ          1
 52       Lê Văn D Chính trị/Nghiệp vụ          0
 53      Bùi Thị X Chính trị/Nghiệp vụ          1
 54 GV Bình Thường Chính trị/Nghiệp vụ          0
```

## Role History Columns

```
[(0, 'id', 'INTEGER', 0, None, 1), (1, 'teacher_id', 'INTEGER', 1, None, 0), (2, 'record_type', 'TEXT', 1, None, 0), (3, 'value_text', 'TEXT', 0, None, 0), (4, 'reduction_rule_id', 'INTEGER', 0, None, 0), (5, 'start_date', 'DATE', 1, None, 0), (6, 'end_date', 'DATE', 0, None, 0), (7, 'actual_weeks_override', 'REAL', 0, None, 0)]
```

## Role History

```
 id  teacher_id record_type                      value_text  reduction_rule_id start_date   end_date  actual_weeks_override
205          49       TITLE                      Giảng viên                NaN 2025-08-04 2025-11-30                    NaN
206          49       TITLE                       Trợ giảng                NaN 2025-12-01        NaN                    NaN
207          49  DEPARTMENT Chính trị, Pháp luật, Nghiệp vụ                NaN 2025-08-04        NaN                    NaN
208          50       TITLE                      Giảng viên                NaN 2025-08-04        NaN                    NaN
209          50  DEPARTMENT Chính trị, Pháp luật, Nghiệp vụ                NaN 2025-08-04        NaN                    NaN
210          50   REDUCTION                       Trưng tập               49.0 2025-09-01 2025-12-28                    NaN
211          50   REDUCTION                       Bồi dưỡng               40.0 2025-10-27 2025-11-17                    NaN
212          50   REDUCTION                   Điều trị bệnh               54.0 2026-04-06 2026-04-27                    NaN
213          51       TITLE                      Giảng viên                NaN 2025-08-04        NaN                    NaN
214          51  DEPARTMENT Chính trị, Pháp luật, Nghiệp vụ                NaN 2025-08-04        NaN                    NaN
215          51   REDUCTION                   Nghỉ thai sản               53.0 2025-12-01 2026-06-01                   23.0
216          51   REDUCTION      Nuôi con nhỏ dưới 12 tháng               44.0 2026-06-02 2026-06-05                    4.0
217          52       TITLE                Giảng viên chính                NaN 2025-08-04        NaN                    NaN
218          52  DEPARTMENT Chính trị, Pháp luật, Nghiệp vụ                NaN 2025-08-04        NaN                    NaN
219          52   REDUCTION                             NaN                7.0 2025-08-04 2025-11-30                    NaN
220          52   REDUCTION                             NaN                6.0 2025-12-01 2026-06-05                    NaN
221          52   REDUCTION                      Đi thực tế               49.0 2025-08-04 2025-09-28                    NaN
222          52   REDUCTION                Đi học bồi dưỡng               40.0 2026-04-06 2026-04-26                    NaN
223          53       TITLE                      Giảng viên                NaN 2025-08-04 2025-11-16                    NaN
224          53       TITLE                Giảng viên chính                NaN 2025-11-17        NaN                    NaN
225          53  DEPARTMENT Chính trị, Pháp luật, Nghiệp vụ                NaN 2025-08-04        NaN                    NaN
226          53   REDUCTION                   Nghỉ thai sản               53.0 2025-08-04 2025-09-21                    NaN
227          53   REDUCTION      Nuôi con nhỏ dưới 12 tháng               44.0 2025-08-04 2026-03-31                    NaN
228          53   REDUCTION                          Đi học               40.0 2026-04-06 2026-07-05                    NaN
229          54       TITLE                      Giảng viên                NaN 2025-08-04        NaN                    NaN
230          54  DEPARTMENT Chính trị, Pháp luật, Nghiệp vụ                NaN 2025-08-04        NaN                    NaN
```

## Timeframes

```
 id              name start_date   end_date  norm_multiplier  standard_academic_weeks
  1 Năm học 2025-2026 2025-08-04 2026-06-05              1.0                     44.0
```

## Academic Holidays

```
Empty DataFrame
Columns: [id, timeframe_id, name, start_date, end_date]
Index: []
```

## Titles

```
                name  base_teaching_hours_natural  base_teaching_hours_social  base_nckh_hours
Giáo sư, Phó Giáo sư                          330                         310              600
    Giảng viên chính                          300                         280              600
          Giảng viên                          270                         250              600
           Trợ giảng                          240                         200              300
```

