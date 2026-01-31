# Neural LAB Python SDK

**PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED**

Python SDK for Neural LAB AI Platform APIs.

## Proprietary Notice

```
Copyright (c) 2026 Neural Thinker | AI Engineering LTDA
CNPJ: 62.155.930/0001-71
Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil

This software is proprietary and confidential.
Unauthorized copying, distribution, or use is strictly prohibited.
```

## Installation

```bash
pip install ntlabs
```

### Optional Dependencies

```bash
# Full installation with all features
pip install ntlabs[full]

# Specific features
pip install ntlabs[cache]        # Redis caching
pip install ntlabs[email]        # Email templates
pip install ntlabs[export]       # PDF/Excel export
pip install ntlabs[middleware]   # FastAPI middleware
pip install ntlabs[observability] # Sentry + OpenTelemetry
```

### For Local Development

```bash
pip install -e /path/to/neural-lab/packages/python-sdk[dev]
```

## Quick Start

```python
from neural_lab import NeuralLabClient

# Initialize client
client = NeuralLabClient(api_key="nl_hipo_xxx")

# Or use environment variable NEURAL_LAB_API_KEY
client = NeuralLabClient()
```

## Available Resources

### Chat (LLM)

```python
response = client.chat.complete(
    messages=[
        {"role": "system", "content": "Você é um assistente médico."},
        {"role": "user", "content": "O que é hipertensão?"}
    ],
    model="maritaca-sabia-3",
    max_tokens=1024,
)
```

### Email

```python
client.email.send(
    to=["paciente@email.com"],
    subject="Confirmação de Consulta",
    html="<h1>Sua consulta foi agendada</h1>",
)
```

### Transcription

```python
result = client.transcribe.audio("consulta.mp3", language="pt")
print(result.text)
```

### Government APIs

```python
# CNPJ lookup
empresa = client.gov.cnpj("12.345.678/0001-90")

# CEP lookup
endereco = client.gov.cep("01310-100")

# CPF validation
valido = client.gov.validate_cpf("123.456.789-00")

# Portal da Transparência
contratos = client.gov.transparencia("contratos", params={"uf": "MG"})
```

### Banco do Brasil (OAuth + PIX)

```python
from decimal import Decimal

# OAuth - Get authorization URL
auth = client.bb.get_authorize_url(redirect_uri="https://app.com/callback")
# Redirect user to auth.authorize_url

# OAuth - Exchange code for tokens
tokens = client.bb.exchange_code(code="abc", state="xyz", redirect_uri="...")

# Get user info (CPF verified by bank)
user = client.bb.get_userinfo(tokens.access_token)
print(f"CPF: {user.cpf}, Nome: {user.nome}")

# PIX - Create charge
charge = client.bb.create_pix_charge(
    amount=Decimal("99.90"),
    description="Consulta Médica",
)
print(f"QR Code: {charge.qr_code}")

# PIX - Check status
status = client.bb.get_pix_status(charge.txid)
if status.status == "CONCLUIDA":
    print(f"Pago em: {status.paid_at}")
```

### Medical AI (Hipócrates)

```python
# Transcribe consultation
transcription = client.saude.transcribe(audio_file)

# Generate SOAP note
soap = client.saude.generate_soap(
    transcription=transcription.text,
    paciente={"idade": 45, "sexo": "M"},
)
```

### Notary AI (Mercurius)

```python
# OCR certificate
result = client.cartorio.ocr(image_file, tipo="nascimento")

# Generate deed
minuta = client.cartorio.generate_escritura(dados)
```

### Billing

```python
usage = client.billing.get_usage()
print(f"Total: R$ {usage.total_cost}")
```

### Authentication (OAuth v2 with PKCE)

```python
# Initiate OAuth flow (returns URL for redirect)
oauth = client.auth.initiate_oauth_v2(
    provider="github",  # or "google"
    redirect_uri="https://myapp.com/auth/callback",
    product="hipocrates",
)
# Redirect user to: oauth["authorization_url"]

# After callback, claim the session (frontend receives sid + sig in URL)
session = client.auth.claim_session(
    session_id="sess_xxx",
    signature="hmac_xxx",
)
print(f"Token: {session['access_token']}")
print(f"User: {session['user']['email']}")

# Validate a session
validation = client.auth.validate_session(
    session_id="sess_xxx",
    product="hipocrates",
)
if validation["valid"]:
    print(f"User: {validation['user']['email']}")

# Check SSO (for cross-product auth)
sso = client.auth.check_sso(product="mercurius")
if sso["has_valid_session"]:
    print("User already authenticated via SSO")

# Refresh tokens (with rotation)
new_tokens = client.auth.refresh_v2(
    refresh_token="old_refresh_token",
    session_id="sess_xxx",
)

# Logout (single session)
client.auth.revoke_session(session_id="sess_xxx")

# Global logout (all sessions)
client.auth.revoke_session(revoke_all=True)
```

### SSO Cross-Product Navigation

```python
# Create ticket for navigating to another product
ticket = client.auth.create_sso_ticket(target_product="mercurius")
# Redirect to: https://mercurius.app/auth?sso_ticket={ticket['ticket']}

# On target product: exchange ticket for session
session = client.auth.exchange_sso_ticket(
    ticket="ticket_xxx",
    target_product="mercurius",
)
```

## Environment Variables

| Variable             | Description                                     |
| -------------------- | ----------------------------------------------- |
| `NEURAL_LAB_API_KEY` | API key (nl_hipo_xxx, nl_merc_xxx, nl_poli_xxx) |
| `NEURAL_LAB_API_URL` | API URL (default: production)                   |

## Error Handling

```python
from neural_lab import (
    NeuralLabClient,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    APIError,
)

try:
    response = client.chat.complete(messages=[...])
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except InsufficientCreditsError:
    print("Add more credits")
except APIError as e:
    print(f"API error: {e}")
```

## License

**Proprietary Software**

Copyright (c) 2026 Neural Thinker | AI Engineering LTDA

All rights reserved. This software and its documentation are proprietary
and confidential. No part of this software may be reproduced, distributed,
or transmitted in any form or by any means without the prior written
permission of Neural Thinker | AI Engineering LTDA.

For licensing inquiries: contato@neural-lab.com.br
