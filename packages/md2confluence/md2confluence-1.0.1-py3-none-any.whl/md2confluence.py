#!/usr/bin/env python3
"""
md2confluence - Markdown to Confluence Sync Tool

Converts markdown documentation to Confluence storage format and syncs via API.

Features:
- Markdown to Confluence storage format conversion
- Image upload and embedding
- Page creation and updates
- Retry logic with exponential backoff
- Rate limiting
- Dry-run mode
- Config file support

Usage:
    ./md2confluence.py                    # Sync all configured docs
    ./md2confluence.py --dry-run          # Preview without changes
    ./md2confluence.py --list             # List configured documents
    ./md2confluence.py --verify           # Verify config and connectivity
    ./md2confluence.py --single "Title" path.md parent_id

Environment Variables:
    CONFLUENCE_API_TOKEN      API token (required)
    CONFLUENCE_USER_EMAIL     User email (required for basic auth)
    CONFLUENCE_AUTH_MODE      Auth mode: basic, bearer, or auto (default: auto)
"""

import argparse
import html
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

REPO_URL = os.environ.get("CONFLUENCE_REPO_URL", "")


@dataclass
class Config:
    """Configuration for Confluence sync."""
    # Connection
    base_url: str = ""
    space_key: str = ""
    auth_mode: str = "auto"  # basic, bearer, or auto
    api_token: str = ""
    user_email: str = ""
    
    # Parent pages
    tech_parent_id: str = ""
    user_parent_id: str = ""
    
    # Behavior
    max_retries: int = 3
    retry_delay: int = 5
    timeout: int = 30
    rate_limit_ms: int = 100
    add_disclaimer: bool = True
    max_image_width: int = 800
    
    # Edge case handling
    existing_page_behavior: str = "update"  # update, skip, fail
    missing_parent_behavior: str = "fail"   # fail, create
    missing_file_behavior: str = "skip"     # skip, fail
    image_failure_behavior: str = "placeholder"  # placeholder, skip, fail
    title_special_chars: str = "sanitize"   # sanitize, encode, fail
    title_strip_pattern: str = r'[<>:"/\\|?*]'
    
    # Document mappings: key -> (title, path, parent_id)
    documents: Dict[str, Tuple[str, str, str]] = field(default_factory=dict)
    
    # Runtime
    dry_run: bool = False
    verbose: bool = False
    
    # Cached values
    _space_id: str = ""


