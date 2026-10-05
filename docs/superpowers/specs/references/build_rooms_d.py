import json, re, os, html as H
os.chdir(os.path.dirname(os.path.abspath(__file__)))
BL=json.load(open('rooms-blocks.json'))
from html.parser import HTMLParser
VOID={'br','img','hr','meta','input','link','wbr','col','source'}
class _Bal(HTMLParser):
    def __init__(s): super().__init__(convert_charrefs=False); s.out=[]; s.st=[]
    def handle_starttag(s,t,a):
        s.out.append(s.get_starttag_text())
        if t not in VOID: s.st.append(t)
    def handle_startendtag(s,t,a): s.out.append(s.get_starttag_text())
    def handle_endtag(s,t):
        if t in s.st:
            while s.st:
                x=s.st.pop(); s.out.append(f'</{x}>')
                if x==t: break
    def handle_data(s,d): s.out.append(d)
    def handle_entityref(s,n): s.out.append(f'&{n};')
    def handle_charref(s,n): s.out.append(f'&#{n};')
def balance(h):
    p=_Bal(); p.feed(h); p.close()
    return ''.join(p.out)+''.join(f'</{x}>' for x in reversed(p.st))

def blk(i, drop_svg=True):
    h=BL[i]['html']
    if drop_svg: h=re.sub(r'<svg.*?</svg>','',h,flags=re.S)
    return balance(h)
def seams():
    h=BL[24]['html']
    return re.findall(r'(<div class="seam".*?)(?=<div class="seam"|$)',h,re.S)
SEAMS=seams()
def seam_parts(i):
    h=SEAMS[i]
    title=re.sub(r'<[^>]+>','',re.search(r'class="seam-title">(.*?)</div>',h,re.S).group(1)).strip()
    sub=re.sub(r'<[^>]+>','',re.search(r'class="seam-sub">(.*?)</div>',h,re.S).group(1)).strip()
    pres=re.findall(r'<pre.*?</pre>',h,re.S)
    heads=re.findall(r'<h5>(.*?)</h5>',h,re.S)
    table=re.findall(r'<table.*?</table>',h,re.S)
    return title,sub,pres,heads,table

# ---------------- SVG kit (inline, token classes) ----------------
def svg(w,h,body,label):
    return f'<svg class="dg" viewBox="0 0 {w} {h}" role="img" aria-label="{H.escape(label)}"><defs><marker id="ar" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="ah"/></marker><marker id="arh" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="ahh"/></marker></defs>{body}</svg>'
def node(x,y,w,h,t,sub='',st='',dash=False,shape='rect'):
    cls=f'n {st}'+(' dash' if dash else '')
    r=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/>' if shape=='rect' else f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}"/>'
    ty=y+h/2+(-2 if sub else 5)
    s=f'<g class="{cls}">{r}<text x="{x+w/2}" y="{ty}" class="t" text-anchor="middle">{t}</text>'
    if sub: s+=f'<text x="{x+w/2}" y="{ty+16}" class="s" text-anchor="middle">{sub}</text>'
    return s+'</g>'
def edge(d,st='',label='',lx=0,ly=0,dash=False):
    m='url(#arh)' if st=='on' else 'url(#ar)'
    s=f'<path class="e {st}{" dash" if dash else ""}" d="{d}" marker-end="{m}"/>'
    if label: s+=f'<text x="{lx}" y="{ly}" class="el {st}">{label}</text>'
    return s
def note(x,y,t,cls='s',anchor='middle'):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{t}</text>'

def MAP(hn=(),he=(),dim=True,cap='시스템 지도'):
    def ns(k): return 'on' if k in hn else ('' if not dim or not hn and not he else 'dim')
    def es(k): return 'on' if k in he else ('' if not dim or not hn and not he else 'dim')
    b=node(10,150,120,56,'Producer','Claude Code · Codex…',ns('prod'))
    b+=node(175,150,130,56,'폴더','~/rooms · linked',ns('folder'))
    b+=node(350,150,130,56,'RoomsCore','인덱스 · 감시',ns('core'))
    b+=node(350,250,130,46,'roomsd','/v1 HTTP+SSE',ns('roomsd'))
    b+=node(540,190,120,40,'데스크탑',' ',ns('desk'))+node(540,240,120,40,'원격 웹','',ns('web'))+node(540,290,120,40,'제3자 UI','',ns('third'))
    b+=node(350,40,130,50,'사용자 에이전트','v2',ns('agent'),dash=True)
    b+=edge('M130 178 H172',es('S1'),'S1',151,170)+edge('M305 178 H347',es('S2'),'S2',326,170)
    b+=edge('M415 206 V247',es('core-roomsd'))
    b+=edge('M480 273 C510 273 510 210 537 210',es('S3'),'S3',516,236)+edge('M480 273 L537 260',es('S3'))+edge('M480 273 C510 273 510 310 537 310',es('S3'))
    b+=edge('M415 150 V93',es('S4'),'S4 (v2)',452,124,dash=True)+edge('M350 65 C240 65 240 120 240 147',es('S4back'),'결과는 다시 폴더로',250,58,dash=True)
    return svg(680,345,b,cap)

def REL():
    b=f'<rect x="10" y="10" width="420" height="250" rx="12" class="grp"/>'+note(24,32,'Home  ~/rooms','gl','start')
    b+=node(30,50,170,70,'Room','owned · linked','on')+node(30,150,170,46,'Artifact (.html)','')
    b+=node(230,50,180,70,'Journal day','journal/YYYY-MM-DD','')+node(230,150,85,46,'Artifact','Dream 등')+node(325,150,85,46,'Note','.md · 나')
    b+=edge('M115 120 V147')+edge('M272 120 V147')+edge('M367 120 V147')
    b+=edge('M200 173 C215 173 215 215 230 215 H272',dash=True)+note(250,235,'그날 생긴 것은 날짜로 조회 (복사 없음)','s')
    b+=node(30,210,170,40,'.rooms/','state.json · index.sqlite','dim')
    b+=node(470,40,150,50,'Producer','HTML을 씀')+node(470,130,150,50,'roomsd','코어 · 인덱스 · 감시')+node(470,220,150,50,'Client','데스크탑 · 웹 · 제3자')
    b+=edge('M470 65 H434','', 'S1',452,58)+edge('M434 155 H467','', 'S2',452,148)+edge('M545 180 V217','', 'S3 /v1',580,202)
    return svg(640,275,b,'용어 관계 맵')

