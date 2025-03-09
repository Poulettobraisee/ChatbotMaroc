import json
import unicodedata
import re
from collections import defaultdict
from fuzzywuzzy import fuzz, process

SYNONYMS = {
    "formations": ["filières", "cursus", "programmes", "diplômes"],
    "bourses": ["aides financières", "subventions", "financements", "aide financière"],
    "ville": ["localisation", "endroit", "région", "marrakech", "marrakesh"],
    "statut": ["type", "secteur", "public/privé"],
    "site_web": ["site internet", "lien", "page web"],
    "type_bourse": ["catégorie de bourse", "types d'aides"],
    "nom": ["université", "école", "institut"]
}

STOP_WORDS = {'de', 'des', "d'", 'et', 'la', 'le', 'les', 'à', 'aux', 'en'}

universities = []
cities = []
universities_by_city = defaultdict(list)
uni_mappings = []

def normalize_string(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8').lower()
    return re.sub(r'[^\w\s]', '', s)

def generate_acronym(name):
    words = [word for word in re.split(r'\W+', name) if word.lower() not in STOP_WORDS]
    return ''.join([word[0].upper() for word in words if word]).lower()

def load_data():
    global universities, cities, universities_by_city, uni_mappings
    try:
        with open('universities.json', 'r', encoding='utf-8') as file:
            universities = json.load(file)
            cities = list({normalize_string(uni["ville"]) for uni in universities})
            
            universities_by_city.clear()
            for uni in universities:
                city_norm = normalize_string(uni["ville"])
                universities_by_city[city_norm].append(uni)
            
            uni_mappings.clear()
            for uni in universities:
                cleaned_name = re.sub(r'\(.*?\)', '', uni["nom"])
                uni_mappings.append({
                    "original": uni["nom"],
                    "normalized": normalize_string(uni["nom"]),
                    "acronym": generate_acronym(cleaned_name)
                })
    except Exception as e:
        print(f"Erreur de chargement : {e}")
        universities = []

def find_best_match(query, choices, threshold=65):
    try:
        result, score = process.extractOne(query, choices, scorer=fuzz.token_set_ratio)
        return result if score >= threshold else None
    except:
        return None

def detect_entities(question):
    question_norm = normalize_string(question)
    entities = {"ville": None, "université": None, "statut": None, "intention": None}

    # Détection université prioritaire
    for mapping in uni_mappings:
        if (mapping["normalized"] in question_norm or 
            mapping["acronym"] in question_norm):
            entities["université"] = mapping["original"]
            break

    # Détection ville si aucune université trouvée
    if not entities["université"]:
        entities["ville"] = find_best_match(question_norm, cities)

    # Détection des intentions
    if "bourse" in question_norm or any(s in question_norm for s in SYNONYMS["bourses"]):
        entities["intention"] = "bourses"
    elif "formation" in question_norm or any(s in question_norm for s in SYNONYMS["formations"]):
        entities["intention"] = "formations"
    elif "site" in question_norm or any(s in question_norm for s in SYNONYMS["site_web"]):
        entities["intention"] = "site_web"

    return entities

def generate_response(entities, question_norm):
    # Réponse pour une université spécifique
    if entities["université"]:
        uni = next((u for u in universities if u["nom"] == entities["université"]), None)
        if not uni:
            return "Aucune information trouvée pour cette université"
            
        response = []
        if entities.get("intention") == "bourses":
            response.extend([
                f"💰 Bourses disponibles : {uni['bourses']}",
                f"📋 Types de bourses : {uni['type_bourse']}"
            ])
        elif entities.get("intention") == "formations":
            response.append(f"🎓 Formations proposées : {', '.join(uni['formations'])}")
        elif entities.get("intention") == "site_web":
            response.append(f"🌐 Site officiel : {uni['site_web']}")
        else:
            response.extend([
                f"🏛️ {uni['nom']} ({uni['statut']})",
                f"📍 Ville : {uni['ville']}",
                f"🔗 Site web : {uni['site_web']}"
            ])
        return "\n".join(response)

    # Réponse par ville
    if entities["ville"]:
        unis = universities_by_city.get(entities["ville"], [])
        if entities["statut"]:
            unis = [u for u in unis if u["statut"] == entities["statut"]]
        
        if unis:
            return (f"📌 Universités à {entities['ville'].capitalize()} ({len(unis)} résultats) :\n" + 
                    "\n".join(f"- {u['nom']} ({u['statut']}) : {u['site_web']}" for u in unis))
        else:
            return f"Aucune université trouvée à {entities['ville'].capitalize()}"

    # Fallback général
    return ("Je peux vous aider avec :\n"
            "- Recherche d'universités par ville\n"
            "- Informations sur les bourses\n"
            "- Sites web des établissements\n"
            "Exemple : 'Bourses à l'EHTP' ou 'Formations à Marrakech'")

def get_response(question, context={}):
    load_data()
    question_norm = normalize_string(question)
    entities = detect_entities(question)
    return generate_response(entities, question_norm), {}