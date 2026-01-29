"""CLI entry point for LlamaDiff."""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.panel import Panel

from .git_diff import GitDiffExtractor
from .reviewer import CodeReviewer, LLMCallError
from .html_server import serve_html_review


console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help", "/?"]})
@click.option(
    '--repo', '-r',
    default='.',
    help='Path to the git repository (default: current directory)'
)
@click.option(
    '--source', '-s',
    default=None,
    help='Source branch (the branch with changes)'
)
@click.option(
    '--uncommitted', '-u',
    is_flag=True,
    default=False,
    help='Review uncommitted changes (staged + unstaged) instead of branch diff'
)
@click.option(
    '--staged',
    is_flag=True,
    default=False,
    help='With --uncommitted, review only staged changes'
)
@click.option(
    '--target', '-t',
    default='main',
    help='Target branch to compare against (default: main)'
)
@click.option(
    '--diff-mode',
    type=click.Choice(['pr', 'compare'], case_sensitive=False),
    default='pr',
    show_default=True,
    help='Diff mode: pr=merge-base(target,source)..source (PR-style), compare=source..target (matches `git diff <source> <target>`).'
)
@click.option(
    '--model', '-m',
    default='ollama/llama3.2',
    help='LLM model to use (e.g., ollama/llama3.2, gpt-4o, claude-3-5-sonnet-20241022)'
)
@click.option(
    '--files', '-f',
    multiple=True,
    help='File patterns to include (e.g., "*.py" "*.js")'
)
@click.option(
    '--context',
    default=100,
    type=int,
    show_default=True,
    help='Number of unchanged context lines to include before/after each diff hunk'
)
@click.option(
    '--output', '-o',
    default=None,
    help='Output file path (default: print to console)'
)
@click.option(
    '--api-base',
    default=None,
    help='Custom API base URL (e.g., for Ollama: http://localhost:11434). If omitted and model starts with ollama/, OLLAMA_API_BASE is used.'
)
@click.option(
    '--html',
    is_flag=True,
    default=False,
    help='Serve review as interactive HTML with line navigation'
)
@click.option(
    '--port',
    default=8765,
    type=int,
    help='Port for HTML server (default: 8765)'
)
@click.option(
    '--dump-context',
    default=None,
    help='Dump diff context sent to LLM to this file for debugging'
)
@click.option(
    '--llm-trace',
    default=None,
    help='Write plain-text trace of each LLM call (full request + full response/error + timings) to this file'
)
@click.option(
    '--llm-timeout',
    default=None,
    type=float,
    help='Per-request LLM timeout in seconds (passed to litellm). If omitted, litellm default is used.'
)
@click.option(
    '--max-tokens',
    default=None,
    type=int,
    help='Maximum tokens to generate per LLM call (passed to litellm). If omitted, provider default is used.'
)
def main(
    repo: str,
    source: Optional[str],
    uncommitted: bool,
    staged: bool,
    target: str,
    diff_mode: str,
    model: Optional[str],
    files: tuple,
    context: int,
    output: Optional[str],
    api_base: Optional[str],
    html: bool,
    port: int,
    dump_context: Optional[str],
    llm_trace: Optional[str],
    llm_timeout: Optional[float],
    max_tokens: Optional[int]
):
    """
    AI-powered code review for git branch diffs.
    
    Compares SOURCE branch against TARGET branch and provides
    an LLM-generated code review.
    
    Examples:
    
        LlamaDiff -s feature-branch -t main
        
        LlamaDiff -r /path/to/repo -s develop -t main -m gpt-4o
        
        LlamaDiff -s feature -t main -f "*.py" -o review.md
        
        LlamaDiff -s feature -t main --html --port 9000
        
        LlamaDiff --uncommitted
        
        LlamaDiff -u --staged -f "*.py"
    """
    # Load environment variables
    load_dotenv()
    
    # Determine model
    if model is None:
        model = os.getenv('DEFAULT_MODEL', 'ollama/llama3.2')
    
    # Determine API base
    if api_base is None and model.startswith('ollama/'):
        api_base = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434')
    
    console.print(Panel.fit(
        f"[bold blue]LlamaDiff[/bold blue] Code Review\n"
        f"[dim]Model: {model}[/dim]",
        border_style="blue"
    ))
    
    # Initialize git extractor
    try:
        extractor = GitDiffExtractor(repo)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    
    console.print(f"\n[dim]Repository:[/dim] {extractor.repo_path}")
    
    # Validate options
    if uncommitted:
        if source:
            console.print("[yellow]Warning:[/yellow] --source is ignored when using --uncommitted")
        console.print(f"[dim]Reviewing:[/dim] uncommitted changes" + (" (staged only)" if staged else ""))
    else:
        if staged:
            console.print("[red]Error:[/red] --staged requires --uncommitted")
            sys.exit(1)
        if not source:
            console.print("[red]Error:[/red] --source is required (or use --uncommitted)")
            sys.exit(1)
        console.print(f"[dim]Comparing:[/dim] {source} → {target}")
    
    # Get diff
    try:
        file_patterns = list(files) if files else None
        with console.status("[bold green]Extracting diff..."):
            if uncommitted:
                branch_diff = extractor.get_uncommitted_diff(file_patterns, context_lines=context, staged_only=staged)
            else:
                branch_diff = extractor.get_diff(source, target, file_patterns, context_lines=context, diff_mode=diff_mode)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    
    if branch_diff.total_files == 0:
        if uncommitted:
            console.print("\n[yellow]No uncommitted changes found.[/yellow]")
        else:
            console.print("\n[yellow]No changes found between branches.[/yellow]")
            console.print(f"[dim]Details: diff-mode='{diff_mode}'[/dim]")
            if diff_mode.lower() == "pr":
                console.print(f"[dim]In pr mode we review what '{source}' would add if merged into '{target}' (merge-base(target, source)..source).[/dim]")
                console.print(f"[dim]If '{source}' is behind '{target}', this can be empty even if `git diff {source} {target}` shows changes.[/dim]")
                console.print(f"[dim]Try one of these:[/dim]")
                console.print(f"[dim]- Match git diff: python -m llama_diff -s {source} -t {target} --diff-mode compare[/dim]")
                console.print(f"[dim]- Review PR in opposite direction: python -m llama_diff -s {target} -t {source} --diff-mode pr[/dim]")
            else:
                console.print(f"[dim]In compare mode we show tip-to-tip differences (source..target), like `git diff {source} {target}`.[/dim]")
                console.print(f"[dim]If you expected a PR-style diff (what source adds), try `--diff-mode pr` or swap source/target.[/dim]")
        sys.exit(0)
    
    console.print(f"[dim]{branch_diff.summary}[/dim]\n")
    
    if dump_context:
        dump_path = Path(dump_context)
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dump_path, 'w') as f:
            f.write(f"# Diff Context: {branch_diff.source_branch} → {branch_diff.target_branch}\n\n")
            for file_diff in branch_diff.files:
                f.write(f"## {file_diff.path} ({file_diff.change_type})\n\n")
                f.write("```diff\n")
                f.write(file_diff.diff_content)
                f.write("\n```\n\n")
        console.print(f"[green]Context dumped to:[/green] {dump_path}")
    
    # Initialize reviewer
    reviewer = CodeReviewer(model=model, api_base=api_base, trace_path=llm_trace, timeout=llm_timeout, max_tokens=max_tokens)
    
    # Review with progress
    def progress_callback(current: int, total: int, file_path: str):
        progress.update(task, completed=current, description=f"[cyan]Reviewing {file_path}[/cyan]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.completed}/{task.total}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Starting review...[/cyan]", total=branch_diff.total_files)
            review = reviewer.review_branch_diff(branch_diff, progress_callback)
    except LLMCallError as e:
        console.print("\n[red]LLM error:[/red] " + str(e))
        console.print(f"[dim]Model:[/dim] {e.model}")
        if e.api_base:
            console.print(f"[dim]API base:[/dim] {e.api_base}")
        sys.exit(2)
    
    # Output results
    if html:
        console.print(f"\n[green]Starting HTML server on port {port}...[/green]")
        serve_html_review(review, branch_diff, extractor, port=port)
    else:
        markdown_output = review.to_markdown()
        
        if output:
            output_path = Path(output)
            output_path.write_text(markdown_output)
            console.print(f"\n[green]Review saved to:[/green] {output_path}")
        else:
            console.print("\n")
            console.print(Markdown(markdown_output))
    
    # Summary stats
    total_issues = sum(len(r.issues) for r in review.file_reviews)
    total_suggestions = sum(len(r.suggestions) for r in review.file_reviews)
    
    console.print(Panel.fit(
        f"[bold]Review Complete[/bold]\n"
        f"Files reviewed: {len(review.file_reviews)}\n"
        f"Issues found: {total_issues}\n"
        f"Suggestions: {total_suggestions}",
        border_style="green"
    ))


if __name__ == '__main__':
    main()