def SCATTER():
    b=''
    srcs=[('claude.ai','Artifacts'),('로컬 폴더','docs/…/specs'),('세션 폴더','sessions/*/artifacts'),('대시보드','66개 중 56개 "기타"')]
    for i,(t,s) in enumerate(srcs): b+=node(20,20+i*68,170,52,t,s,'dim')
    b+=node(400,120,200,70,'Home ~/rooms','폴더에 넣기만 하면','on')
    for i in range(4): b+=edge(f'M190 {46+i*68} C300 {46+i*68} 300 155 397 155','on' if i==1 else '')
    b+=note(300,300,'등록 · 설치 없이, 쓰기만 하면 모인다','s')
    return svg(620,310,b,'흩어진 아티팩트가 한곳으로')

def USMAP():
    us=[('US-1','HTML을 쓰면 바로 뜬다',1),('US-2','방 만들기 · 이름 바꾸기',2),('US-3','기존 폴더 연결',2),('US-4','가로 띠 · 확대',1),('US-5','Journal 하루',3),('US-6','원격 읽기 전용',4),('US-8','온보딩 14일',5),('US-7','제3자 UI',0)]
    fl=['S3 프로토콜','흐름 1 수집','흐름 2 방','흐름 3 Journal','흐름 4 원격','흐름 5 온보딩']
    b=''
    for i,f in enumerate(fl): b+=node(430,14+i*52,190,40,f,'',)
    for i,(k,t,f) in enumerate(us):
        y=14+i*40; b+=f'<text x="14" y="{y+20}" class="t" text-anchor="start">{k}</text><text x="70" y="{y+20}" class="s" text-anchor="start">{t}</text>'
        b+=edge(f'M260 {y+16} C340 {y+16} 340 {34+f*52} 427 {34+f*52}')
    return svg(640,340,b,'사용자 이야기와 흐름')

def STATE():
    b=node(40,70,130,48,'indexed','','on')+node(270,70,130,48,'updated','')+node(500,70,120,48,'removed','','dim')
    b+=edge('M10 94 H37','on','add',22,86)
    b+=edge('M170 88 H267','','change',218,80)+edge('M267 104 H173','','change',218,124)
    b+=edge('M170 94 C300 20 420 20 497 80','','unlink',335,32)+edge('M400 94 H497','','unlink · 무시 규칙',450,86)
    b+=note(330,170,'removed는 다시 add되면 새로 indexed (ArtifactId는 roomId + relPath)','s')
    return svg(640,190,b,'아티팩트 수명')

def CREATED(step=None):
    rows=[('rooms:created 메타','producer가 적었으면 이것이 이긴다'),('저장된 첫 발견 시각','index.sqlite, ArtifactId 기준'),('birthtime','첫 발견 때만 · 링크는 대상 기준'),('mtime','마지막 대체')]
    b=''
    for i,(t,s) in enumerate(rows):
        st='on' if step==i else ''
        b+=node(40,20+i*70,280,52,f'{i+1}. {t}',s,st)
        if i<3: b+=edge(f'M180 {72+i*70} V{87+i*70}','', '없으면',214,82+i*70)
    b+=node(400,115,200,60,'createdAt','이후 고정','on')+edge('M320 46 C370 46 370 140 397 140','on')
    b+=note(500,215,'Journal day = createdAt의 로컬 날짜','s')+note(500,235,'재시작 · rename · 동기화 후에도 불변','s')
    return svg(640,310,b,'createdAt 우선순위')

def PIPE(step):
    names=[('파일 이벤트','notify'),('무시 규칙','ignore'),('메타 추출','lol_html 64KB'),('인덱스 갱신','index.sqlite'),('SSE 이벤트','/v1/events')]
    b=''
    for i,(t,s) in enumerate(names):
        st='on' if i==step else ('done' if i<step else '')
        b+=node(10+i*126,40,112,56,t,s,st)
        if i<4: b+=edge(f'M{122+i*126} 68 H{133+i*126}','on' if i==step else ('done' if i<step else ''))
    # timing ruler
    b+='<line x1="10" y1="160" x2="630" y2="160" class="rule"/>'
    for x,t in [(12,'0 쓰기'),(150,'300ms 디바운스'),(330,'크기 안정 확인'),(628,'≤ 2초 카드')]:
        b+=f'<line x1="{x}" y1="154" x2="{x}" y2="166" class="rule"/>'+note(x,186,t,'s','start' if x==12 else 'end' if x==628 else 'middle')
    b+=f'<rect x="10" y="156" width="{min(620,(step+1)*124)}" height="8" rx="4" class="prog"/>'
    return svg(640,200,b,'아티팩트 수집 파이프라인')

def ROOMOPS(which=None):
    lanes=[('만들기',['이름 검증','mkdir ~/rooms/<slug>','state.json id','room.added']),('연결',['경로 검증 (realpath)','state.json {id,path,name}','스캔','room.added']),('이름 바꾸기',['owned: 폴더 rename','linked: 표시 이름만','감시 이벤트 억제','room.updated 1회'])]
    b=''
    for li,(t,steps) in enumerate(lanes):
        y=20+li*95; st='on' if which==li else ''
        b+=f'<text x="12" y="{y+30}" class="t {st}" text-anchor="start">{t}</text>'
        for si,s in enumerate(steps):
            b+=node(110+si*132,y+8,120,40,s,'',st if si<4 else '')
            if si<3: b+=edge(f'M{230+si*132} {y+28} H{239+si*132}',st)
    b+=note(330,305,'linked 폴더 안에는 어떤 파일도 쓰지 않는다','s')
    return svg(660,315,b,'방 만들기 · 연결 · 이름 바꾸기')

def JOURNAL():
    b=node(20,20,210,52,'journal/2026-10-05/*.html','Dream 등','on')
    b+=node(20,95,210,52,'모든 방의 아티팩트','createdAt 날짜 == 그날')+node(20,170,210,52,'journal/2026-10-05/*.md','노트 · 나')
    b+=node(300,95,140,52,'realpath 중복 제거','')+node(500,95,120,52,'JournalDay','artifacts · notes','on')
    b+=edge('M230 46 C265 46 265 121 297 121','on')+edge('M230 121 H297')+edge('M440 121 H497','on')+edge('M230 196 C420 196 460 160 520 150')
    b+=note(320,260,'복사하지 않고 날짜로 조회한다 · 폴더가 없어도 빈 day','s')
    return svg(640,280,b,'Journal day 구성')

