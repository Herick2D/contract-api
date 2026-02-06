# Contract Generator API
# Dockerfile para produção

FROM python:3.11-slim

# Metadados
LABEL maintainer="Contract Generator Team"
LABEL version="1.0.0"
LABEL description="API de geração de contratos a partir de templates Word e dados Excel"

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (incluindo unrar para suporte a arquivos RAR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    unrar-free \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (cache de layers)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretórios necessários (incluindo prints)
RUN mkdir -p /app/storage/templates \
             /app/storage/temp \
             /app/storage/outputs \
             /app/storage/prints

# Usuário não-root para segurança
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Porta da aplicação
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
