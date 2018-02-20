"""[Autoranging program for resistor reading and profiling]"""
#########################################
# IMPORTS
#########################################
import logging
try:
    import RPi.GPIO as GPIO
    from colorama import init, Fore, Style
    import Adafruit_ADS1x15
except ImportError as err:
    print('ERROR - Module not installed: '.format(err))

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

# DEBUG MESSAGES
DBG_OPEN_CIRCUIT = Fore.LIGHTRED_EX + 'OPEN CIRCUIT!!'
DBG_SHORT_CIRCUIT = Fore.LIGHTRED_EX + 'SHORT CIRCUIT!!'
DBG_ADC_ERROR = Fore.LIGHTRED_EX + 'ERROR ADC INIT - NOT CONNECTED?'
DBG_ADC_INIT_OK = Fore.LIGHTGREEN_EX + 'ADC Initialized OK.'
DBG_ADC_MUX_RESET = Fore.LIGHTCYAN_EX + 'ADC Range MUX RESET.'
DBG_ADC_AUTORANGE_FAIL = Fore.LIGHTRED_EX + 'ERROR -- AUTORANGE FAILED --'

DBG_ADC_RANGE = 'ADC RANGE MUX CHANNEL SET TO {}'
DBG_ADC_AVG = 'ADC AVG READING: {}'
DBG_ADC_VOLT_RESISTOR = 'Voltage/Resistor - ADCSAMPLE: {}, RESISTOR: {}'


#########################################
# FUNCTION DEFINITIONS
#########################################


def adc_init():
    """[Initializes the ADC settings and mode]
    """
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(MUX_PINS, (int(i) for i in MUX_PINS_IO))  # Sets the pins 17 and 4 as OUTPUTS

        logging.debug(DBG_ADC_INIT_OK)
    except ImportError:
        logging.debug(DBG_ADC_ERROR)


def adc_set_range(output_channel):
    """[Set the range pins of the mux accordingly]

    Arguments:
        output {[int]} -- [from 0 to 3 means from 249kohms to 24R9ohms]
    """
    GPIO.output(MUX_PINS, output_channel)

    logging.debug(DBG_ADC_RANGE.format(output_channel))


def adc_reset_range():
    """[RESETS THE ADC RANGE OUTPUT TO THE HIGHEST 249K ohm value]"""
    GPIO.output(MUX_PINS, RESET_MUX)

    logging.debug(DBG_ADC_MUX_RESET)


def adc_read_average():
    """[Read the ADC channel and averages "avg_samples" times]

    Returns:
        [float] -- [ averaged ADC read value ]
    """
    adc_values_list = [0.0] * ADC_AVG_SAMPLES

    for each in range(ADC_AVG_SAMPLES):
        adc_values_list[each] = adc.read_adc(0, gain=ADC_GAIN)

    reading = sum(adc_values_list) / len(adc_values_list)

    logging.debug(DBG_ADC_AVG.format(reading))
    return reading


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

    logging.debug(DBG_ADC_AUTORANGE_FAIL)


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

    logging.debug(DBG_ADC_VOLT_RESISTOR.format(adc_sample_read, resistor_value))

    return resistor_value


def adc_resistor_read():
    """[Reads ADC channel, with autoranging and returns a value in ohms and scale]

    Returns:
        [Tuple] -- [Resistor value and its scale]
    """
    adc_reset_range()
    adc_sample_read, adc_sample_scale = adc_autorange()

    if adc_sample_read > VOLTAGE_ADC_CEILING and adc_sample_scale == HIGH_IMPEDANCE:
        logging.debug(DBG_OPEN_CIRCUIT)
        return DBG_OPEN_CIRCUIT
    elif adc_sample_read < VOLTAGE_ADC_FLOOR and adc_sample_scale == LOW_IMPEDANCE:
        logging.debug(DBG_SHORT_CIRCUIT)
        return DBG_SHORT_CIRCUIT
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
