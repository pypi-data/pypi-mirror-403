import re
from contextvars import ContextVar
from typing import Any, Dict, Optional
from datetime import datetime

# This 'vault' stores the data for the current request thread/task only
_request_store: ContextVar[Dict[str, Any]] = ContextVar("hexa_data", default={})

class HexaPackage:
    # 1. Dynamic properties so users can do 'hexapackage.context'
    @property
    def context(self) -> str:
        return _request_store.get().get("context", "")

    @property
    def prompt(self) -> str:
        return _request_store.get().get("prompt", "")

    @property
    def schema(self) -> Dict:
        return _request_store.get().get("schema", {})

    # 2. The Unpack Method: Sets the 'vault' for the current request
    def unpack(self, body: Dict[str, Any]):
        _request_store.set(body)
        return self

    # 3. The Pack Method: Grabs the output AND the assembled input
    def pack(self, output: Any, final_llm_input: str):
        """
        Captures the final result and the actual string sent to the LLM.
        """
        data = _request_store.get()
        return {
            "output": output,
            "trace": {
                "final_llm_input": final_llm_input, # THE ASSEMBLED SOUP
                "timestamp": datetime.utcnow().isoformat()
            }
        }

# Create a single instance to be used everywhere
hexapackage = HexaPackage()