import csv
import barcode
from barcode.writer import ImageWriter
import os

# Chemins des fichiers
input_file = 'hardware_data.csv'
output_folder = 'barcodes/'

# Créez le dossier de sortie s'il n'existe pas
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Lire le fichier CSV et générer des codes-barres
with open(input_file, mode='r', newline='') as file:
    reader = csv.DictReader(file)
    for row in reader:
        sn = row['SN']  # Lire le numéro de série depuis la colonne SN
        if sn:  # Vérifier que le numéro de série n'est pas vide
            try:
                code128 = barcode.get_barcode_class('code128')
                barcode_instance = code128(sn, writer=ImageWriter())
                barcode_file = os.path.join(output_folder, f"{sn}.png")
                barcode_instance.save(barcode_file)
                print(f"Code-barres pour SN {sn} enregistré sous {barcode_file}")
            except Exception as e:
                print(f"Erreur lors de la génération du code-barres pour SN {sn}: {e}")
