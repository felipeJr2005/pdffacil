from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Criar aplicação FastAPI
app = FastAPI(title="PDF Fácil API", 
              description="API para processamento de arquivos PDF",
              version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pdffacil.com", "http://pdffacil.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está funcionando."""
    return {"message": "PDF Processor API está funcionando"}

# Importar módulos funcionais
from modules.pdf_to_text.routes import router as pdf_to_text_router
from modules.pdf_to_docx.routes import router as pdf_to_docx_router

# Incluir rotas
app.include_router(pdf_to_text_router)
app.include_router(pdf_to_docx_router)

# TEMPORARIAMENTE DESABILITADO (depende de PyPDF2):
# from modules.pdf_to_excel.routes import router as pdf_to_excel_router
# app.include_router(pdf_to_excel_router)