def load_config(config_file: str = ".confluence-sync.conf") -> Config:
    """Load configuration from shell-style config file."""
    global REPO_URL
    config = Config()
    
    # Track config sources for reporting
    config_sources = {}
    
    # Load from environment first
    env_vars = {
        "api_token": "CONFLUENCE_API_TOKEN",
        "user_email": "CONFLUENCE_USER_EMAIL",
        "auth_mode": "CONFLUENCE_AUTH_MODE",
        "base_url": "CONFLUENCE_BASE_URL",
        "space_key": "CONFLUENCE_SPACE_KEY",
        "tech_parent_id": "CONFLUENCE_TECH_PARENT_ID",
        "user_parent_id": "CONFLUENCE_USER_PARENT_ID",
    }
    
    for attr, env_name in env_vars.items():
        value = os.environ.get(env_name, "")
        if value:
            setattr(config, attr, value)
            config_sources[attr] = "env"
    
    # Default auth_mode if not set
    if not config.auth_mode:
        config.auth_mode = "auto"
    
    # Parse config file if it exists
    config_path = Path(config_file)
    if config_path.exists():
        log_info(f"Config file found: {config_file}")
        content = config_path.read_text()
        
        # Build a local variable context for resolving references
        local_vars = {
            "CONFLUENCE_TECH_PARENT_ID": config.tech_parent_id,
            "CONFLUENCE_USER_PARENT_ID": config.user_parent_id,
        }
        
        # Two-pass parsing: first pass gets base values, second pass resolves references
        doc_lines = []  # Store doc lines for second pass
        
        # Parse shell variable assignments
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Handle variable assignments: VAR="value" or VAR="${VAR:-default}"
            match = re.match(r'^([A-Z_][A-Z0-9_]*)=(.+)$', line)
            if match:
                var_name = match.group(1)
                var_value = match.group(2).strip('"\'')
                
                # Resolve ${VAR:-default} patterns using env + local vars
                def resolve_default(m):
                    env_var = m.group(1)
                    default = m.group(2)
                    return os.environ.get(env_var, local_vars.get(env_var, default))
                
                var_value = re.sub(r'\$\{([^:}]+):-([^}]*)\}', resolve_default, var_value)
                var_value = re.sub(r'\$\{([^}]+)\}', lambda m: os.environ.get(m.group(1), local_vars.get(m.group(1), '')), var_value)
                
                # Store document mappings for second pass
                if var_name.startswith("CONFLUENCE_DOC_"):
                    doc_lines.append((var_name, var_value))
                    continue
                
                # Update local vars for reference resolution
                local_vars[var_name] = var_value
                
                # Map to config attributes (only override if not set from env)
                if var_name == "CONFLUENCE_API_TOKEN" and "api_token" not in config_sources:
                    config.api_token = var_value
                    config_sources["api_token"] = "config"
                elif var_name == "CONFLUENCE_USER_EMAIL" and "user_email" not in config_sources:
                    config.user_email = var_value
                    config_sources["user_email"] = "config"
                elif var_name == "CONFLUENCE_BASE_URL" and "base_url" not in config_sources:
                    config.base_url = var_value
                    config_sources["base_url"] = "config"
                elif var_name == "CONFLUENCE_SPACE_KEY" and "space_key" not in config_sources:
                    config.space_key = var_value
                    config_sources["space_key"] = "config"
                elif var_name == "CONFLUENCE_AUTH_MODE" and "auth_mode" not in config_sources:
                    config.auth_mode = var_value
                    config_sources["auth_mode"] = "config"
                elif var_name == "CONFLUENCE_REPO_URL":
                    REPO_URL = var_value
                elif var_name == "CONFLUENCE_TECH_PARENT_ID" and "tech_parent_id" not in config_sources:
                    config.tech_parent_id = var_value
                    config_sources["tech_parent_id"] = "config"
                    local_vars[var_name] = var_value
                elif var_name == "CONFLUENCE_USER_PARENT_ID" and "user_parent_id" not in config_sources:
                    config.user_parent_id = var_value
                    config_sources["user_parent_id"] = "config"
                    local_vars[var_name] = var_value
                elif var_name == "CONFLUENCE_MAX_RETRIES":
                    config.max_retries = int(var_value)
                elif var_name == "CONFLUENCE_RETRY_DELAY":
                    config.retry_delay = int(var_value)
                elif var_name == "CONFLUENCE_TIMEOUT":
                    config.timeout = int(var_value)
                elif var_name == "CONFLUENCE_RATE_LIMIT_MS":
                    config.rate_limit_ms = int(var_value)
                elif var_name == "CONFLUENCE_ADD_DISCLAIMER":
                    config.add_disclaimer = var_value.lower() == "true"
                elif var_name == "CONFLUENCE_MAX_IMAGE_WIDTH":
                    config.max_image_width = int(var_value)
                elif var_name == "CONFLUENCE_EXISTING_PAGE_BEHAVIOR":
                    config.existing_page_behavior = var_value
                elif var_name == "CONFLUENCE_MISSING_PARENT_BEHAVIOR":
                    config.missing_parent_behavior = var_value
                elif var_name == "CONFLUENCE_MISSING_FILE_BEHAVIOR":
                    config.missing_file_behavior = var_value
                elif var_name == "CONFLUENCE_IMAGE_FAILURE_BEHAVIOR":
                    config.image_failure_behavior = var_value
                elif var_name == "CONFLUENCE_TITLE_SPECIAL_CHARS":
                    config.title_special_chars = var_value
                elif var_name == "CONFLUENCE_TITLE_STRIP_PATTERN":
                    config.title_strip_pattern = var_value
        
        # Second pass: process document mappings with resolved parent IDs
        for var_name, var_value in doc_lines:
            parts = var_value.split('|')
            if len(parts) == 3:
                doc_key = var_name[15:]  # Remove CONFLUENCE_DOC_ prefix
                title, path, parent_id = parts
                # Resolve parent_id references using local_vars
                if parent_id.startswith("${") and parent_id.endswith("}"):
                    ref_var = parent_id[2:-1]
                    parent_id = local_vars.get(ref_var, config.tech_parent_id)
                config.documents[doc_key] = (title, path, parent_id)
        
        log_info(f"  Loaded {len(config.documents)} document mapping(s) from config")
    else:
        log_warn(f"Config file not found: {config_file}")
        log_info("  Using environment variables only")
    
    # Log config sources
    if config_sources:
        env_count = sum(1 for v in config_sources.values() if v == "env")
        conf_count = sum(1 for v in config_sources.values() if v == "config")
        if env_count:
            log_debug(f"  {env_count} setting(s) from environment variables")
        if conf_count:
            log_debug(f"  {conf_count} setting(s) from config file")
    
    # Auto-detect auth mode
    if config.auth_mode == "auto":
        config.auth_mode = "basic" if config.user_email else "bearer"
    
    return config


# =============================================================================
# LOGGING
# =============================================================================

# ANSI colors (disabled if not a terminal)
if sys.stdout.isatty():
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'
else:
    RED = GREEN = YELLOW = BLUE = NC = ''

_verbose = False

def log_info(msg: str):
    print(f"{GREEN}[INFO]{NC} {msg}")

def log_warn(msg: str):
    print(f"{YELLOW}[WARN]{NC} {msg}")

def log_error(msg: str):
    print(f"{RED}[ERROR]{NC} {msg}", file=sys.stderr)

def log_debug(msg: str):
    if _verbose:
        print(f"{BLUE}[DEBUG]{NC} {msg}", file=sys.stderr)


# =============================================================================
# MARKDOWN TO CONFLUENCE CONVERSION
# =============================================================================

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text, quote=False)


def convert_code_blocks(content: str) -> str:
    """Convert fenced code blocks to Confluence code macro."""
    def replace_code_block(match):
        lang = match.group(1) or "text"
        code = match.group(2)
        lang_map = {
            "sh": "bash", "shell": "bash", "js": "javascript",
            "ts": "typescript", "py": "python", "yml": "yaml", "": "text"
        }
        lang = lang_map.get(lang.lower(), lang.lower())
        code = escape_html(code.strip())
        
        return f'''<ac:structured-macro ac:name="code" ac:schema-version="1">
<ac:parameter ac:name="language">{lang}</ac:parameter>
<ac:parameter ac:name="theme">Confluence</ac:parameter>
<ac:parameter ac:name="linenumbers">true</ac:parameter>
<ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body>
</ac:structured-macro>'''
    
    return re.sub(r'```(\w*)\n(.*?)```', replace_code_block, content, flags=re.DOTALL)


