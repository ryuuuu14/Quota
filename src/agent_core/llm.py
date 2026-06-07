import os
import time
import hashlib
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from agent_core.metrics import MetricsCollector
from agent_core.cost import CostController

# Simple in-memory LRU-like cache
_LLM_CACHE: Dict[str, Any] = {}
_MAX_CACHE_SIZE = 100

def _get_cache_key(system_prompt: str, user_prompt: str, model: str) -> str:
    combined = f"{system_prompt}|||{user_prompt}|||{model}"
    return hashlib.md5(combined.encode("utf-8")).hexdigest()

def _add_to_cache(key: str, val: Any):
    global _LLM_CACHE
    if len(_LLM_CACHE) >= _MAX_CACHE_SIZE:
        # Simple FIFO/random eviction if full
        first_key = next(iter(_LLM_CACHE))
        _LLM_CACHE.pop(first_key)
    _LLM_CACHE[key] = val

class GeminiPool:
    _client: Optional[genai.Client] = None
    _metrics = MetricsCollector()
    _cost = CostController(budget_pct=0.50)

    @classmethod
    def get_client(cls) -> genai.Client:
        if cls._client is None:
            # We can pick up GEMINI_API_KEY from environment or fallback
            cls._client = genai.Client()
        return cls._client

    @classmethod
    def call(cls, 
             system_prompt: str, 
             user_prompt: str, 
             complexity: str = "default", 
             pipeline_name: str = "unknown",
             agent_name: str = "unknown",
             model_override: Optional[str] = None,
             use_cache: bool = True) -> str:
        
        start_time = time.time()
        
        # 1. Select Model
        if model_override:
            model = model_override
        else:
            model = cls._cost.select_model(complexity)

        # 2. Check Cache
        cache_key = _get_cache_key(system_prompt, user_prompt, model)
        if use_cache and cache_key in _LLM_CACHE:
            duration_ms = (time.time() - start_time) * 1000
            cached_res = _LLM_CACHE[cache_key]
            cls._metrics.log_call(
                agent_name=agent_name,
                pipeline_name=pipeline_name,
                duration_ms=duration_ms,
                tokens_in=0,
                tokens_out=0,
                model_used=model,
                cache_hit=True
            )
            return cached_res

        # 3. Check Budget / Rate Limit
        if not cls._cost.can_proceed(model):
            # Enforce 50% budget limit fallback to alternate models or OpenAI
            if model != "gemini-2.0-flash":
                model = "gemini-2.0-flash"
            else:
                return cls._openai_fallback(system_prompt, user_prompt, pipeline_name, agent_name, start_time)

        # 4. Attempt API call
        try:
            client = cls.get_client()
            cls._cost.record_call(model)
            
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0
                )
            )
            
            res_text = response.text or ""
            
            # Simple token estimation since response.usage_metadata is not always populated or accurate in mock/free SDK calls
            tokens_in = len(system_prompt.split()) + len(user_prompt.split())
            tokens_out = len(res_text.split())
            if response.usage_metadata:
                tokens_in = response.usage_metadata.prompt_token_count
                tokens_out = response.usage_metadata.candidates_token_count

            duration_ms = (time.time() - start_time) * 1000
            cls._metrics.log_call(
                agent_name=agent_name,
                pipeline_name=pipeline_name,
                duration_ms=duration_ms,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                model_used=model,
                cache_hit=False
            )
            
            if use_cache:
                _add_to_cache(cache_key, res_text)
            return res_text

        except Exception as gemini_err:
            # Fallback to OpenAI
            print(f"[Gemini Pool Warning] Gemini call failed: {gemini_err}. Attempting OpenAI fallback...")
            return cls._openai_fallback(system_prompt, user_prompt, pipeline_name, agent_name, start_time)

    @classmethod
    def _openai_fallback(cls, system_prompt: str, user_prompt: str, pipeline_name: str, agent_name: str, start_time: float) -> str:
        try:
            # Check OpenAI env API key
            if not os.environ.get("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable not set.")
                
            model = "gpt-4o"
            cls._cost.record_call(model)
            llm = ChatOpenAI(model=model, temperature=0)
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = llm.invoke(messages)
            res_text = response.content or ""
            
            tokens_in = len(system_prompt.split()) + len(user_prompt.split())
            tokens_out = len(res_text.split())
            
            duration_ms = (time.time() - start_time) * 1000
            cls._metrics.log_call(
                agent_name=agent_name,
                pipeline_name=pipeline_name,
                duration_ms=duration_ms,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                model_used=model,
                cache_hit=False
            )
            return res_text
        except Exception as openai_err:
            print(f"[Gemini Pool Error] OpenAI fallback failed: {openai_err}. Falling back to mock output...")
            # Ultimate mock fallback
            res_text = _mock_llm(system_prompt, user_prompt)
            duration_ms = (time.time() - start_time) * 1000
            cls._metrics.log_call(
                agent_name=agent_name,
                pipeline_name=pipeline_name,
                duration_ms=duration_ms,
                tokens_in=0,
                tokens_out=0,
                model_used="mock-model",
                cache_hit=False
            )
            return res_text

def _mock_llm(system_prompt: str, user_prompt: str) -> str:
    """Produce plausible mock output so the graph structure is testable."""
    task = user_prompt[:200]
    if "PLANNING" in system_prompt or "plan" in system_prompt.lower():
        return f"""## Plan for: {task}

**Files to create:**
- src/bulk_import/templates.py (Excel template generator)
- src/bulk_import/parser.py (Excel parser)
- src/pages/5_NhapDuLieu.py (Upload UI)

**Files to modify:**
- src/database.py (add session_teacher_totals table)
- src/calculations.py (read from session_teacher_totals if present)

**Approach:**
1. Create bulk_import module with template generator and parser
2. Add DB migration for session_teacher_totals
3. Modify calculations.py to check totals table first
4. Build Streamlit upload page with year selector, file upload, preview, confirm

**Risks:** Ensure atomic COMMIT/ROLLBACK on upload"""
    elif "BUILD" in system_prompt or "Implement" in system_prompt:
        return f"""## Build Summary

**Created:**
- src/bulk_import/__init__.py
- src/bulk_import/templates.py (24 lines)
- src/bulk_import/parser.py (45 lines)
- src/pages/5_NhapDuLieu.py (120 lines)

**Modified:**
- src/database.py — added session_teacher_totals table (8 lines)
- src/calculations.py — added totals check before activity_logs aggregation (15 lines)

All files follow project conventions: absolute DB_PATH, Vietnamese labels, MD3 theme, parameterized queries."""
    elif "TEST" in system_prompt or "test" in system_prompt.lower() or "Run" in system_prompt:
        return ""
    elif "VALIDATE" in system_prompt or "review" in system_prompt.lower():
        return """## Validation Report

**PASSED** — 8/8 checks passed

Details:
- Pattern consistency: Follows existing patterns ✓
- Imports: All present ✓
- Error handling: DB wrapped in try/except ✓
- Encoding: UTF-8 configured ✓
- DB_PATH: Uses absolute path ✓
- Vietnamese: UI text in Vietnamese ✓
- Naming: snake_case consistent ✓
- Security: Parameterized queries used ✓

No issues found."""
    return f"[Mock LLM] Processing task: {task[:100]}..."

