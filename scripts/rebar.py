"""Source-validated monthly direct-LBS subset. No inferred conversions."""
import datetime as dt
import hashlib
from decimal import Decimal, InvalidOperation

GROUPS = ('Commodity rebar', 'Fabricated rebar')
# Explicit reviewed item identities, hashed to avoid publishing customer-specific item names.
# 20-foot commodity; 40-foot AND coils fabricated. Never classify by class alone.
ITEM_MAP = {'053312bf4f1b41069860632e881df96c4ac14d0527e8853453d3ca8fb45ce96f': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '1550bbfd8865cc0bb31c2a7574edaff6167c6ea1b88761420cc08b5c387e6303': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 '24e10bcce20161371c2ee8e358f662ec405071ca7e66007946bcf349fe9b4545': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 '299e6006902846ea10d8cd9a32eb792062bbc3c292ab21eaf42d791f24557fc1': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '2f6778eb6999cf3d29e94cb2d610f0e078a326cfe887a8c37831e698b9e2de90': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 '3f13b5ef866c109a7440efebed818c824bb46b0253ac6e61ff4f871d7d2b35a6': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 '3f86701f1637c183a48df22b597fa39d1922e5eda5760d9a4660a72ce214cdea': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 '41cc2d3e95065bfeff42421ce3df9d53e7f4348cc65e6cf1492658e38671fce3': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '44c66411b8cf6cccb798298edb40b8df3e6b4344dee40edadb822f298d61f1f1': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '4cafd97655745d30cee16a278f832e0c94c7f3e7d593fa3bd87568c28d008abe': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 '549b6ddb09ff56572b740b5bb9e34c59ccde1f41d746ec6b3f46f9f3b3f3ffd1': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '552b122e4a008215ceb8975ec4d7d6d75057dc174fb533d89f8bc3235a145cf0': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 '5ba28abcc2f759a83b4667e8612264e089b91725965d74146dc484d8ff9cfda4': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '5cf82d9f44c50e846d598d892b5589c422c18fa14292b53dc9f91adfaee35226': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 '603b33288b87dfbc4319fe6f1ea9d2c645aea727b10ffac31c5b316d31a00ae4': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 '6624cbb740c14109ac52359fc136c0fe9c392f3d577b8b8943a5959c84a31664': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 '67aa7dab7cdcd1bcc5c1da9851a7f03e5cf0507a2aa562d4d2bc188de976d87b': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 '6ffa4b92254e300fddc912a780c4f9a75ee7170dfab73064861016cf493a1743': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 '75dc365a3522fc0f90230827b712df5f0a97296df3fc80dd9ddc9b52a8f11276': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 '78f997b3c3b45b67c57bfc6296aebf990c78889915f39bd99d44d2867255c76c': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 '7a0f9901ed344b9f4517997255fe83ee3832d64069e167cd2a794459aa688376': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '7d04477deb90293a1fd961b8a3ea0c1a8099736545dada020f0b3d7c36b0efd8': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 '83de61b05c7a29346056dc0fd2629bfd2b0da748261e526ee070633c1544a2ae': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '853be480bc9dba7031b04e44cb0f6bfea167d0da1e74e030f0dd934b5f990168': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 '8b5ad443ac6928e2ac7e0daefe0ad86d66e58dbf8738810a61349255bc4ebb95': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 '903ace28e0da149f56c2966ce055bb5882d8e01e07e985ef490ef9b779cab7d3': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 '94d64a9d683b77de8c9f387fdbdacb2747ff991f034681d4059afd539685b531': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 'a3af8f454bd35a5566b2098e4be2804047c85093ab15a84ca5677054ae7a70d3': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 'a5f16e5c39c75fcce3db7ecd1c13e4699ea1758d0c725f93be6832033d402c48': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 'b0b2e16152102a6e57531e4d177a7936708597ab35bee188c2e85546e561505a': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 'b1ff86c6adc4ca8255a4b7c083f562cb1230a1543330474f207cf599d92a653d': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 'c27b5f36d3fd0698be32c1fe81de52439073afbbfad99e410cbe5da8368f3d85': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 'c4eb053ff9410c1f4f2ec1cc20b23382032493f561924589d74a5696f660dcd7': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 'c981c714154810eebfb57665ddda04cc088383d75efda4e3d06ba6cbede4a800': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 'ce6a6b6014d5c3aef87c1179f21bc86d7f112a9128c56314d07261b0b0b0113a': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 'd6a6115f0887526774dbfd274cc1ef83bd4297318b3573db6eb2f8edeaaa131c': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 'dfdee2492be27cb9378a842461044b17857c0d5a2ed79219c0f84b5ae1763ad5': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 'e65ce980ccab31699faf19fc8266d80169c0528631f6060c2bbd5906c2bb5356': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 'e96c7b53cfb088b1f875a15027156f27034dafd8b5d87fd2b54355ebbe0a052e': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 'ed148c78c5b2804e3fc48d05012945c6f68d7d3c1df5d0022fad127242f02a49': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 'f17ca8f51becaf92729c94748db918f6f1390bc3e237e546807f971301386ba0': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 'f724c3b5d3fb9ee2e0a23903fcebb23bba57376de4cb35f36d34d594d2fb1a66': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 'f7c929510495af84753d48ff8227ad62eb1d3767b03561188c3423a11f11d5d0': {'group': 'Fabricated rebar',
                                                                      'prepaid': False},
 'fc4fa18c1356bdbd9d1ce39a3c64e5a4cdc0a0fab833e2a1b7124dcdae7e17a2': {'group': 'Commodity rebar',
                                                                      'prepaid': False},
 'fd41a96b4a3f73d48d10faaec1ca2ba185c7fdc79054e72c85b0e682b761d99d': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 'fddc89e402327b089726256db32513ef7bf86eee94d3e5606ebb7b01fa7da023': {'group': 'Commodity rebar',
                                                                      'prepaid': True},
 'ff8f46af2be018c8c04da866fe264109a0eb36e943009dd3292205e4876dbf14': {'group': 'Fabricated rebar',
                                                                      'prepaid': True},
 'ffa6ea2c97578bfc1f1564e4d55b9c3d57660377f9de39bbdfb046fe15adb784': {'group': 'Fabricated rebar',
                                                                      'prepaid': True}}

