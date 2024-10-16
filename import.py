import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime

# Charger les variables d'environnement
load_dotenv('.env.development.local')

# Remplacez par votre URL Supabase et votre clé API
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

# Créer un client Supabase
supabase: Client = create_client(url, key)

# Lire le fichier CSV
file_path = 'hardware_data.csv'  # Remplacez par le chemin de votre fichier CSV
data = pd.read_csv(file_path)

# Préparer les données pour l'insertion
data.columns = [
    "modele",
    "sn",
    "n_chargeur",
    "proprietaire",
    "statut",
    "garanti",
    "contrat",
    "commentaires",
    "date_garantie",
    "provenance",
    "date",
    "derniere_modification",
    "derniere_modification_par"
]

# Ne pas convertir 'garanti' et 'contrat' en booléen, mais les garder comme chaînes
# Vous pouvez éventuellement vouloir normaliser les chaînes si nécessaire
data['garanti'] = data['garanti'].apply(lambda x: str(x).strip() if pd.notna(x) else None)
data['contrat'] = data['contrat'].apply(lambda x: str(x).strip() if pd.notna(x) else None)

# Filtrer les lignes vides
data = data.dropna(how='all')

"""# Insérer les données dans la table de Supabase
for index, row in data.iterrows():
    data_dict = row.where(pd.notnull(row), None).to_dict()  # Remplace les nan par None

    print(data_dict)  # Afficher le contenu avant l'insertion
    response = supabase.table('hardware').insert(data_dict).execute()
    print(response)  # Affiche la réponse de Supabase

print("Importation terminée.")"""
