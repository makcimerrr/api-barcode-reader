import csv
import barcode
from barcode.writer import ImageWriter
import os

# Chemins des fichiers
input_file = 'hardware_data.csv'
output_folder = 'barcodes/'
prises_folder = 'barcodes/prises/'

# Exemple de tableau contenant des numéros de série
serial_numbers = ['1697AP01', '1697AP02', '1697AP03', '1697AP04', '1697AP05', '1697AP06']

# Créez les dossiers de sortie s'ils n'existent pas
for folder in [output_folder, prises_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)


# Fonction pour générer des codes-barres depuis une liste de numéros de série
def generate_barcodes_from_list(sn_list):
    for sn in sn_list:
        if sn:  # Vérifier que le numéro de série n'est pas vide
            try:
                code128 = barcode.get_barcode_class('code128')
                barcode_instance = code128(sn, writer=ImageWriter())
                barcode_file = os.path.join(prises_folder, f"{sn}.png")
                barcode_instance.save(barcode_file)
                print(f"Code-barres pour SN {sn} enregistré sous {barcode_file}")
            except Exception as e:
                print(f"Erreur lors de la génération du code-barres pour SN {sn}: {e}")


# Fonction pour générer des codes-barres depuis un fichier CSV
def generate_barcodes_from_csv(file):
    with open(file, mode='r', newline='') as file:
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


# Appeler les fonctions pour générer les codes-barres
generate_barcodes_from_list(serial_numbers)
# generate_barcodes_from_csv(input_file)
