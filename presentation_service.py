"""
Presentation Service - Professional formatting for SkyModderAI responses.

Provides:
- LaTeX formatting for responses
- PDF export (via WeasyPrint or LaTeX)
- HTML export (self-contained with embedded CSS)
- Markdown formatting with academic-grade citations

All exports include:
- Version badges
- Conflict warnings
- Credibility scores
- Source citations
"""

import html
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LaTeXFormatter:
    """Format responses as LaTeX documents."""

    # LaTeX document template
    DOCUMENT_TEMPLATE = (
        r"""
\documentclass[11pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{tcolorbox}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{xcolor}

% Colors
\definecolor{primary}{RGB}{59, 130, 246}
\definecolor{success}{RGB}{34, 197, 94}
\definecolor{warning}{RGB}{251, 191, 36}
\definecolor{error}{RGB}{239, 68, 68}

% Geometry
\geometry{
    top=2.5cm,
    bottom=2.5cm,
    left=2.5cm,
    right=2.5cm
}

% Hyperlinks
\hypersetup{
    colorlinks=true,
    linkcolor=primary,
    filecolor=magenta,
    urlcolor=primary,
    citecolor=primary
}

% Header/Footer
\pagestyle{fancy}
\fancyhf{}
\rhead{SkyModderAI}
\lhead{\leftmark}
\rfoot{Page \thepage\ of \pageref{LastPage}}

% Custom boxes
\newtcolorbox{infobox}[1][]{
    colback=primary!10,
    colframe=primary,
    title=#1,
    boxrule=1pt
}

\newtcolorbox{warningbox}[1][]{
    colback=warning!10,
    colframe=warning,
    title=#1,
    boxrule=1pt
}

\newtcolorbox{errorbox}[1][]{
    colback=error!10,
    colframe=error,
    title=#1,
    boxrule=1pt
}

\newtcolorbox{successbox}[1][]{
    colback=success!10,
    colframe=success,
    title=#1,
    boxrule=1pt
}

% Title
\title{\textbf{\Large """
        + "{{title}}"
        + r"""}}
\author{SkyModderAI Intelligence Engine}
\date{"""
        + "{{date}}"
        + r"""}

\begin{document}

\maketitle

\tableofcontents
\newpage

"""
        + "{{content}}"
        + r"""

\end{document}
"""
    )

    @classmethod
    def format_response(cls, content: Dict[str, Any]) -> str:
        """
        Format a response as LaTeX.

        Args:
            content: Response content with sections, warnings, etc.

        Returns:
            LaTeX formatted string
        """
        title = content.get("title", "SkyModderAI Guide")
        date = datetime.now().strftime("%B %d, %Y")

        # Build content sections
        latex_content = []

        # Executive summary
        if content.get("summary"):
            latex_content.append(cls._create_section("Executive Summary", content["summary"]))

        # Warnings (high priority first)
        if content.get("warnings"):
            latex_content.append(cls._create_warnings(content["warnings"]))

        # Main content sections
        for section in content.get("sections", []):
            latex_content.append(
                cls._create_section(
                    section.get("title", "Section"),
                    section.get("content", ""),
                    section.get("subsection", False),
                )
            )

        # Recommendations
        if content.get("recommendations"):
            latex_content.append(cls._create_recommendations(content["recommendations"]))

        # Sources
        if content.get("sources"):
            latex_content.append(cls._create_sources(content["sources"]))

        # Combine
        full_content = "\n\n".join(latex_content)

        # Fill template
        doc = cls.DOCUMENT_TEMPLATE
        doc = doc.replace("{{title}}", cls._escape(title))
        doc = doc.replace("{{date}}", date)
        doc = doc.replace("{{content}}", full_content)

        return doc

    @classmethod
    def _create_section(cls, title: str, content: str, subsection: bool = False) -> str:
        """Create a LaTeX section."""
        cmd = "subsection" if subsection else "section"
        return f"\\{cmd}{{{cls._escape(title)}}}\n\n{cls._format_content(content)}"

    @classmethod
    def _create_warnings(cls, warnings: List[Dict[str, Any]]) -> str:
        """Create warning boxes."""
        latex = "\\section{⚠️ Important Warnings}\n\n"

        for warning in warnings:
            level = warning.get("level", "warning")
            message = warning.get("message", "")

            if level == "error" or level == "high":
                box_type = "errorbox"
                icon = "❌"
            elif level == "warning" or level == "medium":
                box_type = "warningbox"
                icon = "⚠️"
            else:
                box_type = "infobox"
                icon = "ℹ️"

            latex += f"\\begin{{{box_type}}}[{icon} {cls._escape(message)}]\n"

            if warning.get("details"):
                latex += "\\begin{itemize}\n"
                for detail in warning["details"]:
                    latex += f"  \\item {cls._escape(detail)}\n"
                latex += "\\end{itemize}\n"

            latex += f"\\end{{{box_type}}}\n\n"

        return latex

    @classmethod
    def _create_recommendations(cls, recommendations: List[Dict[str, Any]]) -> str:
        """Create recommendations section."""
        latex = "\\section{✅ Recommendations}\n\n"
        latex += "\\begin{enumerate}[label=\\textbf{\\arabic*.}]\n"

        for rec in recommendations:
            priority = rec.get("priority", "normal")
            content = rec.get("content", "")

            priority_marker = ""
            if priority == "high":
                priority_marker = "\\textcolor{error}{\\textbf{[HIGH PRIORITY]}} "
            elif priority == "medium":
                priority_marker = "\\textcolor{warning}{\\textbf{[MEDIUM]}} "

            latex += f"  \\item {priority_marker}{cls._escape(content)}\n"

        latex += "\\end{enumerate}\n"
        return latex

    @classmethod
    def _create_sources(cls, sources: List[Dict[str, Any]]) -> str:
        """Create sources/bibliography section."""
        latex = "\\section{📚 Sources}\n\n"
        latex += "\\begin{itemize}\n"

        for source in sources:
            title = source.get("title", "Unknown")
            url = source.get("url", "")
            credibility = source.get("credibility_score", 0)

            # Credibility indicator
            if credibility >= 0.8:
                cred_badge = "\\textcolor{success}{★★★}"
            elif credibility >= 0.6:
                cred_badge = "\\textcolor{warning}{★★☆}"
            else:
                cred_badge = "\\textcolor{error}{★☆☆}"

            latex += f"  \\item {cred_badge} {cls._escape(title)}"
            if url:
                latex += f" \\href{{{url}}}{{[Link]}}"
            latex += "\n"

        latex += "\\end{itemize}\n"
        return latex

    @classmethod
    def _format_content(cls, content: str) -> str:
        """Format markdown-like content as LaTeX."""
        if not content:
            return ""

        # Convert markdown to LaTeX
        # Bold
        content = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", content)
        # Italic
        content = re.sub(r"\*(.+?)\*", r"\\textit{\1}", content)
        # Code
        content = re.sub(r"`(.+?)`", r"\\texttt{\1}", content)
        # Lists
        content = re.sub(
            r"^- (.+)$",
            r"\\begin{itemize}\n  \\item \1\n\\end{itemize}",
            content,
            flags=re.MULTILINE,
        )
        # Numbered lists
        content = re.sub(
            r"^(\d+)\. (.+)$",
            r"\\begin{enumerate}\n  \\item \2\n\\end{enumerate}",
            content,
            flags=re.MULTILINE,
        )
        # Line breaks
        content = content.replace("\n\n", "\\par\n\n")

        return content

    @classmethod
    def _escape(cls, text: str) -> str:
        """Escape special LaTeX characters."""
        if not text:
            return ""

        special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
            "\\": r"\textbackslash{}",
        }

        for char, escape in special_chars.items():
            text = text.replace(char, escape)

        return text


