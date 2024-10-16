from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import pandas as pd
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)  # Active CORS pour toutes les routes

# Charger les variables d'environnement
load_dotenv('.env.development.local')  # Assurez-vous que ce fichier contient SUPABASE_URL et SUPABASE_ANON_KEY

# Créer le client Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)


@app.route('/api/hardware/<sn>', methods=['GET'])
def get_hardware(sn):
    try:
        response = supabase.table('hardware').select('*').eq('sn', sn).execute()
        if response.data:
            return jsonify(response.data[0])  # Return the first result
        else:
            return jsonify({'error': 'PC non trouvé'}), 404
    except Exception as e:
        print(f"Error retrieving hardware with SN {sn}: {e}")  # Log the error for debugging
        return jsonify({'error': 'Erreur lors de la récupération des données.'}), 500


@app.route('/api/search', methods=['GET'])
def search_hardware():
    try:
        query = request.args.get('query', '').lower()
        if not query:
            return jsonify({'error': 'Veuillez fournir une requête de recherche.'}), 400

        response = supabase.table('hardware').select('*').execute()
        results = [
            item for item in response.data
            if any(query in str(value).lower() for value in item.values())
        ]

        if results:
            return jsonify(results)
        else:
            return jsonify({'error': 'Aucun résultat trouvé pour la requête donnée.'}), 404
    except Exception as e:
        print(f"Error searching hardware: {e}")  # Log the error for debugging
        return jsonify({'error': 'Erreur lors de la recherche des données.'}), 500


# Route pour enregistrer une modification
@app.route('/api/hardware/<int:hardware_id>/modify', methods=['POST'])
def record_modification(hardware_id):
    # Récupérer les données JSON de la requête
    data = request.json

    # Vérifier que les données nécessaires sont présentes
    if not all(key in data for key in ('ancien_proprietaire', 'commentaire', 'modifie_par')):
        return jsonify(
            {'error': 'Champs manquants. Veuillez fournir ancien_proprietaire, commentaire, et modifie_par.'}), 400

    # Préparer les données pour l'insertion
    historique_data = {
        'hardware_id': hardware_id,
        'date_modification': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ancien_proprietaire': data['ancien_proprietaire'],
        'commentaire': data['commentaire'],
        'modifie_par': data['modifie_par']
    }

    # Insérer dans la table historique_modifications
    response = supabase.table('historique_modifications').insert(historique_data).execute()

    # Vérifier si l'insertion a réussi
    if response.status_code == 201:
        return jsonify({'message': 'Modification enregistrée avec succès!', 'data': response.data}), 201
    else:
        return jsonify({'error': 'Erreur lors de l\'enregistrement de la modification.', 'details': response.data}), 500


# Point d'entrée de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
