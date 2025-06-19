import csv
from typing import List

import requests

from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import PhotometricDataModel
from src.dasch.dasch_identificator_model import DaschIdentificatorModel

REFCAT_APASS = "apass"

# TODO: fixme:
#  should use async requests to not block!
class DaschPlugin(PhotometricCataloguePlugin):
    # https://dasch.cfa.harvard.edu/dr7/web-apis/
    def __init__(self):
        self.base_url = "https://api.starglass.cfa.harvard.edu/public"
        self.querycat_endpoint = f"{self.base_url}/dasch/dr7/querycat"
        self.lightcurve_endpoint = f"{self.base_url}/dasch/dr7/lightcurve"

    def list_objects(self, ra_deg, dec_deg, radius_arcsec) -> List[DaschIdentificatorModel]:
        query_body = {
            "dec_deg": dec_deg,
            "ra_deg": ra_deg,
            "radius_arcsec": radius_arcsec,
            "refcat": REFCAT_APASS
        }
        query_resp = requests.post(self.querycat_endpoint, json=query_body)
        query_data = query_resp.json()

        reader = csv.reader(query_data)
        header = next(reader)

        object_ra_deg = header.index("ra_deg")
        object_dec_deg = header.index("dec_deg")
        gsc_bin_index_idx = header.index("gsc_bin_index")
        ref_number_idx = header.index("ref_number")

        result = []
        for row in reader:
            identificator_ra_deg = row[object_ra_deg]
            identificator_dec_deg = row[object_dec_deg]
            identificator_gsc_bin_index = row[gsc_bin_index_idx]
            identificator_ref_number = row[ref_number_idx]
            if (identificator_ra_deg == '' or identificator_dec_deg == ''
                    or identificator_gsc_bin_index == '' or identificator_ref_number == ''):
                continue

            result.append(DaschIdentificatorModel(
                gsc_bin_index=int(identificator_gsc_bin_index),
                ref_number=int(identificator_ref_number),
                ra_deg=float(identificator_ra_deg),
                dec_deg=float(identificator_dec_deg)
            ))

        return result


        #sess = daschlab.open_session()
        #sess.select_target(ra_deg, dec_deg).select_refcat("apass")
        #curve = sess.lightcurve()
        #closest_object

    def get_photometric_data(self, identificator: DaschIdentificatorModel) -> List[PhotometricDataModel]:
        lc_body = {
            "gsc_bin_index": identificator.gsc_bin_index,
            "ref_number": identificator.ref_number,
            "refcat": REFCAT_APASS
        }
        lc_resp = requests.post(self.lightcurve_endpoint, json=lc_body)
        lc_data = lc_resp.json()

        reader = csv.reader(lc_data)
        header = next(reader)
        jd_idx = header.index("date_jd")
        mag_idx = header.index("magcal_magdep")
        err_idx = header.index("magcal_magdep_rms")

        result = []
        for row in reader:
            jd_str = row[jd_idx]
            mag_str = row[mag_idx]
            err_str = row[err_idx]
            if jd_str == '' or mag_str == '' or err_str == '':
                continue

            jd = float(row[jd_idx])
            mag = float(row[mag_idx])
            err = float(row[err_idx])

            result.append(PhotometricDataModel(julian_date=jd, magnitude=mag, error=err))

        return result