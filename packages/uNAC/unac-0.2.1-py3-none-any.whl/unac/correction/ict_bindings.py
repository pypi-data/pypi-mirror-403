import copy
import csv
import hashlib
import os
import shutil
import subprocess
from importlib.resources import files

import numpy as np

import unac.util.data as d
from unac.correction.interface import CorrectionInterface
from unac.util.config import Config


class IctCorrection(CorrectionInterface):
    # ict file names
    CHEM_FILE_PREFIX = "chem_data"
    RAW_FILE_PREFIX = "raw_data"
    COR_FILE_PREFIX = "cor_data"
    NATAB_FILE_PREFIX = "natab"
    ICT_FILE_PREFIX = "ict_output"
    TRANSLATION_PREFIX = "trans"

    ict_dir = files("unac").joinpath("external").joinpath("ICT")

    ICT_EXEC = ict_dir / "ict.pl"

    class IctChemComposition:
        """
        Class to help with the creation of ICTs Chem Composition files

        Attributes
        ----------
        name : str
            The name of the metabolite. This name is not understood in any way or matched against known metabolites
        cs_pre : int
            The number of carbons in the precursor / mother ion
        sum_pre : data.ChemFormula
            The molecular formula of the precursor / mother ion
        cs_pro : int
            The number of carbons in the product / daughter ion
        sum_pro : data.ChemFormula
            The molecular formula for the product / daughter ion
        """

        def __init__(self, name, cs_pre, sum_pre, cs_pro, sum_pro):
            self.name = name
            self.cs_pre = int(cs_pre)
            self.sum_pre = sum_pre
            self.cs_pro = int(cs_pro)
            self.sum_pro = sum_pro

        def create_ict_string(self):
            """return the string that is needed in the ICT Chemical composition file"""
            (sum_pre_string, sum_pro_string) = self.__sum_formula_string()

            line1 = f"{self.name}: Precursor: 13C{self.cs_pre}, {sum_pre_string}"
            line2 = f"{self.name}: Product Ion: 13C{self.cs_pro}, {sum_pro_string}"
            return line1 + "\n" + line2 + "\n"

        def __sum_formula_string(self):
            pre_dict = copy.deepcopy(self.sum_pre.elems)
            pro_dict = copy.deepcopy(self.sum_pro.elems)

            # subtract backbone carbons!
            pre_dict["C"] = pre_dict["C"] - self.cs_pre
            pro_dict["C"] = pro_dict["C"] - self.cs_pro

            # some precursor atoms might be lost, but are required by ICT
            for elem_name in pre_dict.keys():
                if elem_name not in pro_dict.keys():
                    pro_dict[elem_name] = 0

            sum_pre_string = self.__create_element_string(pre_dict)
            sum_pro_string = self.__create_element_string(pro_dict)

            return sum_pre_string, sum_pro_string

        @staticmethod
        def __create_element_string(element_dict):
            element_strings = []
            for element in element_dict:
                element_strings.append(f"{element}{element_dict[element]}")
            element_string = ", ".join(element_strings)
            return element_string

    def __init__(self):
        super().__init__("ICT")

    @staticmethod
    def create_natural_abundance_file():
        base_mass = {"C": 12, "H": 1, "N": 14, "O": 16, "P": 31, "S": 32, "Si": 28}
        out = ""
        nat = Config.get_natab()
        for atom in nat:
            part1 = []
            for shift in range(len(nat[atom])):
                part1.append(f"{atom}{base_mass[atom] + shift}")
            out += " ".join(part1) + ": " + " ".join(f"{x}" for x in nat[atom]) + "\n"
        return out

    @staticmethod
    def make_ict_filename(prefix, infix):
        """
        create a filename in a way that ict likes them

        the filename will start with prefix and end with .txt. In between there will be a hashed version of infix to
        avoid any trouble with the filesystem and special characters

        :param prefix: a prefix that tells the ict user what kind of file it is (e.g. chem_data or raw_data)
        :param infix: a user supplied identifier string
        :return: the complete filename
        """
        hash_name = hashlib.md5(infix.encode()).hexdigest()
        return prefix + "_" + hash_name + ".txt"

    @staticmethod
    def parse_corrected_data(cor_data, slug_to_met, corr_file_name):
        cur_mid = ""
        data = np.array
        first = True

        # check if we can recover all mids from the corrected data
        mids = set(cor_data.keys())

        with open(corr_file_name, newline="") as cor_file:
            cor_reader = csv.reader(cor_file, delimiter=",")
            for row in cor_reader:
                if len(row) > 1:
                    m_id = slug_to_met[row[0].split("_")[0]]
                    if m_id != cur_mid:
                        if not first:
                            # new mid -> data for old mid complete, write it to the data structure
                            IctCorrection.update_with_cor_data(cor_data, cur_mid, data)
                            mids.remove(cur_mid)
                        else:
                            first = False

                        # start new data
                        cur_mid = m_id
                        data = [[float(i) for i in row[1:]]]

                    else:
                        # append data
                        data = np.append(data, np.array([[float(i) for i in row[1:]]]), axis=0)
            # write final metabolite
            IctCorrection.update_with_cor_data(cor_data, cur_mid, data)
            mids.remove(cur_mid)
            if mids:
                print(f"The following measurements where not found in the corrected data: {mids}")
                # remove entries from corr_data, for which no corrected data was recovered (otherwise it would contain
                # the uncorrected data)
                for mid in mids:
                    cor_data.pop(mid)

    @staticmethod
    def update_with_cor_data(cor_data, cur_mid, data):
        # new mid, normalize collected ones and write to file
        if cur_mid not in cor_data:
            print(f"{cur_mid} not present in data")
        measurement: d.Meaasurement = cor_data[cur_mid]
        # zero out everything (including possible higher mass traces)
        measurement.data.loc[:, :] = 0
        measurement.data.loc[measurement.generate_possible_masses(), :] = data
        measurement.normalize()

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("perl") is not None

    @classmethod
    def requirements(cls) -> list[str]:
        return ["Perl >= 5.10"]

    def perform_correction(self, data, path):
        """

        :param data: a dict of d.Measurement with the uncorrected data
        :param path: prefix_path for the filenames
        :return: success status
        """
        out_path = path + "/ICT/"
        os.makedirs(out_path, exist_ok=True)

        # Build the files (chem data and raw)
        chem_data = ""
        raw_data = ""
        # help putting the corrected data back
        slug_to_met = {}
        for met in data:
            uncor_data: d.Measurement = data[met]
            slug = uncor_data.get_slug()
            slug_to_met[slug] = met
            ict_chem = IctCorrection.IctChemComposition(
                slug,
                uncor_data.pre_c,
                uncor_data.pre,
                uncor_data.pro_c,
                uncor_data.pro,
            )
            chem_data = f"{chem_data}{ict_chem.create_ict_string()}\n"

            for index in uncor_data.generate_possible_masses():
                row = uncor_data.data.loc[index].values

                raw_data_row_pre = f"{slug}_M{index.pre_shift}"
                if uncor_data.is_msms():
                    raw_data_row_pre += f".{index.pro_shift}"

                raw_data_row_data = ", ".join([str(x) for x in row])
                raw_data = f"{raw_data}{raw_data_row_pre}, {raw_data_row_data}\n"

        chem_file_name = out_path + "/chem_data.txt"
        raw_file_name = out_path + "/raw_data.txt"
        corr_file_name = out_path + "/corr_data.txt"
        natab_file_name = out_path + "/nat_ab.txt"
        out_file_name = out_path + "/ict_out.txt"

        # write files to disk
        with open(chem_file_name, "w+") as chem_file:
            chem_file.write(chem_data)

        with open(raw_file_name, "w+") as raw_file:
            raw_file.write(raw_data)

        with open(natab_file_name, "w+") as natab_file:
            natab_file.write(IctCorrection.create_natural_abundance_file())

        # execute ICT
        run_cmd = [
            IctCorrection.ICT_EXEC,
            "-c " + chem_file_name,
            "-m " + raw_file_name,
            "-o " + corr_file_name,
            "-i " + natab_file_name,
        ]
        proc_stat = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # save stdout to ict_file
        with open(out_file_name, "w+") as out_file:
            out_file.write(proc_stat.stdout.decode())

        # evaluate return code
        # TODO print the messages elsewhere, or ignore them all together
        if proc_stat.returncode:
            print(
                f"\t\tICT failed (return code: {proc_stat.returncode})\n\n"
                f"========================== Begin Error Message ==========================\n\n"
                f"{proc_stat.stderr.decode()}\n"
                f"=========================== End Error Message ===========================\n\n"
                f"\t\tCheck the ICT output file located at {out_file_name}"
            )
            return False

        IctCorrection.parse_corrected_data(data, slug_to_met, corr_file_name)
        return True
