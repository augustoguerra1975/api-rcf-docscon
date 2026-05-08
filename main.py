import os
import httpx
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

# 2. INICIALIZAÇÃO DO FIREBASE (Sua chave já está ok no Render)
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
            print("--- MOTOR FIREBASE PRONTO ---")
except Exception as e:
    print(f"--- ERRO FIREBASE: {str(e)} ---")

# 3. ROTAS
@app.get("/")
def root():
    return {"status": "Online", "msg": "API RCF - Integração Aberta"}

@app.get("/api/cotas")
def listar_cotas():
    if not db: return {"erro": "Banco offline"}
    try:
        docs = db.collection("cotas_contempladas").get(timeout=10)
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]
    except Exception as e:
        return {"erro": str(e)}

# ✨ SINCRONIZAÇÃO ABERTA (Sem Token)
@app.get("/api/sincronizar")
async def sincronizar():
    if not db: return {"erro": "DB Offline"}
    
    # URL pública que você forneceu
    url = "https://app.dwconsorcios.com.br/api/v1/contemplados"

    async with httpx.AsyncClient() as client:
        try:
            # Chamada direta, sem cabeçalhos de autenticação
            res = await client.get(url, timeout=30.0)
            
            if res.status_code != 200:
                return {"erro": f"Erro na API DW: {res.status_code}"}
                
            cartas = res.json()
            
            # Gravação em lote no seu Firebase
            for carta in cartas:
                c_id = str(carta.get("id", "cota_id"))
                db.collection("cotas_contempladas").document(c_id).set(carta)
            
            return {"status": "Sucesso", "total_importado": len(cartas)}
        except Exception as e:
            return {"erro_sync": str(e)}

@app.post("/webhook-docscon")
async def webhook(request: Request):
    if not db: return {"status": "offline"}
    dados = await request.json()
    c_id = str(dados.get("id", "sem_id"))
    db.collection("cotas_contempladas").document(c_id).set(dados)
    return {"status": "recebido"}
