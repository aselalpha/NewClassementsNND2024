import json
import logging
import pandas as pd

from data_collectors.datas_graid_collector import DatasGraidCollector
from data_collectors.teams_gen_collector import TeamsGenCollector
from data_collectors.polis_parcours_collector import PolisParcoursCollector
from data_collectors.polis_badgeuses_collector import PolisBadgeusesCollector
from data_collectors.data_actis_collector import DataActisCollector

from models.team import Team
from models.epreuve import EpreuveCourse, EpreuveActi
from models.poincon import Poincon


class OneDayController:

    def __init__(self, day_repository: str, day_num: int) -> None:
        self.day_repository = day_repository
        self.day_num = day_num

        # Récupération de toutes les données d'initialisation
        with open(self.day_repository+'initialisation.json') as json_file:
            data = json.load(json_file)

        self.datas_graid = DatasGraidCollector(data['doigts_csv'])
        self.data_actis = DataActisCollector(data['actis_excel'])
        self.teams_gen = TeamsGenCollector(data['teams_excel'])
        self.polis_parcours = PolisParcoursCollector(data['epreuves_excel'])
        self.polis_badgeuses = PolisBadgeusesCollector(data['badgeuses_excel'])

        self.mass_start: str|None = data['mass_start']

        self.teams_list: list[Team] = self.teams_gen.create_teams()
        self.epreuves_list: list[EpreuveCourse|EpreuveActi] = self.polis_parcours.create_epreuves()

        self.epreuves_courses_list: list[EpreuveCourse] = [course for course in self.epreuves_list if isinstance(course, EpreuveCourse)]
        self.epreuves_actis_list: list[EpreuveActi] = [acti for acti in self.epreuves_list if isinstance(acti, EpreuveActi)]


    def __repr__(self) -> str:
        return f"ODC(J{self.day_num})"


    def initialize(self):

        self.add_badgeuses_to_epreuves()
        self.add_datas_doigts_to_teams()

        self.add_mass_start()

        self.add_runned_epreuves_to_teams()
        self.add_actis_to_teams()
    

    def calculate_times(self):
        """Calcule les temps mis par chaque équipe sur chaque épreuve."""
        logging.info("Calcul des temps courus par chaque équipe sur chaque épreuve...")

        for team in self.teams_list:
            for epreuve_course in self.epreuves_courses_list:
                team.aggregate_transit_times_by_epreuve(epreuve_course)
                team.calculate_epreuve_course_times(epreuve_course)
        logging.info("Temps calculés.\n" + "-"*50)


    ##################################
    ### Appelées dans initialize() ###
    ##################################

    def add_badgeuses_to_epreuves(self):
        """Ajoute les badgeuses lues dans le POLIS_badgeuses à l'épreuve correspondante de epreuves_list."""
        logging.info("Ajout des badgeuses aux épreuves...")

        for _, row in self.polis_badgeuses.df.iterrows():
            epreuve: EpreuveCourse = self.get_epreuve(row['epreuve'])

            poincon_to_add = Poincon(epreuve, str(row['signaleur']), int(row['numero']), str(row['fonction']), float(row['points']))
            epreuve.badgeuses_list.append(poincon_to_add)
            
            logging.info(f"Ajout de la badgeuse {row['numero']} ({row['fonction']}) à {epreuve.name}")
            
            # Si présence d'un meilleur grimpeur dans l'épreuve, on arrange les poinçons pour qu'il n'y ait pas de doublon
            if epreuve.meilleur_grimpeur and poincon_to_add.role == 'fin':
                epreuve.clean_meilleur_grimpeur()
        
        logging.info("Toutes les badgeuses ont été ajoutées aux épreuves correspondantes.\n" + "-"*50)


    def add_datas_doigts_to_teams(self):
        """Attribue à chaque équipe ses temps de passage (transit time)."""

        logging.info("Attribution des données des doigts aux équipes correspondantes...")

        for _, row in self.datas_graid.df_cleaned.iterrows():
            team = self.get_team_from_doigt(row)
            team.transit_times = row.dropna()

            # Convertir les colonnes Record x CN en int
            CN_columns_of_transit_times = [column for column in team.transit_times.keys() if 'CN' in column]
            team.transit_times[CN_columns_of_transit_times] = team.transit_times[CN_columns_of_transit_times].astype('int64')

            logging.info(f"Attribution des données à {team.team_name}")
        
        self.clean_teams_not_running()

        logging.info("Toutes les données des doigts ont été attribuées aux équipes correspondantes.\n" + "-"*50)


    def add_mass_start(self):
        """
        Ajoute le temps mass_start correspondant à la badgeuse -1 aux données de doigt.
        """

        if self.mass_start == None:
            logging.info(f"Pas de mass start pris en compte.\n" + "-"*50)
            return
        
        # Vérifie le format d'entrée de mass_start
        self.check_mass_start_time_format()
        # Ajout du temps de mass_start aux équipes.
        for team in self.teams_list:
            mass_start_CN_and_time = pd.Series({'Record 0 CN': -1, 'Record 0 time': self.mass_start})
            team.transit_times = pd.concat([mass_start_CN_and_time, team.transit_times])
        
        logging.info(f"Prise en compte de l'horaire de mass start {self.mass_start}.\n" + "-"*50)


    def add_runned_epreuves_to_teams(self):
        """
        Ajoute à chaque équipe les épreuves qu'elle a courues sous la forme {'epreuve_course': EpreuveCourse, 'time': temps en s, 'points': float}.

        Regarde dans les badgeuses présentes dans team.transit_times (index Record x CN) et à quelle épreuve ces badgeuses sont affectées.\n
        Vérifie dans le même temps si pour chaque épreuve courue, toutes les badgeuses sont bien présentes.
        """
        logging.info("Ajout des épreuves courues à chaque équipe...")

        global_missing_bip = False

        for team in self.teams_list:
            # Récupération des badgeuses de l'équipe à partir de team.transit_times
            team_badgeuses_list = team.get_CN_columns()

            for epreuve in self.epreuves_courses_list:
                for poincon in epreuve.badgeuses_list:                    
                    if poincon.badgeuse in team_badgeuses_list:
                        team.runned_epreuve_courses_list.append({'epreuve_course': epreuve})
                        logging.info(f"{team} a couru {epreuve}.")
                        break

            team_missing_bip = team.check_all_epreuve_badgeuses_are_present()
            if team_missing_bip: global_missing_bip = True
        
        logging.info("Chaque équipe a sa liste d'épreuves courues.\n" + "-"*50)

        # Stoppe le programme si une équipe n'a pas bipé une badgeuse de l'épreuve, une fois que toutes les badgeuses manquantes de toutes les équipes ont été détectées.
        if global_missing_bip:
            self.calculate_mean_times_for_each_segment()
            raise MissingBipsError()


    def add_actis_to_teams(self):
        """
        Ajoute à chaque équipe les actis auxquelles elle a participé, à partir de data_actis.
        """
        logging.info("Ajout des résultats des actis à chaque équipe...")

        # On itère sur les feuilles d'activité de l'Excel
        for acti in self.data_actis.actis_dict.values():
            
            epreuve_acti_object = self.get_epreuve(acti['acti_name'])

            # On itère sur les équipes ayant participé à l'épreuve
            for participating_team in acti['teams_results']:
                team_to_add = self.get_team_from_dossard(participating_team['dossard'])
                team_to_add.epreuve_actis_list.append({'epreuve_acti': epreuve_acti_object,
                                                       'medal': participating_team['medal'],
                                                       'participation_points': epreuve_acti_object.participation_points,
                                                       'ranking_points': epreuve_acti_object.or_argent_bronze[participating_team['medal']]})
                
                logging.info(f"{epreuve_acti_object.name}: {participating_team['medal'].upper()} pour [{team_to_add.dossard}] {team_to_add.team_name}")
        
        logging.info("Tous les résultats d'actis sont ajoutés.\n" + "-"*50)


    ##################################


    def get_team_from_dossard(self, dossard) -> (Team):

        for team in self.teams_list:
            if team.dossard == dossard:
                return team
        
        raise DossardNotFoundError(dossard)


    def calculate_mean_times_for_each_segment(self):

        logging.info("Calcul des temps moyens sur chaque portion d'épreuves...")

        for team in self.teams_list:

            for epreuve_course_dict in team.runned_epreuve_courses_list:
                epreuve_course: EpreuveCourse = epreuve_course_dict['epreuve_course']
                if epreuve_course not in team.missing_bips:
                    
                    team.aggregate_transit_times_by_epreuve(epreuve_course)
                    team.calculate_epreuve_course_times(epreuve_course)
                    for elementary_time in epreuve_course_dict['elementary_times']:
                        epreuve_course.times_between_poincons.append(elementary_time)
        
        for epreuve_course in self.epreuves_courses_list:
            epreuve_course.average_elementary_times()
            logging.info(epreuve_course.name, epreuve_course.mean_times_between_poincons)


    def check_mass_start_time_format(self):
        """Check if the format of mass_start is hh:mm:ss"""
        try:
            time_list = self.mass_start.split(':')
            if len(time_list) != 3:
                raise MassStartTimeFormatNotValidError(self.mass_start)
            for time in time_list:
                if len(time) != 2:
                    raise MassStartTimeFormatNotValidError(self.mass_start)
                int(time)
        except ValueError:
            raise MassStartTimeFormatNotValidError(self.mass_start)


    def get_team_from_doigt(self, row) -> Team:
        """Récupère l'équipe correspondant à la ligne passée en argument."""
        for team in self.teams_list:
            if team.puce == row['SIID']:
                return team
        logging.warning(f"Le doigt de SIID {row['SIID']} semble n'avoir aucune équipe atitrée !")


    def get_epreuve(self, epreuve_name: str) -> EpreuveCourse|EpreuveActi:
            """
            Retourne l'Epreuve dont le nom est epreuve_name parmi la liste d'Epreuves epreuves_list.


            Raises:
                EpreuveInPolisBadgeusesNotFoundError: Si l'épreuve n'est pas trouvée dans la liste des épreuves.
            """
            for epreuve in self.epreuves_list:
                if epreuve_name == epreuve.name:
                    return epreuve
            raise EpreuveInPolisBadgeusesNotFoundError(epreuve_name, self.epreuves_list)


    def clean_teams_not_running(self):
        """Supprime de la liste des équipes toutes celles qui n'ont pas de donnée de doigt associée."""

        teams_to_ignore = []
        # Equipe ignorée si elle n'a rien bipée du tout
        for team in self.teams_list:
            if len(team.transit_times) == 0:
                logging.warning(f"Doigt {team.puce} de l'équipe [{team.dossard}] {team.team_name} non récupéré. Celle-ci est ignorée.")
                teams_to_ignore.append(team)
        for team in teams_to_ignore:
            self.teams_list.remove(team)



