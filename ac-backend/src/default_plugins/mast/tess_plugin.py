from src.default_plugins.mast.mast_plugin import MastPlugin


class TessPlugin(MastPlugin):
    def __init__(self) -> None:
        super().__init__()
        self._directly_identifies_objects = True
        self._description = "The Transiting Exoplanet Survey Satellite (TESS) is an all-sky transit survey, whose principal goal is to detect Earth-sized planets orbiting bright stars that are amenable to follow-up observations to determine planet masses and atmospheric compositions. TESS will conduct high-precision photometry of more than 200,000 stars during a two-year mission with a cadence of approximately 2 minutes."
        self._catalog_url = "https://archive.stsci.edu/missions-and-data/tess"

    def _get_mission(self) -> str:
        return "TESS"

    def _get_target(self) -> str:
        # TIC = TESS Input Catalog
        return "TIC"
