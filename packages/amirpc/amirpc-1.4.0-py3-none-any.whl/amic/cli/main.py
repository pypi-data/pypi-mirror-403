import json
import os
from pathlib import Path

import click
import rich
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.traceback import Traceback
from rich.traceback import install as install_rich_traceback

from amic.ast.dumps import dump_ast, to_jsonable
from amic.ast.model import InlineStruct, TypeRef
from amic.cli.lexers import AmiSpecLexer
from amic.codegen.utils import (
    iter_emits as iter_emits_utils,
)
from amic.codegen.utils import (
    iter_listens as iter_listens_utils,
)
from amic.codegen.utils import (
    iter_rpcs as iter_rpcs_utils,
)
from amic.compilation.pipeline import compile_infrastructure
from amic.errors import (
    AmiToolCompileError as AmiCompileError,
)
from amic.errors import (
    AmiToolError as AmiError,
)
from amic.errors import (
    AmiToolParseError as AmiParseError,
)
from amic.errors import (
    AmiToolValidationError as AmiValidationError,
)
from amic.generator import generate_project
from amic.parsing.parser import parse_file

app = typer.Typer(help="AMI tools", pretty_exceptions_show_locals=False)

# Enable pretty tracebacks for unexpected errors with compact, noise-free output
install_rich_traceback(
    show_locals=False,
    extra_lines=0,
    word_wrap=True,
    max_frames=20,
    locals_max_string=50,
    suppress=(click, typer, rich),
)


@app.command()
def ast(
    path: Path = typer.Argument(..., help="Path to .asl file"),
    json_output: bool = typer.Option(False, "--json", help="Print as JSON"),
    compiled: bool = typer.Option(
        False,
        "--compiled",
        help="Compile project and print compiled AST instead of raw parse tree",
    ),
    include_all_models: bool = typer.Option(
        False,
        "--include-all-models",
        help="Include all reachable non-domain models from same service namespace",
    ),
):
    try:
        pretty = not (os.getenv("AMI_PLAIN") or os.getenv("CI"))
        if compiled:
            if pretty:
                console = Console()
                with console.status("Compiling project", spinner="dots"):
                    ast_obj = compile_infrastructure(
                        path, include_all_models=include_all_models
                    )
            else:
                ast_obj = compile_infrastructure(
                    path, include_all_models=include_all_models
                )
        else:
            if pretty:
                console = Console()
                with console.status("Parsing file", spinner="dots"):
                    ast_obj = parse_file(path)
            else:
                ast_obj = parse_file(path)
        if json_output:
            typer.echo(json.dumps(to_jsonable(ast_obj), ensure_ascii=False, indent=2))
        else:
            if pretty:
                console = Console()
                console.print(Panel.fit("AST", style="bold cyan"))
                console.print(dump_ast(ast_obj))
            else:
                typer.echo(dump_ast(ast_obj))
    except AmiError as err:
        _print_error(err)
        raise typer.Exit(code=1)


