#########################################
# IMPORTS
#########################################
import logging
from statistics import mean

try:
    import RPi.GPIO as GPIO
    from colorama import Fore, Style
    import Adafruit_ADS1x15
except ImportError as err:
    print("ERROR - Module not installed: ".format(err))

logging.basicConfig(level=logging.CRITICAL,
                    format=Style.BRIGHT + "%(asctime)s - %(levelname)s - %(message)s" + Style.NORMAL)


#########################################
# VARIABLES
#########################################

adc = None  # Initial ADC Object declaration

S1 = RESET_MUX = HIGH_IMPEDANCE = (GPIO.LOW, GPIO.LOW)      # 249K ohms
S2 = (GPIO.LOW, GPIO.HIGH)                                  # 24k9 ohms
S3 = (GPIO.HIGH, GPIO.LOW)                                  # 2k49 ohms
S4 = LOW_IMPEDANCE = (GPIO.HIGH, GPIO.HIGH)                 # 24R9 ohms

MUX_OUTPUTS = (S1, S2, S3, S4)              # List of all 4 mux outputs
MUX_PINS = (17, 4)                          # Raspberry GPIO Pin numbers, S1, S0
MUX_PINS_IO = GPIO.OUT

ADC_AUTORANGE_FLOOR = 6000
ADC_AVG_SAMPLES = 10                        # Average number of adc sampling
ADC_GAIN = 2/3
RANGE_SCALE_LIST_STR = ("/100K", "/10K", "/1K", "ohm")

ADC_VOLTAGE_CLAMP = 5.8  # Maximum voltage clamped at adc input
ADC_MAX_SAMPLE_POINTS = 30860
ADC_CALIBRATION_FLOOR = 0.062
VOLTAGE_ADC_FLOOR = 400
VOLTAGE_ADC_CEILING = 30400

# DEBUG MESSAGES
DBG_OPEN_CIRCUIT = Fore.LIGHTYELLOW_EX + "OPEN CIRCUIT!!" + Fore.RESET
DBG_SHORT_CIRCUIT = Fore.LIGHTYELLOW_EX + "SHORT CIRCUIT!!" + Fore.RESET
DBG_HW_INIT_OK = Fore.LIGHTGREEN_EX + "RPI HW Initialized OK." + Fore.RESET
DBG_HW_INIT_ERR = Fore.LIGHTRED_EX + "ERROR Initializing RPi HW" + Fore.RESET
DBG_ADC_INIT_OK = Fore.LIGHTGREEN_EX + "ADC Initialized OK." + Fore.RESET
DBG_ADC_INIT_ERR = Fore.LIGHTRED_EX + "Can't create ADS1x15 instance object" + Fore.RESET
DBG_ADC_ERROR = Fore.LIGHTRED_EX + "ERROR ADC INIT - NOT CONNECTED?" + Fore.RESET
DBG_ADC_MUX_RESET = Fore.LIGHTCYAN_EX + "ADC Range MUX RESET." + Fore.RESET
DBG_ADC_AUTORANGE_FAIL = Fore.LIGHTRED_EX + "ERROR -- AUTORANGE FAILED -- {}" + Fore.RESET

DBG_ADC_RANGE = "ADC RANGE MUX CHANNEL SET TO {}" + Fore.RESET
DBG_ADC_AVG = "ADC AVG READING: {}" + Fore.RESET
DBG_ADC_VOLT_RESISTOR = "Voltage/Resistor - ADCSAMPLE: {}, RESISTOR: {}" + Fore.RESET


#########################################
# FUNCTION HELPER DEFINITIONS
#########################################


