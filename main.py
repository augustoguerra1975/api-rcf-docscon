from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore
import os

# 1. DICIONÁRIO COMPLETO DO FIREBASE (NÃO ALTERAR NADA AQUI)
firebase_creds = {
  "type": "service_account",
  "project_id": "renan-d5f4b",
  "private_key_id": "fcaa0516ec7fe6317df3d73c4ca84d0810a2431c",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC3QFPpGTdYET4d\nGhKgXEVi60fXN2Ov3J7hcK1ljyzwKRQL6hXLhWr4nK3tD6zxPR1u7dW5EMMJ4iTa\n0CJW03u9RgGJ704h22Z7Bt+kqBpuzqeO5VIqYTIi9f89rivCWsK0B94HIDilJafI\nOqdFm7rI50aT2Xf/Uk2kja4mmVVHjYoZUhatGMvjQbmgmO0+l3W4LF5sNz2T1d9V\nYuH3o2nhXT47fTokerchcoKozKGIkuuWEctCO0IvfdC0Ydz7vCaSc5ZzQ+UwfFEm\nDrkF/5cKrG1VusnRi4Bm3QJqDXHyHM0f8vBb0j2cYNL06IygXQXrlqn1xRHKOrNi\nETbmj9nRAgMBAAECggEAIFTIaTQyfEaAhbxrpGDbOh5mTK2gWC8N1hsd8LDv3gh1\nWbvJcCDANJBaLFzrZ52fg4qRPmdbbfM5CuUVZenGp2iCTX6L87PEsziNfTzOexXZ\nYMALfOAsqxfpWk3QOShvuTk5Hls8O0D3Rv+4MvMMo7UQUfYYspKoEbwQiY1cizS8\nhC1htYtYvYjDv31Sqnou76JO5lYpgMz0gdWsNC3NZMSOGJPCEEVpaCbb/6+5Gb+e\ntq806uGfLNwc3SYbB8mXqnst9eDdTbbM/d1Zf9rRiK6N7DmoTPE0PpDcY14LGPKt\nDcDm8Nfnv6WU0tGeixRqZIgPZBcMI8+CyfxnYD9wdQKBgQDcNVhj6gfAfe7mwnlZ\npC2S1e42/jqmvxiV60VimGu+H1b4mUMK8whCpqQXb84onyZta42udXtFTD6CtOSD\nN1mKmKaxj/7+S9djPcDMKrPmpH78UrILaf9VHTcdedp1s70dHvXR7rznipQyGsPQ\ncT+5YsWlqMyzMU9je8Ie0zAnhQKBgQDVCTvcYDiV/Vv2F6iD08gnsCPUKFw/tfAe\ne+rZ7wGGmvcMVnvcFvwXHRkgjHlITGP5rFd0KDFtPk2QPxDFlghBuF5sCPMq+NsX\nJpUWHZqIQ8UX0H39zk4UJTVsfcUPifWdTAzRQGFkDMFSKbuVe/2+lD3l1pEGk78D\nX2IWdi2M3QKBgE6eZQ5W8amRzIdqizSr3vF7m27a2UnLFBYCR2VqEZ1xRvW+kicI\mbxiDlenvSzXlTqfmZfdrcMR84dq2eLXEgrfcTQXuuxDW4S8+WZrIIuJ0yR2ycY1\nc8mJgrHtXUeEglIxSYZH+/2Whk5VK+/xXtTrJLF+UIbxZeyYtLeYoqqZAoGAcvH9\ng4XDYmKG2Pyg5yhBCfEHE/UG+TVQrxILgLVt7FP20ohjYjhgopQHt8Ezu2fEVbXA\npiL9sET6kscEZKf0Iom5IK+fjOMjS5V8wacNd1KhqJzNLkG/bS06ayRdTGoSxWGA\nVPNY2SPst0lfNmPlYIwZ7cZdD+BuIwK3KQlwwF0CgYEAj/8g9zNO1L7uNDPB8zkp\nh/t3ZbHEgvPXX8l92B+ragyRnkPQD3XwWwcqW1zdsfVKo1DoUKep/mPgpQ/nqFPs\nnGx9tP1+Z+GCTOqA2Pb4iAyNC8aN6bVKBko9gu0yyy9oVBJ0inTTfJ730iajVHrM\n77FuEwlA+cWVbDaUZNhN0K8=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@renan-d5f4b.iam.gserviceaccount.com",
  "client_id": "114613657016099860835",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40renan-d5f4b.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# 2. LIMPEZA DA CHAVE (Obrigatório para o Render não se perder)
if "\\n" in firebase_creds["private_key"]:
    firebase_creds["private_key"] = firebase_creds["private_key"].replace("\\n", "\n")

# 3. INICIALIZAÇÃO SEGURA
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Erro Crítico Firebase: {e}")

db = firestore.client()
app = FastAPI()

# 4. PERMISSÕES DE ACESSO (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "Online", "empresa": "RCF Investimentos"}

@app.get("/api/cotas")
async def listar_cotas():
    docs = db.collection("cotas_contempladas").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

@app.post("/webhook-docscon")
async def receber_cota(request: Request):
    dados = await request.json()
    cota_id = str(dados.get("id", "sem_id"))
    db.collection("cotas_contempladas").document(cota_id).set(dados)
    return {"status": "sucesso"}
