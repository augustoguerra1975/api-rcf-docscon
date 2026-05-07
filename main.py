import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 1. PERMISSÕES DE ACESSO
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. INICIALIZAÇÃO DO MOTOR (ORDEM CORRETA)
db = None

try:
    if not firebase_admin._apps:
        firebase_json = os.getenv("FIREBASE_JSON")
        if firebase_json:
            cred_dict = json.loads(firebase_json)
            # Limpeza da chave privada
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            # O CLIENTE SÓ É CRIADO APÓS A INICIALIZAÇÃO
            db = firestore.client()
            print("--- SISTEMA RCF: CONECTADO COM SUCESSO ---")
        else:
            print("--- ERRO: Variável FIREBASE_JSON não encontrada no Render ---")
except Exception as e:
    print(f"--- ERRO CRÍTICO: {str(e)} ---")

# 3. ROTAS DA API
@app.get("/")
def root():
    return {"status": "Online", "msg": "API RCF Investimentos - Versão Final"}

@app.get("/api/cotas")
def listar_cotas():
    if db is None:
        return {"erro": "Banco de dados não inicializado. Verifique os logs do Render."}
    
    try:
        # Busca os documentos no Firebase
        docs = db.collection("cotas_contempladas").get(timeout=10)
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]
    except Exception as e:
        return {"erro_tecnico": str(e)}

@app.post("/webhook-docscon")
async def receber_cota(request: Request):
    if db is None:
        return {"status": "erro", "msg": "DB offline"}
    
    try:
        dados = await request.json()
        cota_id = str(dados.get("id", "sem_id"))
        db.collection("cotas_contempladas").document(cota_id).set(dados)
        return {"status": "sucesso"}
    except Exception as e:
        return {"status": "erro", "msg": str(e)}