def REMOTE():
    b=node(20,40,160,60,'데스크탑 앱','Tauri · 토큰 보유','on')+node(20,170,160,60,'다른 기기','Tailscale','')+node(20,280,160,50,'아티팩트 JS','불투명 origin','dim')
    b+=node(260,40,170,60,'4317 API','loopback · Host · Origin · Bearer','on')+node(260,170,170,60,'4319 원격 리스너','GET만 등록','')+node(260,280,170,50,'4318 파일 origin','CSP sandbox','')
    b+=node(500,150,120,60,'RoomsCore','')
    b+=edge('M180 70 H257','on','쓰기 OK',218,62)+edge('M180 200 H257','','GET만',218,192)+edge('M180 305 H257','','API 호출 불가',218,297,dash=True)
    b+=edge('M430 70 C470 70 470 170 497 175','on')+edge('M430 200 H497')
    b+=note(330,140,'원격에서 쓰기 → 403 read_only (경로 자체가 없음)','s')
    return svg(640,345,b,'리스너 세 개')

def ONBOARD(step):
    steps=[('사용자','한 줄 붙여넣기'),('에이전트','ONBOARD.md 읽기 · 스킬 설치'),('에이전트','jsonl에서 14일 .html 경로'),('에이전트','방 제안 → 사용자 확인 1회'),('에이전트','방 폴더 + 파일 링크 · 확신 없으면 inbox'),('Rooms','흐름 1로 카드가 뜬다')]
    b=''
    for i,(who,t) in enumerate(steps):
        st='on' if i==step else ('done' if i<step else '')
        y=12+i*52
        b+=f'<text x="14" y="{y+26}" class="s" text-anchor="start">{who}</text>'+node(100,y,420,40,t,'',st)
        if i<5: b+=edge(f'M310 {y+40} V{y+50}','on' if i==step else '')
    b+=note(580,170,'Rooms 코어는','s')+note(580,188,'스킬을 모른다','s')
    return svg(640,330,b,'에이전트 온보딩')

def SSE(step):
    b='<line x1="120" y1="30" x2="120" y2="300" class="life"/><line x1="500" y1="30" x2="500" y2="300" class="life"/>'
    b+=note(120,20,'Client','t')+note(500,20,'roomsd','t')
    msgs=[(60,'① SSE 연결 → 이벤트 버퍼링',120,500),(110,'② GET 스냅샷',120,500),(140,'X-Rooms-Seq: 41',500,120),(190,'버퍼: 40 · 41 · 42 · 43',None,None),(240,'③ seq ≤ 41 버림',None,None),(280,'④ 42 · 43 id 기준 upsert',None,None)]
    for i,(y,t,a,c) in enumerate(msgs):
        k=[0,1,1,2,3,4][i]; st='on' if k==step else ('done' if k<step else '')
        if a: b+=edge(f'M{a} {y} H{c+(-4 if c>a else 4)}',st)+note((a+c)/2,y-8,t,'el '+st)
        else: b+=f'<rect x="140" y="{y-20}" width="200" height="30" rx="8" class="box {st}"/>'+note(240,y,t,'el '+st)
    return svg(640,310,b,'SSE 재연결 알고리즘')

def ERR():
    b=node(30,30,150,50,'시작','전체 백필 · 워터마크','on')+node(250,30,150,50,'감시','300ms 디바운스')+node(470,30,150,50,'오버플로','방 단위 재스캔')
    b+=edge('M180 55 H247','on')+edge('M400 55 H467')+edge('M545 80 C545 140 325 140 325 83','', 'resync',435,132)
    b+=node(30,190,170,50,'index.sqlite 깨짐','새로 만들고 전체 백필','dim')+node(250,190,170,50,'잃는 것','첫 발견 시각만','')
    b+=node(470,190,150,50,'노트 저장 실패','1s · 2s · 4s · 3회')+edge('M200 215 H247')
    b+=note(320,290,'파일이 진실이므로 색인은 언제든 재스캔으로 복구된다','s')
    return svg(640,305,b,'복구 정책')

def ARCH(hl=()):
    st=lambda k:'on' if k in hl else ''
    b=node(20,20,180,48,'rooms-protocol','타입의 단일 정의',st('p'))
    b+=node(20,110,180,48,'rooms-core','폴더 규칙 · 색인',st('c'))+node(20,200,180,48,'roomsd','axum HTTP+SSE',st('d'))
    b+=node(280,20,170,48,'protocol-ts','생성된 TS 타입',st('ts'))+node(280,140,170,48,'apps/desktop','Tauri + React',st('desk'))+node(280,220,170,48,'apps/web','원격 읽기 전용',st('web'))
    b+=edge('M110 107 V71')+edge('M110 197 V161')+edge('M200 44 H277','', 'ts-rs',238,36)+edge('M365 137 V71')+edge('M450 244 C490 244 490 50 453 44')
    b+=node(500,110,120,60,'roomsd 프로세스','사이드카 · 런타임','dim',dash=True)+edge('M450 164 H497',dash=True)
    b+=note(320,300,'앱은 생성된 protocol-ts만 의존 → 코어에 닿는 길은 프로토콜뿐','s')
    return svg(640,315,b,'패키지 의존')

def TYPES():
    b=node(20,30,130,48,'Room','id · kind · status','on')+node(220,30,150,48,'Artifact','id · createdAt · source')+node(440,30,170,48,'JournalDay','artifacts · notes')
    b+=node(440,140,170,48,'Note','author: me')+node(220,140,150,48,'RoomsEvent','seq + type')
    b+=edge('M150 54 H217','', '1 : n',184,46)+edge('M370 54 H437','', '날짜로',404,46)+edge('M525 78 V137')+edge('M295 137 V81',dash=True)
    b+=note(320,240,'ArtifactId = sha1(roomId:relPath) 앞 16자 · 이동하면 새 id','s')
    return svg(640,260,b,'값 타입')

def E2E():
    b='<line x1="20" y1="40" x2="620" y2="40" class="rule"/>'
    for x,t in [(90,'오전'),(310,'오후'),(530,'밤')]: b+=note(x,28,t,'t')
    b+=node(20,60,150,56,'Codex','team/…/benchmark.html')+node(240,60,150,56,'Claude Code','pi-plan.html')+node(460,60,160,56,'dream 스킬','journal/…/dream.html')
    b+=node(20,180,150,50,'팀-리서치 띠','+1 · 팀 폴더엔 안 씀','on')+node(240,180,150,50,'브라우저-하네스 띠','+1 · 새 점','on')+node(460,180,160,50,'Journal 10/5','Dream · benchmark · pi-plan','on')
    b+=edge('M95 116 V177','on')+edge('M315 116 V177','on')+edge('M540 116 V177','on')+edge('M170 205 C300 260 420 250 460 215','',dash=True)+edge('M390 205 H457','',dash=True)
    return svg(640,270,b,'하루 시나리오')

