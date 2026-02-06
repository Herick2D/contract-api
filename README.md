# 📄 Contract Generator API

API REST para geração de documentos contratuais a partir de templates Word (.docx) e dados Excel (.xlsx).

## 🎯 Objetivo

Transformar a aplicação desktop de geração de iniciais arbitrais em um serviço web, permitindo:
- Upload de templates Word
- Upload de imagens das cláusulas contratuais (prints)
- Upload de planilhas Excel com dados de contratos
- Processamento em lote
- Download de ZIP com todos os documentos gerados

## 🚀 Quick Start

### Com Docker (Recomendado)

```bash
# Clone ou copie o projeto
cd contract-api

# Suba com Docker Compose
docker-compose up -d

# Acesse a documentação
# http://localhost:8000/docs
```

### Sem Docker

```bash
# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Execute
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentação da API

Após iniciar a aplicação, acesse:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔄 Fluxo de Uso

### 1. Cadastrar Template

Faça upload do modelo Word com os placeholders que serão substituídos:

```bash
curl -X POST "http://localhost:8000/api/v1/templates/" \
  -H "Content-Type: multipart/form-data" \
  -F "name=modelo_inicial_arbitral" \
  -F "description=Modelo de inicial arbitral para despejo" \
  -F "file=@modelo.docx"
```

**Resposta:**
```json
{
  "id": "abc12345",
  "name": "modelo_inicial_arbitral",
  "status": "active",
  "placeholders": ["(NOME DO INQUILINO)", "(inserir o CPF do Inqulino)", ...]
}
```

### 2. Enviar Prints (Imagens das Cláusulas)

Faça upload das imagens das cláusulas contratuais:

```bash
# Arquivo individual
curl -X POST "http://localhost:8000/api/v1/prints/upload" \
  -F "files=@61796.png"

# Múltiplos arquivos
curl -X POST "http://localhost:8000/api/v1/prints/upload" \
  -F "files=@61796.png" \
  -F "files=@814300.jpg"

# Arquivo ZIP com múltiplas imagens
curl -X POST "http://localhost:8000/api/v1/prints/upload" \
  -F "files=@prints.zip"
```

**Resposta:**
```json
{
  "sucesso": true,
  "total_enviados": 1,
  "total_aceitos": 50,
  "total_rejeitados": 0,
  "aceitos": ["61796.png", "814300.jpg", ...],
  "rejeitados": [],
  "mensagem": "50 arquivo(s) enviado(s) com sucesso"
}
```

### 3. Listar Contratos (Opcional)

Verifique quais contratos estão disponíveis no Excel:

```bash
curl -X POST "http://localhost:8000/api/v1/contracts/list" \
  -F "file=@contratos.xlsx"
```

### 4. Verificar Pendências (Opcional)

Identifique campos faltantes antes do processamento:

```bash
curl -X POST "http://localhost:8000/api/v1/contracts/pendencias" \
  -F "file=@contratos.xlsx"
```

### 5. Processar Contratos

Processe todos os contratos ou uma lista específica:

```bash
# Processar todos
curl -X POST "http://localhost:8000/api/v1/contracts/process" \
  -F "template_id=abc12345" \
  -F "file=@contratos.xlsx"

# Processar contratos específicos
curl -X POST "http://localhost:8000/api/v1/contracts/process" \
  -F "template_id=abc12345" \
  -F "file=@contratos.xlsx" \
  -F "contratos=8957,16423,27890"
```

**Resposta:**
```json
{
  "job_id": "xyz789",
  "status": "completed",
  "total_contratos": 51,
  "sucessos": 49,
  "falhas": 2,
  "download_url": "/api/v1/contracts/download/xyz789"
}
```

### 6. Download dos Documentos

Baixe o ZIP com todos os documentos gerados:

```bash
curl -O "http://localhost:8000/api/v1/contracts/download/xyz789"
```

## 📁 Estrutura do Projeto

```
contract-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configurações
│   ├── api/
│   │   └── endpoints/
│   │       ├── templates.py # Endpoints de templates
│   │       ├── prints.py    # Endpoints de prints
│   │       └── contracts.py # Endpoints de contratos
│   ├── models/
│   │   └── schemas.py       # Pydantic schemas
│   └── services/
│       ├── template_service.py
│       └── contract_service.py
├── core/                    # Lógica de negócio (core original)
│   ├── excel_reader.py
│   ├── document_generator.py
│   ├── models.py
│   └── ...
├── storage/
│   ├── templates/           # Templates salvos
│   ├── prints/              # Imagens das cláusulas
│   ├── temp/                # Arquivos temporários
│   └── outputs/             # Documentos gerados
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 📋 Endpoints

