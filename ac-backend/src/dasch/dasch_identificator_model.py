from src.core.integration.schemas import IdentificatorModel


class DaschIdentificatorModel(IdentificatorModel):
    gsc_bin_index: int
    ref_number: int