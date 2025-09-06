"""Router modules for different RAG agents."""

from . import fm_global_router
from . import general_rag_router
from . import code_assistant_router
from . import document_qa_router

__all__ = [
    "fm_global_router",
    "general_rag_router", 
    "code_assistant_router",
    "document_qa_router"
]