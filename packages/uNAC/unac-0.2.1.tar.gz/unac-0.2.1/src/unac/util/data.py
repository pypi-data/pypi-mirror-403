import copy
import math
import re
import unicodedata
from collections import Counter

import numpy as np
import pandas as pd

CHEM_SYMBOLS = [
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
]


class DataError(Exception):
    def __init__(self, msg):
        self.msg = msg


class ChemFormula:
    def __init__(self, formula):
        is_it, msg = ChemFormula.is_chem_formula(formula)
        if not is_it:
            raise DataError(msg)
        self.elems: dict[str, int] = ChemFormula.__frag_to_counts(formula)

    @staticmethod
    def is_chem_formula(formula) -> tuple[bool, str]:
        # a chemical (sum) formula is a non-empty string consisting of Elements (Upper case letter and optionally
        # lowercase letter) and numbers
        chemical_formula_pattern = re.compile(r"(([A-Z][a-z]*)(\d*))+")
        if not chemical_formula_pattern.fullmatch(formula):
            return False, "not a chemical formula"
        # check if no element occurs twice
        p = re.compile(r"([A-Z][a-z]*)\d*")
        elems = re.findall(p, formula)
        if not len(elems) == len(set(elems)):
            return False, "duplicate element"
        # we also check, if the Element is actually a chemical element
        for elem in elems:
            if elem not in CHEM_SYMBOLS:
                return False, f"{elem} is not a chemical element"
        return True, ""

    @staticmethod
    def __frag_to_counts(frag) -> dict[str, int]:
        p = re.compile(r"([A-Z][a-z]*)(\d*)")
        frag_tuples = re.findall(p, frag)
        frag_elems: dict[str, int] = {}
        for elem in frag_tuples:
            count = elem[1]
            if elem[1] == "":
                count = "1"
            count = int(count)
            if count == 0:
                continue
            frag_elems[elem[0]] = int(count)
        return frag_elems

    def __le__(self, other) -> bool:
        assert isinstance(other, ChemFormula)
        for elem in self.elems:
            if elem not in other.elems:
                return False
            if other.elems[elem] < self.elems[elem]:
                return False
        return True

    def __ge__(self, other) -> bool:
        assert isinstance(other, ChemFormula)
        return other <= self

    def __add__(self, other):
        assert isinstance(other, ChemFormula)
        out = copy.deepcopy(self)
        for elem in other.elems:
            if elem in out.elems:
                out.elems[elem] += other.elems[elem]
            else:
                out.elems[elem] = other.elems[elem]
        return out

    def __sub__(self, other):
        assert isinstance(other, ChemFormula)
        assert other <= self
        out = copy.deepcopy(self)
        for elem in other.elems:
            if out.elems[elem] == other.elems[elem]:
                out.elems.pop(elem, None)
                continue
            out.elems[elem] -= other.elems[elem]
        return out

    def __str__(self) -> str:
        order = ["C", "H", "N", "O", "P", "S", "Si"]
        out = ""
        for elem in order:
            if elem in self.elems:
                out += f"{elem}{self.elems[elem]}"

        keys = list(set(self.elems.keys()) - set(order))
        keys.sort()
        for elem in keys:
            out += f"{elem}{self.elems[elem]}"

        return out

    def __eq__(self, other) -> bool:
        if isinstance(other, ChemFormula):
            return self <= other <= self
        else:
            return False


