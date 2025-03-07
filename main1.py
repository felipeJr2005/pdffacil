from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from modules.pdf_to_docx.routes import router as pdf_to_docx_router

app = FastAPI()

# Montar rotas dos módulos
app.include_router(pdf_to_docx_router, prefix="/api")

# Configurar arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/pdf-viewer", response_class=HTMLResponse)
async def pdf_viewer(request: Request):
    return templates.TemplateResponse("pdf_viewer.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
