# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YAngularSpeed
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
Yoctopuce library: Asyncio implementation of YAngularSpeed
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YAngularSpeed
"""
from __future__ import annotations

import sys

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union
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

# --- (YAngularSpeed class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YAngularSpeedValueCallback = Union[Callable[['YAngularSpeed', str], Any], None]
        YAngularSpeedTimedReportCallback = Union[Callable[['YAngularSpeed', YMeasure], Any], None]
    except TypeError:
        YAngularSpeedValueCallback = Union[Callable, Awaitable]
        YAngularSpeedTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YAngularSpeed(YSensor):
    """
    The YAngularSpeed class allows you to read and configure Yoctopuce tachometers.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    # --- (end of YAngularSpeed class start)
    if not _IS_MICROPYTHON:
        # --- (YAngularSpeed return codes)
        pass
        # --- (end of YAngularSpeed return codes)

    # --- (YAngularSpeed attributes declaration)
    _valueCallback: YAngularSpeedValueCallback
    _timedReportCallback: YAngularSpeedTimedReportCallback
    # --- (end of YAngularSpeed attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'AngularSpeed', func)
        # --- (YAngularSpeed constructor)
        # --- (end of YAngularSpeed constructor)

    # --- (YAngularSpeed implementation)
    @classmethod
    def FindAngularSpeed(cls, func: str) -> YAngularSpeed:
        """
        Retrieves a tachometer for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the rtachometer is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAngularSpeed.isOnline() to test if the rtachometer is
        indeed online at a given time. In case of ambiguity when looking for
        a tachometer by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the rtachometer, for instance
                MyDevice.angularSpeed.

        @return a YAngularSpeed object allowing you to drive the rtachometer.
        """
        return cls.FindAngularSpeedInContext(YAPI, func)

    @classmethod
    def FindAngularSpeedInContext(cls, yctx: YAPIContext, func: str) -> YAngularSpeed:
        """
        Retrieves a tachometer for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the rtachometer is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAngularSpeed.isOnline() to test if the rtachometer is
        indeed online at a given time. In case of ambiguity when looking for
        a tachometer by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the rtachometer, for instance
                MyDevice.angularSpeed.

        @return a YAngularSpeed object allowing you to drive the rtachometer.
        """
        obj: Union[YAngularSpeed, None] = yctx._findInCache('AngularSpeed', func)
        if obj:
            return obj
        return YAngularSpeed(yctx, func)

    @classmethod
    def FirstAngularSpeed(cls) -> Union[YAngularSpeed, None]:
        """
        Starts the enumeration of tachometers currently accessible.
        Use the method YAngularSpeed.nextAngularSpeed() to iterate on
        next tachometers.

        @return a pointer to a YAngularSpeed object, corresponding to
                the first tachometer currently online, or a None pointer
                if there are none.
        """
        return cls.FirstAngularSpeedInContext(YAPI)

    @classmethod
    def FirstAngularSpeedInContext(cls, yctx: YAPIContext) -> Union[YAngularSpeed, None]:
        """
        Starts the enumeration of tachometers currently accessible.
        Use the method YAngularSpeed.nextAngularSpeed() to iterate on
        next tachometers.

        @param yctx : a YAPI context.

        @return a pointer to a YAngularSpeed object, corresponding to
                the first tachometer currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('AngularSpeed')
        if hwid:
            return cls.FindAngularSpeedInContext(yctx, hwid2str(hwid))
        return None

    def nextAngularSpeed(self) -> Union[YAngularSpeed, None]:
        """
        Continues the enumeration of tachometers started using yFirstAngularSpeed().
        Caution: You can't make any assumption about the returned tachometers order.
        If you want to find a specific a tachometer, use AngularSpeed.findAngularSpeed()
        and a hardwareID or a logical name.

        @return a pointer to a YAngularSpeed object, corresponding to
                a tachometer currently online, or a None pointer
                if there are no more tachometers to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('AngularSpeed', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindAngularSpeedInContext(self._yapi, hwid2str(next_hwid))
        return None

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YAngularSpeedValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YAngularSpeedTimedReportCallback) -> int:
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

    # --- (end of YAngularSpeed implementation)

