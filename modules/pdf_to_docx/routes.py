from fastapi import APIRouter, File, UploadFile, HTTPException, Header, Request
from typing import List, Optional
from .processor import convert_pdf_to_docx, extract_pdf_preview

# Criar router para este módulo
router = APIRouter()

@router.post("/pdf-to-docx/")
async def pdf_to_docx_endpoint(
    file: UploadFile = File(...),
    pages_to_keep: str = Header(None, alias="pages-to-keep")
):
    """
    Endpoint para converter PDF para DOCX, com opção de selecionar páginas.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        pages_to_keep: Lista opcional de índices de páginas a manter (base 0)
        
    Returns:
        FileResponse: Arquivo DOCX para download
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo não é um PDF")
    
    try:
        # Converter string JSON para lista de inteiros, se presente
        pages_list = None
        if pages_to_keep:
            import json
            pages_list = json.loads(pages_to_keep)
            
        return await convert_pdf_to_docx(file, pages_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conversão: {str(e)}")

@router.post("/pdf-preview/")
async def pdf_preview_endpoint(file: UploadFile = File(...)):
    """
    Endpoint para extrair informações de preview do PDF.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        dict: Informações sobre o PDF (número de páginas, etc.)
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo não é um PDF")
    
    try:
        return await extract_pdf_preview(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao extrair informações: {str(e)}")