### Templates

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/templates/` | Criar novo template |
| GET | `/api/v1/templates/` | Listar templates |
| GET | `/api/v1/templates/{id}` | Obter template |
| PUT | `/api/v1/templates/{id}` | Atualizar template |
| DELETE | `/api/v1/templates/{id}` | Deletar template |
| GET | `/api/v1/templates/{id}/download` | Download do template |

### Prints (Imagens das Cláusulas)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/prints/upload` | Upload de prints (individual, múltiplos ou ZIP/RAR) |
| GET | `/api/v1/prints/` | Listar prints |
| GET | `/api/v1/prints/{contract_number}` | Obter print de um contrato |
| DELETE | `/api/v1/prints/{contract_number}` | Deletar print de um contrato |
| DELETE | `/api/v1/prints/` | Limpar todos os prints |

### Contratos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/contracts/list` | Listar contratos do Excel |
| POST | `/api/v1/contracts/pendencias` | Verificar pendências |
| POST | `/api/v1/contracts/process` | Processar contratos |
| GET | `/api/v1/contracts/job/{id}` | Status do processamento |
| GET | `/api/v1/contracts/download/{id}` | Download do ZIP |
| DELETE | `/api/v1/contracts/job/{id}` | Limpar arquivos do job |

## 🖼️ Prints (Imagens das Cláusulas)

### Nomenclatura

O nome do arquivo **deve ser o número do contrato**:

| Contrato | Nome do arquivo |
|----------|-----------------|
| 61796 | `61796.png` ou `61796.jpg` |
| 814300 | `814300.png` ou `814300.jpg` |

### Formatos aceitos

- **Imagens individuais**: `.png`, `.jpg`, `.jpeg`
- **Arquivos compactados**: `.zip`, `.rar`

### Validação de arquivos compactados

Ao enviar um ZIP ou RAR, a API valida se **todos os arquivos** dentro são imagens válidas. Se houver qualquer arquivo inválido, o upload é rejeitado.

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# API
DEBUG=false
MAX_WORKERS=4

# Dados do Escritório
ADVOGADO_NOME=João Thomaz Prazeres Gondim
ADVOGADO_OAB=270.757
ESCRITORIO_TELEFONE=(21) 2262-7979
ESCRITORIO_WHATSAPP=(21) 96975-0156
ESCRITORIO_EMAIL=quintoandar@gondimadv.com.br
ESCRITORIO_EMAIL_INTIMACOES=camaras.arbitrais@gondimadv.com.br
ESCRITORIO_ENDERECO=Avenida Paulo de Frontin, 1, Centro Empresarial, Cidade Nova, Rio de Janeiro - RJ, 20260-010
```

## 📊 Formato do Excel

O arquivo Excel deve conter as seguintes abas:

### Aba "Contatos" (ou "Base")

| Coluna | Descrição |
|--------|-----------|
| contrato | Número do contrato |
| nome inqs | Nome(s) do(s) inquilino(s) |
| cpf_iqs | CPF(s) do(s) inquilino(s) |
| email inqs | Email(s) do(s) inquilino(s) |
| tel inqs | Telefone(s) do(s) inquilino(s) |
| nome pps | Nome(s) do(s) proprietário(s) |
| cpf_pps | CPF(s) do(s) proprietário(s) |
| email pps | Email(s) do(s) proprietário(s) |
| tel pp | Telefone(s) do(s) proprietário(s) |
| cidade | Cidade do imóvel |
| valor_aluguel | Valor do aluguel |
| valor_condominio | Valor do condomínio |
| valor_iptu | Valor do IPTU |
| valor_seguro_incendio | Valor do seguro |
| valor_historico | Valor histórico do débito |
| valor_atualizado | Valor atualizado do débito |

### Aba "Endereço imóvel"

| Coluna | Descrição |
|--------|-----------|
| contract | Número do contrato |
| house_address | Endereço |
| house_complement | Complemento |
| house_neighborhood | Bairro |
| house_city | Cidade |
| house_zipcode | CEP |

## 🔒 Segurança

Em produção, recomenda-se:

1. **CORS**: Configurar origens permitidas
2. **Rate Limiting**: Implementar limitação de requisições
3. **Autenticação**: Adicionar JWT ou API Key
4. **HTTPS**: Usar certificado SSL
5. **Logs**: Configurar logging adequado

## 🧪 Testes

```bash
# Instala dependências de teste
pip install pytest pytest-asyncio httpx

# Executa testes
pytest tests/ -v
```

## 📈 Monitoramento

Endpoints úteis:
- `/health` - Health check básico
- `/docs` - Documentação interativa
- `/redoc` - Documentação alternativa

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Projeto proprietário.

---

**Desenvolvido com ❤️ usando FastAPI + Python**
