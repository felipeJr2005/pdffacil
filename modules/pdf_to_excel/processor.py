import os
import re
from datetime import datetime
from PyPDF2 import PdfReader
import pandas as pd
from core.common import create_temp_directory, clean_up_temp_directory, create_file_response

async def convert_pdf_to_excel(file):
    """
    Converte um arquivo PDF para Excel, extraindo tabelas.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        FileResponse: Arquivo Excel para download
    """
    # Criar diretório temporário
    temp_dir = create_temp_directory()
    pdf_path = os.path.join(temp_dir, "input.pdf")
    excel_path = os.path.join(temp_dir, "output.xlsx")
    
    try:
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
        
        # Criar resposta com o arquivo
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response = create_file_response(excel_path, file.filename, '.xlsx', media_type)
        
        # Configurar limpeza após envio
        response.background = lambda: clean_up_temp_directory(temp_dir)
        
        return response
    except Exception as e:
        # Limpar arquivos temporários em caso de erro
        clean_up_temp_directory(temp_dir)
        raise e
