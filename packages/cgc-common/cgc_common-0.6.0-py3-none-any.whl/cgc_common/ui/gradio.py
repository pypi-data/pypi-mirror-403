"""Gradio UI theme and CSS utilities for Cindergrace applications.

Provides consistent styling across all Cindergrace Gradio apps with:
- CSS variable system for easy customization
- Pre-built theme with Cindergrace branding
- Header builder with logo integration
"""

from dataclasses import dataclass, field


# Cindergrace Logo SVG (48x48 viewBox, scalable)
LOGO_SVG = '''<svg width="48" height="48" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" rx="96" fill="white"/>
  <circle cx="256" cy="256" r="200" stroke="#7CC8FF" stroke-width="36" fill="none"/>
  <path d="M 56 256 L 56 490" stroke="#7CC8FF" stroke-width="36" stroke-linecap="round"/>
  <path d="M 420 256 A 164 164 0 1 1 338 114" stroke="#1E5AA8" stroke-width="36" stroke-linecap="round"/>
  <path d="M 420 256 L 320 256" stroke="#1E5AA8" stroke-width="36" stroke-linecap="round"/>
  <path d="M 332 180 A 108 108 0 1 0 332 332" stroke="#7CC8FF" stroke-width="28" stroke-linecap="round"/>
</svg>'''


@dataclass
class CSSVariables:
    """CSS variables for Cindergrace theme.

    All colors and dimensions can be customized per-app while maintaining
    consistent branding across the suite.
    """
    # Brand colors
    blue_dark: str = "#1E5AA8"
    blue_light: str = "#7CC8FF"
    blue_hover: str = "#2d6fc0"

    # Background colors
    bg_primary: str = "#f8f9fc"
    bg_secondary: str = "#ffffff"
    bg_card: str = "#ffffff"
    bg_input: str = "#f4f6f8"

    # Text colors
    text_primary: str = "#1c2321"
    text_secondary: str = "#4a5568"
    text_muted: str = "#718096"

    # Status colors
    success: str = "#2ecc71"
    warning: str = "#f39c12"
    error: str = "#e74c3c"

    # Typography
    font_size_base: str = "17px"
    font_size_label: str = "16px"

    # Layout
    border_radius: str = "12px"
    max_width: str = "1200px"
    spacing: str = "20px"

    def to_css_vars(self) -> str:
        """Generate CSS :root block with all variables."""
        return f""":root {{
    --cg-blue-dark: {self.blue_dark};
    --cg-blue-light: {self.blue_light};
    --cg-blue-hover: {self.blue_hover};
    --cg-bg-primary: {self.bg_primary};
    --cg-bg-secondary: {self.bg_secondary};
    --cg-bg-card: {self.bg_card};
    --cg-bg-input: {self.bg_input};
    --cg-text-primary: {self.text_primary};
    --cg-text-secondary: {self.text_secondary};
    --cg-text-muted: {self.text_muted};
    --cg-success: {self.success};
    --cg-warning: {self.warning};
    --cg-error: {self.error};
    --cg-font-size-base: {self.font_size_base};
    --cg-font-size-label: {self.font_size_label};
    --cg-border-radius: {self.border_radius};
    --cg-max-width: {self.max_width};
    --cg-spacing: {self.spacing};
}}"""


def default_css_variables() -> CSSVariables:
    """Get default Cindergrace CSS variables."""
    return CSSVariables()