#########################
### Classes d'Erreurs ###
#########################


class EpreuveInPolisBadgeusesNotFoundError(Exception):
    """Gère les exceptions liées à une épreuve mal écrite dans POLIS_badgeuses.csv"""
    
    def __init__(self, epreuve_name, epreuves_list, *args, **kwargs):
        msg = f"Erreur : L'épreuve {epreuve_name} n'existe pas dans les épreuves définies suivantes : {epreuves_list}"
        super().__init__(msg, *args, **kwargs)


class MassStartTimeFormatNotValidError(Exception):
    """Gère les exceptions liées à un format de temps de mass_start invalide."""
    
    def __init__(self, mass_start, *args, **kwargs):
        msg = f"Erreur : Le temps de mass_start {mass_start} n'est pas au format hh:mm:ss !"
        super().__init__(msg, *args, **kwargs)


class MissingBipsError(Exception):
    """Gère les exceptions liées à des équipes qui n'ont pas bipé toutes les badgeuses de l'épreuve."""

    def __init__(self, *args, **kwargs):
        msg = f"Erreur : Une ou plusieurs équipes n'ont pas bipé toutes les badgeuses de l'épreuve !"
        super().__init__(msg, *args, **kwargs)


class DossardNotFoundError(Exception):
    """Gère les exceptions liées à un dossard inexistant. Par exemple si mal entré dans data_actis.xlsx."""

    def __init__(self, dossard, *args, **kwargs):
        msg = f"Erreur : Le dossard {dossard} n'est pas référencé dans la liste des participants !"
        super().__init__(msg, *args, **kwargs)