import unittest
from unittest.mock import MagicMock, patch
import json

from UtilityCloudAPIWrapper.Searchers import WorkOrderSearch, _WorkOrder


class TestWorkOrderSearchFlow(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://example.com/api/"
        self.logger = MagicMock()
        self.search = WorkOrderSearch(base_url=self.base_url, logger=self.logger)
        self.search.auth = "dummy"
        self.search.auth_initialized = True

    @patch('UtilityCloudAPIWrapper.Backend.easy_requests.EasyReq.make_request')
    def test_query_then_fetch_details(self, mock_make_request):
        self._details_query_test(mock_make_request)
        self._verify_details(mock_make_request)

    def _details_query_test(self, mock_make_request):
        # First call (POST): return one ID in WorkOrders
        post_resp = MagicMock()
        post_resp.json.return_value = {"WorkOrders": [{"ID": 777}]}
        # Second call (GET details): return details for that work order
        get_resp = MagicMock()
        get_resp.json.return_value = {"WorkOrderId": 777, "Title": "Leak"}
        mock_make_request.side_effect = [post_resp, get_resp]

        result = self.search.QueryWorkOrders(facet_string="PRIORITY=1")

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))
        self.assertIsInstance(result[0], _WorkOrder)
        self.assertEqual(777, result[0].WorkOrderId)

    def _verify_details(self, mock_make_request):
        self._verify_first_call(mock_make_request)
        self._verify_second_call(mock_make_request)

    def _verify_first_call(self, mock_make_request):
        # Verify the first call was a POST to the correct URL with JSON payload containing our facet
        self.assertGreaterEqual(mock_make_request.call_count, 2)
        first_call = mock_make_request.call_args_list[0]
        args, kwargs = first_call
        # Method and URL
        self.assertEqual("POST", args[0])
        self.assertEqual(f"{self.base_url}workorder/getworkorders", args[1])
        # Headers are passed via kwargs
        self.assertEqual(self.search.base_headers, kwargs.get('headers'))
        # Payload should be a JSON string; parse and verify keys
        payload_str = kwargs.get('payload')
        payload = json.loads(payload_str)
        self.assertEqual(1, payload.get('page'))
        self.assertEqual("10", payload.get('itemCount'))
        self.assertTrue(payload.get('isAdvanced'))
        self.assertTrue(payload.get('isactive'))
        self.assertEqual("PRIORITY=1", payload.get('facets'))

    def _verify_second_call(self, mock_make_request):
        # Verify the second call fetched details for that ID
        second_call = mock_make_request.call_args_list[1]
        args2, kwargs2 = second_call
        self.assertEqual("GET", args2[0])
        self.assertEqual(f"{self.base_url}workorder?workorderid=777", args2[1])
        # Headers may be positional or kwarg; check both
        headers_passed = kwargs2.get('headers', args2[2] if len(args2) > 2 else None)
        self.assertEqual(self.search.base_headers, headers_passed)
        # Payload for GET should be an empty dict
        payload_passed = kwargs2.get('payload', args2[3] if len(args2) > 3 else None)
        self.assertEqual({}, payload_passed)


if __name__ == '__main__':
    unittest.main()
