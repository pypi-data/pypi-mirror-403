"""CodeContext - Get token-optimized context for a function/symbol."""

import asyncio
from typing import override

from kosong.tooling import CallableTool2, ToolReturnValue, ToolOk, ToolError
from pydantic import BaseModel, Field

from axe_cli.soul.agent import Runtime
from axe_cli.tools.utils import ToolResultBuilder


class CodeContextParams(BaseModel):
    """Parameters for CodeContext tool."""
    
    symbol: str = Field(
        description="Function, class, or method name to get context for."
    )
    path: str = Field(
        description="Project path. Defaults to current directory.",
        default="."
    )


class CodeContext(CallableTool2[CodeContextParams]):
    """
    Get LLM-ready, token-optimized context for a function/symbol using axe-dig.
    
    Runs: `chop context <symbol> --project <path>`
    
    Returns a compressed summary of a symbol that preserves understanding
    while using 95% fewer tokens than raw code.
    """
    
    name: str = "CodeContext"
    params: type[CodeContextParams] = CodeContextParams
    
    def __init__(self, runtime: Runtime):
        description = """Get token-optimized context for a function/symbol.

Runs: `chop context <symbol> --project <path>`

Returns a compressed LLM-ready summary that includes:
- Function signature and docstring
- Key dependencies (what it calls)
- Callers (who uses it)  
- Data flow summary
- Relevant code snippets

**Output format:** "N functions summarized in ~M tokens"

**Why use this instead of ReadFile?**
- 95% fewer tokens while preserving understanding
- Includes cross-file context (callers, dependencies)
- Optimized for LLM comprehension

**When to use:**
- Understanding a function before editing
- Getting context without reading entire files
- Planning refactoring (see dependencies)

**Note:** The codebase is automatically indexed on startup.

Example:
```json
{"symbol": "validate_user", "path": "."}
```
"""
        super().__init__(description=description)
        self._runtime = runtime
        self._work_dir = runtime.builtin_args.AXE_WORK_DIR
    
    @override
    async def __call__(self, params: CodeContextParams) -> ToolReturnValue:
        builder = ToolResultBuilder()
        
        if not params.symbol.strip():
            return ToolError(
                message="Symbol name cannot be empty.",
                brief="Empty symbol"
            )
        
        path = params.path
        if path == ".":
            path = str(self._work_dir)
        
        builder.write(f"📋 Getting context for: {params.symbol}\n\n")
        
        try:
            cmd = f"chop context {params.symbol} --project {path}"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._work_dir)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                if output:
                    builder.write(output)
                    builder.write("\n")
                    return builder.ok(brief=f"Context for {params.symbol}")
                else:
                    return ToolOk(
                        message=f"No context found for '{params.symbol}'. The symbol may not exist or the index needs rebuilding.",
                        brief="No context"
                    )
            else:
                error_msg = stderr.decode().strip() or stdout.decode().strip()
                if "not found" in error_msg.lower():
                    return ToolError(
                        message=f"Symbol '{params.symbol}' not found in the codebase. Check the symbol name or try running 'chop warm .' in terminal to rebuild the index.",
                        brief="Symbol not found"
                    )
                return ToolError(
                    message=f"Failed to get context: {error_msg}",
                    brief="Failed"
                )
                
        except FileNotFoundError:
            return ToolError(
                message="chop command not found. Make sure axe-dig is installed: pip install axe-dig",
                brief="axe-dig not installed"
            )
        except Exception as e:
            return ToolError(
                message=f"Failed to get context: {str(e)}",
                brief="Error"
            )
