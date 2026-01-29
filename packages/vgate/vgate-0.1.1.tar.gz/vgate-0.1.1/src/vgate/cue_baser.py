# -*- encoding: utf-8 -*-
"""
VGATE
vgate module

Database support
"""

from keri import help
from keri.core import coring, serdering
from keri.db import dbing, subing

logger = help.ogler.getLogger()


class CueBaser(dbing.LMDBer):
    """
    CueBaser class for managing databases related to credential issuance and revocation.
    This class extends LMDBer to provide specific functionality for handling credential issuance and revocation.
    It manages several sub-databases for senders, issuances, revocations, received credentials, revoked credentials,
    and acknowledgments.
    It provides methods to reopen the database, clear escrows, and get counts of items in each sub-database.
    Attributes:
        name (str): Name of the database.
        headDirPath (str): Path to the head directory.
        reopen (bool): Whether to reopen the database.
    """

    TailDirPath = 'vgate/db'
    AltTailDirPath = '.vgate/db'
    TempPrefix = 'vgate_db_'

    def __init__(self, name='cb', head_dir_path=None, reopen=True, **kwa):
        """

        Parameters:
            head_dir_path:
            perm:
            reopen:
            kwa:
        """
        self.snd = None

        self.iss = None
        self.rev = None

        self.recv = None
        self.revk = None

        self.ack = None

        super(CueBaser, self).__init__(name=name, headDirPath=head_dir_path, reopen=reopen, **kwa)

    def reopen(self, **kwa):
        """

        :param kwa:
        :return:
        """
        super(CueBaser, self).reopen(**kwa)

        # Database of senders of the presentation or revocation messages
        self.snd = subing.CesrSuber(db=self, subkey='snd.', klas=coring.Prefixer)

        # presentations that are waiting for the credential to be received and parsed
        self.iss = subing.CesrSuber(db=self, subkey='iss.', klas=coring.Dater)
        # revocations that are waiting for the TEL event to be received and processed
        self.rev = subing.CesrSuber(db=self, subkey='rev.', klas=coring.Dater)

        # presentations with resolved credentials that need to be sent to the hook
        self.recv = subing.SerderSuber(db=self, subkey='recv', klas=serdering.SerderACDC)
        # revocations whose TEL rev event has been resolved that need to be sent to the hook
        self.revk = subing.SerderSuber(db=self, subkey='revk', klas=serdering.SerderACDC)

        # presentations that have been sent to the hook that need to be ack'ed
        self.ack = subing.SerderSuber(db=self, subkey='ack', klas=serdering.SerderACDC)

        return self.env

    def clear_escrows(self) -> None:
        """
        Clear all credential escrows. Useful in testing to avoid many unneeded log messages or force reprocessing of presentations.
        """
        self.iss.trim()
        self.rev.trim()
        self.recv.trim()
        self.revk.trim()
        self.ack.trim()
        logger.info('Cleared iss and rev escrows')

    def get_counts(self) -> dict[str, int]:
        """
        Get counts of each database for metrics monitoring
        :return:
        """
        snd = len([said for (said,), prefixer in self.snd.getItemIter()])
        iss = len([said for (said,), dater in self.iss.getItemIter()])
        rev = len([said for (said,), dater in self.rev.getItemIter()])

        recv = len([said for (said, dater_qb64), creder in self.recv.getItemIter()])
        revk = len([said for (said, dater_qb64), creder in self.revk.getItemIter()])
        ack = len([said for (said,), creder in self.ack.getItemIter()])
        return {'senders': snd, 'iss': iss, 'rev': rev, 'recv': recv, 'revk': revk, 'ack': ack}
