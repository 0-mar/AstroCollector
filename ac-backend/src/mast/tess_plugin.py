from src.mast.mast_plugin import MastPlugin


class TessPlugin(MastPlugin):
    def __init__(self) -> None:
        super().__init__()

    def _get_target(self, id: int) -> str:
        # TIC = TESS Input Catalog
        return f"TIC {id}"
