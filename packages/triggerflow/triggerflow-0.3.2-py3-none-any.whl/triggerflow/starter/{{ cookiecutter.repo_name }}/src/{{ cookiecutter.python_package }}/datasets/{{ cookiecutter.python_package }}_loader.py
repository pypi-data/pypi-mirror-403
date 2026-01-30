import pandas as pd
import awkward as ak
from .base_loader import BaseLoader


class {{ cookiecutter.python_package }}Loader(BaseLoader):
    """
    A custom loader example.
    """

    def transform(self, events):

        jets = events.Jet
        pt  = ak.fill_none(ak.pad_none(jets.pt , 2, axis=1, clip=True), -9999.9)
        eta = ak.fill_none(ak.pad_none(jets.eta, 2, axis=1, clip=True), -9999.9)
        phi = ak.fill_none(ak.pad_none(jets.phi, 2, axis=1, clip=True), -9999.9)

        met = events.MET

        result = ak.zip({
            "event": events.event,
            "jet_pt_1":  pt[:, 0],
            "jet_pt_2":  pt[:, 1],
            "jet_eta_1": eta[:, 0],
            "jet_eta_2": eta[:, 1],
            "jet_phi_1": phi[:, 0],
            "jet_phi_2": phi[:, 1],
            "met_pt":    met.pt,
            "met_phi":   met.phi,
        })

        return result
