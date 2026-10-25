"""Editable vector manufacturing drawing of NODI-P03, revision A.
Dimensions come from CAD's frozen geometry. Regenerate after CAD and compare
the emitted drawing_geometry_check.json. This is a prototype drawing, not a production release.
"""
from pathlib import Path
import math,json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
F=Path('/usr/share/fonts/truetype/dejavu')
if not F.exists():
 from matplotlib import get_data_path
 F=Path(get_data_path())/'fonts/ttf'
pdfmetrics.registerFont(TTFont('D',str(F/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DB',str(F/'DejaVuSans-Bold.ttf')))
W,H=1190.55,841.89
p=ROOT/'Drawings/NODI-P03_Yoke_RevA.pdf';c=canvas.Canvas(str(p),pagesize=(W,H));c.setTitle('NODI-P03 — Pan-tilt yoke — Rev A');c.setAuthor('David Borsky — AI-assisted engineering study')
BLACK=(.1,.17,.18);GRAY=(.4,.5,.5)
def line(x1,y1,x2,y2,w=.7):c.setLineWidth(w);c.line(x1,y1,x2,y2)
def text(x,y,t,sz=10,bold=False,align='left'):
 c.setFont('DB' if bold else 'D',sz);getattr(c,{'left':'drawString','center':'drawCentredString','right':'drawRightString'}[align])(x,y,str(t))
def arrow(x,y,ang):
 a=math.radians(ang);s=5
 q=c.beginPath();q.moveTo(x,y);q.lineTo(x+s*math.cos(a+.4),y+s*math.sin(a+.4));q.lineTo(x+s*math.cos(a-.4),y+s*math.sin(a-.4));q.close();c.drawPath(q,fill=1)
def hd(x1,x2,y,ya,t,basic=False):
 line(x1,ya,x1,y+5,.35);line(x2,ya,x2,y+5,.35);line(x1,y,x2,y,.45);arrow(x1,y,0);arrow(x2,y,180)
 tw=pdfmetrics.stringWidth(t,'D',10)+8;c.setFillColorRGB(1,1,1);c.rect((x1+x2-tw)/2,y-2,tw,14,fill=1,stroke=basic);c.setFillColorRGB(*BLACK);text((x1+x2)/2,y+1,t,10,align='center')
def vd(y1,y2,x,xa,t,basic=False):
 line(xa,y1,x+5,y1,.35);line(xa,y2,x+5,y2,.35);line(x,y1,x,y2,.45);arrow(x,y1,90);arrow(x,y2,-90)
 c.saveState();c.translate(x-3,(y1+y2)/2);c.rotate(90);tw=pdfmetrics.stringWidth(t,'D',10)+8;c.setFillColorRGB(1,1,1);c.rect(-tw/2,-2,tw,14,fill=1,stroke=basic);c.setFillColorRGB(*BLACK);text(0,1,t,10,align='center');c.restoreState()
def center(x,y,r=12):
 c.setDash([6,2,1,2]);line(x-r,y,x+r,y,.3);line(x,y-r,x,y+r,.3);c.setDash()
def fcf(x,y,cells):
 for t in cells:
  tw=max(24,pdfmetrics.stringWidth(t,'D',10)+12);c.rect(x,y,tw,20,fill=0)
  if t=='⌖':
   cx=x+tw/2;cy=y+10;c.circle(cx,cy,4);line(cx-7,cy,cx+7,cy,.6);line(cx,cy-7,cx,cy+7,.6)
  else:text(x+tw/2,y+6,t,10,align='center')
  x+=tw
 return x
def datum(x,y,t,dx,dy):
 a=math.atan2(dy,dx);q=c.beginPath();q.moveTo(x,y);q.lineTo(x+6*math.cos(a)+3*math.sin(a),y+6*math.sin(a)-3*math.cos(a));q.lineTo(x+6*math.cos(a)-3*math.sin(a),y+6*math.sin(a)+3*math.cos(a));q.close();c.drawPath(q,fill=1)
 line(x,y,x+dx,y+dy,.6);c.rect(x+dx-10,y+dy-20,20,20);text(x+dx,y+dy-15,t,11,True,align='center')
def frame(sheet):
 c.setStrokeColorRGB(*BLACK);c.setFillColorRGB(*BLACK);c.rect(25,25,W-50,H-50)
 text(42,H-50,'NODI / MECHANICAL DESIGN',15,True);text(W-42,H-49,'PROTOTYPE DEFINITION — NOT A PRODUCTION RELEASE',10,align='right')
 c.rect(25,25,W-50,86);line(25,62,W-25,62);line(770,25,770,111);line(1000,25,1000,111)
 text(40,90,'NODI-P03   PAN–TILT YOKE',15,True);text(40,73,'MATERIAL: PETG, FFF + FINISH DRILL / PROCESS NOTES ON SHEET 2',9)
 text(40,47,'UNITS: mm   |   THIRD ANGLE PROJECTION   |   DO NOT SCALE DRAWING',9)
 text(40,33,'General ±0.25 linear / ±1° angular unless limits, basic dimensions or GD&T apply.',8)
 text(785,88,'REV A  /  2026-10-24',11,True);text(785,72,'Scale: 2:1 views (A3)' if sheet==1 else 'Scale: 1.5:1 views (A3)',9)
 text(785,46,'ASME Y14.5-2018 principles',9);text(785,32,'Unbuilt / inspect before assembly',8)
 text(1015,88,'David Borsky',11,True);text(1015,71,'AI-assisted design study',9);text(1015,45,f'SHEET {sheet} OF 2',11,True)
def note(x,y,rows,leading=16):
 for r in rows:text(x,y,r,9);y-=leading
frame(1)
# Front: X horizontal, Z vertical. Global drawing origin X0 Z34.
s=5.6693;ox=370;oy=280
def X(x):return ox+x*s
def Z(z):return oy+(z-34)*s
# plate96x4, pilot24x5
c.rect(X(-48),Z(34),96*s,4*s)
c.rect(X(-12),Z(29),24*s,5*s)
# arms front projected silhouettes
for x in [-48,44]:c.rect(X(x),Z(38),4*s,64*s)
# Left-pad annular relief, projected hidden edge at its floor.
c.setDash(4,2)
for z1,z2 in [(74,78.5),(97.5,102)]:
 line(X(-45.4),Z(z1),X(-45.4),Z(z2),.35);line(X(-45.4),Z(z2),X(-44),Z(z2),.35)
c.setDash()
# hidden centerbore front
c.setDash(4,2);line(X(-4.5),Z(34),X(-4.5),Z(38),.4);line(X(4.5),Z(34),X(4.5),Z(38),.4);c.setDash()
line(X(48),Z(34),X(57),Z(34));line(X(57),Z(34),X(57),Z(38));line(X(57),Z(38),X(48),Z(38))
center(X(0),Z(88),40);c.setDash([8,3,2,3]);line(X(-55),Z(88),X(54),Z(88),.4);c.setDash()
text(370,750,'FRONT / X–Z',11,True,align='center')
hd(X(-48),X(48),Z(29)-42,Z(34),'96.00')
hd(X(-44),X(44),Z(102)+26,Z(102),'88.00 +0.30 / −0.00')
vd(Z(34),Z(88),X(-48)-45,X(-48),'54.00',True)
vd(Z(34),Z(102),X(-48)-66,X(-48),'68.00')
vd(Z(34),Z(38),X(48)+28,X(48),'4.00')
vd(Z(29),Z(34),X(-12)-20,X(-12),'5.00')
hd(X(-12),X(12),Z(29)-20,Z(29),'Ø24.00 ±0.10')
datum(X(-25),Z(34),'A',0,-75);datum(X(-48),Z(67),'B',-28,0)
fcf(45,172,['▱','0.20']);text(155,177,'APPLIES TO A (annular bottom plate face; exclude pilot)',9)
text(45,147,'Front projection: pads have R14 outline in Y–Z view. Front view does not define pad profile.',8)
# Right side Y–Z pad+stem+plate
ox2=905;oy2=280
def Y(y):return ox2+y*s
def ZZ(z):return oy2+(z-34)*s
c.rect(Y(-20),ZZ(34),40*s,4*s)
zjoin=88-math.sqrt(14**2-6**2)
line(Y(-6),ZZ(38),Y(-6),ZZ(zjoin));line(Y(6),ZZ(38),Y(6),ZZ(zjoin))
ang=math.degrees(math.atan2(zjoin-88,-6))%360
c.arc(Y(-14),ZZ(74),Y(14),ZZ(102),startAng=ang,extent=-(2*ang-180))
# circles features
for yy,d in [(0,6),(-7,2.2),(7,2.2)]:c.circle(Y(yy),ZZ(88),d*s/2);center(Y(yy),ZZ(88),9)
text(905,750,'RIGHT / Y–Z',11,True,align='center')
hd(Y(-20),Y(20),ZZ(34)-48,ZZ(34),'40.00')
hd(Y(-6),Y(6),ZZ(38)+42,ZZ(38),'12.00')
hd(Y(-7),Y(7),ZZ(102)+20,ZZ(88),'14.00',True)
vd(ZZ(34),ZZ(88),Y(20)+35,Y(0),'54.00',True)
hd(Y(-20),Y(0),ZZ(34)-75,ZZ(34),'20.00',True)
datum(Y(-20),ZZ(36),'C',-20,-15)
line(Y(9),ZZ(98),Y(17),ZZ(104));text(Y(17),ZZ(104)+4,'R14.00',9)
line(Y(0),ZZ(88),Y(26),ZZ(93));text(1035,ZZ(93)+4,'Ø6.00 +0.20/−0',8);text(1035,ZZ(93)-8,'THRU RIGHT',8)
line(Y(7),ZZ(88),Y(26),ZZ(84));text(1035,ZZ(84),'2X Ø2.20',8);text(1035,ZZ(84)-12,'+0.15/−0 THRU',8)
text(748,178,'LEFT BORE: Ø4.20 +0.10/−0 THRU (opposite arm)',9)
fcf(748,147,['⌖','Ø0.30','A','B','C']);text(748,131,'Applies separately to LEFT Ø4.2 and RIGHT Ø6 axes.',8)
text(748,117,'Hole Y=0, Z=88 share basic axis; horn holes at Y=±7.',8)
c.showPage();frame(2)
# Top view and section A-A through Y0
ox=340;oy=565
s=4.251969
def TX(x):return ox+x*s
def TY(y):return oy+y*s
c.roundRect(TX(-48),TY(-20),96*s,40*s,3*s)
for x in [-48,44]:c.rect(TX(x),TY(-14),4*s,28*s)
c.rect(TX(46),TY(-2),9*s,4*s);c.circle(TX(55),TY(0),2*s)
for x in [-7,7]:c.circle(TX(x),TY(0),1.1*s);center(TX(x),TY(0),9)
c.circle(TX(0),TY(0),4.5*s);center(TX(0),TY(0),20)
c.setDash(4,2);c.circle(TX(0),TY(0),12*s);c.circle(TX(0),TY(0),10.2*s);c.setDash()
text(340,720,'TOP / X–Y',11,True,align='center')
hd(TX(-48),TX(57),TY(-20)-32,TY(-20),'105.00 OVERALL')
hd(TX(-7),TX(7),TY(20)+25,TY(0),'14.00',True)
line(TX(0),TY(0),TX(16),TY(25));text(TX(16),TY(25)+3,'Ø9.00 +0.20/−0 THRU PLATE',9)
text(92,430,'4X R3 OUTER PLATE CORNERS; ARMS AND STOP LUG EXCEPTED',8)
# Section through plate and pilot
sx=880;sy=595
c.rect(sx-12*s,sy-5*s,24*s,5*s);c.rect(sx-48*s,sy,96*s,4*s)
# white void remove central counterbore and hole
c.setFillColorRGB(1,1,1);c.rect(sx-10.2*s,sy-5*s,20.4*s,5*s,fill=1,stroke=0);c.rect(sx-4.5*s,sy,9*s,4*s,fill=1,stroke=0);c.setFillColorRGB(*BLACK)
for x in [-12,-10.2,10.2,12]:line(sx+x*s,sy-5*s,sx+x*s,sy)
for x in [-4.5,4.5]:line(sx+x*s,sy,sx+x*s,sy+4*s)
text(880,720,'SECTION A–A / PILOT DETAIL',11,True,align='center')
text(687,677,'Section through Y=0; arms/horn holes omitted for clarity.',8)
hd(sx-10.2*s,sx+10.2*s,sy-5*s-27,sy-5*s,'Ø20.40 ±0.20')
text(690,485,'Pilot ring concentric to plate center X=0, Y=0.',9)
text(690,467,'Finish OD to Ø24.00 ±0.10; mating lid bore Ø24.40 +0.20/−0.',9)
text(690,449,'Minimum nominal-dimension radial clearance: 0.15 mm.',9)
fcf(690,415,['⌖','Ø0.30','A','B','C']);text(690,401,'Pilot outer axis: basic X=48 from B, Y=20 from C.',8)
# Complete feature schedule
rows=[
('F01','Plate','96 × 40 × 4; X±48, Y±20, Z34–38; R3 corners'),
('F02','Arms / pads','X−48…−44 and44…48; stem Y±6,Z38…88; padR14@Y0,Z88'),
('F03','Pilot / access','Ø24 OD / Ø20.4 ID ×5 fromZ29…34; Ø9 access through plate'),
('F04','Pitch axes','LEFT Ø4.2; RIGHT Ø6; basicY0,Z88; axis alongX'),
('F05','Horn fasteners','2×Ø2.2 through RIGHT at(Y−7,Z88),(Y+7,Z88)'),
('F06','Yaw horn fasteners','2×Ø2.2 through plate at(X−7,Y0),(X+7,Y0)'),
('F07','Yaw stop','Bridge X45…55,Y±2,Z34…38; Ø4 pin atX55,Y0,Z34…38'),
('F08','Pitch stops','2×Ø3 pins axisX, X−45.5…−44.0; centers below'),
('F08a','Lower stop center','Y+6.773, Z97.906; basic toA:Z63.906; toC:Y26.773'),
('F08b','Upper stop center','Y−8.390, Z96.579; basic toA:Z62.579; toC:Y11.610'),
('F09','Left inner recess','Annular Ø28/Ø19 ×1.40 deep; X−45.4…−44; preserve pivot land within Ø19'),
]
y=371
for n,name,desc in rows:
 text(45,y,n,8,True);text(83,y,name,8,True);text(217,y,desc,8);y-=17
note(45,183,[
'NOTES: All coordinates in feature schedule refer to CAD assembly axes (mm): X0/Y0 at yaw axis; plate underside Z34.',
'Prototype process: PETG FFF, 0.2 layers, five perimeters, local solid pivot/root regions; inspect process coupon first.',
'Deburr and finish-drill critical holes. No supports or burrs on datum A / thrust track. Break exposed edges 0.3 max.',
'Fit Ø4 sleeve without binding; sleeve + fastener sets pivot endfloat. Do not clamp rotating head. Match drill horn if required.',
'Integral stop contacts are fault arrestors. Software limits −15°/+25° pitch, ±30° yaw; hard pitch −20°/+30°, yaw ±35°.',
'General linear tolerances do not apply to boxed basic locations. Inspect hole axes in A|B|C datum frame; GD&T RFS.',
],leading=11)
c.save()
manifest=json.loads((ROOT/'CAD/manifest.json').read_text())
d=manifest['drawing_dimensions']
expected={'yoke_width_mm':96,'yoke_gap_mm':88,'yoke_thickness_mm':4,'pan_plate_depth_mm':40,'pan_plate_z_mm':[34,38],'arm_depth_mm':12,'pitch_axis_z_mm':88,'upper_pad_radius_mm':14,'left_bore_mm':4.2,'right_access_bore_mm':6,'horn_holes_mm':2.2,'horn_hole_y_mm':[-7,7],'pan_horn_hole_x_mm':[-7,7],'pilot_od_mm':24,'pilot_id_mm':20.4,'pilot_z_mm':[29,34],'central_access_mm':9,'pitch_stop_pin_diameter_mm':3,'yaw_stop_lug_center_mm':[55,0,36],'yaw_stop_lug_diameter_mm':4,'yaw_stop_bridge_bounds_mm':[[45,-2,34],[55,2,38]],'pitch_stop_recess_od_mm':28,'pitch_stop_recess_id_mm':19,'pitch_stop_recess_depth_mm':1.4,'pitch_stop_pin_x_mm':[-45.5,-44.0]}
errors=[k for k,v in expected.items() if d.get(k)!=v]
rounded=[[6.773,97.906],[-8.390,96.579]]
for a,b in zip(rounded,d['pitch_stop_centres_yz_mm']):
 if max(abs(x-y) for x,y in zip(a,b))>.00051:errors.append('pitch_stop_centres_yz_mm')
check={'status':'PASS' if not errors else 'FAIL','cad_revision':manifest['revision'],'drawing_revision':'A','nominal_features_compared':len(expected)+2,'maximum_stop_rounding_mm':.00051,'mismatches':errors,'scope':'Parameter agreement, not independent metrology or a complete drawing standards audit.'}
(ROOT/'Drawings/drawing_geometry_check.json').write_text(json.dumps(check,indent=2)+'\n')
if errors:raise RuntimeError(check)
print(p.relative_to(ROOT))
