import pandas
import logging

from models.team import Team

'''
On doit récupérer les colonnes :
- No
- SIID
- No. of records
{
- Record x CN
- Record x DOW
- Record x time
} for x in No. of records

Vérifications à faire :
- Tous les éléments de toutes les colonnes Record x DOW sont les mêmes (tous les bips ont été fait le mm jour)
- No. of records est cohérent avec le nombre de records
'''


class DatasGraidCollector:

    def __init__(self, csv_file: str):
        #Importation de toutes les données
        self.df = pandas.read_csv(csv_file, sep=None, engine='python', skipinitialspace=True, encoding='latin-1')
        self.csv_file = csv_file
        logging.info(f"Collecte des données doigt de {csv_file}...")
        self.df_cleaned = self.get_useful_datas_graid_columns()


    def get_useful_datas_graid_columns(self) -> pandas.DataFrame:
        """Ne garde que les colonnes utiles de datas_graid.csv"""
        logging.info(f"Nettoyage des données de {self.csv_file}...")

        #Retirer les colonnes sans données
        df_cleaned = self.df.dropna(axis='columns', how='all')

        useful_columns = ['No', 'SIID', 'No. of records']

        record_idx = 1
        while f'Record {record_idx} CN' in df_cleaned.columns:
            useful_columns.append(f'Record {record_idx} CN')
            useful_columns.append(f'Record {record_idx} DOW')
            useful_columns.append(f'Record {record_idx} time')
            record_idx += 1
        
        logging.info(f"Les colonnes {useful_columns} de datas_graid ont été conservées.\n")
        return df_cleaned[useful_columns]
    









class TeamInDatasGraidNotFoundError(Exception):
    """Gère les exceptions liées à des numéros de dossard et/ou de SIID mal attribués."""
    
    def __init__(self, dossard, SIID, teams_list, *args, **kwargs):
        msg = f"Erreur : Le couple dossard-SIID ({dossard}, {SIID}) n'est pas référencé dans la liste d'équipes suivante : {teams_list}"
        super().__init__(msg, *args, **kwargs)


