from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from .processor import convert_pdf_to_text  # ← CORRIGIDO: nome correto da função
from core.rate_limiter import rate_limiter

# Criar router para este módulo
router = APIRouter()

@router.post("/pdf-to-text/")
async def pdf_to_text_endpoint(request: Request, file: UploadFile = File(...)):
    """
    Endpoint para extrair texto de PDF - LIMITE: 40 PDFs por dia.
    
    Args:
        request: Request para rate limiting
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        dict: Dados extraídos do PDF
    """
    # Validar tipo de arquivo
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser um PDF")
    
    # Ler conteúdo para verificar tamanho
    content = await file.read()
    file_size = len(content)
    
    # Verificar rate limiting para pdf_to_text
    rate_limiter.check_rate_limit(request, "pdf_to_text", file_size)
    
    # Resetar ponteiro do arquivo
    from io import BytesIO
    file.file = BytesIO(content)
    
    try:
        # Processar o PDF - CORRIGIDO: nome da função
        result = await convert_pdf_to_text(file)
        
        # Adicionar info de rate limiting na resposta
        rate_status = rate_limiter.get_status(request)
        result["rate_limit"] = rate_status["pdf_to_text"]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na extração: {str(e)}")

@router.get("/rate-limit-status/")
async def get_rate_limit_status(request: Request):
    """Endpoint para verificar status do rate limiting."""
    return rate_limiter.get_status(request)
