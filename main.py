import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 1. PERMISSÕES PARA O SITE ACESSAR A API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. INICIALIZAÇÃO SEGURA
try:
    if not firebase_admin._apps:
        firebase_json = os.getenv("FIREBASE_JSON")
        if firebase_json:
            cred_dict = json.loads(firebase_json)
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Erro Firebase: {e}")

db = firestore.client()

@app.get("/")
def root():
    return {"status": "Online", "msg": "API RCF Pronta para Uso"}

# 3. ROTA QUE O SITE USA PARA MOSTRAR AS CARTAS
@app.get("/api/cotas")
def listar_cotas():
    try:
        # Busca todas as cartas da coleção
        docs = db.collection("cotas_contempladas").get(timeout=10)
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]
    except Exception as e:
        return {"erro": str(e)}

@app.post("/webhook-docscon")
async def receber_cota(request: Request):
    dados = await request.json()
    cota_id = str(dados.get("id", "sem_id"))
    db.collection("cotas_contempladas").document(cota_id).set(dados)
    return {"status": "sucesso"}
