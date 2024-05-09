import pandas as pd
import logging

from models.team import Team

'''
On garde toutes les colonnes

Vérifications à faire :
- Toutes les puces sont bien reliées à un doigt
- Les couples (Dossard, Puce) sont les mêmes que dans datas_graid.csv
- Vérifier qu'il y a le bon nombre de concurrents dans chaque équipe
'''


class TeamsGenCollector:

    def __init__(self, csv_file):
        #Importation de toutes les données
        logging.info(f"Lecture de {csv_file}.")

        self.df = pd.read_csv(csv_file, encoding='utf-8', sep=None, engine='python', skipinitialspace=True).dropna(how='all')
        self.csv_file = csv_file
        self.number_of_runners = self.get_number_of_runners()

        self.check_puce_duplicates()

    
    def create_teams(self) -> list[Team]:
        '''Crée la liste d'équipes à partir des données de du fichier d'équipes.'''
        logging.info(f"Création des équipes à partir de {self.csv_file}...")

        teams_list = []

        for _, row in self.df.iterrows():
            concs_list = []
            
            # Création d'une liste de tuples (nom, prenom) des concurrents
            for conc_idx in range(1, self.number_of_runners+1):
                nom = row[f'Nom Conc {conc_idx}']
                prenom = row[f'Prenom Conc {conc_idx}']
                concs_list.append((str(nom), str(prenom)))

            # On force le type de chaque élément pour être au clair sur le type des données
            new_team = Team(
                int(row['Puce']),
                int(row['Dossard']),
                bool(row['Entreprise']),
                str(row['Mixite']).upper(),
                str(row['Nom']),
                concs_list,
                str(row['Contact'])
            )

            logging.info(f"Création de l'équipe {new_team}")
            teams_list.append(new_team)

        logging.info(f"Toutes les équipes ont bien été implémentées.\n" + "-"*50)
        return teams_list


    ################################
    ### Appelées dans __init__() ###
    ################################
    
    def get_number_of_runners(self):
        '''Détermine le nombre de concurrents basé sur les colonnes du fichier d'équipes.'''
        conc_idx = 0
        while f'Prenom Conc {conc_idx}' in self.df.columns:
            conc_idx += 1
        return conc_idx
    

    def check_puce_duplicates(self):
        '''Vérifie qu'il n'y a pas de doublons de puces dans le fichier d'équipes.'''
        if self.df['Puce'].duplicated().any():
            raise TeamsGenPuceDuplicatesError(self.df[self.df['Puce'].duplicated(keep=False)])
        logging.debug("Chaque puce n'est bien attribuée qu'une seule fois dans teams_Gen.csv.")






class TeamsGenPuceDuplicatesError(Exception):
    """Gère les exceptions liées à une puce dupliquée dans teams_Gen.csv"""
    
    def __init__(self, lignes_en_cause, *args, **kwargs):
        msg = f"Il y a des doublons de puces dans teams_Gen.csv !\n {lignes_en_cause}"
        super().__init__(msg, *args, **kwargs)