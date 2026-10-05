import os, re, html as H, importlib.util
here=os.path.dirname(os.path.abspath(__file__)); os.chdir(here)
spec=importlib.util.spec_from_file_location('d','build_rooms_d.py'); D=importlib.util.module_from_spec(spec); spec.loader.exec_module(D)
os.chdir(here)
ROOT=os.path.expanduser('~/personal/alto-rooms/'); P2=os.path.expanduser('~/personal/alto-rooms-plan2/')

# ---------------- concerns ----------------
K={ 'agent':('에이전트','무엇을 만들지 정하고 HTML 파일을 쓴다'),
    'fs':('파일 시스템','진실. 방 = 폴더, 아티팩트 = .html 파일'),
    'core':('RoomsCore','무엇이 아티팩트이고 언제 생겼는지 정한다'),
    'd':('roomsd','누가 무엇을 읽고 쓸 수 있는지 정한다'),
    'client':('클라이언트','보는 사람의 상태와 화면을 정한다'),
    'user':('사용자','방 이름, 연결할 폴더, 노트를 정한다')}
def k(key,text=None): return f'<span class="k k-{key}">{text or K[key][0]}</span>'

# ---------------- code excerpts from real files ----------------
from pygments import highlight as _hl
from pygments.lexers import RustLexer, TypeScriptLexer
from pygments.formatters import HtmlFormatter
def hl(code,path,start):
    lexer=RustLexer() if path.endswith('.rs') else TypeScriptLexer()
    fm=HtmlFormatter(linenos='inline',linenostart=start,cssclass='hl',wrapcode=True)
    return _hl(code,lexer,fm)
def src(path,start_pat,n,concern,note=''):
    base=P2 if path.startswith('apps/') else ROOT
    lines=open(base+path).read().split('\n')
    i=next(j for j,l in enumerate(lines) if re.search(start_pat,l))
    seg=lines[i:i+n]
    ind=min((len(l)-len(l.lstrip()) for l in seg if l.strip()),default=0)
    body='\n'.join(l[ind:] for l in seg)
    where=('alto-rooms-plan2/' if base==P2 else '')+f'{path}:{i+1}'
    return f'<div class="cx k-{concern}-b"><div class="codehead"><span class="dot k-{concern}-bg"></span><span class="path">{where}</span><span class="who">{K[concern][0]}</span></div>{("<p class=codenote>"+note+"</p>") if note else ""}{hl(body,path,i+1)}</div>'

# ---------------- svg ----------------
def svg(w,h,body,label): return D.svg(w,h,body,label)
EXT={'agent':' ext','fs':' ext','user':' ext'}
LANES=[('agent',58),('fs',168),('core',278),('d',388),('client',498)]
def tw(t,px=12.5):
    return sum(px*(0.95 if ord(ch)>0x2e80 else 0.56) for ch in t)
def SEQ(msgs,step,lanes=LANES,h_per=46,title='',err_at=None,allon=False):
    """msgs: (from,to,label,note) ; from==to → self action box. step: current index"""
    W=max(x for _,x in lanes)+60; top=50; H_=top+len(msgs)*h_per+20
    lx=dict(lanes)
    b=''
    for key,x in lanes:
        b+=f'<rect x="{x-50}" y="6" width="100" height="30" rx="8" class="lane k-{key}-fill{EXT.get(key,"")}"/><text x="{x}" y="26" class="lt" text-anchor="middle">{K[key][0]}</text>'
        b+=f'<line x1="{x}" y1="34" x2="{x}" y2="{H_-6}" class="life"/>'
    for i,m in enumerate(msgs):
        fr,to,lab=m[0],m[1],m[2]; y=top+i*h_per+18
        st='on' if (allon or i==step) else ('done' if i<step else 'todo')
        if err_at is not None and i>=err_at and st!='todo': st+=' err'
        if fr==to:
            x=lx[fr]; w=max(96,tw(lab)+20); b+=f'<rect x="{x-w/2}" y="{y-15}" width="{w}" height="28" rx="8" class="act {st} k-{fr}-fill"/><text x="{x}" y="{y+4}" class="al {st}" text-anchor="middle">{lab}</text>'
        else:
            x1,x2=lx[fr],lx[to]; d=1 if x2>x1 else -1
            m_='url(#arh)' if 'on' in st else 'url(#ar)'
            b+=f'<path d="M{x1+d*4} {y} H{x2-d*6}" class="e {st}" marker-end="{m_}"/><text x="{(x1+x2)/2}" y="{y-6}" class="ml {st}" text-anchor="middle">{lab}</text>'
        if len(m)>3 and m[3]: b+=f'<text x="{W-4}" y="{y+4}" class="tm {st}" text-anchor="end">{m[3]}</text>'
    return svg(W,H_,b,title)

def MAP_E(hl=None):
    def st(k_): return '' if hl is None else ('on' if k_ in hl else 'dim')
    def nd(x,y,w,h,t,s,c,key): return f'<g class="n2 {st(key)} k-{c}-fill{" ext" if c in ("agent","fs","user") else ""}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/><text x="{x+w/2}" y="{y+h/2-2}" class="t" text-anchor="middle">{t}</text><text x="{x+w/2}" y="{y+h/2+15}" class="s" text-anchor="middle">{s}</text></g>'
    b=nd(10,140,120,56,'에이전트','HTML을 쓴다','agent','agent')+nd(170,140,130,56,'폴더','~/rooms · linked','fs','fs')
    b+=nd(340,140,140,56,'RoomsCore','규칙 · 색인 · seq','core','core')+nd(340,250,140,50,'roomsd','/v1 · 4318 파일','d','d')
    b+=nd(520,200,120,44,'데스크탑','','client','client')+nd(520,256,120,44,'원격 · 제3자','','client','client')+nd(170,30,130,50,'사용자','방 · 연결 · 노트','user','user')
    E=D.edge
    b+=E('M130 168 H167','', 'S1',149,160)+E('M300 168 H337','', 'S2',318,160)+E('M410 196 V247')+E('M480 268 C500 268 500 222 517 222','', 'S3',504,240)+E('M480 278 H517')
    b+=E('M300 55 C420 55 600 80 590 197','',dash=True)+note(460,72,'화면에서 조작','s')
    return svg(660,320,b,'관심사 지도')
def note(x,y,t,c='s',a='middle'): return f'<text x="{x}" y="{y}" class="{c}" text-anchor="{a}">{t}</text>'

def TREE_SVG(hl=None):
    rows=[('rooms-protocol','core','타입 단일 정의 · ts-rs · schemars',0),('rooms-core','core','폴더 규칙 · 감시 · 색인 · 이벤트',0),('roomsd','d','axum HTTP+SSE · 가드 · 파일 origin',0),('protocol-ts','client','생성 타입 + createRoomsClient',0),('apps/desktop','client','Tauri + React · RoomsStore',0)]
    b=''
    pos={}
    for i,(t,c,s,_) in enumerate(rows):
        y=20+i*62; x=40 if i<3 else 360; y= 20+i*62 if i<3 else 20+(i-3)*62+62
        pos[t]=(x,y); stc='' if hl is None else ('on' if t in hl else 'dim')
        b+=f'<g class="n2 {stc} k-{c}-fill"><rect x="{x}" y="{y}" width="250" height="48" rx="10"/><text x="{x+14}" y="{y+21}" class="t">{t}</text><text x="{x+14}" y="{y+38}" class="s">{s}</text></g>'
    E=D.edge
    b+=E('M165 82 V71')+E('M165 144 V133')+note(178,80,'의존','s','start')
    b+=E('M360 125 C320 125 320 45 293 45','', 'ts 생성',328,70)+E('M485 144 V133')
    b+=E('M610 168 C640 168 640 230 293 175',dash=True)+note(470,222,'런타임: HTTP로만 닿는다','s')
    return svg(660,240,b,'모듈 관계')

def CORE_IN(hl=None):
    def st(k_): return '' if hl is None else ('on' if k_ in hl else 'dim')
    def nd(x,y,w,h,t,s,key): return f'<g class="n2 {st(key)} k-core-fill"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/><text x="{x+w/2}" y="{y+h/2-2}" class="t" text-anchor="middle">{t}</text><text x="{x+w/2}" y="{y+h/2+14}" class="s" text-anchor="middle">{s}</text></g>'
    b=nd(10,20,150,50,'watch.rs','notify 300ms 디바운스','watch')
    b+=f'<rect x="200" y="10" width="250" height="150" rx="12" class="grp"/>'+note(214,30,'core.rs · RoomsCore','gl','start')
    b+=nd(215,40,220,46,'Inner (Mutex)','state · index · unavailable','inner')+nd(215,100,105,46,'seq','AtomicU64','seq')+nd(330,100,105,46,'tx','broadcast 1024','tx')
    b+=nd(10,110,150,50,'walk.rs','ignore 순회 · 링크','walk')+nd(10,190,150,50,'rules.rs','classify · slug · id','rules')
    b+=nd(220,190,110,50,'index.rs','SQLite 색인','index')+nd(345,190,105,50,'meta.rs','&lt;head&gt; 64KB','meta')+nd(490,40,150,50,'state.rs','state.json · inode','state')
    E=D.edge
    b+=E('M160 45 H212','', 'rescan_room',186,38)+E('M85 70 V107')+E('M85 160 V187')+E('M275 146 V187')+E('M397 146 V187')+E('M435 63 H487')+E('M450 125 H530 C560 125 560 280 530 280',dash=True)+note(560,300,'→ roomsd SSE','s')
    b+=note(330,275,'잠금 순서: 방 scan lock → Inner · notes_lock → Inner','s')
    return svg(660,310,b,'코어 내부')

