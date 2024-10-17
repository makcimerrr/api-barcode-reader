import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
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


# Fonction pour exécuter le script update.py
def run_update_script():
    # Exécutez votre script update.py
    process = subprocess.Popen(['python3', 'update_users.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stdout:
        print(stdout.decode())
    if stderr:
        print(stderr.decode())


# Configurer le scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_update_script, 'interval', hours=1)  # Exécutez le script toutes les heures
scheduler.start()


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


@app.route('/api/historique/<int:hardware_id>', methods=['GET'])
def get_historique(hardware_id):
    try:
        # Requête à la base de données pour récupérer l'historique des modifications
        response = supabase.table('historique_modifications').select('*').eq('hardware_id', hardware_id).execute()

        # Si des données sont trouvées, les renvoyer sous forme de JSON
        if response.data:
            return jsonify(response.data)
        else:
            return jsonify({'error': 'Aucun historique trouvé pour ce matériel'}), 404
    except Exception as e:
        print(f"Error retrieving historique with hardware_id {hardware_id}: {e}")
        return jsonify({'error': 'Erreur lors de la récupération de l\'historique.'}), 500


@app.route('/api/historique_modifications/<int:id>', methods=['PUT'])
def update_historique_modifications(id):
    try:
        data = request.json
        new_owner = data['new_owner']
        commentaire = data.get('commentaire', '')
        modifie_par = data.get('modifie_par', 'inconnu')

        # Récupérer l'enregistrement actuel dans la table hardware
        hardware_response = supabase.table('hardware').select('proprietaire').eq('id', id).execute()
        if not hardware_response.data:
            return jsonify({'error': 'Enregistrement hardware non trouvé'}), 404

        current_owner = hardware_response.data[0]['proprietaire']

        # Mettre à jour le propriétaire dans la table hardware
        supabase.table('hardware').update({'proprietaire': new_owner}).eq('id', id).execute()

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


@app.route('/api/sync_notion_users', methods=['POST'])
def sync_notion_users():
    try:
        # Récupérer les données depuis Notion
        notion_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_API_TOKEN')}",
            "Notion-Version": "2022-06-28",
        }
        response = requests.post(notion_url, headers=headers)
        notion_data = response.json()

        users = []
        for result in notion_data.get('results', []):
            first_name = result['properties']['Prénom']['rich_text'][0]['text']['content']
            last_name = result['properties']['Nom']['rich_text'][0]['text']['content']
            users.append({'first_name': first_name, 'last_name': last_name})

        # Vérifier et insérer les nouveaux utilisateurs dans Supabase
        for user in users:
            supabase_response = supabase.table('users').select('*').eq('first_name', user['first_name']).eq('last_name',
                                                                                                            user[
                                                                                                                'last_name']).execute()
            if not supabase_response.data:  # Si l'utilisateur n'existe pas
                supabase.table('users').insert(user).execute()

        return jsonify({'success': True, 'message': 'Utilisateurs synchronisés avec succès.'}), 200

    except Exception as e:
        print(f"Error syncing users from Notion: {e}")  # Log the error for debugging
        return jsonify({'error': 'Erreur lors de la synchronisation des utilisateurs.'}), 500


# Route pour rechercher des suggestions d'utilisateurs
@app.route('/api/users/suggestions', methods=['GET'])
def get_user_suggestions():
    # Récupérer le terme de recherche depuis les paramètres de la requête
    query = request.args.get('query', '')

    if not query:
        return jsonify({"error": "A search query is required"}), 400

    try:
        # Rechercher dans Supabase les utilisateurs correspondant au query dans 'first_name', 'last_name' ou 'login_title'
        response = supabase.table('users') \
            .select('first_name, last_name, login_title, login_link') \
            .ilike('first_name', f'%{query}%') \
            .or_(f"last_name.ilike('%{query}%')") \
            .or_(f"login_title.ilike('%{query}%')") \
            .execute()

        if response.error:
            raise Exception(response.error)

        # Retourner les suggestions en JSON, incluant le login_link
        return jsonify(response.data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Point d'entrée de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
