
DEPENDENCY:int = 1 << 0
LINK:int = 1 << 1
TENTATIVE:int = 1 << 2
REFUTATION:int = 1 << 3


def is_edge_type(edge, *edge_types:int):
    for t in edge_types:
        if not t & edge:
            return False

    return True
