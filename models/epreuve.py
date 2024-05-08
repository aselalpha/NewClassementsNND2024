from typing import List
import numpy as np

from .poincon import Poincon

'''
Découpement des Epreuves :
- Epreuve(nom):
    - Course(nom, temps_ref, obli) #quand il y a un temps de ref ET que ça nécessite des badgeuses:
        - Obli(nom, temps_ref, points_gain_min)
        - BO(nom, points, temps_ref, points_gain_min)
    - Acti(nom, points)
'''

'''
- Voir comment traiter le type Obli ou BO
- Penser au Meilleur grimpeur
'''


class Epreuve:
    def __init__(self, _name, _participation_points, _reference_time, _gain_per_minute, _loss_per_minute, _type, _or_argent_bronze):
        self.name = _name
        self.participation_points = _participation_points
        self.reference_time = _reference_time
        self.gain_per_minute = _gain_per_minute
        self.loss_per_minute = _loss_per_minute
        self.type = _type
        self.or_argent_bronze = _or_argent_bronze
        self.badgeuses_list: List[Poincon] = []    # Est rempli par la methode add_badgeuses_to_epreuves de PolisBadgeusesCollector
        self.badgeuses_sequence = []    # Est rempli par la methode create_badgeuses_sequences de PolisBadgeusesCollector
        self.mean_times_between_poincons = {}


    def __eq__(self, other):
        """Permet de comparer les attributs de deux objets"""
        if type(self) == type(other):
            return vars(self) == vars(other)
        return False

    def __repr__(self):
        # return f'{type(self).__name__}({self.name}, p_points: {self.participation_points}, ref_time: {self.reference_time}, gain/min: {self.gain_per_minute}, {self.type}, {self.or_argent_bronze})'
        return f'{type(self).__name__}({self.name})'

class EpreuveCourse(Epreuve):
    """
    Représente une épreuve de course.

    Attributes:
        name (str): Le nom de la course.
        participation_points (float): Les points de participation.
        reference_time (float): The reference time for the course.
        gain_per_minute (float): The points gained per minute in the course.
        loss_per_minute (float): The points lost per minute in the course.
        type (str): The type of the course.

        ### Defined in __init__():
        meilleur_grimpeur (dict): De la forme {'reference_time': float, 'gain_per_minute': float} si l'épreuve contient une portion MG. None sinon.
        is_obli (bool): True si l'épreuve est une 'Obli', False sinon.
        is_co (bool): True si l'épreuve est une 'CO', False sinon.
    """

    def __init__(self, name, participation_points, reference_time, gain_per_minute, loss_per_minute, type):
        super().__init__(_name=name, _participation_points=participation_points, _reference_time=reference_time, _gain_per_minute=gain_per_minute, _loss_per_minute=loss_per_minute, _type=type, _or_argent_bronze={"or":0, "argent":0, "bronze":0})
        self.meilleur_grimpeur = None
        self.is_obli = 'Obli' in name
        self.is_co = 'CO' in name

        self.times_between_poincons = []

    def __eq__(self, other):
        return super().__eq__(other)
    
    def __repr__(self):
        return super().__repr__()
    
    def create_signaleur_function_dict(self):
        """Crée un dictionnaire de paires """
        pass

    def clean_meilleur_grimpeur(self):
        """
        Une fois que la dernière badgeuse de l'épreuve a été ajoutée, ie quand le role de la badgeuse ajoutée est 'fin',
        on met à jour les poinçons de la liste qui correpondent aussi à un meilleur grimpeur et on supprime les doublons (càd qui ont le même signaleur)
        """

        # Poinçons à supprimer une fois le parcours de la liste des poinçons fini
        idx_to_pop = []

        for idx, poincon in enumerate(self.badgeuses_list):

            if poincon.role == 'mg_debut':  # C'est qu'il y a forcément un poinçon 'degel' ou 'depart' juste avant déjà dans la liste. On vérifie si c'était un autre signaleur ou si c'est le même.
                poincon_precedent = self.badgeuses_list[idx-1]
                assert poincon_precedent.role in ['depart', 'degel']
                if poincon_precedent.signaleur == poincon.signaleur:    # C'est le même poinçon
                    poincon_precedent.is_debut_mg = True
                    idx_to_pop.append(idx)
                else:
                    poincon.is_debut_mg = True
            
            elif poincon.role == 'mg_fin':  # C'est qu'il y aura forcément un poinçon 'gel' ou 'fin' juste après dans la liste. On vérifie si c'est un autre signaleur ou si c'est le même.
                poincon_suivant = self.badgeuses_list[idx+1]
                assert poincon_suivant.role in ['gel', 'fin']
                if poincon_suivant.signaleur == poincon.signaleur:  # C'est le même poinçon
                    poincon_suivant.is_fin_mg = True
                    idx_to_pop.append(idx)
                else:
                    poincon.is_fin_mg = True
        
        for i in reversed(idx_to_pop):  # reversed pour ne pas être affecté par les changements d'index dans la liste en supprimant un élément
            self.badgeuses_list.pop(i)
        

    def average_elementary_times(self):
        
        self.mean_times_between_poincons = {elementary_time[1].signaleur+'-'+elementary_time[2].signaleur: [] for elementary_time in self.times_between_poincons}

        for elementary_time in self.times_between_poincons:
            time, poincon_1, poincon_2 = elementary_time
            key = poincon_1.signaleur+'-'+poincon_2.signaleur
            self.mean_times_between_poincons[key].append(time)
        
        for key, value in self.mean_times_between_poincons.items():
            self.mean_times_between_poincons[key] = np.average(value)





    def check_potential_typo_errors(self):

        # Une course n'a pas de temps de ref

        # Une course n'a pas de points de gain par minute

        # Une Obli a des points de participation non nuls
        if self.is_obli and self.participation_points !=0:
            print(f"{self.name} a des points de participation non nuls !")
        
        # Une Obli a des points de gain par minute négatifs ou nuls
            
        # Une BO a des points de participation négatifs ou nuls


class EpreuveActi(Epreuve):
    
    def __init__(self, name, participation_points, or_argent_bronze):
        super().__init__(_name=name, _participation_points=participation_points, _reference_time=0, _gain_per_minute=0, _loss_per_minute=0, _type='ACTI', _or_argent_bronze=or_argent_bronze)


    def __eq__(self, other):
        return super().__eq__(other)
    
    def __repr__(self):
        return super().__repr__()