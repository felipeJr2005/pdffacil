import os
from pdf2docx import Converter
from core.common import create_temp_directory, clean_up_temp_directory, create_file_response

async def convert_pdf_to_docx(file):
    """
    Converte um arquivo PDF para DOCX usando pdf2docx.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        FileResponse: Arquivo DOCX para download
    """
    # Criar diretório temporário
    temp_dir = create_temp_directory()
    pdf_path = os.path.join(temp_dir, "input.pdf")
    docx_path = os.path.join(temp_dir, "output.docx")
    
    try:
        # Salvar o PDF recebido
        content = await file.read()
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(content)
        
        # Converter PDF para DOCX com configurações otimizadas
        cv = Converter(pdf_path)
        cv.convert(docx_path, 
                  start=0,           # Página inicial
                  end=None,          # Página final (None = todas)
                  pages=None,        # Páginas específicas
                  multi_processing=True,  # Processamento paralelo
                  cpu_count=2)       # Número de CPUs a usar
        cv.close()
        
        # Verificar se o arquivo foi criado
        if not os.path.exists(docx_path):
            raise Exception("Erro na conversão: arquivo DOCX não foi gerado")
        
        # Criar resposta com o arquivo
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        response = create_file_response(docx_path, file.filename, '.docx', media_type)
        
        # Configurar limpeza após envio
        response.background = lambda: clean_up_temp_directory(temp_dir)
        
        return response
        
    except Exception as e:
        # Limpar arquivos temporários em caso de erro
        clean_up_temp_directory(temp_dir)
        raise Exception(f"Erro ao converter PDF para DOCX: {str(e)}")
    finally:
        # Garantir limpeza se ainda não foi feita
        if os.path.exists(temp_dir):
            clean_up_temp_directory(temp_dir)
