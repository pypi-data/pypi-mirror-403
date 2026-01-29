#  Copyright (c) 2024. Qhash
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#
#  Author: Bapan <sbapan41@gmail.com>

from enum import Enum
import logging

from qhash.clients.protos import common_pb2


class QhashSource(Enum):
    """
    Qhash Source
    """

    WEB_PLUGIN = "web-plugin"
    DEBUGGER = "debugger"
    SDK = "sdk"
    PHONE_CALL = "phone-call"
    WHATSAPP = "whatsapp"

    MAPPING = {
        WEB_PLUGIN: common_pb2.Source.WEB_PLUGIN,
        DEBUGGER: common_pb2.Source.DEBUGGER,
        SDK: common_pb2.Source.SDK,
        PHONE_CALL: common_pb2.Source.PHONE_CALL,
        WHATSAPP: common_pb2.Source.WHATSAPP,
    }

    def get(self) -> str:
        return str(self.value)

    def source(self) -> common_pb2.Source:
        mapping = {
            QhashSource.WEB_PLUGIN: common_pb2.Source.WEB_PLUGIN,
            QhashSource.DEBUGGER: common_pb2.Source.DEBUGGER,
            QhashSource.SDK: common_pb2.Source.SDK,
            QhashSource.PHONE_CALL: common_pb2.Source.PHONE_CALL,
            QhashSource.WHATSAPP: common_pb2.Source.WHATSAPP,
        }
        return mapping.get(self)

    @staticmethod
    def from_str(label: str):
        source_map = {
            "web-plugin": QhashSource.WEB_PLUGIN,
            "debugger": QhashSource.DEBUGGER,
            "sdk": QhashSource.SDK,
            "phone-call": QhashSource.PHONE_CALL,
            "whatsapp": QhashSource.WHATSAPP,
        }

        result = source_map.get(label.lower(), QhashSource.WEB_PLUGIN)
        if result == QhashSource.WEB_PLUGIN and label.lower() != "web-plugin":
            logging.warning(
                f"{label} is not supported. Supported sources are: "
                "'web-plugin', 'debugger', 'sdk', 'phone-call', 'whatsapp'."
            )
        return result
