import os
import logging

from controllers.onedaycontroller import OneDayController


class MultiDaysController:

    def __init__(self, days_repository: str) -> None:
        self.days_repository = days_repository
        self.odc_list: list[OneDayController] = []


    def create_onedaycontrollers(self):
        """
        Crée la liste des OneDayController permettant de gérer chaque journée.
        """
        logging.info("Récupération de la liste des journées...")

        for folder in os.listdir(self.days_repository):
            # Récupération du numéro de la journée correspondant
            day_num: int = int(folder[1:])
            self.odc_list.append(OneDayController(self.days_repository+folder+'/', day_num))

        logging.info(f"Les journées {[odc for odc in self.odc_list]} ont été récupérées.")