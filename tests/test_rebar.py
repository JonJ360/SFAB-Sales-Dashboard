import datetime as dt
import unittest
from scripts import rebar

class RebarTests(unittest.TestCase):
    def line(self, **kw):
        return dict(SOPTYPE=3, document='test', LNITMSEQ=1, CMPNTSEQ=0,
                    DOCDATE='2026-08-15', PSTGSTUS=2, VOIDSTTS=0, item='R460C',
                    uom='LBS', QUANTITY='12.34567', QTYBSUOM='1', schedule='LB', **kw)
    def uoms(self):
        return [dict(item='R460C',schedule='LB',uom='LBS',equivalent_uom='LBS',base_quantity='1',equivalent_quantity='1')]
    def test_monthly_sold_returned_exact_and_coils_fabricated(self):
        r=self.line(); ret={**r,'SOPTYPE':4,'QUANTITY':'2.00001'}
        data=rebar.aggregate_monthly([r,ret],self.uoms(),dt.date(2026,8,31))
        row=next(x for x in data['monthly'] if x['period']=='2026-08' and x['group']=='Fabricated rebar')
        self.assertEqual((row['sold_lbs'],row['returned_lbs'],row['net_lbs']),('12.34567','2.00001','10.34566'))
        self.assertEqual(len(data['monthly']),64)
        self.assertFalse(any(x['period']>'2026-08' for x in data['monthly']))

    def test_invalid_source_stays_null_with_coverage(self):
        for change in ({'uom':'EA'},{'QTYBSUOM':None},{'QUANTITY':None},{'QUANTITY':'-1'}, {'QUANTITY':'NaN'}, {'PSTGSTUS':0}, {'VOIDSTTS':1}, {'CMPNTSEQ':1}, {'SOPTYPE':2}, {'item':'UNKNOWN'}):
            with self.subTest(change=change):
                data=rebar.aggregate_monthly([{**self.line(),**change}],self.uoms(),dt.date(2026,8,31))
                row=next(x for x in data['monthly'] if x['period']=='2026-08' and x['group']=='Fabricated rebar')
                self.assertIsNone(row['sold_lbs'])
                self.assertEqual(data['unknown_count'],1)
                self.assertEqual(data['validated_count'],0)
    def test_missing_duplicate_or_wrong_uom_schedule_is_not_evidence(self):
        for u in ([], self.uoms()*2,[{**self.uoms()[0],'equivalent_quantity':'2'}]):
            self.assertEqual(rebar.aggregate_monthly([self.line()],u,dt.date(2026,8,31))['unknown_count'],1)

    def test_prepaid_bridge_is_included_and_commodity_mapping(self):
        # Real identity from approved mapping; no customer-prefixed IDs in fixtures.
        row={**self.line(),'item':'R46020'}
        uom={**self.uoms()[0],'item':'R46020'}
        data=rebar.aggregate_monthly([row],[uom],dt.date(2026,8,31))
        b=next(x for x in data['monthly'] if x['period']=='2026-08' and x['group']=='Commodity rebar')
        self.assertEqual(b['sold_lbs'],'12.34567')
        self.assertEqual(b['prepaid_sold_lbs'],'0')
        self.assertEqual(b['returned_lbs'],'0')
    def test_capture_uses_bounded_selects_and_fails_on_cap(self):
        class Cursor:
            description=[('item',)]
            def execute(self,sql,*params):
                self.sql=sql; return self
            def fetchall(self): return [('x',)] * 50001
        class Connection:
            timeout=0
            def cursor(self): return Cursor()
        with self.assertRaisesRegex(ValueError,'cap'):
            rebar.extract_rebar(Connection(),dt.date(2026,8,31))


    def test_legacy_sql_driver_uses_iso_string_not_date_parameter(self):
        parameters=[]
        class Cursor:
            description=[('item',)]
            def execute(self,sql,*params): parameters.extend(params); return self
            def fetchall(self): return []
        class Connection:
            timeout=0
            def cursor(self): return Cursor()
        rebar.extract_rebar(Connection(),dt.date(2026,8,31))
        self.assertEqual(parameters,['2026-09-01'])

    def test_prepaid_remains_in_totals_and_return_net_is_signed(self):
        from unittest.mock import patch
        import hashlib
        item='PREPAID-TEST'
        sold={**self.line(),'item':item,'QUANTITY':'3.00001'}
        returned={**sold,'SOPTYPE':4,'QUANTITY':'7.00002'}
        units=[{**self.uoms()[0],'item':item}]
        entry={hashlib.sha256(item.encode()).hexdigest():{'group':'Fabricated rebar','prepaid':True}}
        with patch.dict(rebar.ITEM_MAP,entry):
            data=rebar.aggregate_monthly([sold,returned],units,dt.date(2026,8,31))
        b=next(x for x in data['monthly'] if x['period']=='2026-08' and x['group']=='Fabricated rebar')
        self.assertEqual(b['sold_lbs'],b['prepaid_sold_lbs'])
        self.assertEqual(b['returned_lbs'],b['prepaid_returned_lbs'])
        self.assertEqual(b['net_lbs'],'-4.00001')

    def test_duplicate_line_identity_is_fatal(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            rebar.aggregate_monthly([self.line()]*2,self.uoms(),dt.date(2026,8,31))
    def test_future_lines_are_not_silently_added(self):
        with self.assertRaisesRegex(ValueError,'window'):
            rebar.aggregate_monthly([{**self.line(),'DOCDATE':'2026-09-01'}],self.uoms(),dt.date(2026,8,31))
