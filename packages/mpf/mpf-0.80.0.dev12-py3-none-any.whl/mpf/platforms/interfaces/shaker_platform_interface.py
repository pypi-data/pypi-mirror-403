"""Platform interface for shakers."""
from typing import List

import abc


class ShakerPlatformInterface(metaclass=abc.ABCMeta):

    """Interface for shakers in hardware platforms.

    ShakerPlatformInterface is an abstract base class that should be overridden for all
    shaker interface classes on supported platforms.  This class ensures the proper required
    methods are implemented to support shaker operations in MPF.
    """

    __slots__ = []  # type: List[str]

    @abc.abstractmethod
    def pulse(self, duration_secs, power):
        """Enable the shaker for specified duration and power level."""
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self):
        """Stop this shaker.

        This should stop the output and end shaking
        """
        raise NotImplementedError
