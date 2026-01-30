"""RAG codebase search functionality for AccuralAI documentation."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp

from .chunking import smart_chunk
from .embeddings import EmbeddingService, cosine_similarity

LOGGER = logging.getLogger("accuralai.discord.test")


class CodebaseIndex:
    """Index for searching AccuralAI codebase documentation."""

    def __init__(
        self,
        root_path: str | Path,
        use_embeddings: bool = True,
        embedding_api_key: Optional[str] = None,
        embedding_model: str = "gemini-embedding-001",
    ):
        """
        Initialize codebase index.

        Args:
            root_path: Root path to AccuralAI repository
            use_embeddings: Whether to use embeddings for semantic search (default: True)
            embedding_api_key: API key for embeddings (uses GOOGLE_GENAI_API_KEY if None)
            embedding_model: Embedding model to use (default: gemini-embedding-001)
        """
        self.root_path = Path(root_path)
        self.index: List[Dict[str, Any]] = []
        self._initialized = False
        self.use_embeddings = use_embeddings
        self.embedding_service: Optional[EmbeddingService] = None
        self.chunks: List[Dict[str, Any]] = []  # Store chunks with embeddings
        self._embeddings_initialized = False

        # Initialize embedding service if requested
        if self.use_embeddings:
            try:
                self.embedding_service = EmbeddingService(
                    api_key=embedding_api_key,
                    model=embedding_model,
                )
                LOGGER.info("Embedding service initialized for RAG search")
            except Exception as e:
                LOGGER.warning(f"Failed to initialize embedding service: {e}. Falling back to keyword search.")
                self.use_embeddings = False

    async def initialize(self) -> None:
        """Initialize index by scanning codebase."""
        if self._initialized:
            return

        LOGGER.info(f"Initializing codebase index from {self.root_path}")

        # Files to index
        patterns = [
            "**/*.md",
            "**/*.rst",
            "**/*.py",
            "**/README*",
            "**/LICENSE",
            "**/*.toml",
            "**/*.txt",
        ]

        # Directories to include
        include_dirs = [
            "packages",
            "plan",
            "docs",
            "README.md",
            "AGENTS.md",
            "config.toml",
            "accuralai/pyproject.toml",
            # Include docs from packages (like accuralai-discord/docs)
            "packages/*/docs",
        ]

        # Directories to exclude
        exclude_dirs = {
            "__pycache__",
            ".git",
            "node_modules",
            ".pytest_cache",
            "venv",
            "_build",
            "dist",
            ".venv",
        }

        indexed_files = []

        for include_dir in include_dirs:
            # Handle wildcard patterns (e.g., "packages/*/docs")
            if "*" in include_dir:
                # Find all matching directories
                base_pattern, wildcard_part = include_dir.split("/*/", 1)
                base_path = self.root_path / base_pattern
                if base_path.exists() and base_path.is_dir():
                    # Find all subdirectories matching the pattern
                    for subdir in base_path.iterdir():
                        if subdir.is_dir():
                            wildcard_path = subdir / wildcard_part
                            if wildcard_path.exists():
                                # Index this directory
                                for pattern in patterns:
                                    for file_path in wildcard_path.rglob(pattern):
                                        # Skip excluded directories
                                        if any(excluded in file_path.parts for excluded in exclude_dirs):
                                            continue

                                        # Skip if too large (>1MB)
                                        try:
                                            if file_path.stat().st_size > 1_000_000:
                                                continue
                                        except OSError:
                                            continue

                                        try:
                                            content = await self._read_file_async(file_path)
                                            if content:
                                                indexed_files.append({
                                                    "path": str(file_path.relative_to(self.root_path)),
                                                    "content": content,
                                                    "type": self._get_file_type(file_path),
                                                })
                                        except Exception as e:
                                            LOGGER.debug(f"Failed to index {file_path}: {e}")
                continue

            target_path = self.root_path / include_dir
            if not target_path.exists():
                continue

            if target_path.is_file():
                # Index single file
                try:
                    content = await self._read_file_async(target_path)
                    if content:
                        indexed_files.append({
                            "path": str(target_path.relative_to(self.root_path)),
                            "content": content,
                            "type": self._get_file_type(target_path),
                        })
                except Exception as e:
                    LOGGER.warning(f"Failed to index {target_path}: {e}")
            else:
                # Index directory
                for pattern in patterns:
                    for file_path in target_path.rglob(pattern):
                        # Skip excluded directories
                        if any(excluded in file_path.parts for excluded in exclude_dirs):
                            continue

                        # Skip if too large (>1MB)
                        try:
                            if file_path.stat().st_size > 1_000_000:
                                continue
                        except OSError:
                            continue

                        try:
                            content = await self._read_file_async(file_path)
                            if content:
                                indexed_files.append({
                                    "path": str(file_path.relative_to(self.root_path)),
                                    "content": content,
                                    "type": self._get_file_type(file_path),
                                })
                        except Exception as e:
                            LOGGER.debug(f"Failed to index {file_path}: {e}")

        self.index = indexed_files
        self._initialized = True
        LOGGER.info(f"Indexed {len(self.index)} files")

        # Generate embeddings for chunks if using RAG
        if self.use_embeddings and self.embedding_service:
            await self._generate_embeddings()

    @staticmethod
    async def _read_file_async(file_path: Path) -> Optional[str]:
        """Read file asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, file_path.read_text, "utf-8")
        except UnicodeDecodeError:
            # Skip binary files
            return None
        except Exception as e:
            LOGGER.debug(f"Error reading {file_path}: {e}")
            return None

    @staticmethod
    def _get_file_type(file_path: Path) -> str:
        """Get file type based on extension."""
        suffix = file_path.suffix.lower()
        if suffix == ".md":
            return "markdown"
        elif suffix == ".rst":
            return "restructuredtext"
        elif suffix == ".py":
            return "python"
        elif suffix in (".toml", ".cfg"):
            return "config"
        elif suffix == ".txt":
            return "text"
        else:
            return "other"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        file_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search indexed codebase using embeddings (RAG) or keyword search.

        Args:
            query: Search query
            max_results: Maximum results to return
            file_types: Filter by file types (None = all)

        Returns:
            List of matching results with path, content snippets, and relevance scores
        """
        if not self._initialized:
            return []

        # Use embeddings if available, otherwise fall back to keyword search
        if self.use_embeddings and self._embeddings_initialized and self.embedding_service:
            return await self._search_with_embeddings(query, max_results, file_types)
        else:
            return self._search_keyword(query, max_results, file_types)

    async def _search_with_embeddings(
        self,
        query: str,
        max_results: int = 5,
        file_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search using embeddings (semantic search)."""
        if not self.embedding_service:
            return self._search_keyword(query, max_results, file_types)

        # Generate embedding for query
        query_embedding = await self.embedding_service.embed_text(query)

        # Calculate similarity scores for all chunks
        results = []
        for chunk in self.chunks:
            if file_types and chunk["type"] not in file_types:
                continue

            embedding = chunk.get("embedding")
            if not embedding:
                continue

            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, embedding)

            # Add to results
            # Use more content for better context
            chunk_content = chunk["content"]
            results.append({
                "path": chunk["path"],
                "type": chunk["type"],
                "snippet": chunk_content[:800],  # Increased snippet size for better context
                "score": similarity,  # Use similarity as score
                "full_content": chunk_content[:3000],  # Increased for better context
                "chunk_index": chunk.get("chunk_index", 0),
            })

        # Sort by similarity (score) descending
        results.sort(key=lambda x: x["score"], reverse=True)

        # Allow multiple chunks from same file if they're highly relevant (score > 0.7)
        # Otherwise deduplicate by path, keeping highest scoring chunk per file
        high_relevance_threshold = 0.7
        seen_paths: Dict[str, list[Dict[str, Any]]] = {}
        for result in results:
            path = result["path"]
            score = result["score"]
            
            if path not in seen_paths:
                seen_paths[path] = []
            
            # If score is very high, allow multiple chunks from same file
            if score > high_relevance_threshold:
                seen_paths[path].append(result)
            else:
                # For lower scores, keep only the best chunk
                if not seen_paths[path] or score > seen_paths[path][0]["score"]:
                    seen_paths[path] = [result]

        # Flatten and sort
        final_results = []
        for chunks in seen_paths.values():
            # Sort chunks from same file by score and take top 2
            chunks.sort(key=lambda x: x["score"], reverse=True)
            final_results.extend(chunks[:2])
        
        # Sort all results by score and return top results
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:max_results]

    def _search_keyword(
        self,
        query: str,
        max_results: int = 5,
        file_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fallback keyword-based search."""
        query_lower = query.lower()
        query_terms = query_lower.split()

        results = []

        for doc in self.index:
            if file_types and doc["type"] not in file_types:
                continue

            content = doc["content"].lower()
            path = doc["path"].lower()

            # Calculate relevance score
            score = 0

            # Exact phrase match
            if query_lower in content:
                score += 10

            # Term frequency
            term_matches = sum(content.count(term) for term in query_terms)
            score += term_matches

            # Path match (higher weight)
            if any(term in path for term in query_terms):
                score += 5

            # Title/header matches (lines starting with #)
            for line in doc["content"].split("\n")[:20]:  # First 20 lines
                if line.strip().startswith("#"):
                    if any(term in line.lower() for term in query_terms):
                        score += 3

            if score > 0:
                # Extract relevant snippet
                snippet = self._extract_snippet(doc["content"], query_lower)
                results.append({
                    "path": doc["path"],
                    "type": doc["type"],
                    "snippet": snippet,
                    "score": score,
                    "full_content": doc["content"][:2000],  # Limit full content
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:max_results]

    async def _generate_embeddings(self) -> None:
        """Generate embeddings for all indexed chunks."""
        if not self.embedding_service:
            return

        LOGGER.info("Generating embeddings for codebase chunks...")
        self.chunks = []

        for doc in self.index:
            file_type = doc.get("type", "other")
            content = doc.get("content", "")
            path = doc.get("path", "")

            # Extract package name from path for context
            package_name = ""
            path_parts = path.replace("\\", "/").split("/")
            if "packages" in path_parts:
                packages_idx = path_parts.index("packages")
                if packages_idx + 1 < len(path_parts):
                    package_name = path_parts[packages_idx + 1]

            # Chunk the content based on file type (run in thread pool to avoid blocking event loop)
            doc_chunks = await asyncio.to_thread(
                smart_chunk,
                text=content,
                file_type=file_type,
                chunk_size=1200,  # Slightly larger chunks for better context
                chunk_overlap=250,  # More overlap for continuity
            )
            
            # Yield control to event loop periodically to allow Discord heartbeats
            await asyncio.sleep(0)

            # Create chunk entries with package context
            for chunk_idx, chunk_text in enumerate(doc_chunks):
                # Prepend package context to chunk for better semantic understanding
                chunk_with_context = chunk_text
                if package_name:
                    chunk_with_context = f"[Package: {package_name}]\n{chunk_text}"
                
                self.chunks.append({
                    "path": path,
                    "type": file_type,
                    "package": package_name,
                    "chunk_index": chunk_idx,
                    "content": chunk_with_context,  # Include package context
                    "embedding": None,  # Will be populated
                })

        LOGGER.info(f"Created {len(self.chunks)} chunks, generating embeddings...")

        # Generate embeddings in batches
        chunk_texts = [chunk["content"] for chunk in self.chunks]
        embeddings = await self.embedding_service.embed_batch(chunk_texts, batch_size=50)

        # Store embeddings
        for chunk, embedding in zip(self.chunks, embeddings):
            chunk["embedding"] = embedding

        self._embeddings_initialized = True
        LOGGER.info(f"Generated embeddings for {len(self.chunks)} chunks")

    @staticmethod
    def _extract_snippet(content: str, query: str, context_lines: int = 3) -> str:
        """Extract relevant snippet around query match."""
        content_lower = content.lower()
        query_lower = query.lower()

        # Find first match
        idx = content_lower.find(query_lower)
        if idx == -1:
            # No exact match, return first few lines
            return "\n".join(content.split("\n")[:5])

        # Extract context around match
        lines = content.split("\n")
        line_idx = content[:idx].count("\n")

        start = max(0, line_idx - context_lines)
        end = min(len(lines), line_idx + context_lines + 1)

        snippet_lines = lines[start:end]
        snippet = "\n".join(snippet_lines)

        # Highlight query if possible
        if len(snippet) < 500:
            return snippet
        return snippet[:500] + "..."


class WebCodebaseSearch:
    """Search both web and local codebase."""

    def __init__(
        self,
        codebase_root: str | Path,
        use_embeddings: bool = True,
        embedding_api_key: Optional[str] = None,
        embedding_model: str = "gemini-embedding-001",
    ):
        """
        Initialize web and codebase search.

        Args:
            codebase_root: Root path to AccuralAI repository
            use_embeddings: Whether to use embeddings for semantic search (default: True)
            embedding_api_key: API key for embeddings (uses GOOGLE_GENAI_API_KEY if None)
            embedding_model: Embedding model to use (default: gemini-embedding-001)
        """
        self.index = CodebaseIndex(
            codebase_root,
            use_embeddings=use_embeddings,
            embedding_api_key=embedding_api_key,
            embedding_model=embedding_model,
        )

    async def initialize(self) -> None:
        """Initialize codebase index."""
        await self.index.initialize()

    async def search_codebase(
        self,
        query: str,
        max_results: int = 5,
        file_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search local codebase.

        Args:
            query: Search query
            max_results: Maximum results
            file_types: Filter by file types

        Returns:
            Search results
        """
        if not self.index._initialized:
            await self.index.initialize()

        return await self.index.search(query, max_results=max_results, file_types=file_types)

    async def search_web(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search web using Google's grounding with Google Search.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            Web search results
        """
        try:
            from .web_search import search_web as google_search

            results = await google_search(query, max_results=max_results)
            return results
        except Exception as e:
            LOGGER.error(f"Web search error: {e}", exc_info=True)
            return [{"error": f"Web search failed: {str(e)}"}]

    async def search_all(
        self,
        query: str,
        codebase_max: int = 3,
        web_max: int = 3,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search both codebase and web.

        Args:
            query: Search query
            codebase_max: Max codebase results
            web_max: Max web results

        Returns:
            Dict with 'codebase' and 'web' results
        """
        codebase_results, web_results = await asyncio.gather(
            self.search_codebase(query, max_results=codebase_max),
            self.search_web(query, max_results=web_max),
        )

        return {
            "codebase": codebase_results,
            "web": web_results,
        }


def format_codebase_results(results: List[Dict[str, Any]]) -> str:
    """
    Format codebase search results for Discord.

    Args:
        results: Search results

    Returns:
        Formatted string
    """
    if not results:
        return "No results found in codebase."

    lines = ["**📚 Codebase Search Results:**\n"]

    for i, result in enumerate(results, 1):
        path = result.get("path", "unknown")
        snippet = result.get("snippet", "")
        file_type = result.get("type", "unknown")
        score = result.get("score", 0)

        lines.append(f"**{i}. `{path}`** ({file_type})")
        if snippet:
            # Truncate snippet
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            lines.append(f"```{file_type}\n{snippet}\n```")
        lines.append("")

    return "\n".join(lines)


def format_combined_results(
    codebase_results: List[Dict[str, Any]],
    web_results: List[Dict[str, Any]],
) -> str:
    """
    Format combined codebase and web results.

    Args:
        codebase_results: Codebase search results
        web_results: Web search results

    Returns:
        Formatted string
    """
    parts = []

    if codebase_results:
        parts.append(format_codebase_results(codebase_results))

    if web_results and not web_results[0].get("error"):
        from .web_search import format_search_results

        parts.append("**🌐 Web Search Results:**\n")
        parts.append(format_search_results(web_results))

    if not parts:
        return "No results found."

    return "\n\n".join(parts)

