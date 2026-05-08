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

# Inicialização do Firebase
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
            print("--- SISTEMA RCF: CONECTADO ---")
except Exception as e:
    print(f"--- ERRO: {str(e)} ---")

@app.get("/")
def root():
    return {"status": "Online", "servico": "RCF - Integração DW"}

@app.get("/api/cotas")
def listar_cotas():
    if not db: return {"erro": "DB Offline"}
    docs = db.collection("cotas_contempladas").get(timeout=10)
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

# ✨ SINCRONIZAÇÃO E TRADUÇÃO DE CAMPOS
@app.get("/api/sincronizar")
async def sincronizar():
    if not db: return {"erro": "DB Offline"}
    
    url = "https://app.dwconsorcios.com.br/api/v1/contemplados"

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=30.0)
            cartas_dw = res.json()
            
            total = 0
            for item in cartas_dw:
                # TRADUÇÃO: Transformamos os nomes da DW nos nomes que o seu SITE entende
                cota_convertida = {
                    "id_dw": item.get("id"),
                    "categoria": item.get("category"),
                    "valor_credito": item.get("value"),        # 'value' vira 'valor_credito'
                    "valor_entrada": item.get("input"),        # 'input' vira 'valor_entrada'
                    "valor_parcela": item.get("installment"),  # 'installment' vira 'valor_parcela'
                    "parcelas_restantes": item.get("term"),    # 'term' vira 'parcelas_restantes'
                    "taxa_transferencia": item.get("transfer"),
                    "grupo": item.get("group"),
                    "status": item.get("status"),
                    "administradora": item.get("administrator", {}).get("name", "Consórcio"),
                    "ultima_sincronizacao": firestore.SERVER_TIMESTAMP
                }
                
                # Salva no Firebase usando o ID da DW para evitar duplicados
                doc_id = str(item.get("id"))
                db.collection("cotas_contempladas").document(doc_id).set(cota_convertida)
                total += 1
            
            return {"status": "Sucesso", "total_importado": total}
        except Exception as e:
            return {"status": "erro", "detalhe": str(e)}
