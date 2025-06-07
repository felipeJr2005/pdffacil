from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="PDF Fácil API", 
    description="API para processamento de arquivos PDF com proteção contra abuso",
    version="1.0.0"
)

# Middleware de segurança - hosts confiáveis
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["pdffacil-jwuynw.fly.dev", "localhost", "127.0.0.1"]
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pdffacil.com", "http://pdffacil.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    client_ip = request.headers.get("x-forwarded-for", "unknown")
    logger.info(f"Request: {request.method} {request.url} from {client_ip}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {process_time:.2f}s")
    
    return response

@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está funcionando."""
    return {
        "message": "PDF Processor API está funcionando",
        "version": "1.0.0",
        "status": "protected",
        "limits": {
            "max_file_size_mb": 10,
            "pdf_to_text": "40 PDFs por dia",
            "pdf_to_docx": "12 PDFs por dia"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy", "timestamp": time.time()}

# Importar módulos funcionais
from modules.pdf_to_text.routes import router as pdf_to_text_router
from modules.pdf_to_docx.routes import router as pdf_to_docx_router

# Incluir rotas
app.include_router(pdf_to_text_router)
app.include_router(pdf_to_docx_router)

# Handler para rate limiting
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc: HTTPException):
    """Handler customizado para rate limiting."""
    client_ip = request.headers.get("x-forwarded-for", "unknown")
    logger.warning(f"Rate limit triggered for {client_ip}: {exc.detail}")
    
    return {"error": "Rate limit exceeded", "detail": exc.detail}

# TEMPORARIAMENTE DESABILITADO (depende de PyPDF2):
# from modules.pdf_to_excel.routes import router as pdf_to_excel_router
# app.include_router(pdf_to_excel_router)