def convert_inline_code(content: str) -> str:
    """Convert inline code to <code> tags."""
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', content)


def convert_info_panels(content: str) -> str:
    """Convert blockquotes to Confluence format."""
    PANEL_PATTERNS = [
        (r'^\*{0,2}note:?\*{0,2}\s*', 'info'),
        (r'^\*{0,2}info:?\*{0,2}\s*', 'info'),
        (r'^\*{0,2}warning:?\*{0,2}\s*', 'warning'),
        (r'^\*{0,2}caution:?\*{0,2}\s*', 'warning'),
        (r'^\*{0,2}danger:?\*{0,2}\s*', 'warning'),
        (r'^\*{0,2}tip:?\*{0,2}\s*', 'tip'),
        (r'^\*{0,2}hint:?\*{0,2}\s*', 'tip'),
        (r'^\*{0,2}important:?\*{0,2}\s*', 'note'),
        (r'^\*{0,2}security\s+tip:?\*{0,2}\s*', 'warning'),
        (r'^\*{0,2}pro\s+tip:?\*{0,2}\s*', 'tip'),
    ]
    
    def detect_panel(text: str) -> Tuple[Optional[str], str]:
        text_stripped = text.strip()
        text_lower = text_stripped.lower()
        for pattern, panel_type in PANEL_PATTERNS:
            match = re.match(pattern, text_lower, re.IGNORECASE)
            if match:
                remaining = text_stripped[match.end():].strip()
                return (panel_type, remaining)
        return (None, text)
    
    def make_panel(panel_type: str, text: str) -> str:
        return f'''<ac:structured-macro ac:name="{panel_type}" ac:schema-version="1">
<ac:parameter ac:name="icon">true</ac:parameter>
<ac:rich-text-body><p>{text}</p></ac:rich-text-body>
</ac:structured-macro>'''
    
    def make_blockquote(text: str) -> str:
        return f'<blockquote><p>{text}</p></blockquote>'
    
    lines = content.split('\n')
    result = []
    blockquote_lines = []
    
    for line in lines:
        if line.startswith('> '):
            blockquote_lines.append(line[2:])
        elif line.startswith('>') and len(line) > 0:
            blockquote_lines.append(line[1:].lstrip())
        else:
            if blockquote_lines:
                quote_text = ' '.join(blockquote_lines).strip()
                panel_type, remaining_text = detect_panel(quote_text)
                if panel_type:
                    result.append(make_panel(panel_type, remaining_text))
                else:
                    result.append(make_blockquote(quote_text))
                blockquote_lines = []
            result.append(line)
    
    if blockquote_lines:
        quote_text = ' '.join(blockquote_lines).strip()
        panel_type, remaining_text = detect_panel(quote_text)
        if panel_type:
            result.append(make_panel(panel_type, remaining_text))
        else:
            result.append(make_blockquote(quote_text))
    
    return '\n'.join(result)


def convert_tables(content: str) -> str:
    """Convert markdown tables to Confluence tables."""
    lines = content.split('\n')
    result = []
    table_lines = []
    in_table = False
    
    for line in lines:
        if '|' in line and line.strip().startswith('|'):
            in_table = True
            table_lines.append(line)
        else:
            if in_table and table_lines:
                result.append(process_table(table_lines))
                table_lines = []
                in_table = False
            result.append(line)
    
    if table_lines:
        result.append(process_table(table_lines))
    
    return '\n'.join(result)


def process_table(table_lines: List[str]) -> str:
    """Process a markdown table into Confluence format."""
    if len(table_lines) < 2:
        return '\n'.join(table_lines)
    
    rows = []
    is_header = True
    
    for line in table_lines:
        if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
            continue
        
        cells = [c.strip() for c in line.strip().split('|')[1:-1]]
        
        if is_header:
            row = '<tr>' + ''.join(f'<th><p>{cell}</p></th>' for cell in cells) + '</tr>'
            is_header = False
        else:
            row = '<tr>' + ''.join(f'<td><p>{cell}</p></td>' for cell in cells) + '</tr>'
        
        rows.append(row)
    
    return f'<table data-layout="default"><colgroup></colgroup><tbody>{"".join(rows)}</tbody></table>'


def convert_lists(content: str) -> str:
    """Convert markdown lists to HTML lists."""
    lines = content.split('\n')
    result = []
    list_stack = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        ul_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        ol_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
        
        if ul_match:
            indent = len(ul_match.group(1))
            text = ul_match.group(2)
            list_type = 'ul'
        elif ol_match:
            indent = len(ol_match.group(1))
            text = ol_match.group(3)
            list_type = 'ol'
        else:
            while list_stack:
                _, lt = list_stack.pop()
                result.append(f'</{lt}>')
            result.append(line)
            i += 1
            continue
        
        level = indent // 2
        
        while list_stack and list_stack[-1][0] > level:
            _, lt = list_stack.pop()
            result.append(f'</{lt}>')
        
        if list_stack and list_stack[-1][0] == level and list_stack[-1][1] != list_type:
            _, lt = list_stack.pop()
            result.append(f'</{lt}>')
        
        if not list_stack or list_stack[-1][0] < level:
            result.append(f'<{list_type}>')
            list_stack.append((level, list_type))
        
        result.append(f'<li>{text}</li>')
        i += 1
    
    while list_stack:
        _, lt = list_stack.pop()
        result.append(f'</{lt}>')
    
    return '\n'.join(result)