def WRONG(title,code,breaks):
    li=''.join(f'<li>{b}</li>' for b in breaks)
    return f'<div class="wrong"><div class="wrong-h"><span class="x">잘못 놓은 예</span>{title}</div><pre><code>{H.escape(code)}</code></pre><p class="wrong-cap">가상 코드 · 실제 코드에는 없다</p><ul>{li}</ul></div>'
# ---------------- scenes ----------------
S=[]
def sc(sec,title,lead,body='',detail='',vis='',code='',lvl=2,aid=None):
    S.append(dict(sec=sec,title=title,lead=lead,body=body,detail=detail,vis=vis,code=code,lvl=lvl,aid=aid))

# §1 관심사와 아키텍처
WHY={
 'agent':('아티팩트를 만드는 건 이미 사용자의 에이전트다. Rooms가 AI 일을 하지 않으려면 만드는 일은 바깥에 있어야 한다(원칙 2).','Rooms가 생성까지 맡아 모델·프롬프트·API 키가 코어로 들어온다.','바깥'),
 'fs':('설치·등록 없이 어떤 producer든 쓸 수 있는 유일한 공통 입구다. 동기화·백업도 Drive·git에 맡길 수 있다.','Rooms 전용 저장소(DB)를 진실로 두면 에이전트가 Rooms API를 알아야 한다. 결합도 0이 깨진다.','바깥'),
 'core':('"무엇이 아티팩트이고 언제 생겼나"를 한 곳에서 결정론적으로 정해야 "왜 안 보이지?"에 답할 수 있다. 파일에서 다시 알 수 없는 첫 발견 시각도 여기서만 보관한다.','화면마다 순회·무시 규칙·날짜를 따로 구현해 결과가 달라진다.','필수'),
 'd':('여러 화면(데스크탑, 원격, 제3자)이 같은 코어에 붙는 입구이고, 쓰기 자격을 한 곳에서 검사한다.','코어를 Tauri 앱 안에 넣으면 원격 웹과 제3자 UI가 붙을 입구가 없다.','검토'),
 'client':('지난 방문, 열린 탭, 접힘은 보는 사람마다 다르다. 코어가 보는 사람을 모르게 해야 여러 화면이 서로 덮어쓰지 않는다.','코어가 보는 사람 상태를 저장해 기기 사이에 충돌한다.','필수'),
 'user':('주제를 어떻게 나눌지는 취향이다. 종류별 자동 분류는 66개 중 56개가 "기타"로 빠졌다.','Rooms가 방을 자동으로 정하면 같은 실패를 한다. 온보딩 첫 분류만 에이전트가 제안하고 사용자가 확인한다.','바깥')}
NOTE_D='지금 붙는 화면은 데스크탑 하나이고 원격(Plan 4)은 아직이다. v1만 보면 roomsd를 앱과 다른 프로세스로 둔 비용(상주, 포트, 토큰)이 이득보다 클 수 있다.'
OWN={'agent':'out','fs':'out','user':'out','core':'ours','d':'ours','client':'ours'}
CONTRACT={'agent':'S1 폴더 규칙(방 폴더 아래 .html이면 보인다), 선택 메타 rooms:*, 온보딩 스킬과 ONBOARD.md',
 'fs':'방 = 폴더, 아티팩트 = .html, 무시 규칙과 .roomsignore. linked 폴더에는 쓰지 않는다',
 'user':'화면 조작 세 가지(방 만들기·이름 바꾸기, 폴더 연결, 노트 저장)와 그 이름·경로 규칙'}
CLIENT_NOTE='데스크탑 앱(참고 구현)은 우리가 만든다. 원격 웹과 제3자 UI는 같은 /v1을 쓰는 바깥 클라이언트다.'
def kcard(key,d):
    w=WHY[key]
    if OWN[key]=='out':
        return f'<div class="kc kc-out k-{key}-b"><div class="kc-h">{k(key)}<span class="own own-out">바깥 · 우리가 만들지 않음</span></div><p class="kc-do">{d}</p><dl><dt>우리가 정하는 계약</dt><dd>{CONTRACT[key]}</dd><dt>왜 바깥에 두나</dt><dd>{w[0]}</dd><dt>안에 두면</dt><dd>{w[1]}</dd></dl></div>'
    nec='꼭 있어야 함' if w[2]=='필수' else '검토 필요'
    extra=('<dt>검토할 점</dt><dd>'+NOTE_D+'</dd>') if key=='d' else ''
    extra+=('<dt>범위</dt><dd>'+CLIENT_NOTE+'</dd>') if key=='client' else ''
    return f'<div class="kc k-{key}-b"><div class="kc-h">{k(key)}<span class="own own-ours">우리 것</span><span class="nec nec-{"ok" if w[2]=="필수" else "chk"}">{nec}</span></div><p class="kc-do">{d}</p><dl><dt>왜 있어야 하나</dt><dd>{w[0]}</dd><dt>없으면</dt><dd>{w[1]}</dd>{extra}</dl></div>'
def _old_kcard(key,d):
    w=WHY[key]; nec='꼭 있어야 함' if w[2]=='필수' else '검토 필요'
    extra=('<dt>검토할 점</dt><dd>'+NOTE_D+'</dd>') if key=='d' else ''
    return f'<div class="kc k-{key}-b"><div class="kc-h">{k(key)}<span class="nec nec-{"ok" if w[2]=="필수" else "chk"}">{nec}</span></div><p class="kc-do">{d}</p><dl><dt>왜 있어야 하나</dt><dd>{w[0]}</dd><dt>없으면</dt><dd>{w[1]}</dd>{extra}</dl></div>'
rows='<div class="kgroup">우리가 만드는 것</div>'+''.join(kcard(key,K[key][1]) for key in ('core','d','client'))+'<div class="kgroup">바깥 · 계약으로만 만난다</div>'+''.join(kcard(key,K[key][1]) for key in ('agent','fs','user'))
sc('a1','관심사 여섯 개: 누가 정하고, 누가 하나',
   '이 스펙의 핵심은 "Rooms는 폴더를 읽어 보여주기만 하고, 정하는 일은 각자에게 둔다"는 것이다. 색은 문서 전체에서 같은 관심사를 뜻한다.',
   f'<div class="kcards">{rows}</div>'
   f'<p>{k("agent")}는 Rooms를 모른다. {k("core")}는 HTTP, UI, AI를 모른다. {k("client")}는 코어 내부를 모르고 /v1만 안다. 그래서 어느 한쪽을 바꿔도 나머지가 깨지지 않는다.</p>',
   '', MAP_E())
S[-1]['aid']='concerns'
sc('a1','큰 그림: 파일이 진실이고, 나머지는 그것을 번역한다',
   f'{k("agent")}가 쓴 파일을 {k("core")}가 규칙으로 읽어 색인과 이벤트로 바꾸고, {k("d")}가 그것을 /v1로 내보내고, {k("client")}가 화면에 그린다.',
   f'<p>방향은 한쪽뿐이다: 파일 시스템 → core → roomsd → client. 쓰기는 {k("user")}가 화면에서 한 조작(방 만들기, 이름 바꾸기, 노트 저장)만 거꾸로 들어온다.</p>','',MAP_E(('agent','fs','core','d','client')))
tree=f'''<pre class="tree"><code>alto-rooms/
├─ crates/
│  ├─ {k("core","rooms-protocol")}   <span class="tc">값 타입 정의 (serde · ts-rs · schemars)</span>
│  ├─ {k("core","rooms-core")}       <span class="tc">2,550줄 중 핵심</span>
│  │  ├─ core.rs     <span class="tc">RoomsCore 파사드 · 잠금 · seq · 방/노트 연산</span>
│  │  ├─ watch.rs    <span class="tc">notify 감시 · 300ms 디바운스 · resync 합치기</span>
│  │  ├─ walk.rs     <span class="tc">ignore 순회 · 링크 규칙</span>
│  │  ├─ rules.rs    <span class="tc">경로 분류 · 이름/날짜 검증 · ArtifactId</span>
│  │  ├─ index.rs    <span class="tc">SQLite 색인 · createdAt 결정</span>
│  │  ├─ meta.rs     <span class="tc">&lt;head&gt; 64KB 메타 추출</span>
│  │  └─ state.rs    <span class="tc">state.json · inode</span>
│  └─ {k("d","roomsd")}           <span class="tc">main · routes · guard · sse</span>
├─ packages/{k("client","protocol-ts")}   <span class="tc">생성 타입 + client.ts</span>
└─ apps/{k("client","desktop")}           <span class="tc">Plan 2 진행 중 · RoomsStore</span></code></pre>'''
sc('a1','실제 폴더 구조와 모듈 관계',
   f'앱은 생성된 protocol-ts만 의존한다. {k("core")}는 다른 언어, 다른 프로세스라 앱이 직접 닿을 수 없다. 그래서 "UI 교체 가능"이 구조로 강제된다.',
   tree,D.B(16),TREE_SVG())
