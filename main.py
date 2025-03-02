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
        
        # Ler o PDF
        pdf = PdfReader(pdf_path)
        
        # Criar um escritor Excel
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            # Extrair texto de cada página
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                
                # Tentar estruturar o texto em linhas e colunas
                lines = page_text.split('\n')
                rows = []
                
                for line in lines:
                    if line.strip():
                        # Tenta dividir a linha em colunas (divisão por espaços múltiplos)
                        cols = [col.strip() for col in re.split(r'\s{2,}', line) if col.strip()]
                        if len(cols) > 1:
                            # Se conseguimos identificar colunas, adicionamos como uma linha
                            rows.append(cols)
                        else:
                            # Caso contrário, adicionamos como uma coluna única
                            rows.append([line.strip()])
                
                # Se temos dados estruturados
                if rows:
                    # Determinar o número máximo de colunas
                    max_cols = max(len(row) for row in rows)
                    
                    # Padronizar todas as linhas para ter o mesmo número de colunas
                    normalized_rows = []
                    for row in rows:
                        if len(row) < max_cols:
                            row = row + [''] * (max_cols - len(row))
                        normalized_rows.append(row)
                    
                    # Criar dataframe
                    columns = [f'Coluna {j+1}' for j in range(max_cols)]
                    df = pd.DataFrame(normalized_rows, columns=columns)
                    
                    # Salvar em uma planilha
                    sheet_name = f'Página {i+1}'
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # Se não conseguimos estruturar, salvar o texto bruto
                    df = pd.DataFrame({'Texto': [page_text]})
                    sheet_name = f'Página {i+1}'
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Adicionar planilha de resumo
            summary = []
            summary.append(["Arquivo", file.filename])
            summary.append(["Total de Páginas", len(pdf.pages)])
            summary.append(["Data de Processamento", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            
            df_summary = pd.DataFrame(summary)
            df_summary.to_excel(writer, sheet_name='Resumo', index=False, header=False)
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Resumo']
            worksheet.set_column('A:A', 20)
            worksheet.set_column('B:B', 40)
        
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
