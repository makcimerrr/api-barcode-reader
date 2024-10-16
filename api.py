from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Charger les variables d'environnement depuis le fichier .env.development.local
load_dotenv('.env.development.local')

# Initialiser Supabase avec les variables d'environnement
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(url, key)


# Route pour obtenir les informations d'un PC via son SN
@app.route('/api/hardware/<sn>', methods=['GET'])
def get_hardware(sn):
    response = supabase.table('hardware').select('*').eq('SN', sn).execute()

    if response['data']:
        return jsonify(response['data'][0])
    else:
        return jsonify({'error': 'PC non trouvé'}), 404


# Nouvelle route pour la recherche par texte
@app.route('/api/search', methods=['GET'])
def search_hardware():
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify({'error': 'Veuillez fournir une requête de recherche.'}), 400

    response = supabase.table('hardware').select('*').execute()
    results = [item for item in response['data'] if any(query in str(value).lower() for value in item.values())]

    if results:
        return jsonify(results)
    else:
        return jsonify({'error': 'Aucun résultat trouvé pour la requête donnée.'}), 404


# Point d'entrée de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
