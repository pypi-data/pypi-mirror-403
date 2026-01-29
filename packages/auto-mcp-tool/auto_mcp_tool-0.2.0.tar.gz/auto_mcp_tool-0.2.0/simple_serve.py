from auto_mcp import AutoMCP
import examples.simple_math.math_utils as math_utils

auto = AutoMCP(use_llm=False)
server = auto.create_server([math_utils])
server.run()