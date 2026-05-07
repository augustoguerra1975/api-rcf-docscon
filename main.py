from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore

# 1. CONFIGURAÇÃO FIREBASE
firebase_creds = {
  "type": "service_account",
  "project_id": "renan-d5f4b",
  "private_key_id": "fcaa0516ec7fe6317df3d73c4ca84d0810a2431c",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC3QFPpGTdYET4d\nGhKgXEVi60fXN2Ov3J7hcK1ljyzwKRQL6hXLhWr4nK3tD6zxPR1u7dW5EMMJ4iTa\n0CJW03u9RgGJ704h22Z7Bt+kqBpuzqeO5VIqYTIi9f89rivCWsK0B94HIDilJafI\nOqdFm7rI50aT2Xf/Uk2kja4mmVVHjYoZUhatGMvjQbmgmO0+l3W4LF5sNz2T1d9V\nYuH3o2nhXT47fTokerchcoKozKGIkuuWEctCO0IvfdC0Ydz7vCaSc5ZzQ+UwfFEm\nDrkF/5cKrG1VusnRi4Bm3QJqDXHyHM0f8vBb0j2cYNL06IygXQXrlqn1xRHKOrNi\nETbmj9nRAgMBAAECggEAIFTIaTQyfEaAhbxrpGDbOh5mTK2gWC8N1hsd8LDv3gh1\nWbvJcCDANJBaLFzrZ52fg4qRPmdbbfM5CuUVZenGp2iCTX6L87PEsziNfTzOexXZ\nYMALfOAsqxfpWk3QOShvuTk5Hls8O0D3Rv+4MvMMo7UQUfYYspKoEbwQiY1cizS8\nhC1htYtYvYjDv31Sqnou76JO5lYpgMz0gdWsNC3NZMSOGJPCEEVpaCbb/6+5Gb+e\ntq806uGfLNwc3SYbB8mXqnst9eDdTbbM/d1Zf9rRiK6N7DmoTPE0PpDcY14LGPKt\nDcDm8Nfnv6WU0tGeixRqZIgPZBcMI8+CyfxnYD9wdQKBgQDcNVhj6gfAfe7mwnlZ\npC2S1e42/jqmvxiV60VimGu+H1b4mUMK8whCpqQXb84onyZta42udXtFTD6CtOSD\nN1mKmKaxj/7+S9djPcDMKrPmpH78UrILaf9VHTcdedp1s70dHvXR7rznipQyGsPQ\ncT+5YsWlqMyzMU9je8Ie0zAnhQKBgQDVCTvcYDiV/Vv2F6iD08gnsCPUKFw/tfAe\ne+rZ7wGGmvcMVnvcFvwXHRkgjHlITGP5rFd0KDFtPk2QPxDFlghBuF5sCPMq+NsX\nJpUWHZqIQ8UX0H39zk4UJTVsfcUPifWdTAzRQGFkDMFSKbuVe/2+lD3l1pEGk78D\nX2IWdi2M3QKBgE6eZQ5W8amRzIdqizSr3vF7m27a2UnLFBYCR2VqEZ1xRvW+kicI\nmbxiDlenvSzXlTqfmZfdrcMR84dq2eLXEgrfcTQXuuxDW4S8+WZrIIuJ0yR2ycY1\nc8mJgrHtXUeEglIxSYZH+/2Whk5VK+/xXtTrJLF+UIbxZeyYtLeYoqqZAoGAcvH9\ng4XDYmKG2Pyg5yhBCfEHE/UG+TVQrxILgLVt7FP20ohjYjhgopQHt8Ezu2fEVbXA\npiL9sET6kscEZKf0Iom5IK+fjOMjS5V8wacNd1KhqJzNLkG/bS06ayRdTGoSxWGA\nVPNY2SPst0lfNmPlYIwZ7cZdD+BuIwK3KQlwwF0CgYEAj/8g9zNO1L7uNDPB8zkp\nh/t3ZbHEgvPXX8l92B+ragyRnkPQD3XwWwcqW1zdsfVKo1DoUKep/mPgpQ/nqFPs\nnGx9tP1+Z+GCTOqA2Pb4iAyNC8aN6bVKBko9gu0yyy9oVBJ0inTTfJ730iajVHrM\n77FuEwlA+cWVbDaUZNhN0K8=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@renan-d5f4b.iam.gserviceaccount.com",
}

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

# ATIVAR PERMISSÃO PARA O SITE (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/webhook-docscon")
async def receber_cota(request: Request):
    dados = await request.json()
    cota_id = str(dados.get("id", "sem_id"))
    info_cota = {
        "administradora": dados.get("administradora_nome"),
        "valor_credito": dados.get("valor_credito"),
        "valor_entrada": dados.get("valor_entrada"),
        "valor_parcela": dados.get("valor_parcela"),
        "parcelas_restantes": dados.get("parcelas_restantes"),
        "status": dados.get("status_nome"),
        "categoria": dados.get("categoria_nome", "Imóvel")
    }
    db.collection("cotas_contempladas").document(cota_id).set(info_cota)
    return {"status": "sucesso"}

# ROTA QUE ENTREGA OS DADOS PARA O SITE
@app.get("/api/cotas")
async def listar_cotas():
    cotas_ref = db.collection("cotas_contempladas")
    docs = cotas_ref.stream()
    return [doc.to_dict() for doc in docs]
