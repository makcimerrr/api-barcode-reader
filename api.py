from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app)

# Initialiser Firebase Admin SDK avec les informations d'identification
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Connexion à la base de données Firestore
db = firestore.client()


# Route pour obtenir les informations d'un PC via son SN
@app.route('/api/hardware/<sn>', methods=['GET'])
def get_hardware(sn):
    # Requête Firestore pour obtenir le document correspondant au SN
    doc_ref = db.collection('hardware').document(sn)
    doc = doc_ref.get()

    if doc.exists:
        return jsonify(doc.to_dict())
    else:
        return jsonify({'error': 'PC non trouvé'}), 404


# Nouvelle route pour la recherche par texte
@app.route('/api/search', methods=['GET'])
def search_hardware():
    query = request.args.get('query', '').lower()  # Récupère la requête de recherche et la met en minuscules
    if not query:
        return jsonify({'error': 'Veuillez fournir une requête de recherche.'}), 400

    # Requête Firestore pour rechercher dans tous les documents
    results = []
    docs = db.collection('hardware').stream()

    for doc in docs:
        data = doc.to_dict()
        # Recherche dans tous les champs du document
        if any(query in str(value).lower() for value in data.values()):
            results.append(data)

    if results:
        return jsonify(results)
    else:
        return jsonify({'error': 'Aucun résultat trouvé pour la requête donnée.'}), 404


# Point d'entrée de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
