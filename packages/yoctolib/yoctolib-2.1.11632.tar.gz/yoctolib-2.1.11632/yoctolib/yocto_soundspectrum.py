# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YSoundSpectrum
#
#  - - - - - - - - - License information: - - - - - - - - -
#
#  Copyright (C) 2011 and beyond by Yoctopuce Sarl, Switzerland.
#
#  Yoctopuce Sarl (hereafter Licensor) grants to you a perpetual
#  non-exclusive license to use, modify, copy and integrate this
#  file into your software for the sole purpose of interfacing
#  with Yoctopuce products.
#
#  You may reproduce and distribute copies of this file in
#  source or object form, as long as the sole purpose of this
#  code is to interface with Yoctopuce products. You must retain
#  this notice in the distributed source file.
#
#  You should refer to Yoctopuce General Terms and Conditions
#  for additional information regarding your rights and
#  obligations.
#
#  THE SOFTWARE AND DOCUMENTATION ARE PROVIDED 'AS IS' WITHOUT
#  WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING
#  WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, FITNESS
#  FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO
#  EVENT SHALL LICENSOR BE LIABLE FOR ANY INCIDENTAL, SPECIAL,
#  INDIRECT OR CONSEQUENTIAL DAMAGES, LOST PROFITS OR LOST DATA,
#  COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY OR
#  SERVICES, ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT
#  LIMITED TO ANY DEFENSE THEREOF), ANY CLAIMS FOR INDEMNITY OR
#  CONTRIBUTION, OR OTHER SIMILAR COSTS, WHETHER ASSERTED ON THE
#  BASIS OF CONTRACT, TORT (INCLUDING NEGLIGENCE), BREACH OF
#  WARRANTY, OR OTHERWISE.
#
# *********************************************************************
"""
Yoctopuce library: High-level API for YSoundSpectrum
version: PATCH_WITH_VERSION
requires: yocto_soundspectrum_aio
requires: yocto_api
provides: YSoundSpectrum
"""
from __future__ import annotations

import sys

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union, Final
    from collections.abc import Callable, Awaitable
    const = lambda obj: obj
    _IS_MICROPYTHON = False
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_soundspectrum_aio import YSoundSpectrum as YSoundSpectrum_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YSoundSpectrum class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YSoundSpectrumValueCallback = Union[Callable[['YSoundSpectrum', str], Any], None]
    except TypeError:
        YSoundSpectrumValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YSoundSpectrum(YFunction):
    """
    The YSoundSpectrum class allows you to read and configure Yoctopuce sound spectrum analyzers.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    _aio: YSoundSpectrum_aio
    # --- (end of YSoundSpectrum class start)
    if not _IS_MICROPYTHON:
        # --- (YSoundSpectrum return codes)
        INTEGRATIONTIME_INVALID: Final[int] = YAPI.INVALID_UINT
        SPECTRUMDATA_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of YSoundSpectrum return codes)


    # --- (YSoundSpectrum implementation)

    @classmethod
    def FindSoundSpectrum(cls, func: str) -> YSoundSpectrum:
        """
        Retrieves a sound spectrum analyzer for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the sound spectrum analyzer is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSoundSpectrum.isOnline() to test if the sound spectrum analyzer is
        indeed online at a given time. In case of ambiguity when looking for
        a sound spectrum analyzer by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the sound spectrum analyzer, for instance
                MyDevice.soundSpectrum.

        @return a YSoundSpectrum object allowing you to drive the sound spectrum analyzer.
        """
        return cls._proxy(cls, YSoundSpectrum_aio.FindSoundSpectrumInContext(YAPI_aio, func))

    @classmethod
    def FindSoundSpectrumInContext(cls, yctx: YAPIContext, func: str) -> YSoundSpectrum:
        """
        Retrieves a sound spectrum analyzer for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the sound spectrum analyzer is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSoundSpectrum.isOnline() to test if the sound spectrum analyzer is
        indeed online at a given time. In case of ambiguity when looking for
        a sound spectrum analyzer by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the sound spectrum analyzer, for instance
                MyDevice.soundSpectrum.

        @return a YSoundSpectrum object allowing you to drive the sound spectrum analyzer.
        """
        return cls._proxy(cls, YSoundSpectrum_aio.FindSoundSpectrumInContext(yctx._aio, func))

    @classmethod
    def FirstSoundSpectrum(cls) -> Union[YSoundSpectrum, None]:
        """
        comment from .yc definition
        """
        return cls._proxy(cls, YSoundSpectrum_aio.FirstSoundSpectrumInContext(YAPI_aio))

    @classmethod
    def FirstSoundSpectrumInContext(cls, yctx: YAPIContext) -> Union[YSoundSpectrum, None]:
        """
        comment from .yc definition
        """
        return cls._proxy(cls, YSoundSpectrum_aio.FirstSoundSpectrumInContext(yctx._aio))

    def nextSoundSpectrum(self) -> Union[YSoundSpectrum, None]:
        """
        comment from .yc definition
        """
        return self._proxy(type(self), self._aio.nextSoundSpectrum())

    if not _DYNAMIC_HELPERS:
        def get_integrationTime(self) -> int:
            """
            Returns the integration time in milliseconds for calculating time
            weighted spectrum data.

            @return an integer corresponding to the integration time in milliseconds for calculating time
                    weighted spectrum data

            On failure, throws an exception or returns YSoundSpectrum.INTEGRATIONTIME_INVALID.
            """
            return self._run(self._aio.get_integrationTime())

    if not _DYNAMIC_HELPERS:
        def set_integrationTime(self, newval: int) -> int:
            """
            Changes the integration time in milliseconds for computing time weighted
            spectrum data. Be aware that on some devices, changing the integration
            time for time-weighted spectrum data may also affect the integration
            period for one or more sound pressure level measurements.
            Remember to call the saveToFlash() method of the
            module if the modification must be kept.

            @param newval : an integer corresponding to the integration time in milliseconds for computing time weighted
                    spectrum data

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_integrationTime(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YSoundSpectrumValueCallback) -> int:
            """
            Registers the callback function that is invoked on every change of advertised value.
            The callback is invoked only during the execution of ySleep or yHandleEvents.
            This provides control over the time when the callback is triggered. For good responsiveness, remember to call
            one of these two functions periodically. To unregister a callback, pass a None pointer as argument.

            @param callback : the callback function to call, or a None pointer. The callback function should take two
                    arguments: the function object of which the value has changed, and the character string describing
                    the new advertised value.
            @noreturn
            """
            return super().registerValueCallback(callback)

    # --- (end of YSoundSpectrum implementation)

