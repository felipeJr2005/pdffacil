import os
from PyPDF2 import PdfReader
from core.common import create_temp_directory, clean_up_temp_directory

async def convert_pdf_to_txt(file):
    """
    Extrai texto de um arquivo PDF.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        dict: Dicionário contendo o texto extraído e metadados
    """
    # Criar diretório temporário
    temp_dir = create_temp_directory()
    pdf_path = os.path.join(temp_dir, "input.pdf")
    
    try:
        # Salvar o PDF recebido
        content = await file.read()
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(content)
        
        # Ler o PDF e extrair o texto
        pdf = PdfReader(pdf_path)
        
        # Extrair texto de cada página
        text_content = []
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            text_content.append({
                "page": i + 1,
                "content": page_text
            })
        
        # Extrair metadados do PDF, se disponíveis
        metadata = {}
        if pdf.metadata:
            for key, value in pdf.metadata.items():
                # Converte as chaves para formato adequado
                if key.startswith('/'):
                    key = key[1:]
                metadata[key] = str(value)
        
        # Resultado final
        result = {
            "filename": file.filename,
            "total_pages": len(pdf.pages),
            "metadata": metadata,
            "text": text_content
        }
        
        return result
        
    except Exception as e:
        # Limpar arquivos temporários em caso de erro
        clean_up_temp_directory(temp_dir)
        raise e
    finally:
        # Sempre limpar arquivos temporários após o uso
        clean_up_temp_directory(temp_dir)
