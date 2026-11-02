import os
import requests

# Catalogue officiel du marché Dantokpa
STOCK_DB = {
    "P01": {"name": "Pagne wax 6 yards", "price_xof": 12000, "stock": 14},
    "P02": {"name": "Chemise bazin homme", "price_xof": 18500, "stock": 3},
    "P03": {"name": "Sac en raphia", "price_xof": 7500, "stock": 0},
    "P04": {"name": "Sandales en cuir", "price_xof": 9000, "stock": 8},
    "P05": {"name": "Robe en wax", "price_xof": 22000, "stock": 5},
    "P06": {"name": "Beurre de karité 500 g", "price_xof": 3500, "stock": 40}
}

# Zones de livraison officielles
ZONES_LIVRAISON = {
    "cotonou": {"fee": 1000, "delay": "24 à 48 h"},
    "akpakpa": {"fee": 1000, "delay": "24 à 48 h"},
    "fidjrossè": {"fee": 1500, "delay": "24 à 48 h"},
    "calavi": {"fee": 2000, "delay": "24 à 48 h"},
    "porto-novo": {"fee": 3000, "delay": "24 à 48 h"},
    "ouidah": {"fee": 3500, "delay": "24 à 48 h"}
}

def chercher_produits(query: str) -> str:
    """Trouve des pagnes et accessoires par mot-clé dans le catalogue."""
    results = []
    query_clean = query.lower().strip()
    for ref, p in STOCK_DB.items():
        if query_clean in p["name"].lower() or query_clean in ref.lower():
            results.append(f"Réf: {ref} | Produit: {p['name']} | Prix: {p['price_xof']} FCFA | Stock: {p['stock']}")
    if not results:
        return f"<<< aucun produit pour {query} >>>"
    return "\n".join(results)

def verifier_stock(reference: str) -> str:
    """Donne le stock exact d'une référence produit (ex: P01)."""
    ref_clean = reference.upper().strip()
    product = STOCK_DB.get(ref_clean)
    if not product:
        return "<<< référence inconnue >>>"
    return f"Produit: {product['name']} (Réf: {ref_clean}) | Stock disponible: {product['stock']} unités | Prix: {product['price_xof']} FCFA"

def frais_livraison(zone: str) -> str:
    """Donne les frais et le délai de livraison pour une zone autorisée."""
    zone_clean = zone.lower().strip()
    info = ZONES_LIVRAISON.get(zone_clean)
    if not info:
        zones_possibles = ", ".join(ZONES_LIVRAISON.keys())
        return f"<<< zone non desservie >>>. Zones desservies : {zones_possibles}"
    return f"Zone: {zone.capitalize()} | Frais: {info['fee']} FCFA | Délai: {info['delay']}"

def convertir_devise(amount: float, target_currency: str) -> str:
    """Convertit un montant en FCFA vers une devise étrangère (EUR, USD, NGN)."""
    curr_clean = target_currency.upper().strip()
    try:
        eur_amount = amount / 655.957
        if curr_clean == "EUR":
            return f"{amount} FCFA équivaut à {eur_amount:.2f} EUR."
        url = f"https://api.frankfurter.app/latest?amount={eur_amount}&from=EUR&to={curr_clean}"
        res = requests.get(url, timeout=5).json()
        rate = res.get("rates", {}).get(curr_clean)
        if rate:
            return f"{amount} FCFA équivaut à {rate} {curr_clean}."
        return "<<< devise non prise en charge >>>"
    except Exception as e:
        return f"<<< devise non prise en charge >>>"

def creer_commande(reference: str, quantity: int, delivery_zone: str, client_phone: str) -> str:
    """Enregistre une commande (action irréversible)."""
    ref_clean = reference.upper().strip()
    product = STOCK_DB.get(ref_clean)
    if not product:
        return "<<< référence inconnue >>>"
    if product["stock"] < quantity:
        return f"<<< stock insuffisant pour {ref_clean} >>> ({product['stock']} disponibles)"
    zone_clean = delivery_zone.lower().strip()
    if zone_clean not in ZONES_LIVRAISON:
        return "<<< zone non desservie >>>"
    
    total_articles = product["price_xof"] * quantity
    frais = ZONES_LIVRAISON[zone_clean]["fee"]
    total_general = total_articles + frais
    return f"COMMANDE PRÉ-ENREGISTRÉE | Ref: {ref_clean} ({product['name']}) x{quantity} | Total: {total_general} FCFA | Client: {client_phone}"

AVAILABLE_TOOLS = {
    "chercher_produits": chercher_produits,
    "verifier_stock": verifier_stock,
    "frais_livraison": frais_livraison,
    "convertir_devise": convertir_devise,
    "creer_commande": creer_commande,
}