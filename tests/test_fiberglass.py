import datetime as dt
import unittest
from scripts import rebar

class FiberglassTests(unittest.TestCase):
    def row(self, **changes):
        return dict(dict(SOPTYPE=3,document='synthetic',LNITMSEQ=1,CMPNTSEQ=0,DOCDATE='2026-01-02',PSTGSTUS=2,VOIDSTTS=0,item='RAVEN 1/2',uom='EA',schedule='EA',QTYBSUOM='1',QUANTITY='12',XTNDPRCE='60.25'),**changes)
    def units(self):
        return [dict(item='RAVEN 1/2',schedule='EA',uom='EA',equivalent_uom='EA',base_quantity='1',equivalent_quantity='1')]
    def test_separate_pieces_sales_and_coverage(self):
        r=rebar.aggregate_monthly([self.row(),self.row(SOPTYPE=4,QUANTITY='15',XTNDPRCE='-70.50')],self.units(),dt.date(2026,1,31))
        self.assertEqual(r['classified_count'],2)
        self.assertEqual(r['unknown_count'],0)
        b=r['fiberglass']['monthly'][-1]
        self.assertEqual([b[k] for k in ('sold_each','returned_each','net_each','gross_sales','return_sales','net_sales')],['12','15','-3','60.25','70.50','-10.25'])
        self.assertTrue(all(b[k] is None for k in ('sold_lbs','returned_lbs','net_lbs')))
        units=[{**self.units()[0], 'shipping_weight':360}]
        weighted=rebar.aggregate_monthly([self.row(),self.row(SOPTYPE=4,QUANTITY='15',XTNDPRCE='70.50')],units,dt.date(2026,1,31))['fiberglass']['monthly'][-1]
        self.assertEqual([weighted[k] for k in ('sold_lbs','returned_lbs','net_lbs')],['43.2','54','-10.8'])
        for weight in (0,-1,'NaN',None,296):
            bad=rebar.aggregate_monthly([self.row()],[{**units[0],'shipping_weight':weight}],dt.date(2026,1,31))['fiberglass']['monthly'][-1]
            self.assertIsNone(bad['sold_lbs'])
        conflicting=rebar.aggregate_monthly([self.row(shipping_weight=296)],units,dt.date(2026,1,31))['fiberglass']['monthly'][-1]
        self.assertIsNone(conflicting['sold_lbs'])
        duplicate=rebar.aggregate_monthly([self.row()],units*2,dt.date(2026,1,31))
        self.assertEqual(duplicate['unknown_count'],1)
        self.assertIsNone(duplicate['fiberglass']['monthly'][-1]['sold_each'])
        self.assertEqual(r['candidate_count'],r['validated_count']+r['classified_count']+r['excluded_count']+r['unknown_count'])

    def test_untrusted_units_and_new_identity_stay_unknown(self):
        for change in ({'schedule':'2'},{'QTYBSUOM':'2'},{'uom':'LBS'},{'item':'RAVEN-NEW'},{'XTNDPRCE':None},{'QUANTITY':'-1'}):
            r=rebar.aggregate_monthly([self.row(**change)],self.units(),dt.date(2026,1,31))
            self.assertEqual(r['unknown_count'],1)
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            rebar.aggregate_monthly([self.row()]*2,self.units(),dt.date(2026,1,31))