def decimal(value):
    try:
        d = Decimal(str(value))
        return d if d.is_finite() else None
    except (ValueError, InvalidOperation):
        return None


def validated_pounds(row, uoms):
    if (row.get('SOPTYPE') not in (3,4) or row.get('VOIDSTTS') != 0
            or row.get('PSTGSTUS') != 2 or row.get('CMPNTSEQ') != 0):
        return None
    quantity = decimal(row.get('QUANTITY'))
    if row.get('uom') != 'LBS' or decimal(row.get('QTYBSUOM')) != 1 or quantity is None or quantity < 0:
        return None
    matches = [u for u in uoms if u.get('item') == row.get('item')
               and u.get('schedule') == row.get('schedule') and u.get('uom') == 'LBS']
    if len(matches) != 1:
        return None
    u = matches[0]
    if u.get('equivalent_uom') != 'LBS' or decimal(u.get('base_quantity')) != 1 or decimal(u.get('equivalent_quantity')) != 1:
        return None
    return quantity


def aggregate_monthly(lines, uoms, as_of):
    buckets, coverage, seen = {}, {}, set()
    for year in range(2024, as_of.year + 1):
        for month in range(1,13):
            period = f'{year}-{month:02d}'
            if period > as_of.isoformat()[:7]: continue
            coverage[period] = dict(period=period, candidate_count=0, validated_count=0, unknown_count=0)
            for group in GROUPS:
                buckets[period,group] = dict(period=period, group=group,
                    sold_lbs=Decimal(0), returned_lbs=Decimal(0),
                    prepaid_sold_lbs=Decimal(0), prepaid_returned_lbs=Decimal(0),
                    sold_count=0, returned_count=0, validated_count=0)
    for r in lines:
        key = tuple(r.get(k) for k in ('SOPTYPE','document','LNITMSEQ','CMPNTSEQ'))
        if any(v is None for v in key): raise ValueError('Missing source-line identity')
        if key in seen: raise ValueError('Duplicate source-line identity')
        seen.add(key)
        date = dt.date.fromisoformat(str(r['DOCDATE'])[:10])
        if not dt.date(2024,1,1) <= date <= as_of: raise ValueError('Source outside report window')
        period = date.isoformat()[:7]
        c = coverage[period]; c['candidate_count'] += 1
        mapped = ITEM_MAP.get(hashlib.sha256(r['item'].encode()).hexdigest())
        value = validated_pounds(r,uoms) if mapped else None
        if value is None:
            c['unknown_count'] += 1
            continue
        c['validated_count'] += 1
        b = buckets[period,mapped['group']]
        kind = 'sold' if r['SOPTYPE'] == 3 else 'returned'
        b[kind+'_lbs'] += value
        b[kind+'_count'] += 1
        b['validated_count'] += 1
        if mapped['prepaid']: b['prepaid_'+kind+'_lbs'] += value
    for b in buckets.values():
        c = coverage[b['period']]
        b['candidate_count_month'] = c['candidate_count']
        b['unknown_count_month'] = c['unknown_count']
        for kind in ('sold','returned'):
            # Unknown candidate membership cannot be attributed to either group.
            # Do not fabricate zero where no valid observation supports a measure.
            if c['unknown_count'] and not b[kind+'_count']:
                b[kind+'_lbs'] = None
                b['prepaid_'+kind+'_lbs'] = None
        b['net_lbs'] = None if b['sold_lbs'] is None or b['returned_lbs'] is None else b['sold_lbs']-b['returned_lbs']
        for key in ('sold_lbs','returned_lbs','net_lbs','prepaid_sold_lbs','prepaid_returned_lbs'):
            b[key] = None if b[key] is None else str(b[key])
    return dict(monthly=list(buckets.values()), coverage=list(coverage.values()),
        candidate_count=len(seen), validated_count=sum(c['validated_count'] for c in coverage.values()),
        unknown_count=sum(c['unknown_count'] for c in coverage.values()),
        status='validated subset; not complete rebar totals',
        basis='SFAB posted nonvoid historical invoices/returns, Document Date, parent lines, direct LBS only. Sold and returned are positive magnitudes; net is sold less returned.',
        coverage_warning='Rebar-name/class and coil candidates only. Unknown units/items remain unavailable. Item identity mapping is stock-length based, not finished cut length. Current item/UOM master corroborates transaction LBS; historical master changes are not reconstructed.',
        prepaid_policy='Prepaid mapped items included; bridge is part of each total, not additional pounds. No Anthony-equivalent or ton-conversion claim.',
        start='2024-01-01', through=as_of.isoformat())

