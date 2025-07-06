from src.core.integration.schemas import StellarObjectIdentificatorDto


class DaschStellarObjectIdentificatorDto(StellarObjectIdentificatorDto):
    gsc_bin_index: int
    ref_number: int
