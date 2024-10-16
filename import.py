import os
import csv
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env.development.local
load_dotenv('.env.development.local')

# Initialiser Supabase avec les variables d'environnement
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(url, key)


# Fonction pour importer les données du CSV dans Supabase
def import_csv_to_supabase(csv_file):
    with open(csv_file, mode='r', newline='', encoding='utf-8-sig') as file:  # Utilisez utf-8-sig
        reader = csv.DictReader(file)
        for row in reader:
            # Afficher la ligne lue pour le débogage
            print(row)
            try:
                response = supabase.table('hardware').insert(row).execute()
                print(f"Inserted row: {row} with response: {response}")
            except Exception as e:
                print(f"Error inserting row: {row} - {str(e)}")
    print("Importation terminée.")


# Spécifiez le nom de votre fichier CSV
csv_file = 'hardware_data.csv'  # Remplacez par le chemin de votre fichier CSV
import_csv_to_supabase(csv_file)
