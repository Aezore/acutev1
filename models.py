""" MODELS MODULE """
import logging
import random
import msgpack
import numpy

from peewee import SqliteDatabase, Model, CharField, IntegerField, BlobField, ForeignKeyField
from colorama import Style

logging.basicConfig(level=logging.DEBUG,
                    format=Style.BRIGHT + "%(asctime)s - %(levelname)s - %(message)s" +
                    Style.NORMAL)

DB = SqliteDatabase("database.db")

STDV_CORRECTION = 2  # Standard deviation correction factor
COMPLIANT = [1]

###############################################
# DATABASE MODELS
###############################################


class EcuType(Model):
    """ ECU TYPE MODEL CLASS """
    ecu_name = CharField()
    ecu_pincount = IntegerField()

    class Meta:
        """ META CLASS """
        database = DB


class PinData(Model):
    """ PIN DATA MODEL CLASS """
    ecu_name = ForeignKeyField(EcuType, backref="ecu")
    ecu_ref_number = CharField()
    ecu_db_number = IntegerField()
    pin_reading_msgpack = BlobField()

    class Meta:
        """ META CLASS """
        database = DB

#################################################
# FUNCTIONS DEFINITION
#################################################


def uix_input():
    """ TEST ROUTINE MANUAL INPUT """
    name = input("Nombre?: ")
    pincount = input("Pincount?: ")

    create_ecu(name=name, pincount=pincount)
    new_profile(name, pincount)


def create_ecu(name, pincount):
    """ CREATE NEW ECU PROFILE ROUTINE """
    if not EcuType.select().where(EcuType.ecu_name == name):
        ecu = EcuType.create(ecu_name=name, ecu_pincount=pincount)
        ecu.save()
    else:
        print("ECU NAME ALREADY EXIST")


def new_profile(name, pincount):
    """ NEW PROFILE ROUTINE """
    ecu = EcuType.select().where(EcuType.ecu_name == name).get()
    population = get_profiles(ecu_type=ecu)

    sample_data = random.sample(range(1000), pincount)
    save_profile(ecu_type=ecu, data=sample_data, ref="0281011900", dbnumber=20211)

    results = compliance(new_profiledata=sample_data, known_good_values=population)

    if results == COMPLIANT:
        print("ECU IS COMPLIANT UNDER STANDARD PROFILING")
    else:
        for each in results:
            print(each)


def compliance(new_profiledata, known_good_values):
    """
    Test a new set of ADC values with known good ones
    """
    known_and_new = known_good_values[:]
    known_and_new.append(new_profiledata)

    stdv_list = []
    mean_list = []
    results = []

    arr = numpy.array(known_and_new)
    mean_list = numpy.mean(arr, axis=0)
    stdv_list = numpy.std(arr, axis=0)

    for pin_number, (mean_value, stdv, pin_data) in enumerate(zip(mean_list,
                                                                  stdv_list,
                                                                  new_profiledata)):
        if (stdv/mean_value) * 100 > STDV_CORRECTION:
            results.append(['DEFECT', pin_number, mean_value, stdv, pin_data,
                            ((stdv/mean_value)*100)])
        else:
            results.append(['OK', pin_number, mean_value, stdv, pin_data,
                            ((stdv/mean_value)*100)])

    if not results:
        return COMPLIANT

    return results


def powerset(seq):
    """
    Returns all the subsets of this set. This is a generator.
    """
    if len(seq) <= 1:
        yield seq
        yield []
    else:
        for item in powerset(seq[1:]):
            yield [seq[0]]+item
            yield item


def save_profile(ecu_type, data, ref, dbnumber):
    """ SAVE PROFILE ROUTINE """
    profile_datapacked = msgpack.packb(list(data))
    profile = PinData.create(ecu_name=ecu_type,
                             ecu_ref_number=ref,
                             ecu_db_number=dbnumber,
                             pin_reading_msgpack=profile_datapacked)
    profile.save()


def get_profiles(ecu_type):
    """ GET DB PROFILES """
    profile_list = PinData.select().where(PinData.ecu_name == ecu_type)
    profile_datalist = []
    for each in profile_list:
        profile_datalist.append(msgpack.unpackb(each.pin_reading_msgpack))

    return profile_datalist


def init_db():
    """ STARTUP ROUTINE """
    try:
        DB.connect()
        # logging.DEBUG("Database connection OK")
    except Exception as err:
        print(err)
        # logging.DEBUG("Database connection ERROR")

    try:
        DB.create_tables([EcuType, PinData])
        # logging.DEBUG("Database tables created")
    except Exception as err:
        print(err)
        # logging.CRITICAL("Database tables creation ERROR")
