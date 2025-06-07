import os
import logging
from pdf2docx import Converter
from core.common import create_temp_directory, clean_up_temp_directory, create_file_response

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def convert_pdf_to_docx(file):
    """
    Converte um arquivo PDF para DOCX usando pdf2docx com debug detalhado.
    
    Args:
        file: Arquivo PDF enviado pelo usuário
        
    Returns:
        FileResponse: Arquivo DOCX para download
    """
    temp_dir = None
    try:
        # Criar diretório temporário
        temp_dir = create_temp_directory()
        logger.info(f"Diretório temporário criado: {temp_dir}")
        
        pdf_path = os.path.join(temp_dir, "input.pdf")
        docx_path = os.path.join(temp_dir, "output.docx")
        
        # Salvar o PDF recebido
        content = await file.read()
        logger.info(f"PDF recebido: {len(content)} bytes")
        
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(content)
        
        # Verificar se PDF foi salvo
        if not os.path.exists(pdf_path):
            raise Exception("Erro ao salvar PDF temporário")
        
        pdf_size = os.path.getsize(pdf_path)
        logger.info(f"PDF salvo: {pdf_path} ({pdf_size} bytes)")
        
        # Tentar converter PDF para DOCX
        logger.info("Iniciando conversão com pdf2docx...")
        
        try:
            cv = Converter(pdf_path)
            logger.info("Converter inicializado")
            
            # Converter com configurações básicas primeiro
            cv.convert(docx_path, start=0, end=None)
            logger.info("Conversão executada")
            
            cv.close()
            logger.info("Converter fechado")
            
        except Exception as conv_error:
            logger.error(f"Erro na conversão pdf2docx: {str(conv_error)}")
            raise Exception(f"Erro interno pdf2docx: {str(conv_error)}")
        
        # Verificar se o arquivo DOCX foi criado
        if not os.path.exists(docx_path):
            logger.error(f"Arquivo DOCX não foi criado em: {docx_path}")
            
            # Listar arquivos no diretório temp para debug
            temp_files = os.listdir(temp_dir)
            logger.error(f"Arquivos no temp_dir: {temp_files}")
            
            raise Exception("pdf2docx falhou em gerar arquivo DOCX")
        
        # Verificar tamanho do arquivo DOCX
        docx_size = os.path.getsize(docx_path)
        logger.info(f"DOCX criado: {docx_path} ({docx_size} bytes)")
        
        if docx_size == 0:
            raise Exception("Arquivo DOCX criado está vazio")
        
        # Criar resposta com o arquivo
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        response = create_file_response(docx_path, file.filename, '.docx', media_type)
        
        # Configurar limpeza após envio
        response.background = lambda: clean_up_temp_directory(temp_dir)
        
        logger.info("Resposta criada com sucesso")
        return response
        
    except Exception as e:
        logger.error(f"Erro na conversão PDF para DOCX: {str(e)}")
        
        # Limpar arquivos temporários em caso de erro
        if temp_dir and os.path.exists(temp_dir):
            clean_up_temp_directory(temp_dir)
        
        # Re-raise com mensagem clara
        raise Exception(f"Erro ao converter PDF para DOCX: {str(e)}")
    
    finally:
        # Log final
        logger.info("Processamento finalizado")
