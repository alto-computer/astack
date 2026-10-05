/* extracted from spec-reference-rooms-v1.html by tools/extract_kit.py */
(function(){
  var scenes=[].slice.call(document.querySelectorAll('.scene')),V=[].slice.call(document.querySelectorAll('.stage .vis')),C=[].slice.call(document.querySelectorAll('.codepane .code1'));
  var cap=null,where=document.getElementById('where'),D=[].slice.call(document.querySelectorAll('.toc a')),prog=document.getElementById('prog'),cur=-1;
  function set(i){if(i===cur||i<0)return;cur=i;V.forEach(function(v){v.classList.toggle('on',+v.dataset.v===+scenes[i].dataset.i)});C.forEach(function(c){c.classList.toggle('on',+c.dataset.c===+scenes[i].dataset.i)});
    scenes.forEach(function(s,k){s.classList.toggle('active',k===i)});var s=scenes[i];
    if(cap)cap.textContent=s.querySelector('.no').textContent+' · '+s.querySelector('.st span:last-child').textContent;
    where.textContent=s.querySelector('.st span:last-child').textContent;
    D.forEach(function(a){a.classList.toggle('on',a.dataset.sec===s.dataset.sec)});}
  function pick(){var mid=innerHeight*0.45,best=-1,bd=1e9;scenes.forEach(function(s,k){var r=s.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return;var d=Math.abs(r.top+Math.min(r.height,innerHeight)/2-mid);if(d<bd){bd=d;best=k;}});
    if(best<0){best=0;}set(best);var h=document.documentElement;prog.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}
  addEventListener('scroll',pick,{passive:true});addEventListener('resize',pick);
  [].forEach.call(document.querySelectorAll('[data-depth-set]'),function(b){b.addEventListener('click',function(){
    var anchor=scenes[cur>=0?cur:0],top=anchor.getBoundingClientRect().top;
    document.body.setAttribute('data-depth',b.dataset.depthSet);
    [].forEach.call(document.querySelectorAll('[data-depth-set]'),function(x){x.setAttribute('aria-pressed',x===b)});
    scrollBy(0,anchor.getBoundingClientRect().top-top);pick();});});
  pick();
})();

(function(){var bs=[].slice.call(document.querySelectorAll('.rfilter button')),rows=[].slice.call(document.querySelectorAll('table.rv tbody tr'));
bs.forEach(function(b){b.onclick=function(){bs.forEach(function(x){x.setAttribute('aria-pressed',x===b)});var f=b.dataset.f;
rows.forEach(function(r){r.hidden=!(f==='all'||r.classList.contains('rv-'+f))});};});})();