def TEST():
    rows=[('Unit (core)','cargo test','규칙 · 메타 fallback · 슬러그'),('Integration (core)','tempfile','이벤트 · 색인 · 백필 · linked 무쓰기'),('Contract (protocol)','insta','JSON Schema · 원격 쓰기 없음'),('UI','Playwright','만들기 · 이름 · ⌘B · 확대'),('E2E (manual)','curl','§8 시나리오 · 제3자 흉내')]
    b=''
    for i,(t,tool,s) in enumerate(rows):
        w=600-i*70; x=20+i*35
        b+=f'<g class="n"><rect x="{x}" y="{250-i*52}" width="{w}" height="44" rx="8"/><text x="{x+14}" y="{250-i*52+20}" class="t" text-anchor="start">{t} · {tool}</text><text x="{x+14}" y="{250-i*52+36}" class="s" text-anchor="start">{s}</text></g>'
    return svg(640,305,b,'테스트 층')

# ---------------- pseudo code (설명용) ----------------
PSEUDO_CLASSIFY='''// 설명용 의사 코드 — 실제 코드는 rooms-core
fn classify(path) -> Kind {
  if ignored(path)             { return Ignore }   // 숨김 · node_modules · .gitignore · .roomsignore
  if is_symlink(path) {
    let t = target(path)?      // 깨진 링크면 Ignore
    if is_dir(t)               { return Ignore }   // 디렉터리 링크는 따르지 않음
    if !is_html(t)             { return Ignore }
    return Artifact { time_from: t }               // 시각은 대상 기준
  }
  match (dir_of(path), ext(path)) {
    (journal/<date>, "md")     => Note,
    (_, "html" | "htm")        => Artifact,
    (home_root, dir)           => OwnedRoomAdd,     // Finder에서 만든 폴더도 방
    _                          => Ignore,
  }
}'''
PSEUDO_CREATED='''// 설명용 의사 코드
fn created_at(a: &Artifact, db: &Index, fs: &Stat) -> Time {
  if let Some(t) = a.meta.rooms_created { return t }      // 1
  if let Some(t) = db.first_seen(a.id)  { return t }      // 2 (고정)
  let t = fs.birthtime(a.target).or(fs.mtime(a.target));  // 3 → 4
  db.store_first_seen(a.id, t);                           // 첫 발견 때 한 번
  t
}
// Journal day = local_date(created_at)'''
PSEUDO_PIPE='''// 설명용 의사 코드 — 흐름 1
on fs_event(batch) after debounce(300ms):
  for path in batch:
    wait_until size_stable(path, 300ms)
    match classify(path):
      Artifact => {
        let meta = read_head(path, 64KB)      // lol_html, <head>만
        let title = meta.rooms_title ?? meta.title ?? file_stem(path)
        index.upsert(id(room, rel), title, created_at(..))
        events.emit({ seq: next(), type: "artifact.added" | "artifact.updated", artifact })
      }
      Ignore => if index.has(path) { index.remove(..); emit("artifact.removed") }
// 쓰기 시작부터 카드까지 ≤ 2초'''
PSEUDO_JOURNAL='''// 설명용 의사 코드 — 흐름 3
fn journal_day(date) -> JournalDay {
  let a = glob("journal/{date}/*.html")
        + index.artifacts_where(local_date(created_at) == date)
  let artifacts = dedupe_by(a, |x| realpath(x.target))
                    .sort_by(created_at)          // dream.html은 맨 앞
  let notes = glob("journal/{date}/*.md")
  JournalDay { date, artifacts, notes }           // 폴더가 없어도 빈 day
}'''
PSEUDO_SSE='''// 설명용 의사 코드 — 클라이언트 동기화 (Q7)
const buf = [];
const es = new EventSource("/v1/events");
es.onmessage = (m) => buf.push(JSON.parse(m.data));        // ① 먼저 연결, 버퍼링

const res  = await fetch("/v1/rooms");                    // ② 스냅샷
const seq0 = +res.headers.get("X-Rooms-Seq");
state.replace(await res.json());

for (const e of buf) if (e.seq > seq0) apply(e);          // ③ seq ≤ 스냅샷은 버림
es.onmessage = (m) => apply(JSON.parse(m.data));

function apply(e) {                                       // ④ id 기준 멱등
  if (e.type.endsWith(".removed")) state.delete(e);
  else state.upsert(e);
}
// 재연결도 같은 순서. 이벤트 재생은 없음'''
PSEUDO_ROOMS='''// 설명용 의사 코드 — 흐름 2
POST /v1/rooms {name}
  validate(name)            // 1–80자, / \\ : .. 금지, journal 금지
  slug = nfc(name).replace(" ", "-")
  conflict? -> 409 room_exists  // slug를 NFC · 대소문자 무시로 비교
  mkdir(home/slug); state.add({id: nanoid(12), name, inode})
  emit("room.added")

PATCH /v1/rooms/:id {name}
  if room.kind == owned:
    suppress_watch(room) { rename(folder, slug(name)) }
  state.set_name(id, name)  // linked는 표시 이름만
  emit("room.updated")      // artifact 이벤트 없음 (id는 roomId 기준)'''

# ---------------- scenes ----------------
S=[]  # dict(sec, title, lead, body, detail, vis, code)
def sc(sec,title,lead,body='',detail='',vis='',code=''):
    S.append(dict(sec=sec,title=title,lead=lead,body=body,detail=detail,vis=vis,code=code))
def B(*ix): return ''.join(blk(i) for i in ix)
def pre(t,cap=''): return (f'<div class="codecap">{cap}</div>' if cap else '')+'<pre><code>'+H.escape(t)+'</code></pre>'

