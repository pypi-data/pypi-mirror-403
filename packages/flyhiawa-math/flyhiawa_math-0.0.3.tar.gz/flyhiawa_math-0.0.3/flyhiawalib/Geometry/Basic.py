def babilonic(tries: int | float, sqrt: int | float, approx: int | float):
    c = approx
    for _ in range(tries):
        c = (1 / 2) * (c + (sqrt / c))
    return c

def pitagoras(a: int | float, b: int | float):
    return (a ** 2) + (b ** 2)