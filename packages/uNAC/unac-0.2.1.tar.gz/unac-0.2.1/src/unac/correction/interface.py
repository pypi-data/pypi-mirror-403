import copy
from abc import ABC, abstractmethod
from timeit import default_timer as timer


class CorrectionInterface(ABC):
    name: str

    def __init__(self, name):
        self.name = name

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Return True if this backend can be used in the current environment."""

    @classmethod
    @abstractmethod
    def requirements(cls) -> list[str]:
        """Human-readable requirements (for error messages)."""

    def perform_correction_ui(self, data, path="", silent=False):
        """
        This method performs the correction on data and returns the corrected data
        Call this method from a user interface. Do not override this method
        :param data: a dict of d.Measurement with the uncorrected data
        :param path: path to store potential files
        :param silent: wether to print output or not
        :return: the corrected data as a dict of d.Measurement
        """
        if not silent:
            print(f"\trunning {self.name}")
        cor_data = copy.deepcopy(data)
        start = timer()
        success = self.perform_correction(cor_data, path)
        end = timer()
        if not silent:
            if success:
                print(f"\t\tcorrected {len(cor_data):3} measurements in {end - start:7.2f}s")
            else:
                print("\t\tfailed")
        return cor_data

    @abstractmethod
    def perform_correction(self, data, path):
        """
        This method performs the correction on data
        It must be implemented in any correction algorithm
        :param data: a dict of d.Measurement with a copy the uncorrected data. After execution, it should contain the
        corrected data
        :param path: path to store potential files
        :return: success status
        """
        raise NotImplementedError()
