import logging
import datetime

from controllers.multidayscontroller import MultiDaysController


def setup_logging():
    """Définition des paramètres de logging."""
    datetimenow = datetime.datetime.now().strftime("%Y-%m-%d %H %M %S")

    logging.basicConfig(
        level=logging.DEBUG,
        encoding='utf-8',
        format='[%(levelname)s]: %(message)s',
        handlers=[
            logging.FileHandler("LOGS/"+datetimenow+".log"),
            logging.StreamHandler()
        ]
    )




def main():
    
    nightnday = MultiDaysController("DAYS")
    nightnday.create_onedaycontrollers()

    for day in nightnday.odc_list:
        day.initialize()
        # day.calculate_times()
        # day.calculate_scores()


if __name__ == "__main__":
    setup_logging()
    main()