import datetime as dt
import hashlib
import unittest
from unittest.mock import patch
from scripts import rebar
from tests.test_rebar import RebarTests

class ExclusionTests(RebarTests):
    def test_reviewed_item_exclusion_keeps_zero_not_unknown(self):
        r={**self.line(), 'item':'HR050','uom':'EA'}
        data=rebar.aggregate_monthly([r],[],dt.date(2026,8,31))
        self.assertEqual((data['candidate_count'],data['validated_count'],data['unknown_count'],data['excluded_count']),(1,0,0,1))
        for b in data['monthly']:
            if b['period']=='2026-08':
                self.assertEqual(b['sold_lbs'],'0')
                self.assertEqual(b['excluded_count_month'],1)
        self.assertIn('non-rebar/financial',data['coverage_warning'])
        self.assertIn('not complete',data['status'])

    def test_s1300_explicit_service_exclusion(self):
        data=rebar.aggregate_monthly([{**self.line(),'item':'S1300','uom':'EA'}],[],dt.date(2026,8,31))
        self.assertEqual(data['unknown_count'],0)
        self.assertEqual(data['excluded_count'],1)

    def test_ui_separates_exclusions(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        js=(root/'rebar.js').read_text()
        html=(root/'index.html').read_text()
        self.assertIn('report.excluded_count',js)
        self.assertIn('r.excluded_count_month',js)
        self.assertIn('Excluded non-rebar/financial lines (whole month)',html)

    def test_exact_description_not_generic_and_all_period_counts(self):
        digest=hashlib.sha256('S1100\0reviewed synthetic fee'.encode()).hexdigest()
        rows=[self.line()]
        for n,(item,description,month) in enumerate([('S1100','reviewed synthetic fee','08'),('S1100','generic rebar','08'),('RAVEN 1/2','rebar','09'),('S1300','rebar','09'),('MISC','other credit','09')],2):
            rows.append({**self.line(),'document':str(n),'item':item,'description':description,'uom':'EA','DOCDATE':f'2026-{month}-15'})
        with patch.dict(rebar.EXACT_ITEM_DESCRIPTION_EXCLUSIONS,{digest:'synthetic reviewed fee'}):
            data=rebar.aggregate_monthly(rows,self.uoms(),dt.date(2026,9,30))
        self.assertEqual((data['candidate_count'],data['validated_count'],data['unknown_count'],data['excluded_count']),(6,1,3,2))
        for c in data['coverage']:
            self.assertEqual(c['candidate_count'],c['validated_count']+c['unknown_count']+c['excluded_count'])
        for b in data['monthly']:
            c=next(c for c in data['coverage'] if c['period']==b['period'])
            self.assertEqual(b['excluded_count_month'],c['excluded_count'])
            if b['period']=='2026-09': self.assertIsNone(b['sold_lbs'])
        known=next(b for b in data['monthly'] if b['period']=='2026-08' and b['group']=='Fabricated rebar')
        self.assertEqual(known['sold_lbs'],'12.34567')
