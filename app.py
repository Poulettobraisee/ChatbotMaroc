from flask import Flask, render_template, request, jsonify, session
from chatbot import get_response, load_data
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['JSON_AS_ASCII'] = False  # Pour le support Unicode

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        question = request.form.get('question')
        context = session.get('last_context', {})
        response, new_context = get_response(question, context)
        session['last_context'] = new_context
        return jsonify({'response': response})
    
    except Exception as e:
        app.logger.error(f"Erreur /ask: {str(e)}")
        return jsonify({'response': "Une erreur est survenue"}), 500

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    try:
        if request.method == 'POST':
            # Validation du content-type
            if not request.is_json:
                return jsonify({"error": "Le content-type doit être application/json"}), 400

            data = request.get_json()
            
            # Validation du format
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                return jsonify({
                    "error": "Format invalide - Le corps doit être un tableau d'universités",
                    "exemple": "[{'nom': '...', 'ville': '...'}]"
                }), 400
                
            # Sauvegarde atomique
            temp_path = 'universities.temp.json'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            os.replace(temp_path, 'universities.json')
            load_data()  # Rechargement des données
            
            return jsonify({
                "status": "success",
                "count": len(data),
                "message": f"Mise à jour réussie ({len(data)} universités)"
            })

        else:  # GET
            # Création du fichier si absent
            if not os.path.exists('universities.json'):
                with open('universities.json', 'w', encoding='utf-8') as f:
                    f.write("[]")
            
            # Lecture sécurisée
            with open('universities.json', 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

            # Statistiques
            stats = {
                'public': sum(1 for u in data if u.get('statut') == 'Publique'),
                'private': sum(1 for u in data if u.get('statut') == 'Privée')
            }
            
            return render_template(
                'admin.html',
                universities=sorted(data, key=lambda x: x['nom']),
                count=len(data),
                stats=stats
            )

    except Exception as e:
        app.logger.error(f"Erreur admin: {str(e)}")
        return jsonify({"error": "Erreur serveur"}), 500

if __name__ == '__main__':
    app.run(debug=True)