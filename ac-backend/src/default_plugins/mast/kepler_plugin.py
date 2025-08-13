from src.default_plugins.mast.mast_plugin import MastPlugin


class KeplerPlugin(MastPlugin):
    def __init__(self) -> None:
        super().__init__()

    def _get_mission(self) -> str:
        return "Kepler"

    def _get_target(self) -> str:
        return "KIC"
