import itertools

from unac.correction.naive import NaiveCorrection
from unac.util.config import Config


def collect_metabolites(data):
    mets = set()
    for tool in data:
        for met in data[tool]:
            mets.add(met)
    return mets


def pairwise_compare_equal(first, second):
    df = second.subtract(first, fill_value=0).abs()
    max_diff = df.max().max()
    return max_diff <= Config.get_diff_tol(), max_diff


def is_problematic(met_data):
    if len(met_data) < 2:
        return False, 0, ""
    for tool in met_data:
        min_val = tool.min().min()
        if min_val < -Config.get_neg_tol():
            return True, min_val, "negative values"
    for comb in itertools.combinations(met_data, 2):
        ok, max_diff = pairwise_compare_equal(comb[0], comb[1])
        if not ok:
            return True, max_diff, "difference to large"
    return False, 0, ""


def compare_results(data):
    mets = collect_metabolites(data)
    problematic = {}
    for met in mets:
        met_data = []
        for tools in data:
            if met in data[tools]:
                met_data.append(data[tools][met].data)
        prob, val, why = is_problematic(met_data)
        if prob:
            problematic[met] = (val, why)
    return problematic


def filter_problematic(cor_data, problematic):
    plain_data = {}
    mets = collect_metabolites(cor_data)

    for met in mets:
        for tool in cor_data:
            # Do not use values from ManualCorrection, if others are available
            if tool == NaiveCorrection().name and len(cor_data) > 1:
                continue
            if met not in problematic and met in cor_data[tool]:
                plain_data[met] = cor_data[tool][met]
                # Take the values from the first tool that delivers them
                # The results are labeled unproblematic, hence they are essentially equal
                # note: the "equality" obviously depends on Config.get_diff_tol()
                continue
    return plain_data
