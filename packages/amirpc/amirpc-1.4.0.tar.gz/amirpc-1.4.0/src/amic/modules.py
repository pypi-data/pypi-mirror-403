from pathlib import Path

from amic.ast.model import Model, ModuleFile
from amic.compilation.compiled import WELL_KNOWN_NAMESPACE, WELL_KNOWN_TYPES
from amic.decorators import apply_decorators_parsed
from amic.errors import AmiToolCompileError as AmiCompileError
from amic.locate import (
    loc_ref_line,
)
from amic.parsing.parser import parse_file as parse_one


def resolve_path(root_dir: Path, current_file: Path, ref: str) -> Path:
    if ref.startswith("$/"):
        return (root_dir / ref[2:]).resolve()
    p = Path(ref)
    if p.is_absolute():
        return p
    return (current_file.parent / p).resolve()


def ns_for_file(root_dir: Path, file_path: Path) -> str:
    rel = file_path.relative_to(root_dir)
    if file_path.name == "mod.asl":
        ns_parts = list(rel.parent.parts)
    else:
        ns_parts = list(rel.with_suffix("").parts)
    return ".".join(ns_parts) if ns_parts else ""


class ModuleUnit:
    def __init__(self, ns: str, path: Path, ast: ModuleFile):
        self.ns = ns
        self.path = path
        self.ast = ast


def make_well_known_module() -> ModuleUnit:
    decls: list[object] = []
    for name in WELL_KNOWN_TYPES:
        decls.append(
            Model(name=name, fields=[], attrs=[], domain=False, decorators=None)
        )
    ast = ModuleFile(imports=[], decls=decls, module=WELL_KNOWN_NAMESPACE)
    pseudo_path = Path(f"<{WELL_KNOWN_NAMESPACE}>")
    return ModuleUnit(ns=WELL_KNOWN_NAMESPACE, path=pseudo_path, ast=ast)


def collect_module(root_dir: Path, current_file: Path, ref: str) -> ModuleUnit:
    if ref.startswith("@/"):
        if ref == "@/well-known":
            return make_well_known_module()
        raise AmiCompileError(
            f"Unknown virtual module provider: {ref}",
            file=current_file,
            line=loc_ref_line(current_file, ref),
            stage="bind",
            hint="Only '@/well-known' is supported at the moment",
        )
    path = resolve_path(root_dir, current_file, ref)
    if not path.exists():
        raise AmiCompileError(
            f"Module file not found: {ref}",
            file=current_file,
            line=loc_ref_line(current_file, ref),
            column=None,
            stage="bind",
            hint="Check the path in 'services{ X from \"...\" };' or file existence",
        )
    ast = parse_one(path)
    apply_decorators_parsed(ast, file=path)
    if not isinstance(ast, ModuleFile):
        if hasattr(ast, "infrastructure"):
            raise AmiCompileError(
                "Only one infrastructure is allowed in an imported file",
                file=path,
                stage="bind",
                hint="Move 'infrastructure' to the root file and import modules without it",
            )
        raise AmiCompileError(
            "Module must be a module file",
            file=path,
            stage="bind",
            hint="The file must contain type/service declarations and, if needed, 'module \"...\"';",
        )
    ns = ast.module or ns_for_file(root_dir, path)
    return ModuleUnit(ns=ns, path=path, ast=ast)
