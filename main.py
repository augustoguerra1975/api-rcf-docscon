import os
import httpx
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

# INICIALIZAÇÃO FIREBASE
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

@app.get("/api/cotas")
def listar_cotas():
    if not db: return {"erro": "DB Offline"}
    docs = db.collection("cotas_contempladas").get(timeout=10)
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

# SINCRONIZAÇÃO COM LOG DE QUANTIDADE
@app.get("/api/sincronizar")
async def sincronizar():
    if not db: return {"erro": "DB Offline"}
    
    # IMPORTANTE: Se não colocar o Token, a DW só manda 1 carta de exemplo
    token = os.getenv("DOCSCON_TOKEN")
    url = "https://app.dwconsorcios.com.br/api/v1/contemplados"

    async with httpx.AsyncClient() as client:
        try:
            # Se houver token, ele envia. Se não, vai "aberto" e recebe só o exemplo.
            headers = {"X-Token": token} if token else {}
            res = await client.get(url, headers=headers, timeout=30.0)
            cartas = res.json()
            
            print(f"--- DEBUG: Recebidas {len(cartas)} cartas da DW ---")

            for carta in cartas:
                c_id = str(carta.get("id", f"cota_{carta.get('numero_proposta', 'ex')}"))
                db.collection("cotas_contempladas").document(c_id).set(carta)
            
            return {"status": "Sucesso", "total_recebido": len(cartas), "aviso": "Se veio apenas 1, voce precisa configurar o DOCSCON_TOKEN no Render."}
        except Exception as e:
            return {"erro": str(e)}
