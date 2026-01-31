# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YSoundSpectrum
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
Yoctopuce library: Asyncio implementation of YSoundSpectrum
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa

from .yocto_api_aio import (
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction
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
    # --- (end of YSoundSpectrum class start)
    if not _IS_MICROPYTHON:
        # --- (YSoundSpectrum return codes)
        INTEGRATIONTIME_INVALID: Final[int] = YAPI.INVALID_UINT
        SPECTRUMDATA_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of YSoundSpectrum return codes)

    # --- (YSoundSpectrum attributes declaration)
    _valueCallback: YSoundSpectrumValueCallback
    # --- (end of YSoundSpectrum attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'SoundSpectrum', func)
        # --- (YSoundSpectrum constructor)
        # --- (end of YSoundSpectrum constructor)

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
        return cls.FindSoundSpectrumInContext(YAPI, func)

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
        obj: Union[YSoundSpectrum, None] = yctx._findInCache('SoundSpectrum', func)
        if obj:
            return obj
        return YSoundSpectrum(yctx, func)

    @classmethod
    def FirstSoundSpectrum(cls) -> Union[YSoundSpectrum, None]:
        """
        comment from .yc definition
        """
        return cls.FirstSoundSpectrumInContext(YAPI)

    @classmethod
    def FirstSoundSpectrumInContext(cls, yctx: YAPIContext) -> Union[YSoundSpectrum, None]:
        """
        comment from .yc definition
        """
        hwid: Union[HwId, None] = yctx._firstHwId('SoundSpectrum')
        if hwid:
            return cls.FindSoundSpectrumInContext(yctx, hwid2str(hwid))
        return None

    def nextSoundSpectrum(self) -> Union[YSoundSpectrum, None]:
        """
        comment from .yc definition
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('SoundSpectrum', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindSoundSpectrumInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_integrationTime(self) -> int:
        """
        Returns the integration time in milliseconds for calculating time
        weighted spectrum data.

        @return an integer corresponding to the integration time in milliseconds for calculating time
                weighted spectrum data

        On failure, throws an exception or returns YSoundSpectrum.INTEGRATIONTIME_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("integrationTime")
        if json_val is None:
            return YSoundSpectrum.INTEGRATIONTIME_INVALID
        return json_val

    async def set_integrationTime(self, newval: int) -> int:
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
        rest_val = str(newval)
        return await self._setAttr("integrationTime", rest_val)

    async def get_spectrumData(self) -> str:
        json_val: Union[str, None] = await self._fromCache("spectrumData")
        if json_val is None:
            return YSoundSpectrum.SPECTRUMDATA_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YSoundSpectrumValueCallback) -> int:
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
            return await super().registerValueCallback(callback)

    # --- (end of YSoundSpectrum implementation)

