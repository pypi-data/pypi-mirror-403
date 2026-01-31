# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YCounter
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
Yoctopuce library: High-level API for YCounter
version: PATCH_WITH_VERSION
requires: yocto_counter_aio
requires: yocto_api
provides: YCounter
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
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_counter_aio import YCounter as YCounter_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YCounter class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YCounterValueCallback = Union[Callable[['YCounter', str], Any], None]
        YCounterTimedReportCallback = Union[Callable[['YCounter', YMeasure], Any], None]
    except TypeError:
        YCounterValueCallback = Union[Callable, Awaitable]
        YCounterTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YCounter(YSensor):
    """
    The YCounter class allows you to read and configure Yoctopuce gcounters.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    _aio: YCounter_aio
    # --- (end of YCounter class start)
    if not _IS_MICROPYTHON:
        # --- (YCounter return codes)
        pass
        # --- (end of YCounter return codes)


    # --- (YCounter implementation)

    @classmethod
    def FindCounter(cls, func: str) -> YCounter:
        """
        Retrieves a counter for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the counter is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YCounter.isOnline() to test if the counter is
        indeed online at a given time. In case of ambiguity when looking for
        a counter by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the counter, for instance
                MyDevice.counter.

        @return a YCounter object allowing you to drive the counter.
        """
        return cls._proxy(cls, YCounter_aio.FindCounterInContext(YAPI_aio, func))

    @classmethod
    def FindCounterInContext(cls, yctx: YAPIContext, func: str) -> YCounter:
        """
        Retrieves a counter for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the counter is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YCounter.isOnline() to test if the counter is
        indeed online at a given time. In case of ambiguity when looking for
        a counter by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the counter, for instance
                MyDevice.counter.

        @return a YCounter object allowing you to drive the counter.
        """
        return cls._proxy(cls, YCounter_aio.FindCounterInContext(yctx._aio, func))

    @classmethod
    def FirstCounter(cls) -> Union[YCounter, None]:
        """
        Starts the enumeration of gcounters currently accessible.
        Use the method YCounter.nextCounter() to iterate on
        next gcounters.

        @return a pointer to a YCounter object, corresponding to
                the first counter currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YCounter_aio.FirstCounterInContext(YAPI_aio))

    @classmethod
    def FirstCounterInContext(cls, yctx: YAPIContext) -> Union[YCounter, None]:
        """
        Starts the enumeration of gcounters currently accessible.
        Use the method YCounter.nextCounter() to iterate on
        next gcounters.

        @param yctx : a YAPI context.

        @return a pointer to a YCounter object, corresponding to
                the first counter currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YCounter_aio.FirstCounterInContext(yctx._aio))

    def nextCounter(self) -> Union[YCounter, None]:
        """
        Continues the enumeration of gcounters started using yFirstCounter().
        Caution: You can't make any assumption about the returned gcounters order.
        If you want to find a specific a counter, use Counter.findCounter()
        and a hardwareID or a logical name.

        @return a pointer to a YCounter object, corresponding to
                a counter currently online, or a None pointer
                if there are no more gcounters to enumerate.
        """
        return self._proxy(type(self), self._aio.nextCounter())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YCounterValueCallback) -> int:
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

    if not _IS_MICROPYTHON:
        def registerTimedReportCallback(self, callback: YCounterTimedReportCallback) -> int:
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
            return super().registerTimedReportCallback(callback)

    # --- (end of YCounter implementation)

