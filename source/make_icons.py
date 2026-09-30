from PIL import Image, ImageDraw
S=1024
def icon(maskable):
    im=Image.new("RGBA",(S,S),(0,0,0,0)); d=ImageDraw.Draw(im)
    bg=(21,28,40,255)
    if maskable: d.rectangle([0,0,S,S],fill=bg)
    else: d.rounded_rectangle([0,0,S-1,S-1],radius=220,fill=bg)
    k=0.78 if maskable else 1.0   # keep motif inside the maskable safe zone
    c=lambda x,y:(S/2+(x-S/2)*k, S/2+(y-S/2)*k)
    top=c(512,300); kids=[c(262,700),c(512,700),c(762,700)]
    line=(163,171,185,255); w=int(26*k)
    busy=c(512,520)[1]
    d.line([top,(top[0],busy)],fill=line,width=w)
    d.line([(kids[0][0],busy),(kids[2][0],busy)],fill=line,width=w)
    for kx,ky in kids: d.line([(kx,busy),(kx,ky)],fill=line,width=w)
    def dot(p,r,col):
        r*=k; d.ellipse([p[0]-r,p[1]-r,p[0]+r,p[1]+r],fill=col,outline=(21,28,40,255),width=int(14*k))
    dot(top,120,(224,184,74,255))
    for p,col in zip(kids,[(165,123,214,255),(91,155,230,255),(114,182,106,255)]): dot(p,92,col)
    return im
base=icon(False); mask=icon(True)
for n,sz,im in [("icon-192.png",192,base),("icon-512.png",512,base),("icon-maskable-512.png",512,mask),("apple-touch-icon.png",180,mask)]:
    im.resize((sz,sz),Image.LANCZOS).save("site_assets/"+n)
im=base.resize((64,64),Image.LANCZOS); im.save("site_assets/favicon.png")
print("ok")
