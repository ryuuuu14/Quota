import yaml

new_synonyms = [
    {
        'expected': 'Chức danh',
        'synonyms': ['chuc danh', 'chức danh', 'title']
    },
    {
        'expected': 'Chức vụ',
        'synonyms': ['chuc vu', 'chức vụ', 'chức vụ lãnh đạo', 'role']
    },
    {
        'expected': 'Cấp bậc quân hàm',
        'synonyms': ['cap bac', 'cấp bậc', 'cấp bậc quân hàm', 'quân hàm', 'ngạch lương']
    },
    {
        'expected': 'Học hàm học vị',
        'synonyms': ['hoc ham', 'học hàm', 'học vị', 'học hàm học vị', 'trình độ']
    },
    {
        'expected': 'Loại hợp đồng',
        'synonyms': ['loai hop dong', 'loại hợp đồng', 'hợp đồng', 'employment type']
    },
    {
        'expected': 'Ngày bổ nhiệm',
        'synonyms': ['ngay bo nhiem', 'ngày bổ nhiệm', 'appointment date']
    },
    {
        'expected': 'Nữ',
        'synonyms': ['nu', 'nữ', 'giới tính', 'gender', 'female']
    },
    {
        'expected': 'Tổ bộ môn',
        'synonyms': ['to bo mon', 'tổ bộ môn', 'tổ môn', 'bộ môn', 'subject group']
    },
    {
        'expected': 'Đơn vị',
        'synonyms': ['don vi', 'đơn vị', 'phòng ban', 'khoa', 'department']
    }
]

file_path = 'config/synonyms.yaml'
with open(file_path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

data['synonyms'].extend(new_synonyms)

with open(file_path, 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print('Updated synonyms.yaml')
