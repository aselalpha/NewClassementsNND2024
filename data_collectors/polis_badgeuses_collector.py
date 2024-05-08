import pandas
from typing import List

from epreuves.epreuve import Epreuve

'''
On garde toutes les colonnes

Vérifications à faire :
- Toutes les épreuves lues sont bien définies
- Il y a bien une badgeuse depart et fin pour chaque épreuve (sauf la 1ère épreuve qui peut être en mass start)
'''


class PolisBadgeusesCollector:
    
    """
    Classe appelée après PolisParcoursCollector, une fois que toutes les épreuves ont été créées
    """

    def __init__(self, csv_file, show_log=True):
        """Importe toutes les données"""
        self.df = pandas.read_csv(csv_file).dropna(how='all')
        self.csv_file = csv_file
        if show_log: print(f"Collecte des données de {csv_file}")
    

    def check_epreuves_are_defined(self):
        pass

    def check_epreuves_construction(self):
        pass




class EpreuveInPolisBadgeusesNotFoundError(Exception):
    """Gère les exceptions liées à une épreuve mal écrite dans POLIS_badgeuses.csv"""
    
    def __init__(self, epreuve_name, epreuves_list, *args, **kwargs):
        msg = f"Erreur : L'épreuve {epreuve_name} n'existe pas dans les épreuves définies suivantes : {epreuves_list}"
        super().__init__(msg, *args, **kwargs)