CMP_ROWS=[('정체','라이브러리 crate (rooms-core)','실행 파일 crate (main.rs)'),
 ('아는 것','파일 시스템, SQLite, 무시 규칙, 잠금','HTTP, 포트, 헤더, 토큰, origin'),
 ('모르는 것','HTTP, UI, 누가 요청했는지','아티팩트 판정 규칙, 색인 구조'),
 ('정하는 것','무엇이 아티팩트인지, createdAt, seq 순서','누가 쓸 수 있는지, 어떤 origin에서 파일을 여는지'),
 ('내놓는 것','Rust 함수와 값 (Room, RoomsEvent)','/v1 JSON, SSE 텍스트, 파일 바이트'),
 ('의존','tokio · ignore · lol_html · rusqlite · notify (axum 없음)','axum · tower-http + rooms-core'),
 ('테스트','core_flows.rs 함수 42개, 임시 폴더로, HTTP 없이','api.rs 함수 18개, 실제 요청으로')]
cmp_t='<table class="cmp"><thead><tr><th></th><th>'+k('core')+'</th><th>'+k('d')+'</th></tr></thead><tbody>'+''.join(f'<tr><td class="rh">{a}</td><td>{b}</td><td>{c}</td></tr>' for a,b,c in CMP_ROWS)+'</tbody></table>'
def PROC(wrong=False):
    b='<rect x="10" y="10" width="420" height="250" rx="14" class="grp"/>'+note(26,32,'roomsd 프로세스 (하나)','gl','start')
    b+='<g class="n2 k-d-fill"><rect x="30" y="50" width="380" height="80" rx="10"/><text x="46" y="74" class="t">roomsd 층</text><text x="46" y="94" class="s">4317 API · 4318 파일 · write_guard · JSON · SSE</text><text x="46" y="112" class="s">토큰 · 홈 잠금 · spawn_blocking</text></g>'
    b+='<g class="n2 k-core-fill"><rect x="30" y="160" width="380" height="80" rx="10"/><text x="46" y="184" class="t">rooms-core 라이브러리</text><text x="46" y="204" class="s">규칙 · 감시 · 색인 · seq · 이벤트</text><text x="46" y="222" class="s">HTTP를 쓸 수 없다 (의존성에 axum 없음)</text></g>'
    b+=D.edge('M220 130 V157','', '함수 호출',262,148)
    b+='<g class="n2 k-client-fill"><rect x="480" y="60" width="160" height="60" rx="10"/><text x="560" y="86" class="t" text-anchor="middle">Tauri 앱</text><text x="560" y="104" class="s" text-anchor="middle">별도 프로세스</text></g>'
    b+=D.edge('M477 90 H413','on','HTTP · SSE',445,82)
    b+='<g class="n2 k-fs-fill"><rect x="480" y="180" width="160" height="60" rx="10"/><text x="560" y="206" class="t" text-anchor="middle">~/rooms</text><text x="560" y="224" class="s" text-anchor="middle">파일 시스템</text></g>'
    b+=D.edge('M410 210 H477')
    b+=note(330,290,'프로세스가 갈리는 곳은 roomsd ↔ 앱. core ↔ roomsd는 같은 프로세스 안의 층','s')
    return svg(660,305,b,'프로세스 경계')
W1=WRONG('토큰 검사를 코어에 넣으면',
"""// rooms-core/src/core.rs (가상)
pub fn create_room(&self, name: &str, auth: &HeaderMap, peer: IpAddr) -> Result<Room> {
    if !peer.is_loopback() || auth.get("authorization") != Some(&self.token) {
        return Err(CoreError::ReadOnly);
    }
    ...
}""",
['코어가 HTTP 헤더와 IP를 알아야 해서 axum을 의존하게 된다. "코어는 HTTP를 모른다"가 깨진다.',
 '감시기가 Finder에서 만든 폴더를 방으로 받아들일 때도 토큰이 필요해진다. 요청자가 없는 호출이라 넘길 토큰이 없다.',
 '코어 테스트 42개가 전부 가짜 요청을 만들어야 한다.'])
W2=WRONG('이름 규칙을 roomsd에 넣으면',
"""// roomsd/src/routes.rs (가상)
pub async fn create_room(Json(b): Json<CreateBody>) -> ... {
    if b.name.contains('/') || b.name == "journal" { return Err(400) }
    let slug = b.name.replace(' ', "-");      // NFC 정규화 빠짐
    core.mkdir_room(&slug)
}""",
['나중에 붙는 입구(원격 리스너, CLI, 테스트)가 이 검사를 건너뛴다. 규칙이 입구마다 따로 생긴다.',
 'Finder에서 만든 폴더는 roomsd를 거치지 않으므로 "연구 도구"와 "연구-도구" 충돌을 못 잡는다.',
 '규칙과 mkdir이 다른 잠금에 있어 동시에 두 요청이 오면 같은 이름 방이 둘 생길 수 있다.'])
sc('a1','RoomsCore와 roomsd: 무엇이 다르고 왜 나눴나',
   f'둘은 같은 프로세스 안의 두 층이다. roomsd 실행 파일이 rooms-core 라이브러리를 안에 넣어 쓴다. 프로세스가 갈리는 곳은 roomsd와 앱 사이다. {k("core")}는 규칙과 상태를, {k("d")}는 번역과 자격 검사를 맡는다.',
   cmp_t+'<p><b>왜 나눴나.</b> ① 의존 방향을 컴파일러가 강제한다. rooms-core의 의존성에 axum이 없어서 코어 코드에서 HTTP를 쓸 수 없다. ② 규칙 테스트가 HTTP 없이 빠르다. ③ 같은 코어를 다른 입구(원격 읽기 리스너, CLI)로 다시 쓸 수 있다.</p>'
   '<p><b>꼭 나눠야 했나.</b> crate가 하나 늘었을 뿐 프로세스는 늘지 않았다. 비용이 작고 ①의 이득이 확실하다. 비용이 큰 결정은 따로 있다. roomsd를 앱과 <i>다른 프로세스</i>로 둔 것이다(상주, 포트, 토큰). 리뷰 표에서 다시 본다.</p>'
   '<p>같은 "방 만들기"를 두 층이 실제로 어떻게 나눠 하는지:</p>'
   +src('crates/roomsd/src/routes.rs',r'pub async fn create_room',3,'d','roomsd 층: JSON을 풀어 코어 함수를 부르고 다시 JSON으로 감싼다. 규칙은 하나도 없다')
   +src('crates/rooms-core/src/core.rs',r'pub fn create_room',19,'core','코어 층: 이름 검증, slug 충돌, mkdir, state.json, 이벤트까지 같은 잠금 안에서')
   +'<p>무엇을 어디에 두면 안 되는지 한 번씩 거꾸로 놓아 보면 경계가 분명해진다.</p>'+W1+W2,
   '',PROC())
S[-1]['aid']='arch-split'
sc('a1','코어 안의 큰 그림',
   f'{k("core")} 안에서는 watch가 경로를 받아 방을 다시 훑고, 짧은 색인 단계만 Inner 잠금을 잡는다. 파일 목록을 만들고 머리를 읽는 일은 잠금 밖에서 한다.',
   '<p>이벤트 번호(seq)는 Inner를 잡은 채로 올리고 보낸다. 그래서 여러 곳에서 동시에 이벤트를 내도 받는 쪽은 항상 증가하는 seq를 본다.</p>','',CORE_IN(),
   src('crates/rooms-core/src/core.rs',r'Must be called with `Inner` held',5,'core'))

# §2 데이터 흐름
F1=[('agent','fs','benchmark.html 씀','0'),('fs','core','fs 이벤트','300ms'),('core','core','scan_room · classify',''),('core','core','read_entry · 64KB',''),('core','core','index.apply · createdAt',''),('core','d','emit seq 42',''),('d','client','SSE artifact.added','≤2s'),('client','client','seq 비교 → 카드','')]
steps=[
 ('에이전트가 방 폴더에 HTML을 쓴다',f'{k("agent")}는 Rooms를 모른다. 경로 규칙(S1)만 지키면 된다: 방 폴더 아래 .html, 무시 경로 밖.',src('crates/rooms-core/src/rules.rs',r'pub fn classify_path',25,'core','S1의 실체: 이 함수가 "무엇이 아티팩트인가"를 결정론적으로 정한다')),
 ('300ms 동안 이벤트를 모아 방 단위로 넘긴다',f'{k("core")}의 watch가 디바운스한 경로 묶음에서 방을 찾아 rescan_room을 부른다. 홈 바로 아래 변화면 먼저 Finder 변경(방 추가·이름 변경·삭제)을 맞춘다.',src('crates/rooms-core/src/watch.rs',r'let debouncer = new_debouncer',26,'core')),
 ('방을 다시 훑는다 (잠금 밖)',f'방마다 scan lock으로 직렬화하고, 목록 만들기와 파일 읽기는 Inner 잠금 없이 한다. 디렉터리 링크는 따르지 않고, 파일 링크는 대상이 .html일 때만 받는다.',src('crates/rooms-core/src/core.rs',r'fn try_rescan_room',14,'core')),
 ('바뀐 파일만 머리 64KB를 읽는다','지문(대상 경로 + mtime)이 같으면 읽지 않는다. 바뀐 파일만 &lt;head&gt;에서 rooms:* 메타와 제목을 꺼낸다.',src('crates/rooms-core/src/index.rs',r'pub fn read_entry',11,'core')+src('crates/rooms-core/src/meta.rs',r'pub fn read_meta',8,'core')),
 ('색인에 반영하고 createdAt을 고정한다','한 트랜잭션에서 upsert와 사라진 파일 제거를 한다. createdAt은 메타 → 이미 저장된 값 → 파일 시각 순이고, 한 번 정해지면 바뀌지 않는다.',src('crates/rooms-core/src/index.rs',r'fn upsert_facts',14,'core','createdAt 결정: meta.created → existing → file_created')),
 ('변경을 seq 붙은 이벤트로 낸다',f'적용 직전에 방이 지워졌거나 이름이 바뀌었으면 아무것도 쓰지 않는다. 적용한 변경마다 seq를 하나씩 올려 broadcast한다.',src('crates/rooms-core/src/core.rs',r'Removed while we were reading',16,'core')),
 ('roomsd가 SSE로 흘려보낸다',f'{k("d")}는 연결마다 맨 처음 resync{{null}}을 보내고, 이후 이벤트를 그대로 흘린다. 느린 수신자는 resync로 대체한다.',src('crates/roomsd/src/sse.rs',r'pub async fn events',16,'d')),
 ('클라이언트가 seq를 비교해 카드를 붙인다',f'{k("client")}는 그 방 스냅샷의 seq보다 작거나 같은 이벤트를 버리고, id 기준으로 덮어쓴다. 띠 끝(가장 최근)에 카드가 붙는다.',src('apps/desktop/src/data/roomsStore.ts',r'private applyArtifact',18,'client','Plan 2 브랜치(진행 중)의 코드'))]
