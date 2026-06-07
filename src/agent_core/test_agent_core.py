import os
import pytest
from agent_core.metrics import MetricsCollector
from agent_core.cost import CostController
from agent_core.llm import GeminiPool
from agent_core import tools

def test_metrics_collector():
    collector = MetricsCollector()
    collector.clear()
    collector.log_call("test_agent", "test_pipeline", 150.0, 10, 20, "mock-model", False)
    
    summary = collector.get_summary()
    assert summary["total_calls"] == 1
    assert summary["total_tokens_in"] == 10
    assert summary["total_tokens_out"] == 20
    assert summary["total_duration_ms"] == 150.0
    assert summary["cache_hit_rate"] == 0.0

def test_cost_controller():
    controller = CostController(budget_pct=0.5)
    model = controller.select_model("default")
    assert model in ["gemini-2.5-flash", "gemini-2.0-flash"]
    
    # Try pro selection
    pro_model = controller.select_model("planning")
    assert pro_model in ["gemini-2.5-pro", "gemini-2.5-flash"]

def test_tools():
    # Test read_file on non-existent file
    content = tools.read_file("nonexistent.txt")
    assert "[ERROR reading" in content

    # Test write_file & read_file & edit_file
    temp_file = "test_temp_file.txt"
    try:
        write_res = tools.write_file(temp_file, "line 1\nline 2\n")
        assert "[OK]" in write_res
        
        read_res = tools.read_file(temp_file)
        assert read_res == "line 1\nline 2\n"
        
        edit_res = tools.edit_file(temp_file, "line 1", "line changed")
        assert "[OK]" in edit_res
        
        read_res2 = tools.read_file(temp_file)
        assert "line changed\nline 2\n" == read_res2
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def test_gemini_pool_mock_fallback():
    # If API keys are missing, it should fall back to mock
    res = GeminiPool.call(
        system_prompt="Test planning prompt",
        user_prompt="plan a task",
        complexity="planning",
        pipeline_name="test_pipeline",
        agent_name="test_agent",
        use_cache=False
    )
    assert "Plan for:" in res or "Build Summary" in res or "Validation Report" in res or "[Mock LLM]" in res

def test_pipeline_orchestrator():
    from agent_core.orchestrator import PipelineOrchestrator
    import os
    os.environ['SKIP_TESTS'] = '1'
    orchestrator = PipelineOrchestrator()
    res = orchestrator.full_cycle("Build a simple calculator")
    assert "research" in res
    assert "dev" in res
    assert "debug" in res
    assert "metrics" in res
