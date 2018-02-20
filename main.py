"""[Autoranging program for resistor reading and profiling]
"""
#########################################
# IMPORTS
#########################################

import RPi.GPIO as GPIO
import Adafruit_ADS1x15

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

adc = Adafruit_ADS1x15.ADS1115()            # Creates the instance


#########################################
# VARIABLES
#########################################


S1 = RESET_MUX = (GPIO.LOW, GPIO.LOW)       # 249K ohms
S2 = (GPIO.LOW, GPIO.HIGH)                  # 24k9 ohms
S3 = (GPIO.HIGH, GPIO.LOW)                  # 2k49 ohms
S4 = (GPIO.HIGH, GPIO.HIGH)                 # 24R9 ohms

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

#########################################
# FUNCTION DEFINITIONS
#########################################


def init_adc():
    """[Initializes the ADC settings and mode]
    """

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(True)
    GPIO.setup(MUX_PINS, MUX_PINS_IO)  # Sets the pins 17 and 4 as OUTPUTS

    logging.debug('ADC Initialized.')


def set_adc_range(output_channel):
    """[Set the range pins of the mux accordingly]

    Arguments:
        output {[int]} -- [from 0 to 3 means from 249kohms to 24R9ohms]
    """
    GPIO.output(MUX_PINS, output_channel)

    logging.debug('ADC RANGE MUX CHANNEL SET TO {}.'.format(output_channel))


def reset_adc_range():
    """[RESETS THE ADC RANGE OUTPUT TO THE HIGHEST 249K ohm value]
    """
    GPIO.output(MUX_PINS, RESET_MUX)

    logging.debug('ADC Range MUX RESET.')


def read_adc_average():
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


def autorange():
    """[AUTO RANGING SELECTION FUNCTION - If the adc resistor is too high
        the fucntion dials down until a reasonable value is true]

    Returns:
        [INTEGER]   -- [ADC AVERAGE VALUE]
        [STRING]    -- [THE RANGE IN "OHMS" OF SUCH VALUE]
    """
    reset_adc_range()       # RESETS the range to S1 (249K)

    for channel, autorange_scale in zip(MUX_OUTPUTS, RANGE_SCALE_LIST_STR):
        buffered_adc_sample = read_adc_average()
        if buffered_adc_sample < ADC_AUTORANGE_FLOOR:
            set_adc_range(output_channel=channel)
        else:
            return buffered_adc_sample, autorange_scale

    logging.debug('ERROR -- AUTORANGE FAILED --')


def pin_adc_terminal(read_pin):
    """[Read the resistor value]

    Arguments:
        read_pin {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    debug_text = "Volts: {0:>4.4f}     Ohms: {1}"  # Debug text

    if read_pin[0] > 30500:
        return("Open circuit!")
    elif read_pin[0] < 400:
        return("Short to GND!")
    else:
        return debug_text.format(
                                (read_pin[0]*(5.8/30860)) - 0.042,
                                RANGE_SCALE_LIST_STR[read_pin[1]]
                                )


def main():
    """[Main entry point]
    """
    logging.debug('Main Entry Point')
    init_adc()

    while True:
        read_pin = autorange()

        print("DEBUG: Raw ADC: {0:>6} ADCRANGE: {1}".format(read_pin[0],
                                                            read_pin[1]
                                                            ))
        input()


if __name__ == '__main__':
    main()