sc('s0','흩어진 아티팩트를 폴더 하나로 모은다','에이전트가 만든 HTML이 여러 곳에 흩어져 놓치고, 너무 많고, 한곳에서 보기 어렵다. Rooms는 폴더에 넣기만 하면 방별로 훑고 Journal에서 하루를 이해하게 한다.',B(0,1),'',SCATTER())
sc('s0','Rooms는 AI 일을 하지 않는다','Rooms는 저장소와 사람을 위한 이해 공간이다. 아티팩트를 만들지 않고 에이전트를 돌리지 않는다. 바깥과 만나는 곳은 버전 붙은 계약 세 개뿐이다.',B(2),B(3,6),MAP(hn=('folder','core','roomsd'),he=('S1','S3','S4')))
sc('s0','용어 사이의 관계','Home 안에 방이 있고 방 안에 아티팩트가 있다. Journal day는 날짜로 된 방이고, 그날 생긴 아티팩트를 복사하지 않고 조회한다.',blk(5),B(4),REL())
sc('s1','사용자 이야기 8개','폴더에 쓰면 뜬다, 방을 만들고 연결한다, 띠로 훑는다, Journal로 하루를 본다, 원격으로 읽는다, 첫날 온보딩, 제3자 UI.',B(7),B(8),USMAP())
sc('s2','무엇이 아티팩트가 되나','방 폴더(하위 포함)의 .html/.htm만 아티팩트다. 무시 규칙은 결정론적이라 "왜 안 보이지?"에 답할 수 있다.',B(9),B(12),MAP(hn=('folder','core'),he=('S2',)),pre(PSEUDO_CLASSIFY,'파일 이벤트 분류'))
sc('s2','"그날 생긴 것"이 흔들리지 않게','아티팩트의 날짜는 처음 발견할 때 정하고 고정한다. 재시작, 임시 파일 rename, 동기화가 있어도 Journal에서 다른 날로 옮겨 가지 않는다.','<p>우선순위는 <code>rooms:created</code> 메타 → 저장된 첫 발견 시각 → (첫 발견 때만) birthtime → mtime. 링크는 대상 파일의 시각을 쓴다. 그래서 온보딩한 날에 몰리지 않는다.</p>',B(10),CREATED(1),pre(PSEUDO_CREATED,'createdAt 결정'))
sc('s2','아티팩트의 수명','add로 indexed, change로 updated, unlink나 무시 규칙에 걸리면 removed.',blk(11),'',STATE())
sc('s3','파일이 진실이므로 복구는 재스캔이다','색인은 언제든 다시 만들 수 있다. 잃는 것은 첫 발견 시각뿐이고 파일 시각으로 대체된다.',B(14),B(13),ERR())
sc('s4','코어는 별도 프로세스, UI는 프로토콜로만 닿는다','Rust 코어(roomsd)와 Tauri 앱을 프로세스로 나누고, 앱은 생성된 타입만 의존한다. 그래서 UI를 갈아끼울 수 있다.',B(15,19),B(16,20,21,22),ARCH(('c','d','ts')))
sc('s4','기술 선택과 바꿀 시점','모든 선택은 "진실은 파일 하나, UI 교체 가능, 결합도 0"에서 나온다. 대안과 기각 이유를 함께 둔다.','<p>파일 = 진실, SQLite = 다시 만들 수 있는 색인. 프로토콜은 HTTP + JSON + SSE라 curl과 브라우저 EventSource로 바로 붙는다.</p>',B(18),ARCH(('p','c')))
for i in range(4):
    title,sub,pres,heads,table=seam_parts(i)
    code=''.join(pre(H.unescape(re.sub(r'<[^>]+>','',p)),re.sub(r'<[^>]+>','',heads[k]) if k<len(heads) else '') for k,p in enumerate(pres))
    hl={0:dict(hn=('prod','folder'),he=('S1',)),1:dict(hn=('folder','core'),he=('S2',)),2:dict(hn=('roomsd','desk','web','third'),he=('S3',)),3:dict(hn=('core','agent'),he=('S4','S4back'))}[i]
    title=['S1 · Producer → 폴더 (폴더 규칙)','S2 · 폴더 → RoomsCore (해석)','S3 · roomsd → Client (Rooms Protocol v1)','S4 · core → 사용자 에이전트 (Handoff, v2 예약)'][i]
    sub=['아무 에이전트, 스크립트, 사람이 Rooms에 아티팩트를 넣는 유일한 방법. 설치, 등록, 전용 스킬이 없다.','파일 시스템을 도메인 값(Room, Artifact, JournalDay)과 변경 이벤트로 번역한다.','UI를 갈아끼울 수 있게 하는 허리. 데스크탑 앱도 이것만 쓴다.','v1에서는 구현하지 않는다. 형태만 고정해 v2가 데이터 변경 없이 붙게 한다.'][i]
    sc('s5',title,sub,balance(''.join(table)),B(25) if i==3 else '',MAP(**hl),code)
sc('s6','값 타입과 입출력 계약','Room, Artifact, JournalDay, Note, RoomsEvent. 모든 값은 rooms-protocol에서 한 번만 정의하고 TS 타입과 JSON Schema를 생성한다.',B(30),B(27,28,29),TYPES(),re.sub(r'<p[^>]*>.*?</p>','',blk(26),flags=re.S))
sc('s7','핵심 흐름 다섯 개','수집, 방 조작, Journal, 원격, 온보딩. 쓰기는 방 조작과 노트뿐이고 나머지는 읽기다.',B(31),'',MAP())
sc('s7','흐름 1 · 언제 시작하나','시작할 때 전체 스캔 한 번, 이후 파일 이벤트마다. 앱이 꺼져 있던 동안 생긴 파일도 시작 스캔으로 잡힌다.',B(33),'',PIPE(0),pre(PSEUDO_PIPE,'흐름 1'))
for k,(t,l) in enumerate([('무시 규칙을 거른다','기본 목록 + linked의 .gitignore + .roomsignore. 걸리면 카드가 생기지 않는다.'),('앞 64KB에서 메타를 읽는다','lol_html로 <head>만 읽고 멈춘다. 제목은 rooms:title → <title> → 파일 이름.'),('인덱스를 갱신한다','index.sqlite에 upsert. createdAt은 처음 발견할 때 정해지고 고정된다.'),('SSE로 내보낸다','artifact.added에 seq를 붙여 보낸다. 띠 끝에 카드와 새 문서 점이 붙는다.')]):
    sc('s7',f'흐름 1 · {t}',l,'' if k<3 else B(38),B(35,36) if k==1 else (B(37,39) if k==3 else ''),PIPE(k+1),pre(PSEUDO_PIPE,'흐름 1'))
