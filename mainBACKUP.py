from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import re
import tempfile
from datetime import datetime
from PyPDF2 import PdfReader
from pdf2docx import Converter
import pandas as pd
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
            # Lista para armazenar dados de todas as páginas
            all_table_data = []
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                
                # Melhorar detecção de tabelas
                lines = page_text.split('\n')
                structured_rows = []
                
                for line in lines:
                    # Remover linhas de cabeçalho ou rodapé
                    if any(header in line for header in ['U.S. Department', 'Table 1.', 'Footnotes:', 'Total Apportionment']):
                        continue
                    
                    # Dividir linha usando regex para lidar com múltiplos espaços
                    cols = [col.strip() for col in re.split(r'\s{2,}', line) if col.strip()]
                    
                    # Validar se a linha parece ser uma linha de dados
                    if len(cols) >= 4:
                        try:
                            # Tentar converter dados numéricos
                            population = int(cols[1].replace(',', ''))
                            representatives = int(cols[2].replace(',', ''))
                            change = int(cols[3].replace(',', '')) if len(cols) > 3 else 0
                            
                            structured_rows.append([
                                cols[0],  # Estado
                                population,
                                representatives,
                                change
                            ])
                        except (ValueError, IndexError):
                            # Pular linhas que não podem ser convertidas
                            continue
                
                # Adicionar dados da página à lista geral
                all_table_data.extend(structured_rows)
            
            # Criar DataFrame principal
            if all_table_data:
                df = pd.DataFrame(all_table_data, 
                                  columns=['Estado', 'População', 'Representantes', 'Mudança 2010'])
                
                # Salvar planilha principal
                df.to_excel(writer, sheet_name='Dados', index=False)
                
                # Adicionar planilha de resumo
                summary_data = [
                    ['Total de Estados', len(df)],
                    ['População Total', df['População'].sum()],
                    ['Total de Representantes', df['Representantes'].sum()],
                    ['Data de Processamento', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                ]
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Resumo', index=False, header=False)
                
                # Ajustar largura das colunas
                workbook = writer.book
                worksheet_dados = writer.sheets['Dados']
                worksheet_resumo = writer.sheets['Resumo']
                
                # Formatação para planilha de dados
                formato_numero = workbook.add_format({'num_format': '#,##0'})
                worksheet_dados.set_column('A:A', 20)  # Estado
                worksheet_dados.set_column('B:B', 15, formato_numero)  # População
                worksheet_dados.set_column('C:C', 15, formato_numero)  # Representantes
                worksheet_dados.set_column('D:D', 15, formato_numero)  # Mudança
                
                # Formatação para planilha de resumo
                worksheet_resumo.set_column('A:A', 25)
                worksheet_resumo.set_column('B:B', 20)
            
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