sc('a2','에이전트가 HTML을 저장하면 2초 안에 그 방 띠에 카드가 뜬다',
   '유저가 겪는 일: Claude Code가 결과 HTML을 방 폴더에 저장하면, 앱의 그 방 띠 끝에 2초 안에 카드가 생기고 새 문서 점이 붙는다. 등록도 명령도 없다.',
   '<p>앱이 꺼져 있던 동안 생긴 파일은 다음 시작 때 전체 스캔으로 잡힌다. 아래 여덟 단계가 그 2초 안에 일어나는 일이다. 오른쪽 그림에서 지금 단계가 빨간 실로 표시된다.</p>','',SEQ(F1,0,title='US-1 전체 경로',allon=True),'',2,'us1')
for i,(t,l,c) in enumerate(steps):
    sc('a2',t,l,'','',SEQ(F1,i,title='US-1 흐름'),c,3,f'us1-{i+1}')
FS=[('client','d','① SSE 연결',''),('d','client','resync{null} · seq 41',''),('client','d','② GET 스냅샷',''),('d','core','seq 먼저 읽고 → 데이터',''),('d','client','X-Rooms-Seq: 41 + 목록',''),('client','client','③ 버퍼에서 ≤41 버림 · ④ 적용','')]
sc('a2','앱을 열거나 연결이 끊겼다 이어져도 빠지는 카드가 없다',f'유저가 겪는 일: 앱을 새로 열거나 잠자기에서 깨어나 연결이 다시 붙어도 카드가 빠지거나 두 번 생기지 않는다. {k("client")}는 이벤트 재생 없이 스냅샷과 seq만으로 맞춘다. {k("d")}는 seq를 데이터보다 먼저 읽는다. 그래야 놓치는 이벤트가 없다.','<p>먼저 읽으면 최악의 경우 같은 이벤트를 한 번 더 적용하는데, 적용이 id 기준 덮어쓰기라 안전하다.</p>'+WRONG('seq를 데이터 다음에 읽으면',"let v = f(core)?;          // ① 데이터 (seq 41 시점)\n// ← 이 사이에 artifact.added seq 42 발생\nlet seq = core.current_seq(); // ② seq = 42",['클라이언트는 "42까지 반영됨"으로 알고 버퍼의 42를 버린다.','그런데 데이터에는 42가 없다. 그 카드는 다음 이벤트가 올 때까지 화면에 안 뜬다.']),'',SEQ(FS,3,title='스냅샷과 seq'),src('crates/roomsd/src/routes.rs',r'Snapshot GET with',20,'d'))
S[-1]['aid']='us2'
FR=[('user','client','이름 "연구 도구" 입력',''),('client','d','POST /v1/rooms + Bearer',''),('d','d','write_guard 4가지 검사',''),('d','core','create_room',''),('core','fs','slug 확인 · mkdir · state.json',''),('core','client','room.added (SSE)','')]
LANES_W=[('user',58),('client',168),('d',278),('core',388),('fs',498)]
sc('a2','사이드바 +로 방을 만들고, 제목을 눌러 이름을 바꾼다',f'유저가 겪는 일: 이름을 치고 Enter를 누르면 방이 생기고, 제목을 눌러 고치면 저장 버튼 없이 바뀐다. {k("user")}가 화면에서 한 조작만 쓰기로 들어온다. {k("d")}가 쓰기 자격을 검사하고, {k("core")}가 이름 검사와 폴더 생성을 한 잠금 안에서 한다.',f'<p>owned 방의 이름 바꾸기는 폴더 이름까지 바꾸고, linked 방은 표시 이름만 바꾼다. 앱에서 바꾼 이름은 artifact 이벤트를 내지 않는다(ArtifactId가 roomId 기준).</p>',D.B(43,44),SEQ(FR,4,lanes=LANES_W,title='방 만들기'),src('crates/rooms-core/src/core.rs',r'pub fn create_room',19,'core'))
S[-1]['aid']='us3'

sc('a2','쓰던 폴더(팀 폴더 포함)를 옮기지 않고 방으로 연결한다',f'유저가 겪는 일: 폴더를 고르면 그 안의 HTML이 바로 방 띠에 뜨고, 원래 폴더에는 아무것도 생기지 않는다. {k("user")}가 고른 경로를 realpath로 바꿔 Home 관련 경로, 기존 linked 방과 겹치는 경로를 거부한다. 그래서 한 파일은 정확히 한 방에만 속한다.',f'<p>Rooms는 linked 폴더 안에 아무것도 쓰지 않는다. .gitignore는 linked 방에서만 따른다.</p>','',SEQ([('user','client','폴더 선택',''),('client','d','POST /v1/rooms/link',''),('d','core','link_folder',''),('core','core','realpath · 겹침 검사',''),('core','client','room.added → rescan','')],3,lanes=LANES_W,title='폴더 연결'),src('crates/rooms-core/src/core.rs',r'pub fn link_folder',12,'core'))
S[-1]['aid']='us4'
FJ=[('client','d','GET /v1/journal/2026-10-05',''),('d','core','journal_day',''),('core','core','by_day + realpath 중복 제거',''),('core','fs','journal/날짜/*.md 읽기',''),('d','client','JournalDay + seq','')]
sc('a2','Journal에서 그날 생긴 아티팩트와 내 노트를 함께 본다',f'유저가 겪는 일: 날짜를 고르면 그날 모든 방에서 생긴 아티팩트와 내가 쓴 계획·회고가 한 화면에 나온다. 그날의 아티팩트는 복사하지 않고 created_day로 조회한다. 같은 원본이 두 방에 링크돼도 대상 경로로 한 번만 보인다. 노트는 {k("fs")}에서 바로 읽는다.','<p>노트 저장은 임시 파일에 쓰고 rename으로 바꾼다. notes_lock을 쓰기, rename, 이벤트까지 잡아서 note.saved 순서가 파일 순서와 같다.</p>',D.B(51,52,53),SEQ(FJ,2,title='Journal 하루'),src('crates/rooms-core/src/core.rs',r'pub fn journal_day',20,'core'))
S[-1]['aid']='us5'
FO=[('client','d','GET :4318/방/문서.html',''),('d','d','Host 검사',''),('d','core','resolve_file',''),('core','fs','realpath · 방 안인지 확인',''),('d','client','파일 + CSP sandbox',''),('client','client','새 탭 · 불투명 origin','')]
sc('a2','카드를 확대하면 문서가 새 탭에서 열린다','유저가 겪는 일: 카드 오른쪽 위 확대를 누르면 그 아티팩트가 새 문서 탭으로 열린다. 문서는 앱과 다른 origin(4318)에서 sandbox로 열려서, 문서 안 스크립트가 앱 API를 부를 수 없다.','<p>파일 요청은 방 안의 파일만 통과한다. 상위 경로, 숨김 파일, 방 밖으로 나가는 디렉터리 링크는 거부된다(3.5).</p>','',SEQ(FO,4,lanes=[('client',58),('d',190),('core',322),('fs',454)],title='문서 열기'),src('crates/roomsd/src/routes.rs',r'pub async fn file',9,'d')+src('crates/roomsd/src/lib.rs',r'pub fn build_files_router',9,'d'),2,'us6')
# §3 에러 흐름
E1=[('fs','core','이벤트 유실 (overflow)',''),('core','core','resync 요청 합치기 (2초 간격)',''),('core','core','sync_home_dirs + backfill_all',''),('core','d','resync{null}',''),('d','client','resync{null}',''),('client','d','스냅샷 다시 받기','')]
sc('a3','감시 이벤트가 유실되면: 전부 다시 맞춘다',f'{k("core")}는 방 단위 재스캔을 믿지 않고 전체를 다시 훑은 뒤 resync를 낸다. 여러 번 요청이 와도 2초 간격으로 한 번 더만 돈다.','<p>스펙 §3은 "해당 방 전체 재스캔"이었는데, 코드는 오버플로 때 전체 resync로 간다(커밋 90a2c83 "coalesce watcher-triggered resyncs"). 스펙보다 보수적인 쪽으로 바뀐 지점이다.</p>','',SEQ(E1,1,err_at=0,title='오버플로'),src('crates/rooms-core/src/watch.rs',r'let debouncer = new_debouncer',8,'core')+src('crates/rooms-core/src/core.rs',r'pub fn resync_all',7,'core'))
S[-1]['aid']='e1'
E2=[('fs','core','linked 폴더 사라짐',''),('core','core','root_available = false',''),('core','client','room.updated (unavailable)',''),('core','core','2초마다 재확인',''),('fs','core','폴더 돌아옴',''),('core','client','room.updated (ok)','')]
sc('a3','연결한 폴더가 사라지면: 방과 색인은 남긴다',f'방을 지우지 않고 status만 unavailable로 바꾼다. 색인 행도 지우지 않는다. 2초마다 다시 확인해서 돌아오면 ok로 되돌린다.','<p>훑는 도중에 사라진 경우도 같은 길로 간다. 부분 목록을 적용하면 행이 지워질 수 있기 때문이다.</p>','',SEQ(E2,2,err_at=0,title='폴더 사라짐'),src('crates/rooms-core/src/core.rs',r'if !root_available\(&root\) \{',8,'core'))
S[-1]['aid']='e2'
E3=[('core','core','방 A 훑는 중 (잠금 밖)',''),('user','core','방 A 이름 변경',''),('core','core','적용 직전 root 재확인',''),('core','core','다르면 아무것도 안 씀',''),('core','core','rename 후속 재스캔이 처리','')]
sc('a3','훑는 도중에 방 이름이 바뀌면: 아무것도 쓰지 않는다',f'잠금 밖에서 읽은 목록은 옛 경로를 가리킨다. 적용 직전에 경로를 다시 확인하고 다르면 버린다. 지워진 파일이 되살아나는 일을 막는다.','<p>같은 방의 스캔은 scan lock으로 직렬화되므로 마지막에 적용되는 스캔이 가장 최신이다.</p>','',SEQ(E3,3,lanes=[('user',80),('core',330),('fs',560)],err_at=1,title='경쟁 조건'),src('crates/rooms-core/src/core.rs',r'Removed while we were reading',4,'core'))
S[-1]['aid']='e3'
E4=[('client','d','POST (원격 · 토큰 없음)',''),('d','d','loopback? Host? Origin? Bearer?',''),('d','client','403 read_only',''),('fs','d','아티팩트 JS → /v1 호출',''),('d','fs','막힘: 4318 sandbox origin','')]
sc('a3','자격 없는 쓰기와 아티팩트 안의 스크립트',f'{k("d")}의 쓰기는 네 조건을 모두 통과해야 한다. 아티팩트 HTML은 다른 origin(4318)에서 sandbox로 열려 API를 부를 수 없다.','<p>원격 읽기 전용 리스너(4319)는 아직 코드에 없다(Plan 4). 지금 main.rs는 4317, 4318만 연다.</p>','',SEQ(E4,2,lanes=[('client',80),('d',330),('fs',560)],err_at=1,title='쓰기 거부'),src('crates/roomsd/src/guard.rs',r'pub async fn write_guard',9,'d')+src('crates/roomsd/src/lib.rs',r'pub fn build_files_router',9,'d'))
S[-1]['aid']='e4'
E5=[('client','d','GET 4318/방/../../x',''),('d','core','resolve_file',''),('core','core','.. · 점 파일 · 디렉터리 링크 탈출 검사',''),('core','d','path_escape 400','')]
sc('a3','방 밖 파일을 요청하면: path_escape',f'{k("core")}는 상위 경로, 숨김 경로, 방 밖으로 나가는 디렉터리 링크를 모두 거부한다. 파일 링크는 대상이 .html일 때만 따른다.','',D.B(13),SEQ(E5,2,lanes=[('client',80),('d',330),('core',560)],err_at=2,title='경로 탈출'),src('crates/rooms-core/src/core.rs',r'pub fn resolve_file',14,'core'))
S[-1]['aid']='e5'

