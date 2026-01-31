from importlib.util import find_spec

import unac.util.data as d
from unac.correction.interface import CorrectionInterface
from unac.util.config import Config


class IsocorCorrection(CorrectionInterface):
    def __init__(self):
        super().__init__("isocor")

    @classmethod
    def is_available(cls) -> bool:
        if find_spec("isocor"):
            return True
        else:
            return False

    @classmethod
    def requirements(cls) -> list[str]:
        return ["pip install unac[isocor]"]

    def perform_correction(self, data, path):
        """

        :param data: a dict of d.Measurement with the uncorrected data
        :param path: prefix_path for the filenames
        :return: success status
        """

        import isocor

        # delete all MSMS data
        remove = [k for k in data if data[k].is_msms()]
        for k in remove:
            del data[k]

        for met in data:
            # we cheat a bit here, as we do not know if, and what the derivative is. Therefore, we treat everything that
            # is not the backbone as the derivative
            measurement: d.Measurement = data[met]
            formula = f"C{data[met].pre_c}"
            derivative_formula = str(measurement.pre - d.ChemFormula(formula))
            # the actual correction / call to isocor
            corrector = isocor.mscorrectors.MetaboliteCorrectorFactory(
                formula=formula,
                derivative_formula=derivative_formula,
                tracer="13C",
                data_isotopes=Config.get_natab_isocor(),
            )

            # make a slice with only the relevant mass traces and zero out the higher ones
            possible_masses = measurement.generate_possible_masses()
            measurement.data.loc[measurement.data.index.difference(possible_masses, sort=False), :] = 0
            for col_id in measurement.data:
                cor_met_data = corrector.correct(measurement.data.loc[possible_masses, col_id].to_list())
                measurement.data.loc[possible_masses, col_id] = cor_met_data[1]

        return True
