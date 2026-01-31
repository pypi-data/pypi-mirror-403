from pygments.lexer import RegexLexer, bygroups, words
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Whitespace,
)


class AmiSpecLexer(RegexLexer):
    """Minimal Pygments lexer for AMI Spec Language (.asl).

    Heuristic highlighting: keywords, identifiers, numbers, strings, comments, braces.
    This is intentionally conservative to avoid mis-highlighting.
    """

    name = "AMI Spec"
    aliases = ["ami-asl", "ami", "asl"]
    filenames = ["*.asl"]

    _KEYWORDS = (
        # Language keywords per grammar
        "module",
        "import",
        "from",
        "service",
        "services",
        "infrastructure",
        "domain",
        "model",
        "enum",
        "error",
        "rpc",
        "event",
        "acl",
        "allow",
        "call",
        "listen",
        "namespace",
        # literals
        "true",
        "false",
    )

    tokens = {
        "root": [
            # whitespace and comments
            (r"\s+", Whitespace),
            (r"//.*?$", Comment.Single),
            (r"/\*", Comment.Multiline, "comment"),
            # decorators: @name(opt args) — ensure '@' is output via groups
            (
                r"(@)([A-Za-z_][A-Za-z0-9_]*)(\()",
                bygroups(Punctuation, Name.Decorator, Punctuation),
                "decorator_args",
            ),
            (r"(@)([A-Za-z_][A-Za-z0-9_]*)", bygroups(Punctuation, Name.Decorator)),
            # strings
            (r'"[^"\\]*(?:\\.[^"\\]*)*' + r'"', String.Double),
            (r"'[^'\\]*(?:\\.[^'\\]*)*'", String.Single),
            # keywords
            (words(_KEYWORDS, suffix=r"\b"), Keyword),
            # punctuation and operators (enter attrs state for inline [ ... ])
            (r"\[", Punctuation, "attrs"),
            (r"[{}\]();,]", Punctuation),
            (r"[:=><.!\-]+", Operator),
            # builtin scalar types
            (r"\b(int|string|bool|float)\b", Keyword.Type),
            # numbers
            (r"\b[0-9]+\b", Number.Integer),
            # dotted names (namespace or types)
            (r"([A-Z][A-Za-z0-9_]*)(\.)", bygroups(Name.Class, Punctuation)),
            (r"([a-z_][A-Za-z0-9_]*)(\.)", bygroups(Name.Namespace, Punctuation)),
            # types in annotations: name after ':' or '->' until delimiter
            (
                r"(:|->)(\s*)([A-Z][A-Za-z0-9_]*)(\b)",
                bygroups(Operator, Whitespace, Name.Class, Text),
            ),
            (
                r"(:|->)(\s*)([a-z_][A-Za-z0-9_]*)(\b)",
                bygroups(Operator, Whitespace, Name, Text),
            ),
            # identifiers
            (r"\b[A-Z][A-Za-z0-9_]*\b", Name.Class),  # PascalCase as type/class
            (r"\b[a-z_][A-Za-z0-9_]*\b", Name),
            (r"\.", Punctuation),
        ],
        "decorator_args": [
            (r"\)", Punctuation, "#pop"),
            (r",", Punctuation),
            (r"\s+", Whitespace),
            (r"[A-Za-z_][A-Za-z0-9_]*\s*=", Name.Attribute),
            (r"[A-Za-z_][A-Za-z0-9_]*", Name),
            (r"[0-9]+", Number.Integer),
            (r'"[^"\\]*(?:\\.[^"\\]*)*' + r'"', String.Double),
            (r"'[^'\\]*(?:\\.[^'\\]*)*'", String.Single),
        ],
        "attrs": [
            (r"\]", Punctuation, "#pop"),
            (r",", Punctuation),
            (r"\s+", Whitespace),
            # key: value
            (
                r"([A-Za-z_][A-Za-z0-9_]*)(\s*)(:)",
                bygroups(Name.Attribute, Whitespace, Punctuation),
            ),
            # values
            (r"\b(int|string|bool|float|true|false)\b", Keyword.Type),
            (r"[0-9]+", Number.Integer),
            (r'"[^"\\]*(?:\\.[^"\\]*)*' + r'"', String.Double),
            (r"'[^'\\]*(?:\\.[^'\\]*)*'", String.Single),
            (r"([A-Z][A-Za-z0-9_]*)(\.)", bygroups(Name.Class, Punctuation)),
            (r"([a-z_][A-Za-z0-9_]*)(\.)", bygroups(Name.Namespace, Punctuation)),
            (r"\b[A-Z][A-Za-z0-9_]*\b", Name.Class),
            (r"\b[a-z_][A-Za-z0-9_]*\b", Name),
            (r"[:=><.!\-]+", Operator),
        ],
        "comment": [
            (r"[^*/]+", Comment.Multiline),
            (r"/\*", Comment.Multiline, "comment"),
            (r"\*/", Comment.Multiline, "#pop"),
            (r"[*/]", Comment.Multiline),
        ],
    }