# §5 비즈니스 로직 (after review)
sc('a5','무엇이 아티팩트인가','방 폴더(하위 포함)의 .html/.htm. 숨김 폴더, node_modules, dist, build, .next, coverage는 무시. linked는 .gitignore도, 모든 방은 .roomsignore를 따른다.',D.B(9),D.B(12),'',src('crates/rooms-core/src/walk.rs',r'for entry in walker.flatten',22,'core'))
sc('a5','날짜와 id는 어떻게 정해지나','createdAt은 처음 발견할 때 정하고 고정한다. Journal day는 그 로컬 날짜. ArtifactId는 sha1(roomId:relPath) 앞 16자라 파일을 옮기면 새 id가 된다.',D.B(10),'',D.CREATED(1),src('crates/rooms-core/src/rules.rs',r'pub fn artifact_id',6,'core'))
sc('a5','방 이름 규칙','폴더 이름은 NFC 정규화 후 공백을 -로 바꾼 slug. 충돌은 NFC, 대소문자 무시로 비교해 "연구 도구"와 "연구-도구"를 같은 이름으로 본다.','','', '',src('crates/rooms-core/src/rules.rs',r'pub fn validate_room_name',18,'core'))
sc('a5','잠금과 순서 보장','방 scan lock → Inner, notes_lock → Inner 순서로만 잡는다. seq는 Inner 안에서 올리고 보낸다. 스냅샷은 seq를 데이터보다 먼저 읽는다.','',D.B(14),CORE_IN(('inner','seq','tx')),src('crates/rooms-core/src/core.rs',r'fn emit_changes',14,'core'))

# ---------------- review table (§4) ----------------
REV=[
 ('결정','파일 = 진실, SQLite = 다시 만들 수 있는 색인','user','외부 사례','Codex CLI의 sessions/*.jsonl + state.sqlite. 사용자가 제안','색인이 진실이 되면 에이전트가 파일만 쓰는 규칙과 충돌','index.rs 테스트 deleting_db_rebuilds · corrupt_db_is_recreated','us1-5'),
 ('결정','코어는 Rust 별도 프로세스(roomsd)','agent','외부 사례','Codex CLI 구조. 초안은 Bun+TS였고 사용자 질문 뒤 Rust로 바뀜','상주 방식(사이드카 vs launchd)이 아직 미정(열린 질문 2)','main.rs: 4317 · 4318 바인드, 홈 잠금','arch-split'),
 ('결정','프로토콜은 HTTP + JSON + SSE','agent','대안 비교','JSON-RPC stdio · WebSocket · gRPC를 비교해 기각','양방향 실시간이 필요해지면 SSE로 부족','routes.rs · sse.rs','us2'),
 ('가정','파일 쓰기는 300ms 디바운스면 끝나 있다','agent','근거 없음','스펙에는 "크기 안정 300ms 확인"이 있으나 코드에서 그 대기를 찾지 못함 (추론)','쓰는 중인 파일을 읽으면 제목·메타가 빈 카드가 잠깐 뜬다. 다음 이벤트에서 updated로 고쳐짐','watch.rs 디바운스만 확인','us1-2'),
 ('가정','파일 이벤트 → 카드 ≤ 2초','agent','측정','타이밍 테스트 있음(ROOMS_TEST_SLOWDOWN로 경계 조정)','큰 팀 폴더에서 첫 스캔이 길면 체감 지연','커밋 f1d966b','us1'),
 ('결정','createdAt은 첫 발견 때 고정','user','사용자 결정','Journal "그날 생긴 것"이 흔들리지 않게 (Senior Q2)','동기화 도구가 파일을 새로 쓰면 첫 발견이 늦어짐. 메타가 없으면 그 날짜로 고정','index.rs first_seen_is_kept_across_reopen_and_rewrite','us1-5'),
 ('결정','owned 방은 inode로 추적','agent','코드베이스','Finder에서 이름을 바꿔도 같은 id (Senior Q3)','다른 볼륨·동기화 폴더로 옮기면 inode가 바뀌어 방이 지워졌다 새로 생김','state.rs inode_survives_rename','e3'),
 ('결정','아티팩트는 별도 origin(4318) + CSP sandbox','agent','외부 사례','불투명 origin이면 아티팩트 JS가 API를 못 부른다 (Senior Q6)','allow-same-origin이 필요한 아티팩트(저장소 사용)는 동작 안 함','lib.rs build_files_router','us6'),
 ('결정','쓰기 = loopback + Host + Origin + 실행마다 새 Bearer','agent','외부 사례','DNS rebinding · CSRF 방어 (Senior Q6)','토큰 전달은 Tauri가 맡음. 제3자 로컬 도구는 쓰기 불가','guard.rs write_guard','e4'),
 ('결정','원격 보기는 GET만 등록한 별도 리스너(4319)','agent','대안 비교','tailscale serve는 요청이 loopback으로 보여 쓰기 검사가 뚫림','아직 구현 안 됨(Plan 4)','—','e4'),
 ('결정','이벤트 재생 없이 스냅샷 + seq로 맞춘다','agent','외부 사례','Kubernetes list-watch(resourceVersion)와 같은 모양 (비유, 추론)','seq가 데이터보다 늦게 읽히면 갱신을 잃음 → 코드가 seq를 먼저 읽음','routes.rs snapshot','us2'),
 ('가정','카드 미리보기는 보이는 카드만 sandbox iframe 축소 렌더','agent','근거 없음','썸네일 사전 생성은 무거워서 기각. 성능 측정 없음','방 하나에 카드 수십 개면 iframe 비용','Plan 2에서 확인 필요','us6'),
 ('가정','온보딩은 최근 14일이면 충분','agent','근거 없음','"7일은 비고 30일은 거칠다"는 감','오래된 핵심 문서가 빠짐. 재실행으로 넓힐 수 있음','—','concerns'),
 ('결정','방 삭제 없음, 연결 해제도 v1에 없음','user','사용자 결정','필요해지면 추가','잘못 연결한 폴더를 되돌릴 방법이 없음','—','us3'),
 ('전제','에이전트는 Rooms를 모르고 폴더 규칙만 지킨다','user','사용자 결정','공리: 결합도 0','메타(rooms:created 등)를 안 쓰면 날짜·출처가 파일 시각에 의존','meta.rs fallback 테스트','us1-1'),
]
TAG={'외부 사례':'ok','대안 비교':'ok','측정':'ok','사용자 결정':'user','코드베이스':'mid','근거 없음':'bad'}
rv=''.join(f'<tr class="rv-{TAG[b]}"><td><span class="tag">{t}</span></td><td><b>{w}</b><div class="who2">{k(who, "사용자가 정함" if who=="user" else "에이전트가 정함")}</div></td><td><span class="ev ev-{TAG[b]}">{b}</span><div class="sm">{why}</div></td><td class="sm">{risk}</td><td class="sm mono">{chk}</td><td><a href="#{lnk}" class="jump">흐름 보기</a></td></tr>' for t,w,who,b,why,risk,chk,lnk in REV)
REVIEW=f'''<section class="review" id="a4"><div class="secHead"><div class="n">§4</div><h2>가정, 전제, 결정 리뷰</h2></div>
<p class="rlead">위 흐름을 본 뒤에 읽는다. 빨간 줄은 근거가 없는 가정이라 먼저 확인할 곳이다. <b>근거</b> 칸은 외부 사례를 봤는지, 코드베이스만 보고 정했는지, 아무 근거가 없는지를 나눈다.</p>
<div class="rfilter"><button data-f="all" aria-pressed="true">전체 {len(REV)}</button><button data-f="bad" aria-pressed="false">근거 없음 {sum(1 for r in REV if TAG[r[3]]=="bad")}</button><button data-f="user" aria-pressed="false">사용자 결정 {sum(1 for r in REV if TAG[r[3]]=="user")}</button><button data-f="ok" aria-pressed="false">외부 사례 · 비교 · 측정</button></div>
<div class="tablewrap"><table class="rv"><thead><tr><th>종류</th><th>무엇을</th><th>근거</th><th>틀리면 깨지는 것</th><th>확인한 곳</th><th></th></tr></thead><tbody>{rv}</tbody></table></div></section>'''

