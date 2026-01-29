"""HTML server for interactive code review viewing."""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader

from .reviewer import CodeReview, FileReview
from .git_diff import BranchDiff, GitDiffExtractor


TEMPLATES_DIR = Path(__file__).parent / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=True
)


def get_language(path: str) -> str:
    """Get language for syntax highlighting."""
    ext = os.path.splitext(path)[1].lower()
    ext_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.tsx': 'tsx', '.jsx': 'jsx', '.json': 'json', '.html': 'xml',
        '.css': 'css', '.scss': 'scss', '.md': 'markdown',
        '.yaml': 'yaml', '.yml': 'yaml', '.sh': 'bash', '.bash': 'bash',
        '.go': 'go', '.rs': 'rust', '.java': 'java', '.c': 'c',
        '.cpp': 'cpp', '.h': 'c', '.hpp': 'cpp', '.rb': 'ruby',
        '.php': 'php', '.sql': 'sql', '.xml': 'xml', '.toml': 'toml',
    }
    return ext_map.get(ext, 'plaintext')


def generate_index_html(review: CodeReview, branch_diff: BranchDiff) -> str:
    """Generate main review page using Jinja2 template."""
    
    change_labels = {'A': 'Added', 'D': 'Deleted', 'M': 'Modified', 'R': 'Renamed'}
    
    files = []
    for idx, (file_review, file_diff) in enumerate(zip(review.file_reviews, branch_diff.files)):
        files.append({
            'idx': idx,
            'path': file_review.path,
            'change_type': file_diff.change_type,
            'change_label': change_labels.get(file_diff.change_type, 'Changed'),
            'summary': file_review.summary,
            'issues': file_review.issues,
            'suggestions': file_review.suggestions,
        })
    
    template = env.get_template('index.html')
    return template.render(
        source_branch=review.source_branch,
        target_branch=review.target_branch,
        overall_summary=review.overall_summary,
        files=files,
        file_count=len(review.file_reviews),
        total_issues=sum(len(r.issues) for r in review.file_reviews),
        total_suggestions=sum(len(r.suggestions) for r in review.file_reviews),
    )


def generate_code_html(
    file_idx: int,
    file_review: FileReview,
    file_diff,
    content: str,
    review: CodeReview
) -> str:
    """Generate code page using Jinja2 template."""
    
    change_labels = {'A': 'Added', 'D': 'Deleted', 'M': 'Modified', 'R': 'Renamed'}
    
    template = env.get_template('code.html')
    return template.render(
        source_branch=review.source_branch,
        target_branch=review.target_branch,
        file_path=file_review.path,
        file_name=os.path.basename(file_review.path),
        change_type=file_diff.change_type,
        change_label=change_labels.get(file_diff.change_type, 'Changed'),
        summary=file_review.summary,
        issues=file_review.issues,
        suggestions=file_review.suggestions,
        language=get_language(file_review.path),
        code_content=content,
        line_count=len(content.split('\n')),
        diff_content=file_diff.diff_content,
    )


class ReviewHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Custom HTTP handler for serving the review."""
    
    review: CodeReview = None
    branch_diff: BranchDiff = None
    extractor: GitDiffExtractor = None
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '':
            html_content = generate_index_html(self.review, self.branch_diff)
            self.send_html(html_content)
        elif path.startswith('/code/'):
            try:
                file_idx = int(path.split('/')[2])
                if 0 <= file_idx < len(self.review.file_reviews):
                    file_review = self.review.file_reviews[file_idx]
                    file_diff = self.branch_diff.files[file_idx]
                    content = self.extractor.get_file_content(
                        self.branch_diff.source_branch, 
                        file_review.path
                    ) or "[File not available]"
                    
                    html_content = generate_code_html(
                        file_idx, file_review, file_diff, content, self.review
                    )
                    self.send_html(html_content)
                else:
                    self.send_error(404, "File not found")
            except (ValueError, IndexError):
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "Not found")
    
    def send_html(self, content: str):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass


def serve_html_review(
    review: CodeReview,
    branch_diff: BranchDiff,
    extractor: GitDiffExtractor,
    port: int = 8765,
    open_browser: bool = True
) -> None:
    """Start HTTP server to serve the HTML review."""
    
    handler = type('Handler', (ReviewHTTPHandler,), {
        'review': review,
        'branch_diff': branch_diff,
        'extractor': extractor
    })
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\n🌐 Review server running at: {url}")
        print("Press Ctrl+C to stop the server\n")
        
        if open_browser:
            webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")
