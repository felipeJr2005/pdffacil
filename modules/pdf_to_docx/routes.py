from fastapi import APIRouter, File, UploadFile, HTTPException
from .processor import convert_pdf_to_docx

# Criar router para este módulo
router = APIRouter()

@router.post("/pdf-to-docx/")
async def pdf_to_docx_endpoint(file: UploadFile = File(...)):
    """
    Endpoint para converter PDF para DOCX.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        FileResponse: Arquivo DOCX para download
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo não é um PDF")
    
    try:
        return await convert_pdf_to_docx(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conversão: {str(e)}")