sc('s7','흐름 2 · 방 만들기, 연결, 이름 바꾸기','owned는 폴더 이름을 바꾸고, linked는 표시 이름만 바꾼다. 저장 버튼은 없다.',B(41,42),B(43,44,45,46,47),ROOMOPS(0),pre(PSEUDO_ROOMS,'흐름 2'))
sc('s7','흐름 3 · Journal 하루','그날 journal 폴더의 HTML + 모든 방에서 그날 생긴 아티팩트 + 내 노트. 복사하지 않고 조회한다.',B(49,50),B(51,52,53,54,55),JOURNAL(),pre(PSEUDO_JOURNAL,'흐름 3'))
sc('s7','흐름 4 · 원격은 읽기 전용','원격 리스너(4319)에는 GET 경로만 있다. 검사가 아니라 구조로 쓰기를 막는다.',B(57,58,59,60),B(61,62,63),REMOTE())
for k,l in enumerate(['첫 실행에 방이 없으면 "이 한 줄을 에이전트에게 붙여넣으세요"를 보여준다.','에이전트가 ONBOARD.md를 읽고 rooms 스킬을 자기 스킬 폴더에 설치한다.','대화 기록(jsonl)에서 최근 14일 동안 .html을 쓴 경로를 뽑는다.','주제별 방을 제안하고 사용자가 한 번 확인한다.','원본은 두고 파일 링크만 만든다. 확신 없는 파일은 inbox로.']):
    sc('s7',f'흐름 5 · 온보딩 {k+1}/5',l,B(65,66) if k==0 else '',B(67,68,69,70,71) if k==4 else '',ONBOARD(k))
for k,(t,l) in enumerate([('SSE 먼저 연결','클라이언트는 이벤트 스트림부터 열고 들어오는 이벤트를 버퍼에 쌓는다.'),('스냅샷을 받는다','GET 응답 헤더 X-Rooms-Seq가 그 시점 seq다.'),('버퍼를 맞춘다','버퍼에서 seq가 스냅샷 이하인 것은 이미 반영된 것이라 버린다.'),('나머지를 적용한다','적용은 항상 id 기준 upsert/delete라 두 번 와도 안전하다. 재연결도 같은 순서.')]):
    sc('s7',f'알고리즘 · 재연결해도 이벤트를 잃지 않는다 {k+1}/4' if k==0 else f'알고리즘 · {t}',l,'<p>Senior Q7에서 나온 규칙이다. 이벤트 재생 없이 스냅샷과 seq만으로 맞춘다.</p>' if k==0 else '','',SSE(k+(1 if k>=2 else 0)),pre(PSEUDO_SSE,'클라이언트 동기화'))
sc('s8','하루 시나리오','팀 폴더, 방, 밤 루틴이 각자 파일을 쓰고, Journal 10/5에 모두 모인다. 팀 폴더에는 아무것도 쓰지 않는다.',blk(72),'',E2E())
sc('s9','테스트 층','규칙은 단위 테스트, 이벤트와 색인은 통합 테스트, 프로토콜은 스냅샷, UI는 Playwright.',B(73),'',TEST())
sc('s10','진입점부터 걷기','입구는 세 개다. 폴더, /v1, RoomsCore::open(). 데스크탑 앱조차 /v1만 안다.',B(74,75),B(76),MAP(hn=('folder','roomsd','core'),he=()))
sc('s11','열린 질문','세션 id 채우기, roomsd 상주 방식, Codex 기록 형식, Home 위치 설정, 새 문서 점, linked 재연결 UI.',B(77),'',MAP(hn=('agent',),he=('S4',)))

SECS=[('s0','0 · Overview'),('s1','1 · Requirements'),('s2','2 · 규칙'),('s3','3 · 에러'),('s4','4 · 아키텍처'),('s5','5 · Seams'),('s6','6 · Contracts'),('s7','7 · 핵심 흐름'),('s8','8 · 시나리오'),('s9','9 · 테스트'),('s10','10 · 리뷰'),('s11','11 · 열린 질문')]

