# Skill: Context Window Management & Optimization

## Context Trigger Words
- "context", "token", "limit", "history", "summarize", "large file", "regulation", "budget"

## Token Budget & Context Placement Protocols

### 1. Serial Position Optimization (primacy/recency placement)
Always structure active agent contexts so that critical information sits at the Primacy (beginning) and Recency (end) regions where the LLM weights attention most:
1. **START (Primacy - High Weight):** System Prompt instructions followed immediately by critical T04 regulation constraints (e.g. `Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md`).
2. **MIDDLE (Low Weight):** Summarized older conversation turns and long terminal log dumps.
3. **END (Recency - High Weight):** The current user query, specific target file links, and final constraints (e.g. "Do not use inline styles").

### 2. Token Budget Allocation
Allocate token capacity dynamically across context elements:
- **System Instructions:** 10% of window
- **T04 Regulations / Context:** 15% of window
- **Conversation History:** 40% of window
- **Current Query / Targets:** 10% of window
- **Reserved Output Buffer:** 25% of window

### 3. Tiered Context Strategy
- **Small Context (<32k tokens):** Pass full message history.
- **Medium Context (32k - 100k tokens):** Summarize older conversation turns, keeping only the recent 5 messages fully expanded.
- **Large Context (>100k tokens):** Apply query-specific search to the T04 regulations instead of loading all 1,827 lines into context.

### 4. Intelligent Summarization
When summarization is triggered:
- Keep all user-approved database schema choices (such as the "Hybrid" approach decision).
- Summarize long SQL tables, stdout traces, or OCR text logs into a few sentences detailing the final result/errors.
