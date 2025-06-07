import pymupdf
import logging

logger = logging.getLogger(__name__)

async def convert_pdf_to_text(file):
    """
    Extrai texto de um arquivo PDF usando PyMuPDF.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        dict: Dados extraídos do PDF
    """
    try:
        # Ler o conteúdo do arquivo
        content = await file.read()
        logger.info(f"PDF recebido: {len(content)} bytes")
        
        # Abrir PDF com PyMuPDF
        doc = pymupdf.open(stream=content, filetype="pdf")
        
        # Extrair informações básicas
        num_pages = len(doc)
        metadata = doc.metadata
        
        # Extrair texto de todas as páginas
        full_text = ""
        pages_text = []
        
        for page_num in range(num_pages):
            page = doc[page_num]
            page_text = page.get_text()
            pages_text.append({
                "page": page_num + 1,
                "text": page_text.strip(),
                "char_count": len(page_text)
            })
            full_text += page_text + "\n"
        
        # Fechar documento
        doc.close()
        
        # Preparar resposta
        result = {
            "success": True,
            "filename": file.filename,
            "pages": num_pages,
            "total_characters": len(full_text),
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", "")
            },
            "full_text": full_text.strip(),
            "pages_text": pages_text
        }
        
        logger.info(f"Texto extraído: {num_pages} páginas, {len(full_text)} caracteres")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
        raise Exception(f"Erro ao processar PDF: {str(e)}")
    
    finally:
        # Garantir que o documento seja fechado
        try:
            if 'doc' in locals():
                doc.close()
        except:
            pass
