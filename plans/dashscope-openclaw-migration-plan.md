# Piano di Migrazione: Aggiornamento Endpoint DashScope/OpenClaw

## Panoramica

Questo piano dettaglia le modifiche necessarie per integrare il nuovo endpoint **Coding Plan** di Alibaba Cloud (OpenClaw) nel progetto BookWriterAI, sostituendo/aggiornando l'attuale implementazione DashScope.

## Contesto

### Endpoint Attuale (Legacy)
- **URL**: `https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation`
- **API**: Nativa DashScope (non OpenAI-compatible)
- **Implementazione**: Usa `requests.post()` con payload custom

### Nuovo Endpoint (OpenClaw/Coding Plan)
- **URL**: `https://coding-intl.dashscope.aliyuncs.com/v1`
- **API**: OpenAI-compatible (`/v1/chat/completions`)
- **Provider**: `bailian`
- **Documentazione**: OpenClaw - Alibaba Cloud Model Studio

## Modelli Supportati (Nuovi)

| Modello | Context Window | Max Tokens | Input |
|---------|---------------|------------|-------|
| `qwen3.5-plus` | 1,000,000 | 65,536 | text, image |
| `qwen3-max-2026-01-23` | 262,144 | 65,536 | text |
| `qwen3-coder-next` | 262,144 | 65,536 | text |
| `qwen3-coder-plus` | 1,000,000 | 65,536 | text |
| `MiniMax-M2.5` | 196,608 | 32,768 | text |
| `glm-5` | 202,752 | 16,384 | text |
| `glm-4.7` | 202,752 | 16,384 | text |
| `kimi-k2.5` | 262,144 | 32,768 | text, image |

## Modifiche Richieste

### 1. ebooks.py - Classe Config

**Posizione**: Linee 57-86

**Modifiche**:
- Aggiungere `bailian` come provider valido
- Aggiornare `__post_init__` per supportare `BAILIAN_API_KEY`
- Mantenere retrocompatibilità con `DASHSCOPE_API_KEY`

```python
@dataclass
class Config:
    # ... existing fields ...
    provider: str = "openai"  # "openai", "qwen", o "bailian"
    # ...
    
    def __post_init__(self):
        if self.provider == "bailian" and not self.api_key:
            self.api_key = os.getenv("BAILIAN_API_KEY", "") or os.getenv("DASHSCOPE_API_KEY", "")
        if self.provider == "qwen" and not self.api_key:
            self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if self.provider == "openai" and not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("API key non trovata. Imposta OPENAI_API_KEY, BAILIAN_API_KEY o DASHSCOPE_API_KEY nel .env")
```

### 2. ebooks.py - BaseAgent._setup_client()

**Posizione**: Linee 721-738

**Modifiche**:
- Aggiungere caso `bailian` che usa OpenAI client con endpoint custom
- Mantenere caso `qwen` per retrocompatibilità (deprecato)
- Aggiornare caso `openai` per supportare endpoint bailian

```python
def _setup_client(self):
    if self.config.provider == "openai":
        client_kwargs = {"api_key": self.config.api_key}
        if self.config.endpoint:
            client_kwargs["base_url"] = self.config.endpoint
        self.client = OpenAI(**client_kwargs)
    elif self.config.provider == "bailian":
        # Nuovo provider bailian - usa OpenAI-compatible endpoint
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url="https://coding-intl.dashscope.aliyuncs.com/v1"
        )
    elif self.config.provider == "qwen":
        # Legacy - nativo DashScope (deprecato)
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
```

### 3. ebooks.py - BaseAgent.call_ai()

**Posizione**: Linee 740-778

**Modifiche**:
- Aggiungere caso `bailian` che usa lo stesso formato di `openai`
- Il provider bailian usa API OpenAI-compatible

```python
def call_ai(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
    max_tokens = max_tokens or self.config.max_tokens_per_call
    retries = 3
    for attempt in range(retries):
        try:
            if self.config.provider in ["openai", "bailian"]:
                # Entrambi usano client OpenAI (bailian è OpenAI-compatible)
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()
            elif self.config.provider == "qwen":
                # Legacy - nativo DashScope
                ...
```

