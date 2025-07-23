from src.mast.mast_plugin import MastPlugin


class TessPlugin(MastPlugin):
    def __init__(self) -> None:
        super().__init__()

    def _get_target(self) -> str:
        # TIC = TESS Input Catalog
        return "TIC"
