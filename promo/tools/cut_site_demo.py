import json,re
m=json.load(open('marks.json')); T0=m['cast_t0_wall']; F=m.get('F',1)
L=open('frames.txt').read().split('\n')
files=[];durs=[]
for i,l in enumerate(L):
    if l.startswith('file') and i+1<len(L) and L[i+1].startswith('duration'):
        files.append(re.search(r"'(.*)'",l).group(1)); durs.append(float(L[i+1].split()[1]))
ts=[];acc=0
for d in durs: ts.append(acc); acc+=d*F          # время «страницы»
c=lambda k:(m[k]-T0)*F
segs=[(c('s1'),c('s5')),(c('s5')+0.55,c('s6')),(c('s6')+0.75,c('end'))]
out=["ffconcat version 1.0"]; total=0
for a,b in segs:
    idx=[i for i,t in enumerate(ts) if a<=t<b]
    for k,i in enumerate(idx):
        d=(ts[idx[k+1]]-ts[i]) if k+1<len(idx) else max(0.03,b-ts[i])
        out+= [f"file '{files[i]}'", f"duration {d:.4f}"]; total+=d
out.append(f"file '{files[idx[-1]]}'")
open('edit.txt','w').write('\n'.join(out)); open('total.txt','w').write(str(total))
print('total',round(total,2),'frames',len(files),'fps≈',round(len(files)/ (acc),1))
