def fatorial(n: int):
    f = 1
    for i in range(f, n + 1):
        f *= i
    return f

def termial(n):
    return (n * (n + 1)) // 2

def plus_list(terms: list[float]):
    return sum(terms)

def inverse(n):
    return 1 / n