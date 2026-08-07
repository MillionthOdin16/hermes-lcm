import sys
import types
import os

hermes_lcm_mod = types.ModuleType('hermes_lcm')
hermes_lcm_mod.__path__ = [os.path.abspath('.')]
sys.modules['hermes_lcm'] = hermes_lcm_mod

# Create dummy 'agent' module
agent_mod = types.ModuleType('agent')
agent_mod.__path__ = [os.path.abspath('.')]
sys.modules['agent'] = agent_mod

context_engine_mod = types.ModuleType('agent.context_engine')
class DummyContextEngine:
    def get_status(self): return {}
    def on_session_reset(self, *args, **kwargs): pass
context_engine_mod.ContextEngine = DummyContextEngine
sys.modules['agent.context_engine'] = context_engine_mod

if __name__ == "__main__":
    os.system("uv run pytest tests/test_lcm_engine.py")