@app.command()
def gen(
    path: Path = typer.Argument(
        ..., help="Path to root .asl file (must contain infrastructure)"
    ),
    out: Path = typer.Option(
        ..., "--out", help="Output directory to generate package into"
    ),
    gateway: bool = typer.Option(
        True,
        "--gateway/--no-gateway",
        help="Generate FastAPI gateway routes in specs package (default: enabled)",
    ),
    include_all_models: bool = typer.Option(
        False,
        "--include-all-models",
        help="Include all reachable non-domain models from same service namespace",
    ),
):
    try:
        pretty = not (os.getenv("AMI_PLAIN") or os.getenv("CI"))
        if pretty:
            console = Console()
            with console.status("Compiling project", spinner="dots"):
                compiled = compile_infrastructure(
                    path, include_all_models=include_all_models
                )
            with console.status("Generating package", spinner="earth"):
                written = generate_project(compiled, out)

            # Generate gateway metadata JSON
            gateway_path: Path | None = None
            if gateway:
                from amic.codegen.gateway import generate_gateway_metadata

                with console.status("Generating gateway metadata", spinner="dots12"):
                    gateway_path = generate_gateway_metadata(compiled, out)

            # Summary panel
            console.print(
                Panel.fit(
                    f"Generated package to [bold]{out}[/bold]",
                    title="Success",
                    border_style="green",
                )
            )

            # Files table
            table = Table(title="Written files", box=box.SIMPLE_HEAVY)
            table.add_column("#", justify="right", style="cyan", no_wrap=True)
            table.add_column("Path", style="white")
            table.add_column("Type", style="yellow")
            for i, p in enumerate(written, start=1):
                table.add_row(str(i), str(p), "specs")
            if gateway_path:
                table.add_row(
                    str(len(written) + 1), str(gateway_path), "gateway-metadata"
                )
            console.print(table)
        else:
            compiled = compile_infrastructure(
                path, include_all_models=include_all_models
            )
            written = generate_project(compiled, out)
            for p in written:
                typer.echo(f" - {p}")

            # Generate gateway metadata if enabled
            if gateway:
                from amic.codegen.gateway import generate_gateway_metadata

                gateway_path = generate_gateway_metadata(compiled, out)
                if gateway_path:
                    typer.echo(f" - {gateway_path} (gateway-metadata)")
    except AmiError as err:
        _print_error(err)
        raise typer.Exit(code=1)


