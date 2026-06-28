## Builder — Task {task_id}

### Instructions
Implement the task described below. Read each target file before writing.

### Task
{task_description}

### Target files
{target_files}

### Do NOT touch
{protected_files}

### Rules
- One change at a time
- No "while I'm here" improvements
- Update tests if behavior changes
- Keep backward compatibility
- After each write: verify syntax with `python -c "import py_compile; py_compile.compile(FILE, doraise=True)"`

### Done signal
```
[BUILDER_DONE] Files: {files_changed}
[BUILDER_SUMMARY] {one-line summary}
```
