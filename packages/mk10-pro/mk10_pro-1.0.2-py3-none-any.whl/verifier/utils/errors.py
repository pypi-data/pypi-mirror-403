# SPDX-License-Identifier: MIT
"""Standalone verifier error types."""


class VerifierError(Exception):
    """Base exception for verifier errors."""
    pass


class MTBError(VerifierError):
    """MTB verification error."""
    pass

