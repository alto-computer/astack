/* astack 점검 퀴즈. 상태는 페이지 안에서만(닫으면 초기화). 저장소·네트워크를 쓰지 않는다. */
(function(){
  [].slice.call(document.querySelectorAll('details.quiz[data-kind="mc"]')).forEach(function(q){
    var opts=[].slice.call(q.querySelectorAll('.opts li')),out=q.querySelector('.verdict');
    opts.forEach(function(li){
      li.tabIndex=0;li.setAttribute('role','button');
      function pick(){
        opts.forEach(function(o){o.classList.remove('picked','ok','no')});
        var ok=li.hasAttribute('data-ok');
        li.classList.add('picked',ok?'ok':'no');
        if(out){out.innerHTML=(ok?'<b>맞아요.</b> ':'<b>아니에요.</b> ')+(li.getAttribute('data-why')||'')}
      }
      li.addEventListener('click',pick);
      li.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();pick()}});
    });
  });
})();
