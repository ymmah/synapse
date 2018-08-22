# -*- coding: utf-8 -*-
# Copyright 2016 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from twisted.internet import defer

from synapse.http.servlet import (
    RestServlet,
    assert_params_in_dict,
    parse_json_object_from_request,
)

from ._base import client_v2_patterns

logger = logging.getLogger(__name__)


class RoomUpgradeRestServlet(RestServlet):
    PATTERNS = client_v2_patterns(
        "/rooms/(?P<room_id>[^/]*)/upgrade$",
        v2_alpha=False,
    )

    def __init__(self, hs):
        """

        Args:
            hs (synapse.server.HomeServer):
        """
        super(RoomUpgradeRestServlet, self).__init__()
        self.hs = hs
        self.room_creation_handler = hs.get_room_creation_handler()
        self.auth = hs.get_auth()

    @defer.inlineCallbacks
    def on_POST(self, request, room_id):
        requester = yield self.auth.get_user_by_req(request)

        content = parse_json_object_from_request(request)
        assert_params_in_dict(content, ("new_version", ))
        new_version = content["new_version"]

        # XXX first check that we have enough perms in the old room

        new_room_id = yield self.room_creation_handler.clone_exiting_room(
            requester, old_room_id=room_id, new_room_version=new_version,
        )

        # XXX send a tombstone in the old room
        # XXX send a power_levels in the old room, if possible

        ret = {
            "replacement_room": new_room_id,
        }

        defer.returnValue((200, ret))


def register_servlets(hs, http_server):
    RoomUpgradeRestServlet(hs).register(http_server)