# Base CSS styles using variables
_BASE_STYLES = """
body, .gradio-container {
    background: linear-gradient(135deg, var(--cg-bg-primary) 0%, #eef1f5 100%) !important;
    color: var(--cg-text-primary) !important;
    font-family: "Nunito", "Segoe UI", system-ui, sans-serif !important;
    font-size: var(--cg-font-size-base) !important;
}

.gradio-container {
    max-width: var(--cg-max-width) !important;
    margin: 0 auto !important;
    padding: var(--cg-spacing) !important;
}

h1, h2, h3, .markdown-text h1, .markdown-text h2, .markdown-text h3 {
    font-family: "Comfortaa", sans-serif !important;
    color: var(--cg-blue-dark) !important;
    font-weight: 600 !important;
}

h1, .markdown-text h1 { font-size: 2em !important; }
h2, .markdown-text h2 {
    font-size: 1.4em !important;
    border-bottom: 2px solid var(--cg-blue-light);
    padding-bottom: 0.3em;
    margin-top: 1em !important;
}

.panel, .gr-group, .gr-box, .block {
    background: var(--cg-bg-card) !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: var(--cg-border-radius) !important;
    padding: var(--cg-spacing) !important;
    box-shadow: 0 4px 16px rgba(30, 90, 168, 0.08) !important;
    margin-bottom: var(--cg-spacing) !important;
}

label, .gr-input-label, .label-wrap, .label-wrap span {
    color: var(--cg-text-secondary) !important;
    font-size: var(--cg-font-size-label) !important;
    font-weight: 600 !important;
}

button, .gr-button {
    font-family: "Nunito", sans-serif !important;
    font-size: var(--cg-font-size-base) !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
}

button.primary, .gr-button.primary, button[variant="primary"] {
    background: linear-gradient(135deg, var(--cg-blue-dark) 0%, var(--cg-blue-hover) 100%) !important;
    color: white !important;
    border: none !important;
}

button.secondary, .gr-button.secondary {
    background: white !important;
    color: var(--cg-blue-dark) !important;
    border: 2px solid var(--cg-blue-dark) !important;
}

.app-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
}

.app-header svg { width: 48px; height: 48px; flex-shrink: 0; }
.app-header h1 { margin: 0 !important; font-size: 1.8em !important; }
.app-header .subtitle { color: var(--cg-text-muted); font-size: 0.95em; margin-top: 2px; }

table { font-size: 15px !important; }
th { background: var(--cg-bg-primary) !important; color: var(--cg-blue-dark) !important; font-weight: 600 !important; }
td { padding: 8px 12px !important; }
tr:hover { background: rgba(30, 90, 168, 0.03) !important; }
"""


@dataclass
class GradioTheme:
    """Complete Gradio theme for Cindergrace applications.

    Usage:
        theme = GradioTheme(title="My App", subtitle="Description")

        with gr.Blocks(css=theme.css()) as demo:
            gr.HTML(theme.header_html())
            # ... app content
    """
    title: str = "Cindergrace"
    subtitle: str = ""
    variables: CSSVariables = field(default_factory=CSSVariables)
    custom_css: str = ""
    logo_svg: str = LOGO_SVG

    def css(self) -> str:
        """Generate complete CSS including variables, base styles, and custom CSS."""
        parts = [
            self.variables.to_css_vars(),
            _BASE_STYLES,
        ]
        if self.custom_css:
            parts.append(self.custom_css)
        return "\n".join(parts)

    def header_html(self) -> str:
        """Generate header HTML with logo, title, and optional subtitle."""
        subtitle_html = ""
        if self.subtitle:
            subtitle_html = f'<div class="subtitle">{self.subtitle}</div>'

        return f"""<div class="app-header">
    {self.logo_svg}
    <div>
        <h1>{self.title}</h1>
        {subtitle_html}
    </div>
</div>"""


def build_header(
    title: str,
    subtitle: str = "",
    logo_svg: str = LOGO_SVG,
) -> str:
    """Build header HTML with Cindergrace branding.

    Args:
        title: Main title text
        subtitle: Optional subtitle/description
        logo_svg: Custom SVG logo (defaults to Cindergrace logo)

    Returns:
        HTML string for use in gr.HTML()
    """
    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<div class="subtitle">{subtitle}</div>'

    return f"""<div class="app-header">
    {logo_svg}
    <div>
        <h1>{title}</h1>
        {subtitle_html}
    </div>
</div>"""
