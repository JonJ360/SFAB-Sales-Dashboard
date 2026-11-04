from pathlib import Path

def test_rebar_csv_includes_excluded_month_count():
 js=(Path(__file__).resolve().parents[1]/'rebar.js').read_text()
 assert "'unknown_count_month','excluded_count_month'" in js
 assert 'candidate/unknown/excluded counts repeat per group' in js

def test_rebar_script_version_avoids_cached_pre_exclusion_renderer():
 html=(Path(__file__).resolve().parents[1]/'index.html').read_text()
 assert 'src="rebar.js?v=1.4"' in html
