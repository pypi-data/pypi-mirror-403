"""
RLM Engine - Recursive Language Model execution engine.

This implements the RLM pattern from "Recursive Language Models" (Zhang et al., 2025)
following the reference implementation at https://github.com/alexzhang13/rlm

The key insight: Long prompts should not be fed into the neural network directly
but should instead be treated as part of the environment that the LLM can
symbolically interact with.

The model has access to:
- knowledge: KnowledgeContext instance for exploring documents
- llm_query(prompt): Function to make recursive LLM calls on excerpts
- llm_query_batched(prompts): Function to make multiple concurrent LLM calls
- print(): Outputs to observation buffer
- FINAL(answer) / FINAL_VAR(var_name) to return results
"""

import logging
import re
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from watsonx_rlm_knowledge.context import KnowledgeContext
from watsonx_rlm_knowledge.exceptions import EngineError

logger = logging.getLogger(__name__)


# Pattern to extract REPL code blocks
CODE_BLOCK_PATTERN = re.compile(
    r"```repl\s*\n(.*?)\n```",
    re.DOTALL
)

# Pattern for FINAL_VAR - must be at start of line
FINAL_VAR_PATTERN = re.compile(
    r"^\s*FINAL_VAR\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)",
    re.MULTILINE
)

# Pattern for FINAL - greedy to handle nested parens
FINAL_PATTERN = re.compile(
    r"^\s*FINAL\s*\((.*)\)\s*$",
    re.MULTILINE | re.DOTALL
)


def _build_system_prompt(num_documents: int, total_size_mb: float, context_summary: str) -> str:
    """Build the RLM system prompt following the paper's approach."""
    return f"""You are tasked with answering a query using a knowledge base. You can access and analyze this knowledge interactively in a REPL environment that can recursively query sub-LLMs. You will be queried iteratively until you provide a final answer.

The REPL environment is initialized with:
1. A `knowledge` object that provides access to {num_documents} documents ({total_size_mb:.1f} MB total).
2. A `llm_query(prompt)` function to query a sub-LLM (handles ~100K chars) for semantic analysis.
3. A `llm_query_batched(prompts)` function to query multiple prompts concurrently (much faster).
4. The ability to use `print()` to view output and continue reasoning.
{context_summary}

KNOWLEDGE OBJECT METHODS:
- knowledge.list_files() -> List[str]: All document paths
- knowledge.find_files(pattern) -> List[str]: Find files by glob (e.g., "*cancel*", "*server*")
- knowledge.search(needle, max_matches=100) -> List[SearchMatch]: Full-text search
- knowledge.grep(needle) -> List[(path, line_no, text)]: Simple grep
- knowledge.head(path, nbytes=32000) -> str: Read beginning of document
- knowledge.read_full(path) -> str: Read entire document (up to 2MB)
- knowledge.read_slice(path, offset, nbytes) -> str: Read section of document

Make sure to explicitly look through the knowledge base in REPL before answering your query. A good strategy is:
1. First search/find relevant files using multiple keywords
2. Read the content of ALL relevant files found (there may be multiple!)
3. Use llm_query to extract/summarize information from each document
4. Aggregate findings into a comprehensive answer

When you want to execute Python code, wrap it in triple backticks with 'repl':
```repl
# Search for relevant documents
matches = knowledge.search("cancel")
for m in matches[:10]:
    print(f"{{m.path}}: {{m.line_text[:80]}}")
```

When you have gathered enough information and are ready to answer, use ONE of:
- FINAL(your complete answer here) - for direct answers
- FINAL_VAR(variable_name) - to return a variable you built

Remember: There may be MULTIPLE relevant documents covering different aspects. Search thoroughly and read all relevant files before providing your final answer."""


@dataclass
class RLMConfig:
    """Configuration for RLM engine."""
    max_iterations: int = 15
    max_code_retries: int = 3
    llm_query_max_chars: int = 100_000
    execution_timeout: float = 60.0
    max_output_chars: int = 20000


