"""LLM-based code review module."""

import os
import re
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import urllib.request

import litellm
from litellm import completion
from litellm import exceptions as litellm_exceptions

from .git_diff import BranchDiff, FileDiff


@dataclass
class FileReview:
    """Review result for a single file."""
    path: str
    issues: list[str]
    suggestions: list[str]
    summary: str


@dataclass
class CodeReview:
    """Complete code review result."""
    source_branch: str
    target_branch: str
    file_reviews: list[FileReview]
    overall_summary: str
    
    def to_markdown(self) -> str:
        """Convert review to markdown format."""
        lines = [
            f"# Code Review: {self.source_branch} → {self.target_branch}",
            "",
            "## Files Reviewed",
        ]

        for review in self.file_reviews:
            lines.append(f"- `{review.path}` (issues: {len(review.issues)}, suggestions: {len(review.suggestions)})")

        lines += [
            "",
            "## Overall Summary (all files)",
            self.overall_summary,
            "",
            "---",
            ""
        ]
        
        for review in self.file_reviews:
            lines.append(f"## `{review.path}`")
            lines.append("")
            lines.append(review.summary)
            lines.append("")

            lines.append("### Issues")
            if review.issues:
                for issue in review.issues:
                    lines.append(f"- {issue}")
            else:
                lines.append("- None")
            lines.append("")

            lines.append("### Suggestions")
            if review.suggestions:
                for suggestion in review.suggestions:
                    lines.append(f"- {suggestion}")
            else:
                lines.append("- None")
            lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)


class LLMCallError(RuntimeError):
    def __init__(self, message: str, *, model: str, api_base: Optional[str]):
        super().__init__(message)
        self.model = model
        self.api_base = api_base


SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the provided git diff and provide a thorough code review.

Focus on:
1. **Bugs & Errors**: Logic errors, potential runtime errors, edge cases
2. **Security**: Vulnerabilities, insecure patterns, exposed secrets
3. **Performance**: Inefficient code, unnecessary operations, memory leaks
4. **Code Quality**: Readability, maintainability, naming conventions
5. **Best Practices**: Language idioms, design patterns, SOLID principles
6. **Code Smells**: Structural or stylistic indicators of poor design that may lead to bugs or technical debt

Be specific and actionable. When referencing code, cite the first line number using "Line:X" format (e.g., Line:107).
Keep your review concise but thorough."""

FILE_REVIEW_PROMPT = """Review this file diff:

**File**: {path}
**Change Type**: {change_type}

```diff
{diff_content}
```

IMPORTANT: Each line is prefixed with "Line:X" showing the actual file line number. Example: "Line:42 +code" means line 42 is an addition. Deleted lines have no line number. You MUST cite a line number for EVERY issue and suggestion - no exceptions.

Provide your review in this exact format:

SUMMARY: [One paragraph summary of the changes and their quality]

ISSUES:
- Line:X: [Issue description]
- Line:Y: [Issue description]
(or "None" if no issues)

SUGGESTIONS:
- Line:X: [Suggestion description]
- Line:Y: [Suggestion description]
(or "None" if no suggestions)

EVERY issue and suggestion MUST start with "Line:X:" where X is the line number. Do not include general comments without line numbers."""

OVERALL_SUMMARY_PROMPT = """Based on reviewing all the file changes in this pull request from '{source}' to '{target}', provide a brief overall summary (2-3 paragraphs) covering:

1. What the changes accomplish
2. Overall code quality assessment
3. Key recommendations before merging

Do NOT include line number references (like "Line:X") in this summary - those details are already in the per-file reviews. You may reference file names when relevant, but focus on the high-level narrative.

