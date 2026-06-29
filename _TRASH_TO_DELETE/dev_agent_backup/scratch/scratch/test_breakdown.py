import sys
sys.path.insert(0, 'src')
from calculations import get_teacher_formula_breakdown

b = get_teacher_formula_breakdown(100, 4)
if not b:
    print("No breakdown returned")
    sys.exit(1)

print("Teacher:", b['teacher_name'])
print("Title:", b['teacher_title'])
print("Dept:", b['teacher_dept'])
print("Timeframe:", b['tf_name'], b['tf_start'], "->", b['tf_end'])
print("Std weeks:", b['std_weeks'])
print()
print("Holidays:", len(b['holidays']))
for h in b['holidays']:
    print(f"  {h['name']}: {h['start']} -> {h['end']}")
print()
for i, seg in enumerate(b['segments'], 1):
    wd = seg['workday_detail']
    print(f"Segment {i}: {seg['period_start']} -> {seg['period_end']}")
    if wd:
        print(f"  Calendar={wd['calendar_days']} Weekend={wd['weekend_days']} Holidays={wd['holiday_days_count']} Workdays={wd['active_workdays']}")
        print(f"  Weeks: {wd['full_weeks']}w + {wd['remainder_days']}d = {seg['seg_weeks']:.4f}")
    print(f"  Base GC={seg['base_gc']} Role_red={seg['role_t_red_pct']}% req_gc={seg['req_gc']:.2f}")
print()
print(f"Total required GC: {b['total_required_gc']:.2f}")
print("Reductions:", len(b['reductions']))
for red in b['reductions']:
    wd_r = red['workday_detail']
    print(f"  Rule: {red['rule_name']} | {red['period_start']} -> {red['period_end']}")
    if wd_r:
        print(f"  Workdays={wd_r['active_workdays']} Weeks={red['red_weeks']:.4f}")
    print(f"  GD reduction={red['teaching_reduction_pct']}%")
