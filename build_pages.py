from pathlib import Path
import os, json, html, re, shutil
from urllib.parse import quote, unquote
import xml.etree.ElementTree as ET
import markdown
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'_site'
OWNER=os.environ.get('GITHUB_REPOSITORY','dobjk/aaa').split('/')[0]
REPO=os.environ.get('GITHUB_REPOSITORY','dobjk/aaa').split('/')[1]
BASE=f'https://{OWNER}.github.io/{REPO}'
CSS='''*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#1b263b;font:17px/1.85 system-ui,sans-serif}header{background:#12233c;color:white;padding:25px max(6vw,20px)}header a{color:white;text-decoration:none}main{max-width:1050px;margin:35px auto;padding:0 22px}article,.hero{background:white;border:1px solid #e2e8f0;border-radius:18px;padding:clamp(22px,5vw,55px)}h1{font-size:clamp(26px,4vw,39px);line-height:1.45}h2{margin-top:35px;font-size:25px}a{color:#1366b0;overflow-wrap:anywhere}img{max-width:100%;height:auto;border-radius:10px}article p{overflow-wrap:anywhere}input{width:100%;padding:15px;border:1px solid #b8c8dc;border-radius:10px;font:inherit;margin:15px 0}ul.cards{list-style:none;padding:0;display:grid;gap:12px}.cards li{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:20px}.cards a{text-decoration:none;font-weight:600}footer{padding:30px;text-align:center;color:#58677e;font-size:14px}button{padding:12px 25px;border:0;border-radius:9px;background:#1366b0;color:white;font:inherit;cursor:pointer}.muted{color:#60738c;font-size:14px}pre{overflow:auto}table{border-collapse:collapse}td,th{border:1px solid #ddd;padding:8px}'''
def shell(title,body,url):
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><meta name="description" content="'+html.escape(title,quote=True)+'"><link rel="canonical" href="'+html.escape(url,quote=True)+'"><link rel="stylesheet" href="'+BASE+'/assets/style.css"></head><body><header><a href="'+BASE+'/">AAA · 文章库</a></header><main>'+body+'</main><footer>AAA 文章库 · <a href="'+BASE+'/catalog.html">完整文章目录</a></footer></body></html>'
def convert_link(match):
 owner, repo, path=match.groups()
 if owner.lower()==OWNER.lower() and repo==REPO:
  return BASE+'/'+quote(str(Path(unquote(path)).with_suffix('.html')),safe='/')
 return match.group(0)
def build():
 if OUT.exists():shutil.rmtree(OUT)
 (OUT/'assets').mkdir(parents=True)
 (OUT/'assets/style.css').write_text(CSS,encoding='utf-8')
 entries=[]
 for p in sorted(ROOT.rglob('*.md')):
  rel=p.relative_to(ROOT)
  if any(part.startswith('.') or part=='_site' for part in rel.parts) or p.name in ('PAGES_SETUP.md','README.md'):continue
  text=p.read_text(encoding='utf-8-sig')
  title=next((line[2:].strip() for line in text.splitlines() if line.startswith('# ')),p.stem)
  text=re.sub(r'https://github\.com/([^/]+)/([^/]+)/blob/main/([^\s)<>]+\.md)',convert_link,text)
  url=BASE+'/'+quote(rel.with_suffix('.html').as_posix(),safe='/')
  rendered=markdown.markdown(text,extensions=['tables','fenced_code','sane_lists'])
  dest=OUT/rel.with_suffix('.html');dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_text(shell(title,'<article>'+rendered+'</article>',url),encoding='utf-8')
  entries.append({'title':title,'url':url})
  # Keep local image assets available; remote Baidu images stay at their original URLs.
 for p in ROOT.rglob('*'):
  if p.is_file() and p.suffix.lower() in ('.jpg','.jpeg','.png','.gif','.webp','.svg'):
   rel=p.relative_to(ROOT)
   if any(x.startswith('.') or x=='_site' for x in rel.parts):continue
   dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 cards=''.join('<li><a href="'+html.escape(e['url'],quote=True)+'">'+html.escape(e['title'])+'</a></li>' for e in entries)
 data=json.dumps(entries,ensure_ascii=False).replace('<','\\u003c')
 body='<section class="hero"><p class="muted">AAA / 文章阅读</p><h1>从目录发现下一篇文章</h1><p>共 '+str(len(entries))+' 篇文章。按标题搜索，或浏览完整目录。</p><label for="search">搜索文章标题</label><input id="search" type="search" placeholder="输入游戏名称或关键词"><p id="count" class="muted"></p></section><ul class="cards" id="list">'+''.join(cards.split('</li>')[:30])+'</li></ul><button id="more" type="button">加载更多</button>'
 script='''<script>const data=DATA;let filtered=data,n=30;const list=document.querySelector('#list'),more=document.querySelector('#more');function draw(){list.replaceChildren();for(const item of filtered.slice(0,n)){const li=document.createElement('li'),a=document.createElement('a');a.href=item.url;a.textContent=item.title;li.append(a);list.append(li)}document.querySelector('#count').textContent='找到 '+filtered.length+' 篇 · 已展示 '+Math.min(n,filtered.length)+' 篇';more.hidden=n>=filtered.length}document.querySelector('#search').addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();filtered=data.filter(x=>x.title.toLowerCase().includes(q));n=30;draw()});more.addEventListener('click',()=>{n+=30;draw()});draw()</script>'''.replace('DATA',data)
 (OUT/'index.html').write_text(shell('AAA 文章库',body+script,BASE+'/'),encoding='utf-8')
 (OUT/'catalog.html').write_text(shell('完整文章目录','<h1>完整文章目录</h1><p>'+str(len(entries))+' 篇文章</p><ul class="cards">'+cards+'</ul>',BASE+'/catalog.html'),encoding='utf-8')
 ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns);tree=ET.Element('{'+ns+'}urlset')
 for url in [BASE+'/',BASE+'/catalog.html']+[e['url'] for e in entries]:
  node=ET.SubElement(tree,'{'+ns+'}url');ET.SubElement(node,'{'+ns+'}loc').text=url
 ET.ElementTree(tree).write(OUT/'sitemap.xml',encoding='utf-8',xml_declaration=True)
 (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n',encoding='utf-8')
 (OUT/'.nojekyll').touch()
 print('已构建',len(entries),'篇文章；输出目录:',OUT)
if __name__=='__main__':build()
