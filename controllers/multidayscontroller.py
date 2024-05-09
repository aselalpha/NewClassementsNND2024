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
        logging.info("RÉCUPÉRATION DES JOURNÉES...")

        for folder in os.listdir(self.days_repository):
            # Récupération du numéro de la journée correspondant
            day_num: int = int(folder[1:])
            logging.info("="*50 + f"\nRécupération de la journée J{day_num}...\n" + "-"*50)

            self.odc_list.append(OneDayController(self.days_repository+'/'+folder+'/', day_num))