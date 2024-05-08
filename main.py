import logging

from controllers.multidayscontroller import MultiDaysController


def setup_logging():
    """Définition des paramètres de logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='logs.log',
        encoding='utf-8',
        filemode='w',
        format='[%(levelname)s]: %(message)s'
    )




def main():
    
    nightnday = MultiDaysController("DAYS")
    nightnday.create_onedaycontrollers()

    for day in nightnday.onedaycontrollers_list:
        day.initialize()
        day.calculate_times()
        day.calculate_scores()


if __name__ == "__main__":
    setup_logging()
    main()