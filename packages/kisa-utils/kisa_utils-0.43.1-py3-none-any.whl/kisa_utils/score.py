import itertools
import difflib
from kisa_utils.functionUtils import enforceRequirements

def __removeNonAlpha(name:str)->str:
    return ''.join([xter for xter in name if xter.isalpha() or ' '==xter])

def __getCommonCase(name:str)->str:
    return name.upper()

def __getPermutations(names:list[str], itemsPerResult:int=-1) -> list[str]:
    if -1== itemsPerResult:
        return [''.join(p) for p in itertools.permutations(names)]

    results = []
    for nameCombination in itertools.combinations(names, itemsPerResult):
        results += [''.join(p) for p in itertools.permutations(nameCombination)]

    return results

@enforceRequirements
def getNamesMatchScore(namesA:str, namesB:str, /) -> float:
    '''
    Arguments:
        namesA(str): first set of names eg 'John Doe'
        namesB(str): second set of names eg 'Jane Doe'
    Returns:
        score is in range 0.0 - 100.0
    '''
    score:float = 0.0
    if not (namesA and namesB): return score

    # print(f'original: `{namesA}` <-> `{namesB}`')
    namesA, namesB = __getCommonCase(namesA), __getCommonCase(namesB)
    namesA, namesB = __removeNonAlpha(namesA), __removeNonAlpha(namesB)

    namesListA, namesListB = [n for n in namesA.split(' ') if n], [n for n in namesB.split(' ') if n]
    namesListA.sort(); namesListB.sort()

    if not (len(namesListA)>1 and len(namesListB)>1): return score

    # print(f'cleaned: `{" ".join(namesListA)}` <-> `{" ".join(namesListB)}`')

    if namesListA == namesListB: return 100.0

    leastNameCount = min(len(namesListA), len(namesListB))

    for permutationA in __getPermutations(namesListA, itemsPerResult=leastNameCount):
        for permutationB in __getPermutations(namesListB, itemsPerResult=leastNameCount):
            if (_score := difflib.SequenceMatcher(None, permutationA, permutationB).ratio()*100) > score:
                # print(f'    {permutationA}, {permutationB}')
                score = _score
                if 100.0 == score: return score

    return score
