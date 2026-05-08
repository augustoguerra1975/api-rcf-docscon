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

# Inicialização do Firebase (Sua chave já está configurada no Render)
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

@app.get("/")
def root():
    return {"status": "Online", "msg": "API RCF - Tradutor DW v1.1"}

@app.get("/api/cotas")
def listar_cotas():
    if not db: return {"erro": "DB Offline"}
    try:
        docs = db.collection("cotas_contempladas").get(timeout=10)
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]
    except Exception as e:
        return {"erro": str(e)}

# ✨ SINCRONIZAÇÃO COM TRADUTOR DE CAMPOS
@app.get("/api/sincronizar")
async def sincronizar():
    if not db: return {"erro": "DB Offline"}
    
    url = "https://app.dwconsorcios.com.br/api/v1/contemplados"

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=30.0)
            cartas_dw = res.json()
            
            if not isinstance(cartas_dw, list):
                return {"status": "erro", "msg": "API não enviou uma lista", "resposta": str(cartas_dw)[:100]}

            total = 0
            for item in cartas_dw:
                # MAPEAMENTO: Transformamos o padrão DW no padrão que seu SITE espera
                cota_traduzida = {
                    "id_origem": item.get("id"),
                    "administradora": item.get("administrator", {}).get("name", "N/A"),
                    "valor_credito": item.get("value"),
                    "valor_entrada": item.get("input"),
                    "valor_parcela": item.get("installment"),
                    "parcelas_restantes": item.get("term"),
                    "status": item.get("status"),
                    "categoria": item.get("category"),
                    "grupo": item.get("group")
                }
                
                # Salvamos no Firebase com o ID da DW para não duplicar
                doc_id = f"dw_{item.get('id')}"
                db.collection("cotas_contempladas").document(doc_id).set(cota_traduzida)
                total += 1
            
            return {
                "status": "Sucesso",
                "total_importado": total,
                "detalhe": f"Foram encontradas {total} cartas na API pública."
            }
        except Exception as e:
            return {"status": "erro", "msg": str(e)}
