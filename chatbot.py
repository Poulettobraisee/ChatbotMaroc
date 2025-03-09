import json
import unicodedata

# Fonction pour normaliser les chaînes (enlever les accents, etc.)
def normalize_string(s):
    normalized_str = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8').lower()
    return normalized_str

# Charger les données des universités depuis un fichier JSON
def load_universities():
    try:
          with open('universities.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        return []

# Fonction principale pour traiter les questions
def get_response(question):
    universities = load_universities()

    if not universities:
        return "Erreur : Impossible de charger les données des universités."

    # Vérification que la question n'est pas vide
    if not question or question.strip() == "":
        return "Veuillez poser une question."

    question_normalized = normalize_string(question)  # Normaliser la question pour la comparaison

    # Recherche d'un nom d'université spécifique dans la question
    for university in universities:
        if normalize_string(university["nom"]) in question_normalized:
            # Si un nom d'université est trouvé, on renvoie directement les formations ou bourses
            if "bourses" in question_normalized:
                return f"Bourses disponibles pour {university['nom']} : {university['bourses']} ({university['type_bourse']})"
            if "formations" in question_normalized:
                return f"Formations proposées par {university['nom']} : {', '.join(university['formations'])}."

    
    cities = [
        "casablanca", "rabat", "marrakech", "fès", "kenitra", "nador", "tanger", 
        "settat", "agadir", "oujda", "tétouan", "eljadida", "essaouira", "safi", 
        "benslimane", "khemisset", "azilal", "taroudant", "khouribga", "mohammedia",
        "beni mellal", "larache", "sidi ifni", "marrakech", "meknès", "oufella", 
        "taounate", "tiznit", "ouarzzazate", "chichaoua", "ifrane"
    ]
    
    for city in cities:
        if city in question_normalized:
            universities_in_city = [uni for uni in universities if normalize_string(uni["ville"]) == city]
            if universities_in_city:
                result = "\n".join([f"- {uni['nom']} ({uni['site_web']})" for uni in universities_in_city])
                return f"Voici les universités à {city.capitalize()} :\n{result}"
            return f"Aucune université trouvée à {city.capitalize()}."

    # Recherche des bourses ou formations pour une ville spécifique
    if "bourses" in question_normalized:
        print(f"Recherche des bourses pour : {question_normalized}")  # Debugging
        for city in cities:
            if city in question_normalized:
                universities_in_city = [uni for uni in universities if normalize_string(uni["ville"]) == city]
                if universities_in_city:
                    result = "\n".join([f"Bourses disponibles pour {uni['nom']} : {uni['bourses']} ({uni['type_bourse']})" for uni in universities_in_city])
                    return f"Voici les bourses disponibles pour les universités à {city.capitalize()} :\n{result}"

    if "formations" in question_normalized:
        print(f"Recherche des formations pour : {question_normalized}")  # Debugging
        for city in cities:
            if city in question_normalized:
                universities_in_city = [uni for uni in universities if normalize_string(uni["ville"]) == city]
                if universities_in_city:
                    result = "\n".join([f"Formations proposées par {uni['nom']} : {', '.join(uni['formations'])}" for uni in universities_in_city])
                    return f"Voici les formations proposées dans les universités à {city.capitalize()} :\n{result}"

    return "Je ne comprends pas votre question. Posez des questions sur les universités, les bourses ou les formations."
