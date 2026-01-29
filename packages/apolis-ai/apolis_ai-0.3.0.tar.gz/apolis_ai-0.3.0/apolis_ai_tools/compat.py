import sys
import types
import warnings

# Shim for langchain.docstore.document.Document
# Required for paddlex (PaddleOCR) compatibility with modern langchain (0.1+)
# Paddlex expects 'from langchain.docstore.document import Document'
try:
    import langchain.docstore.document
except ImportError:
    try:
        from langchain_core.documents import Document
        
        # Create fake modules structure
        docstore = types.ModuleType("langchain.docstore")
        docstore_document = types.ModuleType("langchain.docstore.document")
        
        # Inject Document class
        docstore_document.Document = Document
        docstore.document = docstore_document
        
        # Inject into sys.modules
        sys.modules["langchain.docstore"] = docstore
        sys.modules["langchain.docstore.document"] = docstore_document

        # Shim for langchain.text_splitter (RecursiveCharacterTextSplitter)
        import langchain_text_splitters
        text_splitter = types.ModuleType("langchain.text_splitter")
        text_splitter.RecursiveCharacterTextSplitter = langchain_text_splitters.RecursiveCharacterTextSplitter
        sys.modules["langchain.text_splitter"] = text_splitter
        
        warnings.warn("Applied 'langchain.docstore' and 'langchain.text_splitter' shims for compatibility.")
        
    except ImportError:
        pass # If langchain_core missing, we can't do much
