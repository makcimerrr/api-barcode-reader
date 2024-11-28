from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import datetime
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

load_dotenv('.env.development.local')

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


@app.route('/api/update_owner/<int:id>', methods=['PUT'])
def update_historique_modifications(id):
    try:
        data = request.json
        new_owner = data['new_owner']
        commentaire = data.get('commentaire', '')
        modifie_par = data.get('modifie_par', 'inconnu')

        # Nettoyer le new_owner pour obtenir uniquement le login_title
        login_title = new_owner.split(' (')[0].strip()  # Retire la partie après '(' et nettoie

        # Récupérer l'enregistrement actuel dans la table hardware
        hardware_response = supabase.table('hardware').select('proprietaire').eq('id', id).execute()
        if not hardware_response.data:
            return jsonify({'error': 'Enregistrement hardware non trouvé'}), 404

        current_owner = hardware_response.data[0]['proprietaire']

        # Récupérer le 'promo_statut' du nouveau propriétaire dans la table 'users'
        user_response = supabase.table('users').select('promo_statut').eq('login_title', login_title).execute()
        if not user_response.data:
            return jsonify({'error': 'Propriétaire non trouvé dans la table users'}), 404

        promo_statut = user_response.data[0]['promo_statut']

        type_modification = determine_type_modification('proprietaire', current_owner, new_owner)

        # Mettre à jour le propriétaire et le statut dans la table hardware
        supabase.table('hardware').update({
            'proprietaire': new_owner,
            'statut': promo_statut,
            'type_modification': type_modification,
        }).eq('id', id).execute()

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


@app.route('/api/users/suggestions', methods=['GET'])
def user_suggestions():
    try:
        query = request.args.get('query', '').lower()
        if not query:
            return jsonify({'error': 'Veuillez fournir une requête de recherche.'}), 400

        # Debug log
        # print(f"Recherche d'utilisateurs avec la requête: {query}")

        # Utilisation correcte de 'or_' pour plusieurs clauses 'ilike'
        response = supabase.table('users').select('*').or_(
            f"login_title.ilike.%{query}%,first_name.ilike.%{query}%,last_name.ilike.%{query}%"
        ).execute()
        # Debug log
        # print(f"Réponse de la base de données: {response.data}")

        if response.data:
            return jsonify(response.data)
        else:
            return jsonify({'error': 'Aucun résultat trouvé pour la requête donnée.'}), 404
    except Exception as e:
        print(f"Erreur lors de la recherche d'utilisateurs: {e}")  # Log l'erreur pour le débogage
        return jsonify({'error': 'Erreur lors de la recherche des données.'}), 500


@app.route('/api/update_column/<int:item_id>', methods=['PUT'])
def update_column(item_id):
    data = request.json
    column_type = data.get('column_type')
    new_value = data.get('new_value')
    modificateur = data.get('modifie_par')

    valid_columns = ['statut', 'contrat', 'commentaire']

    if column_type not in valid_columns:
        return jsonify({'error': 'Invalid column type provided'}), 400

    try:
        # Récupérer l'ancienne valeur de la colonne avant de la mettre à jour
        current_value_response = supabase.table('hardware').select('*').eq('id', item_id).execute()

        if not current_value_response.data:  # Utiliser .data pour accéder aux données
            print("Item not found with ID:", item_id)  # Log si l'élément n'est pas trouvé
            return jsonify({'error': 'Item not found'}), 404

        current_item = current_value_response.data[0]
        current_statut = current_item['statut'] if 'statut' in current_item else None
        current_proprietaire = current_item['proprietaire']
        current_n_chargeur = current_item['n_chargeur']
        current_garanti = current_item['garanti']
        current_contrat = current_item['contrat']
        current_commentaire = current_item['commentaires']

        # Si le statut est changé, supprimer les valeurs des colonnes associées
        if column_type == 'statut':
            # Déterminer le type de modification
            type_modification = determine_type_modification(column_type, current_statut, new_value)
            supabase.table('hardware').update({
                'statut': new_value,
                'proprietaire': None,
                'n_chargeur': None,
                'garanti': None,
                'contrat': None,
                'commentaires': None,
                'type_modification': type_modification,  # Mise à jour du type de modification
                'derniere_modification_par': modificateur  # Mise à jour du modificateur
            }).eq('id', item_id).execute()

            # Insérer l'historique de modification
            histor_data = {
                'hardware_id': item_id,
                'date_modification': 'now()',  # Utiliser une méthode pour obtenir le timestamp actuel
                'ancien_proprietaire': current_proprietaire,
                'ancien_n_chargeur': current_n_chargeur,
                'ancienne_garanti': current_garanti,
                'ancien_contrat': current_contrat,
                'commentaire': current_commentaire,
                'modifie_par': modificateur
            }
            supabase.table('historique_modifications').insert(histor_data).execute()
        elif column_type == 'contrat':
            # Déterminer le type de modification
            type_modification = determine_type_modification(column_type, current_contrat, new_value)
            supabase.table('hardware').update({
                column_type: new_value,
                'type_modification': type_modification,
                'derniere_modification_par': modificateur
            }).eq('id', item_id).execute()

            # Insérer l'historique de modification pour le contrat
            histor_data = {
                'hardware_id': item_id,
                'date_modification': 'now()',  # Utiliser une méthode pour obtenir le timestamp actuel
                'ancien_proprietaire': current_proprietaire,
                'ancien_n_chargeur': current_n_chargeur,
                'ancienne_garanti': current_garanti,
                'ancien_contrat': current_contrat,
                'commentaire': current_commentaire,
                'modifie_par': modificateur
            }
            supabase.table('historique_modifications').insert(histor_data).execute()
        else:
            # Pour les autres colonnes, on peut juste mettre à jour
            supabase.table('hardware').update({
                column_type: new_value,
                'derniere_modification_par': modificateur
            }).eq('id', item_id).execute()

        return jsonify({'message': f'{column_type} updated successfully'}), 200

    except Exception as e:
        print("Exception occurred:", str(e))  # Affichez l'erreur
        return jsonify({'error': str(e)}), 500


def determine_type_modification(column_type, old_value, new_value):
    if old_value == new_value:
        return 'Pas de changement'

    if column_type == 'proprietaire':
        return f'Changement Owner'

    elif column_type == 'contrat':
        # Logique pour le contrat
        if old_value == 'Oui' and new_value == 'Non':
            return 'Contrat : Passage Oui -> Non'
        elif old_value == 'Non' and new_value == 'Oui':
            return 'Contrat : Passage Non -> Oui'
        # Autres règles spécifiques pour 'contrat'

    elif column_type == 'statut':
        # Logique pour le statut
        if 'Promo' in old_value and 'Promo' in new_value:
            # Par exemple, gérer le format "Promo 2024 P1" à "Promo P1 - 2024"
            old_parts = old_value.split(' ')
            new_parts = new_value.split(' ')
            # Custom logic to match and compare the different parts if necessary
            return f'Statut : Passage {old_value} --> {new_value}'
        # Autres règles spécifiques pour 'statut'

    return f'Changement de {old_value} à {new_value}'


# Point d'entrée de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
