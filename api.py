from flask import Flask, jsonify, request
from flask_cors import CORS
import csv

app = Flask(__name__)
CORS(app)  # Cette ligne active CORS pour toutes les routes, vous pouvez spécifier des origines si besoin

# Chargement des données depuis le fichier CSV
def load_data(csv_file):
    data = []
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data

# Charger les données du fichier CSV au démarrage du serveur
data = load_data('hardware_data.csv')  # Assurez-vous que le chemin est correct selon votre environnement de déploiement

# Route pour obtenir les informations d'un PC via son SN
@app.route('/api/hardware/<sn>', methods=['GET'])
def get_hardware(sn):
    # Recherche des données par SN
    result = next((item for item in data if item['SN'] == sn), None)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'PC non trouvé'}), 404

# Point d'entrée de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
