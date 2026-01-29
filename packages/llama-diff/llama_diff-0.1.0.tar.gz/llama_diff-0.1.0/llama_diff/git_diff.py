"""Git diff extraction module."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import fnmatch
import re

from git import Repo
from git.exc import InvalidGitRepositoryError, GitCommandError
from gitdb.exc import BadName


def format_diff_with_line_numbers(diff_content: str) -> str:
    """Add explicit line numbers to diff content for clearer LLM understanding."""
    lines = diff_content.split('\n')
    result = []
    new_line_num = 0
    
    for line in lines:
        if line.startswith('@@'):
            match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@.*', line)
            if match:
                new_line_num = int(match.group(1))
            # Skip hunk headers to avoid LLM confusion with line numbers
            continue
        elif line.startswith('-'):
            result.append(f"       {line}")
        elif line.startswith('+'):
            result.append(f"Line:{new_line_num:<3} {line}")
            new_line_num += 1
        elif line.startswith(' '):
            if new_line_num > 0:
                result.append(f"Line:{new_line_num:<3} {line}")
                new_line_num += 1
            else:
                result.append(line)
        elif line == '':
            if new_line_num > 0:
                result.append(f"Line:{new_line_num:<3} ")
                new_line_num += 1
            else:
                result.append(line)
        else:
            result.append(line)
    
    return '\n'.join(result)


@dataclass
class FileDiff:
    """Represents a diff for a single file."""
    path: str
    change_type: str  # 'A' (added), 'D' (deleted), 'M' (modified), 'R' (renamed)
    diff_content: str
    old_path: Optional[str] = None  # For renames


@dataclass
class BranchDiff:
    """Represents the complete diff between two branches."""
    source_branch: str
    target_branch: str
    files: list[FileDiff]
    
    @property
    def total_files(self) -> int:
        return len(self.files)
    
    @property
    def summary(self) -> str:
        added = sum(1 for f in self.files if f.change_type == 'A')
        deleted = sum(1 for f in self.files if f.change_type == 'D')
        modified = sum(1 for f in self.files if f.change_type == 'M')
        renamed = sum(1 for f in self.files if f.change_type == 'R')
        return f"Files: {added} added, {deleted} deleted, {modified} modified, {renamed} renamed"


class GitDiffExtractor:
    """Extracts diffs between git branches."""
    
    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path).resolve()
        try:
            self.repo = Repo(self.repo_path)
        except InvalidGitRepositoryError:
            raise ValueError(f"Not a valid git repository: {self.repo_path}")
    
    def get_branches(self) -> list[str]:
        """Get list of all branches in the repository."""
        return [ref.name for ref in self.repo.refs if hasattr(ref, 'name')]
    
    def validate_branch(self, branch: str) -> bool:
        """Check if a branch exists."""
        if branch == "uncommitted":
            return True
        try:
            self.repo.rev_parse(branch)
            return True
        except (GitCommandError, BadName):
            return False
    
    def get_diff(
        self,
        source_branch: str,
        target_branch: str,
        file_patterns: Optional[list[str]] = None,
        context_lines: int = 50,
        diff_mode: str = "pr"
    ) -> BranchDiff:
        """
        Get the diff between two branches.
        
        Args:
            source_branch: The branch with changes (e.g., feature branch)
            target_branch: The base branch to compare against (e.g., main)
            file_patterns: Optional glob patterns to filter files (e.g., ['*.py', '*.js'])
            context_lines: Number of unchanged context lines to include before/after each diff hunk
        
        Returns:
            BranchDiff object containing all file diffs
        """
        if not self.validate_branch(source_branch):
            raise ValueError(f"Branch not found: {source_branch}")
        if not self.validate_branch(target_branch):
            raise ValueError(f"Branch not found: {target_branch}")
        
        if diff_mode not in {"pr", "compare"}:
            raise ValueError(f"Invalid diff_mode: {diff_mode}")

        if diff_mode == "pr":
            merge_base = self.repo.merge_base(target_branch, source_branch)
            if not merge_base:
                base_commit = self.repo.rev_parse(target_branch)
            else:
                base_commit = merge_base[0]
            left_commit = base_commit
            right_commit = self.repo.rev_parse(source_branch)
        else:
            left_commit = self.repo.rev_parse(source_branch)
            right_commit = self.repo.rev_parse(target_branch)
        
        # Get diff between commits
        if context_lines < 0:
            raise ValueError("context_lines must be >= 0")
        diff_index = left_commit.diff(
            right_commit,
            create_patch=True,
            unified=context_lines,
        )
        
        files = []
        for diff_item in diff_index:
            # Determine file path and change type
            if diff_item.new_file:
                path = diff_item.b_path
                change_type = 'A'
                old_path = None
            elif diff_item.deleted_file:
                path = diff_item.a_path
                change_type = 'D'
                old_path = None
            elif diff_item.renamed:
                path = diff_item.b_path
                change_type = 'R'
                old_path = diff_item.a_path
            else:
                path = diff_item.b_path or diff_item.a_path
                change_type = 'M'
                old_path = None
            
            # Apply file pattern filter
            if file_patterns:
                if not any(fnmatch.fnmatch(path, pattern) for pattern in file_patterns):
                    continue
            
            # Get the actual diff content and format with line numbers
            try:
                raw_diff = diff_item.diff.decode('utf-8', errors='replace')
                diff_content = format_diff_with_line_numbers(raw_diff)
            except Exception:
                diff_content = "[Binary file or encoding error]"
            
            files.append(FileDiff(
                path=path,
                change_type=change_type,
                diff_content=diff_content,
                old_path=old_path
            ))
        
        return BranchDiff(
            source_branch=source_branch,
            target_branch=target_branch,
            files=files
        )
    
    def get_file_content(self, branch: str, file_path: str) -> Optional[str]:
        """Get the content of a file at a specific branch."""
        try:
            if branch == "uncommitted":
                target_path = (self.repo_path / file_path).resolve()
                if self.repo_path not in target_path.parents and target_path != self.repo_path:
                    return None
                if not target_path.is_file():
                    return None
                return target_path.read_text(encoding="utf-8", errors="replace")
            commit = self.repo.rev_parse(branch)
            blob = commit.tree / file_path
            return blob.data_stream.read().decode('utf-8', errors='replace')
        except (KeyError, GitCommandError, BadName):
            return None
    
    def get_uncommitted_diff(
        self,
        file_patterns: Optional[list[str]] = None,
        context_lines: int = 50,
        staged_only: bool = False
    ) -> BranchDiff:
        """
        Get diff of uncommitted changes (working directory vs HEAD).
        
        Args:
            file_patterns: Optional glob patterns to filter files (e.g., ['*.py', '*.js'])
            context_lines: Number of unchanged context lines to include before/after each diff hunk
            staged_only: If True, only include staged changes; otherwise include all uncommitted changes
        
        Returns:
            BranchDiff object containing all file diffs
        """
        if context_lines < 0:
            raise ValueError("context_lines must be >= 0")
        
        head_commit = self.repo.head.commit
        
        files = []
        
        if staged_only:
            # Only staged changes (index vs HEAD)
            diff_index = head_commit.diff(None, create_patch=True, unified=context_lines)
        else:
            # All uncommitted changes: staged + unstaged
            # First get staged changes (HEAD vs index)
            staged_diff = head_commit.diff(None, create_patch=True, unified=context_lines)
            # Then get unstaged changes (index vs working tree)
            unstaged_diff = self.repo.index.diff(None, create_patch=True, unified=context_lines)
            
            # Combine both, preferring unstaged if file appears in both
            seen_paths = set()
            diff_items = []
            
            for diff_item in unstaged_diff:
                path = diff_item.b_path or diff_item.a_path
                seen_paths.add(path)
                diff_items.append(diff_item)
            
            for diff_item in staged_diff:
                path = diff_item.b_path or diff_item.a_path
                if path not in seen_paths:
                    diff_items.append(diff_item)
            
            diff_index = diff_items
        
        for diff_item in diff_index:
            # Determine file path and change type
            if diff_item.new_file:
                path = diff_item.b_path
                change_type = 'A'
                old_path = None
            elif diff_item.deleted_file:
                path = diff_item.a_path
                change_type = 'D'
                old_path = None
            elif diff_item.renamed:
                path = diff_item.b_path
                change_type = 'R'
                old_path = diff_item.a_path
            else:
                path = diff_item.b_path or diff_item.a_path
                change_type = 'M'
                old_path = None
            
            # Apply file pattern filter
            if file_patterns:
                if not any(fnmatch.fnmatch(path, pattern) for pattern in file_patterns):
                    continue
            
            # Get the actual diff content and format with line numbers
            try:
                raw_diff = diff_item.diff.decode('utf-8', errors='replace')
                diff_content = format_diff_with_line_numbers(raw_diff)
            except Exception:
                diff_content = "[Binary file or encoding error]"
            
            files.append(FileDiff(
                path=path,
                change_type=change_type,
                diff_content=diff_content,
                old_path=old_path
            ))
        
        return BranchDiff(
            source_branch="uncommitted",
            target_branch="HEAD",
            files=files
        )
