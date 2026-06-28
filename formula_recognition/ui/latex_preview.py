import html

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # pragma: no cover - only used on incomplete Qt installs
    QWebEngineView = None


MATHJAX_SCRIPT_URL = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"
MATHJAX_BASE_URL = QUrl("https://cdn.jsdelivr.net/")
DISPLAY_ENVIRONMENTS = {
    "align",
    "align*",
    "equation",
    "equation*",
    "flalign",
    "flalign*",
    "gather",
    "gather*",
    "multline",
    "multline*",
}


class LatexPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "previewCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(120)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        if QWebEngineView is not None:
            self.viewer = QWebEngineView()
            self.viewer.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            self._uses_web_engine = True
        else:
            self.viewer = QTextBrowser()
            self.viewer.setOpenExternalLinks(False)
            self._uses_web_engine = False

        layout.addWidget(self.viewer)
        self.set_latex("")

    def set_latex(self, latex: str) -> None:
        document = render_latex_preview_html(latex)
        if self._uses_web_engine:
            self.viewer.setHtml(document, MATHJAX_BASE_URL)
        else:
            self.viewer.setHtml(document)


def render_latex_preview_html(latex: str) -> str:
    latex = _strip_math_delimiters(latex.strip())
    if not latex:
        return _render_empty_preview_html()

    math_body = _format_math_body(latex)
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    html,
    body {{
      margin: 0;
      min-height: 100%;
      background: #ffffff;
      color: #111827;
      font-family: "Cambria Math", "Times New Roman", serif;
    }}

    body {{
      box-sizing: border-box;
      padding: 12px 14px;
      overflow-wrap: anywhere;
    }}

    #preview {{
      min-height: 80px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 21px;
      line-height: 1.5;
    }}

    mjx-container {{
      overflow-x: auto;
      overflow-y: hidden;
      max-width: 100%;
      padding: 4px 0;
    }}

    .fallback {{
      white-space: pre-wrap;
      color: #475569;
      font-family: Consolas, "Courier New", monospace;
      font-size: 13px;
    }}
  </style>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [["\\\\(", "\\\\)"], ["$", "$"]],
        displayMath: [["\\\\[", "\\\\]"], ["$$", "$$"]],
        processEscapes: true,
        processEnvironments: true,
        packages: {{"[+]": ["ams", "autoload", "boldsymbol", "color", "newcommand", "noerrors", "noundefined"]}}
      }},
      svg: {{
        fontCache: "global",
        scale: 1.05
      }},
      startup: {{
        typeset: true
      }}
    }};
  </script>
  <script defer src="{MATHJAX_SCRIPT_URL}"></script>
</head>
<body>
  <main id="preview">{math_body}</main>
</body>
</html>"""


def _render_empty_preview_html() -> str:
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    html,
    body {
      margin: 0;
      min-height: 100%;
      background: #ffffff;
      color: #64748b;
      font-family: "Segoe UI", sans-serif;
    }

    body {
      box-sizing: border-box;
      padding: 12px 14px;
    }

    #preview {
      min-height: 80px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <main id="preview">暂无公式预览</main>
</body>
</html>"""


def _strip_math_delimiters(value: str) -> str:
    pairs = (("$$", "$$"), (r"\[", r"\]"), (r"\(", r"\)"), ("$", "$"))
    for start, end in pairs:
        if value.startswith(start) and value.endswith(end):
            return value[len(start) : len(value) - len(end)].strip()
    return value


def _format_math_body(latex: str) -> str:
    escaped_latex = html.escape(latex)
    if _read_top_level_environment(latex) in DISPLAY_ENVIRONMENTS:
        return escaped_latex
    return f"\\[{escaped_latex}\\]"


def _read_top_level_environment(latex: str) -> str:
    stripped = latex.lstrip()
    prefix = r"\begin{"
    if not stripped.startswith(prefix):
        return ""

    end_index = stripped.find("}", len(prefix))
    if end_index == -1:
        return ""
    return stripped[len(prefix) : end_index]
