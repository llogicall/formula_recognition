import html


GREEK_SYMBOLS = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "theta": "θ",
    "lambda": "λ",
    "mu": "μ",
    "pi": "π",
    "rho": "ρ",
    "sigma": "σ",
    "phi": "φ",
    "omega": "ω",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Phi": "Φ",
    "Omega": "Ω",
}

OPERATORS = {
    "cdot": "·",
    "times": "×",
    "pm": "±",
    "leq": "≤",
    "geq": "≥",
    "neq": "≠",
    "infty": "∞",
}


def render_latex_preview_html(latex: str) -> str:
    latex = _strip_math_delimiters(latex.strip())
    if not latex:
        return _wrap("暂无公式预览")

    return _wrap(_render_tokens(latex))


def _wrap(body: str) -> str:
    return (
        '<div style="font-size:20px; line-height:1.5; color:#111827;">'
        f"{body}"
        "</div>"
    )


def _strip_math_delimiters(value: str) -> str:
    pairs = (("$$", "$$"), (r"\[", r"\]"), (r"\(", r"\)"), ("$", "$"))
    for start, end in pairs:
        if value.startswith(start) and value.endswith(end):
            return value[len(start) : len(value) - len(end)].strip()
    return value


def _render_tokens(value: str) -> str:
    output = []
    index = 0
    while index < len(value):
        if value.startswith(r"\frac", index):
            numerator, next_index = _read_braced(value, index + len(r"\frac"))
            denominator, index = _read_braced(value, next_index)
            output.append(_render_fraction(numerator, denominator))
            continue

        if value.startswith(r"\sqrt", index):
            radicand, index = _read_braced(value, index + len(r"\sqrt"))
            output.append("√" + _group(_render_tokens(radicand)))
            continue

        char = value[index]
        if char in "^_":
            content, index = _read_script(value, index + 1)
            tag = "sup" if char == "^" else "sub"
            output.append(f"<{tag}>{_render_tokens(content)}</{tag}>")
            continue

        if char == "\\":
            command, index = _read_command(value, index + 1)
            output.append(html.escape(GREEK_SYMBOLS.get(command, OPERATORS.get(command, command))))
            continue

        if char == "{":
            content, index = _read_braced(value, index)
            output.append(_render_tokens(content))
            continue

        output.append(html.escape(char))
        index += 1

    return "".join(output).replace("\n", "<br>")


def _render_fraction(numerator: str, denominator: str) -> str:
    return (
        '<span style="display:inline-block; text-align:center; vertical-align:middle;">'
        f'<span style="display:block; border-bottom:1px solid #111827; padding:0 4px;">{_render_tokens(numerator)}</span>'
        f'<span style="display:block; padding:0 4px;">{_render_tokens(denominator)}</span>'
        "</span>"
    )


def _group(content: str) -> str:
    return f'<span style="padding-left:2px;">{content}</span>'


def _read_script(value: str, index: int):
    if index < len(value) and value[index] == "{":
        return _read_braced(value, index)
    if index < len(value):
        return value[index], index + 1
    return "", index


def _read_braced(value: str, index: int):
    while index < len(value) and value[index].isspace():
        index += 1
    if index >= len(value) or value[index] != "{":
        return "", index

    depth = 0
    start = index + 1
    while index < len(value):
        if value[index] == "{":
            depth += 1
        elif value[index] == "}":
            depth -= 1
            if depth == 0:
                return value[start:index], index + 1
        index += 1
    return value[start:], len(value)


def _read_command(value: str, index: int):
    start = index
    while index < len(value) and value[index].isalpha():
        index += 1
    if start == index and index < len(value):
        return value[index], index + 1
    return value[start:index], index