def convert_headers(content: str) -> str:
    """Convert markdown headers to HTML headers."""
    for i in range(6, 0, -1):
        pattern = r'^' + '#' * i + r' (.+)$'
        content = re.sub(pattern, rf'<h{i}>\1</h{i}>', content, flags=re.MULTILINE)
    return content


def convert_emphasis(content: str) -> str:
    """Convert bold, italic, and strikethrough."""
    content = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', content)
    content = re.sub(r'\*\*\*([^*]+)\*\*\*', r'<strong><em>\1</em></strong>', content)
    content = re.sub(r'___([^_]+)___', r'<strong><em>\1</em></strong>', content)
    content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', content)
    content = re.sub(r'(?<![*\w])\*([^*]+)\*(?![*\w])', r'<em>\1</em>', content)
    content = re.sub(r'(?<![_\w])_([^_]+)_(?![_\w])', r'<em>\1</em>', content)
    return content


def convert_task_lists(content: str) -> str:
    """Convert task list checkboxes to Confluence status macros."""
    content = re.sub(
        r'^(\s*)[-*+]\s+\[[xX]\]\s+(.+)$',
        r'\1<ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Green</ac:parameter><ac:parameter ac:name="title">DONE</ac:parameter></ac:structured-macro> \2',
        content, flags=re.MULTILINE
    )
    content = re.sub(
        r'^(\s*)[-*+]\s+\[\s*\]\s+(.+)$',
        r'\1<ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Grey</ac:parameter><ac:parameter ac:name="title">TODO</ac:parameter></ac:structured-macro> \2',
        content, flags=re.MULTILINE
    )
    return content


def convert_autolinks(content: str) -> str:
    """Convert autolinks <url> and bare URLs to HTML links."""
    content = re.sub(r'<(https?://[^>]+)>', r'<a href="\1">\1</a>', content)
    content = re.sub(r'<([^@\s]+@[^>\s]+)>', r'<a href="mailto:\1">\1</a>', content)
    return content


def convert_reference_links(content: str) -> str:
    """Convert reference-style links [text][ref] with [ref]: url definitions."""
    ref_pattern = r'^\[([^\]]+)\]:\s*(\S+)(?:\s+"([^"]*)")?\s*$'
    references = {}
    
    for match in re.finditer(ref_pattern, content, re.MULTILINE):
        ref_id = match.group(1).lower()
        url = match.group(2)
        title = match.group(3) or ""
        references[ref_id] = (url, title)
    
    content = re.sub(ref_pattern, '', content, flags=re.MULTILINE)
    
    def replace_ref_link(match):
        text = match.group(1)
        ref_id = (match.group(2) or text).lower()
        if ref_id in references:
            url, title = references[ref_id]
            title_attr = f' title="{title}"' if title else ''
            return f'<a href="{url}"{title_attr}>{text}</a>'
        return match.group(0)
    
    content = re.sub(r'\[([^\]]+)\]\[([^\]]*)\]', replace_ref_link, content)
    content = re.sub(r'\[([^\]]+)\]\[\]', replace_ref_link, content)
    
    return content


def strip_html_comments(content: str) -> str:
    """Remove HTML comments from content."""
    return re.sub(r'<!--[\s\S]*?-->', '', content)


def convert_links(content: str) -> str:
    """Convert markdown links to HTML links (but not images)."""
    return re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)


def convert_horizontal_rules(content: str) -> str:
    """Convert horizontal rules."""
    return re.sub(r'^---+$', r'<hr />', content, flags=re.MULTILINE)


def remove_extra_blank_lines(content: str) -> str:
    """Remove extra blank lines."""
    content = re.sub(r'\n\n+(<h[1-6]>)', r'\n\1', content)
    content = re.sub(r'(</h[1-6]>)\n\n+', r'\1\n', content)
    content = re.sub(r'\n\n+(<[uo]l>)', r'\n\1', content)
    content = re.sub(r'(</[uo]l>)\n\n+', r'\1\n', content)
    content = re.sub(r'\n\n+(<ac:structured-macro ac:name="code")', r'\n\1', content)
    content = re.sub(r'(</ac:structured-macro>)\n\n+', r'\1\n', content)
    content = re.sub(r'\n\n+(<table)', r'\n\1', content)
    content = re.sub(r'(</table>)\n\n+', r'\1\n', content)
    content = re.sub(r'\n{3,}', r'\n\n', content)
    return content


def wrap_paragraphs(content: str) -> str:
    """Wrap plain text lines in <p> tags."""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
            continue
        if stripped.startswith('<') or stripped.startswith('<!--'):
            result.append(line)
            continue
        result.append(f'<p>{stripped}</p>')
    
    return '\n'.join(result)


def add_disclaimer(content: str, md_file: str) -> str:
    """Add a disclaimer panel at the bottom of the content."""
    repo_url = REPO_URL
    if repo_url:
        source_link = f'<a href="{repo_url}/src/main/{md_file}">{md_file}</a>'
    else:
        source_link = f'<code>{md_file}</code>'
    
    disclaimer = f'''
<ac:structured-macro ac:name="note" ac:schema-version="1">
<ac:parameter ac:name="icon">true</ac:parameter>
<ac:parameter ac:name="title">Auto-Generated Content</ac:parameter>
<ac:rich-text-body>
<p>This page is automatically generated from {source_link} in the repository. 
<strong>Do not edit this page directly</strong> - changes will be overwritten on the next sync. 
To update this content, modify the source file and commit to the repository.</p>
</ac:rich-text-body>
</ac:structured-macro>'''
    return content + disclaimer


