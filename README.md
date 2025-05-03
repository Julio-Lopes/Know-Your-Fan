# Know Your Esports Fan 🎮
> Know Your Fan é uma estratégia amplamente usada por clubes de eSports para entender melhor seus fãs e oferecer experiências personalizadas. Este projeto coleta e analisa dados de fãs com integração à Twitch, análise via IA (Gemini), OCR, validação de documentos e persistência em PostgreSQL.

---

## 🔧 Funcionalidades

- Autenticação via Twitch para obter canais seguidos
- Classificação de interesses em categorias de jogos com IA (Gemini)
- Formulário com validação de CPF e OCR para leitura de documentos
- Análise de links com validação por IA para identificar perfis relevantes no eSports
- Armazenamento de dados em banco PostgreSQL
- Dashboard com gráficos de insights dos fãs cadastrados

---

## 🧪 Tecnologias Utilizadas

- Python
- [Streamlit](https://streamlit.io)
- [Google Gemini API](https://ai.google.dev/)
- [Twitch API](https://dev.twitch.tv/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- PostgreSQL
- Plotly (para visualizações)

---

## 🚀 Como Executar Localmente

### 1. Clone o repositório

```bash
git clone https://github.com/Julio-Lopes/Know-Your-Fan
cd know-your-esports-fan
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz com o seguinte conteúdo:

```env
TWITCH_CLIENT_ID=seu_client_id
TWITCH_CLIENT_SECRET=sua_client_secret
TWITCH_REDIRECT_URI=http://localhost:8501
GENAI_API_KEY=sua_api_key_gemini

DB_NAME=fanfuria
DB_USER=postgres
DB_PASSWORD=root
DB_HOST=localhost
DB_PORT=5432
```

> ⚠️ Certifique-se de que o [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) esteja instalado e configurado no seu sistema.

### 5. Execute o app

```bash
streamlit run app.py
```

---

## 🗄️ Estrutura do Banco de Dados

Tabela: `esports_fans`

| Campo              | Tipo    |
|--------------------|---------|
| nome               | TEXT    |
| cpf                | TEXT    |
| endereco           | TEXT    |
| interesses         | TEXT    |
| eventos_2024       | TEXT    |
| compras_2024       | TEXT    |
| temas_detectados   | TEXT    |
| streamers_seguidos | TEXT    |
| links_validados    | TEXT    |

---
