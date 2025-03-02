from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import tempfile
from PyPDF2 import PdfReader
from pdf2docx import Converter
import pandas as pd
import tabula
import shutil

app = FastAPI()

# Configurar CORS para permitir solicitações do seu site
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pdffacil.com", "http://pdffacil.com"],  # Lista de origens permitidas
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos os métodos
    allow_headers=["*"],  # Permitir todos os cabeçalhos
)

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
        
        # Converter PDF para DOCX usando pdf2docx
        # Esta biblioteca preserva melhor a formatação, incluindo tabelas, imagens e layout
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        
        # Retornar o arquivo DOCX
        response = FileResponse(
            path=docx_path, 
            filename=file.filename.replace('.pdf', '.docx'),
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

@app.post("/pdf-to-excel/")
async def pdf_to_excel(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo não é um PDF")
    
    try:
        # Criar diretório temporário
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "input.pdf")
        excel_path = os.path.join(temp_dir, "output.xlsx")
        
        # Salvar o PDF recebido
        content = await file.read()
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(content)
        
        # Extrair tabelas de todas as páginas do PDF
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        
        # Criar um escritor Excel
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            # Se nenhuma tabela for encontrada, criar uma planilha com o texto extraído
            if not tables:
                pdf = PdfReader(pdf_path)
                text = ""
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    text += page_text + "\n\n"
                
                # Criar um DataFrame com o texto
                df = pd.DataFrame({"Texto Extraído": [text]})
                df.to_excel(writer, sheet_name='Texto Extraído', index=False)
            else:
                # Salvar cada tabela em uma aba diferente da planilha
                for i, table in enumerate(tables):
                    sheet_name = f'Tabela {i+1}'
                    # Limitar o nome da aba para 31 caracteres (limite do Excel)
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:31]
                    table.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Configurar formatação adicional se necessário
            workbook = writer.book
            for sheet in writer.sheets:
                worksheet = writer.sheets[sheet]
                # Ajustar largura das colunas
                worksheet.autofit()
        
        # Retornar o arquivo Excel
        response = FileResponse(
            path=excel_path, 
            filename=file.filename.replace('.pdf', '.xlsx'),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Configurar função para limpar arquivos temporários após envio
        response.background = lambda: shutil.rmtree(temp_dir, ignore_errors=True)
        
        return response
        
    except Exception as e:
        # Limpar arquivos temporários em caso de erro
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Erro na conversão: {str(e)}")