ITEM_UOM_SQL = """SELECT TOP (50001) RTRIM(i.ITEMNMBR) item,RTRIM(i.ITEMDESC) description,RTRIM(i.ITMCLSCD) item_class,RTRIM(i.UOMSCHDL) schedule,i.ITEMSHWT shipping_weight,RTRIM(u.UOFM) uom,RTRIM(u.EQUIVUOM) equivalent_uom,u.EQUOMQTY equivalent_quantity,u.QTYBSUOM base_quantity,RTRIM(u.UOFMLONGDESC) uom_description
FROM dbo.IV00101 i LEFT JOIN dbo.IV40202 u ON i.UOMSCHDL=u.UOMSCHDL
WHERE i.ITEMDESC LIKE '%REBAR%' OR i.ITMCLSCD LIKE '%REBAR%' OR i.ITEMNMBR LIKE '%REBAR%' OR i.ITEMDESC LIKE '%COIL%'
ORDER BY i.ITEMNMBR,u.SEQNUMBR"""
LINE_SQL = """SELECT TOP (50001) h.SOPTYPE,RTRIM(h.SOPNUMBE) document,h.DOCDATE,h.PSTGSTUS,h.VOIDSTTS,l.LNITMSEQ,l.CMPNTSEQ,RTRIM(l.ITEMNMBR) item,RTRIM(l.ITEMDESC) description,RTRIM(l.UOFM) uom,l.QUANTITY,l.QTYBSUOM,l.QTYFULFI,l.QTYRTRND,l.XTNDPRCE,l.EXTDCOST,RTRIM(i.UOMSCHDL) schedule,RTRIM(i.ITMCLSCD) item_class,i.ITEMSHWT shipping_weight
FROM dbo.SOP30200 h JOIN dbo.SOP30300 l ON h.SOPTYPE=l.SOPTYPE AND h.SOPNUMBE=l.SOPNUMBE LEFT JOIN dbo.IV00101 i ON l.ITEMNMBR=i.ITEMNMBR
WHERE h.SOPTYPE IN (3,4) AND h.VOIDSTTS=0 AND h.DOCDATE>='20240101' AND h.DOCDATE<?
AND (l.ITEMDESC LIKE '%REBAR%' OR i.ITMCLSCD LIKE '%REBAR%' OR l.ITEMNMBR LIKE '%REBAR%' OR l.ITEMDESC LIKE '%COIL%' OR i.ITEMDESC LIKE '%COIL%')
ORDER BY h.SOPTYPE,h.SOPNUMBE,l.LNITMSEQ,l.CMPNTSEQ"""


def extract_rebar(connection, as_of):
    connection.timeout = 25
    results = []
    for sql, params in ((ITEM_UOM_SQL,()), (LINE_SQL,((as_of+dt.timedelta(days=1)).isoformat(),))):
        cursor = connection.cursor()
        cursor.execute(sql, *params)
        names = [x[0] for x in cursor.description]
        rows = [dict(zip(names,row)) for row in cursor.fetchall()]
        if len(rows) >= 50001: raise ValueError('Rebar SELECT cap reached; refusing partial snapshot')
        results.append(rows)
    return aggregate_monthly(results[1],results[0],as_of)
