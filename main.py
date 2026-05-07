import os
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI

app = FastAPI()

# PEGA A CHAVE E LIMPA TUDO
raw_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
clean_key = raw_key.strip().replace("\\n", "\n").replace('"', '')

@app.get("/api/cotas")
def testar_conexao():
    # LOG DE SEGURANÇA (Verifique isso no painel do Render!)
    print(f"--- DEBUG CHAVE ---")
    print(f"Tamanho da chave: {len(clean_key)} caracteres")
    print(f"Começa com: {clean_key[:25]}")
    print(f"Termina com: {clean_key[-25:]}")
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": "renan-d5f4b",
                "private_key": clean_key,
                "client_email": "firebase-adminsdk-fbsvc@renan-d5f4b.iam.gserviceaccount.com",
                "token_uri": "https://oauth2.googleapis.com/token",
            })
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        # TESTE RÁPIDO: Tenta ler apenas 1 documento com timeout de 10 segundos
        doc = db.collection("cotas_contempladas").limit(1).get(timeout=10)
        return {"status": "Conectado!", "cartas_encontradas": len(doc)}
    
    except Exception as e:
        print(f"ERRO REAL NO FIREBASE: {str(e)}")
        return {"erro_real": str(e)}
