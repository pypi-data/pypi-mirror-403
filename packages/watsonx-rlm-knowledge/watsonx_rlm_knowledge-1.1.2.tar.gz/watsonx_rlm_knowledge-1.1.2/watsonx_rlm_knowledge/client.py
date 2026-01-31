"""
KnowledgeClient - Main interface for RLM-based knowledge querying.

This is the primary entry point for users of the library. It provides
a simple interface to query a knowledge base using the RLM pattern
with WatsonX as the LLM backend.

Example:
    # Simple setup from environment
    client = KnowledgeClient.from_directory("/path/to/knowledge")
    answer = client.query("How does authentication work?")

    # With explicit credentials
    client = KnowledgeClient.from_credentials(
        knowledge_root="/path/to/knowledge",
        api_key="your-api-key",
        project_id="your-project-id"
    )
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from watsonx_rlm_knowledge.context import KnowledgeContext, KnowledgeContextConfig
from watsonx_rlm_knowledge.engine import RLMEngine, RLMConfig, RLMResult
from watsonx_rlm_knowledge.preprocessor import DocumentPreprocessor, PreprocessorConfig
from watsonx_rlm_knowledge.exceptions import ConfigurationError, RLMKnowledgeError

logger = logging.getLogger(__name__)


# Default values
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_REGION_URL = "https://us-south.ml.cloud.ibm.com"


@dataclass
class WatsonXConfig:
    """Configuration for WatsonX connection.

    Attributes:
        api_key: IBM Cloud API key
        project_id: WatsonX project ID
        url: WatsonX region URL (e.g., https://us-south.ml.cloud.ibm.com)
        model_id: Model to use (defaults to openai/gpt-oss-120b)
        max_tokens: Maximum tokens for generation
        temperature: Temperature for generation
        top_p: Top-p for generation
        repetition_penalty: Repetition penalty
        reasoning_effort: Reasoning effort for gpt-oss models ("low", "medium", "high")
    """
    api_key: str = ""
    project_id: str = ""
    url: str = DEFAULT_REGION_URL
    model_id: str = DEFAULT_MODEL
    max_tokens: int = 8192
    temperature: float = 0.1
    top_p: float = 1.0
    repetition_penalty: float = 1.0
    reasoning_effort: str = "low"

    @classmethod
    def from_env(cls) -> "WatsonXConfig":
        """Create config from environment variables.

        Environment variables:
            WATSONX_API_KEY or WATSONX_APIKEY: IBM Cloud API key
            WATSONX_PROJECT_ID: WatsonX project ID
            WATSONX_URL or WATSONX_REGION_URL: WatsonX region URL
            WATSONX_MODEL_ID: Model ID
        """
        return cls(
            api_key=os.environ.get("WATSONX_API_KEY", os.environ.get("WATSONX_APIKEY", "")),
            project_id=os.environ.get("WATSONX_PROJECT_ID", ""),
            url=os.environ.get("WATSONX_URL", os.environ.get("WATSONX_REGION_URL", DEFAULT_REGION_URL)),
            model_id=os.environ.get("WATSONX_MODEL_ID", DEFAULT_MODEL),
        )

    def validate(self) -> bool:
        """Check if config has required fields."""
        return bool(self.api_key and self.project_id and self.url)

    def get_generation_params(self) -> Dict[str, Any]:
        """Get generation parameters for ModelInference."""
        params = {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repetition_penalty": self.repetition_penalty,
        }
        if self.reasoning_effort:
            params["reasoning_effort"] = self.reasoning_effort
        return params


class KnowledgeClient:
    """Main client for RLM-based knowledge base queries.

    This client provides a simple interface to:
    1. Index documents in a directory (including PDF, DOCX, etc.)
    2. Query the knowledge base using natural language
    3. Get answers synthesized from relevant documents

    The client uses the RLM (Recursive Language Model) pattern where
    the LLM writes Python code to explore the knowledge base rather
    than having all content in context at once.

    Example:
        # Quick setup from environment variables
        client = KnowledgeClient.from_directory("/path/to/docs")

        # Query the knowledge base
        answer = client.query("What are the authentication methods?")
        print(answer)

        # Get detailed result with metadata
        result = client.query_detailed("Explain the API endpoints")
        print(f"Answer: {result.answer}")
        print(f"Iterations: {result.iterations}")
        print(f"Time: {result.total_time}s")

    Environment Variables:
        WATSONX_API_KEY: IBM Cloud API key
        WATSONX_PROJECT_ID: WatsonX project ID
        WATSONX_URL: Optional, defaults to us-south
        WATSONX_MODEL_ID: Optional, defaults to openai/gpt-oss-120b
    """

    def __init__(
        self,
        knowledge: KnowledgeContext,
        watsonx_config: WatsonXConfig,
        engine_config: Optional[RLMConfig] = None,
    ):
        """Initialize client with pre-configured components.

        Most users should use the factory methods instead:
        - KnowledgeClient.from_directory()
        - KnowledgeClient.from_credentials()
        - KnowledgeClient.from_env()

        Args:
            knowledge: Configured knowledge context
            watsonx_config: WatsonX configuration
            engine_config: Optional RLM engine configuration
        """
        self.knowledge = knowledge
        self.watsonx_config = watsonx_config
        self.engine_config = engine_config or RLMConfig()

        # Initialize WatsonX model using native ibm-watsonx-ai
        self._model = self._create_model()

        # Create the engine
        self._engine = RLMEngine(
            knowledge=knowledge,
            llm_call_fn=self._llm_call,
            config=self.engine_config,
        )

        logger.info(f"Initialized KnowledgeClient for {knowledge.root}")

    def _create_model(self):
        """Create the IBM WatsonX ModelInference instance."""
        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference
        except ImportError:
            raise ImportError(
                "ibm-watsonx-ai package not found. Install with: pip install ibm-watsonx-ai"
            )

        credentials = Credentials(
            url=self.watsonx_config.url,
            api_key=self.watsonx_config.api_key,
        )

        model = ModelInference(
            model_id=self.watsonx_config.model_id,
            credentials=credentials,
            project_id=self.watsonx_config.project_id,
            params=self.watsonx_config.get_generation_params(),
        )

        logger.info(f"Created ModelInference for model: {self.watsonx_config.model_id}")
        return model

    @classmethod
    def from_directory(
        cls,
        knowledge_root: str,
        preprocess: bool = True,
        watsonx_config: Optional[WatsonXConfig] = None,
        context_config: Optional[KnowledgeContextConfig] = None,
        engine_config: Optional[RLMConfig] = None,
    ) -> "KnowledgeClient":
        """Create client from a knowledge directory.

        This is the recommended way to create a client. It:
        1. Loads WatsonX credentials from environment
        2. Sets up the knowledge context
        3. Optionally preprocesses documents

        Args:
            knowledge_root: Path to directory containing knowledge documents
            preprocess: If True, preprocess documents on init (recommended)
            watsonx_config: Optional WatsonX config (loads from env if not provided)
            context_config: Optional knowledge context configuration
            engine_config: Optional RLM engine configuration

        Returns:
            Configured KnowledgeClient

        Raises:
            ConfigurationError: If credentials not found or invalid

        Example:
            # Basic usage (credentials from environment)
            client = KnowledgeClient.from_directory("/path/to/docs")

            # With custom config
            client = KnowledgeClient.from_directory(
                "/path/to/docs",
                engine_config=RLMConfig(max_iterations=20)
            )
        """
        # Load WatsonX config from env if not provided
        if watsonx_config is None:
            watsonx_config = WatsonXConfig.from_env()

        if not watsonx_config.validate():
            raise ConfigurationError(
                "WatsonX credentials not found. Set environment variables:\n"
                "  WATSONX_API_KEY\n"
                "  WATSONX_PROJECT_ID\n"
                "Or provide a WatsonXConfig object."
            )

        # Create knowledge context
        knowledge = KnowledgeContext(
            root=knowledge_root,
            config=context_config,
        )

        # Preprocess documents if requested
        if preprocess:
            logger.info("Preprocessing documents...")
            count = knowledge.preprocess()
            logger.info(f"Preprocessed {count} documents")

        return cls(
            knowledge=knowledge,
            watsonx_config=watsonx_config,
            engine_config=engine_config,
        )

    @classmethod
    def from_credentials(
        cls,
        knowledge_root: str,
        api_key: str,
        project_id: str,
        url: str = DEFAULT_REGION_URL,
        model_id: str = DEFAULT_MODEL,
        preprocess: bool = True,
        context_config: Optional[KnowledgeContextConfig] = None,
        engine_config: Optional[RLMConfig] = None,
    ) -> "KnowledgeClient":
        """Create client with explicit credentials.

        Args:
            knowledge_root: Path to knowledge directory
            api_key: IBM Cloud API key
            project_id: WatsonX project ID
            url: WatsonX region URL
            model_id: Model ID to use
            preprocess: If True, preprocess documents on init
            context_config: Optional knowledge context configuration
            engine_config: Optional RLM engine configuration

        Returns:
            Configured KnowledgeClient

        Example:
            client = KnowledgeClient.from_credentials(
                knowledge_root="/path/to/docs",
                api_key="your-api-key",
                project_id="your-project-id"
            )
        """
        watsonx_config = WatsonXConfig(
            api_key=api_key,
            project_id=project_id,
            url=url,
            model_id=model_id,
        )

        return cls.from_directory(
            knowledge_root=knowledge_root,
            preprocess=preprocess,
            watsonx_config=watsonx_config,
            context_config=context_config,
            engine_config=engine_config,
        )

    @classmethod
    def from_env(
        cls,
        knowledge_root: Optional[str] = None,
        preprocess: bool = True,
        context_config: Optional[KnowledgeContextConfig] = None,
        engine_config: Optional[RLMConfig] = None,
    ) -> "KnowledgeClient":
        """Create client from environment variables.

        Environment Variables:
            WATSONX_API_KEY: IBM Cloud API key
            WATSONX_PROJECT_ID: WatsonX project ID
            WATSONX_URL: Optional region URL
            WATSONX_MODEL_ID: Optional model ID
            RLM_KNOWLEDGE_ROOT: Optional knowledge directory

        Args:
            knowledge_root: Path to knowledge directory (or from RLM_KNOWLEDGE_ROOT)
            preprocess: If True, preprocess documents
            context_config: Optional context configuration
            engine_config: Optional engine configuration

        Returns:
            Configured KnowledgeClient
        """
        if knowledge_root is None:
            knowledge_root = os.environ.get("RLM_KNOWLEDGE_ROOT")

        if not knowledge_root:
            raise ConfigurationError(
                "Knowledge root not specified. Provide knowledge_root argument "
                "or set RLM_KNOWLEDGE_ROOT environment variable."
            )

        return cls.from_directory(
            knowledge_root=knowledge_root,
            preprocess=preprocess,
            context_config=context_config,
            engine_config=engine_config,
        )

    def _llm_call(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Internal LLM call function for the RLM engine.

        Uses the native ibm-watsonx-ai ModelInference.chat() method.
        """
        # Format messages for the API (only role and content)
        formatted_messages = [
            {"role": msg["role"], "content": msg.get("content", "") or ""}
            for msg in messages
        ]

        response = self._model.chat(messages=formatted_messages)

        # Handle response format from native SDK
        if isinstance(response, dict) and "choices" in response:
            return response["choices"][0].get("message", {}).get("content", "")
        elif isinstance(response, str):
            return response

        return str(response) if response else ""

    def query(
        self,
        question: str,
        additional_context: str = "",
    ) -> str:
        """Query the knowledge base with a question.

        This is the simplest interface - ask a question, get an answer.

        Args:
            question: Natural language question about the knowledge base
            additional_context: Optional additional context to include

        Returns:
            Answer synthesized from relevant documents

        Example:
            answer = client.query("What authentication methods are supported?")
            print(answer)
        """
        result = self._engine.run(
            query=question,
            additional_context=additional_context,
        )
        return result.answer

    def query_detailed(
        self,
        question: str,
        additional_context: str = "",
    ) -> RLMResult:
        """Query the knowledge base and get detailed results.

        This returns the full RLMResult with metadata about the
        exploration process.

        Args:
            question: Natural language question
            additional_context: Optional additional context

        Returns:
            RLMResult with answer, iterations, time, observations, etc.

        Example:
            result = client.query_detailed("Explain the database schema")
            print(f"Answer: {result.answer}")
            print(f"Iterations: {result.iterations}")
            print(f"Time: {result.total_time:.2f}s")
            print(f"Success: {result.success}")
        """
        return self._engine.run(
            query=question,
            additional_context=additional_context,
        )

    def chat(
        self,
        messages: List[Dict[str, Any]],
        use_knowledge: bool = True,
        **kwargs
    ) -> str:
        """Chat interface with optional knowledge base access.

        Args:
            messages: List of messages in OpenAI format
            use_knowledge: If True, use RLM to access knowledge base
            **kwargs: Additional parameters for the LLM

        Returns:
            Assistant response

        Example:
            response = client.chat([
                {"role": "user", "content": "What does the config file do?"}
            ])
        """
        # Extract user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if use_knowledge and user_message:
            # Use RLM engine
            return self.query(user_message)
        else:
            # Direct LLM call
            return self._llm_call(messages, **kwargs)

    def list_documents(self, pattern: Optional[str] = None) -> List[str]:
        """List all documents in the knowledge base.

        Args:
            pattern: Optional glob pattern to filter (e.g., "*.pdf")

        Returns:
            List of document paths (relative to knowledge root)
        """
        docs = self.knowledge.list_documents(pattern=pattern)
        return [d.relative_path for d in docs]

    def search(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search the knowledge base for a term.

        Args:
            query: Search term
            max_results: Maximum results to return

        Returns:
            List of matches with path, line number, and text
        """
        matches = self.knowledge.search(query, max_matches=max_results)
        return [
            {
                "path": m.path,
                "line": m.line_number,
                "text": m.line_text,
            }
            for m in matches
        ]

    def read_document(self, path: str, max_bytes: int = 50000) -> str:
        """Read content from a document.

        Args:
            path: Path to document (relative to knowledge root)
            max_bytes: Maximum bytes to read

        Returns:
            Document content as text
        """
        return self.knowledge.read_slice(path, 0, max_bytes)

    def preprocess(self, force: bool = False) -> int:
        """Preprocess/reprocess documents in the knowledge base.

        Args:
            force: If True, reprocess all documents regardless of cache

        Returns:
            Number of documents processed
        """
        return self.knowledge.preprocess(force=force)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base.

        Returns:
            Dict with document counts, sizes, etc.
        """
        docs = self.knowledge.list_documents()

        total_size = sum(d.size_bytes for d in docs)
        text_size = sum(d.text_size_bytes for d in docs)

        formats = {}
        for d in docs:
            fmt = d.format
            formats[fmt] = formats.get(fmt, 0) + 1

        return {
            "document_count": len(docs),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "text_size_bytes": text_size,
            "text_size_mb": round(text_size / (1024 * 1024), 2),
            "formats": formats,
            "knowledge_root": str(self.knowledge.root),
        }

    def cleanup(self):
        """Clean up resources."""
        # Native SDK handles its own cleanup
        self._model = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    def __repr__(self) -> str:
        return f"KnowledgeClient(root='{self.knowledge.root}')"