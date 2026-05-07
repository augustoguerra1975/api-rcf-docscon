import os
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 1. PERMISSÕES DE ACESSO (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. INICIALIZAÇÃO DO MOTOR
db = None

def inicializar_firebase():
    global db
    try:
        if not firebase_admin._apps:
            # Pega a chave que você configurou no print image_b31b5b.png
            chv = os.getenv("FIREBASE_PRIVATE_KEY", "")
            
            # Limpeza cirúrgica da chave (remove sujeira de tradução e quebras de linha)
            chv_limpa = chv.strip().replace("\\n", "\n").replace('"', '')
            
            if not chv_limpa:
                print("--- ERRO: Chave FIREBASE_PRIVATE_KEY não encontrada! ---")
                return

            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": "renan-d5f4b",
                "private_key": chv_limpa,
                "client_email": "firebase-adminsdk-fbsvc@renan-d5f4b.iam.gserviceaccount.com",
                "token_uri": "https://oauth2.googleapis.com/token",
            })
            
            # Inicializa e já cria o cliente do banco
            firebase_app = firebase_admin.initialize_app(cred)
            db = firestore.client(app=firebase_app)
            print("--- MOTOR RCF: LIGADO COM SUCESSO ---")
    except Exception as e:
        print(f"--- FALHA NA PARTIDA: {str(e)} ---")

# Tenta ligar o motor assim que o código carrega
inicializar_firebase()

# 3. ROTAS
@app.get("/")
def root():
    status = "Online" if db else "Offline (Erro no Firebase)"
    return {"status": status, "msg": "API RCF Investimentos"}

@app.get("/api/cotas")
def listar_cotas():
    if not db:
        return {"erro": "Banco de dados offline. Verifique a chave no Render."}
    
    try:
        # Busca as cartas no Firebase
        docs = db.collection("cotas_contempladas").get(timeout=10)
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]
    except Exception as e:
        return {"erro_tecnico": str(e)}

@app.post("/webhook-docscon")
async def receber_cota(request: Request):
    if not db:
        return {"status": "erro", "msg": "DB offline"}
    
    try:
        dados = await request.json()
        cota_id = str(dados.get("id", "sem_id"))
        db.collection("cotas_contempladas").document(cota_id).set(dados)
        return {"status": "sucesso"}
    except Exception as e:
        return {"status": "erro", "msg": str(e)}
