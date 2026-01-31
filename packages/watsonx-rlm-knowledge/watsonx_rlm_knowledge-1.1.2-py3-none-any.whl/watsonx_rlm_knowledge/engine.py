"""
RLM Engine - Recursive Language Model execution engine.

This implements the RLM pattern from "Recursive Language Models" (Zhang et al., 2025)
where:
1. The prompt/context is treated as part of an external environment
2. The LLM writes Python code to explore the knowledge base
3. The LLM can recursively call itself (llm_query) over snippets
4. Variables persist in a REPL environment across iterations
5. Final output via FINAL(answer) or FINAL_VAR(variable_name)

Key insight from the paper: "Long prompts should not be fed into the neural
network directly but should instead be treated as part of the environment
that the LLM can symbolically interact with."

The model has access to:
- knowledge: KnowledgeContext instance for exploring documents
- llm_query(prompt): Function to make recursive LLM calls on excerpts
- print(): Outputs to observation buffer
- FINAL(answer) / FINAL_VAR(var_name) to return results
"""

import logging
import re
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from watsonx_rlm_knowledge.context import KnowledgeContext
from watsonx_rlm_knowledge.exceptions import (
    EngineError,
    MaxIterationsError,
    CodeExecutionError,
)

logger = logging.getLogger(__name__)


# Pattern to extract Python/REPL code blocks
CODE_BLOCK_PATTERN = re.compile(
    r"```(?:python|repl)\s*(.*?)\s*```",
    re.DOTALL | re.IGNORECASE
)

# Pattern to detect FINAL( - we'll use balanced paren extraction
FINAL_START_PATTERN = re.compile(r"FINAL\s*\(", re.IGNORECASE)

# Pattern to detect FINAL_VAR() - return variable
FINAL_VAR_PATTERN = re.compile(
    r"FINAL_VAR\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)",
    re.DOTALL
)

# Legacy pattern for backwards compatibility
FINAL_ANSWER_PATTERN = re.compile(
    r"FINAL_ANSWER:\s*(.*)",
    re.DOTALL
)


