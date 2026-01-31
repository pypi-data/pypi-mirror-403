import numpy as np

import unac.util.data as d
from unac.correction.interface import CorrectionInterface
from unac.util.config import Config


class NaiveCorrection(CorrectionInterface):
    def __init__(self):
        super().__init__("naive correction")

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def requirements(cls) -> list[str]:
        return []

    @staticmethod
    def compute_elem_matrix(natabs, num):
        mat = np.zeros((num + 1, num + 1))
        for col in range(num + 1):
            for shift in range(len(natabs)):
                if col + shift < num + 1:
                    mat[col + shift, col] = natabs[shift]
        return mat

    @staticmethod
    def compute_corr_matrix(c=0, h=0, n=0, o=0, p=0, s=0, si=0, num=0):
        nat = Config.get_natab()
        c_mat = NaiveCorrection.compute_elem_matrix(nat["C"], num)
        h_mat = NaiveCorrection.compute_elem_matrix(nat["H"], num)
        n_mat = NaiveCorrection.compute_elem_matrix(nat["N"], num)
        o_mat = NaiveCorrection.compute_elem_matrix(nat["O"], num)
        p_mat = NaiveCorrection.compute_elem_matrix(nat["P"], num)
        s_mat = NaiveCorrection.compute_elem_matrix(nat["S"], num)
        si_mat = NaiveCorrection.compute_elem_matrix(nat["Si"], num)
        return (
            np.linalg.matrix_power(c_mat, c)
            @ np.linalg.matrix_power(h_mat, h)
            @ np.linalg.matrix_power(n_mat, n)
            @ np.linalg.matrix_power(o_mat, o)
            @ np.linalg.matrix_power(p_mat, p)
            @ np.linalg.matrix_power(s_mat, s)
            @ np.linalg.matrix_power(si_mat, si)
        )

    def perform_correction(self, data, path):
        """

        :param data: a dict of d.Measurement with the uncorrected data
        :param path: prefix_path for the filenames
        :return: a dict of d.Measurement with the corrected data
        """

        # delete all MSMS data
        remove = [k for k in data if data[k].is_msms()]
        for k in remove:
            del data[k]

        for met in data:
            measurement: d.Measurement
            measurement = data[met]
            elems = measurement.pre.elems
            for elem in ["C", "H", "N", "O", "P", "S", "Si"]:
                if elem not in elems:
                    elems[elem] = 0
            max_trace = max(measurement.pre_c, measurement.data.shape[0] - 1)
            corr_matrix = np.linalg.inv(
                NaiveCorrection.compute_corr_matrix(
                    c=elems["C"] - measurement.pre_c,
                    h=elems["H"],
                    n=elems["N"],
                    o=elems["O"],
                    p=elems["P"],
                    s=elems["S"],
                    si=elems["Si"],
                    num=max_trace,
                )
            )
            cdata = corr_matrix.dot(measurement.data.to_numpy())
            measurement.data.loc[:, :] = cdata
            measurement.normalize()

        return True
