"""
parser.py — Tree-sitter based code parser for Python and JavaScript.
Extracts function definitions, class definitions, imports, and call relationships
to build the dependency graph.
"""
import os
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser


PY_LANGUAGE = Language(tspython.language())
JS_LANGUAGE = Language(tsjavascript.language())


def get_parser(language: str) -> Parser:
    """Return a tree-sitter parser for the given language."""
    parser = Parser()
    if language == "python":
        parser.language = PY_LANGUAGE
    elif language == "javascript":
        parser.language = JS_LANGUAGE
    else:
        raise ValueError(f"Unsupported language: {language}")
    return parser


def detect_language(file_path: str) -> str | None:
    """Detect the programming language from the file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {".py": "python", ".js": "javascript"}
    return mapping.get(ext)


def parse_file(file_path: str) -> dict:
    """
    Parse a source file and extract structured information.
    Returns:
        {
            "file_path": str,
            "language": str,
            "code": str,
            "line_count": int,
            "functions": [{"name": str, "start_line": int, "end_line": int, "code": str}],
            "classes": [{"name": str, "start_line": int, "end_line": int}],
            "imports": [str],
            "calls": [str],
        }
    """
    language = detect_language(file_path)
    if not language:
        return None

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()

    parser = get_parser(language)
    tree = parser.parse(bytes(code, "utf-8"))
    root = tree.root_node

    functions = []
    classes = []
    imports = []
    calls = []

    if language == "python":
        _extract_python(root, code, functions, classes, imports, calls)
    elif language == "javascript":
        _extract_javascript(root, code, functions, classes, imports, calls)

    return {
        "file_path": file_path,
        "language": language,
        "code": code,
        "line_count": code.count("\n") + 1,
        "functions": functions,
        "classes": classes,
        "imports": list(set(imports)),
        "calls": list(set(calls)),
    }


def _extract_python(node, code, functions, classes, imports, calls):
    """Recursively extract Python AST nodes."""
    for child in node.children:
        if child.type == "function_definition":
            name_node = child.child_by_field_name("name")
            if name_node:
                func_code = code[child.start_byte:child.end_byte]
                functions.append({
                    "name": name_node.text.decode("utf-8"),
                    "start_line": child.start_point[0] + 1,
                    "end_line": child.end_point[0] + 1,
                    "code": func_code,
                })

        elif child.type == "class_definition":
            name_node = child.child_by_field_name("name")
            if name_node:
                classes.append({
                    "name": name_node.text.decode("utf-8"),
                    "start_line": child.start_point[0] + 1,
                    "end_line": child.end_point[0] + 1,
                })
            # Recurse into class body for methods
            _extract_python(child, code, functions, classes, imports, calls)

        elif child.type == "import_statement":
            imports.append(child.text.decode("utf-8").strip())

        elif child.type == "import_from_statement":
            imports.append(child.text.decode("utf-8").strip())

        elif child.type == "call":
            func_node = child.child_by_field_name("function")
            if func_node:
                calls.append(func_node.text.decode("utf-8"))

        else:
            _extract_python(child, code, functions, classes, imports, calls)


def _extract_javascript(node, code, functions, classes, imports, calls):
    """Recursively extract JavaScript AST nodes."""
    for child in node.children:
        if child.type == "function_declaration":
            name_node = child.child_by_field_name("name")
            if name_node:
                func_code = code[child.start_byte:child.end_byte]
                functions.append({
                    "name": name_node.text.decode("utf-8"),
                    "start_line": child.start_point[0] + 1,
                    "end_line": child.end_point[0] + 1,
                    "code": func_code,
                })

        elif child.type == "class_declaration":
            name_node = child.child_by_field_name("name")
            if name_node:
                classes.append({
                    "name": name_node.text.decode("utf-8"),
                    "start_line": child.start_point[0] + 1,
                    "end_line": child.end_point[0] + 1,
                })
            _extract_javascript(child, code, functions, classes, imports, calls)

        elif child.type == "import_statement":
            imports.append(child.text.decode("utf-8").strip())

        elif child.type == "lexical_declaration":
            # Catch `const x = require(...)` patterns
            text = child.text.decode("utf-8")
            if "require(" in text:
                imports.append(text.strip())
            # Catch arrow functions: const foo = () => {}
            for decl in child.children:
                if decl.type == "variable_declarator":
                    value = decl.child_by_field_name("value")
                    if value and value.type == "arrow_function":
                        name_node = decl.child_by_field_name("name")
                        if name_node:
                            func_code = code[decl.start_byte:decl.end_byte]
                            functions.append({
                                "name": name_node.text.decode("utf-8"),
                                "start_line": decl.start_point[0] + 1,
                                "end_line": decl.end_point[0] + 1,
                                "code": func_code,
                            })

        elif child.type == "call_expression":
            func_node = child.child_by_field_name("function")
            if func_node:
                calls.append(func_node.text.decode("utf-8"))

        else:
            _extract_javascript(child, code, functions, classes, imports, calls)


def collect_files(root_dir: str, extensions: list[str]) -> list[str]:
    """
    Walk a directory tree and collect all source files matching the given extensions.
    Skips common non-source directories.
    """
    skip_dirs = {"node_modules", "venv", ".venv", "__pycache__", ".git", ".tox", "dist", "build"}
    collected = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prune directories we don't want to descend into
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in extensions:
                collected.append(os.path.join(dirpath, fname))

    return collected
