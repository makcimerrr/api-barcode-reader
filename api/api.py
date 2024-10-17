from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
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


@app.route('/api/historique_modifications/<int:id>', methods=['PUT'])
def update_historique_modifications(id):
    try:
        data = request.json
        new_owner = data['new_owner']
        commentaire = data.get('commentaire', '')
        modifie_par = data.get('modifie_par', 'inconnu')

        # Récupérer l'enregistrement actuel dans la table hardware
        hardware_response = supabase.table('hardware').select('owner').eq('id', id).execute()
        if not hardware_response.data:
            return jsonify({'error': 'Enregistrement hardware non trouvé'}), 404

        current_owner = hardware_response.data[0]['owner']

        # Mettre à jour le propriétaire dans la table hardware
        supabase.table('hardware').update({'owner': new_owner}).eq('id', id).execute()

        # Insérer l'ancien propriétaire dans la table historique_modifications
        histor_data = {
            'hardware_id': id,
            'date_modification': 'now()',
            'ancien_proprietaire': current_owner,
            'commentaire': commentaire,
            'modifie_par': modifie_par
        }
        supabase.table('historique_modifications').insert(histor_data).execute()

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"Error updating historique_modifications with ID {id}: {e}")  # Log the error for debugging
        return jsonify({'error': 'Erreur lors de la mise à jour des données.'}), 500


# Point d'entrée de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
