import tomllib
from decimal import Decimal

import numpy as np


class Config:
    NATAB_KEY = "natural_abundance"
    TOL_KEY = "tolerance"
    TOL_DIFF_KEY = "diff"
    TOL_NEG_KEY = "negative"
    DEFAULT_NAT = {
        "C": [0.9893, 0.0107],
        "H": [0.999885, 0.000115],
        "N": [0.99636, 0.00364],
        "O": [0.99757, 0.00038, 0.00205],
        "P": [1],
        "S": [0.9499, 0.0075, 0.0425, 0, 0.0001],
        "Si": [0.92223, 0.04685, 0.03092],
    }
    DEFAULT_MASS = {
        "C": [Decimal("12.0"), Decimal("13.003354835")],
        "H": [Decimal("1.0078250322"), Decimal("2.0141017781")],
        "N": [Decimal("14.003074004"), Decimal("15.000108899")],
        "O": [Decimal("15.99491462"), Decimal("16.999131757"), Decimal("17.999159613")],
        "P": [Decimal("30.973761998")],
        "S": [
            Decimal("31.972071174"),
            Decimal("32.971458910"),
            Decimal("33.9678670"),
            Decimal("35.0"),
            Decimal("35.967081"),
        ],
        "Si": [Decimal("27.976926535"), Decimal("28.976494665"), Decimal("29.9737701")],
    }

    DEFAULT_EPS_DIFF = 0.001
    DEFAULT_EPS_NEG = 0.001
    __conf = {
        NATAB_KEY: DEFAULT_NAT,
        TOL_KEY: {
            TOL_DIFF_KEY: DEFAULT_EPS_DIFF,
            TOL_NEG_KEY: DEFAULT_EPS_NEG,
        },
    }

    @staticmethod
    def get_natab():
        return Config.__conf[Config.NATAB_KEY]

    @staticmethod
    def get_natab_isocor():
        na = Config.get_natab()
        out_na = {}
        for atom in na:
            out_na[atom] = {"abundance": na[atom], "mass": Config.DEFAULT_MASS[atom]}
        return out_na

    @staticmethod
    def get_diff_tol():
        return Config.__conf[Config.TOL_KEY][Config.TOL_DIFF_KEY]

    @staticmethod
    def get_neg_tol():
        return Config.__conf[Config.TOL_KEY][Config.TOL_NEG_KEY]

    @staticmethod
    def parse_config(fn):
        with open(fn, "rb") as f:
            data = tomllib.load(f)
        for key in data:
            if key not in Config.__conf:
                raise NameError(f'"{key}" is not a valid config entry. Valid entries are {Config.__conf.keys()}')
            else:
                Config.__conf[key] = data[key]
        Config.__verify_config()

    @staticmethod
    def __verify_config():
        if Config.get_neg_tol() < 0 or Config.get_neg_tol() > 1:
            raise ValueError(
                f"tolerance for negative values has to be betwenn 0 and 1. The supplied values is {Config.get_neg_tol()}"
            )
        if Config.get_diff_tol() < 0 or Config.get_diff_tol() > 1:
            raise ValueError(
                f"tolerance for differences in values has to be betwenn 0 and 1. The supplied values is {Config.get_diff_tol()}"
            )
        nat = Config.get_natab()
        atoms = {"C", "H", "N", "O", "P", "S", "Si"}
        provided = set(nat.keys())
        not_provided = atoms.difference(provided)
        if not_provided:
            raise ValueError(f"Natural abundance for the following atoms is missing {not_provided}")
        for atom in nat:
            if np.any(np.array(nat[atom]) > 1) or np.any(np.array(nat[atom]) < 0):
                raise ValueError(
                    f"Natural abundance values for {atom} are not within the range of 0..1. The provided values are {nat[atom]}"
                )
            total_ab = np.sum(nat[atom])
            if np.abs(total_ab - 1) > 1e-14:
                raise ValueError(
                    f"Natural abundance for {atom} does not sum up to 1. The provided values are {nat[atom]}, which sums to {total_ab}"
                )
