from fastapi import APIRouter, File, UploadFile, HTTPException
from .processor import convert_pdf_to_text

# Criar router para este módulo
router = APIRouter()

@router.post("/pdf-to-text/")
async def pdf_to_text_endpoint(file: UploadFile = File(...)):
    """
    Endpoint para extrair texto de um PDF.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        dict: Conteúdo de texto do PDF por página e metadados
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo não é um PDF")
    
    try:
        return await convert_pdf_to_text(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na extração de texto: {str(e)}")
