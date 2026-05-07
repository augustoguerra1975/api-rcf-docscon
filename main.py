import os
import json
import httpx # Importante para buscar dados da Docscon
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# INICIALIZAÇÃO DO FIREBASE
db = None
try:
    if not firebase_admin._apps:
        chv = os.getenv("FIREBASE_PRIVATE_KEY", "")
        chv_limpa = chv.strip().replace("\\n", "\n").replace('"', '')
        
        if chv_limpa:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": "renan-d5f4b",
                "private_key": chv_limpa,
                "client_email": "firebase-adminsdk-fbsvc@renan-d5f4b.iam.gserviceaccount.com",
                "token_uri": "https://oauth2.googleapis.com/token",
            })
            firebase_app = firebase_admin.initialize_app(cred)
            db = firestore.client(app=firebase_app)
except Exception as e:
    print(f"Erro Firebase: {e}")

@app.get("/")
def root():
    return {"status": "Online", "msg": "API RCF Pronta"}

@app.get("/api/cotas")
def listar_cotas():
    if not db: return {"erro": "DB Offline"}
    docs = db.collection("cotas_contempladas").get(timeout=10)
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

# ✨ NOVA FUNÇÃO: SINCRONIZAR TUDO DA DOCSCON
@app.get("/api/sincronizar")
async def sincronizar_docscon():
    # ⚠️ SUBSTITUA PELO SEU TOKEN DA DOCSCON ABAIXO
    TOKEN_DOCSCON = "SEU_TOKEN_AQUI" 
    URL_DOCSCON = "https://api.docscon.com.br/v1/contempladas"

    async with httpx.AsyncClient() as client:
        try:
            # 1. Busca os dados lá na Docscon
            response = await client.get(URL_DOCSCON, headers={"X-Token": TOKEN_DOCSCON})
            cartas = response.json()

            # 2. Salva cada carta no seu Firebase
            count = 0
            for carta in cartas:
                cota_id = str(carta.get("id", f"cota_{count}"))
                db.collection("cotas_contempladas").document(cota_id).set(carta)
                count += 1

            return {"status": "Sucesso", "total_importado": count}
        except Exception as e:
            return {"status": "Erro na sincronização", "detalhe": str(e)}

@app.post("/webhook-docscon")
async def receber_cota(request: Request):
    if not db: return {"status": "erro"}
    dados = await request.json()
    cota_id = str(dados.get("id", "sem_id"))
    db.collection("cotas_contempladas").document(cota_id).set(dados)
    return {"status": "sucesso"}
