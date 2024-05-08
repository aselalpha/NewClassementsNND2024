import os
import logging

from controllers.onedaycontroller import OneDayController


class MultiDaysController:

    def __init__(self, days_repository: str) -> None:
        self.days_repository = days_repository


    def create_onedaycontrollers(self):
        """
        Crée la liste des OneDayController permettant de gérer chaque journée, `onedaycontrollers_list`.
        """
        logging.info("Récupération de la liste des journées...")

        odc_list: list[OneDayController] = []

        for folder in os.listdir(self.days_repository):
            # Récupération du numéro de la journée correspondant
            num_journee: int = int(folder[1:])
            odc_list.append(OneDayController(self.days_repository+folder+'/', num_journee))
        
        self.onedaycontrollers_list = odc_list
        logging.info(f"Toutes les journées ont été récupérées: {[odc for odc in self.onedaycontrollers_list]}")