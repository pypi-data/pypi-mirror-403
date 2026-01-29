**Como Instalar**: ```pip install flyhiawa-math```

Como usar funções de médias:
```python
from flyhiawa-math import Statistics.means

Statistics.means.HARMONIC_LIST.extend([2, 7, 3, 0.68])
print(Statistics.means.harmonic_mean())
```
Ou
```python
from flyhiawa-math import Statistics.means

Statistics.means.ARITHMETIC_LIST.extend([2, 7, 3, 0.68])
print(Statistics.means.arithmetic_mean())
```

Imprimir as outras funções:
```python
import flyhiawa-math

print(babilonic(9, 185, 169))
```

Listas das funções:
- babilonic(tries, sqrt, approx)
- fatorial(n)
- termial(n)
- pitagoras(a, b)
- mass_energy(mass)
- sensible_heat(t, m, c)
- harmonic_mean()
- arithmetic_mean()
- hypercube_edges(d)
- hypercube_faces(d)
- hypercube_vertices(d)
- inverse(n)
- plus_list(terms)

Variáveis:
```python
ARITHMETIC_LIST
HARMONIC_LIST
```