Files changed:
{files_summary}"""


class CodeReviewer:
    """LLM-based code reviewer using litellm."""
    
    def __init__(
        self,
        model: str = "ollama/llama3.2",
        api_base: Optional[str] = None,
        trace_path: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3
    ):
        self.model = model
        self.api_base = api_base
        self.trace_path = trace_path
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._ollama_preflight_done = False
        
        # Clear trace file at start of new review session
        if trace_path:
            trace_file = Path(trace_path)
            trace_file.parent.mkdir(parents=True, exist_ok=True)
            trace_file.write_text("")  # Overwrite with empty file
        
        # Configure litellm
        litellm.drop_params = True
        litellm.set_verbose = False
        litellm.print_verbose = False
        litellm.suppress_debug_info = True
        if api_base:
            litellm.api_base = api_base

    def _write_trace(self, record: dict) -> None:
        if not self.trace_path:
            return
        trace_path = Path(self.trace_path)
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        with trace_path.open("a", encoding="utf-8") as f:
            event = record.get("event", "")
            ts = record.get("ts", time.time())
            ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
            call_id = record.get("call_id")

            f.write("\n" + ("=" * 80) + "\n")
            if call_id is not None:
                f.write(f"LLM TRACE - {event.upper()} @ {ts_str} (call_id={call_id})\n")
            else:
                f.write(f"LLM TRACE - {event.upper()} @ {ts_str}\n")
            f.write(("=" * 80) + "\n")
            f.write(f"MODEL: {record.get('model')}\n")
            f.write(f"API_BASE: {record.get('api_base')}\n")
            f.write(f"TIMEOUT: {record.get('timeout')}\n")
            f.write(f"MAX_TOKENS: {record.get('max_tokens')}\n")

            litellm_kwargs = record.get("litellm_kwargs")
            if litellm_kwargs is not None:
                f.write("\n-- LITELLM KWARGS --\n")
                for k, v in litellm_kwargs.items():
                    f.write(f"{k}: {v}\n")

            messages_full = record.get("messages_full")
            if messages_full is not None:
                f.write("\n-- MESSAGES (FULL) --\n")
                for i, m in enumerate(messages_full, start=1):
                    role = m.get("role")
                    content = m.get("content", "")
                    content_str = content if isinstance(content, str) else str(content)
                    f.write("\n" + ("-" * 80) + "\n")
                    f.write(f"MESSAGE {i} (role={role})\n")
                    f.write(("-" * 80) + "\n")
                    f.write(content_str)
                    if not content_str.endswith("\n"):
                        f.write("\n")

            if event == "response":
                f.write("\n-- RESPONSE (FULL) --\n")
                f.write(record.get("response", ""))
                if not str(record.get("response", "")).endswith("\n"):
                    f.write("\n")
                f.write(f"\nRESPONSE_LEN: {record.get('response_len')}\n")
                f.write(f"ELAPSED_SEC: {record.get('elapsed_sec')}\n")

            if event == "error":
                f.write("\n-- ERROR --\n")
                f.write(f"ERROR_TYPE: {record.get('error_type')}\n")
                f.write(f"ERROR: {record.get('error')}\n")
                proxy_env = record.get("proxy_env")
                if proxy_env is not None:
                    f.write("\n-- PROXY ENV --\n")
                    for k, v in proxy_env.items():
                        f.write(f"{k}: {v}\n")

    def _messages_summary(self, messages: list[dict]) -> dict:
        total_chars = 0
        summarized = []
        for m in messages:
            content = m.get("content", "")
            content_str = content if isinstance(content, str) else str(content)
            total_chars += len(content_str)
            summarized.append({
                "role": m.get("role"),
                "content_len": len(content_str),
                "content_preview": content_str[:500],
            })
        return {"total_content_chars": total_chars, "messages": summarized}

    def _ollama_preflight(self) -> Optional[str]:
        if not self.api_base:
            return "api_base is not set"
        base = self.api_base.rstrip('/')
        url = f"{base}/api/tags"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if getattr(resp, "status", 200) >= 400:
                    return f"HTTP {resp.status}"
            return None
        except Exception as e:
            return repr(e)
    
    def _call_llm(self, messages: list[dict]) -> str:
        """Make a call to the LLM."""
        call_id = int(time.time() * 1000)
        trace_base = {
            "ts": time.time(),
            "call_id": call_id,
            "model": self.model,
            "api_base": self.api_base,
            "timeout": self.timeout,
            "max_tokens": self.max_tokens,
            "messages": self._messages_summary(messages),
        }

        if self.model.startswith("ollama/") and not self._ollama_preflight_done:
            self._ollama_preflight_done = True
            preflight_error = self._ollama_preflight()
            if preflight_error:
                proxy_info = {
                    "HTTP_PROXY": os.getenv("HTTP_PROXY") or os.getenv("http_proxy"),
                    "HTTPS_PROXY": os.getenv("HTTPS_PROXY") or os.getenv("https_proxy"),
                    "ALL_PROXY": os.getenv("ALL_PROXY") or os.getenv("all_proxy"),
                    "NO_PROXY": os.getenv("NO_PROXY") or os.getenv("no_proxy"),
                }
                raise LLMCallError(
                    f"Ollama preflight failed for {self.api_base or '(default)'} ({preflight_error}). "
                    f"Proxy env: {proxy_info}",
                    model=self.model,
                    api_base=self.api_base,
                )

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.timeout is not None:
            kwargs["timeout"] = self.timeout
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens

        self._write_trace({
            **trace_base,
            "event": "request",
            "litellm_kwargs": {k: v for k, v in kwargs.items() if k != "messages"},
            "messages_full": messages,
        })

        try:
            start = time.time()
            response = completion(**kwargs)
            elapsed = time.time() - start
            content = response.choices[0].message.content
            self._write_trace({
                **trace_base,
                "event": "response",
                "elapsed_sec": elapsed,
                "response": content or "",
                "response_len": len(content or ""),
            })
            return content
        except litellm_exceptions.APIConnectionError as e:
            api_base = self.api_base or "(default)"
            if self.model.startswith("ollama/"):
                proxy_info = {
                    "HTTP_PROXY": os.getenv("HTTP_PROXY") or os.getenv("http_proxy"),
                    "HTTPS_PROXY": os.getenv("HTTPS_PROXY") or os.getenv("https_proxy"),
                    "ALL_PROXY": os.getenv("ALL_PROXY") or os.getenv("all_proxy"),
                    "NO_PROXY": os.getenv("NO_PROXY") or os.getenv("no_proxy"),
                }
                self._write_trace({
                    **trace_base,
                    "event": "error",
                    "error_type": "APIConnectionError",
                    "error": repr(e),
                    "proxy_env": proxy_info,
                })
                raise LLMCallError(
                    f"Cannot connect to Ollama at {api_base}. Start Ollama or set --api-base/OLLAMA_API_BASE. "
                    f"Underlying error: {repr(e)}. Proxy env: {proxy_info}",
                    model=self.model,
                    api_base=self.api_base,
                ) from e
            self._write_trace({
                **trace_base,
                "event": "error",
                "error_type": "APIConnectionError",
                "error": repr(e),
            })
            raise LLMCallError(
                f"Cannot connect to LLM provider (model={self.model}, api_base={api_base}).",
                model=self.model,
                api_base=self.api_base,
            ) from e
        except litellm_exceptions.AuthenticationError as e:
            self._write_trace({
                **trace_base,
                "event": "error",
                "error_type": "AuthenticationError",
                "error": repr(e),
            })
            raise LLMCallError(
                f"Authentication failed for model={self.model}. Check your API key environment variables.",
                model=self.model,
                api_base=self.api_base,
            ) from e
        except litellm_exceptions.RateLimitError as e:
            self._write_trace({
                **trace_base,
                "event": "error",
                "error_type": "RateLimitError",
                "error": repr(e),
            })
            raise LLMCallError(
                f"Rate limit hit for model={self.model}. Try again later or use a different model/provider.",
                model=self.model,
                api_base=self.api_base,
            ) from e
        except litellm_exceptions.BadRequestError as e:
            self._write_trace({
                **trace_base,
                "event": "error",
                "error_type": "BadRequestError",
                "error": repr(e),
            })
            raise LLMCallError(
                f"Bad request for model={self.model}. {str(e)[:200]}",
                model=self.model,
                api_base=self.api_base,
            ) from e
    
    def _parse_file_review(self, response: str, path: str) -> FileReview:
        """Parse LLM response into FileReview structure."""
        summary = ""
        issues = []
        suggestions = []
        
        current_section = None
        
        for line in response.split('\n'):
            line = line.strip()

            if line.startswith('SUMMARY:'):
                current_section = 'summary'
                summary = line[8:].strip()
                continue

            if line.startswith('ISSUES:'):
                current_section = 'issues'
                continue

            if line.startswith('SUGGESTIONS:'):
                current_section = 'suggestions'
                continue

            if current_section == 'summary' and line:
                summary += ' ' + line
                continue

            if not current_section:
                continue

            if not line:
                continue

            normalized = re.sub(r"^(?:[-*]\s+|\d+[\.)]\s+)", "", line).strip()
            if normalized.lower() == 'none':
                continue

            m = re.match(r"^(Line:\s*\d+\s*:\s*.+)$", normalized)
            if not m:
                continue

            item = m.group(1)
            if current_section == 'issues':
                issues.append(item)
            elif current_section == 'suggestions':
                suggestions.append(item)

        if not summary and response.strip():
            summary = response.strip()

        if not issues and not suggestions:
            for raw_line in response.split('\n'):
                candidate = raw_line.strip()
                if not candidate:
                    continue
                candidate = re.sub(r"^(?:[-*]\s+|\d+[\.)]\s+)", "", candidate).strip()
                if re.search(r"Line:\s*\d+", candidate):
                    issues.append(candidate)
                if len(issues) >= 20:
                    break

        return FileReview(
            path=path,
            issues=issues,
            suggestions=suggestions,
            summary=summary.strip()
        )
    
    def review_file(self, file_diff: FileDiff) -> FileReview:
        """Review a single file diff."""
        change_type_map = {
            'A': 'Added',
            'D': 'Deleted',
            'M': 'Modified',
            'R': 'Renamed'
        }
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": FILE_REVIEW_PROMPT.format(
                path=file_diff.path,
                change_type=change_type_map.get(file_diff.change_type, 'Changed'),
                diff_content=file_diff.diff_content[:8000]  # Limit context
            )}
        ]
        
        response = self._call_llm(messages)
        return self._parse_file_review(response, file_diff.path)
    
    def review_branch_diff(
        self,
        branch_diff: BranchDiff,
        progress_callback=None
    ) -> CodeReview:
        """
        Review all changes between branches.
        
        Args:
            branch_diff: The diff to review
            progress_callback: Optional callback(current, total, file_path) for progress
        
        Returns:
            Complete CodeReview object
        """
        file_reviews = []
        
        for i, file_diff in enumerate(branch_diff.files):
            if progress_callback:
                progress_callback(i + 1, len(branch_diff.files), file_diff.path)
            
            review = self.review_file(file_diff)
            file_reviews.append(review)
        
        # Generate overall summary
        files_summary = "\n".join([
            f"- {r.path}: {r.summary}"
            for r in file_reviews
        ])
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": OVERALL_SUMMARY_PROMPT.format(
                source=branch_diff.source_branch,
                target=branch_diff.target_branch,
                files_summary=files_summary
            )}
        ]
        
        overall_summary = self._call_llm(messages)
        
        return CodeReview(
            source_branch=branch_diff.source_branch,
            target_branch=branch_diff.target_branch,
            file_reviews=file_reviews,
            overall_summary=overall_summary
        )
