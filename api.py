import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv('.env.development.local')

app = Flask(__name__)
CORS(app)

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(url, key)


@app.route('/api/hardware/<sn>', methods=['GET'])
def get_hardware(sn):
    try:
        response = supabase.table('hardware').select('*').eq('SN', sn).execute()
        if response.data:
            return jsonify(response.data[0])
        else:
            return jsonify({'error': 'PC non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['GET'])
def search_hardware():
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify({'error': 'Veuillez fournir une requête de recherche.'}), 400

    try:
        response = supabase.table('hardware').select('*').filter('Modèle', 'ilike', f'%{query}%').execute()
        if response.data:
            return jsonify(response.data)
        else:
            return jsonify({'error': 'Aucun résultat trouvé pour la requête donnée.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/hardware', methods=['POST'])
def add_hardware():
    try:
        new_hardware = request.json
        response = supabase.table('hardware').insert(new_hardware).execute()
        if response.status_code == 201:
            return jsonify(response.data[0]), 201
        else:
            return jsonify({'error': 'Erreur lors de l\'ajout du matériel.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