SECS=[('a0','0 · Overview'),('a1','1 · 관심사와 아키텍처'),('a2','2 · 데이터 흐름'),('a3','3 · 에러 흐름'),('a4','4 · 가정 · 결정 리뷰'),('a5','5 · 비즈니스 로직'),('a6','부록 · Seam · Contract')]
TITLES={'a1':'핵심 관심사와 아키텍처','a2':'주요 유저 스토리의 데이터 흐름','a3':'에러 시나리오의 데이터 흐름','a5':'알아야 할 비즈니스 로직과 동작 방식'}

SENT=re.compile(r'(?<=[다요음함됨임])\.(?:\s+)(?=\S)|(?<=\))\.(?:\s+)(?=[가-힣A-Z{<"“①-⑩])')
def para(text,per=2):
    parts=[p for p in SENT.split(text) if p.strip()]
    if len(parts)<=per: return f'<p>{text}</p>'
    out=[]
    for j in range(0,len(parts),per):
        chunk='. '.join(x.strip() for x in parts[j:j+per])
        if j+per<len(parts): chunk=chunk.rstrip()+'.'
        out.append(f'<p>{chunk}</p>')
    return ''.join(out)
def reflow(h):
    # split long <p> (no block children) into 2-sentence paragraphs
    def f(m):
        attrs,inner=m.group(1),m.group(2)
        if '<pre' in inner or '<ul' in inner or '<table' in inner or attrs.strip(): return m.group(0)
        return para(inner)
    return re.sub(r'<p([^>]*)>(.*?)</p>',f,h,flags=re.S)
INTRO={
 'a2':'<p class="sinlead">핵심 경로 여섯 개. 각 줄이 아래 2.1~2.6이고, 2.1은 그 안의 기술 단계까지 따라간다.</p><table class="ustab"><thead><tr><th>#</th><th>유저가 겪는 것</th><th>핵심 경로</th><th>보장되는 것</th><th>스펙</th></tr></thead><tbody>'
  '<tr><td><a href="#us1">2.1</a></td><td>에이전트가 HTML을 저장하면 2초 안에 그 방 띠에 카드가 뜬다</td><td>폴더 → 감시 → 색인 → SSE → 화면</td><td>등록·명령 없음. 꺼져 있던 동안 생긴 것도 다음 시작 때</td><td>US-1</td></tr>'
  '<tr><td><a href="#us2">2.2</a></td><td>앱을 열거나 연결이 끊겼다 이어져도 빠지는 카드가 없다</td><td>SSE 먼저 → 스냅샷 + seq</td><td>이벤트 재생 없이 누락·중복 없음</td><td>US-7 · S3</td></tr>'
  '<tr><td><a href="#us3">2.3</a></td><td>사이드바 +로 방을 만들고, 제목을 눌러 이름을 바꾼다</td><td>화면 → /v1 쓰기 → 폴더 → 이벤트</td><td>저장 버튼 없음. 같은 이름 거부</td><td>US-2</td></tr>'
  '<tr><td><a href="#us4">2.4</a></td><td>쓰던 폴더를 옮기지 않고 방으로 연결한다</td><td>경로 검사 → state.json → 스캔</td><td>원래 폴더에 아무것도 쓰지 않음</td><td>US-3</td></tr>'
  '<tr><td><a href="#us5">2.5</a></td><td>Journal에서 그날 생긴 아티팩트와 내 노트를 함께 본다</td><td>날짜 조회 → 중복 제거 → 노트</td><td>복사 없음. 같은 원본은 한 번</td><td>US-5</td></tr>'
  '<tr><td><a href="#us6">2.6</a></td><td>카드를 확대하면 문서가 새 탭에서 열린다</td><td>4318 파일 origin → 방 밖 차단 → sandbox</td><td>문서 스크립트는 앱 API를 못 부름</td><td>US-4</td></tr></tbody></table>',
 'a3':'<p class="sinlead">사용자에게 어떻게 보이는지부터. 각 줄이 아래 3.1~3.5다.</p><table class="ustab"><thead><tr><th>#</th><th>무엇이 잘못되나</th><th>사용자에게 보이는 것</th><th>처리</th></tr></thead><tbody>'
  '<tr><td><a href="#e1">3.1</a></td><td>감시 이벤트가 유실됨</td><td>몇 초 늦게 반영</td><td>전체 다시 맞춤 + resync</td></tr>'
  '<tr><td><a href="#e2">3.2</a></td><td>연결한 폴더가 사라짐</td><td>방 이름이 흐려짐, 카드는 남음</td><td>unavailable, 2초마다 재확인</td></tr>'
  '<tr><td><a href="#e3">3.3</a></td><td>훑는 도중 방 이름이 바뀜</td><td>아무 이상 없음</td><td>적용 안 하고 후속 재스캔에 맡김</td></tr>'
  '<tr><td><a href="#e4">3.4</a></td><td>자격 없는 쓰기, 문서 안 스크립트의 API 호출</td><td>원격에는 쓰기 버튼 없음</td><td>403 read_only, 별도 origin</td></tr>'
  '<tr><td><a href="#e5">3.5</a></td><td>방 밖 파일 요청</td><td>문서가 열리지 않음</td><td>path_escape 400</td></tr></tbody></table>'}
def scene_html(i,s,no,anchor):
    vis_inl=f'<div class="inl vis-inl">{s["vis"]}</div>' if s['vis'] else ''
    code_inl=f'<div class="codes">{s["code"]}</div>' if s['code'] else ''
    body=f'<div class="d2">{s["body"]}</div>' if s['body'] else ''
    det=f'<div class="more2">{s["detail"]}</div>' if s['detail'] else ''
    tag='h3' if s.get('lvl',2)==2 else 'h4'
    return f'<section class="scene lvl{s.get("lvl",2)}" id="{s.get("aid") or anchor}" data-i="{i}" data-sec="{s["sec"]}"><{tag} class="st"><span class="no">{no}</span><span>{s["title"]}</span></{tag}><div class="lead">{para(s["lead"])}</div>{vis_inl}{reflow(body)}{code_inl}{reflow(det)}</section>'

def reader(sec_ids):
    parts=[];vis=[];codes=[]
    for sid in sec_ids:
        parts.append(f'<div class="secHead" id="{sid}"><div class="n">§{sid[1:]}</div><h2>{TITLES[sid]}</h2></div>'+INTRO.get(sid,''))
        n=0;n3=0
        for i,s in enumerate(S):
            if s['sec']!=sid: continue
            if s.get('lvl',2)==2: n+=1; n3=0; no=f'{sid[1:]}.{n}'
            else: n3+=1; no=f'{sid[1:]}.{n}.{n3}'
            parts.append(scene_html(i,s,no,f'{sid}-{n}-{n3}'))
            vis.append(f'<div class="vis" data-v="{i}">{s["vis"]}</div>' if s['vis'] else f'<div class="vis" data-v="{i}"></div>')
            codes.append(f'<div class="code1" data-c="{i}">{s["code"]}</div>')
    return f'<div class="reader"><div class="scenes">{"".join(parts)}</div><aside class="stage">{"".join(vis)}<div class="cap"></div></aside></div>'

