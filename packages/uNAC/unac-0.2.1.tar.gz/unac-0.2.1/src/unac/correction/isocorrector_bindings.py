import os
import shutil
from importlib.util import find_spec

import unac.util.data as d
from unac.correction.interface import CorrectionInterface
from unac.util.config import Config


class IsoCorrectoRCorrection(CorrectionInterface):
    def __init__(self):
        super().__init__("IsoCorrectoR")

    @staticmethod
    def create_measurement_file_content(data):
        max_cols = 0
        mfile_content = ""
        for met in data:
            uncor_data: d.Measurement = data[met]
            slug = uncor_data.get_slug()
            for row_idx in range(min(uncor_data.pre_c + 1, uncor_data.data.shape[0])):
                pass
            for index in uncor_data.generate_possible_masses():
                vals = uncor_data.data.loc[index].values
                max_cols = max(max_cols, len(vals))
                mfile_row_data = ", ".join([str(x) for x in vals])
                mfile_label = f"{slug}_{index.pre_shift}"
                if index.msms:
                    mfile_label += f".{index.pro_shift}"
                mfile_content = mfile_content + "\n" + mfile_label + ", " + mfile_row_data
        mfile_content = mfile_content + "\n"
        mfile_content = "Measurements/Samples, " + ", ".join([f"Sample{i}" for i in range(max_cols)]) + mfile_content
        return mfile_content

    @staticmethod
    def set_corrected_data(out_data, isocorrector_data):
        slug_to_met = {}
        for met in out_data:
            datum: d.Measurement = out_data[met]
            slug_to_met[datum.get_slug()] = met

        for slug in slug_to_met:
            met = slug_to_met[slug]
            datum: d.Measurement = out_data[met]
            num_rep_times = datum.data.shape[1]
            possible_masses = datum.generate_possible_masses()
            for index in datum.get_masses():
                if index in possible_masses:
                    mfile_label = f"{slug}_{index.pre_shift}"
                    if index.msms:
                        mfile_label += f".{index.pro_shift}"
                    # for a specific measurement, possibly not all rep_times are there
                    # so we just set the present ones
                    datum.data.loc[index, :] = isocorrector_data.loc[
                        mfile_label, isocorrector_data.columns[:num_rep_times]
                    ].values
                else:
                    datum.data.loc[index, :] = 0

    @staticmethod
    def create_molecule_file_content(data):
        text = "Molecule, MS ion or MS/MS product ion, MS/MS neutral loss\n"
        for met in data:
            datum: d.Measurement = data[met]
            line = f"{datum.get_slug()}, "
            if datum.is_msms():
                line += f"{datum.pro}"
                if datum.pro_c > 0:
                    line += f"LabC{datum.pro_c}"
                loss = datum.pre - datum.pro
                loss_c = datum.pre_c - datum.pro_c
                line += f", {loss}"
                if loss_c > 0:
                    line += f"LabC{loss_c}"
            else:
                line += f"{datum.pre}"
                if datum.pre_c > 0:
                    line += f"LabC{datum.pre_c}"
                line += ", "
            line += "\n"
            text += line
        return text

    @staticmethod
    def create_element_file_content():
        text = "Element, Isotope abundance_Mass shift, Tracer isotope mass shift, Tracer purity\n"
        nat_ab = Config.get_natab()
        for elem in nat_ab:
            line = f"{elem}, "
            line += "/".join([f"{nat_ab[elem][i]}_{i}" for i in range(len(nat_ab[elem])) if nat_ab[elem][i] > 0])
            line += ", "
            if len(nat_ab[elem]) - 1 > 0:
                line += f"{len(nat_ab[elem])-1}"
            line += ", 1\n"
            text += line
        return text

    @classmethod
    def is_available(cls) -> bool:
        if shutil.which("R") is None:
            return False
        if find_spec("rpy2"):
            return cls._r_packages_installed()
        else:
            return False

    @classmethod
    def _r_packages_installed(cls) -> bool:
        import rpy2.robjects.packages as rpackages

        if not rpackages.isinstalled("BiocManager"):
            return False
        if not rpackages.isinstalled("IsoCorrectoR"):
            return False
        return True

    @classmethod
    def requirements(cls) -> list[str]:
        return [
            "R >= 4.0",
            "pip install unac[isocorrector]",
            "uNAC-setup (R packages)",
        ]

    def perform_correction(self, data, path):
        import rpy2.rinterface_lib as rinterface_lib
        import rpy2.robjects as robjects
        import rpy2.robjects.conversion as rconversion
        import rpy2.robjects.packages as rpackages
        from rpy2.robjects import pandas2ri

        out_path = path + "/isocorrector/"
        os.makedirs(out_path, exist_ok=True)
        measurement_file_name = f"{out_path}/MeasurementFile.csv"
        molecule_file_name = f"{out_path}/MoleculeFile.csv"
        element_file_name = f"{out_path}/ElementFile.csv"

        with open(measurement_file_name, "w+") as meas_file:
            meas_file.write(IsoCorrectoRCorrection.create_measurement_file_content(data))

        with open(molecule_file_name, "w+") as mol_file:
            mol_file.write(IsoCorrectoRCorrection.create_molecule_file_content(data))

        with open(element_file_name, "w+") as element_file:
            element_file.write(IsoCorrectoRCorrection.create_element_file_content())

        IsoCorrectoRCorrection.create_element_file_content()

        rpackages.importr("utils")
        isocorrector = rpackages.importr("IsoCorrectoR")

        # suppresses R output
        def f(x):
            pass

        rinterface_lib.callbacks.consolewrite_print = f
        rinterface_lib.callbacks.consolewrite_warnerror = f
        res = isocorrector.IsoCorrection(
            MeasurementFile=measurement_file_name,
            MoleculeFile=molecule_file_name,
            ElementFile=element_file_name,
            CorrectTracerElementCore=False,
            DirOut=out_path,
            FileOut="result",
            FileOutFormat="csv",
            ReturnResultsObject=True,
        )
        if res[0][0] == "FALSE":
            return False
        else:
            corrected_fractions = res[1][2]
            with (robjects.default_converter + pandas2ri.converter).context():
                df = rconversion.get_conversion().rpy2py(corrected_fractions)
            IsoCorrectoRCorrection.set_corrected_data(data, df)

        return True