### 4. ebooks.py - Argomenti CLI

**Posizione**: Linee 1039-1044

**Modifiche**:
- Aggiornare choices per includere `bailian`
- Aggiornare help text

```python
parser.add_argument("--provider", choices=["openai", "qwen", "bailian"], default="openai",
                    help="Provider AI (openai, bailian per Coding Plan, qwen per DashScope legacy)")
```

### 5. ebooks.py - Logica Default Model

**Posizione**: Linee 1049-1054

**Modifiche**:
- Aggiungere default model per bailian

```python
if not args.model:
    if args.provider == "openai":
        args.model = "gpt-4"
    elif args.provider == "bailian":
        args.model = "qwen3.5-plus"
    else:  # qwen
        args.model = "qwen-max"
```

### 6. .env.example

**Aggiungere**:
```bash
# =============================================================================
# BAILIAN API (Alibaba Cloud Coding Plan - OpenClaw)
# =============================================================================
# Ottieni la tua chiave da: https://dashscope.aliyun.com/
# Endpoint: https://coding-intl.dashscope.aliyuncs.com/v1
BAILIAN_API_KEY=your-bailian-api-key-here
```

### 7. requirements.txt

Nessuna modifica richiesta - le dipendenze esistenti (`openai>=1.0.0`) sono sufficienti.

### 8. ARCHITECTURE.md

**Aggiornare sezione Configurazione** (Linee 152-176):
- Aggiungere documentazione provider `bailian`
- Aggiornare esempio endpoint

### 9. README.md

**Aggiornare sezioni**:
- Requisiti di Sistema: nessuna modifica
- Installazione: aggiungere `BAILIAN_API_KEY`
- Guida Rapida: aggiungere esempio bailian
- Configurazione: aggiornare tabella parametri
- Troubleshooting: aggiungere sezione bailian

## Schema di Richiesta/Risposta

### Richiesta (OpenAI-compatible)
```json
{
  "model": "qwen3.5-plus",
  "messages": [
    {"role": "system", "content": "Sei un assistente utile."},
    {"role": "user", "content": "prompt qui"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### Risposta (OpenAI-compatible)
```json
{
  "choices": [
    {
      "message": {
        "content": "risposta generata",
        "role": "assistant"
      }
    }
  ]
}
```

## Dipendenze

Nessuna dipendenza aggiuntiva richiesta. Il provider `bailian` usa la libreria `openai` già presente.

## Retrocompatibilità

- Il provider `qwen` esistente continua a funzionare (nativo DashScope)
- `DASHSCOPE_API_KEY` è ancora supportato come fallback per `bailian`
- Gli endpoint personalizzati (`--endpoint`) continuano a funzionare con provider `openai`

## Test Consigliati

1. Testare provider `bailian` con modello `qwen3.5-plus`
2. Testare provider `bailian` con modello `kimi-k2.5`
3. Verificare retrocompatibilità provider `qwen`
4. Verificare provider `openai` con endpoint custom bailian
5. Testare error handling per API key mancanti

## Esempi di Utilizzo

### Nuovo provider bailian (raccomandato)
```bash
python ebooks.py \
    --topic "Intelligenza Artificiale" \
    --pages 400 \
    --provider bailian \
    --model "qwen3.5-plus" \
    --output "libro.md"
```

### Provider openai con endpoint bailian (alternativa)
```bash
python ebooks.py \
    --topic "Intelligenza Artificiale" \
    --pages 400 \
    --provider openai \
    --endpoint "https://coding-intl.dashscope.aliyuncs.com/v1" \
    --model "qwen3.5-plus" \
    --output "libro.md"
```

### Legacy qwen (deprecato ma funzionante)
```bash
python ebooks.py \
    --topic "Intelligenza Artificiale" \
    --pages 400 \
    --provider qwen \
    --model "qwen-max" \
    --output "libro.md"
```
