from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from .processor import convert_pdf_to_docx
from core.rate_limiter import rate_limiter

# Criar router para este módulo
router = APIRouter()

@router.post("/pdf-to-docx/")
async def pdf_to_docx_endpoint(request: Request, file: UploadFile = File(...)):
    """
    Endpoint para converter PDF para DOCX - LIMITE: 12 PDFs por dia.
    
    Args:
        request: Request para rate limiting
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        FileResponse: Arquivo DOCX para download
    """
    # Validar tipo de arquivo
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser um PDF")
    
    # Ler conteúdo para verificar tamanho
    content = await file.read()
    file_size = len(content)
    
    # Verificar rate limiting para pdf_to_docx
    rate_limiter.check_rate_limit(request, "pdf_to_docx", file_size)
    
    # Resetar ponteiro do arquivo
    from io import BytesIO
    file.file = BytesIO(content)
    
    try:
        # Processar o PDF
        return await convert_pdf_to_docx(file)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conversão: {str(e)}")

@router.get("/pdf-to-docx/status/")
async def get_docx_rate_limit_status(request: Request):
    """Endpoint para verificar status do rate limiting para PDF-to-DOCX."""
    full_status = rate_limiter.get_status(request)
    return {
        "ip": full_status["ip"],
        "pdf_to_docx": full_status["pdf_to_docx"]
    }
