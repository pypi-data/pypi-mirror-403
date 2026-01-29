def hypercube_faces(d):
    if d < 0:
        raise ValueError("Dimension cannot is 0!")
    else:
        return ((d * (d - 1)) / 2) * (2 ** (d - 2))
    
def hypercube_edges(d):
    if d < 0:
        raise ValueError("Dimension cannot is 0!")
    else:
        return (2 ** (d - 1)) * d
    
def hypercube_vertices(d):
    if d < 0:
        raise ValueError("Dimension cannot is 0!")
    else:
        return 2 ** d