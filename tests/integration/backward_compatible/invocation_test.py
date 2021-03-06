import time

from mock import MagicMock

import hazelcast
from hazelcast.errors import OperationTimeoutError
from hazelcast.invocation import Invocation
from hazelcast.protocol.client_message import OutboundMessage
from hazelcast.serialization import LE_INT
from tests.base import HazelcastTestCase


class InvocationTimeoutTest(HazelcastTestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc = cls.create_rc()
        cls.cluster = cls.create_cluster(cls.rc, None)
        cls.member = cls.cluster.start_member()

    @classmethod
    def tearDownClass(cls):
        cls.rc.terminateCluster(cls.cluster.id)
        cls.rc.exit()

    def setUp(self):
        self.client = hazelcast.HazelcastClient(cluster_name=self.cluster.id, invocation_timeout=1)

    def tearDown(self):
        self.client.shutdown()

    def configure_client(cls, config):
        config["cluster_name"] = cls.cluster.id
        config["invocation_timeout"] = 1
        return config

    def test_invocation_timeout(self):
        request = OutboundMessage(bytearray(22), True)
        invocation_service = self.client._invocation_service
        invocation = Invocation(request, partition_id=1)

        def mock(*_):
            time.sleep(2)
            return False

        invocation_service._invoke_on_partition_owner = MagicMock(side_effect=mock)
        invocation_service._invoke_on_random_connection = MagicMock(return_value=False)

        invocation_service.invoke(invocation)
        with self.assertRaises(OperationTimeoutError):
            invocation.future.result()

    def test_invocation_not_timed_out_when_there_is_no_exception(self):
        buf = bytearray(22)
        LE_INT.pack_into(buf, 0, 22)
        request = OutboundMessage(buf, True)
        invocation_service = self.client._invocation_service
        invocation = Invocation(request)
        invocation_service.invoke(invocation)

        time.sleep(2)
        self.assertFalse(invocation.future.done())
        self.assertEqual(1, len(invocation_service._pending))
