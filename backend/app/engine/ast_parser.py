import os
import ast
import hashlib
from typing import List, Dict, Any, Optional

try:
    from tree_sitter_languages import get_parser, get_language
    HAS_TREE_SITTER = True
except Exception:
    HAS_TREE_SITTER = False


class ASTCodeChunker:
    """
    Semantic AST Code Chunker with Multi-Language Tree-Sitter Support
    and graceful Python AST & sliding-window fallbacks.
    """
    
    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".go": "go",
        ".rs": "rust"
    }

    QUERY_SCM = """
    (function_definition) @function
    (class_definition) @class
    (method_definition) @method
    (function_declaration) @function
    (method_declaration) @method
    (type_declaration) @type
    """

    def __init__(self):
        self.parsers = {}
        if HAS_TREE_SITTER:
            for ext, lang in self.SUPPORTED_LANGUAGES.items():
                try:
                    self.parsers[ext] = get_parser(lang)
                except Exception:
                    pass

    def chunk_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Parses source code into structured semantic chunks (function, class, method).
        """
        if not content.strip():
            return []

        ext = os.path.splitext(file_path)[1].lower()

        # 1. Try Tree-Sitter Parser
        if HAS_TREE_SITTER and ext in self.parsers:
            try:
                chunks = self._chunk_with_tree_sitter(file_path, ext, content)
                if chunks:
                    return chunks
            except Exception:
                pass

        # 2. Fallback to Python AST if Python file
        if ext == ".py":
            try:
                chunks = self._chunk_with_python_ast(file_path, content)
                if chunks:
                    return chunks
            except Exception:
                pass

        # 3. Fallback to sliding-window line chunking
        return self._fallback_line_chunk(file_path, content)

    def _chunk_with_tree_sitter(self, file_path: str, ext: str, content: str) -> List[Dict[str, Any]]:
        parser = self.parsers.get(ext)
        if not parser:
            return []

        tree = parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        lang = get_language(self.SUPPORTED_LANGUAGES[ext])
        query = lang.query(self.QUERY_SCM)
        captures = query.captures(root_node)

        if not captures:
            return []

        lines = content.splitlines()
        chunks = []

        for node, tag in captures:
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            chunk_code = "\n".join(lines[start_line:end_line + 1])

            name_node = node.child_by_field_name("name")
            symbol_name = name_node.text.decode("utf8") if name_node else "anonymous"

            chunks.append({
                "file_path": file_path,
                "symbol_name": symbol_name,
                "symbol_type": tag,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "content": chunk_code,
                "checksum": hashlib.sha256(chunk_code.encode("utf8")).hexdigest()
            })

        return chunks

    def _chunk_with_python_ast(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        tree = ast.parse(content, filename=file_path)
        lines = content.splitlines()
        chunks = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = getattr(node, "end_lineno", start)
                chunk_lines = lines[start - 1:end]
                code = "\n".join(chunk_lines)
                chunks.append({
                    "file_path": file_path,
                    "symbol_name": node.name,
                    "symbol_type": "function",
                    "start_line": start,
                    "end_line": end,
                    "content": code,
                    "checksum": hashlib.sha256(code.encode("utf8")).hexdigest()
                })
            elif isinstance(node, ast.ClassDef):
                start = node.lineno
                end = getattr(node, "end_lineno", start)
                chunk_lines = lines[start - 1:end]
                code = "\n".join(chunk_lines)
                chunks.append({
                    "file_path": file_path,
                    "symbol_name": node.name,
                    "symbol_type": "class",
                    "start_line": start,
                    "end_line": end,
                    "content": code,
                    "checksum": hashlib.sha256(code.encode("utf8")).hexdigest()
                })

        return chunks

    def _fallback_line_chunk(self, file_path: str, content: str, chunk_size: int = 60, overlap: int = 10) -> List[Dict[str, Any]]:
        lines = content.splitlines()
        if not lines:
            return []

        chunks = []
        step = max(1, chunk_size - overlap)
        for i in range(0, len(lines), step):
            chunk_lines = lines[i:i + chunk_size]
            code = "\n".join(chunk_lines)
            chunks.append({
                "file_path": file_path,
                "symbol_name": f"lines_{i+1}_{i+len(chunk_lines)}",
                "symbol_type": "block",
                "start_line": i + 1,
                "end_line": i + len(chunk_lines),
                "content": code,
                "checksum": hashlib.sha256(code.encode("utf8")).hexdigest()
            })
            if i + chunk_size >= len(lines):
                break
        return chunks

    def search_symbols(self, file_path: str, content: str, query: str) -> List[Dict[str, Any]]:
        """
        Filters parsed chunks for symbols matching the query string.
        """
        chunks = self.chunk_file(file_path, content)
        query_lower = query.lower()
        return [c for c in chunks if query_lower in c.get("symbol_name", "").lower()]
