import os
import httpx
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# FIREBASE (Usando sua chave que já funciona no Render)
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

# ✨ SINCRONIZAÇÃO PÚBLICA (Sem Token)
@app.get("/api/sincronizar")
async def sincronizar():
    if not db: return {"erro": "DB Offline"}
    
    # URL oficial da sua documentação
    url = "https://app.dwconsorcios.com.br/api/v1/contemplados"

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=30.0)
            cartas = res.json()
            
            # Limpa as cotas antigas (opcional) e salva as novas
            for carta in cartas:
                # Usa o 'id' numérico da API como identificador no Firebase
                c_id = str(carta.get("id"))
                db.collection("cotas_contempladas").document(c_id).set(carta)
            
            # Retorna o que ele recebeu para você conferir no navegador
            return {
                "status": "Sucesso", 
                "total_importado": len(cartas), 
                "exemplo_recebido": cartas[0] if cartas else "Lista vazia"
            }
        except Exception as e:
            return {"erro": str(e)}
