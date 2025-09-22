from src.default_plugins.mast.mast_plugin import MastPlugin


class KeplerPlugin(MastPlugin):
    def __init__(self) -> None:
        super().__init__()
        self._description = "The Kepler spacecraft was launched into an earth trailing orbit and stared at a 100 sq. degree patch of sky near Cygnus in order to measure the brightness variations of about 200,000 stars.  Its primary mission was to find exoplanets transiting these stars and to determine the prevalence of exoplanets in the Galaxy.  The Kepler spacecraft rotated by 90 degrees every 90 days in order to keep the solar panels pointing at the sun and thus the Kepler data is divided into 90-day quarters. Kepler only downloaded the pixels surrounding selected stars of interest at either a 30-minute or 1-minute cadence. The mission produced a flux time series for each star and searched these light curves for the presence of a transiting exoplanet."
        self._catalog_url = "https://archive.stsci.edu/missions-and-data/kepler"

    def _get_mission(self) -> str:
        return "Kepler"

    def _get_target(self) -> str:
        return "KIC"