@app.command()
def check(
    path: Path = typer.Argument(
        ..., help="Path to root .asl file (must contain infrastructure)"
    ),
    include_all_models: bool = typer.Option(
        False,
        "--include-all-models",
        help="Include all reachable non-domain models from same service namespace",
    ),
):
    def _asl_type_str(t: object) -> str:
        if isinstance(t, TypeRef):
            if t.kind == "container" and t.name == "list" and t.args:
                inner = _asl_type_str(t.args[0])
                s = f"list[{inner}]"
            else:
                s = t.name
            if getattr(t, "optional", False):
                s += "?"
            return s
        if isinstance(t, InlineStruct):
            parts = [f"{f.name}: {_asl_type_str(f.type)}" for f in t.fields]
            return "{" + ", ".join(parts) + "}"
        return str(t)

    def _format_rpc_row(ns_path: list[str], r) -> tuple[str, str, str, str]:
        name = ".".join(ns_path + [r.name]) if ns_path else r.name
        params = ", ".join([f"{p.name}: {_asl_type_str(p.type)}" for p in r.params])
        ret = _asl_type_str(r.returns)
        throws: list[str] = []
        for a in getattr(r, "attrs", []) or []:
            if a.name == "throws":
                throws.extend([str(x) for x in a.args])
        return name, params, ret, ", ".join(throws)

    def _format_event_row(kind: str, ns_path: list[str], e) -> tuple[str, str, str]:
        name = ".".join(ns_path + [e.name]) if ns_path else e.name
        params = ", ".join([f"{p.name}: {_asl_type_str(p.type)}" for p in e.params])
        return kind, name, params

    try:
        pretty = not (os.getenv("AMI_PLAIN") or os.getenv("CI"))
        if pretty:
            console = Console()
            with console.status("Compiling project", spinner="dots"):
                compiled = compile_infrastructure(
                    path, include_all_models=include_all_models
                )
            console.print(
                Panel.fit(
                    f"Module: [bold]{compiled.subject_prefix}[/bold]",
                    border_style="cyan",
                )
            )
            # Services overview table
            overview = Table(title="Services", box=box.SIMPLE_HEAVY)
            overview.add_column("Service", style="bold white")
            overview.add_column("RPCs", justify="right")
            overview.add_column("Emits", justify="right")
            overview.add_column("Listens", justify="right")
            for cs in compiled.services:
                num_rpcs = sum(1 for _ in iter_rpcs_utils(cs.service))
                num_emits = sum(1 for _ in iter_emits_utils(cs.service))
                num_listens = sum(1 for _ in iter_listens_utils(cs.service))
                overview.add_row(
                    cs.name, str(num_rpcs), str(num_emits), str(num_listens)
                )
            console.print(overview)
            # Detailed listing per service
            for cs in compiled.services:
                svc_panel = Panel.fit(f"[bold]{cs.name}[/bold]", border_style="magenta")
                console.print(svc_panel)
                rpc_rows = [
                    _format_rpc_row(ns_path, r)
                    for ns_path, r in iter_rpcs_utils(cs.service)
                ]
                if rpc_rows:
                    tbl = Table(title="RPCs", box=box.MINIMAL_HEAVY_HEAD)
                    tbl.add_column("Name", style="bold white")
                    tbl.add_column("Params", style="white")
                    tbl.add_column("Returns", style="white")
                    tbl.add_column("Throws", style="cyan")
                    for name, params, ret, throws in rpc_rows:
                        tbl.add_row(name, params, ret, throws)
                    console.print(tbl)
                emit_rows = [
                    _format_event_row("emit", ns_path, e)
                    for ns_path, e in iter_emits_utils(cs.service)
                ]
                listen_rows = [
                    _format_event_row("listen", ns_path, e)
                    for ns_path, e in iter_listens_utils(cs.service)
                ]
                ev_rows = emit_rows + listen_rows
                if ev_rows:
                    et = Table(title="Events", box=box.MINIMAL_HEAVY_HEAD)
                    et.add_column("Kind", style="cyan")
                    et.add_column("Name", style="bold white")
                    et.add_column("Params", style="white")
                    for kind, name, params in ev_rows:
                        et.add_row(kind, name, params)
                    console.print(et)
            if getattr(compiled, "acl", None):
                at = Table(title="ACL", box=box.SIMPLE_HEAVY)
                at.add_column("Subject", style="bold white")
                at.add_column("Action", style="cyan")
                at.add_column("Target", style="white")
                for rule in compiled.acl or []:
                    if not getattr(rule, "actions", None):
                        at.add_row(rule.subject, "allow", "[]")
                        continue
                    for act in rule.actions:
                        at.add_row(rule.subject, act.kind, act.target)
                console.print(at)
        else:
            compiled = compile_infrastructure(
                path, include_all_models=include_all_models
            )
            typer.echo(f"Module: {compiled.subject_prefix}")
            for cs in compiled.services:
                typer.echo(f"Service {cs.name}")
                for ns_path, r in iter_rpcs_utils(cs.service):
                    name, params, ret, throws = _format_rpc_row(ns_path, r)
                    throws_sfx = f" [throws: {throws}]" if throws else ""
                    typer.echo(f"  - rpc {name}({params}) -> {ret}{throws_sfx}")
                for ns_path, e in iter_emits_utils(cs.service):
                    kind, name, params = _format_event_row("emit", ns_path, e)
                    typer.echo(f"  - {kind} {name}({params})")
                for ns_path, e in iter_listens_utils(cs.service):
                    kind, name, params = _format_event_row("listen", ns_path, e)
                    typer.echo(f"  - {kind} {name}({params})")
            if getattr(compiled, "acl", None):
                typer.echo("ACL:")
                for rule in compiled.acl or []:
                    if not getattr(rule, "actions", None):
                        typer.echo(f"  allow {rule.subject} -> []")
                        continue
                    for act in rule.actions:
                        typer.echo(f"  {rule.subject} -> {act.kind} {act.target}")
    except AmiError as err:
        _print_error(err)
        raise typer.Exit(code=1)


