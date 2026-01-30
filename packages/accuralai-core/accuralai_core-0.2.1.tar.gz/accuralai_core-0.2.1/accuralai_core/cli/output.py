"""CLI output helpers with enhanced formatting."""

from __future__ import annotations

import json
import re
from typing import Optional

from ..contracts.models import GenerateResponse


class ColorTheme:
    """Color theme for terminal output."""
    
    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Colors
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    
    # Background colors
    BG_BLUE = "\033[104m"
    BG_GREEN = "\033[102m"
    BG_YELLOW = "\033[103m"
    BG_RED = "\033[101m"
    
    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{color}{text}{cls.RESET}"
    
    @classmethod
    def bold(cls, text: str) -> str:
        """Make text bold."""
        return f"{cls.BOLD}{text}{cls.RESET}"
    
    @classmethod
    def dim(cls, text: str) -> str:
        """Make text dim."""
        return f"{cls.DIM}{text}{cls.RESET}"


class MonochromeTheme(ColorTheme):
    """Monochrome theme for terminal output."""
    
    # Override colors with monochrome equivalents
    BLUE = "\033[90m"      # Gray
    GREEN = "\033[90m"     # Gray
    YELLOW = "\033[90m"    # Gray
    RED = "\033[90m"       # Gray
    MAGENTA = "\033[90m"   # Gray
    CYAN = "\033[90m"      # Gray
    WHITE = "\033[97m"     # White
    GRAY = "\033[90m"      # Gray


class HighContrastTheme(ColorTheme):
    """High contrast theme for terminal output."""
    
    # Override colors with high contrast equivalents
    BLUE = "\033[94m"      # Bright blue
    GREEN = "\033[92m"     # Bright green
    YELLOW = "\033[93m"    # Bright yellow
    RED = "\033[91m"       # Bright red
    MAGENTA = "\033[95m"   # Bright magenta
    CYAN = "\033[96m"      # Bright cyan
    WHITE = "\033[97m"     # Bright white
    GRAY = "\033[90m"      # Gray


class PastelTheme(ColorTheme):
    """Pastel theme for terminal output."""
    
    # Override colors with pastel equivalents
    BLUE = "\033[94m"      # Light blue
    GREEN = "\033[92m"     # Light green
    YELLOW = "\033[93m"    # Light yellow
    RED = "\033[91m"       # Light red
    MAGENTA = "\033[95m"   # Light magenta
    CYAN = "\033[96m"      # Light cyan
    WHITE = "\033[97m"     # White
    GRAY = "\033[90m"      # Light gray


def get_theme(theme_name: str) -> ColorTheme:
    """Get a theme instance by name."""
    themes = {
        "default": ColorTheme,
        "monochrome": MonochromeTheme,
        "high-contrast": HighContrastTheme,
        "pastel": PastelTheme,
    }
    return themes.get(theme_name, ColorTheme)()


