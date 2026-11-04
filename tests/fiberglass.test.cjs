const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
test('separate fiberglass pieces/sales CSV and absent legacy category',()=>{
 const source=fs.readFileSync('rebar.js','utf8');const nodes={fiberglassPanel:{},fiberglassBody:{},fiberglassExport:{},rebarYear:{value:'2026'}};let download,blob;
 const ctx={state:{data:{rebar:{}}},document:{getElementById:id=>nodes[id],createElement:()=>({set download(v){download=v},click(){}})},esc:String,Blob:class{constructor(parts){blob=parts.join('')}},URL:{createObjectURL:()=>'',revokeObjectURL(){}},setTimeout:()=>{}};vm.createContext(ctx);vm.runInContext(source,ctx);
 vm.runInContext('renderFiberglass()',ctx);assert.equal(nodes.fiberglassPanel.hidden,true);
 ctx.state.data.rebar.fiberglass={monthly:[{period:'2026-01',sold_each:'12',returned_each:'1',net_each:'11',gross_sales:'60.25',return_sales:'5',net_sales:'55.25',sold_lbs:null,returned_lbs:null,net_lbs:null}]};vm.runInContext('renderFiberglass();exportFiberglass()',ctx);assert.equal(nodes.fiberglassPanel.hidden,false);assert.match(nodes.fiberglassBody.innerHTML,/12/);assert.match(blob,/Fiberglass Rebar/);assert.match(blob,/sold_each/);assert.match(blob,/Not available/);assert.match(download,/fiberglass/);
 const html=fs.readFileSync('index.html','utf8');assert.match(html,/VERSION 1.5/);assert.match(html,/rebar.js\?v=1.5/);
});
