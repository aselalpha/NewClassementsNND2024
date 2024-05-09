import pandas as pd
import logging


"""
On doit :
- Récupérer chaque feuille = une acti
- Dans chaque feuille sont indiqués : le nom de l'acti, les points attribués, nom/prénom d'un membre de l'équipe, médaille obtenue
- Créer un dictionnaire de clés 'acti_name' (str), 'or_argent_bronze' (dict), 'team_results' (li

A VERIFIER:
- Chaque équipe n'est présente qu'une seule fois sur chaque acti

/!\ Obligation d'avoir un fichier d'actis même si aucune acti dans la journée ?
"""



class DataActisCollector:

    def __init__(self, excel_file: str):
        logging.info(f"Lecture de {excel_file}.")

        # Dict of sheets. "A:H" englobe les huit colonnes utilisées de chaque feuille.
        self.excel_file = pd.read_excel(excel_file, sheet_name=None, usecols="A:G")

        self.actis_dict = {}
        for sheet_name, sheet_data in self.excel_file.items():
            self.actis_dict[sheet_name] = self.extract_data(sheet_data)
    
    
    def extract_data(self, sheet: pd.DataFrame) -> dict:
        
        """Extrait les données d'un sheet."""

        epreuve_acti_dict = {}

        epreuve_acti_dict['acti_name'] = str(sheet['Nom acti'].iloc[0])
        epreuve_acti_dict['participation_points'] = float(sheet['Points Participation'].iloc[0])
        epreuve_acti_dict['or_argent_bronze'] = {'or': float(sheet['Points Or'].iloc[0]), 'argent': float(sheet['Points Argent'].iloc[0]), 'bronze': float(sheet['Points Bronze'].iloc[0])}

        # Partie du sheet ne contenant que les scores des différentes équipes
        dossard_medal_df = sheet[['Dossard', 'Medaille']].dropna(how='all')
        
        epreuve_acti_dict['teams_results'] = [{'dossard': int(dossard_medal_df['Dossard'].iloc[row_idx]), 'medal': str(dossard_medal_df['Medaille'].iloc[row_idx]).strip().lower()} for row_idx in dossard_medal_df.index]

        return epreuve_acti_dict
