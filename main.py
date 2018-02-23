"""[Autoranging program for resistor reading and profiling]"""
#########################################
# IMPORTS
#########################################
import logging

try:
    from colorama import init, Style
    from adclib import adc_resistor_read, raspi_init
    from tqdm import tqdm
except ImportError as err:
    print("ERROR - Module not installed: ".format(err))

logging.basicConfig(level=logging.CRITICAL,
                    format=Style.BRIGHT + "%(asctime)s - %(levelname)s - %(message)s" + Style.NORMAL)

#####################################################
# MAIN FUNCTION
#####################################################


def main():
    """[Main entry point]"""
    logging.debug("Main Entry Point")
    raspi_init()
    init()  # Colorama init

    while True:
        for each in tqdm(range(156)):
            read_pin = adc_resistor_read()
        print("Value: ", read_pin)
        input()


if __name__ == "__main__":
    main()
