import Arithmetic
from variables import ARITHMETIC_LIST, HARMONIC_LIST

def arithmetic_mean():
    elements = len(ARITHMETIC_LIST)
    return Arithmetic.plus_list(ARITHMETIC_LIST) / elements

def harmonic_mean():
    elements = len(HARMONIC_LIST)
    pick = [Arithmetic.inverse(x) for x in HARMONIC_LIST]
    return elements / Arithmetic.plus_list(pick)