CSS='''
:root{--canvas:#ffffff;--surface:#f7f7f7;--surface-strong:#f2f2f2;--hairline:#dddddd;--ink:#222222;--ink-2:#6a6a6a;--ink-3:#929292;
--thread:#ff385c;--accent:#e31c5f;--accent-ink:#c2134f;--accent-soft:#fff0f3;--accent-line:#ffc9d4;
--jost:"Jost","Apple SD Gothic Neo","Pretendard",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--canvas);color:var(--ink);font-family:var(--jost);font-size:15.5px;line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:var(--ink)} code{font-family:var(--mono);font-size:.86em;background:var(--surface);padding:1px 4px;border-radius:4px}
button{font:inherit;color:inherit;cursor:pointer}
:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
[hidden]{display:none!important}
.top{position:sticky;top:0;z-index:30;background:rgba(255,255,255,.9);backdrop-filter:blur(10px);border-bottom:1px solid var(--hairline)}
.top-in{max-width:1560px;margin:0 auto;padding:10px 24px;display:flex;gap:16px;align-items:center}
.top .mark{font-weight:500}.top .mark span{color:var(--accent)}
.top .where{color:var(--ink-2);font-size:13.5px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.top .sp{flex:1}
.seg{display:inline-flex;border:1px solid var(--hairline);border-radius:999px;padding:3px;background:var(--canvas);flex:none}
.seg button{border:0;background:transparent;border-radius:999px;min-height:30px;padding:0 13px;font-size:13.5px;color:var(--ink-2)}
.seg button[aria-pressed="true"]{background:var(--ink);color:#fff}
.prog{position:absolute;left:0;bottom:-1px;height:2px;background:var(--thread);width:0}
/* dash toc */
.toc{position:fixed;left:14px;top:50%;transform:translateY(-50%);z-index:25;display:grid;gap:9px;padding:10px 8px;border-radius:12px}
.toc a{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--ink-2);font-size:13px;height:12px}
.toc a i{display:block;height:2px;width:14px;border-radius:2px;background:var(--hairline);transition:width .2s,background .2s;flex:none}
.toc a span{opacity:0;transform:translateX(-4px);transition:opacity .15s,transform .15s;white-space:nowrap}
.toc a.on i{width:26px;background:var(--thread)} .toc a.on{color:var(--ink)}
.toc:hover{background:rgba(255,255,255,.96);box-shadow:0 6px 16px rgba(0,0,0,.08)}
.toc:hover a span{opacity:1;transform:none}
.toc a:hover i{background:var(--ink)}
@media (max-width:1100px){.toc{display:none}}
/* head */
.wrap{max-width:1560px;margin:0 auto;padding:0 24px 0 64px}
.cover{padding:56px 0 28px;display:grid;gap:14px;max-width:900px}
.kick{font-size:13px;color:var(--accent);font-weight:500}
.cover h1{margin:0;font-size:clamp(34px,4.6vw,54px);font-weight:500;letter-spacing:-.02em;line-height:1.1}
.meta{font-size:13px;color:var(--ink-2)}
.l30{font-size:19px;line-height:1.6;max-width:760px;margin:0}
.l30 b{font-weight:600}
.overview{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);gap:36px;align-items:center;padding:28px 0 48px;border-bottom:1px solid var(--hairline)}
.overview .kick{margin-bottom:6px}
.overview p{margin:0 0 10px;color:var(--ink-2)}
/* reader */
.reader{display:grid;grid-template-columns:minmax(0,.95fr) minmax(0,1.25fr);gap:40px;align-items:start}
body[data-depth="3"] .reader{grid-template-columns:minmax(0,.9fr) minmax(0,1.05fr) minmax(0,.95fr);gap:28px}
.stage,.codepane{position:sticky;top:72px;height:calc(100vh - 96px);display:flex;flex-direction:column;justify-content:center;gap:10px;min-width:0}
.codepane{display:none}
body[data-depth="3"] .codepane{display:flex}
.stage .vis{display:none;border:1px solid var(--hairline);border-radius:14px;padding:16px;background:var(--canvas)}
.stage .vis.on{display:block}
.stage .cap,.codepane .cap{font-size:12.5px;color:var(--ink-2);font-family:var(--mono)}
.codepane .code{display:none;overflow:auto;max-height:100%;border-radius:14px;background:var(--surface);padding:6px 14px}
.codepane .code.on{display:block}
.codepane .none{font-size:13.5px;color:var(--ink-3)}
.secHead{padding:64px 0 6px;border-top:2px solid var(--ink);margin-top:40px}
.secHead:first-child{margin-top:28px}
.secHead .n{font-family:var(--mono);font-size:12.5px;color:var(--accent)}
.secHead h2{margin:4px 0 0;font-size:28px;font-weight:500;letter-spacing:-.01em}
.scene{padding:7vh 0;border-top:1px solid transparent}
.scene + .scene{border-top-color:var(--surface-strong)}
.scene h3{margin:0 0 10px;font-size:21px;font-weight:500;line-height:1.35;letter-spacing:-.01em;display:flex;gap:10px;align-items:baseline}
.scene h3 .no{font-family:var(--mono);font-size:12px;color:var(--ink-3);font-weight:400;flex:none}
.scene.active h3 .no{color:var(--accent)}
.lead{font-size:17px;line-height:1.7;margin:0 0 14px;color:var(--ink)}
.d2,.d3{color:#333}
body[data-depth="1"] .d2,body[data-depth="1"] .d3,body[data-depth="2"] .d3{display:none}
.d3{border-top:1px dashed var(--hairline);margin-top:16px;padding-top:12px}
.d3::before{content:"세부";display:block;font-size:12px;color:var(--ink-2);margin-bottom:6px;font-family:var(--mono)}
.d2 p,.d3 p{margin:0 0 10px}
.d2 ul,.d3 ul,.d2 ol,.d3 ol{padding-left:20px;margin:0 0 12px}
.d2 li,.d3 li{margin:3px 0}
.scene table{border-collapse:collapse;width:100%;font-size:13.5px;margin:10px 0 14px;display:block;overflow-x:auto}
.scene th{font-weight:500;text-align:left;color:var(--ink-2);font-size:12.5px;border-bottom:1px solid var(--hairline);padding:7px 10px 7px 0;white-space:nowrap}
.scene td{border-bottom:1px solid var(--surface-strong);padding:8px 10px 8px 0;vertical-align:top}
.scene .meta,.scene .review-box,.scene .ambiguous{font-size:14px}
.ambiguous{background:var(--accent-soft);border-radius:4px;padding:0 3px}
.review-box{background:var(--surface);border-radius:12px;padding:12px 14px;margin:12px 0}
.review-box h4{margin:0 0 4px;font-size:13px;font-weight:500;color:var(--ink-2)}
.qa{margin:10px 0}.qa .q{font-weight:600}
.scene .flow{display:flex;flex-wrap:wrap;gap:6px}.scene .slot{border:1px solid var(--hairline);border-radius:8px;padding:2px 8px;font-size:13px}
.inl{display:none}
pre{margin:0;font-family:var(--mono);font-size:12.5px;line-height:1.6;white-space:pre;overflow-x:auto;padding:10px 0}
pre code{background:none;padding:0}
.codecap{font-size:12px;color:var(--ink-2);margin-top:8px;font-family:var(--mono)}
.badge{font-size:11px}
/* svg */
svg.dg{width:100%;height:auto;display:block;font-family:var(--jost)}
.dg .n rect,.dg .n ellipse{fill:var(--canvas);stroke:var(--hairline);stroke-width:1.5}
.dg .n .t{fill:var(--ink);font-size:13px;font-weight:500}
.dg .n .s,.dg .s{fill:var(--ink-2);font-size:11px}
.dg .t{fill:var(--ink);font-size:13px;font-weight:500}
.dg .gl{fill:var(--ink-2);font-size:12px}
.dg .n.on rect,.dg .n.on ellipse{fill:var(--accent-soft);stroke:var(--accent);stroke-width:2.2}
.dg .n.on .t{fill:var(--accent-ink)}
.dg .n.done rect{fill:var(--surface-strong);stroke:var(--ink-3)}
.dg .n.dim{opacity:.55}
.dg .n.dash rect{stroke-dasharray:5 4}
.dg .e{fill:none;stroke:var(--ink-3);stroke-width:1.6}
.dg .e.dash{stroke-dasharray:5 5}
.dg .e.on{stroke:var(--thread);stroke-width:2.6;stroke-dasharray:7 5;animation:flowdash .9s linear infinite}
@keyframes flowdash{to{stroke-dashoffset:-12}}
@media (prefers-reduced-motion:reduce){.dg .e.on{animation:none;stroke-dasharray:none}}
.dg .e.done{stroke:var(--ink-2)}
.dg .e.dim{opacity:.3}
.dg .ah{fill:var(--ink-3)} .dg .ahh{fill:var(--thread)}
.dg .el{fill:var(--ink-2);font-size:11.5px;text-anchor:middle;font-family:var(--mono)}
.dg .el.on{fill:var(--accent-ink);font-weight:500}
.dg .grp{fill:none;stroke:var(--hairline);stroke-dasharray:4 4}
.dg .rule{stroke:var(--hairline);stroke-width:2}
.dg .prog{fill:var(--thread)}
.dg .life{stroke:var(--hairline);stroke-width:2;stroke-dasharray:3 5}
.dg .box{fill:var(--surface);stroke:var(--hairline)} .dg .box.on{fill:var(--accent-soft);stroke:var(--accent)}
footer{border-top:1px solid var(--hairline);margin-top:60px;padding:24px 0 80px;color:var(--ink-2);font-size:13px}
@media (max-width:1200px){
  body[data-depth="3"] .reader{grid-template-columns:minmax(0,1fr) minmax(0,1.1fr)}
  body[data-depth="3"] .codepane{display:none}
  body[data-depth="3"] .inl.code-inl{display:block}
}
@media (max-width:900px){
  .wrap{padding:0 16px}
  .reader,body[data-depth="3"] .reader{grid-template-columns:1fr}
  .stage,.codepane{display:none!important}
  .inl.vis-inl{display:block;border:1px solid var(--hairline);border-radius:12px;padding:10px;margin:12px 0}
  body[data-depth="3"] .inl.code-inl{display:block}
  .overview{grid-template-columns:1fr}
  .top .where{display:none}
}
.inl.code-inl{background:var(--surface);border-radius:12px;padding:4px 12px;margin:12px 0;overflow-x:auto}
'''

