# 🔐 SSI Empoorio ID Python SDK

**Complete Self-Sovereign Identity SDK for Python applications**

[![PyPI version](https://badge.fury.io/py/ssi-empoorio-id.svg)](https://pypi.org/project/ssi-empoorio-id/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.empoorio.id/python-sdk)

## ✨ Características

- ✅ **Verifiable Credentials**: Emisión, verificación y revocación completa
- ✅ **Biometric Authentication**: Soporte para WebAuthn/FIDO2
- ✅ **Zero-Knowledge Proofs**: Privacidad con selective disclosure
- ✅ **Quantum-Resistant**: Integración con algoritmos post-cuánticos
- ✅ **Async/Await**: Soporte completo para operaciones asíncronas
- ✅ **Type Hints**: Completamente tipado para mejor DX
- ✅ **CLI Tool**: Herramienta de línea de comandos integrada

## 🚀 Instalación

### Desde PyPI (Recomendado)
```bash
pip install ssi-empoorio-id
```

### Desde GitHub
```bash
pip install git+https://github.com/empoorio/ssi-empoorio-id.git#subdirectory=sdks/python
```

### Desarrollo
```bash
git clone https://github.com/empoorio/ssi-empoorio-id.git
cd ssi-empoorio-id/sdks/python
pip install -e .[dev]
```

## 📖 Uso Rápido

### 1. Importar y Configurar
```python
from ssi_empoorio_id import SSIEmporioSDK

# Configuración básica
ssi = SSIEmporioSDK(
    issuer_url='https://api.empoorio.id',
    verifier_url='https://verify.empoorio.id',
    api_key='your-api-key'  # opcional
)
```

### 2. Emitir Verifiable Credential
```python
# Datos del credential
subject = {
    'id': 'did:emp:user123',
    'name': 'Juan Pérez',
    'email': 'juan@email.com',
    'age': 30,
    'nationality': 'Mexican'
}

# Emitir credential
vc = ssi.issue_credential(
    subject=subject,
    credential_type=['VerifiableCredential', 'IdentityCredential'],
    options={
        'quantum_resistant': True,  # Firma post-cuántica
        'zkp_enabled': True,        # Zero-knowledge proofs
        'expiration_date': '2027-01-01T00:00:00Z'
    }
)

print(f'VC emitido: {vc.id}')
```

### 3. Verificar Credential
```python
verification = ssi.verify_credential(vc, {
    'checks': ['signature', 'expiration', 'revocation', 'quantum_resistance']
})

if verification.verified:
    print('✅ Credential válido')
    # Proceder con autenticación
else:
    print('❌ Errores:', verification.errors)
```

### 4. Autenticación Biométrica (Web)
```python
# Para aplicaciones web, la biometría se maneja en el frontend
# El SDK Python puede verificar credenciales biométricas

biometric_subject = ssi.create_biometric_credential(
    user_id='user123',
    biometric_data={
        'type': 'fingerprint',
        'level': 'high',
        'platform': 'Android',
        'user_agent': 'Mozilla/5.0...'
    },
    options={
        'selective_disclosure': True
    }
)

# Crear VC biométrico completo
biometric_vc = ssi.issue_credential(
    subject=biometric_subject,
    credential_type=['VerifiableCredential', 'BiometricCredential']
)
```

## 🛠️ CLI Tool

El SDK incluye un CLI completo que funciona en cualquier terminal.

### Comandos Principales

#### Verifiable Credentials
```bash
# Emitir VC desde archivo JSON
ssi-python vc issue subject.json -t VerifiableCredential,KYC -q -z

# Verificar VC
ssi-python vc verify credential.json -c signature,expiration,revocation

# Revocar VC
ssi-python vc revoke vc-id-123 -r "Usuario solicitó"

# Ver status de VC
ssi-python vc status vc-id-123
```

#### DIDs
```bash
# Generar DID
ssi-python did create -p bank

# Validar DID
ssi-python did validate did:emp:user123
```

#### Utilidades
```bash
# Generar UUID
ssi-python util uuid

# Crear template
ssi-python util template subject.json -i did:emp:issuer -t VerifiableCredential

# Validar formato
ssi-python util validate-format credential.json
```

#### Desarrollo
```bash
# Test API
ssi-python dev test-api

# Demo interactivo
ssi-python dev demo
```

## 🏗️ Arquitectura

```
ssi_empoorio_id/
├── __init__.py          # Exports principales
├── sdk.py              # SDK principal (sync/async)
├── utils.py            # Utilidades
├── cli.py              # CLI tool
└── types.py            # Type hints
```

### Clases Principales

#### SSIEmporioSDK
Cliente principal para todas las operaciones SSI.

#### AsyncSSIEmporioSDK
Versión asíncrona del SDK para mejor performance.

#### Utilidades
Funciones helper para desarrollo SSI.

## 🔧 API Reference

### SSIEmporioSDK

#### Constructor
```python
SSIEmporioSDK(
    issuer_url: str = "http://localhost:3001",
    verifier_url: str = "http://localhost:3002",
    api_key: Optional[str] = None,
    timeout: float = 30.0,
    session: Optional[requests.Session] = None
)
```

#### Verifiable Credentials
```python
# Emisión
issue_credential(subject: dict, credential_type: List[str], options: dict = None) -> VerifiableCredential

# Emisión batch
issue_credentials_batch(credentials: List[dict], options: dict = None) -> List[VerifiableCredential]

# Verificación
verify_credential(vc: Union[VerifiableCredential, dict], options: dict = None) -> VerificationResult

# Revocación
revoke_credential(vc_id: str, reason: str = None) -> dict

# Status
get_credential_status(vc_id: str) -> dict
```

#### Biometric Operations
```python
# Crear VC biométrico
create_biometric_credential(user_id: str, biometric_data: dict, options: dict = None) -> dict

# Verificar VC biométrico
verify_biometric_credential(credential: dict, required_level: str = 'basic') -> dict

# Métodos soportados
get_biometric_methods() -> dict

# Gestión de credenciales
get_user_biometric_credentials(user_id: str) -> List[dict]
delete_biometric_credential(credential_id: str) -> dict
```

#### Utilidades
```python
# DID operations
create_test_did(prefix: str = 'emp') -> str
validate_did(did: str) -> bool

# VC utilities
extract_claims(vc: VerifiableCredential) -> dict
is_credential_expired(vc: VerifiableCredential) -> bool
get_issuer_did(vc: VerifiableCredential) -> str
get_subject_did(vc: VerifiableCredential) -> str
```

### AsyncSSIEmporioSDK

Versión asíncrona con todas las mismas funcionalidades:
```python
async def issue_credential(self, subject: dict, credential_type: List[str], options: dict = None) -> VerifiableCredential:
    # Implementación asíncrona
    pass
```

## 🎯 Ejemplos Completos

### Aplicación Web con FastAPI
```python
# main.py
from fastapi import FastAPI, HTTPException
from ssi_empoorio_id import SSIEmporioSDK
from pydantic import BaseModel

app = FastAPI()
ssi = SSIEmporioSDK()

class CredentialRequest(BaseModel):
    subject: dict
    types: list[str]
    options: dict = None

@app.post("/vc/issue")
async def issue_vc(request: CredentialRequest):
    try:
        vc = ssi.issue_credential(
            subject=request.subject,
            credential_type=request.types,
            options=request.options
        )
        return {"success": True, "vc": vc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vc/verify")
async def verify_vc(vc: dict):
    try:
        result = ssi.verify_credential(vc)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Aplicación de Línea de Comandos
```python
#!/usr/bin/env python3
# cli_app.py
import asyncio
from ssi_empoorio_id import AsyncSSIEmporioSDK

async def main():
    ssi = AsyncSSIEmporioSDK(
        issuer_url='https://api.empoorio.id'
    )

    # Crear VC
    subject = {
        'id': 'did:emp:user123',
        'name': 'Juan Pérez',
        'email': 'juan@email.com'
    }

    vc = await ssi.issue_credential(
        subject=subject,
        credential_type=['VerifiableCredential', 'IdentityCredential']
    )

    print(f"VC creado: {vc.id}")

    # Verificar VC
    verification = await ssi.verify_credential(vc)
    print(f"Verificado: {verification.verified}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Integración con Django
```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from ssi_empoorio_id import SSIEmporioSDK

ssi = SSIEmporioSDK()

@method_decorator(csrf_exempt, name='dispatch')
class SSIView(View):
    def post(self, request, action):
        try:
            data = json.loads(request.body)

            if action == 'issue':
                vc = ssi.issue_credential(
                    subject=data['subject'],
                    credential_type=data['types'],
                    options=data.get('options')
                )
                return JsonResponse({'success': True, 'vc': vc})

            elif action == 'verify':
                result = ssi.verify_credential(data['vc'])
                return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

## 🔧 Desarrollo y Testing

### Configuración del Entorno
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -e .[dev]
```

### Ejecutar Tests
```bash
# Todos los tests
pytest

# Tests con cobertura
pytest --cov=ssi_empoorio_id --cov-report=html

# Tests específicos
pytest tests/test_vc.py -v

# Tests asíncronos
pytest tests/test_async.py -v
```

### Desarrollo Interactivo
```python
# Iniciar REPL con SDK
python -c "from ssi_empoorio_id import SSIEmporioSDK; ssi = SSIEmporioSDK(); print('SDK listo!')"

# Ejecutar CLI
python -m ssi_empoorio_id.cli vc issue subject.json
```

## 🚀 Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["python", "main.py"]
```

### Producción con Gunicorn
```bash
# Instalar
pip install gunicorn

# Ejecutar
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

## 📚 Documentación Adicional

- **[Guía de Integración](https://docs.empoorio.id/integration)**: Cómo integrar SSI
- **[Autenticación Biométrica](https://docs.empoorio.id/biometric)**: Guía completa de biometría
- **[API Reference](https://api.empoorio.id/docs)**: Referencia técnica completa

## 🤝 Contribuir

```bash
# Clonar
git clone https://github.com/empoorio/ssi-empoorio-id.git
cd ssi-empoorio-id/sdks/python

# Instalar dependencias de desarrollo
pip install -e .[dev]

# Ejecutar tests
pytest

# Formatear código
black ssi_empoorio_id/
isort ssi_empoorio_id/

# Type checking
mypy ssi_empoorio_id/
```

## 📄 Licencia

MIT License - ver [LICENSE](../../LICENSE)

## 🆘 Soporte

- **📧 Email**: sdk@empoorio.id
- **🐛 Issues**: https://github.com/empoorio/ssi-empoorio-id/issues
- **📖 Docs**: https://docs.empoorio.id/python-sdk

---

**🚀 El SDK Python más completo para Self-Sovereign Identity.**