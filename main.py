from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import io
import os
import tempfile
from PyPDF2 import PdfReader
from docx import Document
import shutil

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

@app.post("/pdf-to-docx/")
async def pdf_to_docx(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo não é um PDF")
    
    try:
        # Criar diretório temporário
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "input.pdf")
        docx_path = os.path.join(temp_dir, "output.docx")
        
        # Salvar o PDF recebido
        content = await file.read()
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(content)
        
        # Ler o PDF
        pdf = PdfReader(pdf_path)
        
        # Criar documento DOCX
        doc = Document()
        
        # Para cada página, extrair texto e adicionar ao DOCX
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            if i > 0:  # Adicionar quebra de página após a primeira página
                doc.add_page_break()
            doc.add_paragraph(page_text)
        
        # Salvar o DOCX
        doc.save(docx_path)
        
        # Retornar o arquivo DOCX
        response = FileResponse(
            path=docx_path, 
            filename="converted.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # Configurar função para limpar arquivos temporários após envio
        response.background = lambda: shutil.rmtree(temp_dir, ignore_errors=True)
        
        return response
        
    except Exception as e:
        # Limpar arquivos temporários em caso de erro
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Erro na conversão: {str(e)}")
