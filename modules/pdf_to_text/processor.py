import os
import fitz  # PyMuPDF
from core.common import create_temp_directory, clean_up_temp_directory

async def convert_pdf_to_text(file):
    """
    Extrai texto de um arquivo PDF usando PyMuPDF.
    
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
        
        # Abrir o PDF com PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Extrair texto de cada página
        text_content = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Extrair texto com melhor formatação
            page_text = page.get_text("text")
            
            # Alternativa para texto com layout preservado (descomente se necessário)
            # page_text = page.get_text("dict")  # Para estrutura mais detalhada
            # page_text = page.get_text("blocks")  # Para blocos de texto
            
            text_content.append({
                "page": page_num + 1,
                "content": page_text or ""
            })
        
        # Extrair metadados do PDF
        metadata = {}
        pdf_metadata = doc.metadata
        if pdf_metadata:
            # Mapear metadados para formato compatível
            metadata_mapping = {
                'title': 'Title',
                'author': 'Author', 
                'subject': 'Subject',
                'creator': 'Creator',
                'producer': 'Producer',
                'creationDate': 'CreationDate',
                'modDate': 'ModDate',
                'keywords': 'Keywords'
            }
            
            for pymupdf_key, display_key in metadata_mapping.items():
                if pymupdf_key in pdf_metadata and pdf_metadata[pymupdf_key]:
                    metadata[display_key] = str(pdf_metadata[pymupdf_key])
        
        # Informações adicionais do documento
        doc_info = {
            "page_count": len(doc),
            "is_pdf": True,
            "needs_password": doc.needs_pass,
            "is_encrypted": doc.is_encrypted,
            "permissions": doc.permissions if hasattr(doc, 'permissions') else None
        }
        
        # Fechar o documento
        doc.close()
        
        # Resultado final (mantendo compatibilidade com frontend)
        result = {
            "filename": file.filename,
            "total_pages": len(text_content),
            "metadata": metadata,
            "document_info": doc_info,
            "text": text_content
        }
        
        return result
        
    except Exception as e:
        # Fechar documento se ainda estiver aberto
        if 'doc' in locals() and doc:
            doc.close()
        
        # Limpar arquivos temporários em caso de erro
        clean_up_temp_directory(temp_dir)
        raise e
    finally:
        # Sempre limpar arquivos temporários após o uso
        clean_up_temp_directory(temp_dir)