def _extract_balanced_parens(text: str, start_pos: int) -> Optional[str]:
    """Extract content from balanced parentheses starting at start_pos.

    Handles nested parentheses correctly, so FINAL(An SSAD (doc) is...)
    will extract the full content, not just "An SSAD (doc".

    Args:
        text: The full text
        start_pos: Position of the opening '('

    Returns:
        The content inside the balanced parentheses, or None if unbalanced
    """
    if start_pos >= len(text) or text[start_pos] != '(':
        return None

    depth = 0
    content_start = start_pos + 1

    for i in range(start_pos, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                # Found the matching closing paren
                return text[content_start:i].strip()

    # Unbalanced - return everything after opening paren
    return text[content_start:].strip()


def _extract_final_content(text: str) -> Optional[str]:
    """Extract the content from FINAL(...) handling nested parentheses."""
    match = FINAL_START_PATTERN.search(text)
    if not match:
        return None

    # Find the opening paren position
    paren_pos = match.end() - 1
    return _extract_balanced_parens(text, paren_pos)


def _build_rlm_system_prompt(
    context_summary: str,
    num_documents: int,
    total_size_mb: float,
) -> str:
    """Build the RLM system prompt with context metadata.

    Following the paper's approach of informing the LLM about the
    environment it's operating in.
    """
    return f"""You are operating in an RLM (Recursive Language Model) REPL environment to answer questions about a knowledge base.

IMPORTANT: You do NOT have the documents in your context window. Instead, the knowledge base is loaded as an external environment that you can interact with programmatically.

ENVIRONMENT SUMMARY:
- Number of documents: {num_documents}
- Total text size: {total_size_mb:.2f} MB
- Context access: Via the 'knowledge' object
{context_summary}

AVAILABLE IN REPL:
1. 'knowledge' - KnowledgeContext for exploring documents:
   - knowledge.list_files() -> List[str]: All document paths
   - knowledge.list_documents(pattern=None) -> List[DocumentSummary]: Documents with metadata
   - knowledge.head(path, nbytes=32000) -> str: Read beginning of document
   - knowledge.read_slice(path, offset=0, nbytes=50000) -> str: Read section of document
   - knowledge.read_full(path) -> str: Read entire document (up to 2MB)
   - knowledge.search(needle, max_matches=100) -> List[SearchMatch]: Full-text search
   - knowledge.grep(needle, max_matches=50) -> List[(path, line_no, text)]: Simple grep
   - knowledge.search_regex(pattern) -> List[SearchMatch]: Regex search
   - knowledge.find_files(pattern) -> List[str]: Find files by glob
   - knowledge.get_table_of_contents(path) -> List[str]: Get document headings
   - knowledge.count_occurrences(needle) -> int: Count string occurrences

2. 'llm_query(prompt)' - Recursively query an LLM on text excerpts:
   - Can handle up to ~100K characters per call
   - Use for semantic analysis, summarization, or sub-questions
   - Returns string response
   - IMPORTANT: Batch information together to minimize calls (e.g., process 50-100 items per call)

3. 'print()' - Output to observation buffer (will be shown to you)

4. Variables persist across REPL iterations - use them to build up your answer

CODE EXECUTION:
When you need to explore the knowledge base, output a code block:
```repl
# Your Python code here
# Use 'knowledge' and 'llm_query' as needed
# Results from print() will be shown to you
result = knowledge.search("your search term")
for r in result[:10]:
    print(f"{{r.path}}:{{r.line_number}}: {{r.line_text}}")
```

FINAL ANSWER:
When you have enough information, output ONE of:
- FINAL(your complete answer here) - to return a direct answer
- FINAL_VAR(variable_name) - to return a variable you built up in the REPL

STRATEGY (from paper):
1. Start by probing: List files, search for keywords, print samples
2. Use code to filter: regex queries, keyword searches based on your priors
3. Chunk and recurse: For large content, split and use llm_query() per chunk
4. Build up answers: Store intermediate results in variables
5. Aggregate: Combine sub-results into final answer

EXAMPLE - Searching and reading:
```repl
# Find relevant documents
matches = knowledge.search("authentication")
print(f"Found {{len(matches)}} matches")
for m in matches[:5]:
    print(f"  {{m.path}}:{{m.line_number}}: {{m.line_text[:80]}}")
```

EXAMPLE - Chunking with llm_query:
```repl
# For a large document, chunk and summarize
content = knowledge.read_full("docs/manual.pdf")
chunk_size = 50000
summaries = []
for i in range(0, len(content), chunk_size):
    chunk = content[i:i+chunk_size]
    summary = llm_query(f"Summarize the key points about authentication from this section:\\n\\n{{chunk}}")
    summaries.append(summary)
    print(f"Chunk {{i//chunk_size + 1}}: {{summary[:100]}}...")

# Aggregate summaries
final_answer = llm_query(f"Combine these summaries into a comprehensive answer:\\n\\n" + "\\n---\\n".join(summaries))
```
Then: FINAL_VAR(final_answer)

EXAMPLE - Information-dense tasks:
```repl
# When processing many items, batch them
items = knowledge.read_full("data.txt").split("\\n")
batch_size = 100
classifications = []
for i in range(0, len(items), batch_size):
    batch = items[i:i+batch_size]
    batch_str = "\\n".join(batch)
    result = llm_query(f"Classify each of these items:\\n{{batch_str}}")
    classifications.append(result)
    print(f"Processed batch {{i//batch_size + 1}}/{{len(items)//batch_size + 1}}")
```

RULES:
- Output ONLY a ```repl``` code block OR a FINAL statement, never both
- Be efficient - prefer targeted searches over reading entire documents
- For semantic analysis (classification, summarization), use llm_query()
- Batch llm_query() calls to minimize API costs (aim for 50-100K chars per call)
- Track progress with print() statements

IMPORTANT - THOROUGH EXPLORATION REQUIRED:
- Do NOT give up after just 1-2 searches. Try MULTIPLE search strategies:
  1. Try different keywords (synonyms, related terms, abbreviations)
  2. Try case variations and partial matches
  3. Use find_files() to locate relevant documents by name
  4. Read promising files directly with head() or read_full()
- Only conclude "information not found" after AT LEAST 5 different search attempts
- If initial searches find nothing, try:
  - Broader terms (e.g., "server" instead of "bare metal server")
  - More specific terms (e.g., "cancel device" instead of "cancel")
  - Related concepts (e.g., "remove", "delete", "terminate")
  - File name patterns (e.g., find_files("*cancel*") or find_files("*bare*metal*"))
"""


@dataclass
class RLMConfig:
    """Configuration for RLM engine.

    Attributes:
        max_iterations: Maximum REPL iterations before timeout
        min_iterations_before_not_found: Minimum iterations before allowing "not found" answers
        max_code_retries: Max retries on code execution errors
        llm_query_max_chars: Max characters per llm_query call (~100K as per paper)
        main_max_tokens: Max output tokens for main LLM
        temperature: Sampling temperature
        timeout_per_iteration: Timeout per iteration in seconds
        safe_execution: If True, restrict dangerous operations
        include_traceback: If True, include tracebacks in errors
    """
    max_iterations: int = 20  # Increased from 15 per paper observations
    min_iterations_before_not_found: int = 5  # Require thorough exploration
    max_code_retries: int = 3
    llm_query_max_chars: int = 100_000  # ~100K chars per paper
    main_max_tokens: int = 8192  # Increased for longer code blocks
    temperature: float = 0.1
    timeout_per_iteration: float = 120.0  # Increased for complex operations
    safe_execution: bool = True
    include_traceback: bool = True


@dataclass
class RLMResult:
    """Result from RLM execution.

    Attributes:
        answer: The final answer produced
        iterations: Number of REPL iterations used
        total_time: Total execution time in seconds
        observations: List of observation outputs from each iteration
        code_blocks: List of code blocks executed
        llm_query_count: Number of recursive llm_query calls made
        errors: List of any errors encountered
        success: Whether execution completed successfully
    """
    answer: str
    iterations: int
    total_time: float
    observations: List[str] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    llm_query_count: int = 0
    errors: List[str] = field(default_factory=list)
    success: bool = True


class RLMEngine:
    """Executes RLM loops for knowledge base queries.

    Implements the Recursive Language Model pattern where the LLM
    programmatically explores a knowledge base through a REPL environment,
    making recursive sub-calls as needed.

    Key features from the paper:
    - Context treated as external environment (not in prompt)
    - llm_query() for recursive sub-LM calls
    - Variables persist across iterations
    - FINAL() / FINAL_VAR() for flexible output

    Example:
        engine = RLMEngine(knowledge, llm_call_fn)
        result = engine.run("How does the authentication system work?")
        print(result.answer)
        print(f"Used {result.iterations} iterations, {result.llm_query_count} sub-calls")
    """

    def __init__(
        self,
        knowledge: KnowledgeContext,
        llm_call_fn: Callable[[List[Dict[str, Any]]], str],
        config: Optional[RLMConfig] = None,
    ):
        """Initialize RLM engine.

        Args:
            knowledge: Knowledge context for document access
            llm_call_fn: Function to call the LLM with messages
            config: Optional engine configuration
        """
        self.knowledge = knowledge
        self.llm_call_fn = llm_call_fn
        self.config = config or RLMConfig()

        # Execution namespace for REPL
        self._namespace: Dict[str, Any] = {}
        self._llm_query_count = 0
        self._observation_buffer: List[str] = []
        self._reset_namespace()

    def _reset_namespace(self):
        """Reset the REPL execution namespace."""
        self._llm_query_count = 0
        self._observation_buffer = []

        self._namespace = {
            # Core RLM objects
            "knowledge": self.knowledge,
            "llm_query": self._llm_query,
            # Legacy alias
            "subcall": self._llm_query,
            # Safe builtins
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "sorted": sorted,
            "reversed": reversed,
            "min": min,
            "max": max,
            "sum": sum,
            "any": any,
            "all": all,
            "abs": abs,
            "round": round,
            "print": self._safe_print,
            "isinstance": isinstance,
            "type": type,
            "repr": repr,
            "hasattr": hasattr,
            "getattr": getattr,
            # For text processing
            "re": re,
            # Result variables
            "obs": "",
            "result": None,
            "answer": None,
            "final_answer": None,
        }

    def _safe_print(self, *args, **kwargs):
        """Safe print that captures to observation buffer."""
        output = " ".join(str(a) for a in args)
        self._observation_buffer.append(output)
        # Also store in obs for backwards compatibility
        current_obs = self._namespace.get("obs", "")
        if current_obs:
            self._namespace["obs"] = current_obs + "\n" + output
        else:
            self._namespace["obs"] = output

    def _llm_query(self, prompt: str) -> str:
        """Make a recursive LLM call on a text excerpt.

        This is the key mechanism from the RLM paper for handling
        content that requires semantic understanding.

        Args:
            prompt: The prompt/question with context to send to sub-LLM

        Returns:
            String response from the sub-LLM
        """
        self._llm_query_count += 1

        # Cap input size per paper guidelines (~100K chars)
        if len(prompt) > self.config.llm_query_max_chars:
            prompt = prompt[:self.config.llm_query_max_chars] + "\n\n[...truncated...]"

        sub_messages = [
            {
                "role": "system",
                "content": (
                    "You are a sub-LLM in an RLM (Recursive Language Model) loop. "
                    "Answer based ONLY on the provided text. Be concise and factual. "
                    "If asked to classify, summarize, or extract, follow the format requested."
                )
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.llm_call_fn(sub_messages)
            return response
        except Exception as e:
            logger.warning(f"llm_query failed: {e}")
            return f"(llm_query error: {e})"

    def _get_context_summary(self) -> tuple:
        """Get summary information about the knowledge base."""
        try:
            docs = self.knowledge.list_documents()
            num_docs = len(docs)
            total_bytes = sum(d.text_size_bytes for d in docs)
            total_mb = total_bytes / (1024 * 1024)

            # Build summary of document types
            formats = {}
            for d in docs:
                fmt = d.format
                formats[fmt] = formats.get(fmt, 0) + 1

            format_str = ", ".join(f"{count} {fmt}" for fmt, count in sorted(formats.items()))
            summary = f"- Document types: {format_str}" if format_str else ""

            # Add sample file names
            if docs:
                sample = docs[:5]
                file_list = "\n".join(f"  - {d.relative_path}" for d in sample)
                if len(docs) > 5:
                    file_list += f"\n  ... and {len(docs) - 5} more"
                summary += f"\n- Sample files:\n{file_list}"

            return summary, num_docs, total_mb
        except Exception as e:
            logger.warning(f"Failed to get context summary: {e}")
            return "", 0, 0.0

    def run(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        additional_context: str = "",
    ) -> RLMResult:
        """Run RLM loop to answer a query.

        Args:
            query: The user's question about the knowledge base
            system_prompt: Optional custom system prompt (overrides default)
            additional_context: Additional context to include

        Returns:
            RLMResult with answer and execution metadata
        """
        start_time = time.time()
        self._reset_namespace()

        # Build system prompt with context metadata
        if system_prompt:
            system_content = system_prompt
        else:
            context_summary, num_docs, total_mb = self._get_context_summary()
            system_content = _build_rlm_system_prompt(
                context_summary=context_summary,
                num_documents=num_docs,
                total_size_mb=total_mb,
            )

        if additional_context:
            system_content += f"\n\nADDITIONAL CONTEXT:\n{additional_context}"

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Query: {query}"},
        ]

        result = RLMResult(
            answer="",
            iterations=0,
            total_time=0.0,
        )

        code_retry_count = 0

        for iteration in range(self.config.max_iterations):
            result.iterations = iteration + 1

            try:
                # Get LLM response
                model_response = self.llm_call_fn(messages)

                if not model_response:
                    logger.warning("Empty model response")
                    messages.append({"role": "assistant", "content": ""})
                    messages.append({
                        "role": "user",
                        "content": "Your response was empty. Please output a ```repl``` code block to explore or FINAL(answer)."
                    })
                    continue

                logger.debug(f"Iteration {iteration + 1}: {model_response[:200]}...")

                # Check for FINAL_VAR() first (returns a variable)
                final_var_match = FINAL_VAR_PATTERN.search(model_response)
                if final_var_match:
                    var_name = final_var_match.group(1)
                    if var_name in self._namespace:
                        result.answer = str(self._namespace[var_name])
                        result.success = True
                        break
                    else:
                        # Variable not found, ask to fix
                        messages.append({"role": "assistant", "content": model_response})
                        messages.append({
                            "role": "user",
                            "content": f"Variable '{var_name}' not found. Available variables: {list(k for k in self._namespace.keys() if not k.startswith('_') and k not in ['knowledge', 'llm_query', 'subcall', 're', 'print'])}. Please fix or use FINAL(answer) instead."
                        })
                        continue

                # Check for FINAL() (direct answer) - use balanced paren extraction
                final_content = _extract_final_content(model_response)
                if final_content is not None:
                    # Check if this looks like a "not found" answer given too early
                    not_found_phrases = [
                        "not found", "no information", "does not contain",
                        "couldn't find", "could not find", "unable to find",
                        "no relevant", "no results", "no matches",
                        "not present", "not available", "cannot find"
                    ]
                    is_not_found = any(phrase in final_content.lower() for phrase in not_found_phrases)

                    if is_not_found and iteration < self.config.min_iterations_before_not_found - 1:
                        # Reject premature "not found" - push back to explore more
                        messages.append({"role": "assistant", "content": model_response})
                        messages.append({
                            "role": "user",
                            "content": (
                                "You've only done a few searches. Before concluding the information isn't available, "
                                "please try more search strategies:\n"
                                "1. Try different keywords (synonyms, related terms)\n"
                                "2. Use find_files() to search by filename\n"
                                "3. Try broader or more specific terms\n"
                                "4. Read promising files directly with head() or read_full()\n\n"
                                "Output a ```repl``` code block with additional searches."
                            )
                        })
                        continue

                    result.answer = final_content
                    result.success = True
                    break

                # Check for legacy FINAL_ANSWER:
                if self._is_final_answer(model_response):
                    result.answer = self._extract_final_answer(model_response)
                    result.success = True
                    break

                # Extract and execute code
                code = self._extract_code(model_response)

                if code:
                    result.code_blocks.append(code)

                    # Clear observation buffer
                    self._observation_buffer = []

                    # Execute the code
                    exec_result = self._execute_code(code)

                    if exec_result["success"]:
                        obs = exec_result["observation"]
                        result.observations.append(obs)
                        code_retry_count = 0  # Reset on success

                        # Add to conversation
                        messages.append({"role": "assistant", "content": model_response})

                        # Truncate observation if too long
                        obs_display = obs
                        if len(obs) > 8000:
                            obs_display = obs[:8000] + f"\n\n[...truncated {len(obs) - 8000} chars. Use more targeted queries or store intermediate results in variables...]"

                        messages.append({
                            "role": "user",
                            "content": f"Execution output:\n{obs_display}\n\nContinue exploring with ```repl``` or provide FINAL(answer) / FINAL_VAR(variable_name)."
                        })
                    else:
                        error_msg = exec_result["error"]
                        result.errors.append(error_msg)
                        code_retry_count += 1

                        if code_retry_count >= self.config.max_code_retries:
                            messages.append({"role": "assistant", "content": model_response})
                            messages.append({
                                "role": "user",
                                "content": (
                                    f"Code execution failed repeatedly: {error_msg}\n\n"
                                    "Please provide FINAL(your answer based on what you know so far)."
                                )
                            })
                        else:
                            messages.append({"role": "assistant", "content": model_response})
                            messages.append({
                                "role": "user",
                                "content": f"Code execution error: {error_msg}\n\nPlease fix the code and try again."
                            })
                else:
                    # No code block found - guide back on track
                    messages.append({"role": "assistant", "content": model_response})
                    messages.append({
                        "role": "user",
                        "content": (
                            "Please output ONE of:\n"
                            "1. A ```repl``` code block to explore the knowledge base\n"
                            "2. FINAL(your answer here) to provide a direct answer\n"
                            "3. FINAL_VAR(variable_name) to return a variable you've built\n\n"
                            "Do not include explanations outside the code block."
                        )
                    })

            except Exception as e:
                logger.error(f"Iteration {iteration + 1} failed: {e}")
                result.errors.append(str(e))

                messages.append({
                    "role": "user",
                    "content": f"An error occurred: {e}\n\nPlease continue or provide FINAL(answer)."
                })

        # Record llm_query count
        result.llm_query_count = self._llm_query_count

        # Check if we exhausted iterations
        if not result.answer:
            result.success = False

            # Try to provide partial answer from observations
            partial_info = ""
            if result.observations:
                partial_info = "\n\nInformation gathered:\n" + "\n---\n".join(result.observations[-3:])

            result.answer = (
                f"I was unable to complete the answer within {result.iterations} iterations "
                f"({self._llm_query_count} sub-queries made).{partial_info}"
            )

        result.total_time = time.time() - start_time
        return result

    def _is_final_answer(self, text: str) -> bool:
        """Check if response contains legacy final answer pattern."""
        return "FINAL_ANSWER:" in text

    def _extract_final_answer(self, text: str) -> str:
        """Extract the final answer from legacy pattern."""
        match = FINAL_ANSWER_PATTERN.search(text)
        if match:
            return match.group(1).strip()

        idx = text.find("FINAL_ANSWER:")
        if idx != -1:
            return text[idx + 13:].strip()

        return text

    def _extract_code(self, text: str) -> Optional[str]:
        """Extract Python/REPL code from response."""
        match = CODE_BLOCK_PATTERN.search(text)
        if match:
            return match.group(1).strip()

        # Fallback: if it looks like Python code (has knowledge. or llm_query calls)
        if ("knowledge." in text or "llm_query(" in text) and "FINAL" not in text:
            lines = []
            in_code = False
            for line in text.split("\n"):
                if "knowledge." in line or "llm_query(" in line or "subcall(" in line:
                    in_code = True
                    lines.append(line)
                elif in_code and line.strip() and not line.startswith(("#", "/*", "*", "//")):
                    if any(kw in line for kw in ["for ", "if ", "=", "print(", "while ", "def ", "class "]):
                        lines.append(line)

            if lines:
                return "\n".join(lines)

        return None

    def _execute_code(self, code: str) -> Dict[str, Any]:
        """Execute Python code in restricted namespace.

        Returns:
            Dict with 'success', 'observation', and optionally 'error'
        """
        # Reset obs
        self._namespace["obs"] = ""
        self._observation_buffer = []

        # Basic safety checks
        if self.config.safe_execution:
            forbidden = [
                "import ", "__import__", "exec(", "eval(",
                "open(", "os.", "sys.", "subprocess",
                "__builtins__", "__globals__", "__locals__",
                "compile(", "setattr(", "delattr(",
            ]
            for pattern in forbidden:
                if pattern in code:
                    return {
                        "success": False,
                        "error": f"Forbidden operation: {pattern}",
                        "observation": "",
                    }

        try:
            exec(code, {"__builtins__": {}}, self._namespace)

            # Combine observation buffer
            if self._observation_buffer:
                obs = "\n".join(self._observation_buffer)
            else:
                obs = self._namespace.get("obs", "")

            if not obs:
                obs = "(Code executed successfully but no output. Use print() to show results.)"

            return {
                "success": True,
                "observation": str(obs)[:50000],  # Cap observation size
                "error": None,
            }

        except Exception as e:
            error_msg = str(e)
            if self.config.include_traceback:
                tb = traceback.format_exc()
                # Clean up traceback to show relevant parts
                error_msg += "\n" + tb

            return {
                "success": False,
                "observation": "",
                "error": error_msg[:4000],
            }

    def chat(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Simple chat interface that uses RLM for knowledge queries.

        If the query seems to need knowledge base access, uses RLM.
        Otherwise, passes through to LLM directly.
        """
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        # Check if this needs knowledge base access
        knowledge_indicators = [
            "document", "file", "knowledge", "based on",
            "according to", "what does", "find", "search",
            "look up", "check", "in the", "from the",
            "explain", "describe", "how does", "what is",
        ]

        needs_knowledge = any(
            indicator in user_message.lower()
            for indicator in knowledge_indicators
        )

        if needs_knowledge:
            result = self.run(user_message)
            return result.answer
        else:
            return self.llm_call_fn(messages, **kwargs)