class ResponseFormatter:
    """Enhanced response formatter with modern styling."""
    
    def __init__(self, theme: Optional[ColorTheme] = None, theme_name: str = "default"):
        self.theme = theme or get_theme(theme_name)
    
    def format_metadata_bar(self, response: GenerateResponse) -> str:
        """Format metadata information in a modern bar style."""
        parts = []
        
        # Status indicator
        status_color = self.theme.GREEN if response.finish_reason == "stop" else self.theme.YELLOW
        status = self.theme.colorize(f"* {response.finish_reason}", status_color)
        parts.append(status)
        
        # Cache status
        cache_status = response.metadata.get("cache_status", "unknown")
        if cache_status == "hit":
            cache_display = self.theme.colorize("Cache: HIT", self.theme.GREEN)
        elif cache_status == "miss":
            cache_display = self.theme.colorize("Cache: MISS", self.theme.YELLOW)
        elif cache_status == "disabled":
            cache_display = self.theme.colorize("Cache: OFF", self.theme.GRAY)
        else:
            cache_display = self.theme.colorize("Cache: ?", self.theme.GRAY)
        parts.append(cache_display)
        
        # Token savings from canonicalization
        canonicalize_metrics = response.metadata.get("canonicalize_metrics", {})
        cache_status = response.metadata.get("cache_status", "unknown")
        
        if cache_status == "hit":
            # For cache hits, show both canonicalizer savings and cache savings
            canonicalize_savings = canonicalize_metrics.get("tokens_saved", 0)
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            if canonicalize_savings > 0:
                savings_display = self.theme.colorize(
                    f"Saved: {canonicalize_savings} tokens (canonicalizer) + {total_tokens} tokens (cache hit)", 
                    self.theme.GREEN
                )
            else:
                savings_display = self.theme.colorize(
                    f"Saved: {total_tokens} tokens (cache hit)", 
                    self.theme.GREEN
                )
            parts.append(savings_display)
        elif canonicalize_metrics.get("tokens_saved", 0) > 0:
            # For cache misses, show only canonicalizer savings
            tokens_saved = canonicalize_metrics["tokens_saved"]
            compression_ratio = canonicalize_metrics.get("compression_ratio", 0)
            savings_display = self.theme.colorize(
                f"Saved: {tokens_saved} tokens ({compression_ratio:.1%})", 
                self.theme.GREEN
            )
            parts.append(savings_display)
        
        # Latency
        latency = self.theme.colorize(f"Latency: {response.latency_ms}ms", self.theme.CYAN)
        parts.append(latency)
        
        # Token usage
        if response.usage and response.usage.total_tokens:
            tokens = self.theme.colorize(f"Tokens: {response.usage.total_tokens}", self.theme.BLUE)
            parts.append(tokens)
        
        # Route info if available
        if hasattr(response, 'route_info') and response.route_info:
            route = self.theme.colorize(f"{response.route_info}", self.theme.MAGENTA)
            parts.append(route)
        
        return " | ".join(parts)
    
    def format_response_header(self, response: GenerateResponse) -> str:
        """Format response with modern header design."""
        metadata_bar = self.format_metadata_bar(response)
        
        # Calculate dynamic width based on content
        content_width = len(metadata_bar)
        # Ensure minimum width for readability
        min_width = 30
        border_width = max(content_width + 4, min_width)  # +4 for padding and borders
        
        # Create dynamic bordered header
        top_border = "+- Response " + "-" * (border_width - 13) + "+"
        content_line = f"| {metadata_bar:<{border_width - 4}} |"
        bottom_border = "+" + "-" * (border_width - 2) + "+"
        
        header_lines = [top_border, content_line, bottom_border]
        
        return "\n".join(header_lines)
    
    def highlight_code_blocks(self, text: str) -> str:
        """Add syntax highlighting to code blocks."""
        # Pattern to match code blocks
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        
        def replace_code_block(match):
            language = match.group(1) or "text"
            code = match.group(2)
            
            # Color the language tag
            lang_tag = self.theme.colorize(f"```{language}", self.theme.YELLOW)
            
            # Basic syntax highlighting for common languages
            highlighted_code = self._highlight_syntax(code, language)
            
            return f"{lang_tag}\n{highlighted_code}\n```"
        
        return re.sub(code_block_pattern, replace_code_block, text, flags=re.DOTALL)
    
    def _highlight_syntax(self, code: str, language: str) -> str:
        """Apply basic syntax highlighting based on language."""
        if language in ["python", "py"]:
            return self._highlight_python(code)
        elif language in ["javascript", "js", "typescript", "ts"]:
            return self._highlight_javascript(code)
        elif language in ["bash", "sh", "shell"]:
            return self._highlight_bash(code)
        elif language in ["json"]:
            return self._highlight_json(code)
        else:
            return code
    
    def _highlight_python(self, code: str) -> str:
        """Basic Python syntax highlighting."""
        lines = code.split('\n')
        highlighted = []
        
        for line in lines:
            # Keywords
            keywords = ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'return', 'try', 'except', 'finally', 'with', 'as']
            for keyword in keywords:
                line = re.sub(rf'\b{keyword}\b', self.theme.colorize(keyword, self.theme.BLUE), line)
            
            # Strings
            line = re.sub(r'"[^"]*"', self.theme.colorize(r'\g<0>', self.theme.GREEN), line)
            line = re.sub(r"'[^']*'", self.theme.colorize(r'\g<0>', self.theme.GREEN), line)
            
            # Comments
            line = re.sub(r'#.*$', self.theme.colorize(r'\g<0>', self.theme.GRAY), line)
            
            highlighted.append(line)
        
        return '\n'.join(highlighted)
    
    def _highlight_javascript(self, code: str) -> str:
        """Basic JavaScript syntax highlighting."""
        lines = code.split('\n')
        highlighted = []
        
        for line in lines:
            # Keywords
            keywords = ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'class', 'import', 'export']
            for keyword in keywords:
                line = re.sub(rf'\b{keyword}\b', self.theme.colorize(keyword, self.theme.BLUE), line)
            
            # Strings
            line = re.sub(r'"[^"]*"', self.theme.colorize(r'\g<0>', self.theme.GREEN), line)
            line = re.sub(r"'[^']*'", self.theme.colorize(r'\g<0>', self.theme.GREEN), line)
            
            # Comments
            line = re.sub(r'//.*$', self.theme.colorize(r'\g<0>', self.theme.GRAY), line)
            
            highlighted.append(line)
        
        return '\n'.join(highlighted)
    
    def _highlight_bash(self, code: str) -> str:
        """Basic Bash syntax highlighting."""
        lines = code.split('\n')
        highlighted = []
        
        for line in lines:
            # Commands
            if line.strip() and not line.startswith('#'):
                first_word = line.split()[0]
                line = re.sub(rf'^{re.escape(first_word)}', self.theme.colorize(first_word, self.theme.BLUE), line)
            
            # Comments
            line = re.sub(r'#.*$', self.theme.colorize(r'\g<0>', self.theme.GRAY), line)
            
            highlighted.append(line)
        
        return '\n'.join(highlighted)
    
    def _highlight_json(self, code: str) -> str:
        """Basic JSON syntax highlighting."""
        try:
            # Try to parse and pretty-print JSON
            parsed = json.loads(code)
            formatted = json.dumps(parsed, indent=2)
            
            lines = formatted.split('\n')
            highlighted = []
            
            for line in lines:
                # Keys
                line = re.sub(r'"([^"]+)":', self.theme.colorize(r'"\1":', self.theme.BLUE), line)
                
                # Strings
                line = re.sub(
                    r':\s*"([^"]*)"',
                    lambda m: ': ' + self.theme.colorize('"' + m.group(1) + '"', self.theme.GREEN),
                    line,
                )
                
                # Numbers
                line = re.sub(r':\s*(\d+\.?\d*)', lambda m: f': {self.theme.colorize(m.group(1), self.theme.YELLOW)}', line)
                
                highlighted.append(line)
            
            return '\n'.join(highlighted)
        except json.JSONDecodeError:
            return code
    
    def format_response_body(self, response: GenerateResponse) -> str:
        """Format the response body with enhanced styling."""
        text = response.output_text
        
        # Apply syntax highlighting
        highlighted_text = self.highlight_code_blocks(text)
        
        # Add subtle indentation for better readability
        lines = highlighted_text.split('\n')
        indented_lines = [f"  {line}" if line.strip() else line for line in lines]
        
        return '\n'.join(indented_lines)
    
    def format_full_response(self, response: GenerateResponse) -> str:
        """Format a complete response with header and body."""
        header = self.format_response_header(response)
        body = self.format_response_body(response)
        
        return f"{header}\n\n{body}"


def render_text(response: GenerateResponse, theme_name: str = "default") -> str:
    """Return a human-readable string for CLI display with enhanced formatting."""
    formatter = ResponseFormatter(theme_name=theme_name)
    return formatter.format_full_response(response)


def render_json(response: GenerateResponse) -> str:
    """Return a JSON string representation of the response."""
    data = response.model_dump(mode="json")
    return json.dumps(data, indent=2)


def render_compact(response: GenerateResponse, theme_name: str = "default") -> str:
    """Return a compact format for quick viewing."""
    formatter = ResponseFormatter(theme_name=theme_name)
    metadata = formatter.format_metadata_bar(response)
    body = response.output_text
    
    return f"{metadata}\n{body}"


def render_streaming_chunk(chunk: str, is_complete: bool = False) -> str:
    """Render a streaming response chunk."""
    if is_complete:
        return chunk
    else:
        return chunk