APPX=''.join(f'<details class="apx"><summary>{t}</summary><div>{h}</div></details>' for t,h in [
 ('S1 · Producer → 폴더',D.balance(D.SEAMS[0])),('S2 · 폴더 → RoomsCore',D.balance(D.SEAMS[1])),('S3 · roomsd → Client',D.balance(D.SEAMS[2])),('S4 · Handoff (v2)',D.balance(D.SEAMS[3])),
 ('값 타입',D.blk(26)),('입력 검증',D.blk(27)),('출력 보장',D.blk(28)),('에러 코드',D.blk(29)),('Acceptance Criteria',D.blk(8)),('Glossary',D.blk(4)),('Senior Q&A',D.blk(76)),('열린 질문',D.blk(77)),('테스트 전략',D.blk(73))])

CSS=D.CSS+'''
.scene.lvl3{padding:5vh 0 5vh 22px;border-left:2px solid var(--surface-strong)}
.scene.lvl3 h4.st{margin:0 0 8px;font-size:17px;font-weight:500;display:flex;gap:10px;align-items:baseline}
.scene.lvl3 h4.st .no{font-family:var(--mono);font-size:12px;color:var(--ink-3);font-weight:400}
.scene.lvl3.active h4.st .no{color:var(--accent)}
.scene.lvl3 .lead{font-size:16px}
.sinlead{margin:14px 0 10px;color:#333}
table.ustab{border-collapse:collapse;width:100%;font-size:14px;margin:0 0 10px}
table.ustab th{text-align:left;font-weight:500;color:var(--ink-2);font-size:12.5px;border-bottom:1px solid var(--hairline);padding:8px 12px 8px 0}
table.ustab td{border-bottom:1px solid var(--surface-strong);padding:10px 12px 10px 0;vertical-align:top}
table.ustab td:first-child{font-family:var(--mono);font-size:12.5px;white-space:nowrap}
.lead p{margin:0 0 10px}
.d2 p,.more2 p{margin:0 0 12px}
.hl{margin:0;background:transparent}
.hl pre{margin:0;padding:10px 12px 12px;font-family:var(--mono);font-size:13px;line-height:1.7;white-space:pre;overflow-x:auto;color:#1f2328}
.hl .linenos{display:inline-block;width:3.2em;padding-right:1em;text-align:right;color:#8c959f;user-select:none;-webkit-user-select:none}
.hl .k,.hl .kd,.hl .kr,.hl .kn,.hl .kp,.hl .kc{color:#cf222e}
.hl .kt,.hl .nc,.hl .nn{color:#953800}
.hl .nf,.hl .fm{color:#8250df}
.hl .s,.hl .s1,.hl .s2,.hl .sb,.hl .sc,.hl .se{color:#0a3069}
.hl .m,.hl .mi,.hl .mf,.hl .mh{color:#0550ae}
.hl .c,.hl .c1,.hl .cm,.hl .cs,.hl .sd{color:#57606a;font-style:italic;background:#fff8c5}
.hl .nb,.hl .bp{color:#0550ae}
.hl .o,.hl .p{color:#1f2328}
.hl .fm,.hl .nd{color:#8250df}
.cx{font-size:13px}
.cx .codenote,.d2 .cx .codenote{margin:6px 12px 0;font-size:12.5px;color:var(--ink-2)}
/* 단색: 관심사 색 제거. 구분은 실선(우리 것) / 점선(바깥), 강조는 실(빨강)만 */
.k{color:var(--ink)!important;border-bottom:0!important;font-weight:600}
.kc,.cx{border-top-color:var(--hairline)!important} .kc{border-top-width:1px!important}
.codehead .dot{background:var(--ink-3)!important}
.dg rect.lane.ext,.dg .n2.ext rect{stroke-dasharray:5 4!important}
.nec-ok{background:var(--surface)!important;color:var(--ink-2)!important}

.kgroup{font-size:13px;color:var(--ink-2);margin:10px 0 0;font-weight:500}
.kc-out{border-style:dashed;border-top-style:solid;background:var(--surface)}
.own{font-size:12px;border-radius:999px;padding:1px 9px;margin-left:auto}
.own-ours{background:var(--ink);color:#fff} .own-out{border:1px dashed var(--ink-3);color:var(--ink-2)}
.kc-h .nec{margin-left:6px}
.kc dl{grid-template-columns:118px minmax(0,1fr)!important}
.dg .n2.ext rect{stroke-dasharray:5 4}
.reader{grid-template-columns:minmax(0,1fr) minmax(0,1.15fr)!important;gap:44px!important}
.codes{margin:14px 0 4px}
.more2{margin-top:12px}
.kcards{display:grid;gap:10px;margin:8px 0 14px}
.kc{border:1px solid var(--hairline);border-top:3px solid;border-radius:12px;padding:12px 14px;background:var(--canvas)}
.kc-h{display:flex;justify-content:space-between;align-items:center;gap:8px}
.kc-do{margin:6px 0 8px;font-size:14.5px}
.kc dl{margin:0;display:grid;grid-template-columns:96px minmax(0,1fr);gap:4px 10px;font-size:13.5px}
.kc dt{color:var(--ink-2)} .kc dd{margin:0;color:#333}
.nec{font-size:12px;border-radius:999px;padding:1px 9px} .nec-ok{background:var(--k-fs-t);color:var(--k-fs)} .nec-chk{background:#fbe9e5;color:#c13515}
table.cmp{border-collapse:collapse;width:100%;font-size:13.5px;margin:6px 0 14px;display:table}
table.cmp th{text-align:left;font-weight:500;padding:6px 10px 8px 0;border-bottom:1px solid var(--hairline)}
table.cmp td{padding:8px 10px 8px 0;border-bottom:1px solid var(--surface-strong);vertical-align:top}
table.cmp td.rh{color:var(--ink-2);white-space:nowrap}
.wrong{border:1px dashed #c13515;border-radius:12px;padding:12px 14px;margin:12px 0;background:#fffafa}
.wrong-h{display:flex;gap:8px;align-items:center;font-weight:600;font-size:14.5px}
.wrong-h .x{font-size:12px;font-weight:500;color:#c13515;border:1px solid #c13515;border-radius:999px;padding:0 8px}
.wrong pre{background:#fbeeee;border-radius:8px;padding:8px 10px;margin:8px 0 4px;font-size:12px;overflow-x:auto}
.wrong-cap{margin:0 0 6px;font-size:12px;color:var(--ink-2)}
.wrong ul{margin:0;padding-left:18px;font-size:13.5px;display:grid;gap:3px}
:root{--k-agent:#b45309;--k-fs:#4d7c0f;--k-core:#1d4ed8;--k-d:#6d28d9;--k-client:#0e7490;--k-user:#e31c5f;
--k-agent-t:#fdf3e7;--k-fs-t:#f1f6e8;--k-core-t:#eef3fd;--k-d-t:#f4effc;--k-client-t:#e9f5f7;--k-user-t:#fff0f3}
.k{font-weight:500;border-bottom:2px solid;padding:0 1px}
.k-agent{color:var(--k-agent);border-color:var(--k-agent-t)} .k-fs{color:var(--k-fs);border-color:var(--k-fs-t)} .k-core{color:var(--k-core);border-color:var(--k-core-t)}
.k-d{color:var(--k-d);border-color:var(--k-d-t)} .k-client{color:var(--k-client);border-color:var(--k-client-t)} .k-user{color:var(--k-user);border-color:var(--k-user-t)}
pre .k{border-bottom:0}
.legend{display:flex;flex-wrap:wrap;gap:8px 14px;font-size:13.5px;margin:6px 0 0}
.legend span.k{border-bottom-width:3px}
.dg .k-agent-fill rect{fill:var(--k-agent-t);stroke:var(--k-agent)} .dg .k-fs-fill rect{fill:var(--k-fs-t);stroke:var(--k-fs)} .dg .k-core-fill rect{fill:var(--k-core-t);stroke:var(--k-core)}
.dg .k-d-fill rect{fill:var(--k-d-t);stroke:var(--k-d)} .dg .k-client-fill rect{fill:var(--k-client-t);stroke:var(--k-client)} .dg .k-user-fill rect{fill:var(--k-user-t);stroke:var(--k-user)}
.dg rect.lane{stroke-width:1.4} .dg rect.k-agent-fill{fill:var(--k-agent-t);stroke:var(--k-agent)} .dg rect.k-fs-fill{fill:var(--k-fs-t);stroke:var(--k-fs)} .dg rect.k-core-fill{fill:var(--k-core-t);stroke:var(--k-core)} .dg rect.k-d-fill{fill:var(--k-d-t);stroke:var(--k-d)} .dg rect.k-client-fill{fill:var(--k-client-t);stroke:var(--k-client)} .dg rect.k-user-fill{fill:var(--k-user-t);stroke:var(--k-user)}
.dg .lt{font-size:13.5px;font-weight:500;fill:var(--ink)}
.dg .n2 rect{stroke-width:1.6} .dg .n2 .t{fill:var(--ink);font-size:13px;font-weight:500} .dg .n2 .s{fill:var(--ink-2);font-size:11px}
.dg .n2.on rect{stroke-width:3} .dg .n2.dim{opacity:.35}
.dg rect.act{stroke-width:1.3;opacity:.55} .dg rect.act.on{opacity:1;stroke-width:2.6} .dg rect.act.done{opacity:.8} .dg rect.act.todo{opacity:.25}
.dg .al{font-size:12.5px;fill:var(--ink)} .dg .al.todo{fill:var(--ink-3)} .dg .al.on{font-weight:600}
.dg .ml{font-size:12.5px;fill:var(--ink-2)} .dg .ml.on{fill:var(--accent-ink);font-weight:500} .dg .ml.todo{fill:var(--ink-3)}
.dg .e.todo{stroke:var(--hairline)} .dg .e.err.on,.dg .e.err.done{stroke:#c13515} .dg .act.err{stroke:#c13515!important}
.dg .tm{font-size:12px;fill:var(--ink-2);font-family:var(--mono)} .dg .tm.on{fill:var(--accent-ink)}
.cx{border-radius:12px;background:var(--surface);margin:0 0 12px;overflow:hidden;border-top:3px solid}
.k-agent-b{border-color:var(--k-agent)} .k-fs-b{border-color:var(--k-fs)} .k-core-b{border-color:var(--k-core)} .k-d-b{border-color:var(--k-d)} .k-client-b{border-color:var(--k-client)} .k-user-b{border-color:var(--k-user)}
.codehead{display:flex;gap:8px;align-items:center;padding:8px 12px 0;font-size:12px;font-family:var(--mono);color:var(--ink-2)}
.codehead .dot{width:8px;height:8px;border-radius:50%;flex:none}
.k-agent-bg{background:var(--k-agent)} .k-fs-bg{background:var(--k-fs)} .k-core-bg{background:var(--k-core)} .k-d-bg{background:var(--k-d)} .k-client-bg{background:var(--k-client)} .k-user-bg{background:var(--k-user)}
.codehead .path{color:var(--ink)} .codehead .who{margin-left:auto;font-family:var(--jost)}
.codenote{margin:6px 12px 0;font-size:12.5px;color:var(--ink-2)}
.cx pre{padding:8px 12px 12px;white-space:pre;overflow-x:auto}
.stage .vis{display:none} .stage .vis.on{display:block} .stage .vis:empty{display:none!important}
.tree{background:var(--surface);border-radius:12px;padding:12px 14px;font-size:12.5px;line-height:1.75;overflow-x:auto}
.tree .tc{color:var(--ink-2)}
.lead2{display:none}
.review{padding:20px 0 40px}
.rlead{max-width:860px;color:#333;margin:0 0 14px}
.rfilter{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.rfilter button{border:1px solid var(--hairline);background:var(--canvas);border-radius:999px;min-height:32px;padding:0 13px;font-size:13.5px}
.rfilter button[aria-pressed="true"]{background:var(--ink);color:#fff;border-color:var(--ink)}
.tablewrap{overflow-x:auto}
table.rv{border-collapse:collapse;width:100%;font-size:14px;min-width:980px}
table.rv th{font-weight:500;text-align:left;color:var(--ink-2);font-size:12.5px;border-bottom:1px solid var(--hairline);padding:8px 12px 8px 0}
table.rv td{border-bottom:1px solid var(--surface-strong);padding:12px 12px 12px 0;vertical-align:top}
table.rv tr.rv-bad td:first-child{box-shadow:inset 3px 0 0 #c13515;padding-left:10px}
table.rv td:first-child{padding-left:10px}
.tag{font-size:12px;border:1px solid var(--hairline);border-radius:999px;padding:1px 9px;white-space:nowrap}
.who2{margin-top:4px;font-size:12.5px}
.ev{font-size:12px;border-radius:999px;padding:1px 9px;white-space:nowrap;font-weight:500}
.ev-ok{background:var(--k-fs-t);color:var(--k-fs)} .ev-user{background:var(--k-user-t);color:var(--k-user)} .ev-mid{background:var(--k-core-t);color:var(--k-core)} .ev-bad{background:#fbe9e5;color:#c13515}
.sm{font-size:13.5px;color:#333;margin-top:4px} .mono{font-family:var(--mono);font-size:12px}
.jump{font-size:13px;white-space:nowrap}
.apx{border-top:1px solid var(--hairline);padding:10px 0} .apx summary{cursor:pointer;font-weight:500}
.apx > div{padding:10px 0;font-size:14px;overflow-x:auto} .apx table{border-collapse:collapse;font-size:13px} .apx td,.apx th{border-bottom:1px solid var(--surface-strong);padding:6px 10px 6px 0;text-align:left;vertical-align:top} .apx pre{background:var(--surface);border-radius:10px;padding:10px 12px;font-size:12px}
@media (max-width:900px){.reader{grid-template-columns:1fr!important}.inl.vis-inl{display:block}}
'''
JS=D.JS.replace("C=[].slice.call(document.querySelectorAll('.codepane .code'))","C=[].slice.call(document.querySelectorAll('.codepane .code1'))")
JS=JS.replace("V.forEach(function(v,k){v.classList.toggle('on',k===i)});C.forEach(function(c,k){c.classList.toggle('on',k===i)});",
 "V.forEach(function(v){v.classList.toggle('on',+v.dataset.v===+scenes[i].dataset.i)});C.forEach(function(c){c.classList.toggle('on',+c.dataset.c===+scenes[i].dataset.i)});")
