const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('fiberglass populated -> missing rebar -> legacy -> populated resets export and panel',()=>{
 const nodes=Object.fromEntries(['rebarYear','rebarBody','rebarCoverage','rebarExport','rebarStatus','fiberglassPanel','fiberglassBody','fiberglassExport'].map(id=>[id,{value:'2026',innerHTML:'',textContent:'',disabled:false,onclick:null}]));
 const populated={monthly:[{period:'2026-01',group:'Commodity rebar'}],fiberglass:{monthly:[{period:'2026-01',sold_each:'12'}]}};
 const ctx={state:{data:{rebar:populated},charts:{}},document:{getElementById:id=>nodes[id]},esc:String,chart:()=>{}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync('rebar.js','utf8'),ctx);
 const render=()=>vm.runInContext('renderRebar()',ctx);
 const absent=()=>{assert.equal(nodes.fiberglassPanel.hidden,true);assert.equal(nodes.fiberglassBody.innerHTML,'');assert.equal(nodes.fiberglassExport.disabled,true);assert.equal(nodes.fiberglassExport.onclick,null);};
 const present=()=>{assert.equal(nodes.fiberglassPanel.hidden,false);assert.match(nodes.fiberglassBody.innerHTML,/12/);assert.equal(nodes.fiberglassExport.disabled,false);assert.equal(typeof nodes.fiberglassExport.onclick,'function');};
 render();present();
 ctx.state.data={};render();absent();
 ctx.state.data={rebar:{monthly:populated.monthly}};render();absent();
 ctx.state.data={rebar:populated};render();present();
});
