# -*- encoding: utf-8 -*-
"""
tests module

"""

import os

import lmdb
from keri.db import subing

import vgate


def test_baser():
    """
    Test Baser class
    """
    baser = vgate.CueBaser(reopen=True)
    assert isinstance(baser, vgate.CueBaser)
    assert baser.name == 'cb'
    assert baser.temp is False
    assert isinstance(baser.env, lmdb.Environment)
    assert baser.path.endswith('vgate/db/cb')
    assert baser.env.path() == baser.path
    assert os.path.exists(baser.path)

    assert isinstance(baser.snd, subing.CesrSuber)
    assert isinstance(baser.iss, subing.CesrSuber)
    assert isinstance(baser.rev, subing.CesrSuber)
    assert isinstance(baser.recv, subing.SerderSuber)
    assert isinstance(baser.revk, subing.SerderSuber)
    assert isinstance(baser.ack, subing.SerderSuber)

    assert baser.env.stat()['entries'] == 7  # One for each DB above and then one for the version field, __version__
