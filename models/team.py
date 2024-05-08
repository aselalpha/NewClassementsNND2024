from copy import deepcopy
from typing import List, Tuple
import pandas
from datetime import datetime

from models.epreuve import EpreuveCourse
from models.poincon import Poincon

class Team:

    def __init__(self, puce: int, dossard: int, ent: bool, mixite: str, team_name: str, concs_list: List[Tuple], contact: str):
        self.puce = puce
        self.dossard = dossard
        self.team_name = team_name
        self.concs_list = concs_list
        self.ent = ent
        self.mixite = mixite
        self.contact = contact
        self.transit_times = pandas.Series()
        self.runned_epreuve_courses_list: List[dict] = []   # De la forme [{'epreuve_course': Epreuve1, 'times': [{'badgeuse_num': 52, 'signaleur': 'S1', ... , 'bip_time': 11:52:34}], 'points': 0.0, 'elementary_times': [], 'total_time': 0.0, 'points_dict': {}, 'total_points': 150}, ...]
                                                            # A CHANGER, pour rendre plus lisible qu'une liste de dict de dict
        self.epreuve_actis_list: List = []    # De la forme [{'epreuve_acti': Epreuve1, 'medal': 'or', 'points': 5}]
        
        self.missing_bips: List = []

        self.courses_total_time: float = 0.0
        self.courses_points: float = 0.0
        self.mg_time: float = 0.0
        self.mg_points: float = 0.0
        self.actis_points: float = 0.0
        self.total_points: float = 0.0

        self.CN_columns = []
        self.times_columns = []

    def __repr__(self):
        return f'Team(Puce: {self.puce}, Num: {self.dossard}, {self.team_name})'
    
    def __eq__(self, other):
        """Compare deux objets Team, qui sont considérées comme identiques si elles ont même nom, même numéro de puce, même numéro de dossard et même liste de concs."""

        if isinstance(self, other.__class__):
            return self.puce == other.puce and self.dossard == other.dossard and self.team_name == other.team_name and self.concs_list == other.concs_list
        return False


    def get_CN_columns(self) -> (List):
        """
        Filter and keep only the columns in the transit_times DataFrame that contain 'CN' in their index.\n
        Returns a list.
        """
        try:
            CN_columns = self.transit_times.loc[self.transit_times.index.str.contains('CN')].astype('int64').to_list()
        except AttributeError as error:
            print("self.transit_times n'a peut-être pas été initialisé...")
            raise error
        return CN_columns


    def get_time_columns(self) -> (List[datetime]):
        """
        Filter and keep only the values in the transit_times DataFrame that contain 'time' in their index.
        Returns a list of datetime objects.
        """
        try:
            time_columns = self.transit_times.loc[self.transit_times.index.str.contains('time')].to_list()
        except AttributeError as error:
            print("self.transit_times n'a peut-être pas été initialisé...")
            raise error
        return time_columns





    def check_nb_records_is_coherent(self, show_log=True):
        """"
        Lit transit_times et vérifie que 'No. of records' est cohérent avec le nombre de colonnes 'Record x CN'.\n
        Sinon renvoie une exception NoOfRecordsNotCoherentError.
        """

        if len(self.transit_times.loc[self.transit_times.index.str.contains('CN')]) != self.transit_times['No. of records']:
            print(f"/!\\ Le nombre de colonnes 'Record x CN' de {self.team_name} ({self.puce}) n'est pas cohérent avec 'No. of records' ({self.transit_times['No. of records']} attendus)!")


    def check_all_epreuve_badgeuses_are_present(self, show_log=True):
        """Pour chaque épreuve dans team.runned_epreuve_courses_list, vérifie que toutes les badgeuses de l'épreuves sont présentes dans team.transit_times, le bon nombre de fois (ignore la badgeuse -1 de mass_start).\n
        Retourne True si une badgeuse n'a pas été bipée, False sinon."""
        
        missing_bip = False
        
        for epreuve_dict in self.runned_epreuve_courses_list:

            # Récupération des badgeuses bipées par l'équipe, avec répétition si badgées plusieurs fois
            transit_times_list = self.get_CN_columns()
            
            epreuve: EpreuveCourse = epreuve_dict['epreuve_course']
            for poincon in epreuve.badgeuses_list:
                # Ignore la badgeuse -1 (mass_start), qui n'a pas encore été ajoutée avec son temps aux données de l'équipe au moment de l'appel de cette méthode.
                if poincon.badgeuse == -1: continue

                if poincon.badgeuse in transit_times_list:
                    transit_times_list.remove(poincon.badgeuse)
                else:
                    missing_bip = True
                    self.missing_bips.append(epreuve)
                    print(f"/!\\ {self.team_name} ({self.puce}) a couru l'épreuve {epreuve.name} mais n'a pas (re?)bipé la badgeuse {poincon.badgeuse} !")

        # Permet de stopper le programme si une équipe n'a pas bipé une badgeuse de l'épreuve, une fois que toutes les badgeuses manquantes de toutes les équipes ont été détectées.
        return missing_bip


    def check_badgeuse_not_bipped_more_than_two_times(self):
        """Vérifie qu'aucune badgeuse n'a été bipée plus de deux fois par l'équipe, ce qui est impossible."""
        pass
    

    def aggregate_transit_times_by_epreuve(self, epreuve_to_aggregate: EpreuveCourse, show_log=False):
        """
        Affecte les temps de transit_times aux épreuves correspondantes.

        /!\ BUG S'IL Y A DES BADGEUSES NO BIPEES SUR LE PARCOURS. IL FAUT AJOUTER LES TEMPS NON BIPES AU BON ENDROIT ET PAS EN FIN DE LIGNE DU CSV.
        """

        for epreuve_dict in self.runned_epreuve_courses_list:
            if epreuve_dict['epreuve_course'] == epreuve_to_aggregate:
                
                if show_log: print(f"{self.team_name}: Regroupement des poinçons de {epreuve_to_aggregate}")
                epreuve_dict['poincons_times'] = []

                epreuve: EpreuveCourse = epreuve_dict['epreuve_course']

                CN_list = self.get_CN_columns()
                bip_time_list = self.get_time_columns()

                badgeuse_idx = 0
                while badgeuse_idx < len(epreuve.badgeuses_list):
                    # print(f"badgeuse_idx: {badgeuse_idx}\nCN_list: {CN_list}\nepreuve.badgeuses_list[badgeuse_idx]['badgeuse_num']: {epreuve.badgeuses_list[badgeuse_idx].badgeuse}")
                    
                    if CN_list[0] == epreuve.badgeuses_list[badgeuse_idx].badgeuse:
                        CN_list.pop(0)
                        bip_time = bip_time_list.pop(0)
                        epreuve_dict['poincons_times'].append((epreuve.badgeuses_list[badgeuse_idx], bip_time))
                        badgeuse_idx += 1
                    else:
                        CN_list.pop(0)
                        bip_time_list.pop(0)
        
        self.check_depart_gel_degel_fin()


    
    def calculate_epreuve_course_times(self, epreuve_to_calculate):
        """Calcule les temps mis par l'équipe sur une course."""
        
        for epreuve_course_dict in self.runned_epreuve_courses_list:
            if epreuve_course_dict['epreuve_course'] == epreuve_to_calculate:

                epreuve_course_dict['elementary_times'] = []    # Stocke les temps mis entre deux badgeuses sous la forme
                
                poincon_time_list: list[tuple[Poincon, str]] = epreuve_course_dict['poincons_times']
                # Sécurité non nécessaire après le check_depart_gel_degel_fin() mais qui a le mérite d'exister 
                # if (len(times_dict_list) % 2) != 0: raise OddNumberOfBipsError(self.team_name, epreuve_course_dict['epreuve_course'].name)


                for i in range(0, len(poincon_time_list)):

                    poincon, time = poincon_time_list[i]
                    if poincon.role != 'fin':   # Evite une erreur d'indice out of bound
                        poincon_next, time_next = poincon_time_list[i+1]


                    if poincon.role in ['gel', 'fin']:
                        continue
                    else:
                        first_time = datetime.strptime(time, "%H:%M:%S")
                        second_time = datetime.strptime(time_next, "%H:%M:%S")

                        elementary_time = second_time - first_time
                        
                        # Stocke sous la forme (temps entre P1 et P2, P1, P2)
                        epreuve_course_dict['elementary_times'].append((elementary_time.total_seconds(), poincon, poincon_next))


                # Calcul du temps total sur l'épreuve
                epreuve_course_dict['total_time'] = sum([elementary_time[0] for elementary_time in epreuve_course_dict['elementary_times']])

                # Calcul du temps meilleur grimpeur
                if epreuve_course_dict['epreuve_course'].meilleur_grimpeur:

                    for elementary_time_tuple in epreuve_course_dict['elementary_times']:
                        elementary_time, poincon_1, poincon_2 = elementary_time_tuple
                        if poincon_1.is_debut_mg and poincon_2.is_fin_mg:
                            epreuve_course_dict['mg_time'] = elementary_time

    

    def calculate_epreuves_course_points(self, show_log=False):
        """
        Calcule les points engrangés pour chaque course:
        - Points bonus par badgeuse bipée
        - Points de participation à la course
        - Points de rapidité
        """

        for epreuve_course_dict in self.runned_epreuve_courses_list:
            epreuve: EpreuveCourse = epreuve_course_dict['epreuve_course']
            if show_log: print(f"{self.team_name}: Calcul des points de l'épreuve {epreuve}")
            epreuve_course_dict['points_dict'] = {}  # Stocke les points de l'épreuve

            # Calcul des points de rapidité
            points_rapidite = 0
            ref_time = epreuve.reference_time*60    # Conversion min -> s

            if not epreuve.meilleur_grimpeur:
                # Ajout des bonus
                if epreuve_course_dict['total_time'] < ref_time:
                    points_rapidite += (ref_time - epreuve_course_dict['total_time'])/60 * epreuve.gain_per_minute
                # Ajout des malus
                if epreuve_course_dict['total_time'] > ref_time:
                    points_rapidite -= (epreuve_course_dict['total_time'] - ref_time)/60 * epreuve.loss_per_minute
            
            else:
                without_mg_time = epreuve_course_dict['total_time'] - epreuve_course_dict['mg_time']
                # Ajout des bonus
                if without_mg_time < ref_time:
                    points_rapidite += (ref_time - without_mg_time)/60 * epreuve.gain_per_minute
                # Ajout des malus
                if without_mg_time > ref_time:
                    points_rapidite -= (without_mg_time - ref_time)/60 * epreuve.loss_per_minute

                # Ajout des points meilleur grimpeur
                points_mg = 0
                mg_ref_time, mg_gain_per_minute , mg_loss_per_minute = epreuve.meilleur_grimpeur['reference_time']*60, epreuve.meilleur_grimpeur['gain_per_minute'], epreuve.meilleur_grimpeur['loss_per_minute']
                
                if epreuve_course_dict['mg_time'] < mg_ref_time:
                    points_mg += (mg_ref_time - epreuve_course_dict['mg_time'])/60 * mg_gain_per_minute
                if epreuve_course_dict['mg_time'] > mg_ref_time:
                    points_mg -= (epreuve_course_dict['mg_time'] - mg_ref_time)/60 * mg_loss_per_minute
                
                epreuve_course_dict['points_dict']['points_mg'] = points_mg

            # Ajout des différents types de points
            epreuve_course_dict['points_dict']['points_bip'] = sum([badgeuse[0].bonus_points for badgeuse in epreuve_course_dict['poincons_times']])
            epreuve_course_dict['points_dict']['points_participation'] = epreuve.participation_points
            epreuve_course_dict['points_dict']['points_rapidite'] = points_rapidite

            # Points totaux sur la course
            epreuve_course_dict['total_points'] = sum(epreuve_course_dict['points_dict'].values())


    def calculate_total_points(self):
        
        self.courses_total_time = sum([course['total_time'] for course in self.runned_epreuve_courses_list])
        self.courses_points = sum([course['total_points'] for course in self.runned_epreuve_courses_list])

        # Dont points de MG, qui sont en réalité déjà comptés dans les points totaux
        for epreuve_course_dict in self.runned_epreuve_courses_list:
            if epreuve_course_dict['epreuve_course'].meilleur_grimpeur:
                self.mg_time += epreuve_course_dict['mg_time']
                self.mg_points += epreuve_course_dict['points_dict']['points_mg']
        
        self.actis_points = sum([acti['participation_points']+acti['ranking_points'] for acti in self.epreuve_actis_list])
        self.total_points = self.courses_points + self.actis_points



    def check_depart_gel_degel_fin(self):
        pass
    


    # DEPRECATED
    def get_badgeuses(self):
        """
        Renvoie la liste des badgeuses bipées par l'équipe, d'après team.transit_times.\n
        Garde les colonnes 'Record x CN' de team.transit_times.
        """
        return self.transit_times.loc[self.transit_times.index.str.contains('CN')].astype('int64')





