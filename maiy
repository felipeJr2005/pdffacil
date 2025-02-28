from fastapi import FastAPI, File, UploadFile, HTTPException
import io
from PyPDF2 import PdfReader

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "PDF Processor API está funcionando"}

@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo não é um PDF")
    
    try:
        content = await file.read()
        pdf = PdfReader(io.BytesIO(content))
        
        text = ""
        for i, page in enumerate(pdf.pages):
            text += f"--- Página {i+1} ---\n"
            page_text = page.extract_text() or ""
            text += page_text + "\n\n"
        
        return {"total_pages": len(pdf.pages), "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
