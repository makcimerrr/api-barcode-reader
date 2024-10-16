import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# 1. Initialiser Firebase Admin SDK avec les informations d'identification
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# 2. Connexion à Firestore (base de données Firebase)
db = firestore.client()

# 3. Charger les données CSV avec pandas
csv_file = 'hardware_data.csv'
data = pd.read_csv(csv_file)

# 4. Itérer à travers chaque ligne du fichier CSV et ajouter à la base de données
collection_name = 'hardware'  # Nom de la collection dans Firestore

for index, row in data.iterrows():
    doc_id = row['SN']  # Utiliser le numéro de série (SN) comme ID du document
    doc_data = row.to_dict()  # Convertir la ligne en dictionnaire
    db.collection(collection_name).document(doc_id).set(doc_data)

print(f"Les données ont été importées dans Firebase Firestore.")
