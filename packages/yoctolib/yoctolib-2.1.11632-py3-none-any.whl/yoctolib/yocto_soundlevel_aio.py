# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YSoundLevel
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
Yoctopuce library: Asyncio implementation of YSoundLevel
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YSoundLevel
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, YSensor, YMeasure
)

# --- (YSoundLevel class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YSoundLevelValueCallback = Union[Callable[['YSoundLevel', str], Any], None]
        YSoundLevelTimedReportCallback = Union[Callable[['YSoundLevel', YMeasure], Any], None]
    except TypeError:
        YSoundLevelValueCallback = Union[Callable, Awaitable]
        YSoundLevelTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YSoundLevel(YSensor):
    """
    The YSoundLevel class allows you to read and configure Yoctopuce sound pressure level meters.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    # --- (end of YSoundLevel class start)
    if not _IS_MICROPYTHON:
        # --- (YSoundLevel return codes)
        LABEL_INVALID: Final[str] = YAPI.INVALID_STRING
        INTEGRATIONTIME_INVALID: Final[int] = YAPI.INVALID_UINT
        # --- (end of YSoundLevel return codes)

    # --- (YSoundLevel attributes declaration)
    _valueCallback: YSoundLevelValueCallback
    _timedReportCallback: YSoundLevelTimedReportCallback
    # --- (end of YSoundLevel attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'SoundLevel', func)
        # --- (YSoundLevel constructor)
        # --- (end of YSoundLevel constructor)

    # --- (YSoundLevel implementation)
    @classmethod
    def FindSoundLevel(cls, func: str) -> YSoundLevel:
        """
        Retrieves a sound pressure level meter for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the sound pressure level meter is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSoundLevel.isOnline() to test if the sound pressure level meter is
        indeed online at a given time. In case of ambiguity when looking for
        a sound pressure level meter by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the sound pressure level meter, for instance
                MyDevice.soundLevel1.

        @return a YSoundLevel object allowing you to drive the sound pressure level meter.
        """
        return cls.FindSoundLevelInContext(YAPI, func)

    @classmethod
    def FindSoundLevelInContext(cls, yctx: YAPIContext, func: str) -> YSoundLevel:
        """
        Retrieves a sound pressure level meter for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the sound pressure level meter is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSoundLevel.isOnline() to test if the sound pressure level meter is
        indeed online at a given time. In case of ambiguity when looking for
        a sound pressure level meter by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the sound pressure level meter, for instance
                MyDevice.soundLevel1.

        @return a YSoundLevel object allowing you to drive the sound pressure level meter.
        """
        obj: Union[YSoundLevel, None] = yctx._findInCache('SoundLevel', func)
        if obj:
            return obj
        return YSoundLevel(yctx, func)

    @classmethod
    def FirstSoundLevel(cls) -> Union[YSoundLevel, None]:
        """
        Starts the enumeration of sound pressure level meters currently accessible.
        Use the method YSoundLevel.nextSoundLevel() to iterate on
        next sound pressure level meters.

        @return a pointer to a YSoundLevel object, corresponding to
                the first sound pressure level meter currently online, or a None pointer
                if there are none.
        """
        return cls.FirstSoundLevelInContext(YAPI)

    @classmethod
    def FirstSoundLevelInContext(cls, yctx: YAPIContext) -> Union[YSoundLevel, None]:
        """
        Starts the enumeration of sound pressure level meters currently accessible.
        Use the method YSoundLevel.nextSoundLevel() to iterate on
        next sound pressure level meters.

        @param yctx : a YAPI context.

        @return a pointer to a YSoundLevel object, corresponding to
                the first sound pressure level meter currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('SoundLevel')
        if hwid:
            return cls.FindSoundLevelInContext(yctx, hwid2str(hwid))
        return None

    def nextSoundLevel(self) -> Union[YSoundLevel, None]:
        """
        Continues the enumeration of sound pressure level meters started using yFirstSoundLevel().
        Caution: You can't make any assumption about the returned sound pressure level meters order.
        If you want to find a specific a sound pressure level meter, use SoundLevel.findSoundLevel()
        and a hardwareID or a logical name.

        @return a pointer to a YSoundLevel object, corresponding to
                a sound pressure level meter currently online, or a None pointer
                if there are no more sound pressure level meters to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('SoundLevel', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindSoundLevelInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_unit(self, newval: str) -> int:
        """
        Changes the measuring unit for the sound pressure level (dBA, dBC or dBZ).
        That unit will directly determine frequency weighting to be used to compute
        the measured value. Remember to call the saveToFlash() method of the
        module if the modification must be kept.

        @param newval : a string corresponding to the measuring unit for the sound pressure level (dBA, dBC or dBZ)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("unit", rest_val)

    async def get_label(self) -> str:
        """
        Returns the label for the sound pressure level measurement, as per
        IEC standard 61672-1:2013.

        @return a string corresponding to the label for the sound pressure level measurement, as per
                IEC standard 61672-1:2013

        On failure, throws an exception or returns YSoundLevel.LABEL_INVALID.
        """
        json_val: Union[str, None] = await self._lazyCache("label")
        if json_val is None:
            return YSoundLevel.LABEL_INVALID
        return json_val

    async def get_integrationTime(self) -> int:
        """
        Returns the integration time in milliseconds for measuring the sound pressure level.

        @return an integer corresponding to the integration time in milliseconds for measuring the sound pressure level

        On failure, throws an exception or returns YSoundLevel.INTEGRATIONTIME_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("integrationTime")
        if json_val is None:
            return YSoundLevel.INTEGRATIONTIME_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YSoundLevelValueCallback) -> int:
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

    if not _IS_MICROPYTHON:
        async def registerTimedReportCallback(self, callback: YSoundLevelTimedReportCallback) -> int:
            """
            Registers the callback function that is invoked on every periodic timed notification.
            The callback is invoked only during the execution of ySleep or yHandleEvents.
            This provides control over the time when the callback is triggered. For good responsiveness, remember to call
            one of these two functions periodically. To unregister a callback, pass a None pointer as argument.

            @param callback : the callback function to call, or a None pointer. The callback function should take two
                    arguments: the function object of which the value has changed, and an YMeasure object describing
                    the new advertised value.
            @noreturn
            """
            return await super().registerTimedReportCallback(callback)

    # --- (end of YSoundLevel implementation)

