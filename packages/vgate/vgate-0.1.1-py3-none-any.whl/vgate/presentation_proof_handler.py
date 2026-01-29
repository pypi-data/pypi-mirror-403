from hio.base import doing
from keri import help
from keri.core import coring
from keri.peer import exchanging

logger = help.ogler.getLogger()


class PresentationProofHandler(doing.Doer):
    """
    Processor for responding to peer-to-peer (exn) notification messages of IPEX Grant presentation proofs.

    """

    def __init__(self, cdb, hby, notifier, parser, **kwa):
        """Initialize instance

        Parameters:
            cdb (CueBaser): communication escrow database environment
            notifier(Notifier): to read notifications to processes exns
            **kwa (dict): keyword arguments passes to super Doer

        """
        self.cdb = cdb
        self.hby = hby
        self.notifier = notifier
        self.parser = parser
        super(PresentationProofHandler, self).__init__()

    def process_notes(self):
        """
        Handles incoming IPEX Grant presentations by processing the notification queue that is populated when IPEX Grant events occur, which is what happens when a cred

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.

        The payload of the notification exn message is expected to have the following format:
        {
            "r": "/exn/ipex/grant",
            "d": "SAID of the credential"
        }
        The IPEX Grant EXN is then loaded from the Exchanger database.
        The EXN is expected to have the following format:
        {
            "e": { // embedded data in an exchange message.
                "anc": // SerderKERI: anchoring interaction event of the issuance event. Has a reference to the issuance
                {
                    "v":"KERI10JSON00013a_",                                     // CESR version string of this event
                    "t":"ixn",                                                   // KEL Event type
                    "d":"EGhSHKIV5-nkeirdkqzqsvmeF1FXw_yH8NvPSAY1Rgyd",          // SAID digest of the anchoring interaction event
                    "i":"EMl4RhuR_JxpiMd1N8DEJEhTxM3Ovvn9Xya8AN-tiUbl",          // Identifier of the issuer
                    "s":"2",                                                     // Sequence number in the issuer's KEL of the anchoring interaction event.
                    "p":"ED1kkh5_ECYriK-j2gSv6Zjr5way88XVhwRCxk5zoTRG",          // The previous event's digest
                    "a":[ // The anchoring interaction event's seal. Anchors both the issuance TEL event below and the associated ACDC below to the issuer's KEL.
                        {
                            "i":"EElymNmgs1u0mSaoCeOtSsNOROLuqOz103V3-4E-ClXH",  // SAID digest of the ACDC
                            "s": "0",                                            // Sequence number of the TEL event for the TEL associated with the ACDC anchored in this event.
                            "d":"ECUw7AdWEE3fvr7dgbFDXj0CEZuJTTa_H8-iLLAmIUPO"   // SAID digest of the TEL event for the TEL associated with the ACDC anchored in this event.
                        }
                    ]
                },
                "iss": // SerderKERI: registry issuance TEL event body. Has a reference to the ACDC credential.
                {
                    "v":"KERI10JSON0000ed_",                             // CESR version string of this event
                    "t":"iss",                                           // TEL Event type
                    "d":"ECUw7AdWEE3fvr7dgbFDXj0CEZuJTTa_H8-iLLAmIUPO",  // SAID digest of the issuance TEL event.
                    "i":"EElymNmgs1u0mSaoCeOtSsNOROLuqOz103V3-4E-ClXH",  // SAID digest of the ACDC. This refers to the ACDC below.
                    "s":"0",                                             // Sequence number of the TEL issuance event
                    "ri":"EB-u4VAF7A7_GR8PXJoAVHv5X9vjtXew8Yo6Z3w9mQUQ", // Registry identifier of the issuer
                    "dt":"2021-06-27T21:26:21.233257+00:00"              // The datetime the issuance event was created
                },
                "acdc":  // SerderACDC: credential body. The iss event has a reference to this event
                {
                    "v":"ACDC10JSON000197_",                              // CESR version string of this ACDC. indicates serialization type and protocol type
                    "d":"EElymNmgs1u0mSaoCeOtSsNOROLuqOz103V3-4E-ClXH",   // SAID digest of the ACDC
                    "i":"EMl4RhuR_JxpiMd1N8DEJEhTxM3Ovvn9Xya8AN-tiUbl",   // Issuer identifier of the credential
                    "ri":"EB-u4VAF7A7_GR8PXJoAVHv5X9vjtXew8Yo6Z3w9mQUQ",  // Registry identifier that issued this credential
                    "s":"EMQWEcCnVRk1hatTNyK3sIykYSrrFvafX3bHQ9Gkk1kC",   // Schema identifier of the credential
                    "a": { // The credential's attributes; the data the credential contains
                        "d":"EO9_6NattzsFiO8Fw1cxjYmDjOsKKSbootn-wXn9S3iB",  // SAID digest of the attributes section
                        "dt":"2021-06-27T21:26:21.233257+00:00",             // The datetime the credential was created
                        "i":"EMl4RhuR_JxpiMd1N8DEJEhTxM3Ovvn9Xya8AN-tiUbl",  // The identifier of the credential's subject (issuee)
                        "LEI":"254900OPPU84GM83MG36"                         // The Legal Entity Identifier of the credential's subject. This is the data for this credential, a QVI-like credential.
                    }
                }
            }
        }
        """
        for keys, notice in self.notifier.noter.notes.getItemIter():
            logger.info(f'Processing notice {notice}')
            attrs = notice.attrs
            route = attrs['r']

            if route == '/exn/ipex/grant':
                # said of grant message
                said = attrs['d']
                exn, pathed = exchanging.cloneMessage(self.hby, said=said)
                embeds = exn.ked['e']

                for label in ('anc', 'iss', 'acdc'):
                    ked = embeds[label]
                    sadder = coring.Sadder(ked=ked)
                    ims = bytearray(sadder.raw) + pathed[label]
                    self.parser.parseOne(ims=ims)

                acdc = embeds['acdc']
                said = acdc['d']

                sender = acdc['i']
                prefixer = coring.Prefixer(qb64=sender)

                self.cdb.snd.pin(keys=(said,), val=prefixer)
                self.cdb.iss.pin(keys=(said,), val=coring.Dater())

            # deleting wether its a grant or not, since we only process grant
            self.notifier.noter.notes.rem(keys=keys)

        return False

    def recur(self, tyme):
        """
        On each iteration process exchange (exn) notifications of IPEX Grant presentation notifications.
        """
        self.process_notes()
        return False  # Loop infinitely - long-running Doer task
