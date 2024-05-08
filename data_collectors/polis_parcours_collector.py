import pandas as pd
import logging

from models.epreuve import Epreuve, EpreuveCourse, EpreuveActi

'''
On garde toutes les colonnes

Vérifications à faire :
'''


class PolisParcoursCollector:
    
    def __init__(self, csv_file: str):
        #Importation de toutes les données
        self.df = pd.read_csv(csv_file).dropna(how='all')
        self.csv_file = csv_file
        logging.info(f"Collecte des données de {csv_file}")
        

    def create_epreuves(self) -> list[Epreuve]:
        """Crée la liste des Épreuves."""
        logging.info(f"Implémentation des épreuves de {self.csv_file}")

        epreuves_list: list[Epreuve] = []

        for _, row in self.df.iterrows():

            if not 'meilleur grimpeur' in row['nom']:
                new_epreuve: Epreuve = self._create_epreuve_object(row)
                epreuves_list.append(new_epreuve)
            else:
                self._append_mg_to_epreuve_course(row, epreuves_list)

        logging.info(f"Toutes les épreuves ont bien été implémentées.\n")
        return epreuves_list


    def _create_epreuve_object(self, row: pd.Series) -> Epreuve:
        """Retourne une sous-classe de Épreuve selon type_epreuve (défini avec la méthode __type_epreuve)."""

        if row['type'] in ['trail', 'vtt']:
            epreuve_object = EpreuveCourse(
                str(row['nom']),
                float(row['points']),
                float(row['temps_ref']),
                float(row['points_gain_min']),
                float(row['points_perte_min']),
                str(row['type'])
            )
        
        elif row['type'] == 'acti':
            epreuve_object = EpreuveActi(
                str(row['nom']),
                float(row['points']),
                {'or':float(row['or']), 'argent':float(row['argent']), 'bronze':float(row['bronze'])}
            )
        
        logging.info(f"Création de l'épreuve {epreuve_object}")
        return epreuve_object



    def _append_mg_to_epreuve_course(self, row: pd.Series, epreuves_list: list[EpreuveCourse]):
        """Modifie l'épreuve contenant un meilleur grimpeur pour l'y intégrer."""

        mg_epreuve_name = str(row['nom']).replace(" meilleur grimpeur", '')
        for epreuve in epreuves_list:
            if epreuve.name == mg_epreuve_name:
                epreuve.meilleur_grimpeur = {'reference_time': float(row['temps_ref']), 'gain_per_minute': float(row['points_gain_min']), 'loss_per_minute': float(row['points_perte_min'])}