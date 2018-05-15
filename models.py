from peewee import SqliteDatabase, Model, CharField, IntegerField, BlobField, ForeignKeyField
from colorama import Style
import logging
import msgpack
import random
import numpy

logging.basicConfig(level=logging.DEBUG,
                    format=Style.BRIGHT + "%(asctime)s - %(levelname)s - %(message)s" + Style.NORMAL)

db = SqliteDatabase("database.db")

STDV_CORRECTION = 2  # Standard deviation correction factor
COMPLIANT = [1]

###############################################
# DATABASE MODELS
###############################################


class ecu_type(Model):
    ecu_name = CharField()
    ecu_pincount = IntegerField()

    class Meta:
        database = db


class pin_data(Model):
    ecu_name = ForeignKeyField(ecu_type, backref="ecu")
    ecu_ref_number = CharField()
    ecu_db_number = IntegerField()
    pin_reading_msgpack = BlobField()

    class Meta:
        database = db

#################################################
# FUNCTIONS DEFINITION
#################################################


def uix_input():
    name = input("Nombre?: ")
    pincount = input("Pincount?: ")

    create_ecu(name=name, pincount=pincount)
    new_profile(name, pincount)


def create_ecu(name, pincount):
    if not ecu_type.select().where(ecu_type.ecu_name == name):
        ecu = ecu_type.create(ecu_name=name, ecu_pincount=pincount)
        ecu.save()
    else:
        print("ECU NAME ALREADY EXIST")


def new_profile(name, pincount):
    ecu = ecu_type.select().where(ecu_type.ecu_name == name).get()
    population = get_profiles(ecu)

    # sample_data = (random.randint(0, 9) for each in range(156))
    sample_data = random.sample(range(1000), 156)
    save_profile(ecu, sample_data, "0281011900", 20211)

    results = compliance(new_profiledata=sample_data, known_good_values=population)

    if results == COMPLIANT:
        print("ECU IS COMPLIANT UNDER STANDARD PROFILING")
    else:
        for each in results:
            print(each)


def compliance(new_profiledata, known_good_values):
    known_and_new = known_good_values[:]
    known_and_new.append(new_profiledata)

    stdv_list = []
    mean_list = []
    results = []

    arr = numpy.array(known_and_new)
    mean_list = numpy.mean(arr, axis=0)
    stdv_list = numpy.std(arr, axis=0)

    for pin_number, (mean_value, stdv, pin_data) in enumerate(zip(numpy.nditer(mean_list),
                                                                  numpy.nditer(stdv_list),
                                                                  new_profiledata)):
        if pin_data > mean_value + (STDV_CORRECTION * stdv) or pin_data < mean_value - (STDV_CORRECTION * stdv):
            results.append(['DEFECT', pin_number, mean_value, stdv, pin_data])

    if not results:
        return COMPLIANT
    else:
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
    profile_datapacked = msgpack.packb(list(data))
    profile = pin_data.create(ecu_name=ecu_type,
                              ecu_ref_number=ref,
                              ecu_db_number=dbnumber,
                              pin_reading_msgpack=profile_datapacked)
    profile.save()


def get_profiles(ecu_type):
    profile_list = pin_data.select().where(pin_data.ecu_name == ecu_type)
    profile_datalist = []
    for each in profile_list:
        profile_datalist.append(msgpack.unpackb(each.pin_reading_msgpack))

    return profile_datalist


def init_db():
    try:
        db.connect()
        # logging.DEBUG("Database connection OK")
    except Exception as err:
        print(err)
        # logging.DEBUG("Database connection ERROR")

    try:
        db.create_tables([ecu_type, pin_data])
        # logging.DEBUG("Database tables created")
    except Exception as err:
        print(err)
        # logging.CRITICAL("Database tables creation ERROR")
