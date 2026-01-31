"""Tests for Gradio UI module."""

from cgc_common.ui.gradio import (
    CSSVariables,
    GradioTheme,
    LOGO_SVG,
    build_header,
    default_css_variables,
)


class TestCSSVariables:
    def test_default_values(self):
        css_vars = CSSVariables()
        assert css_vars.blue_dark == "#1E5AA8"
        assert css_vars.max_width == "1200px"
        assert css_vars.font_size_base == "17px"

    def test_custom_values(self):
        css_vars = CSSVariables(blue_dark="#FF0000", max_width="800px")
        assert css_vars.blue_dark == "#FF0000"
        assert css_vars.max_width == "800px"
        # Unchanged defaults
        assert css_vars.blue_light == "#7CC8FF"

    def test_to_css_vars(self):
        css_vars = CSSVariables()
        css = css_vars.to_css_vars()
        assert ":root {" in css
        assert "--cg-blue-dark: #1E5AA8" in css
        assert "--cg-max-width: 1200px" in css
        assert "--cg-font-size-base: 17px" in css

    def test_to_css_vars_custom(self):
        css_vars = CSSVariables(max_width="900px")
        css = css_vars.to_css_vars()
        assert "--cg-max-width: 900px" in css


class TestGradioTheme:
    def test_default_theme(self):
        theme = GradioTheme()
        assert theme.title == "Cindergrace"
        assert theme.subtitle == ""

    def test_custom_theme(self):
        theme = GradioTheme(title="My App", subtitle="Description")
        assert theme.title == "My App"
        assert theme.subtitle == "Description"

    def test_css_includes_variables(self):
        theme = GradioTheme()
        css = theme.css()
        assert ":root {" in css
        assert "--cg-blue-dark" in css

    def test_css_includes_base_styles(self):
        theme = GradioTheme()
        css = theme.css()
        assert ".gradio-container" in css
        assert ".app-header" in css
        assert "button.primary" in css

    def test_css_includes_custom_css(self):
        custom = ".my-class { color: red; }"
        theme = GradioTheme(custom_css=custom)
        css = theme.css()
        assert ".my-class { color: red; }" in css

    def test_css_custom_variables(self):
        css_vars = CSSVariables(max_width="800px")
        theme = GradioTheme(variables=css_vars)
        css = theme.css()
        assert "--cg-max-width: 800px" in css

    def test_header_html_basic(self):
        theme = GradioTheme(title="Test App")
        html = theme.header_html()
        assert '<div class="app-header">' in html
        assert "<h1>Test App</h1>" in html
        assert "svg" in html.lower()

    def test_header_html_with_subtitle(self):
        theme = GradioTheme(title="Test", subtitle="A description")
        html = theme.header_html()
        assert '<div class="subtitle">A description</div>' in html

    def test_header_html_without_subtitle(self):
        theme = GradioTheme(title="Test", subtitle="")
        html = theme.header_html()
        assert 'class="subtitle"' not in html

    def test_custom_logo(self):
        custom_logo = '<svg><circle/></svg>'
        theme = GradioTheme(logo_svg=custom_logo)
        html = theme.header_html()
        assert custom_logo in html


class TestBuildHeader:
    def test_basic_header(self):
        html = build_header("My Title")
        assert '<div class="app-header">' in html
        assert "<h1>My Title</h1>" in html

    def test_header_with_subtitle(self):
        html = build_header("Title", subtitle="Subtitle text")
        assert "Subtitle text" in html
        assert 'class="subtitle"' in html

    def test_header_without_subtitle(self):
        html = build_header("Title", subtitle="")
        assert 'class="subtitle"' not in html

    def test_custom_logo(self):
        custom = '<svg id="custom"></svg>'
        html = build_header("Title", logo_svg=custom)
        assert 'id="custom"' in html


class TestDefaultCSSVariables:
    def test_returns_css_variables(self):
        css_vars = default_css_variables()
        assert isinstance(css_vars, CSSVariables)
        assert css_vars.blue_dark == "#1E5AA8"


class TestLogoSVG:
    def test_logo_is_svg(self):
        assert "<svg" in LOGO_SVG
        assert "</svg>" in LOGO_SVG

    def test_logo_has_viewbox(self):
        assert 'viewBox="0 0 512 512"' in LOGO_SVG

    def test_logo_has_cindergrace_colors(self):
        assert "#7CC8FF" in LOGO_SVG  # Light blue
        assert "#1E5AA8" in LOGO_SVG  # Dark blue
