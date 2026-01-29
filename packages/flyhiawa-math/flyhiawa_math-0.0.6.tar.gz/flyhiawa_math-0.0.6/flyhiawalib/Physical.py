def mass_energy(mass: int | float):
    c = 299792458
    if mass < 0:
        raise ValueError("Mass cannot be negative!")
    else:
        e = mass * c ** 2
        return e
    
def sensible_heat(t, m, c):
    if m < 0 or c < 0:
        raise ValueError("Mass or Heat cannot be negative!")
    return t * m * c