def _print_error(err: AmiError) -> None:
    # Plain, deterministic output for CI or forced mode
    if os.getenv("AMI_PLAIN") or os.getenv("CI"):
        loc = []
        if err.location and (err.location.file or err.location.line):
            if err.location.file:
                loc.append(str(err.location.file))
            if err.location.line is not None:
                loc.append(str(err.location.line))
            if err.location.column is not None:
                loc.append(str(err.location.column))
        loc_s = ":".join(loc)
        meta = f" [{loc_s}]" if loc_s else ""
        hint = f"\nHint: {err.hint}" if getattr(err, "hint", None) else ""
        typer.echo(f"ERROR {_friendly_title(err)}: {err.message}{meta}{hint}")
        return

    console = Console(stderr=True, highlight=True)

    # Header in compiler style: error[kind]: message
    header = Text()
    header.append("error", style="bold red")
    header.append(f"[{_friendly_tag(err)}]", style="magenta")
    header.append(": ")
    header.append(err.message, style="bold")
    console.print(header)

    # Location line and top gutter
    loc_str = _format_location(err)
    if loc_str:
        console.print(Text(f"  --> {loc_str}", style="cyan"))

    # Code excerpt with syntax highlighting and highlighted line
    excerpt = _build_source_excerpt(err)
    if excerpt is not None:
        console.print(excerpt)

    # no extra pipes around the code frame

    # Hints and notes
    if getattr(err, "hint", None):
        console.print(Text(f"help: {err.hint}", style="cyan"))
    for n in getattr(err, "notes", []):
        console.print(Text(f"note: {n}", style="yellow"))

    # Optional: full traceback for debug if cause is present
    if os.getenv("AMI_DEBUG") and getattr(err, "__cause__", None):
        cause = err.__cause__  # type: ignore[assignment]
        console.print(
            Traceback.from_exception(
                type(cause),  # type: ignore[arg-type]
                cause,  # type: ignore[arg-type]
                cause.__traceback__,  # type: ignore[arg-type]
                show_locals=False,
                extra_lines=0,
                max_frames=20,
                word_wrap=True,
                suppress=(click, typer, rich),
            )
        )


def _format_location(err: AmiError) -> str:
    if not getattr(err, "location", None):
        return ""
    file_part: str | None = None
    line_part: str | None = None
    col_part: str | None = None
    if err.location.file:
        file_part = str(err.location.file)
    if err.location.line is not None:
        line_part = str(err.location.line)
    if err.location.column is not None:
        col_part = str(err.location.column)
    parts = [p for p in [file_part, line_part, col_part] if p]
    return ":".join(parts)


def _build_source_excerpt(err: AmiError) -> Syntax | None:
    loc = getattr(err, "location", None)
    if not loc or not loc.file or loc.line is None:
        return None
    try:
        text = Path(loc.file).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    lines = text.splitlines()
    if not lines:
        return None
    target_line = max(1, int(loc.line))
    start = max(1, target_line - 3)
    end = min(len(lines), target_line + 3)
    # Slice visible window; drop leading blank to avoid off-by-one rendering in Syntax
    window = lines[start - 1 : end]
    if window and window[0] == "":
        start += 1
        window = window[1:]
    excerpt = "\n".join(window)
    lexer = _pick_lexer(str(loc.file), text)
    return Syntax(
        excerpt,
        lexer,
        theme=_syntax_theme(),
        line_numbers=True,
        word_wrap=False,
        indent_guides=False,
        start_line=start,
        highlight_lines={target_line},
    )


def _friendly_title(err: AmiError) -> str:
    if isinstance(err, AmiCompileError):
        return "Compilation error"
    if isinstance(err, AmiParseError):
        return "Parse error"
    if isinstance(err, AmiValidationError):
        return "Validation error"
    # Fallback
    return "Error"


def _syntax_theme() -> str:
    # Use ANSI themes that don't force background and play nicely with terminal theme.
    # Override via AMI_SYNTAX_THEME (e.g. "ansi_light" or "ansi_dark").
    return os.getenv("AMI_SYNTAX_THEME", "ansi_dark")


def _pick_lexer(file_path: str, full_text: str):
    # Try to guess lexer based on filename and content; fallback heuristics for .asl
    try:
        guessed = Syntax.guess_lexer(file_path, code=full_text)
    except Exception:
        guessed = "text"
    if guessed not in {None, "", "default", "text"}:
        return guessed  # type: ignore[return-value]
    # Heuristic for AMI spec files
    if file_path.endswith(".asl"):
        # Prefer custom lexer; allow override via AMI_SYNTAX_LEXER
        override = os.getenv("AMI_SYNTAX_LEXER")
        if override:
            return override
        try:
            return AmiSpecLexer()
        except Exception:
            return "hcl"
    return "text"


def _friendly_tag(err: AmiError) -> str:
    if isinstance(err, AmiCompileError):
        return "compilation"
    if isinstance(err, AmiParseError):
        return "parse"
    if isinstance(err, AmiValidationError):
        return "validation"
    return "error"


def main() -> None:
    app()


if __name__ == "__main__":
    main()