def scene_html(i,s,no):
    vis_inl=f'<div class="inl vis-inl">{s["vis"]}</div>'
    code_inl=f'<div class="inl code-inl">{s["code"]}</div>' if s['code'] else ''
    body=f'<div class="d2">{s["body"]}</div>' if s['body'] else ''
    det=f'<div class="d3">{s["detail"]}</div>' if s['detail'] else ''
    return f'<section class="scene" data-i="{i}" data-sec="{s["sec"]}"><h3><span class="no">{no}</span><span>{H.escape(s["title"])}</span></h3><p class="lead">{H.escape(s["lead"])}</p>{vis_inl}{body}{det}{code_inl}</section>'

parts=[];cur=None;cnt={}
for i,s in enumerate(S):
    if s['sec']!=cur:
        cur=s['sec']; lab=dict(SECS)[cur]
        parts.append(f'<div class="secHead" id="{cur}"><div class="n">§{cur[1:]}</div><h2>{lab.split(" · ",1)[1]}</h2></div>')
    cnt[cur]=cnt.get(cur,0)+1
    parts.append(scene_html(i,s,f'{cur[1:]}.{cnt[cur]}'))
stage=''.join(f'<div class="vis" data-v="{i}">{s["vis"]}</div>' for i,s in enumerate(S))
codes=''.join(f'<div class="code" data-c="{i}">{s["code"]}</div>' if s['code'] else f'<div class="code" data-c="{i}"><p class="none">이 장면에는 코드가 없습니다.</p></div>' for i,s in enumerate(S))
dash=''.join(f'<a href="#{k}" data-sec="{k}"><i></i><span>{v}</span></a>' for k,v in SECS)
JS='''
(function(){
  var scenes=[].slice.call(document.querySelectorAll('.scene')),V=[].slice.call(document.querySelectorAll('.stage .vis')),C=[].slice.call(document.querySelectorAll('.codepane .code'));
  var cap=document.getElementById('vcap'),where=document.getElementById('where'),D=[].slice.call(document.querySelectorAll('.toc a')),prog=document.getElementById('prog'),cur=-1;
  function set(i){if(i===cur||i<0)return;cur=i;V.forEach(function(v,k){v.classList.toggle('on',k===i)});C.forEach(function(c,k){c.classList.toggle('on',k===i)});
    scenes.forEach(function(s,k){s.classList.toggle('active',k===i)});var s=scenes[i];
    cap.textContent=s.querySelector('.no').textContent+' · '+s.querySelector('h3 span:last-child').textContent;
    where.textContent=s.querySelector('h3 span:last-child').textContent;
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
'''
HTML=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Alto Rooms v1 스펙 이해물: 폴더에 넣기만 하면 방별로 훑고 Journal로 하루를 이해하는 구조, 계약, 핵심 흐름">
<meta name="rooms:created" content="2026-10-05T17:40:00+09:00"><meta name="rooms:machine" content="MacBook-Pro">
<title>Alto Rooms v1 스펙</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Jost:wght@400;500;600&display=swap">
<style>{CSS}</style></head><body data-depth="2">
<div class="top"><div class="top-in"><span class="mark">Rooms <span>spec</span></span><span class="where" id="where"></span><span class="sp"></span>
<div class="seg" role="group" aria-label="추상화 수준"><button type="button" data-depth-set="1" aria-pressed="false">요지</button><button type="button" data-depth-set="2" aria-pressed="true">구조</button><button type="button" data-depth-set="3" aria-pressed="false">세부 + 코드</button></div></div><div class="prog" id="prog"></div></div>
<nav class="toc" aria-label="목차">{dash}</nav>
<div class="wrap">
<header class="cover"><div class="kick">Spec · Alto Rooms v1</div><h1>폴더에 넣기만 하면,<br>방에서 훑고 Journal에서 이해한다</h1>
<div class="meta">spec · 10월 5일 · 12장 · {len(S)}장면</div>
<p class="l30">에이전트가 만든 HTML 아티팩트가 claude.ai, 로컬 폴더, 세션마다 흩어져 있다. Rooms는 <b>폴더 규칙 하나</b>로 모으고, 방(주제)과 Journal(시간) 두 축으로 보여준다. 코어는 어떤 에이전트·스킬·UI와도 결합하지 않는다.</p></header>
<section class="overview"><div><div class="kick">3분 · 시스템 지도</div><p>입구는 세 개다. 들어오는 입구는 폴더(S1), 코어 안의 입구는 <code>RoomsCore::open()</code>, UI의 입구는 Rooms 프로토콜 <code>/v1</code>(S3).</p><p>아래로 내려가면 오른쪽 그림이 장면마다 바뀐다. 위의 <b style="font-weight:500">요지 / 구조 / 세부 + 코드</b>로 추상화 수준을 오갈 수 있다.</p></div><div>{MAP(hn=('folder','core','roomsd'),he=('S1','S2','S3'))}</div></section>
<div class="reader"><div class="scenes">{''.join(parts)}</div>
<aside class="stage">{stage}<div class="cap" id="vcap"></div></aside>
<aside class="codepane"><div class="cap">코드 · 계약</div>{codes}</aside>
</div>
<footer>원문 ~/personal/alto-rooms/docs/superpowers/specs/2026-10-05-alto-rooms-v1-spec.html · 표와 코드는 원문 그대로, 그림과 요지는 재구성 · "설명용 의사 코드"는 실제 코드가 아님 · Claude Code가 썼습니다</footer>
</div>
<script>{JS}</script></body></html>'''
open('rooms-d.html','w').write(HTML); print('ok',len(S),os.path.getsize('rooms-d.html'))
