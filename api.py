# api.py
from flask import Flask, jsonify, request
from flask_cors import CORS  # Importer CORS
import csv

app = Flask(__name__)
CORS(app)  # Activer CORS pour toutes les routes

# Chargement des données depuis le fichier CSV
def load_data(csv_file):
    data = []
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data

# Charger les données du fichier CSV au démarrage du serveur
data = load_data('hardware_data.csv')  # Assurez-vous du chemin relatif correct vers le CSV

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