def slugify(value):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    taken from django.utils
    """
    value = str(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = value.replace("_", "-")
    return re.sub(r"[-\s]+", "-", value)


class RepTime:
    def __init__(self, rep, time):
        self.rep = rep
        self.time = time

    def req(self, rep):
        return self.rep == rep

    def teq(self, time):
        return self.time == time

    def __str__(self):
        return f"Rep:{self.rep} Time:{self.time}"

    def __repr__(self):
        return self.__str__()


class MassLane:
    def __init__(self, pre_shift, pro_shift, msms: bool):
        self.pre_shift: int = int(pre_shift)
        self.pro_shift: int = int(pro_shift)
        self.msms: bool = msms

    def __str__(self) -> str:
        if self.msms:
            return f"M{self.pre_shift}->m{self.pro_shift}"
        else:
            return f"M{self.pre_shift}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if isinstance(other, MassLane):
            return (self.pre_shift == other.pre_shift) and (self.pro_shift == other.pro_shift)
        return False

    def __hash__(self):
        return hash(str(self))


def is_number(s) -> bool:
    """
    Check if something can be converted to a number
    :param s: the object (string?) to check
    :return: True iff s can be converted to a number
    """
    if s is None:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def represents_int(s) -> bool:
    """
    Check if something can be converted to an integer number
    :param s: the object (string?) to check
    :return: True iff s can be converted to an integer number
    """
    if s is None:
        return False
    try:
        int(s)
        return True
    except ValueError:
        return False


class Measurement:
    default_stddev: float = 0.01

    def __init__(
        self,
        mid: str,
        masses: list[MassLane],
        pre: str,
        pre_c: str | int,
        pre_mass: str | float,
        pro: str,
        pro_c: str | int,
        pro_mass: str | float,
    ):
        self.mid: str = mid
        self.masses: list[MassLane] = masses
        self.pre_c: int = int(pre_c)
        self.pre_mass: str = pre_mass  # the mass can be anything, just used for plot titles etc
        self.pro_c: int = int(pro_c)
        self.pro_mass: str = pro_mass  # same es pre_mass
        self.data: pd.DataFrame = pd.DataFrame(index=masses)

        # check if precursor and product are proper chemical sum formulas and if the product is a (possibly identical)
        # part of the precursor
        try:
            self.pre: ChemFormula = ChemFormula(pre)
        except DataError as err:
            raise DataError(f"precursor {pre} is not a proper chemical formula ({err.msg})")
        try:
            self.pro: ChemFormula = ChemFormula(pro)
        except DataError as err:
            raise DataError(f"product {self.pro} is not a proper chemical formula ({err.msg})")

        # ChemFormula implements comparison operators
        if not self.pro <= self.pre:
            raise DataError(f"product {self.pro} is not a part of the precursor {self.pre}")

        # collect the mass shifts of precursor and product
        pre_shifts = [i.pre_shift for i in self.masses]
        pro_shifts = [i.pro_shift for i in self.masses]

        # check if precursor shifts (ms) / precursor+product shifts (msms) are unique
        counts = Counter(self.masses)
        for elem in counts:
            if counts[elem] > 1:
                raise DataError(f"Mass shift {elem} occurs {counts[elem]} times")

        # check the precursor shifts if they are monotonic, start at 0, go up to at least pre_c and increase by at
        # most one
        if not pre_shifts[0] == 0:
            raise DataError(f"first precursor mass is not 0 ({pre_shifts[0]})")
        if max(pre_shifts) < self.pre_c:
            raise DataError(
                f"highest precursor mass {max(pre_shifts)} is lower than the highest possible one {self.pre_c}"
            )
        for prev, curr in zip(pre_shifts, pre_shifts[1:]):
            if curr < prev:
                raise DataError(f"precursor masses decrease {prev} -> {curr}")
            if curr > prev + 1:
                raise DataError(f"precursor masses increases by more than 1 {prev} -> {curr}")

        # if this is an MS measurement the mass shifts of precursor and product have to be identical (as precursor and
        # product are identical)
        if not self.is_msms():
            # single MS
            if not pre_shifts == pro_shifts:
                raise DataError("for (single) MS measurements precursor and product are not identical")
        else:
            # MSMS
            # we already know that pre_shifts are monotonic
            # check very first shift
            if not pro_shifts[0] == 0:
                raise DataError(f"first product mass shift is not 0 ({pro_shifts[0]})")
            for prev_shift, curr_shift in zip(self.masses, self.masses[1:]):
                # same precursor mass -> product muss must increase by exactly 1
                if prev_shift.pre_shift == curr_shift.pre_shift:
                    if curr_shift.pro_shift != prev_shift.pro_shift + 1:
                        raise DataError(
                            f"product mass shifts to not increase by exactly 1: {prev_shift} -> {curr_shift}"
                        )
                # otherwise pre shift increased by exactly 1
                else:
                    # we have a new precursor mass, so the latest product mass must be high enough
                    if prev_shift.pro_shift < min(prev_shift.pre_shift, self.pro_c):
                        raise DataError(
                            f"highest product mass shift ({prev_shift.pro_shift}) for precursor shift ({prev_shift.pre_shift}) is not high enough"
                        )
                    # furthermore the new product mass has to be as low as possible
                    if curr_shift.pro_shift != max(curr_shift.pre_shift - (self.pre_c - self.pro_c), 0):
                        raise DataError(
                            f"lowest product mass shift ({curr_shift.pro_shift}) for precursor shift ({curr_shift.pre_shift}) is not high enough"
                        )
            # check very last shift
            if pro_shifts[-1] < min(pre_shifts[-1], self.pro_c):
                raise DataError(f"last product mass shift ({pro_shifts[-1]}) is not high enough")

    def add_data(self, rep, times, data, masses):
        # TODO add information about the location of the faulty field
        assert data.shape[1] == len(times)
        if not masses == self.masses:
            raise DataError(
                f"could not insert new data for {self.mid} as masses disagree. New masses: {masses} -> old masses "
                f"{self.masses}"
            )
        for time_idx in range(len(times)):
            new_col = data[:, time_idx]
            time = times[time_idx]
            if any(new_col):
                # the column is not empty
                for val, mass in zip(new_col, masses):
                    if val is None:
                        raise DataError(
                            f"values for all mass traces at time {time} and mass {mass} have to be supplied"
                        )
                    if not is_number(val):
                        raise DataError(
                            f'measurement values have to be numbers. "{val}" at time {time} and mass {mass} is not'
                        )
                    if val < 0:
                        raise DataError(f'measured values have to be >=0. "{val}"  at time {time} and mass {mass}')
                self.data[RepTime(rep, time)] = new_col

    def is_msms(self):
        return not (self.pre == self.pro)

    def generate_possible_masses(self) -> list[MassLane]:
        """
        Only certain masses are theoretically possible. Nonetheless, other can be measured
        Returns: a list of all possible masses in cannonical order
        -------

        """
        possible: list[MassLane] = []
        if self.is_msms():
            for pre_shift in range(self.pre_c + 1):
                for pro_shift in range(max(0, pre_shift - (self.pre_c - self.pro_c)), min(self.pro_c, pre_shift) + 1):
                    possible.append(MassLane(pre_shift, pro_shift, self.is_msms()))
        else:
            for i in range(self.pre_c + 1):
                possible.append(MassLane(i, i, self.is_msms()))
        return possible

    def is_inst(self):
        times = set()
        for head in self.data:
            times.add(head.time)
            if len(times) > 1:
                return True
        return False

    def get_times(self):
        times = set()
        for head in self.data:
            times.add(head.time)
        times = [x for x in times]
        times.sort()
        return times

    def get_reps(self):
        reps = set()
        for head in self.data:
            reps.add(head.rep)
        reps = [x for x in reps]
        reps.sort()
        return reps

    def get_masses(self):
        return self.masses

    def normalize(self):
        for col in self.data:
            # if all values 0, normalizing does not make any sense
            if np.any(self.data[col] != 0):
                dsum = self.data[col].sum(axis=0)
                self.data[col] /= dsum

    def build_fluxml_name(self):
        prefix = self.mid + "#M"
        if self.is_msms():
            m_part = (
                "("
                + "),(".join([str(x.pre_shift) + "," + str(x.pro_shift) for x in self.generate_possible_masses()])
                + ")"
            )
        else:
            m_part = ",".join([str(x.pre_shift) for x in self.generate_possible_masses()])
        return prefix + m_part

    def build_plot_title(self):
        title = f"{self.mid}"
        if self.is_msms():
            if not math.isnan(self.pre_mass) and not math.isnan(self.pro_mass):
                title = f"{title} {self.pre_mass} -> {self.pro_mass}"
        else:
            if not math.isnan(self.pre_mass):
                title = f"{title} {self.pre_mass}"

        return title

    def calc_means_and_stddevs(self):
        self.normalize()  # this is an unexpected side effect ...
        # sort for time-points
        timed_data = {}
        for col in self.data:
            if col.time not in timed_data:
                timed_data[col.time] = pd.DataFrame(index=self.data.index)
            timed_data[col.time][col.rep] = self.data[col]

        means = pd.DataFrame(index=self.data.index)
        stddevs = pd.DataFrame(index=self.data.index)
        # calculate mean and stddev for each time-point
        for time in sorted(timed_data.keys(), key=float):
            means[float(time)] = timed_data[time].mean(axis=1)
            stddevs[float(time)] = timed_data[time].std(axis=1, ddof=0).clip(lower=Measurement.default_stddev)

        return means, stddevs

    def calc_means_and_stddevs_no_neg(self):
        means, stddevs = self.calc_means_and_stddevs()
        non_neg_means = means.clip(lower=0)
        return non_neg_means, stddevs

    def get_slug(self):
        if self.is_msms():
            return slugify(f"{self.mid}_{self.pre}_{self.pro}")
        else:
            return slugify(f"{self.mid}_{self.pre}")