@dataclass
class RLMResult:
    """Result from RLM execution."""
    answer: str
    iterations: int
    total_time: float
    observations: List[str] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    llm_query_count: int = 0
    success: bool = True


class RLMEngine:
    """Executes RLM loops for knowledge base queries.

    Implements the Recursive Language Model pattern where the LLM
    programmatically explores a knowledge base through a REPL environment.
    """

    def __init__(
        self,
        knowledge: KnowledgeContext,
        llm_call_fn: Callable[[List[Dict[str, Any]]], str],
        config: Optional[RLMConfig] = None,
    ):
        self.knowledge = knowledge
        self.llm_call_fn = llm_call_fn
        self.config = config or RLMConfig()
        self._namespace: Dict[str, Any] = {}
        self._llm_query_count = 0
        self._output_buffer: List[str] = []

    def _reset_namespace(self):
        """Reset the REPL execution namespace."""
        self._llm_query_count = 0
        self._output_buffer = []
        self._namespace = {
            "knowledge": self.knowledge,
            "llm_query": self._llm_query,
            "llm_query_batched": self._llm_query_batched,
            "print": self._capture_print,
            "len": len, "str": str, "int": int, "float": float, "bool": bool,
            "list": list, "dict": dict, "set": set, "tuple": tuple,
            "range": range, "enumerate": enumerate, "zip": zip,
            "sorted": sorted, "min": min, "max": max, "sum": sum,
            "any": any, "all": all, "abs": abs, "round": round,
            "isinstance": isinstance, "type": type, "hasattr": hasattr, "getattr": getattr,
            "re": re,
        }

    def _capture_print(self, *args, **kwargs):
        """Capture print output to buffer."""
        output = " ".join(str(a) for a in args)
        self._output_buffer.append(output)

    def _llm_query(self, prompt: str) -> str:
        """Make a recursive LLM call on text."""
        self._llm_query_count += 1
        if len(prompt) > self.config.llm_query_max_chars:
            prompt = prompt[:self.config.llm_query_max_chars] + "\n\n[...truncated...]"

        messages = [
            {"role": "system", "content": "Answer based ONLY on the provided text. Be concise and factual."},
            {"role": "user", "content": prompt},
        ]
        try:
            return self.llm_call_fn(messages)
        except Exception as e:
            logger.warning(f"llm_query failed: {e}")
            return f"(error: {e})"

    def _llm_query_batched(self, prompts: List[str]) -> List[str]:
        """Make multiple LLM calls (sequential for now)."""
        return [self._llm_query(p) for p in prompts]

    def _get_context_summary(self) -> tuple:
        """Get summary information about the knowledge base."""
        try:
            docs = self.knowledge.list_documents()
            num_docs = len(docs)
            total_bytes = sum(d.text_size_bytes for d in docs)
            total_mb = total_bytes / (1024 * 1024)

            # Sample files
            summary = ""
            if docs:
                sample = [d.relative_path for d in docs[:5]]
                summary = "\n\nSample files: " + ", ".join(sample)
                if len(docs) > 5:
                    summary += f" ... and {len(docs) - 5} more"

            return num_docs, total_mb, summary
        except Exception as e:
            logger.warning(f"Failed to get context summary: {e}")
            return 0, 0.0, ""

    def _find_code_blocks(self, text: str) -> List[str]:
        """Extract REPL code blocks from response."""
        blocks = []
        for match in CODE_BLOCK_PATTERN.finditer(text):
            blocks.append(match.group(1).strip())
        return blocks

    def _find_final_answer(self, text: str) -> Optional[str]:
        """Find FINAL(...) or FINAL_VAR(...) in response."""
        # Check FINAL_VAR first
        match = FINAL_VAR_PATTERN.search(text)
        if match:
            var_name = match.group(1).strip()
            if var_name in self._namespace:
                return str(self._namespace[var_name])
            return None  # Variable not found, continue

        # Check FINAL
        match = FINAL_PATTERN.search(text)
        if match:
            return match.group(1).strip()

        return None

    def _execute_code(self, code: str) -> Dict[str, Any]:
        """Execute Python code in restricted namespace."""
        self._output_buffer = []

        # Basic safety
        forbidden = ["import ", "__import__", "exec(", "eval(", "open(", "os.", "sys.", "subprocess"]
        for pattern in forbidden:
            if pattern in code:
                return {"success": False, "output": f"Forbidden: {pattern}", "error": True}

        try:
            exec(code, {"__builtins__": {}}, self._namespace)
            output = "\n".join(self._output_buffer) if self._output_buffer else "(no output)"
            return {"success": True, "output": output[:self.config.max_output_chars], "error": False}
        except Exception as e:
            tb = traceback.format_exc()
            return {"success": False, "output": f"Error: {e}\n{tb}", "error": True}

    def _format_execution_result(self, code: str, result: Dict[str, Any]) -> str:
        """Format code execution result for message history."""
        status = "executed successfully" if result["success"] else "failed"
        return f"Code {status}:\n```python\n{code}\n```\n\nREPL output:\n{result['output']}"

    def _default_answer(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a default answer when max iterations reached."""
        messages = messages + [{
            "role": "user",
            "content": "You've reached the maximum iterations. Based on all the information you've gathered, please provide your best final answer now. Summarize what you found."
        }]
        try:
            response = self.llm_call_fn(messages)
            # Try to extract just the answer part
            if "FINAL(" in response:
                answer = self._find_final_answer(response)
                if answer:
                    return answer
            return response
        except Exception as e:
            return f"Unable to generate answer: {e}"

    def run(self, query: str, additional_context: str = "") -> RLMResult:
        """Run RLM loop to answer a query."""
        start_time = time.time()
        self._reset_namespace()

        # Build system prompt
        num_docs, total_mb, context_summary = self._get_context_summary()
        system_prompt = _build_system_prompt(num_docs, total_mb, context_summary)

        if additional_context:
            system_prompt += f"\n\nAdditional context: {additional_context}"

        # Initial messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\n\nStart by exploring the knowledge base with ```repl``` code blocks."},
        ]

        result = RLMResult(answer="", iterations=0, total_time=0.0)
        code_errors = 0

        for iteration in range(self.config.max_iterations):
            result.iterations = iteration + 1

            try:
                # Get LLM response
                response = self.llm_call_fn(messages)

                if not response or not response.strip():
                    logger.warning(f"Empty response at iteration {iteration + 1}")
                    messages.append({"role": "assistant", "content": ""})
                    messages.append({"role": "user", "content": "Please continue with a ```repl``` code block or provide FINAL(answer)."})
                    continue

                # Check for final answer
                final_answer = self._find_final_answer(response)
                if final_answer is not None:
                    result.answer = final_answer
                    result.success = True
                    result.llm_query_count = self._llm_query_count
                    result.total_time = time.time() - start_time
                    return result

                # Find and execute code blocks
                code_blocks = self._find_code_blocks(response)

                if code_blocks:
                    messages.append({"role": "assistant", "content": response})

                    for code in code_blocks:
                        result.code_blocks.append(code)
                        exec_result = self._execute_code(code)
                        result.observations.append(exec_result["output"])

                        formatted = self._format_execution_result(code, exec_result)
                        messages.append({"role": "user", "content": formatted})

                        if exec_result["error"]:
                            code_errors += 1
                        else:
                            code_errors = 0

                        if code_errors >= self.config.max_code_retries:
                            messages.append({"role": "user", "content": "Multiple code errors. Please provide FINAL(answer) with what you know."})
                else:
                    # No code block, no final answer - prompt to continue
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": "Please output a ```repl``` code block to explore or FINAL(answer) when ready."})

            except Exception as e:
                logger.error(f"Iteration {iteration + 1} error: {e}")
                messages.append({"role": "user", "content": f"Error occurred: {e}. Please continue or provide FINAL(answer)."})

        # Max iterations reached - get default answer
        result.answer = self._default_answer(messages)
        result.success = True
        result.llm_query_count = self._llm_query_count
        result.total_time = time.time() - start_time
        return result