import requests
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv('.env.development.local')

# Récupérer les clés d'API et autres paramètres
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
notion_api_key = os.getenv("NOTION_API_TOKEN")
notion_database_id = os.getenv("NOTION_DATABASE_ID")

# Créer le client Supabase
supabase: Client = create_client(supabase_url, supabase_key)


# Fonction pour récupérer les utilisateurs de Notion avec pagination
def get_users_from_notion():
    url = f'https://api.notion.com/v1/databases/{notion_database_id}/query'
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    users = []
    has_more = True
    start_cursor = None

    while has_more:
        payload = {}
        if start_cursor:
            payload['start_cursor'] = start_cursor

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(
                f"Erreur lors de la récupération des utilisateurs Notion : {response.status_code} - {response.text}")

        data = response.json()
        for result in data.get("results", []):
            properties = result["properties"]
            first_name = ''
            last_name = ''
            login_title = ''
            login_link = ''

            # Vérifier si le champ "Prénom" existe et contient un texte
            if 'Prénom' in properties and properties['Prénom']['rich_text']:
                first_name = properties['Prénom']['rich_text'][0]['text']['content']

            # Vérifier si le champ "Nom" existe et contient un texte
            if 'Nom' in properties and properties['Nom']['rich_text']:
                last_name = properties['Nom']['rich_text'][0]['text']['content']

            # Vérifier si le champ "Login" existe et contient un titre (le titre de la page)
            if 'Login' in properties and properties['Login']['title']:
                login_title = properties['Login']['title'][0]['text']['content']
                page_id = result['id']
                login_link = f"https://www.notion.so/{page_id.replace('-', '')}"

            # Ajouter l'utilisateur s'il y a des informations valides
            if first_name or last_name or login_title:
                users.append({
                    'first_name': first_name,
                    'last_name': last_name,
                    'login_title': login_title,  # Le titre de la page Login
                    'login_link': login_link  # Le lien vers la page Login
                })

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor", None)

    return users


# Fonction pour mettre à jour ou insérer les utilisateurs dans Supabase
def upsert_users_to_supabase(users):
    for user in users:
        # Vérifier si l'utilisateur avec le même login_title existe
        response = supabase.table('users').select('first_name, last_name, login_link').eq('login_title',
                                                                                          user['login_title']).execute()

        if response.data:
            existing_user = response.data[0]
            # Comparer les données existantes avec les nouvelles données
            if (existing_user['first_name'] != user['first_name'] or
                existing_user['last_name'] != user['last_name'] or
                existing_user['login_link'] != user['login_link']):
                # Si les données sont différentes, mettre à jour les informations
                print(f"Mise à jour de l'utilisateur {user['login_title']}")
                supabase.table('users').update({
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'login_link': user['login_link']
                }).eq('login_title', user['login_title']).execute()
            else:
                print(f"Pas de changement pour l'utilisateur {user['login_title']}, pas de mise à jour effectuée")
        else:
            # Si l'utilisateur n'existe pas, l'insérer
            print(f"Insertion du nouvel utilisateur {user['login_title']}")
            supabase.table('users').insert({
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'login_title': user['login_title'],
                'login_link': user['login_link']
            }).execute()


# Exécuter le script
if __name__ == '__main__':
    try:
        # Appel à la fonction pour récupérer les utilisateurs depuis Notion
        notion_users = get_users_from_notion()

        # Mise à jour ou insertion des utilisateurs dans Supabase
        upsert_users_to_supabase(notion_users)
        print("Mise à jour de Supabase terminée avec succès.")
    except Exception as e:
        print(f"Erreur : {e}")
