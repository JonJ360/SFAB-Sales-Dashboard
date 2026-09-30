import datetime as dt
import unittest
from unittest.mock import patch
from scripts import sales_sync

class Integration(unittest.TestCase):
    def test_rebar_in_live_payload_and_integrity_hash(self):
        class Cursor:
            def execute(self,sql): return self
            def fetchall(self): return []
        class Connection:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def cursor(self): return Cursor()
        with patch.object(sales_sync,'connect',return_value=Connection()), patch('scripts.rebar.extract_rebar',return_value={'monthly':[]}) as rebar:
            data=sales_sync.extract()
        self.assertEqual(data.get('rebar'),{'monthly':[]})
        rebar.assert_called_once()
        self.assertEqual(data['sha256'],sales_sync.source_sha256(data))

    def test_rebar_failure_does_not_stop_live_financial_refresh(self):
        class Cursor:
            def execute(self,sql): return self
            def fetchall(self): return []
        class Connection:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def cursor(self): return Cursor()
        with patch.object(sales_sync,'connect',return_value=Connection()), patch('scripts.rebar.extract_rebar',side_effect=ValueError('cap')):
            data=sales_sync.extract()
        self.assertIsNone(data['rebar'])
        self.assertIn('unavailable',data['rebar_status'])
        self.assertIn('years',data)
        self.assertEqual(data['sha256'],sales_sync.source_sha256(data))
