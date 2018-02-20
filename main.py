"""[Autoranging program for resistor reading and profiling]"""
#########################################
# IMPORTS
#########################################
import logging
import RPi.GPIO as GPIO
from colorama import init, Fore, Style
import Adafruit_ADS1x15

logging.basicConfig(level=logging.DEBUG,
                    format=Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s')

adc = Adafruit_ADS1x15.ADS1115()            # Creates the instance


#########################################
# VARIABLES
#########################################


S1 = RESET_MUX = HIGH_IMPEDANCE = (GPIO.LOW, GPIO.LOW)       # 249K ohms
S2 = (GPIO.LOW, GPIO.HIGH)                  # 24k9 ohms
S3 = (GPIO.HIGH, GPIO.LOW)                  # 2k49 ohms
S4 = LOW_IMPEDANCE = (GPIO.HIGH, GPIO.HIGH)                 # 24R9 ohms

MUX_OUTPUTS = (S1, S2, S3, S4)              # List of all 4 mux outputs
MUX_PINS = (17, 4)                          # Raspberry GPIO Pin numbers
MUX_PINS_IO = (GPIO.OUT, GPIO.OUT)

ADC_AUTORANGE_FLOOR = 3000
ADC_AVG_SAMPLES = 10                        # Average number of adc sampling
ADC_GAIN = 2/3
RANGE_SCALE_LIST_STR = ("/100K",            # Range labels
                        "/10K",
                        "/1K",
                        "ohm")

ADC_VOLTAGE_CLAMP = 5.8  # Maximum voltage clamped at adc input
ADC_MAX_SAMPLE_POINTS = 30860
ADC_CALIBRATION_FLOOR = 0.042
VOLTAGE_ADC_FLOOR = 400
VOLTAGE_ADC_CEILING = 30400

OPEN_CIRCUIT_DBG = Fore.LIGHTRED_EX + 'OPEN CIRCUIT!!'
SHORT_CIRCUIT_DBG = Fore.LIGHTRED_EX + 'SHORT CIRCUIT!!'


#########################################
# FUNCTION DEFINITIONS
#########################################


def adc_init():
    """[Initializes the ADC settings and mode]
    """
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(MUX_PINS, MUX_PINS_IO)  # Sets the pins 17 and 4 as OUTPUTS
        logging.debug(Fore.LIGHTGREEN_EX + 'ADC Initialized OK.')
    except:
        logging.debug(Fore.LIGHTRED_EX + 'ERROR ADC INIT - NOT CONNECTED?')


def adc_set_range(output_channel):
    """[Set the range pins of the mux accordingly]

    Arguments:
        output {[int]} -- [from 0 to 3 means from 249kohms to 24R9ohms]
    """
    GPIO.output(MUX_PINS, output_channel)

    logging.debug('ADC RANGE MUX CHANNEL SET TO {}.'.format(output_channel))


def adc_reset_range():
    """[RESETS THE ADC RANGE OUTPUT TO THE HIGHEST 249K ohm value]"""
    GPIO.output(MUX_PINS, RESET_MUX)

    logging.debug(Fore.LIGHTCYAN_EX 'ADC Range MUX RESET.')


def adc_read_average():
    """[Read the ADC channel and averages "avg_samples" times]

    Returns:
        [INTEGER] -- [ averaged ADC read value ]
    """
    adc_values_list = [0.0] * ADC_AVG_SAMPLES

    for each in range(ADC_AVG_SAMPLES):
        adc_values_list[each] = adc.read_adc(0, gain=ADC_GAIN)

    reading = sum(adc_values_list) / len(adc_values_list)

    logging.debug('ADC AVG READING: {}'.format(reading))
    return int(reading)


def adc_autorange():
    """[AUTO RANGING SELECTION FUNCTION - If the adc resistor is too high
        the fucntion dials down until a reasonable value is true]

    Returns:
        [INTEGER]   -- [ADC AVERAGE VALUE]
        [STRING]    -- [THE RANGE IN "OHMS" OF SUCH VALUE]
    """
    for channel, autorange_scale in zip(MUX_OUTPUTS, RANGE_SCALE_LIST_STR):
        buffered_adc_sample = adc_read_average()
        if buffered_adc_sample < ADC_AUTORANGE_FLOOR:
            adc_set_range(output_channel=channel)
        else:
            return buffered_adc_sample, autorange_scale

    logging.debug('ERROR -- AUTORANGE FAILED --')


def adc_calibration():
    pass


def adc_voltage_conversion(adc_sample_read):
    """[ADC Voltage to Resistance conversion]

    Arguments:
        adc_sample_read {[int]} -- [the adc sample read]

    Returns:
        [int] -- [the sample value converted to resistance according to the scale]
    """
    resistor_value = adc_sample_read * (ADC_VOLTAGE_CLAMP/ADC_MAX_SAMPLE_POINTS) - ADC_CALIBRATION_FLOOR
    logging.debug('adc_voltage_conv - ADCSAMPLE: {}, RESISTOR: {}'.format(adc_sample_read, resistor_value))
    return resistor_value


def adc_resistor_read():
    """[Reads ADC channel, with autoranging and returns a value in ohms and scale]

    Returns:
        [Tuple] -- [Resistor value and its scale]
    """
    adc_reset_range()
    adc_sample_read, adc_sample_scale = adc_autorange()

    if adc_sample_read > VOLTAGE_ADC_CEILING and adc_sample_scale == HIGH_IMPEDANCE:
        logging.debug(OPEN_CIRCUIT_DBG)
        return OPEN_CIRCUIT_DBG
    elif adc_sample_read < VOLTAGE_ADC_FLOOR and adc_sample_scale == LOW_IMPEDANCE:
        logging.debug(SHORT_CIRCUIT_DBG)
        return SHORT_CIRCUIT_DBG
    else:
        resistor_value = adc_voltage_conversion(sample=adc_sample_read)
        return resistor_value, adc_sample_scale


def main():
    """[Main entry point]"""
    logging.debug('Main Entry Point')
    adc_init()
    init()  # Colorama init

    while True:
        read_pin, scale = adc_resistor_read()
        print(read_pin, scale)
        input()


if __name__ == '__main__':
    main()