JS=JS.replace("cap.textContent=","if(cap)cap.textContent=")
JS=JS.replace("h3 span:last-child",".st span:last-child")
JS=JS.replace("var cap=document.getElementById('vcap')","var cap=null")
JS+='''
(function(){var bs=[].slice.call(document.querySelectorAll('.rfilter button')),rows=[].slice.call(document.querySelectorAll('table.rv tbody tr'));
bs.forEach(function(b){b.onclick=function(){bs.forEach(function(x){x.setAttribute('aria-pressed',x===b)});var f=b.dataset.f;
rows.forEach(function(r){r.hidden=!(f==='all'||r.classList.contains('rv-'+f))});};});})();
'''
legend=''.join(k(key) for key in K)
dash=''.join(f'<a href="#{a}" data-sec="{a}"><i></i><span>{t}</span></a>' for a,t in SECS)
HTML=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Alto Rooms v1 스펙 이해물: 관심사, 아키텍처, 실제 코드로 따라가는 데이터 흐름과 에러 흐름, 가정·결정 리뷰">
<meta name="rooms:created" content="2026-10-05T18:30:00+09:00"><meta name="rooms:machine" content="MacBook-Pro">
<title>Alto Rooms v1 스펙 E</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Jost:wght@400;500;600&display=swap">
<style>{CSS}</style></head><body data-depth="all">
<div class="top"><div class="top-in"><span class="mark">Rooms <span>spec</span></span><span class="where" id="where"></span><span class="sp"></span>
</div><div class="prog" id="prog"></div></div>
<nav class="toc" aria-label="목차">{dash}</nav>
<div class="wrap">
<header class="cover" id="a0"><div class="kick">Spec · Alto Rooms v1</div><h1>폴더에 넣기만 하면,<br>방에서 훑고 Journal에서 이해한다</h1>
<div class="meta">spec · 10월 5일 · Plan 1 코드 기준 (7ca19da)</div>
<p class="l30">에이전트가 만든 HTML 아티팩트가 claude.ai, 로컬 폴더, 세션마다 흩어져 있다. Rooms는 <b>폴더 규칙 하나</b>로 모으고, 방(주제)과 Journal(시간) 두 축으로 보여준다. 코어는 어떤 에이전트·스킬·UI와도 결합하지 않는다.</p>
<div class="legend">그림의 색 = 관심사 · 실선 = 우리가 만드는 것 · 점선 = 바깥(계약으로만 만남) · 빨간 실 = 지금 보는 단계</div></header>
<section class="overview"><div><div class="kick">3분 · 누가 무엇을 하나</div><p>{k("agent")}는 파일을 쓰기만 하고, {k("core")}가 규칙으로 읽어 색인과 이벤트를 만들고, {k("d")}가 /v1로 내보내고, {k("client")}가 그린다. {k("user")}는 방 이름, 연결할 폴더, 노트만 정한다.</p><p>글을 읽으면 오른쪽 그림이 장면마다 바뀐다. 핵심 흐름과 에러 흐름에는 실제 코드가 본문 안에 들어 있다.</p></div><div>{MAP_E()}</div></section>
{reader(['a1','a2','a3'])}
{REVIEW}
{reader(['a5'])}
<section class="appendix" id="a6"><div class="secHead"><div class="n">부록</div><h2>Seam · Contract 전문</h2></div>{APPX}</section>
<footer>원문 스펙 ~/personal/alto-rooms/docs/superpowers/specs/2026-10-05-alto-rooms-v1-spec.html · 코드 발췌는 alto-rooms 7ca19da와 alto-rooms-plan2(진행 중)에서 그대로 · 그림과 요지는 재구성 · Claude Code가 썼습니다</footer>
</div>
<script>{JS}</script></body></html>'''
open('rooms-e.html','w').write(HTML); print('ok',len(S),os.path.getsize('rooms-e.html'))