class HTMLFormatter:
    """Format responses as self-contained HTML documents."""

    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="document">
        <header class="header">
            <h1 class="title">{title}</h1>
            <p class="meta">Generated by SkyModderAI on {date}</p>
        </header>
        
        {content}
        
        <footer class="footer">
            <p>SkyModderAI Intelligence Engine • skymoddereai.com</p>
        </footer>
    </div>
</body>
</html>
"""

    CSS_STYLES = """
:root {
    --primary: #3b82f6;
    --success: #22c55e;
    --warning: #fbbf24;
    --error: #ef4444;
    --bg-primary: #ffffff;
    --bg-secondary: #f9fafb;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --border: #e5e7eb;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background: var(--bg-secondary);
    padding: 2rem;
}

.document {
    max-width: 900px;
    margin: 0 auto;
    background: var(--bg-primary);
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 3rem;
}

.header {
    border-bottom: 2px solid var(--border);
    padding-bottom: 2rem;
    margin-bottom: 2rem;
}

.title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.meta {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.section {
    margin-bottom: 2rem;
}

.section-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
}

.warning-box {
    background: var(--warning);
    background: rgba(251, 191, 36, 0.1);
    border-left: 4px solid var(--warning);
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin-bottom: 1rem;
}

.warning-box.high {
    background: rgba(239, 68, 68, 0.1);
    border-left-color: var(--error);
}

