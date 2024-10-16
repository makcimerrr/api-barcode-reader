import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env.development.local
load_dotenv('.env.development.local')

# Initialiser Flask
app = Flask(__name__)
CORS(app)  # Activer CORS

# Initialiser Supabase avec les variables d'environnement
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(url, key)


# Route pour obtenir les informations d'un PC via son SN
@app.route('/api/hardware/<sn>', methods=['GET'])
def get_hardware(sn):
    # Recherche des données par SN
    response = supabase.table('hardware').select('*').eq('SN', sn).execute()
    if response.data:
        return jsonify(response.data[0])
    else:
        return jsonify({'error': 'PC non trouvé'}), 404


# Route pour rechercher des matériels par texte
@app.route('/api/search', methods=['GET'])
def search_hardware():
    query = request.args.get('query', '').lower()  # Récupère la requête de recherche
    if not query:
        return jsonify({'error': 'Veuillez fournir une requête de recherche.'}), 400

    # Recherche dans tous les champs
    response = supabase.table('hardware').select('*').filter('Modèle', 'ilike', f'%{query}%').execute()

    if response.data:
        return jsonify(response.data)
    else:
        return jsonify({'error': 'Aucun résultat trouvé pour la requête donnée.'}), 404


# Route pour ajouter un nouveau matériel
@app.route('/api/hardware', methods=['POST'])
def add_hardware():
    new_hardware = request.json  # Récupérer les données du corps de la requête
    response = supabase.table('hardware').insert(new_hardware).execute()

    if response.status_code == 201:  # Vérifie que l'insertion a réussi
        return jsonify(response.data[0]), 201
    else:
        return jsonify({'error': 'Erreur lors de l\'ajout du matériel.'}), 400


# Point d'entrée de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