def raspi_init():  # Initializes HW GPIO and ADC
    """[Initializes the ADC settings and mode]"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(MUX_PINS, MUX_PINS_IO)  # Sets the pins 17 and 4 as OUTPUTS

        logging.debug(DBG_HW_INIT_OK)
    except OSError as err:
        logging.debug(DBG_ADC_ERROR + "-" + err)

    global adc
    try:
        adc = Adafruit_ADS1x15.ADS1115()  # Creates the object instance for the ADS1115
        logging.debug(DBG_ADC_INIT_OK)
    except Exception:
        logging.debug(DBG_ADC_INIT_ERR)


def adc_reset_range():  # Resets the mux channel to the highest resistor value
    """[RESETS THE ADC RANGE OUTPUT TO THE HIGHEST 249K ohm value]"""
    adc_set_range(output_channel=RESET_MUX)
    logging.debug(DBG_ADC_MUX_RESET)


def adc_set_range(output_channel):  # Sets the mux output channel to MUX_OUTPUTS[output_channel]
    """[Set the range pins of the mux from argument]

    Arguments:
        output_channel {[int]} -- [from 0 to 3 means from 249kohms to 24R9ohms]
    """
    GPIO.output(MUX_PINS, output_channel)

    logging.debug(DBG_ADC_RANGE.format(output_channel))


def adc_read_average():
    """[Read the ADC channel and averages "avg_samples" times]

    Returns:
        [float] -- [ averaged ADC read value ]
    """

    adc_values_list = [0.0 for _ in range(ADC_AVG_SAMPLES)]
    print("ADC_VALUES_LIST:", adc_values_list)

    for each in range(ADC_AVG_SAMPLES):
        try:
            adc_values_list[each] = adc.read_adc(0, gain=ADC_GAIN)
        except OSError:
            logging.debug(DBG_ADC_ERROR)
    print("ADC_VALUE_LIST_AFTER_AVERAGE: ", adc_values_list)
    reading_mean = mean(adc_values_list)
    print("MEAN: ", reading_mean)

    return int(reading_mean)  # Rounds up the value of the mean


def adc_calibration():  # TODO
    """[ADC Zero Calibration]"""
    pass


def adc_voltage_conversion(adc_sample_read):  # Converts the raw ADC integer value into a ohmic value
    """[ADC Voltage to Resistance conversion]

    Arguments:
        adc_sample_read {[int]} -- [the adc sample read]

    Returns:
        [int] -- [the sample value converted to resistance according to the scale]
    """
    resistor_value = adc_sample_read * (ADC_VOLTAGE_CLAMP/ADC_MAX_SAMPLE_POINTS) - ADC_CALIBRATION_FLOOR

    logging.debug(DBG_ADC_VOLT_RESISTOR.format(adc_sample_read, resistor_value))

    return resistor_value

#####################################
# FUNTION ADC READ DEFINITIONS
#####################################


def adc_autorange():

    for channel, autorange_scale in zip(MUX_OUTPUTS, RANGE_SCALE_LIST_STR):
        adc_set_range(channel)
        print("MUX_OUTPUT: " + str(channel) + "RANGE_SCALE: " + str(autorange_scale))
        buffered_adc_sample = adc_read_average()
        print("Buffered_ADC: ", buffered_adc_sample)

        if buffered_adc_sample < VOLTAGE_ADC_FLOOR and buffered_adc_sample > VOLTAGE_ADC_CEILING:
            pass
        elif buffered_adc_sample < VOLTAGE_ADC_FLOOR and channel == LOW_IMPEDANCE:
            adc_reset_range()
            return buffered_adc_sample, autorange_scale
        elif buffered_adc_sample > VOLTAGE_ADC_CEILING and channel == HIGH_IMPEDANCE:
            adc_reset_range()
            return buffered_adc_sample, autorange_scale
        elif buffered_adc_sample > ADC_AUTORANGE_FLOOR and buffered_adc_sample < VOLTAGE_ADC_CEILING:
            adc_reset_range()
            return buffered_adc_sample, autorange_scale


def adc_resistor_read():
    """[Reads ADC channel, with autoranging and returns a value in ohms and scale]

    Returns:
        [LIST] -- [Resistor value and its scale]
    """
    adc_sample_read, adc_sample_scale = adc_autorange()
    print(adc_sample_read, adc_sample_scale)

    if adc_sample_read > VOLTAGE_ADC_CEILING and adc_sample_scale == HIGH_IMPEDANCE:
        logging.debug(DBG_OPEN_CIRCUIT)
        return DBG_OPEN_CIRCUIT
    elif adc_sample_read < VOLTAGE_ADC_FLOOR and adc_sample_scale == LOW_IMPEDANCE:
        logging.debug(DBG_SHORT_CIRCUIT)
        return DBG_SHORT_CIRCUIT
    else:
        resistor_value = adc_voltage_conversion(adc_sample_read=adc_sample_read)
        return resistor_value, adc_sample_scale
