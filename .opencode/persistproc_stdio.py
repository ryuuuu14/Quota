import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from fastmcp import FastMCP
from persistproc.process_manager import ProcessManager
from persistproc.tools import ALL_TOOL_CLASSES

data_dir = Path(os.environ.get("PERSISTPROC_DATA_DIR", Path.home() / ".persistproc"))
pm = ProcessManager(None, data_dir=data_dir)
app = FastMCP("persistproc")

for tool_cls in ALL_TOOL_CLASSES:
    tool = tool_cls()
    tool.register_tool(pm, app)

app.run(transport="stdio")
