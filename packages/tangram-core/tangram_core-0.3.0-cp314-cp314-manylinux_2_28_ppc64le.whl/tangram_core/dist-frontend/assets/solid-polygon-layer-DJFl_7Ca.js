import{G as ie,L as he,p as ge,h as Ye,d as ve}from"./layer-DPcO4AXQ.js";import{x as Xe,U as ue,O as ae}from"./deep-equal-BTW2ZN6S.js";import{g as Re,T as Ge}from"./tesselator-CENyUZ2p.js";import{M as B}from"./shader-Cbdysp2j.js";import{g as Qe}from"./_commonjsHelpers-CqkleIqs.js";const xe={CLOCKWISE:1,COUNTER_CLOCKWISE:-1};function ye(n,e,t={}){return qe(n,t)!==e?(tt(n,t),!0):!1}function qe(n,e={}){return Math.sign(et(n,e))}const _e={x:0,y:1,z:2};function et(n,e={}){const{start:t=0,end:i=n.length,plane:a="xy"}=e,s=e.size||2;let c=0;const f=_e[a[0]],g=_e[a[1]];for(let v=t,x=i-s;v<i;v+=s)c+=(n[v+f]-n[x+f])*(n[v+g]+n[x+g]),x=v;return c/2}function tt(n,e){const{start:t=0,end:i=n.length,size:a=2}=e,s=(i-t)/a,c=Math.floor(s/2);for(let f=0;f<c;++f){const g=t+f*a,v=t+(s-1-f)*a;for(let x=0;x<a;++x){const w=n[g+x];n[g+x]=n[v+x],n[v+x]=w}}}function D(n,e){const t=e.length,i=n.length;if(i>0){let a=!0;for(let s=0;s<t;s++)if(n[i-t+s]!==e[s]){a=!1;break}if(a)return!1}for(let a=0;a<t;a++)n[i+a]=e[a];return!0}function de(n,e){const t=e.length;for(let i=0;i<t;i++)n[i]=e[i]}function $(n,e,t,i,a=[]){const s=i+e*t;for(let c=0;c<t;c++)a[c]=n[s+c];return a}function pe(n,e,t,i,a=[]){let s,c;if(t&8)s=(i[3]-n[1])/(e[1]-n[1]),c=3;else if(t&4)s=(i[1]-n[1])/(e[1]-n[1]),c=1;else if(t&2)s=(i[2]-n[0])/(e[0]-n[0]),c=2;else if(t&1)s=(i[0]-n[0])/(e[0]-n[0]),c=0;else return null;for(let f=0;f<n.length;f++)a[f]=(c&1)===f?i[c]:s*(e[f]-n[f])+n[f];return a}function ee(n,e){let t=0;return n[0]<e[0]?t|=1:n[0]>e[2]&&(t|=2),n[1]<e[1]?t|=4:n[1]>e[3]&&(t|=8),t}function De(n,e){const{size:t=2,broken:i=!1,gridResolution:a=10,gridOffset:s=[0,0],startIndex:c=0,endIndex:f=n.length}=e||{},g=(f-c)/t;let v=[];const x=[v],w=$(n,0,t,c);let C,m;const S=Ve(w,a,s,[]),P=[];D(v,w);for(let I=1;I<g;I++){for(C=$(n,I,t,c,C),m=ee(C,S);m;){pe(w,C,m,S,P);const A=ee(P,S);A&&(pe(w,P,A,S,P),m=A),D(v,P),de(w,P),ot(S,a,m),i&&v.length>t&&(v=[],x.push(v),D(v,w)),m=ee(C,S)}D(v,C),de(w,C)}return i?x:x[0]}const Ce=0,it=1;function ke(n,e=null,t){if(!n.length)return[];const{size:i=2,gridResolution:a=10,gridOffset:s=[0,0],edgeTypes:c=!1}=t||{},f=[],g=[{pos:n,types:c?new Array(n.length/i).fill(it):null,holes:e||[]}],v=[[],[]];let x=[];for(;g.length;){const{pos:w,types:C,holes:m}=g.shift();nt(w,i,m[0]||w.length,v),x=Ve(v[0],a,s,x);const S=ee(v[1],x);if(S){let P=Se(w,C,i,0,m[0]||w.length,x,S);const I={pos:P[0].pos,types:P[0].types,holes:[]},A={pos:P[1].pos,types:P[1].types,holes:[]};g.push(I,A);for(let N=0;N<m.length;N++)P=Se(w,C,i,m[N],m[N+1]||w.length,x,S),P[0]&&(I.holes.push(I.pos.length),I.pos=Y(I.pos,P[0].pos),c&&(I.types=Y(I.types,P[0].types))),P[1]&&(A.holes.push(A.pos.length),A.pos=Y(A.pos,P[1].pos),c&&(A.types=Y(A.types,P[1].types)))}else{const P={positions:w};c&&(P.edgeTypes=C),m.length&&(P.holeIndices=m),f.push(P)}}return f}function Se(n,e,t,i,a,s,c){const f=(a-i)/t,g=[],v=[],x=[],w=[],C=[];let m,S,P;const I=$(n,f-1,t,i);let A=Math.sign(c&8?I[1]-s[3]:I[0]-s[2]),N=e&&e[f-1],O=0,G=0;for(let V=0;V<f;V++)m=$(n,V,t,i,m),S=Math.sign(c&8?m[1]-s[3]:m[0]-s[2]),P=e&&e[i/t+V],S&&A&&A!==S&&(pe(I,m,c,s,C),D(g,C)&&x.push(N),D(v,C)&&w.push(N)),S<=0?(D(g,m)&&x.push(P),O-=S):x.length&&(x[x.length-1]=Ce),S>=0?(D(v,m)&&w.push(P),G+=S):w.length&&(w[w.length-1]=Ce),de(I,m),A=S,N=P;return[O?{pos:g,types:e&&x}:null,G?{pos:v,types:e&&w}:null]}function Ve(n,e,t,i){const a=Math.floor((n[0]-t[0])/e)*e+t[0],s=Math.floor((n[1]-t[1])/e)*e+t[1];return i[0]=a,i[1]=s,i[2]=a+e,i[3]=s+e,i}function ot(n,e,t){t&8?(n[1]+=e,n[3]+=e):t&4?(n[1]-=e,n[3]-=e):t&2?(n[0]+=e,n[2]+=e):t&1&&(n[0]-=e,n[2]-=e)}function nt(n,e,t,i){let a=1/0,s=-1/0,c=1/0,f=-1/0;for(let g=0;g<t;g+=e){const v=n[g],x=n[g+1];a=v<a?v:a,s=v>s?v:s,c=x<c?x:c,f=x>f?x:f}return i[0][0]=a,i[0][1]=c,i[1][0]=s,i[1][1]=f,i}function Y(n,e){for(let t=0;t<e.length;t++)n.push(e[t]);return n}const st=85.051129;function rt(n,e){const{size:t=2,startIndex:i=0,endIndex:a=n.length,normalize:s=!0}=e||{},c=n.slice(i,a);Be(c,t,0,a-i);const f=De(c,{size:t,broken:!0,gridResolution:360,gridOffset:[-180,-180]});if(s)for(const g of f)Ue(g,t);return f}function at(n,e=null,t){const{size:i=2,normalize:a=!0,edgeTypes:s=!1}=t||{};e=e||[];const c=[],f=[];let g=0,v=0;for(let w=0;w<=e.length;w++){const C=e[w]||n.length,m=v,S=lt(n,i,g,C);for(let P=S;P<C;P++)c[v++]=n[P];for(let P=g;P<S;P++)c[v++]=n[P];Be(c,i,m,v),ct(c,i,m,v,t?.maxLatitude),g=C,f[w]=v}f.pop();const x=ke(c,f,{size:i,gridResolution:360,gridOffset:[-180,-180],edgeTypes:s});if(a)for(const w of x)Ue(w.positions,i);return x}function lt(n,e,t,i){let a=-1,s=-1;for(let c=t+1;c<i;c+=e){const f=Math.abs(n[c]);f>a&&(a=f,s=c-1)}return s}function ct(n,e,t,i,a=st){const s=n[t],c=n[i-e];if(Math.abs(s-c)>180){const f=$(n,0,e,t);f[0]+=Math.round((c-s)/360)*360,D(n,f),f[1]=Math.sign(f[1])*a,D(n,f),f[0]=s,D(n,f)}}function Be(n,e,t,i){let a=n[0],s;for(let c=t;c<i;c+=e){s=n[c];const f=s-a;(f>180||f<-180)&&(s-=Math.round(f/360)*360),n[c]=a=s}}function Ue(n,e){let t;const i=n.length/e;for(let s=0;s<i&&(t=n[s*e],(t+180)%360===0);s++);const a=-Math.round(t/360)*360;if(a!==0)for(let s=0;s<i;s++)n[s*e]+=a}class ft extends ie{constructor(e){const{indices:t,attributes:i}=ut(e);super({...e,indices:t,attributes:i})}}function ut(n){const{radius:e,height:t=1,nradial:i=10}=n;let{vertices:a}=n;a&&(Xe.assert(a.length>=i),a=a.flatMap(m=>[m[0],m[1]]),ye(a,xe.COUNTER_CLOCKWISE));const s=t>0,c=i+1,f=s?c*3+1:i,g=Math.PI*2/i,v=new Uint16Array(s?i*3*2:0),x=new Float32Array(f*3),w=new Float32Array(f*3);let C=0;if(s){for(let m=0;m<c;m++){const S=m*g,P=m%i,I=Math.sin(S),A=Math.cos(S);for(let N=0;N<2;N++)x[C+0]=a?a[P*2]:A*e,x[C+1]=a?a[P*2+1]:I*e,x[C+2]=(1/2-N)*t,w[C+0]=a?a[P*2]:A,w[C+1]=a?a[P*2+1]:I,C+=3}x[C+0]=x[C-3],x[C+1]=x[C-2],x[C+2]=x[C-1],C+=3}for(let m=s?0:1;m<c;m++){const S=Math.floor(m/2)*Math.sign(.5-m%2),P=S*g,I=(S+i)%i,A=Math.sin(P),N=Math.cos(P);x[C+0]=a?a[I*2]:N*e,x[C+1]=a?a[I*2+1]:A*e,x[C+2]=t/2,w[C+2]=1,C+=3}if(s){let m=0;for(let S=0;S<i;S++)v[m++]=S*2+0,v[m++]=S*2+2,v[m++]=S*2+0,v[m++]=S*2+1,v[m++]=S*2+1,v[m++]=S*2+3}return{indices:v,attributes:{POSITION:{size:3,value:x},NORMAL:{size:3,value:w}}}}const Ie=`uniform columnUniforms {
  float radius;
  float angle;
  vec2 offset;
  bool extruded;
  bool stroked;
  bool isStroke;
  float coverage;
  float elevationScale;
  float edgeDistance;
  float widthScale;
  float widthMinPixels;
  float widthMaxPixels;
  highp int radiusUnits;
  highp int widthUnits;
} column;
`,dt={name:"column",vs:Ie,fs:Ie,uniformTypes:{radius:"f32",angle:"f32",offset:"vec2<f32>",extruded:"f32",stroked:"f32",isStroke:"f32",coverage:"f32",elevationScale:"f32",edgeDistance:"f32",widthScale:"f32",widthMinPixels:"f32",widthMaxPixels:"f32",radiusUnits:"i32",widthUnits:"i32"}},pt=`#version 300 es
#define SHADER_NAME column-layer-vertex-shader
in vec3 positions;
in vec3 normals;
in vec3 instancePositions;
in float instanceElevations;
in vec3 instancePositions64Low;
in vec4 instanceFillColors;
in vec4 instanceLineColors;
in float instanceStrokeWidths;
in vec3 instancePickingColors;
out vec4 vColor;
#ifdef FLAT_SHADING
out vec3 cameraPosition;
out vec4 position_commonspace;
#endif
void main(void) {
geometry.worldPosition = instancePositions;
vec4 color = column.isStroke ? instanceLineColors : instanceFillColors;
mat2 rotationMatrix = mat2(cos(column.angle), sin(column.angle), -sin(column.angle), cos(column.angle));
float elevation = 0.0;
float strokeOffsetRatio = 1.0;
if (column.extruded) {
elevation = instanceElevations * (positions.z + 1.0) / 2.0 * column.elevationScale;
} else if (column.stroked) {
float widthPixels = clamp(
project_size_to_pixel(instanceStrokeWidths * column.widthScale, column.widthUnits),
column.widthMinPixels, column.widthMaxPixels) / 2.0;
float halfOffset = project_pixel_size(widthPixels) / project_size(column.edgeDistance * column.coverage * column.radius);
if (column.isStroke) {
strokeOffsetRatio -= sign(positions.z) * halfOffset;
} else {
strokeOffsetRatio -= halfOffset;
}
}
float shouldRender = float(color.a > 0.0 && instanceElevations >= 0.0);
float dotRadius = column.radius * column.coverage * shouldRender;
geometry.pickingColor = instancePickingColors;
vec3 centroidPosition = vec3(instancePositions.xy, instancePositions.z + elevation);
vec3 centroidPosition64Low = instancePositions64Low;
vec2 offset = (rotationMatrix * positions.xy * strokeOffsetRatio + column.offset) * dotRadius;
if (column.radiusUnits == UNIT_METERS) {
offset = project_size(offset);
}
vec3 pos = vec3(offset, 0.);
DECKGL_FILTER_SIZE(pos, geometry);
gl_Position = project_position_to_clipspace(centroidPosition, centroidPosition64Low, pos, geometry.position);
geometry.normal = project_normal(vec3(rotationMatrix * normals.xy, normals.z));
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
if (column.extruded && !column.isStroke) {
#ifdef FLAT_SHADING
cameraPosition = project.cameraPosition;
position_commonspace = geometry.position;
vColor = vec4(color.rgb, color.a * layer.opacity);
#else
vec3 lightColor = lighting_getLightColor(color.rgb, project.cameraPosition, geometry.position.xyz, geometry.normal);
vColor = vec4(lightColor, color.a * layer.opacity);
#endif
} else {
vColor = vec4(color.rgb, color.a * layer.opacity);
}
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,ht=`#version 300 es
#define SHADER_NAME column-layer-fragment-shader
precision highp float;
out vec4 fragColor;
in vec4 vColor;
#ifdef FLAT_SHADING
in vec3 cameraPosition;
in vec4 position_commonspace;
#endif
void main(void) {
fragColor = vColor;
geometry.uv = vec2(0.);
#ifdef FLAT_SHADING
if (column.extruded && !column.isStroke && !bool(picking.isActive)) {
vec3 normal = normalize(cross(dFdx(position_commonspace.xyz), dFdy(position_commonspace.xyz)));
fragColor.rgb = lighting_getLightColor(vColor.rgb, cameraPosition, position_commonspace.xyz, normal);
}
#endif
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,oe=[0,0,0,255],gt={diskResolution:{type:"number",min:4,value:20},vertices:null,radius:{type:"number",min:0,value:1e3},angle:{type:"number",value:0},offset:{type:"array",value:[0,0]},coverage:{type:"number",min:0,max:1,value:1},elevationScale:{type:"number",min:0,value:1},radiusUnits:"meters",lineWidthUnits:"meters",lineWidthScale:1,lineWidthMinPixels:0,lineWidthMaxPixels:Number.MAX_SAFE_INTEGER,extruded:!0,wireframe:!1,filled:!0,stroked:!1,flatShading:!1,getPosition:{type:"accessor",value:n=>n.position},getFillColor:{type:"accessor",value:oe},getLineColor:{type:"accessor",value:oe},getLineWidth:{type:"accessor",value:1},getElevation:{type:"accessor",value:1e3},material:!0,getColor:{deprecatedFor:["getFillColor","getLineColor"]}};class je extends he{getShaders(){const e={},{flatShading:t}=this.props;return t&&(e.FLAT_SHADING=1),super.getShaders({vs:pt,fs:ht,defines:e,modules:[ge,t?Ye:Re,ve,dt]})}initializeState(){this.getAttributeManager().addInstanced({instancePositions:{size:3,type:"float64",fp64:this.use64bitPositions(),transition:!0,accessor:"getPosition"},instanceElevations:{size:1,transition:!0,accessor:"getElevation"},instanceFillColors:{size:this.props.colorFormat.length,type:"unorm8",transition:!0,accessor:"getFillColor",defaultValue:oe},instanceLineColors:{size:this.props.colorFormat.length,type:"unorm8",transition:!0,accessor:"getLineColor",defaultValue:oe},instanceStrokeWidths:{size:1,accessor:"getLineWidth",transition:!0}})}updateState(e){super.updateState(e);const{props:t,oldProps:i,changeFlags:a}=e,s=a.extensionsChanged||t.flatShading!==i.flatShading;s&&(this.state.models?.forEach(f=>f.destroy()),this.setState(this._getModels()),this.getAttributeManager().invalidateAll());const c=this.getNumInstances();this.state.fillModel.setInstanceCount(c),this.state.wireframeModel.setInstanceCount(c),(s||t.diskResolution!==i.diskResolution||t.vertices!==i.vertices||(t.extruded||t.stroked)!==(i.extruded||i.stroked))&&this._updateGeometry(t)}getGeometry(e,t,i){const a=new ft({radius:1,height:i?2:0,vertices:t,nradial:e});let s=0;if(t)for(let c=0;c<e;c++){const f=t[c],g=Math.sqrt(f[0]*f[0]+f[1]*f[1]);s+=g/e}else s=1;return this.setState({edgeDistance:Math.cos(Math.PI/e)*s}),a}_getModels(){const e=this.getShaders(),t=this.getAttributeManager().getBufferLayouts(),i=new B(this.context.device,{...e,id:`${this.props.id}-fill`,bufferLayout:t,isInstanced:!0}),a=new B(this.context.device,{...e,id:`${this.props.id}-wireframe`,bufferLayout:t,isInstanced:!0});return{fillModel:i,wireframeModel:a,models:[a,i]}}_updateGeometry({diskResolution:e,vertices:t,extruded:i,stroked:a}){const s=this.getGeometry(e,t,i||a);this.setState({fillVertexCount:s.attributes.POSITION.value.length/3});const c=this.state.fillModel,f=this.state.wireframeModel;c.setGeometry(s),c.setTopology("triangle-strip"),c.setIndexBuffer(null),f.setGeometry(s),f.setTopology("line-list")}draw({uniforms:e}){const{lineWidthUnits:t,lineWidthScale:i,lineWidthMinPixels:a,lineWidthMaxPixels:s,radiusUnits:c,elevationScale:f,extruded:g,filled:v,stroked:x,wireframe:w,offset:C,coverage:m,radius:S,angle:P}=this.props,I=this.state.fillModel,A=this.state.wireframeModel,{fillVertexCount:N,edgeDistance:O}=this.state,G={radius:S,angle:P/180*Math.PI,offset:C,extruded:g,stroked:x,coverage:m,elevationScale:f,edgeDistance:O,radiusUnits:ue[c],widthUnits:ue[t],widthScale:i,widthMinPixels:a,widthMaxPixels:s};g&&w&&(A.shaderInputs.setProps({column:{...G,isStroke:!0}}),A.draw(this.context.renderPass)),v&&(I.setVertexCount(N),I.shaderInputs.setProps({column:{...G,isStroke:!1}}),I.draw(this.context.renderPass)),!g&&x&&(I.setVertexCount(N*2/3),I.shaderInputs.setProps({column:{...G,isStroke:!0}}),I.draw(this.context.renderPass))}}je.layerName="ColumnLayer";je.defaultProps=gt;function vt(n,e,t,i){let a;if(Array.isArray(n[0])){const s=n.length*e;a=new Array(s);for(let c=0;c<n.length;c++)for(let f=0;f<e;f++)a[c*e+f]=n[c][f]||0}else a=n;return t?De(a,{size:e,gridResolution:t}):i?rt(a,{size:e}):a}const xt=1,yt=2,le=4;class mt extends Ge{constructor(e){super({...e,attributes:{positions:{size:3,padding:18,initialize:!0,type:e.fp64?Float64Array:Float32Array},segmentTypes:{size:1,type:Uint8ClampedArray}}})}get(e){return this.attributes[e]}getGeometryFromBuffer(e){return this.normalize?super.getGeometryFromBuffer(e):null}normalizeGeometry(e){return this.normalize?vt(e,this.positionSize,this.opts.resolution,this.opts.wrapLongitude):e}getGeometrySize(e){if(Ae(e)){let i=0;for(const a of e)i+=this.getGeometrySize(a);return i}const t=this.getPathLength(e);return t<2?0:this.isClosed(e)?t<3?0:t+2:t}updateGeometryAttributes(e,t){if(t.geometrySize!==0)if(e&&Ae(e))for(const i of e){const a=this.getGeometrySize(i);t.geometrySize=a,this.updateGeometryAttributes(i,t),t.vertexStart+=a}else this._updateSegmentTypes(e,t),this._updatePositions(e,t)}_updateSegmentTypes(e,t){const i=this.attributes.segmentTypes,a=e?this.isClosed(e):!1,{vertexStart:s,geometrySize:c}=t;i.fill(0,s,s+c),a?(i[s]=le,i[s+c-2]=le):(i[s]+=xt,i[s+c-2]+=yt),i[s+c-1]=le}_updatePositions(e,t){const{positions:i}=this.attributes;if(!i||!e)return;const{vertexStart:a,geometrySize:s}=t,c=new Array(3);for(let f=a,g=0;g<s;f++,g++)this.getPointOnPath(e,g,c),i[f*3]=c[0],i[f*3+1]=c[1],i[f*3+2]=c[2]}getPathLength(e){return e.length/this.positionSize}getPointOnPath(e,t,i=[]){const{positionSize:a}=this;t*a>=e.length&&(t+=1-e.length/a);const s=t*a;return i[0]=e[s],i[1]=e[s+1],i[2]=a===3&&e[s+2]||0,i}isClosed(e){if(!this.normalize)return!!this.opts.loop;const{positionSize:t}=this,i=e.length-t;return e[0]===e[i]&&e[1]===e[i+1]&&(t===2||e[2]===e[i+2])}}function Ae(n){return Array.isArray(n[0])}const Ee=`uniform pathUniforms {
  float widthScale;
  float widthMinPixels;
  float widthMaxPixels;
  float jointType;
  float capType;
  float miterLimit;
  bool billboard;
  highp int widthUnits;
} path;
`,Pt={name:"path",vs:Ee,fs:Ee,uniformTypes:{widthScale:"f32",widthMinPixels:"f32",widthMaxPixels:"f32",jointType:"f32",capType:"f32",miterLimit:"f32",billboard:"f32",widthUnits:"i32"}},wt=`#version 300 es
#define SHADER_NAME path-layer-vertex-shader
in vec2 positions;
in float instanceTypes;
in vec3 instanceStartPositions;
in vec3 instanceEndPositions;
in vec3 instanceLeftPositions;
in vec3 instanceRightPositions;
in vec3 instanceLeftPositions64Low;
in vec3 instanceStartPositions64Low;
in vec3 instanceEndPositions64Low;
in vec3 instanceRightPositions64Low;
in float instanceStrokeWidths;
in vec4 instanceColors;
in vec3 instancePickingColors;
uniform float opacity;
out vec4 vColor;
out vec2 vCornerOffset;
out float vMiterLength;
out vec2 vPathPosition;
out float vPathLength;
out float vJointType;
const float EPSILON = 0.001;
const vec3 ZERO_OFFSET = vec3(0.0);
float flipIfTrue(bool flag) {
return -(float(flag) * 2. - 1.);
}
vec3 getLineJoinOffset(
vec3 prevPoint, vec3 currPoint, vec3 nextPoint,
vec2 width
) {
bool isEnd = positions.x > 0.0;
float sideOfPath = positions.y;
float isJoint = float(sideOfPath == 0.0);
vec3 deltaA3 = (currPoint - prevPoint);
vec3 deltaB3 = (nextPoint - currPoint);
mat3 rotationMatrix;
bool needsRotation = !path.billboard && project_needs_rotation(currPoint, rotationMatrix);
if (needsRotation) {
deltaA3 = deltaA3 * rotationMatrix;
deltaB3 = deltaB3 * rotationMatrix;
}
vec2 deltaA = deltaA3.xy / width;
vec2 deltaB = deltaB3.xy / width;
float lenA = length(deltaA);
float lenB = length(deltaB);
vec2 dirA = lenA > 0. ? normalize(deltaA) : vec2(0.0, 0.0);
vec2 dirB = lenB > 0. ? normalize(deltaB) : vec2(0.0, 0.0);
vec2 perpA = vec2(-dirA.y, dirA.x);
vec2 perpB = vec2(-dirB.y, dirB.x);
vec2 tangent = dirA + dirB;
tangent = length(tangent) > 0. ? normalize(tangent) : perpA;
vec2 miterVec = vec2(-tangent.y, tangent.x);
vec2 dir = isEnd ? dirA : dirB;
vec2 perp = isEnd ? perpA : perpB;
float L = isEnd ? lenA : lenB;
float sinHalfA = abs(dot(miterVec, perp));
float cosHalfA = abs(dot(dirA, miterVec));
float turnDirection = flipIfTrue(dirA.x * dirB.y >= dirA.y * dirB.x);
float cornerPosition = sideOfPath * turnDirection;
float miterSize = 1.0 / max(sinHalfA, EPSILON);
miterSize = mix(
min(miterSize, max(lenA, lenB) / max(cosHalfA, EPSILON)),
miterSize,
step(0.0, cornerPosition)
);
vec2 offsetVec = mix(miterVec * miterSize, perp, step(0.5, cornerPosition))
* (sideOfPath + isJoint * turnDirection);
bool isStartCap = lenA == 0.0 || (!isEnd && (instanceTypes == 1.0 || instanceTypes == 3.0));
bool isEndCap = lenB == 0.0 || (isEnd && (instanceTypes == 2.0 || instanceTypes == 3.0));
bool isCap = isStartCap || isEndCap;
if (isCap) {
offsetVec = mix(perp * sideOfPath, dir * path.capType * 4.0 * flipIfTrue(isStartCap), isJoint);
vJointType = path.capType;
} else {
vJointType = path.jointType;
}
vPathLength = L;
vCornerOffset = offsetVec;
vMiterLength = dot(vCornerOffset, miterVec * turnDirection);
vMiterLength = isCap ? isJoint : vMiterLength;
vec2 offsetFromStartOfPath = vCornerOffset + deltaA * float(isEnd);
vPathPosition = vec2(
dot(offsetFromStartOfPath, perp),
dot(offsetFromStartOfPath, dir)
);
geometry.uv = vPathPosition;
float isValid = step(instanceTypes, 3.5);
vec3 offset = vec3(offsetVec * width * isValid, 0.0);
if (needsRotation) {
offset = rotationMatrix * offset;
}
return offset;
}
void clipLine(inout vec4 position, vec4 refPosition) {
if (position.w < EPSILON) {
float r = (EPSILON - refPosition.w) / (position.w - refPosition.w);
position = refPosition + (position - refPosition) * r;
}
}
void main() {
geometry.pickingColor = instancePickingColors;
vColor = vec4(instanceColors.rgb, instanceColors.a * layer.opacity);
float isEnd = positions.x;
vec3 prevPosition = mix(instanceLeftPositions, instanceStartPositions, isEnd);
vec3 prevPosition64Low = mix(instanceLeftPositions64Low, instanceStartPositions64Low, isEnd);
vec3 currPosition = mix(instanceStartPositions, instanceEndPositions, isEnd);
vec3 currPosition64Low = mix(instanceStartPositions64Low, instanceEndPositions64Low, isEnd);
vec3 nextPosition = mix(instanceEndPositions, instanceRightPositions, isEnd);
vec3 nextPosition64Low = mix(instanceEndPositions64Low, instanceRightPositions64Low, isEnd);
geometry.worldPosition = currPosition;
vec2 widthPixels = vec2(clamp(
project_size_to_pixel(instanceStrokeWidths * path.widthScale, path.widthUnits),
path.widthMinPixels, path.widthMaxPixels) / 2.0);
vec3 width;
if (path.billboard) {
vec4 prevPositionScreen = project_position_to_clipspace(prevPosition, prevPosition64Low, ZERO_OFFSET);
vec4 currPositionScreen = project_position_to_clipspace(currPosition, currPosition64Low, ZERO_OFFSET, geometry.position);
vec4 nextPositionScreen = project_position_to_clipspace(nextPosition, nextPosition64Low, ZERO_OFFSET);
clipLine(prevPositionScreen, currPositionScreen);
clipLine(nextPositionScreen, currPositionScreen);
clipLine(currPositionScreen, mix(nextPositionScreen, prevPositionScreen, isEnd));
width = vec3(widthPixels, 0.0);
DECKGL_FILTER_SIZE(width, geometry);
vec3 offset = getLineJoinOffset(
prevPositionScreen.xyz / prevPositionScreen.w,
currPositionScreen.xyz / currPositionScreen.w,
nextPositionScreen.xyz / nextPositionScreen.w,
project_pixel_size_to_clipspace(width.xy)
);
DECKGL_FILTER_GL_POSITION(currPositionScreen, geometry);
gl_Position = vec4(currPositionScreen.xyz + offset * currPositionScreen.w, currPositionScreen.w);
} else {
prevPosition = project_position(prevPosition, prevPosition64Low);
currPosition = project_position(currPosition, currPosition64Low);
nextPosition = project_position(nextPosition, nextPosition64Low);
width = vec3(project_pixel_size(widthPixels), 0.0);
DECKGL_FILTER_SIZE(width, geometry);
vec3 offset = getLineJoinOffset(prevPosition, currPosition, nextPosition, width.xy);
geometry.position = vec4(currPosition + offset, 1.0);
gl_Position = project_common_position_to_clipspace(geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
}
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,Lt=`#version 300 es
#define SHADER_NAME path-layer-fragment-shader
precision highp float;
in vec4 vColor;
in vec2 vCornerOffset;
in float vMiterLength;
in vec2 vPathPosition;
in float vPathLength;
in float vJointType;
out vec4 fragColor;
void main(void) {
geometry.uv = vPathPosition;
if (vPathPosition.y < 0.0 || vPathPosition.y > vPathLength) {
if (vJointType > 0.5 && length(vCornerOffset) > 1.0) {
discard;
}
if (vJointType < 0.5 && vMiterLength > path.miterLimit + 1.0) {
discard;
}
}
fragColor = vColor;
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,We=[0,0,0,255],_t={widthUnits:"meters",widthScale:{type:"number",min:0,value:1},widthMinPixels:{type:"number",min:0,value:0},widthMaxPixels:{type:"number",min:0,value:Number.MAX_SAFE_INTEGER},jointRounded:!1,capRounded:!1,miterLimit:{type:"number",min:0,value:4},billboard:!1,_pathType:null,getPath:{type:"accessor",value:n=>n.path},getColor:{type:"accessor",value:We},getWidth:{type:"accessor",value:1},rounded:{deprecatedFor:["jointRounded","capRounded"]}},ce={enter:(n,e)=>e.length?e.subarray(e.length-n.length):n};class Ze extends he{getShaders(){return super.getShaders({vs:wt,fs:Lt,modules:[ge,ve,Pt]})}get wrapLongitude(){return!1}getBounds(){return this.getAttributeManager()?.getBounds(["vertexPositions"])}initializeState(){this.getAttributeManager().addInstanced({vertexPositions:{size:3,vertexOffset:1,type:"float64",fp64:this.use64bitPositions(),transition:ce,accessor:"getPath",update:this.calculatePositions,noAlloc:!0,shaderAttributes:{instanceLeftPositions:{vertexOffset:0},instanceStartPositions:{vertexOffset:1},instanceEndPositions:{vertexOffset:2},instanceRightPositions:{vertexOffset:3}}},instanceTypes:{size:1,type:"uint8",update:this.calculateSegmentTypes,noAlloc:!0},instanceStrokeWidths:{size:1,accessor:"getWidth",transition:ce,defaultValue:1},instanceColors:{size:this.props.colorFormat.length,type:"unorm8",accessor:"getColor",transition:ce,defaultValue:We},instancePickingColors:{size:4,type:"uint8",accessor:(i,{index:a,target:s})=>this.encodePickingColor(i&&i.__source?i.__source.index:a,s)}}),this.setState({pathTesselator:new mt({fp64:this.use64bitPositions()})})}updateState(e){super.updateState(e);const{props:t,changeFlags:i}=e,a=this.getAttributeManager();if(i.dataChanged||i.updateTriggersChanged&&(i.updateTriggersChanged.all||i.updateTriggersChanged.getPath)){const{pathTesselator:c}=this.state,f=t.data.attributes||{};c.updateGeometry({data:t.data,geometryBuffer:f.getPath,buffers:f,normalize:!t._pathType,loop:t._pathType==="loop",getGeometry:t.getPath,positionFormat:t.positionFormat,wrapLongitude:t.wrapLongitude,resolution:this.context.viewport.resolution,dataChanged:i.dataChanged}),this.setState({numInstances:c.instanceCount,startIndices:c.vertexStarts}),i.dataChanged||a.invalidateAll()}i.extensionsChanged&&(this.state.model?.destroy(),this.state.model=this._getModel(),a.invalidateAll())}getPickingInfo(e){const t=super.getPickingInfo(e),{index:i}=t,a=this.props.data;return a[0]&&a[0].__source&&(t.object=a.find(s=>s.__source.index===i)),t}disablePickingIndex(e){const t=this.props.data;if(t[0]&&t[0].__source)for(let i=0;i<t.length;i++)t[i].__source.index===e&&this._disablePickingIndex(i);else super.disablePickingIndex(e)}draw({uniforms:e}){const{jointRounded:t,capRounded:i,billboard:a,miterLimit:s,widthUnits:c,widthScale:f,widthMinPixels:g,widthMaxPixels:v}=this.props,x=this.state.model,w={jointType:Number(t),capType:Number(i),billboard:a,widthUnits:ue[c],widthScale:f,miterLimit:s,widthMinPixels:g,widthMaxPixels:v};x.shaderInputs.setProps({path:w}),x.draw(this.context.renderPass)}_getModel(){const e=[0,1,2,1,4,2,1,3,4,3,5,4],t=[0,0,0,-1,0,1,1,-1,1,1,1,0];return new B(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),geometry:new ie({topology:"triangle-list",attributes:{indices:new Uint16Array(e),positions:{value:new Float32Array(t),size:2}}}),isInstanced:!0})}calculatePositions(e){const{pathTesselator:t}=this.state;e.startIndices=t.vertexStarts,e.value=t.get("positions")}calculateSegmentTypes(e){const{pathTesselator:t}=this.state;e.startIndices=t.vertexStarts,e.value=t.get("segmentTypes")}}Ze.defaultProps=_t;Ze.layerName="PathLayer";var X={exports:{}},Me;function Ct(){if(Me)return X.exports;Me=1,X.exports=n,X.exports.default=n;function n(o,l,r){r=r||2;var u=l&&l.length,d=u?l[0]*r:o.length,p=e(o,0,d,r,!0),h=[];if(!p||p.next===p.prev)return h;var y,_,L,b,z,E,R;if(u&&(p=g(o,l,p,r)),o.length>80*r){y=L=o[0],_=b=o[1];for(var F=r;F<d;F+=r)z=o[F],E=o[F+1],z<y&&(y=z),E<_&&(_=E),z>L&&(L=z),E>b&&(b=E);R=Math.max(L-y,b-_),R=R!==0?32767/R:0}return i(p,h,r,y,_,R,0),h}function e(o,l,r,u,d){var p,h;if(d===re(o,l,r,u)>0)for(p=l;p<r;p+=u)h=Pe(p,o[p],o[p+1],h);else for(p=r-u;p>=l;p-=u)h=Pe(p,o[p],o[p+1],h);return h&&G(h,h.next)&&(j(h),h=h.next),h}function t(o,l){if(!o)return o;l||(l=o);var r=o,u;do if(u=!1,!r.steiner&&(G(r,r.next)||O(r.prev,r,r.next)===0)){if(j(r),r=l=r.prev,r===r.next)break;u=!0}else r=r.next;while(u||r!==l);return l}function i(o,l,r,u,d,p,h){if(o){!h&&p&&m(o,u,d,p);for(var y=o,_,L;o.prev!==o.next;){if(_=o.prev,L=o.next,p?s(o,u,d,p):a(o)){l.push(_.i/r|0),l.push(o.i/r|0),l.push(L.i/r|0),j(o),o=L.next,y=L.next;continue}if(o=L,o===y){h?h===1?(o=c(t(o),l,r),i(o,l,r,u,d,p,2)):h===2&&f(o,l,r,u,d,p):i(t(o),l,r,u,d,p,1);break}}}}function a(o){var l=o.prev,r=o,u=o.next;if(O(l,r,u)>=0)return!1;for(var d=l.x,p=r.x,h=u.x,y=l.y,_=r.y,L=u.y,b=d<p?d<h?d:h:p<h?p:h,z=y<_?y<L?y:L:_<L?_:L,E=d>p?d>h?d:h:p>h?p:h,R=y>_?y>L?y:L:_>L?_:L,F=u.next;F!==l;){if(F.x>=b&&F.x<=E&&F.y>=z&&F.y<=R&&A(d,y,p,_,h,L,F.x,F.y)&&O(F.prev,F,F.next)>=0)return!1;F=F.next}return!0}function s(o,l,r,u){var d=o.prev,p=o,h=o.next;if(O(d,p,h)>=0)return!1;for(var y=d.x,_=p.x,L=h.x,b=d.y,z=p.y,E=h.y,R=y<_?y<L?y:L:_<L?_:L,F=b<z?b<E?b:E:z<E?z:E,W=y>_?y>L?y:L:_>L?_:L,Z=b>z?b>E?b:E:z>E?z:E,we=P(R,F,l,r,u),Le=P(W,Z,l,r,u),M=o.prevZ,T=o.nextZ;M&&M.z>=we&&T&&T.z<=Le;){if(M.x>=R&&M.x<=W&&M.y>=F&&M.y<=Z&&M!==d&&M!==h&&A(y,b,_,z,L,E,M.x,M.y)&&O(M.prev,M,M.next)>=0||(M=M.prevZ,T.x>=R&&T.x<=W&&T.y>=F&&T.y<=Z&&T!==d&&T!==h&&A(y,b,_,z,L,E,T.x,T.y)&&O(T.prev,T,T.next)>=0))return!1;T=T.nextZ}for(;M&&M.z>=we;){if(M.x>=R&&M.x<=W&&M.y>=F&&M.y<=Z&&M!==d&&M!==h&&A(y,b,_,z,L,E,M.x,M.y)&&O(M.prev,M,M.next)>=0)return!1;M=M.prevZ}for(;T&&T.z<=Le;){if(T.x>=R&&T.x<=W&&T.y>=F&&T.y<=Z&&T!==d&&T!==h&&A(y,b,_,z,L,E,T.x,T.y)&&O(T.prev,T,T.next)>=0)return!1;T=T.nextZ}return!0}function c(o,l,r){var u=o;do{var d=u.prev,p=u.next.next;!G(d,p)&&V(d,u,u.next,p)&&U(d,p)&&U(p,d)&&(l.push(d.i/r|0),l.push(u.i/r|0),l.push(p.i/r|0),j(u),j(u.next),u=o=p),u=u.next}while(u!==o);return t(u)}function f(o,l,r,u,d,p){var h=o;do{for(var y=h.next.next;y!==h.prev;){if(h.i!==y.i&&N(h,y)){var _=me(h,y);h=t(h,h.next),_=t(_,_.next),i(h,l,r,u,d,p,0),i(_,l,r,u,d,p,0);return}y=y.next}h=h.next}while(h!==o)}function g(o,l,r,u){var d=[],p,h,y,_,L;for(p=0,h=l.length;p<h;p++)y=l[p]*u,_=p<h-1?l[p+1]*u:o.length,L=e(o,y,_,u,!1),L===L.next&&(L.steiner=!0),d.push(I(L));for(d.sort(v),p=0;p<d.length;p++)r=x(d[p],r);return r}function v(o,l){return o.x-l.x}function x(o,l){var r=w(o,l);if(!r)return l;var u=me(r,o);return t(u,u.next),t(r,r.next)}function w(o,l){var r=l,u=o.x,d=o.y,p=-1/0,h;do{if(d<=r.y&&d>=r.next.y&&r.next.y!==r.y){var y=r.x+(d-r.y)*(r.next.x-r.x)/(r.next.y-r.y);if(y<=u&&y>p&&(p=y,h=r.x<r.next.x?r:r.next,y===u))return h}r=r.next}while(r!==l);if(!h)return null;var _=h,L=h.x,b=h.y,z=1/0,E;r=h;do u>=r.x&&r.x>=L&&u!==r.x&&A(d<b?u:p,d,L,b,d<b?p:u,d,r.x,r.y)&&(E=Math.abs(d-r.y)/(u-r.x),U(r,o)&&(E<z||E===z&&(r.x>h.x||r.x===h.x&&C(h,r)))&&(h=r,z=E)),r=r.next;while(r!==_);return h}function C(o,l){return O(o.prev,o,l.prev)<0&&O(l.next,o,o.next)<0}function m(o,l,r,u){var d=o;do d.z===0&&(d.z=P(d.x,d.y,l,r,u)),d.prevZ=d.prev,d.nextZ=d.next,d=d.next;while(d!==o);d.prevZ.nextZ=null,d.prevZ=null,S(d)}function S(o){var l,r,u,d,p,h,y,_,L=1;do{for(r=o,o=null,p=null,h=0;r;){for(h++,u=r,y=0,l=0;l<L&&(y++,u=u.nextZ,!!u);l++);for(_=L;y>0||_>0&&u;)y!==0&&(_===0||!u||r.z<=u.z)?(d=r,r=r.nextZ,y--):(d=u,u=u.nextZ,_--),p?p.nextZ=d:o=d,d.prevZ=p,p=d;r=u}p.nextZ=null,L*=2}while(h>1);return o}function P(o,l,r,u,d){return o=(o-r)*d|0,l=(l-u)*d|0,o=(o|o<<8)&16711935,o=(o|o<<4)&252645135,o=(o|o<<2)&858993459,o=(o|o<<1)&1431655765,l=(l|l<<8)&16711935,l=(l|l<<4)&252645135,l=(l|l<<2)&858993459,l=(l|l<<1)&1431655765,o|l<<1}function I(o){var l=o,r=o;do(l.x<r.x||l.x===r.x&&l.y<r.y)&&(r=l),l=l.next;while(l!==o);return r}function A(o,l,r,u,d,p,h,y){return(d-h)*(l-y)>=(o-h)*(p-y)&&(o-h)*(u-y)>=(r-h)*(l-y)&&(r-h)*(p-y)>=(d-h)*(u-y)}function N(o,l){return o.next.i!==l.i&&o.prev.i!==l.i&&!Ke(o,l)&&(U(o,l)&&U(l,o)&&Je(o,l)&&(O(o.prev,o,l.prev)||O(o,l.prev,l))||G(o,l)&&O(o.prev,o,o.next)>0&&O(l.prev,l,l.next)>0)}function O(o,l,r){return(l.y-o.y)*(r.x-l.x)-(l.x-o.x)*(r.y-l.y)}function G(o,l){return o.x===l.x&&o.y===l.y}function V(o,l,r,u){var d=J(O(o,l,r)),p=J(O(o,l,u)),h=J(O(r,u,o)),y=J(O(r,u,l));return!!(d!==p&&h!==y||d===0&&K(o,r,l)||p===0&&K(o,u,l)||h===0&&K(r,o,u)||y===0&&K(r,l,u))}function K(o,l,r){return l.x<=Math.max(o.x,r.x)&&l.x>=Math.min(o.x,r.x)&&l.y<=Math.max(o.y,r.y)&&l.y>=Math.min(o.y,r.y)}function J(o){return o>0?1:o<0?-1:0}function Ke(o,l){var r=o;do{if(r.i!==o.i&&r.next.i!==o.i&&r.i!==l.i&&r.next.i!==l.i&&V(r,r.next,o,l))return!0;r=r.next}while(r!==o);return!1}function U(o,l){return O(o.prev,o,o.next)<0?O(o,l,o.next)>=0&&O(o,o.prev,l)>=0:O(o,l,o.prev)<0||O(o,o.next,l)<0}function Je(o,l){var r=o,u=!1,d=(o.x+l.x)/2,p=(o.y+l.y)/2;do r.y>p!=r.next.y>p&&r.next.y!==r.y&&d<(r.next.x-r.x)*(p-r.y)/(r.next.y-r.y)+r.x&&(u=!u),r=r.next;while(r!==o);return u}function me(o,l){var r=new se(o.i,o.x,o.y),u=new se(l.i,l.x,l.y),d=o.next,p=l.prev;return o.next=l,l.prev=o,r.next=d,d.prev=r,u.next=r,r.prev=u,p.next=u,u.prev=p,u}function Pe(o,l,r,u){var d=new se(o,l,r);return u?(d.next=u.next,d.prev=u,u.next.prev=d,u.next=d):(d.prev=d,d.next=d),d}function j(o){o.next.prev=o.prev,o.prev.next=o.next,o.prevZ&&(o.prevZ.nextZ=o.nextZ),o.nextZ&&(o.nextZ.prevZ=o.prevZ)}function se(o,l,r){this.i=o,this.x=l,this.y=r,this.prev=null,this.next=null,this.z=0,this.prevZ=null,this.nextZ=null,this.steiner=!1}n.deviation=function(o,l,r,u){var d=l&&l.length,p=d?l[0]*r:o.length,h=Math.abs(re(o,0,p,r));if(d)for(var y=0,_=l.length;y<_;y++){var L=l[y]*r,b=y<_-1?l[y+1]*r:o.length;h-=Math.abs(re(o,L,b,r))}var z=0;for(y=0;y<u.length;y+=3){var E=u[y]*r,R=u[y+1]*r,F=u[y+2]*r;z+=Math.abs((o[E]-o[F])*(o[R+1]-o[E+1])-(o[E]-o[R])*(o[F+1]-o[E+1]))}return h===0&&z===0?0:Math.abs((z-h)/h)};function re(o,l,r,u){for(var d=0,p=l,h=r-u;p<r;p+=u)d+=(o[h]-o[p])*(o[p+1]+o[h+1]),h=p;return d}return n.flatten=function(o){for(var l=o[0][0].length,r={vertices:[],holes:[],dimensions:l},u=0,d=0;d<o.length;d++){for(var p=0;p<o[d].length;p++)for(var h=0;h<l;h++)r.vertices.push(o[d][p][h]);d>0&&(u+=o[d-1].length,r.holes.push(u))}return r},X.exports}var St=Ct();const It=Qe(St),Q=xe.CLOCKWISE,Te=xe.COUNTER_CLOCKWISE,k={};function At(n){if(n=n&&n.positions||n,!Array.isArray(n)&&!ArrayBuffer.isView(n))throw new Error("invalid polygon")}function H(n){return"positions"in n?n.positions:n}function te(n){return"holeIndices"in n?n.holeIndices:null}function Et(n){return Array.isArray(n[0])}function Mt(n){return n.length>=1&&n[0].length>=2&&Number.isFinite(n[0][0])}function Tt(n){const e=n[0],t=n[n.length-1];return e[0]===t[0]&&e[1]===t[1]&&e[2]===t[2]}function Ot(n,e,t,i){for(let a=0;a<e;a++)if(n[t+a]!==n[i-e+a])return!1;return!0}function Oe(n,e,t,i,a){let s=e;const c=t.length;for(let f=0;f<c;f++)for(let g=0;g<i;g++)n[s++]=t[f][g]||0;if(!Tt(t))for(let f=0;f<i;f++)n[s++]=t[0][f]||0;return k.start=e,k.end=s,k.size=i,ye(n,a,k),s}function ze(n,e,t,i,a=0,s,c){s=s||t.length;const f=s-a;if(f<=0)return e;let g=e;for(let v=0;v<f;v++)n[g++]=t[a+v];if(!Ot(t,i,a,s))for(let v=0;v<i;v++)n[g++]=t[a+v];return k.start=e,k.end=g,k.size=i,ye(n,c,k),g}function zt(n,e){At(n);const t=[],i=[];if("positions"in n){const{positions:a,holeIndices:s}=n;if(s){let c=0;for(let f=0;f<=s.length;f++)c=ze(t,c,a,e,s[f-1],s[f],f===0?Q:Te),i.push(c);return i.pop(),{positions:t,holeIndices:i}}n=a}if(!Et(n))return ze(t,0,n,e,0,t.length,Q),t;if(!Mt(n)){let a=0;for(const[s,c]of n.entries())a=Oe(t,a,c,e,s===0?Q:Te),i.push(a);return i.pop(),{positions:t,holeIndices:i}}return Oe(t,0,n,e,Q),t}function fe(n,e,t){const i=n.length/3;let a=0;for(let s=0;s<i;s++){const c=(s+1)%i;a+=n[s*3+e]*n[c*3+t],a-=n[c*3+e]*n[s*3+t]}return Math.abs(a/2)}function Fe(n,e,t,i){const a=n.length/3;for(let s=0;s<a;s++){const c=s*3,f=n[c+0],g=n[c+1],v=n[c+2];n[c+e]=f,n[c+t]=g,n[c+i]=v}}function Ft(n,e,t,i){let a=te(n);a&&(a=a.map(f=>f/e));let s=H(n);const c=i&&e===3;if(t){const f=s.length;s=s.slice();const g=[];for(let v=0;v<f;v+=e){g[0]=s[v],g[1]=s[v+1],c&&(g[2]=s[v+2]);const x=t(g);s[v]=x[0],s[v+1]=x[1],c&&(s[v+2]=x[2])}}if(c){const f=fe(s,0,1),g=fe(s,0,2),v=fe(s,1,2);if(!f&&!g&&!v)return[];f>g&&f>v||(g>v?(t||(s=s.slice()),Fe(s,0,2,1)):(t||(s=s.slice()),Fe(s,2,0,1)))}return It(s,a,e)}class bt extends Ge{constructor(e){const{fp64:t,IndexType:i=Uint32Array}=e;super({...e,attributes:{positions:{size:3,type:t?Float64Array:Float32Array},vertexValid:{type:Uint16Array,size:1},indices:{type:i,size:1}}})}get(e){const{attributes:t}=this;return e==="indices"?t.indices&&t.indices.subarray(0,this.vertexCount):t[e]}updateGeometry(e){super.updateGeometry(e);const t=this.buffers.indices;if(t)this.vertexCount=(t.value||t).length;else if(this.data&&!this.getGeometry)throw new Error("missing indices buffer")}normalizeGeometry(e){if(this.normalize){const t=zt(e,this.positionSize);return this.opts.resolution?ke(H(t),te(t),{size:this.positionSize,gridResolution:this.opts.resolution,edgeTypes:!0}):this.opts.wrapLongitude?at(H(t),te(t),{size:this.positionSize,maxLatitude:86,edgeTypes:!0}):t}return e}getGeometrySize(e){if(be(e)){let t=0;for(const i of e)t+=this.getGeometrySize(i);return t}return H(e).length/this.positionSize}getGeometryFromBuffer(e){return this.normalize||!this.buffers.indices?super.getGeometryFromBuffer(e):null}updateGeometryAttributes(e,t){if(e&&be(e))for(const i of e){const a=this.getGeometrySize(i);t.geometrySize=a,this.updateGeometryAttributes(i,t),t.vertexStart+=a,t.indexStart=this.indexStarts[t.geometryIndex+1]}else{const i=e;this._updateIndices(i,t),this._updatePositions(i,t),this._updateVertexValid(i,t)}}_updateIndices(e,{geometryIndex:t,vertexStart:i,indexStart:a}){const{attributes:s,indexStarts:c,typedArrayManager:f}=this;let g=s.indices;if(!g||!e)return;let v=a;const x=Ft(e,this.positionSize,this.opts.preproject,this.opts.full3d);g=f.allocate(g,a+x.length,{copy:!0});for(let w=0;w<x.length;w++)g[v++]=x[w]+i;c[t+1]=a+x.length,s.indices=g}_updatePositions(e,{vertexStart:t,geometrySize:i}){const{attributes:{positions:a},positionSize:s}=this;if(!a||!e)return;const c=H(e);for(let f=t,g=0;g<i;f++,g++){const v=c[g*s],x=c[g*s+1],w=s>2?c[g*s+2]:0;a[f*3]=v,a[f*3+1]=x,a[f*3+2]=w}}_updateVertexValid(e,{vertexStart:t,geometrySize:i}){const{positionSize:a}=this,s=this.attributes.vertexValid,c=e&&te(e);if(e&&e.edgeTypes?s.set(e.edgeTypes,t):s.fill(1,t,t+i),c)for(let f=0;f<c.length;f++)s[t+c[f]/a-1]=0;s[t+i-1]=0}}function be(n){return Array.isArray(n)&&n.length>0&&!Number.isFinite(n[0])}const Ne=`uniform solidPolygonUniforms {
  bool extruded;
  bool isWireframe;
  float elevationScale;
} solidPolygon;
`,Nt={name:"solidPolygon",vs:Ne,fs:Ne,uniformTypes:{extruded:"f32",isWireframe:"f32",elevationScale:"f32"}},He=`in vec4 fillColors;
in vec4 lineColors;
in vec3 pickingColors;
out vec4 vColor;
struct PolygonProps {
vec3 positions;
vec3 positions64Low;
vec3 normal;
float elevations;
};
vec3 project_offset_normal(vec3 vector) {
if (project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT ||
project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT_OFFSETS) {
return normalize(vector * project.commonUnitsPerWorldUnit);
}
return project_normal(vector);
}
void calculatePosition(PolygonProps props) {
vec3 pos = props.positions;
vec3 pos64Low = props.positions64Low;
vec3 normal = props.normal;
vec4 colors = solidPolygon.isWireframe ? lineColors : fillColors;
geometry.worldPosition = props.positions;
geometry.pickingColor = pickingColors;
if (solidPolygon.extruded) {
pos.z += props.elevations * solidPolygon.elevationScale;
}
gl_Position = project_position_to_clipspace(pos, pos64Low, vec3(0.), geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
if (solidPolygon.extruded) {
#ifdef IS_SIDE_VERTEX
normal = project_offset_normal(normal);
#else
normal = project_normal(normal);
#endif
geometry.normal = normal;
vec3 lightColor = lighting_getLightColor(colors.rgb, project.cameraPosition, geometry.position.xyz, geometry.normal);
vColor = vec4(lightColor, colors.a * layer.opacity);
} else {
vColor = vec4(colors.rgb, colors.a * layer.opacity);
}
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,Rt=`#version 300 es
#define SHADER_NAME solid-polygon-layer-vertex-shader
in vec3 vertexPositions;
in vec3 vertexPositions64Low;
in float elevations;
${He}
void main(void) {
PolygonProps props;
props.positions = vertexPositions;
props.positions64Low = vertexPositions64Low;
props.elevations = elevations;
props.normal = vec3(0.0, 0.0, 1.0);
calculatePosition(props);
}
`,Gt=`#version 300 es
#define SHADER_NAME solid-polygon-layer-vertex-shader-side
#define IS_SIDE_VERTEX
in vec2 positions;
in vec3 vertexPositions;
in vec3 nextVertexPositions;
in vec3 vertexPositions64Low;
in vec3 nextVertexPositions64Low;
in float elevations;
in float instanceVertexValid;
${He}
void main(void) {
if(instanceVertexValid < 0.5){
gl_Position = vec4(0.);
return;
}
PolygonProps props;
vec3 pos;
vec3 pos64Low;
vec3 nextPos;
vec3 nextPos64Low;
#if RING_WINDING_ORDER_CW == 1
pos = vertexPositions;
pos64Low = vertexPositions64Low;
nextPos = nextVertexPositions;
nextPos64Low = nextVertexPositions64Low;
#else
pos = nextVertexPositions;
pos64Low = nextVertexPositions64Low;
nextPos = vertexPositions;
nextPos64Low = vertexPositions64Low;
#endif
props.positions = mix(pos, nextPos, positions.x);
props.positions64Low = mix(pos64Low, nextPos64Low, positions.x);
props.normal = vec3(
pos.y - nextPos.y + (pos64Low.y - nextPos64Low.y),
nextPos.x - pos.x + (nextPos64Low.x - pos64Low.x),
0.0);
props.elevations = elevations * positions.y;
calculatePosition(props);
}
`,Dt=`#version 300 es
#define SHADER_NAME solid-polygon-layer-fragment-shader
precision highp float;
in vec4 vColor;
out vec4 fragColor;
void main(void) {
fragColor = vColor;
geometry.uv = vec2(0.);
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,ne=[0,0,0,255],kt={filled:!0,extruded:!1,wireframe:!1,_normalize:!0,_windingOrder:"CW",_full3d:!1,elevationScale:{type:"number",min:0,value:1},getPolygon:{type:"accessor",value:n=>n.polygon},getElevation:{type:"accessor",value:1e3},getFillColor:{type:"accessor",value:ne},getLineColor:{type:"accessor",value:ne},material:!0},q={enter:(n,e)=>e.length?e.subarray(e.length-n.length):n};class $e extends he{getShaders(e){return super.getShaders({vs:e==="top"?Rt:Gt,fs:Dt,defines:{RING_WINDING_ORDER_CW:!this.props._normalize&&this.props._windingOrder==="CCW"?0:1},modules:[ge,Re,ve,Nt]})}get wrapLongitude(){return!1}getBounds(){return this.getAttributeManager()?.getBounds(["vertexPositions"])}initializeState(){const{viewport:e}=this.context;let{coordinateSystem:t}=this.props;const{_full3d:i}=this.props;e.isGeospatial&&t===ae.DEFAULT&&(t=ae.LNGLAT);let a;t===ae.LNGLAT&&(i?a=e.projectPosition.bind(e):a=e.projectFlat.bind(e)),this.setState({numInstances:0,polygonTesselator:new bt({preproject:a,fp64:this.use64bitPositions(),IndexType:Uint32Array})});const s=this.getAttributeManager(),c=!0;s.remove(["instancePickingColors"]),s.add({indices:{size:1,isIndexed:!0,update:this.calculateIndices,noAlloc:c},vertexPositions:{size:3,type:"float64",stepMode:"dynamic",fp64:this.use64bitPositions(),transition:q,accessor:"getPolygon",update:this.calculatePositions,noAlloc:c,shaderAttributes:{nextVertexPositions:{vertexOffset:1}}},instanceVertexValid:{size:1,type:"uint16",stepMode:"instance",update:this.calculateVertexValid,noAlloc:c},elevations:{size:1,stepMode:"dynamic",transition:q,accessor:"getElevation"},fillColors:{size:this.props.colorFormat.length,type:"unorm8",stepMode:"dynamic",transition:q,accessor:"getFillColor",defaultValue:ne},lineColors:{size:this.props.colorFormat.length,type:"unorm8",stepMode:"dynamic",transition:q,accessor:"getLineColor",defaultValue:ne},pickingColors:{size:4,type:"uint8",stepMode:"dynamic",accessor:(f,{index:g,target:v})=>this.encodePickingColor(f&&f.__source?f.__source.index:g,v)}})}getPickingInfo(e){const t=super.getPickingInfo(e),{index:i}=t,a=this.props.data;return a[0]&&a[0].__source&&(t.object=a.find(s=>s.__source.index===i)),t}disablePickingIndex(e){const t=this.props.data;if(t[0]&&t[0].__source)for(let i=0;i<t.length;i++)t[i].__source.index===e&&this._disablePickingIndex(i);else super.disablePickingIndex(e)}draw({uniforms:e}){const{extruded:t,filled:i,wireframe:a,elevationScale:s}=this.props,{topModel:c,sideModel:f,wireframeModel:g,polygonTesselator:v}=this.state,x={extruded:!!t,elevationScale:s,isWireframe:!1};g&&a&&(g.setInstanceCount(v.instanceCount-1),g.shaderInputs.setProps({solidPolygon:{...x,isWireframe:!0}}),g.draw(this.context.renderPass)),f&&i&&(f.setInstanceCount(v.instanceCount-1),f.shaderInputs.setProps({solidPolygon:x}),f.draw(this.context.renderPass)),c&&i&&(c.setVertexCount(v.vertexCount),c.shaderInputs.setProps({solidPolygon:x}),c.draw(this.context.renderPass))}updateState(e){super.updateState(e),this.updateGeometry(e);const{props:t,oldProps:i,changeFlags:a}=e,s=this.getAttributeManager();(a.extensionsChanged||t.filled!==i.filled||t.extruded!==i.extruded)&&(this.state.models?.forEach(f=>f.destroy()),this.setState(this._getModels()),s.invalidateAll())}updateGeometry({props:e,oldProps:t,changeFlags:i}){if(i.dataChanged||i.updateTriggersChanged&&(i.updateTriggersChanged.all||i.updateTriggersChanged.getPolygon)){const{polygonTesselator:s}=this.state,c=e.data.attributes||{};s.updateGeometry({data:e.data,normalize:e._normalize,geometryBuffer:c.getPolygon,buffers:c,getGeometry:e.getPolygon,positionFormat:e.positionFormat,wrapLongitude:e.wrapLongitude,resolution:this.context.viewport.resolution,fp64:this.use64bitPositions(),dataChanged:i.dataChanged,full3d:e._full3d}),this.setState({numInstances:s.instanceCount,startIndices:s.vertexStarts}),i.dataChanged||this.getAttributeManager().invalidateAll()}}_getModels(){const{id:e,filled:t,extruded:i}=this.props;let a,s,c;if(t){const f=this.getShaders("top");f.defines.NON_INSTANCED_MODEL=1;const g=this.getAttributeManager().getBufferLayouts({isInstanced:!1});a=new B(this.context.device,{...f,id:`${e}-top`,topology:"triangle-list",bufferLayout:g,isIndexed:!0,userData:{excludeAttributes:{instanceVertexValid:!0}}})}if(i){const f=this.getAttributeManager().getBufferLayouts({isInstanced:!0});s=new B(this.context.device,{...this.getShaders("side"),id:`${e}-side`,bufferLayout:f,geometry:new ie({topology:"triangle-strip",attributes:{positions:{size:2,value:new Float32Array([1,0,0,0,1,1,0,1])}}}),isInstanced:!0,userData:{excludeAttributes:{indices:!0}}}),c=new B(this.context.device,{...this.getShaders("side"),id:`${e}-wireframe`,bufferLayout:f,geometry:new ie({topology:"line-strip",attributes:{positions:{size:2,value:new Float32Array([1,0,0,0,0,1,1,1])}}}),isInstanced:!0,userData:{excludeAttributes:{indices:!0}}})}return{models:[s,c,a].filter(Boolean),topModel:a,sideModel:s,wireframeModel:c}}calculateIndices(e){const{polygonTesselator:t}=this.state;e.startIndices=t.indexStarts,e.value=t.get("indices")}calculatePositions(e){const{polygonTesselator:t}=this.state;e.startIndices=t.vertexStarts,e.value=t.get("positions")}calculateVertexValid(e){e.value=this.state.polygonTesselator.get("vertexValid")}}$e.defaultProps=kt;$e.layerName="SolidPolygonLayer";export{je as C,Ze as P,$e as S,zt as n};
//# sourceMappingURL=solid-polygon-layer-DJFl_7Ca.js.map
