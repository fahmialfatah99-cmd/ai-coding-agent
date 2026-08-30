import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

try:
    from ...engine.ast_parser import ASTCodeChunker
except ImportError:
    from app.engine.ast_parser import ASTCodeChunker

router = APIRouter(prefix="/context", tags=["Context & AST Parser"])

chunker = ASTCodeChunker()

class ParseFileRequest(BaseModel):
    file_path: str
    content: str

class SymbolSearchRequest(BaseModel):
    workspace_path: str = "./workspace"
    file_path: str
    query: str

@router.post("/parse")
async def parse_code_ast(req: ParseFileRequest):
    """Parses code into semantic AST chunks using Tree-sitter."""
    chunks = chunker.chunk_file(req.file_path, req.content)
    return {
        "file_path": req.file_path,
        "total_chunks": len(chunks),
        "chunks": chunks
    }

@router.post("/search-symbols")
async def search_symbols(req: SymbolSearchRequest):
    """Searches symbol definitions (functions, classes, methods) in a file."""
    abs_path = os.path.abspath(os.path.join(req.workspace_path, req.file_path))
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    symbols = chunker.search_symbols(req.file_path, content, req.query)
    return {
        "file_path": req.file_path,
        "query": req.query,
        "results": symbols
    }

@router.get("/languages")
async def get_supported_languages():
    """Lists supported programming languages for Tree-sitter AST parsing."""
    return {"supported_extensions": list(ASTCodeChunker.SUPPORTED_LANGUAGES.keys())}
