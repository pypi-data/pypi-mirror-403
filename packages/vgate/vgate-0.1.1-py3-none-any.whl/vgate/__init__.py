# Use relative import to get the module from the same package
from hio.base import doing
from keri.app import habbing, notifying
from keri.vdr import viring

from .communicator import Communicator
from .cue_baser import CueBaser
from .presentation_proof_handler import PresentationProofHandler

__all__ = ['setup']


def setup(hby: habbing.Habery, alias: str) -> [doing.Doer]:
    """
    Load and return the doers for the Vgate module.
    This function is used to initialize the Vgate module's doers.
    """
    hab = hby.habByName(name=alias)
    notifier = notifying.Notifier(hby=hby)
    cue_baser = CueBaser(name=hby.name)
    reger = viring.Reger(name=hab.name, db=hab.db, temp=False)
    communicator = Communicator(hby=hby, hab=hab, cdb=cue_baser, reger=reger, auth=None, hook=None, timeout=10, retry=3)
    presentation_proof_handler = PresentationProofHandler(cdb=cue_baser, hby=hby, notifier=notifier, parser=hab.psr)

    return [communicator, presentation_proof_handler]