.warning-box.medium {
    background: rgba(251, 191, 36, 0.1);
    border-left-color: var(--warning);
}

.warning-box.low {
    background: rgba(59, 130, 246, 0.1);
    border-left-color: var(--primary);
}

.warning-title {
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.warning-details {
    list-style: disc;
    margin-left: 1.5rem;
    color: var(--text-secondary);
}

.recommendation-list {
    list-style: none;
    counter-reset: rec-counter;
}

.recommendation-list li {
    counter-increment: rec-counter;
    position: relative;
    padding-left: 2.5rem;
    margin-bottom: 1rem;
}

.recommendation-list li::before {
    content: counter(rec-counter);
    position: absolute;
    left: 0;
    top: 0;
    width: 1.75rem;
    height: 1.75rem;
    background: var(--primary);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.9rem;
}

.recommendation-list li.high::before {
    background: var(--error);
}

.recommendation-list li.medium::before {
    background: var(--warning);
    color: var(--text-primary);
}

.source-list {
    list-style: none;
}

.source-list li {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
}

.source-list li:last-child {
    border-bottom: none;
}

.credibility {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 0.5rem;
}

.credibility.high {
    background: rgba(34, 197, 94, 0.1);
    color: var(--success);
}

.credibility.medium {
    background: rgba(251, 191, 36, 0.1);
    color: var(--warning);
}

.credibility.low {
    background: rgba(239, 68, 68, 0.1);
    color: var(--error);
}

.source-link {
    color: var(--primary);
    text-decoration: none;
}

.source-link:hover {
    text-decoration: underline;
}

.footer {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

@media (max-width: 768px) {
    body {
        padding: 1rem;
    }
    
    .document {
        padding: 1.5rem;
    }
    
    .title {
        font-size: 1.5rem;
    }
}
"""

    @classmethod
    def format_response(cls, content: Dict[str, Any]) -> str:
        """
        Format a response as self-contained HTML.

        Args:
            content: Response content with sections, warnings, etc.

        Returns:
            HTML string with embedded CSS
        """
        title = content.get("title", "SkyModderAI Guide")
        date = datetime.now().strftime("%B %d, %Y")

        # Build content sections
        html_content = []

        # Executive summary
        if content.get("summary"):
            html_content.append(cls._create_section("Executive Summary", content["summary"]))

        # Warnings
        if content.get("warnings"):
            html_content.append(cls._create_warnings(content["warnings"]))

        # Main sections
        for section in content.get("sections", []):
            html_content.append(
                cls._create_section(
                    section.get("title", "Section"),
                    section.get("content", ""),
                    section.get("subsection", False),
                )
            )

        # Recommendations
        if content.get("recommendations"):
            html_content.append(cls._create_recommendations(content["recommendations"]))

        # Sources
        if content.get("sources"):
            html_content.append(cls._create_sources(content["sources"]))

        # Combine
        full_content = "\n\n".join(html_content)

        # Fill template
        doc = cls.HTML_TEMPLATE
        doc = doc.format(
            title=html.escape(title), date=date, content=full_content, css=cls.CSS_STYLES
        )

        return doc

    @classmethod
    def _create_section(cls, title: str, content: str, subsection: bool = False) -> str:
        """Create an HTML section."""
        tag = "h3" if subsection else "h2"
        return f"""
<div class="section">
    <{tag} class="section-title">{html.escape(title)}</{tag}>
    <div class="section-content">{cls._format_content(content)}</div>
</div>
"""

    @classmethod
    def _create_warnings(cls, warnings: List[Dict[str, Any]]) -> str:
        """Create warning boxes."""
        html = '<div class="section"><h2 class="section-title">⚠️ Important Warnings</h2>\n'

        for warning in warnings:
            level = warning.get("level", "warning")
            message = warning.get("message", "")

            level_class = "low"
            if level == "error" or level == "high":
                level_class = "high"
            elif level == "warning" or level == "medium":
                level_class = "medium"

            html += f"""
<div class="warning-box {level_class}">
    <div class="warning-title">⚠️ {html.escape(message)}</div>
"""

            if warning.get("details"):
                html += '    <ul class="warning-details">\n'
                for detail in warning["details"]:
                    html += f"        <li>{html.escape(detail)}</li>\n"
                html += "    </ul>\n"

            html += "</div>\n"

        html += "</div>\n"
        return html

    @classmethod
    def _create_recommendations(cls, recommendations: List[Dict[str, Any]]) -> str:
        """Create recommendations section."""
        html = '<div class="section"><h2 class="section-title">✅ Recommendations</h2>\n'
        html += '<ol class="recommendation-list">\n'

        for rec in recommendations:
            priority = rec.get("priority", "normal")
            content = rec.get("content", "")

            priority_class = ""
            if priority == "high":
                priority_class = "high"
            elif priority == "medium":
                priority_class = "medium"

            html += f'    <li class="{priority_class}">{cls._format_content(content)}</li>\n'

        html += "</ol></div>\n"
        return html

    @classmethod
    def _create_sources(cls, sources: List[Dict[str, Any]]) -> str:
        """Create sources section."""
        html = '<div class="section"><h2 class="section-title">📚 Sources</h2>\n'
        html += '<ul class="source-list">\n'

        for source in sources:
            title = source.get("title", "Unknown")
            url = source.get("url", "")
            credibility = source.get("credibility_score", 0)

            if credibility >= 0.8:
                cred_class = "high"
                cred_text = "★★★ High"
            elif credibility >= 0.6:
                cred_class = "medium"
                cred_text = "★★☆ Medium"
            else:
                cred_class = "low"
                cred_text = "★☆☆ Low"

            html += "    <li>\n"
            html += f'        <span class="credibility {cred_class}">{cred_text}</span>\n'
            html += f"        {html.escape(title)}"
            if url:
                html += f' — <a href="{html.escape(url)}" class="source-link" target="_blank" rel="noopener">View Source</a>'
            html += "\n    </li>\n"

        html += "</ul></div>\n"
        return html

    @classmethod
    def _format_content(cls, content: str) -> str:
        """Format markdown-like content as HTML."""
        if not content:
            return ""

        # Convert markdown to HTML
        # Bold
        content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
        # Italic
        content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", content)
        # Code
        content = re.sub(r"`(.+?)`", r"<code>\1</code>", content)
        # Line breaks
        content = content.replace("\n\n", "</p><p>")
        content = f"<p>{content}</p>"

        return content


def format_as_latex(content: Dict[str, Any]) -> str:
    """Format content as LaTeX document."""
    return LaTeXFormatter.format_response(content)


def format_as_html(content: Dict[str, Any]) -> str:
    """Format content as self-contained HTML."""
    return HTMLFormatter.format_response(content)


def format_as_pdf(content: Dict[str, Any], output_path: str) -> bool:
    """
    Format content as PDF using WeasyPrint.

    Args:
        content: Response content
        output_path: Path to save PDF

    Returns:
        True if successful
    """
    try:
        from weasyprint import CSS, HTML

        # Generate HTML
        html_content = format_as_html(content)

        # Convert to PDF
        html = HTML(string=html_content)
        html.write_pdf(output_path)

        logger.info(f"PDF saved to {output_path}")
        return True

    except ImportError:
        logger.warning("WeasyPrint not installed. Install with: pip install weasyprint")
        return False
    except Exception as e:
        logger.exception(f"PDF generation failed: {e}")
        return False


def create_guide_content(
    title: str,
    summary: str,
    sections: List[Dict[str, Any]],
    warnings: Optional[List[Dict[str, Any]]] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Create a structured guide content dictionary.

    Args:
        title: Guide title
        summary: Executive summary
        sections: List of section dicts with title, content, subsection
        warnings: List of warning dicts with level, message, details
        recommendations: List of recommendation dicts with priority, content
        sources: List of source dicts with title, url, credibility_score

    Returns:
        Content dictionary ready for formatting
    """
    return {
        "title": title,
        "summary": summary,
        "sections": sections,
        "warnings": warnings or [],
        "recommendations": recommendations or [],
        "sources": sources or [],
    }
