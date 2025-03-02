import tempfile
import os
import shutil
from fastapi.responses import FileResponse

def create_temp_directory():
    """Cria um diretório temporário para processamento de arquivos."""
    return tempfile.mkdtemp()

def clean_up_temp_directory(temp_dir):
    """Limpa um diretório temporário."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

def create_file_response(file_path, original_filename, new_extension, media_type):
    """
    Cria uma resposta de arquivo para download.
    
    Args:
        file_path: Caminho para o arquivo processado
        original_filename: Nome do arquivo original
        new_extension: Nova extensão para o arquivo (.docx, .xlsx, etc.)
        media_type: Tipo MIME do arquivo
        
    Returns:
        FileResponse: Resposta de arquivo para download
    """
    new_filename = original_filename.replace('.pdf', new_extension)
    
    response = FileResponse(
        path=file_path,
        filename=new_filename,
        media_type=media_type
    )
    
    return response
