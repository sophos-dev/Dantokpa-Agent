import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from tool import AVAILABLE_TOOLS

load_dotenv()

app = FastAPI(title="Boutique Intelligente - Dantokpa Vendeur", version="1.0")

# Initialisation du client OpenAI / RodiumAI
client = OpenAI(
    api_key=os.getenv("RODIUM_API_KEY"),
    base_url=os.getenv("RODIUM_BASE_URL", "https://api.rodium.ai/v1") # Ajuste si besoin selon ton URL Rodium
)

# Chargement du System Prompt
def load_system_prompt() -> str:
    path = "prompts/system.md"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Tu es le vendeur virtuel d'Afi au marché Dantokpa."

# Schémas des outils pour le LLM (Tool Calling)
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "chercher_produits",
            "description": "Trouve des pagnes et accessoires par mot-clé dans le catalogue du marché Dantokpa[cite: 3, 4].",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Mot-clé du produit recherché"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verifier_stock",
            "description": "Donne le stock exact d'une référence produit (ex: P01)[cite: 3, 4].",
            "parameters": {
                "type": "object",
                "properties": {
                    "reference": {"type": "string", "description": "Référence exacte du produit (ex: P01)"}
                },
                "required": ["reference"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "frais_livraison",
            "description": "Donne les frais et le délai pour une zone de livraison autorisée[cite: 3, 4].",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {"type": "string", "description": "Zone de livraison (Cotonou, Calavi, etc.)"}
                },
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convertir_devise",
            "description": "Convertit un montant en FCFA vers une devise étrangère (EUR, USD, NGN)[cite: 4].",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Montant en FCFA"},
                    "target_currency": {"type": "string", "description": "Devise cible (EUR, USD, NGN)"}
                },
                "required": ["amount", "target_currency"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "creer_commande",
            "description": "Enregistre une commande (action irréversible nécessitant l'accord de la gérante)[cite: 4].",
            "parameters": {
                "type": "object",
                "properties": {
                    "reference": {"type": "string", "description": "Référence du produit"},
                    "quantity": {"type": "integer", "description": "Quantité"},
                    "delivery_zone": {"type": "string", "description": "Zone de livraison"},
                    "client_phone": {"type": "string", "description": "Téléphone du client"}
                },
                "required": ["reference", "quantity", "delivery_zone", "client_phone"]
            }
        }
    }
]

class ChatRequest(BaseModel):
    message: str
    model: str = "openai/gpt-4o-mini"

@app.post("/chat")
def chat_with_agent(request: ChatRequest):
    system_prompt = load_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message}
    ]
    
    max_steps = 8
    step = 0
    trace_logs = []

    print(f"\n--- [NOUVELLE REQUÊTE] : {request.message} ---")

    while step < max_steps:
        step += 1
        
        response = client.chat.completions.create(
            model=request.model,
            messages=messages,
            tools=tools_schema,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)
        
        # Si le modèle veut appeler des outils
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Trace lisible console
                log_entry = f"Step {step} | Appel outil: {function_name} | Args: {function_args}"
                print(f"🔧 {log_entry}")
                trace_logs.append(log_entry)
                
                if function_name in AVAILABLE_TOOLS:
                    tool_function = AVAILABLE_TOOLS[function_name]
                    try:
                        tool_output = tool_function(**function_args)
                    except Exception as e:
                        tool_output = f"Erreur lors de l'exécution de l'outil : {str(e)}"
                else:
                    tool_output = f"Erreur : Outil {function_name} inconnu."
                
                print(f" résultat: {tool_output}")
                trace_logs.append(f"Résultat: {tool_output}")
                
                # Ajout du retour de l'outil dans l'historique
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_output)
                })
        else:
            # Le modèle a fini et donne sa réponse finale
            print(f"🤖 Réponse finale : {response_message.content}\n")
            return {
                "status": "success",
                "response": response_message.content,
                "trace": trace_logs
            }
            
    raise HTTPException(status_code=500, status_log="Limite d'étapes (max_steps) atteinte sans réponse finale.")