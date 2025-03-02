from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import importlib
import os

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

# Importar módulos manualmente (para controle mais preciso do que é carregado)
from modules.pdf_to_docx.routes import router as pdf_to_docx_router
from modules.pdf_to_excel.routes import router as pdf_to_excel_router
from modules.pdf_to_txt.routes import router as pdf_to_text_router


# Incluir rotas de cada módulo
app.include_router(pdf_to_docx_router)
app.include_router(pdf_to_excel_router)
app.include_router(pdf_to_text_router)


# Versão alternativa com carregamento dinâmico de módulos
"""
def load_modules():
    modules_path = "modules"
    for module_name in os.listdir(modules_path):
        module_dir = os.path.join(modules_path, module_name)
        if os.path.isdir(module_dir) and not module_name.startswith('__'):
            try:
                module = importlib.import_module(f"modules.{module_name}.routes")
                if hasattr(module, "router"):
                    app.include_router(module.router)
                    print(f"Módulo carregado: {module_name}")
            except (ImportError, AttributeError) as e:
                print(f"Erro ao carregar módulo {module_name}: {e}")

# Descomente para usar o carregamento dinâmico
# load_modules()
"""
