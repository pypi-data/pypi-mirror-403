from unac.correction.ict_bindings import IctCorrection
from unac.correction.isocor_bindings import IsocorCorrection
from unac.correction.isocorrector_bindings import IsoCorrectoRCorrection
from unac.correction.naive import NaiveCorrection

ALL_BACKENDS = [
    NaiveCorrection(),
    IsocorCorrection(),
    IctCorrection(),
    IsoCorrectoRCorrection(),
]


def available_backends():
    return [b for b in ALL_BACKENDS if b.is_available()]


def backend_by_name(backend_name: str):
    for backend in ALL_BACKENDS:
        if backend.name == backend_name:
            return backend
    raise KeyError(f"Unknown backend: {backend_name}")