def fix_image_sizing(content: str, max_width: int = 800) -> str:
    """Add width constraint to images."""
    content = re.sub(
        r'<ac:image ac:alt="([^"]*)">\s*<ri:attachment ri:filename="([^"]*)" />\s*</ac:image>',
        rf'<ac:image ac:width="{max_width}" ac:alt="\1"><ri:attachment ri:filename="\2" /></ac:image>',
        content
    )
    return content


def convert_markdown_to_confluence(content: str, md_file: str = "", config: Optional[Config] = None) -> str:
    """Convert markdown content to Confluence storage format."""
    content = strip_html_comments(content)
    content = convert_code_blocks(content)
    content = convert_tables(content)
    content = convert_info_panels(content)
    content = convert_task_lists(content)
    content = convert_lists(content)
    content = convert_headers(content)
    content = convert_emphasis(content)
    content = convert_inline_code(content)
    content = convert_reference_links(content)
    content = convert_autolinks(content)
    content = convert_links(content)
    content = convert_horizontal_rules(content)
    
    max_width = config.max_image_width if config else 800
    content = fix_image_sizing(content, max_width)
    content = remove_extra_blank_lines(content)
    content = wrap_paragraphs(content)
    
    if md_file and (not config or config.add_disclaimer):
        content = add_disclaimer(content, md_file)
    
    return content


# =============================================================================
# CONFLUENCE API CLIENT
# =============================================================================

