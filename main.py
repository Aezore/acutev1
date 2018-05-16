"""[Autoranging program for resistor reading and profiling]"""
#########################################
# IMPORTS
#########################################
import logging
import models

try:
    from colorama import Style
    from colorama import init as colorama_init
    from adclib import adc_resistor_read, raspi_init

    # from tqdm import tqdm
except ImportError as err:
    print("ERROR - Module not installed: {}".format(err))

logging.basicConfig(level=logging.CRITICAL,
                    format=Style.BRIGHT + "%(asctime)s - %(levelname)s - %(message)s" +
                    Style.NORMAL)

#####################################################
# MAIN FUNCTION
#####################################################


def startup():
    """ STARTUP ROUTINE """
    raspi_init()
    colorama_init()
    models.init_db()


def main():
    """[Main entry point]"""
    logging.debug("Main Entry Point")
    startup()
    models.uix_input()
    while True:
        read_pin, read_scale = adc_resistor_read()
        print("main.Value: {:<4} - {:>6}".format(read_pin, read_scale))
        input()


if __name__ == "__main__":
    main()
