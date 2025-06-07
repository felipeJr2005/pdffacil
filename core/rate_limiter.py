import time
from typing import Dict, List
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter simples em memória para proteger a API."""
    
    def __init__(self):
        # Armazena: IP -> {"pdf_to_text": [timestamps], "pdf_to_docx": [timestamps]}
        self.requests: Dict[str, Dict[str, List[float]]] = {}
        
        # Limites por funcionalidade
        self.limits = {
            "pdf_to_text": 40,   # 40 PDFs por dia
            "pdf_to_docx": 12    # 12 PDFs por dia
        }
        self.max_file_size_mb = 10       # 10MB por arquivo
        
        # Tempo de janela em segundos (só diário)
        self.day_window = 86400
    
    def get_client_ip(self, request: Request) -> str:
        """Extrai IP do cliente, considerando proxies."""
        # Fly.io usa headers específicos
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Headers alternativos
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
            
        # IP direto
        if hasattr(request.client, 'host'):
            return request.client.host
            
        return "unknown"
    
    def clean_old_requests(self, ip: str, current_time: float):
        """Remove requests antigos da memória."""
        if ip not in self.requests:
            return
            
        # Remove requests mais antigos que 24h para todas as funcionalidades
        cutoff_time = current_time - self.day_window
        
        for func_name in self.requests[ip]:
            self.requests[ip][func_name] = [
                req_time for req_time in self.requests[ip][func_name] 
                if req_time > cutoff_time
            ]
        
        # Remove funcionalidades vazias
        self.requests[ip] = {
            func: times for func, times in self.requests[ip].items() 
            if times
        }
        
        # Remove IP se não tem requests recentes
        if not self.requests[ip]:
            del self.requests[ip]
    
    def check_rate_limit(self, request: Request, function_name: str, file_size_bytes: int = 0) -> bool:
        """
        Verifica se o request está dentro dos limites.
        
        Args:
            request: Request do FastAPI
            function_name: Nome da função ("pdf_to_text" ou "pdf_to_docx")
            file_size_bytes: Tamanho do arquivo em bytes
            
        Returns:
            True se permitido, HTTPException se bloqueado
        """
        ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Verificar tamanho do arquivo
        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            logger.warning(f"Arquivo muito grande rejeitado: {file_size_mb:.1f}MB de {ip}")
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande. Máximo permitido: {self.max_file_size_mb}MB"
            )
        
        # Verificar se a função é válida
        if function_name not in self.limits:
            raise HTTPException(
                status_code=400,
                detail=f"Função não reconhecida: {function_name}"
            )
        
        # Limpar requests antigos
        self.clean_old_requests(ip, current_time)
        
        # Inicializar estrutura se não existe
        if ip not in self.requests:
            self.requests[ip] = {}
        if function_name not in self.requests[ip]:
            self.requests[ip][function_name] = []
        
        # Contar requests no último dia para esta função
        day_cutoff = current_time - self.day_window
        recent_requests = [
            req_time for req_time in self.requests[ip][function_name] 
            if req_time > day_cutoff
        ]
        
        daily_limit = self.limits[function_name]
        
        # Verificar limite diário
        if len(recent_requests) >= daily_limit:
            logger.warning(f"Rate limit diário excedido para {ip} em {function_name}: {len(recent_requests)} requests")
            raise HTTPException(
                status_code=429,
                detail=f"Limite diário excedido para {function_name}. Máximo: {daily_limit} PDFs por dia. Tente amanhã."
            )
        
        # Registrar request atual
        self.requests[ip][function_name].append(current_time)
        
        # Log para monitoramento
        logger.info(f"Request permitido para {ip} em {function_name}: {len(recent_requests)+1}/{daily_limit} hoje")
        
        return True
    
    def get_status(self, request: Request) -> dict:
        """Retorna status atual do rate limiting para debug."""
        ip = self.get_client_ip(request)
        current_time = time.time()
        
        if ip not in self.requests:
            return {
                "ip": ip,
                "pdf_to_text": {
                    "used_today": 0,
                    "limit_daily": self.limits["pdf_to_text"],
                    "remaining": self.limits["pdf_to_text"]
                },
                "pdf_to_docx": {
                    "used_today": 0,
                    "limit_daily": self.limits["pdf_to_docx"],
                    "remaining": self.limits["pdf_to_docx"]
                }
            }
        
        # Contar requests recentes para cada função
        day_cutoff = current_time - self.day_window
        
        status = {"ip": ip}
        
        for func_name, daily_limit in self.limits.items():
            if func_name in self.requests[ip]:
                used_today = len([r for r in self.requests[ip][func_name] if r > day_cutoff])
            else:
                used_today = 0
            
            status[func_name] = {
                "used_today": used_today,
                "limit_daily": daily_limit,
                "remaining": max(0, daily_limit - used_today)
            }
        
        return status

# Instância global do rate limiter
rate_limiter = RateLimiter()