class ConfluenceClient:
    """Confluence API client with retry logic and rate limiting."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self._setup_auth()
    
    def _setup_auth(self):
        """Configure authentication headers."""
        if self.config.auth_mode == "bearer":
            self.session.headers["Authorization"] = f"Bearer {self.config.api_token}"
        else:
            self.session.auth = (self.config.user_email, self.config.api_token)
        
        self.session.headers["Accept"] = "application/json"
        self.session.headers["Content-Type"] = "application/json"
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        if self.config.rate_limit_ms > 0:
            time.sleep(self.config.rate_limit_ms / 1000)
    
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make an HTTP request with retry logic."""
        self._rate_limit()
        
        retry_delay = self.config.retry_delay
        
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self.session.request(
                    method, url,
                    timeout=self.config.timeout,
                    **kwargs
                )
                
                # Retry on 5xx errors or rate limiting
                if response.status_code >= 500 or response.status_code == 429:
                    if attempt < self.config.max_retries:
                        log_debug(f"Request failed (HTTP {response.status_code}), retry {attempt}/{self.config.max_retries} in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < self.config.max_retries:
                    log_debug(f"Request failed ({e}), retry {attempt}/{self.config.max_retries} in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise
        
        return response
    
    def get_space_id(self) -> str:
        """Look up space ID from space key."""
        if self.config._space_id:
            return self.config._space_id
        
        log_info(f"Looking up space ID for key: {self.config.space_key}")
        
        url = f"{self.config.base_url}/api/v2/spaces?keys={self.config.space_key}"
        response = self._request("GET", url)
        
        if response.status_code != 200:
            log_error(f"Failed to look up space (HTTP {response.status_code})")
            log_error(f"Response: {response.text}")
            sys.exit(2)
        
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            log_error(f"Could not find space with key: {self.config.space_key}")
            sys.exit(2)
        
        self.config._space_id = results[0]["id"]
        log_info(f"Space ID: {self.config._space_id}")
        return self.config._space_id
    
    def verify_parent_page(self, parent_id: str, parent_name: str) -> bool:
        """Verify a parent page exists."""
        if not parent_id:
            log_error(f"Parent page ID is empty for: {parent_name}")
            return False
        
        log_debug(f"Verifying parent page exists: {parent_id} ({parent_name})")
        
        url = f"{self.config.base_url}/api/v2/pages/{parent_id}"
        response = self._request("GET", url)
        
        if response.status_code == 200:
            data = response.json()
            actual_title = data.get("title", "")
            log_debug(f"Parent page verified: {actual_title} (ID: {parent_id})")
            return True
        elif response.status_code == 404:
            log_error(f"Parent page not found: {parent_id} ({parent_name})")
            return False
        else:
            log_error(f"Failed to verify parent page (HTTP {response.status_code}): {parent_id}")
            return False
    
    def get_page_id(self, title: str) -> Optional[str]:
        """Get page ID by title."""
        space_id = self.get_space_id()
        encoded_title = quote(title)
        
        url = f"{self.config.base_url}/api/v2/pages?title={encoded_title}&space-id={space_id}&status=current"
        log_debug(f"Looking up page: {url}")
        
        response = self._request("GET", url)
        
        if response.status_code != 200:
            log_warn(f"Failed to look up page (HTTP {response.status_code})")
            return None
        
        data = response.json()
        results = data.get("results", [])
        
        if results:
            return results[0]["id"]
        return None
    
    def get_page_version(self, page_id: str) -> int:
        """Get current version number of a page."""
        url = f"{self.config.base_url}/api/v2/pages/{page_id}"
        response = self._request("GET", url)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("version", {}).get("number", 1)
        return 1
    
    def create_page(self, title: str, content: str, parent_id: str) -> Optional[str]:
        """Create a new Confluence page."""
        space_id = self.get_space_id()
        
        payload = {
            "spaceId": space_id,
            "status": "current",
            "title": title,
            "parentId": parent_id,
            "body": {
                "representation": "storage",
                "value": content
            }
        }
        
        log_debug(f"Create payload: spaceId={space_id}, title={title}, parentId={parent_id}")
        
        url = f"{self.config.base_url}/api/v2/pages"
        response = self._request("POST", url, json=payload)
        
        if response.status_code in (200, 201):
            data = response.json()
            return data.get("id")
        else:
            log_error(f"Failed to create page (HTTP {response.status_code})")
            try:
                log_error(f"Response: {response.json().get('message', response.text)}")
            except Exception:
                log_error(f"Response: {response.text}")
            return None
    
    def update_page(self, page_id: str, title: str, content: str, version: int) -> bool:
        """Update an existing Confluence page."""
        payload = {
            "id": page_id,
            "status": "current",
            "title": title,
            "body": {
                "representation": "storage",
                "value": content
            },
            "version": {
                "number": version,
                "message": "Automated sync from repository"
            }
        }
        
        url = f"{self.config.base_url}/api/v2/pages/{page_id}"
        response = self._request("PUT", url, json=payload)
        
        if response.status_code == 200:
            return True
        else:
            log_error(f"Failed to update page (HTTP {response.status_code})")
            try:
                log_error(f"Response: {response.json().get('message', response.text)}")
            except Exception:
                log_error(f"Response: {response.text}")
            return False
    
    def upload_attachment(self, page_id: str, file_path: Path) -> Optional[str]:
        """Upload an attachment to a Confluence page."""
        if not file_path.exists():
            log_warn(f"    Attachment file not found: {file_path}")
            return None
        
        filename = file_path.name
        log_debug(f"    Uploading attachment: {filename}")
        
        # Check if attachment already exists
        check_url = f"{self.config.base_url}/rest/api/content/{page_id}/child/attachment?filename={filename}"
        check_response = self._request("GET", check_url)
        
        existing_id = None
        if check_response.status_code == 200:
            data = check_response.json()
            results = data.get("results", [])
            if results:
                existing_id = results[0]["id"]
        
        # Prepare multipart upload
        headers = {"X-Atlassian-Token": "nocheck"}
        # Remove Content-Type for multipart
        upload_headers = {k: v for k, v in self.session.headers.items() if k.lower() != "content-type"}
        upload_headers.update(headers)
        
        with open(file_path, "rb") as f:
            files = {"file": (filename, f)}
            
            if existing_id:
                log_debug(f"    Updating existing attachment: {existing_id}")
                url = f"{self.config.base_url}/rest/api/content/{page_id}/child/attachment/{existing_id}/data"
            else:
                log_debug("    Creating new attachment")
                url = f"{self.config.base_url}/rest/api/content/{page_id}/child/attachment"
            
            # Use session auth but custom headers
            response = self.session.post(
                url, files=files, headers=upload_headers,
                timeout=self.config.timeout
            )
        
        log_debug(f"    HTTP status: {response.status_code}")
        
        if response.status_code in (200, 201):
            data = response.json()
            results = data.get("results", [data])
            if results:
                att_filename = results[0].get("title", filename)
                log_debug(f"    Uploaded: {att_filename}")
                return att_filename
        
        log_warn(f"    Failed to upload attachment: {filename} (HTTP {response.status_code})")
        return None


# =============================================================================
# IMAGE PROCESSING
# =============================================================================

def extract_images(content: str) -> List[Tuple[str, str, str]]:
    """Extract image references from markdown.
    
    Returns list of (full_match, alt_text, path) tuples.
    """
    pattern = r'(!\[([^\]]*)\]\(([^)]+)\))'
    return re.findall(pattern, content)


def process_images(content: str, md_file: Path, page_id: str, 
                   client: ConfluenceClient, config: Config) -> str:
    """Process markdown content: upload images and replace with Confluence macros."""
    md_dir = md_file.parent.resolve()
    images = extract_images(content)
    
    if not images:
        return content
    
    log_info("  Processing images...")
    
    for full_match, alt_text, img_path in images:
        # Skip external URLs
        if img_path.startswith(('http://', 'https://')):
            log_debug(f"    Skipping external image: {img_path}")
            continue
        
        # Resolve relative path
        if img_path.startswith('/'):
            full_path = Path(img_path).resolve()
        else:
            full_path = (md_dir / img_path).resolve()
        
        # Security: prevent path traversal outside markdown directory
        try:
            full_path.relative_to(md_dir)
        except ValueError:
            log_warn(f"    Blocked path traversal attempt: {img_path}")
            content = handle_image_failure(content, full_match, alt_text, img_path, config, "blocked (path traversal)")
            continue
        
        if full_path.exists():
            if config.dry_run:
                log_info(f"    [DRY-RUN] Would upload: {full_path.name}")
                att_filename = full_path.name
            else:
                att_filename = client.upload_attachment(page_id, full_path)
            
            if att_filename:
                # Replace markdown image with Confluence ac:image macro
                confluence_img = f'<ac:image ac:width="{config.max_image_width}" ac:alt="{alt_text}"><ri:attachment ri:filename="{att_filename}" /></ac:image>'
                content = content.replace(full_match, confluence_img)
                log_info(f"    Replaced: {img_path} -> {att_filename}")
            else:
                content = handle_image_failure(content, full_match, alt_text, img_path, config, "upload failed")
        else:
            content = handle_image_failure(content, full_match, alt_text, img_path, config, "not found")
    
    return content


def handle_image_failure(content: str, full_match: str, alt_text: str, 
                         img_path: str, config: Config, reason: str) -> str:
    """Handle image processing failure based on config."""
    behavior = config.image_failure_behavior
    
    if behavior == "placeholder":
        macro_type = "warning" if reason == "not found" else "info"
        placeholder = f'<ac:structured-macro ac:name="{macro_type}"><ac:rich-text-body><p>[Image {reason}: {alt_text or img_path}]</p></ac:rich-text-body></ac:structured-macro>'
        content = content.replace(full_match, placeholder)
        log_warn(f"    Image {reason}, using placeholder: {img_path}")
    elif behavior == "skip":
        content = content.replace(full_match, "")
        log_warn(f"    Image {reason}, removed: {img_path}")
    elif behavior == "fail":
        log_error(f"    Image {reason}: {img_path}")
        raise RuntimeError(f"Image {reason}: {img_path}")
    
    return content


# =============================================================================
# PAGE SYNC
# =============================================================================

def sanitize_title(title: str, config: Config) -> str:
    """Sanitize page title based on config."""
    behavior = config.title_special_chars
    
    if behavior == "sanitize":
        title = re.sub(config.title_strip_pattern, '-', title)
        title = re.sub(r'--+', '-', title)
        title = title.strip('-')
    elif behavior == "encode":
        title = quote(title)
    elif behavior == "fail":
        if re.search(config.title_strip_pattern, title):
            raise ValueError(f"Title contains special characters: {title}")
    
    return title


def sync_page(title: str, md_file: str, parent_id: str, 
              client: ConfluenceClient, config: Config) -> bool:
    """Create or update a Confluence page."""
    # Sanitize title
    original_title = title
    title = sanitize_title(title, config)
    if title != original_title:
        log_debug(f"Title sanitized: '{original_title}' -> '{title}'")
    
    md_path = Path(md_file)
    
    # Handle missing files
    if not md_path.exists():
        if config.missing_file_behavior == "skip":
            log_warn(f"File not found (skipping): {md_file}")
            return True
        else:
            log_error(f"File not found: {md_file}")
            return False
    
    log_info(f"Syncing: {title} from {md_file}")
    
    if config.dry_run:
        log_info(f"  [DRY-RUN] Would sync to parent ID: {parent_id}")
        return True
    
    # Check if page exists
    page_id = client.get_page_id(title)
    
    if page_id:
        log_info(f"  Page exists (ID: {page_id}), updating...")
        
        # Process images first (needs page_id for uploads)
        content = md_path.read_text()
        content = process_images(content, md_path, page_id, client, config)
        content = convert_markdown_to_confluence(content, md_file, config)
        
        # Get current version
        version = client.get_page_version(page_id)
        log_debug(f"  Current version: {version}")
        
        # Update page
        if client.update_page(page_id, title, content, version + 1):
            log_info("  Updated successfully")
            return True
        else:
            return False
    else:
        log_info("  Page does not exist, creating...")
        
        # Create page first (without images)
        content = md_path.read_text()
        initial_content = convert_markdown_to_confluence(content, md_file, config)
        
        new_page_id = client.create_page(title, initial_content, parent_id)
        
        if new_page_id:
            log_info(f"  Created successfully (ID: {new_page_id})")
            
            # Now process images and update the page
            images = extract_images(content)
            
            if images:
                log_info("  Processing images for new page...")
                content = process_images(content, md_path, new_page_id, client, config)
                content = convert_markdown_to_confluence(content, md_file, config)
                
                # Update with images
                client.update_page(new_page_id, title, content, 2)
                log_info("  Images processed")
            
            return True
        else:
            return False


def sync_from_config(client: ConfluenceClient, config: Config) -> bool:
    """Sync all documents from config."""
    if not config.documents:
        log_error("No document mappings found in config")
        log_error("Please define CONFLUENCE_DOC_* mappings in .confluence-sync.conf")
        log_error("")
        log_error("Example format:")
        log_error('  CONFLUENCE_DOC_MYPAGE="Page Title|path/to/file.md|parent_page_id"')
        return False
    
    sync_errors = 0
    synced_count = 0
    
    for doc_key, (title, path, parent_id) in config.documents.items():
        if not title or not path or not parent_id:
            log_warn(f"Invalid mapping for {doc_key}: missing title, path, or parent_id")
            continue
        
        if not sync_page(title, path, parent_id, client, config):
            sync_errors += 1
        synced_count += 1
    
    log_info(f"Synced {synced_count} documents with {sync_errors} error(s)")
    
    return sync_errors == 0


def list_documents(config: Config):
    """List configured documents."""
    if not config.documents:
        log_warn("No CONFLUENCE_DOC_* mappings found in config")
        log_info("Define mappings in .confluence-sync.conf like:")
        log_info('  CONFLUENCE_DOC_README="README|README.md|parent_page_id"')
        return False
    
    log_info("Configured document mappings:")
    print()
    print(f"{'TITLE':<40} {'PATH':<50} {'PARENT_ID':<15} {'EXISTS'}")
    print(f"{'-----':<40} {'----':<50} {'---------':<15} {'------'}")
    
    for doc_key, (title, path, parent_id) in config.documents.items():
        exists = "✓" if Path(path).exists() else "✗"
        print(f"{title:<40} {path:<50} {parent_id:<15} {exists}")
    
    print()
    return True


# =============================================================================
# MAIN
# =============================================================================

def check_env(config: Config) -> bool:
    """Check required configuration settings."""
    log_info("Checking required configuration...")
    
    missing = []
    
    # Check all required settings
    if not config.api_token:
        missing.append("CONFLUENCE_API_TOKEN")
    
    if not config.base_url:
        missing.append("CONFLUENCE_BASE_URL")
    
    if not config.space_key:
        missing.append("CONFLUENCE_SPACE_KEY")
    
    if config.auth_mode == "basic" and not config.user_email:
        missing.append("CONFLUENCE_USER_EMAIL (required for basic auth)")
    
    # Report all missing settings at once
    if missing:
        log_error("Missing required configuration:")
        for item in missing:
            log_error(f"  - {item}")
        log_error("")
        log_error("Set these via environment variables or in .confluence-sync.conf")
        return False
    
    # Log successful configuration
    log_info(f"Auth mode: {config.auth_mode}")
    log_debug(f"CONFLUENCE_API_TOKEN: [set, {len(config.api_token)} chars]")
    if config.user_email:
        log_debug(f"CONFLUENCE_USER_EMAIL: {config.user_email}")
    log_debug(f"CONFLUENCE_BASE_URL: {config.base_url}")
    log_debug(f"CONFLUENCE_SPACE_KEY: {config.space_key}")
    log_debug(f"CONFLUENCE_TECH_PARENT_ID: {config.tech_parent_id or '(not set)'}")
    log_debug(f"CONFLUENCE_USER_PARENT_ID: {config.user_parent_id or '(not set)'}")
    
    log_info("Configuration OK")
    return True


def main():
    global _verbose
    
    parser = argparse.ArgumentParser(
        description="Sync documentation from repository to Confluence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  CONFLUENCE_API_TOKEN      API token for authentication (required)
  CONFLUENCE_USER_EMAIL     User email for authentication (required for basic auth)
  CONFLUENCE_AUTH_MODE      Auth mode: basic, bearer, or auto (default: auto)
  CONFLUENCE_BASE_URL       Confluence base URL
  CONFLUENCE_SPACE_KEY      Space key (e.g., ITS)

Edge case behaviors (set in config):
  CONFLUENCE_MISSING_FILE_BEHAVIOR   skip|fail (default: skip)
  CONFLUENCE_IMAGE_FAILURE_BEHAVIOR  placeholder|skip|fail (default: placeholder)
  CONFLUENCE_TITLE_SPECIAL_CHARS     sanitize|encode|fail (default: sanitize)
"""
    )
    
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be synced without making changes")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("--config", default=".confluence-sync.conf",
                        help="Config file path (default: .confluence-sync.conf)")
    parser.add_argument("--list", action="store_true",
                        help="List configured documents and exit")
    parser.add_argument("--verify", action="store_true",
                        help="Verify config and connectivity, don't sync")
    parser.add_argument("--single", nargs=3, metavar=("TITLE", "PATH", "PARENT_ID"),
                        help="Sync a single document")
    parser.add_argument("--stdin", nargs="?", const="", metavar="FILENAME",
                        help="Read markdown from stdin and convert (for md2confluence.py compatibility)")
    
    args = parser.parse_args()
    
    _verbose = args.verbose
    
    # Handle --stdin for backward compatibility with md2confluence.py
    if args.stdin is not None:
        content = sys.stdin.read()
        result = convert_markdown_to_confluence(content, args.stdin or "")
        print(result)
        return 0
    
    # Load configuration
    config = load_config(args.config)
    config.dry_run = args.dry_run
    config.verbose = args.verbose
    
    # Handle --list option early (doesn't need auth)
    if args.list:
        return 0 if list_documents(config) else 1
    
    log_info("Starting Confluence documentation sync...")
    log_info(f"Base URL: {config.base_url}")
    log_info(f"Space Key: {config.space_key}")
    
    if config.dry_run:
        log_warn("DRY-RUN mode - no changes will be made")
    if config.verbose:
        log_info("Verbose mode enabled")
    
    # Check environment
    if not check_env(config):
        return 1
    
    # Create API client
    client = ConfluenceClient(config)
    
    # Validate space exists
    log_info("Validating Confluence space...")
    client.get_space_id()
    
    # Verify parent pages exist
    log_info("Verifying parent pages...")
    parent_errors = 0
    
    if not client.verify_parent_page(config.tech_parent_id, "Technical Documentation"):
        parent_errors += 1
    
    if not client.verify_parent_page(config.user_parent_id, "User Documentation"):
        parent_errors += 1
    
    if parent_errors > 0:
        log_error("Parent page verification failed. Check page IDs in config.")
        return 4
    
    # Handle --verify option
    if args.verify:
        log_info("Verification complete - all checks passed")
        return 0
    
    # Handle --single option
    if args.single:
        title, path, parent_id = args.single
        log_info(f"Syncing single document: {title}")
        if sync_page(title, path, parent_id, client, config):
            log_info("=== Sync Complete ===")
            return 0
        else:
            return 3
    
    # Sync from config
    if not sync_from_config(client, config):
        return 3
    
    log_info("=== Sync Complete ===")
    log_info("All pages synced successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