class OddNumberOfBipsError(Exception):
    """Exception si une équipe a badgé un nombre de fois impair sur une épreuve (pas possible)."""

    def __init__(self, team, epreuve, *args, **kwargs):
        msg = f"Erreur : L'équipe {team} a un nombre impair de bips sur l'épreuve {epreuve} !"
        super().__init__(msg, *args, **kwargs)



class NoOfRecordsNotCoherentError(Exception):
    """Exception levée quand le nombre de colonnes 'Record x CN' n'est pas cohérent avec 'No. of records'."""

    def __init__(self, team_name, no_records, *args, **kwargs):
        msg = f"Le nombre de colonnes 'Record x CN' de {team_name} n'est pas cohérent avec 'No. of records' ({no_records} indiqués)!"
        super().__init__(msg, *args, **kwargs)



    # def keep_CN_columns(self):
    #     """Ne garde que les colonnes 'Record x CN' pour une ligne de datas_graid donnée."""

    #     columns_to_keep = []
    #     Record_idx = 1
    #     while f'Record {Record_idx} CN' in self.transit_times.keys():
    #         columns_to_keep.append(f'Record {Record_idx} CN')
    #         Record_idx += 1
    #     return self.transit_times[columns_to_keep]
    
    # def keep_CN_columns(self) -> (pandas.Series):
    #     """
    #     Filter and keep only the columns in the transit_times DataFrame that contain 'CN' in their index.

    #     Returns:
    #         self.transit_times_CN (pandas.DataFrame): A new DataFrame containing only the columns with 'CN' in their index.
    #     """
    #     try:
    #         self.transit_times_CN = self.transit_times.loc[self.transit_times.index.str.contains('CN')].astype('int64')
    #     except AttributeError as error:
    #         print("self.transit_times n'a peut-être pas été initialisé...")
    #         raise error
    #     return self.transit_times_CN


    # def get_transit_times_records_number(self, epreuve_course: EpreuveCourse) -> (List[int]):
    #         """Renvoie la liste des numéros de Records de datas_graid de la team correspondant à l'épreuve spécifiée en argument.

    #         Args:
    #             epreuve_course (EpreuveCourse): L'épreuve spécifiée.

    #         Returns:
    #             List[int]: La liste des indices des Records correspondant à l'épreuve.
    #             None: Si aucune séquence de Record n'est trouvée.
    #         """
    #         sequence = epreuve_course.badgeuses_sequence   # Séquence dont l'inclusion est à vérifier dans les transit_times de l'équipe
    #         transit_times_epreuve_course_records = []  # Liste contenant les indices des Records correspondant à l'épreuve

    #         transit_times_CN = self.keep_CN_columns()

    #         counter_column = 0  # Contient la position de la colonne courante. 'Record_idx_CN' contient le nom de la colonne courante.
    #         for Record_idx, num_badgeuse in transit_times_CN.items():  # Parcours les colonnes de self.transit_times_CN
    #             counter_column += 1

    #             # Si on tombe sur la première badgeuse de la séquence en parcourant les transit_times de l'équipe
    #             if num_badgeuse == sequence[0]:
    #                 transit_times_epreuve_course_records.append(counter_column)

    #                 # Alors on parcourt la suite des transit_times voir si on continue bien la séquence
    #                 pos_in_sequence = 1 # Position dans la séquence. On a déjà parcouru l'élément 0.
    #                 while pos_in_sequence < len(sequence) and transit_times_CN[f'Record {counter_column+pos_in_sequence} CN'] == sequence[pos_in_sequence]:
    #                     transit_times_epreuve_course_records.append(counter_column+pos_in_sequence)
    #                     pos_in_sequence += 1
    #                 # Si la raison de fin de boucle while est qu'on est arrivée à la fin de la séquence, on peut quitter la boucle for
    #                 if pos_in_sequence == len(sequence):
    #                     break
            
    #         if transit_times_epreuve_course_records != []:
    #             return transit_times_epreuve_course_records
    #         return None


    # def aggregate_transit_times_by_epreuve_course(self, epreuve_courses_list: List[EpreuveCourse]):
    #     """
    #     Regroupe les temps de passage d'une équipe par épreuve pour un meilleur traitement. \n
    #     Crée la liste des épreuves courues par une équipe
    #     """

    #     CN_columns = self.keep_CN_columns()
    #     for epreuve_course in epreuve_courses_list:
    #         transit_times_epreuve_course_records = self.get_transit_times_records_number(epreuve_course, CN_columns)
            
    #         if transit_times_epreuve_course_records is not None:
    #             # self.transit_times_by_epreuve est de la forme {'Obli 1': [hh:mm:ss, hh::mm::ss, ...], 'Obli 2': [hh:mm:ss, hh::mm::ss, ...], ...}
    #             self.transit_times_by_epreuve_course[epreuve_course.name] = [self.transit_times[f'Record {record_idx} time'] for record_idx in transit_times_epreuve_course_records]
        
    #     self.runned_epreuve_courses = list(self.transit_times_by_epreuve_course.keys())
        
    
    # def calculate_running_time(self, epreuve_course: EpreuveCourse):

    #     associate_function_to_badgeuses






    #     # Récupération du premier transit de la course (= départ)
    #     if epreuve_course.mass_start:
    #         start_time = mass_start_time
    #     else:
    #         # Vérification que le premier signaleur est bien un départ
    #         check_is_first_signaleur_depart(signaleur)
    #         start_time = ...

    #     for signaleur in epreuve_course.badgeuses_list:
    #         pass
            

            
