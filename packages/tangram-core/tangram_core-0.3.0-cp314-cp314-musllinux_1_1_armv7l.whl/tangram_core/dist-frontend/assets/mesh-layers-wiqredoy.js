import{l as qt,c as $t,L as Bt,p as mt,h as en,d as ht,G as $}from"./layer-DPcO4AXQ.js";import{ap as tn,aq as nn,H as Je,ar as g,aC as sn,aD as pt,aE as rn,aF as on,aG as se,aH as an,aI as cn,au as ln,aJ as Ct,aK as fn,aL as un,aM as An,aN as dn,aO as Bn,e as mn,aP as hn,aQ as we,aB as pn,aR as Ae,d as Cn,aS as bn,aT as gn,aU as En,aV as In,aW as Mn,b as x,N as G,y as L,O as de,x as ee}from"./deep-equal-BTW2ZN6S.js";import{T as Tn}from"./array-utils-flat-BBMak426.js";import{u as yn,M as bt}from"./shader-Cbdysp2j.js";import{t as V,u as Fn,V as _n,v as Oe,a as K,i as Rn,s as gt}from"./webgl-developer-tools-utTNOsNf.js";import{g as Gn,a as vn,I as Dn}from"./image-loader-hHJsndO6.js";async function Et(t,e,n,s){return s._parse(t,e,n,s)}function Sn(t){globalThis.loaders||={},globalThis.loaders.modules||={},Object.assign(globalThis.loaders.modules,t)}function On(t){return globalThis.loaders?.modules?.[t]||null}const Be={};async function v(t,e=null,n={},s=null){return e&&(t=xn(t,e,n,s)),Be[t]=Be[t]||Ln(t),await Be[t]}function xn(t,e,n={},s=null){if(!n.useLocalLibraries&&t.startsWith("http"))return t;s=s||t;const r=n.modules||{};return r[s]?r[s]:V?n.CDN?(Fn(n.CDN.startsWith("http")),`${n.CDN}/${e}@${_n}/dist/libs/${s}`):Oe?`../src/libs/${s}`:`modules/${e}/src/libs/${s}`:`modules/${e}/dist/libs/${s}`}async function Ln(t){if(t.endsWith("wasm"))return await Pn(t);if(!V)try{const{requireFromFile:n}=globalThis.loaders||{};return await n?.(t)}catch(n){return console.error(n),null}if(Oe)return importScripts(t);const e=await Un(t);return Hn(e,t)}function Hn(t,e){if(!V){const{requireFromString:s}=globalThis.loaders||{};return s?.(t,e)}if(Oe)return eval.call(globalThis,t),null;const n=document.createElement("script");n.id=e;try{n.appendChild(document.createTextNode(t))}catch{n.text=t}return document.body.appendChild(n),null}async function Pn(t){const{readFileAsArrayBuffer:e}=globalThis.loaders||{};return V||!e||t.startsWith("http")?await(await fetch(t)).arrayBuffer():await e(t)}async function Un(t){const{readFileAsText:e}=globalThis.loaders||{};return V||!e||t.startsWith("http")?await(await fetch(t)).text():await e(t)}function Nn(t,e=5){return typeof t=="string"?t.slice(0,e):ArrayBuffer.isView(t)?Ke(t.buffer,t.byteOffset,e):t instanceof ArrayBuffer?Ke(t,0,e):""}function Ke(t,e,n){if(t.byteLength<=e+n)return"";const s=new DataView(t);let r="";for(let o=0;o<n;o++)r+=String.fromCharCode(s.getUint8(e+o));return r}function Jn(t){try{return JSON.parse(t)}catch{throw new Error(`Failed to parse JSON from data starting with "${Nn(t)}"`)}}function X(t,e){return K(t>=0),K(e>0),t+(e-1)&-4}function wn(t,e,n){let s;if(t instanceof ArrayBuffer)s=new Uint8Array(t);else{const r=t.byteOffset,o=t.byteLength;s=new Uint8Array(t.buffer||t.arrayBuffer,r,o)}return e.set(s,n),n+X(s.byteLength,4)}function Kn(t){switch(t.constructor){case Int8Array:return"int8";case Uint8Array:case Uint8ClampedArray:return"uint8";case Int16Array:return"int16";case Uint16Array:return"uint16";case Int32Array:return"int32";case Uint32Array:return"uint32";case Float32Array:return"float32";case Float64Array:return"float64";default:return"null"}}function It(t){let e=1/0,n=1/0,s=1/0,r=-1/0,o=-1/0,i=-1/0;const a=t.POSITION?t.POSITION.value:[],c=a&&a.length;for(let l=0;l<c;l+=3){const f=a[l],u=a[l+1],A=a[l+2];e=f<e?f:e,n=u<n?u:n,s=A<s?A:s,r=f>r?f:r,o=u>o?u:o,i=A>i?A:i}return[[e,n,s],[r,o,i]]}function jn(t,e,n){const s=Kn(e.value),r=n||Vn(e);return{name:t,type:{type:"fixed-size-list",listSize:e.size,children:[{name:"value",type:s}]},nullable:!1,metadata:r}}function Vn(t){const e={};return"byteOffset"in t&&(e.byteOffset=t.byteOffset.toString(10)),"byteStride"in t&&(e.byteStride=t.byteStride.toString(10)),"normalized"in t&&(e.normalized=t.normalized.toString()),e}const me={};function Xn(t){if(me[t]===void 0){const e=Rn?Yn(t):Qn(t);me[t]=e}return me[t]}function Qn(t){const e=["image/png","image/jpeg","image/gif"],n=globalThis.loaders?.imageFormatsNode||e;return!!globalThis.loaders?.parseImageNode&&n.includes(t)}function Yn(t){switch(t){case"image/avif":case"image/webp":return kn(t);default:return!0}}function kn(t){try{return document.createElement("canvas").toDataURL(t).indexOf(`data:${t}`)===0}catch{return!1}}let Y;class xe extends tn{static get ZERO(){return Y||(Y=new xe(0,0,0,0),Object.freeze(Y)),Y}constructor(e=0,n=0,s=0,r=0){super(-0,-0,-0,-0),nn(e)&&arguments.length===1?this.copy(e):(Je.debug&&(g(e),g(n),g(s),g(r)),this[0]=e,this[1]=n,this[2]=s,this[3]=r)}set(e,n,s,r){return this[0]=e,this[1]=n,this[2]=s,this[3]=r,this.check()}copy(e){return this[0]=e[0],this[1]=e[1],this[2]=e[2],this[3]=e[3],this.check()}fromObject(e){return Je.debug&&(g(e.x),g(e.y),g(e.z),g(e.w)),this[0]=e.x,this[1]=e.y,this[2]=e.z,this[3]=e.w,this}toObject(e){return e.x=this[0],e.y=this[1],e.z=this[2],e.w=this[3],e}get ELEMENTS(){return 4}get z(){return this[2]}set z(e){this[2]=g(e)}get w(){return this[3]}set w(e){this[3]=g(e)}transform(e){return sn(this,this,e),this.check()}transformByMatrix3(e){return pt(this,this,e),this.check()}transformByMatrix2(e){return rn(this,this,e),this.check()}transformByQuaternion(e){return on(this,this,e),this.check()}applyMatrix4(e){return e.transform(this,this),this}}function zn(){const t=new se(9);return se!=Float32Array&&(t[1]=0,t[2]=0,t[3]=0,t[5]=0,t[6]=0,t[7]=0),t[0]=1,t[4]=1,t[8]=1,t}function Wn(t,e){if(t===e){const n=e[1],s=e[2],r=e[5];t[1]=e[3],t[2]=e[6],t[3]=n,t[5]=e[7],t[6]=s,t[7]=r}else t[0]=e[0],t[1]=e[3],t[2]=e[6],t[3]=e[1],t[4]=e[4],t[5]=e[7],t[6]=e[2],t[7]=e[5],t[8]=e[8];return t}function Zn(t,e){const n=e[0],s=e[1],r=e[2],o=e[3],i=e[4],a=e[5],c=e[6],l=e[7],f=e[8],u=f*i-a*l,A=-f*o+a*c,d=l*o-i*c;let B=n*u+s*A+r*d;return B?(B=1/B,t[0]=u*B,t[1]=(-f*s+r*l)*B,t[2]=(a*s-r*i)*B,t[3]=A*B,t[4]=(f*n-r*c)*B,t[5]=(-a*n+r*o)*B,t[6]=d*B,t[7]=(-l*n+s*c)*B,t[8]=(i*n-s*o)*B,t):null}function qn(t){const e=t[0],n=t[1],s=t[2],r=t[3],o=t[4],i=t[5],a=t[6],c=t[7],l=t[8];return e*(l*o-i*c)+n*(-l*r+i*a)+s*(c*r-o*a)}function je(t,e,n){const s=e[0],r=e[1],o=e[2],i=e[3],a=e[4],c=e[5],l=e[6],f=e[7],u=e[8],A=n[0],d=n[1],B=n[2],m=n[3],p=n[4],C=n[5],I=n[6],h=n[7],N=n[8];return t[0]=A*s+d*i+B*l,t[1]=A*r+d*a+B*f,t[2]=A*o+d*c+B*u,t[3]=m*s+p*i+C*l,t[4]=m*r+p*a+C*f,t[5]=m*o+p*c+C*u,t[6]=I*s+h*i+N*l,t[7]=I*r+h*a+N*f,t[8]=I*o+h*c+N*u,t}function $n(t,e,n){const s=e[0],r=e[1],o=e[2],i=e[3],a=e[4],c=e[5],l=e[6],f=e[7],u=e[8],A=n[0],d=n[1];return t[0]=s,t[1]=r,t[2]=o,t[3]=i,t[4]=a,t[5]=c,t[6]=A*s+d*i+l,t[7]=A*r+d*a+f,t[8]=A*o+d*c+u,t}function es(t,e,n){const s=e[0],r=e[1],o=e[2],i=e[3],a=e[4],c=e[5],l=e[6],f=e[7],u=e[8],A=Math.sin(n),d=Math.cos(n);return t[0]=d*s+A*i,t[1]=d*r+A*a,t[2]=d*o+A*c,t[3]=d*i-A*s,t[4]=d*a-A*r,t[5]=d*c-A*o,t[6]=l,t[7]=f,t[8]=u,t}function Ve(t,e,n){const s=n[0],r=n[1];return t[0]=s*e[0],t[1]=s*e[1],t[2]=s*e[2],t[3]=r*e[3],t[4]=r*e[4],t[5]=r*e[5],t[6]=e[6],t[7]=e[7],t[8]=e[8],t}function ts(t,e){const n=e[0],s=e[1],r=e[2],o=e[3],i=n+n,a=s+s,c=r+r,l=n*i,f=s*i,u=s*a,A=r*i,d=r*a,B=r*c,m=o*i,p=o*a,C=o*c;return t[0]=1-u-B,t[3]=f-C,t[6]=A+p,t[1]=f+C,t[4]=1-l-B,t[7]=d-m,t[2]=A-p,t[5]=d+m,t[8]=1-l-u,t}var _e;(function(t){t[t.COL0ROW0=0]="COL0ROW0",t[t.COL0ROW1=1]="COL0ROW1",t[t.COL0ROW2=2]="COL0ROW2",t[t.COL1ROW0=3]="COL1ROW0",t[t.COL1ROW1=4]="COL1ROW1",t[t.COL1ROW2=5]="COL1ROW2",t[t.COL2ROW0=6]="COL2ROW0",t[t.COL2ROW1=7]="COL2ROW1",t[t.COL2ROW2=8]="COL2ROW2"})(_e||(_e={}));const ns=Object.freeze([1,0,0,0,1,0,0,0,1]);class Q extends an{static get IDENTITY(){return rs()}static get ZERO(){return ss()}get ELEMENTS(){return 9}get RANK(){return 3}get INDICES(){return _e}constructor(e,...n){super(-0,-0,-0,-0,-0,-0,-0,-0,-0),arguments.length===1&&Array.isArray(e)?this.copy(e):n.length>0?this.copy([e,...n]):this.identity()}copy(e){return this[0]=e[0],this[1]=e[1],this[2]=e[2],this[3]=e[3],this[4]=e[4],this[5]=e[5],this[6]=e[6],this[7]=e[7],this[8]=e[8],this.check()}identity(){return this.copy(ns)}fromObject(e){return this.check()}fromQuaternion(e){return ts(this,e),this.check()}set(e,n,s,r,o,i,a,c,l){return this[0]=e,this[1]=n,this[2]=s,this[3]=r,this[4]=o,this[5]=i,this[6]=a,this[7]=c,this[8]=l,this.check()}setRowMajor(e,n,s,r,o,i,a,c,l){return this[0]=e,this[1]=r,this[2]=a,this[3]=n,this[4]=o,this[5]=c,this[6]=s,this[7]=i,this[8]=l,this.check()}determinant(){return qn(this)}transpose(){return Wn(this,this),this.check()}invert(){return Zn(this,this),this.check()}multiplyLeft(e){return je(this,e,this),this.check()}multiplyRight(e){return je(this,this,e),this.check()}rotate(e){return es(this,this,e),this.check()}scale(e){return Array.isArray(e)?Ve(this,this,e):Ve(this,this,[e,e]),this.check()}translate(e){return $n(this,this,e),this.check()}transform(e,n){let s;switch(e.length){case 2:s=ln(n||[-0,-0],e,this);break;case 3:s=cn(n||[-0,-0,-0],e,this);break;case 4:s=pt(n||[-0,-0,-0,-0],e,this);break;default:throw new Error("Illegal vector")}return Ct(s,e.length),s}transformVector(e,n){return this.transform(e,n)}transformVector2(e,n){return this.transform(e,n)}transformVector3(e,n){return this.transform(e,n)}}let k,z=null;function ss(){return k||(k=new Q([0,0,0,0,0,0,0,0,0]),Object.freeze(k)),k}function rs(){return z||(z=new Q,Object.freeze(z)),z}function Xe(){const t=new se(4);return se!=Float32Array&&(t[0]=0,t[1]=0,t[2]=0),t[3]=1,t}function os(t){return t[0]=0,t[1]=0,t[2]=0,t[3]=1,t}function Mt(t,e,n){n=n*.5;const s=Math.sin(n);return t[0]=s*e[0],t[1]=s*e[1],t[2]=s*e[2],t[3]=Math.cos(n),t}function Qe(t,e,n){const s=e[0],r=e[1],o=e[2],i=e[3],a=n[0],c=n[1],l=n[2],f=n[3];return t[0]=s*f+i*a+r*l-o*c,t[1]=r*f+i*c+o*a-s*l,t[2]=o*f+i*l+s*c-r*a,t[3]=i*f-s*a-r*c-o*l,t}function is(t,e,n){n*=.5;const s=e[0],r=e[1],o=e[2],i=e[3],a=Math.sin(n),c=Math.cos(n);return t[0]=s*c+i*a,t[1]=r*c+o*a,t[2]=o*c-r*a,t[3]=i*c-s*a,t}function as(t,e,n){n*=.5;const s=e[0],r=e[1],o=e[2],i=e[3],a=Math.sin(n),c=Math.cos(n);return t[0]=s*c-o*a,t[1]=r*c+i*a,t[2]=o*c+s*a,t[3]=i*c-r*a,t}function cs(t,e,n){n*=.5;const s=e[0],r=e[1],o=e[2],i=e[3],a=Math.sin(n),c=Math.cos(n);return t[0]=s*c+r*a,t[1]=r*c-s*a,t[2]=o*c+i*a,t[3]=i*c-o*a,t}function ls(t,e){const n=e[0],s=e[1],r=e[2];return t[0]=n,t[1]=s,t[2]=r,t[3]=Math.sqrt(Math.abs(1-n*n-s*s-r*r)),t}function te(t,e,n,s){const r=e[0],o=e[1],i=e[2],a=e[3];let c=n[0],l=n[1],f=n[2],u=n[3],A,d,B,m,p;return A=r*c+o*l+i*f+a*u,A<0&&(A=-A,c=-c,l=-l,f=-f,u=-u),1-A>En?(d=Math.acos(A),p=Math.sin(d),B=Math.sin((1-s)*d)/p,m=Math.sin(s*d)/p):(B=1-s,m=s),t[0]=B*r+m*c,t[1]=B*o+m*l,t[2]=B*i+m*f,t[3]=B*a+m*u,t}function fs(t,e){const n=e[0],s=e[1],r=e[2],o=e[3],i=n*n+s*s+r*r+o*o,a=i?1/i:0;return t[0]=-n*a,t[1]=-s*a,t[2]=-r*a,t[3]=o*a,t}function us(t,e){return t[0]=-e[0],t[1]=-e[1],t[2]=-e[2],t[3]=e[3],t}function Tt(t,e){const n=e[0]+e[4]+e[8];let s;if(n>0)s=Math.sqrt(n+1),t[3]=.5*s,s=.5/s,t[0]=(e[5]-e[7])*s,t[1]=(e[6]-e[2])*s,t[2]=(e[1]-e[3])*s;else{let r=0;e[4]>e[0]&&(r=1),e[8]>e[r*3+r]&&(r=2);const o=(r+1)%3,i=(r+2)%3;s=Math.sqrt(e[r*3+r]-e[o*3+o]-e[i*3+i]+1),t[r]=.5*s,s=.5/s,t[3]=(e[o*3+i]-e[i*3+o])*s,t[o]=(e[o*3+r]+e[r*3+o])*s,t[i]=(e[i*3+r]+e[r*3+i])*s}return t}const As=dn,ds=mn,Bs=An,ms=Bn,hs=fn,ps=un,yt=gn,Cs=(function(){const t=hn(),e=we(1,0,0),n=we(0,1,0);return function(s,r,o){const i=pn(r,o);return i<-.999999?(Ae(t,e,r),Cn(t)<1e-6&&Ae(t,n,r),bn(t,t),Mt(s,t,Math.PI),s):i>.999999?(s[0]=0,s[1]=0,s[2]=0,s[3]=1,s):(Ae(t,r,o),s[0]=t[0],s[1]=t[1],s[2]=t[2],s[3]=1+i,yt(s,s))}})();(function(){const t=Xe(),e=Xe();return function(n,s,r,o,i,a){return te(t,s,i,a),te(e,r,o,a),te(n,t,e,2*a*(1-a)),n}})();(function(){const t=zn();return function(e,n,s,r){return t[0]=s[0],t[3]=s[1],t[6]=s[2],t[1]=r[0],t[4]=r[1],t[7]=r[2],t[2]=-n[0],t[5]=-n[1],t[8]=-n[2],yt(e,Tt(e,t))}})();const bs=[0,0,0,1];class gs extends In{constructor(e=0,n=0,s=0,r=1){super(-0,-0,-0,-0),Array.isArray(e)&&arguments.length===1?this.copy(e):this.set(e,n,s,r)}copy(e){return this[0]=e[0],this[1]=e[1],this[2]=e[2],this[3]=e[3],this.check()}set(e,n,s,r){return this[0]=e,this[1]=n,this[2]=s,this[3]=r,this.check()}fromObject(e){return this[0]=e.x,this[1]=e.y,this[2]=e.z,this[3]=e.w,this.check()}fromMatrix3(e){return Tt(this,e),this.check()}fromAxisRotation(e,n){return Mt(this,e,n),this.check()}identity(){return os(this),this.check()}setAxisAngle(e,n){return this.fromAxisRotation(e,n)}get ELEMENTS(){return 4}get x(){return this[0]}set x(e){this[0]=g(e)}get y(){return this[1]}set y(e){this[1]=g(e)}get z(){return this[2]}set z(e){this[2]=g(e)}get w(){return this[3]}set w(e){this[3]=g(e)}len(){return hs(this)}lengthSquared(){return ps(this)}dot(e){return Bs(this,e)}rotationTo(e,n){return Cs(this,e,n),this.check()}add(e){return As(this,this,e),this.check()}calculateW(){return ls(this,this),this.check()}conjugate(){return us(this,this),this.check()}invert(){return fs(this,this),this.check()}lerp(e,n,s){return s===void 0?this.lerp(this,e,n):(ms(this,e,n,s),this.check())}multiplyRight(e){return Qe(this,this,e),this.check()}multiplyLeft(e){return Qe(this,e,this),this.check()}normalize(){const e=this.len(),n=e>0?1/e:0;return this[0]=this[0]*n,this[1]=this[1]*n,this[2]=this[2]*n,this[3]=this[3]*n,e===0&&(this[3]=1),this.check()}rotateX(e){return is(this,this,e),this.check()}rotateY(e){return as(this,this,e),this.check()}rotateZ(e){return cs(this,this,e),this.check()}scale(e){return ds(this,this,e),this.check()}slerp(e,n,s){let r,o,i;switch(arguments.length){case 1:({start:r=bs,target:o,ratio:i}=e);break;case 2:r=this,o=e,i=n;break;default:r=e,o=n,i=s}return te(this,r,o,i),this.check()}transformVector4(e,n=new xe){return Mn(n,e,this),Ct(n,4)}lengthSq(){return this.lengthSquared()}setFromAxisAngle(e,n){return this.setAxisAngle(e,n)}premultiply(e){return this.multiplyLeft(e)}multiply(e){return this.multiplyRight(e)}}const Es=`out vec3 pbr_vPosition;
out vec2 pbr_vUV;

#ifdef HAS_NORMALS
# ifdef HAS_TANGENTS
out mat3 pbr_vTBN;
# else
out vec3 pbr_vNormal;
# endif
#endif

void pbr_setPositionNormalTangentUV(vec4 position, vec4 normal, vec4 tangent, vec2 uv)
{
  vec4 pos = pbrProjection.modelMatrix * position;
  pbr_vPosition = vec3(pos.xyz) / pos.w;

#ifdef HAS_NORMALS
#ifdef HAS_TANGENTS
  vec3 normalW = normalize(vec3(pbrProjection.normalMatrix * vec4(normal.xyz, 0.0)));
  vec3 tangentW = normalize(vec3(pbrProjection.modelMatrix * vec4(tangent.xyz, 0.0)));
  vec3 bitangentW = cross(normalW, tangentW) * tangent.w;
  pbr_vTBN = mat3(tangentW, bitangentW, normalW);
#else // HAS_TANGENTS != 1
  pbr_vNormal = normalize(vec3(pbrProjection.modelMatrix * vec4(normal.xyz, 0.0)));
#endif
#endif

#ifdef HAS_UV
  pbr_vUV = uv;
#else
  pbr_vUV = vec2(0.,0.);
#endif
}
`,Is=`precision highp float;

uniform pbrMaterialUniforms {
  // Material is unlit
  bool unlit;

  // Base color map
  bool baseColorMapEnabled;
  vec4 baseColorFactor;

  bool normalMapEnabled;  
  float normalScale; // #ifdef HAS_NORMALMAP

  bool emissiveMapEnabled;
  vec3 emissiveFactor; // #ifdef HAS_EMISSIVEMAP

  vec2 metallicRoughnessValues;
  bool metallicRoughnessMapEnabled;

  bool occlusionMapEnabled;
  float occlusionStrength; // #ifdef HAS_OCCLUSIONMAP
  
  bool alphaCutoffEnabled;
  float alphaCutoff; // #ifdef ALPHA_CUTOFF
  
  // IBL
  bool IBLenabled;
  vec2 scaleIBLAmbient; // #ifdef USE_IBL
  
  // debugging flags used for shader output of intermediate PBR variables
  // #ifdef PBR_DEBUG
  vec4 scaleDiffBaseMR;
  vec4 scaleFGDSpec;
  // #endif
} pbrMaterial;

// Samplers
#ifdef HAS_BASECOLORMAP
uniform sampler2D pbr_baseColorSampler;
#endif
#ifdef HAS_NORMALMAP
uniform sampler2D pbr_normalSampler;
#endif
#ifdef HAS_EMISSIVEMAP
uniform sampler2D pbr_emissiveSampler;
#endif
#ifdef HAS_METALROUGHNESSMAP
uniform sampler2D pbr_metallicRoughnessSampler;
#endif
#ifdef HAS_OCCLUSIONMAP
uniform sampler2D pbr_occlusionSampler;
#endif
#ifdef USE_IBL
uniform samplerCube pbr_diffuseEnvSampler;
uniform samplerCube pbr_specularEnvSampler;
uniform sampler2D pbr_brdfLUT;
#endif

// Inputs from vertex shader

in vec3 pbr_vPosition;
in vec2 pbr_vUV;

#ifdef HAS_NORMALS
#ifdef HAS_TANGENTS
in mat3 pbr_vTBN;
#else
in vec3 pbr_vNormal;
#endif
#endif

// Encapsulate the various inputs used by the various functions in the shading equation
// We store values in this struct to simplify the integration of alternative implementations
// of the shading terms, outlined in the Readme.MD Appendix.
struct PBRInfo {
  float NdotL;                  // cos angle between normal and light direction
  float NdotV;                  // cos angle between normal and view direction
  float NdotH;                  // cos angle between normal and half vector
  float LdotH;                  // cos angle between light direction and half vector
  float VdotH;                  // cos angle between view direction and half vector
  float perceptualRoughness;    // roughness value, as authored by the model creator (input to shader)
  float metalness;              // metallic value at the surface
  vec3 reflectance0;            // full reflectance color (normal incidence angle)
  vec3 reflectance90;           // reflectance color at grazing angle
  float alphaRoughness;         // roughness mapped to a more linear change in the roughness (proposed by [2])
  vec3 diffuseColor;            // color contribution from diffuse lighting
  vec3 specularColor;           // color contribution from specular lighting
  vec3 n;                       // normal at surface point
  vec3 v;                       // vector from surface point to camera
};

const float M_PI = 3.141592653589793;
const float c_MinRoughness = 0.04;

vec4 SRGBtoLINEAR(vec4 srgbIn)
{
#ifdef MANUAL_SRGB
#ifdef SRGB_FAST_APPROXIMATION
  vec3 linOut = pow(srgbIn.xyz,vec3(2.2));
#else // SRGB_FAST_APPROXIMATION
  vec3 bLess = step(vec3(0.04045),srgbIn.xyz);
  vec3 linOut = mix( srgbIn.xyz/vec3(12.92), pow((srgbIn.xyz+vec3(0.055))/vec3(1.055),vec3(2.4)), bLess );
#endif //SRGB_FAST_APPROXIMATION
  return vec4(linOut,srgbIn.w);;
#else //MANUAL_SRGB
  return srgbIn;
#endif //MANUAL_SRGB
}

// Find the normal for this fragment, pulling either from a predefined normal map
// or from the interpolated mesh normal and tangent attributes.
vec3 getNormal()
{
  // Retrieve the tangent space matrix
#ifndef HAS_TANGENTS
  vec3 pos_dx = dFdx(pbr_vPosition);
  vec3 pos_dy = dFdy(pbr_vPosition);
  vec3 tex_dx = dFdx(vec3(pbr_vUV, 0.0));
  vec3 tex_dy = dFdy(vec3(pbr_vUV, 0.0));
  vec3 t = (tex_dy.t * pos_dx - tex_dx.t * pos_dy) / (tex_dx.s * tex_dy.t - tex_dy.s * tex_dx.t);

#ifdef HAS_NORMALS
  vec3 ng = normalize(pbr_vNormal);
#else
  vec3 ng = cross(pos_dx, pos_dy);
#endif

  t = normalize(t - ng * dot(ng, t));
  vec3 b = normalize(cross(ng, t));
  mat3 tbn = mat3(t, b, ng);
#else // HAS_TANGENTS
  mat3 tbn = pbr_vTBN;
#endif

#ifdef HAS_NORMALMAP
  vec3 n = texture(pbr_normalSampler, pbr_vUV).rgb;
  n = normalize(tbn * ((2.0 * n - 1.0) * vec3(pbrMaterial.normalScale, pbrMaterial.normalScale, 1.0)));
#else
  // The tbn matrix is linearly interpolated, so we need to re-normalize
  vec3 n = normalize(tbn[2].xyz);
#endif

  return n;
}

// Calculation of the lighting contribution from an optional Image Based Light source.
// Precomputed Environment Maps are required uniform inputs and are computed as outlined in [1].
// See our README.md on Environment Maps [3] for additional discussion.
#ifdef USE_IBL
vec3 getIBLContribution(PBRInfo pbrInfo, vec3 n, vec3 reflection)
{
  float mipCount = 9.0; // resolution of 512x512
  float lod = (pbrInfo.perceptualRoughness * mipCount);
  // retrieve a scale and bias to F0. See [1], Figure 3
  vec3 brdf = SRGBtoLINEAR(texture(pbr_brdfLUT,
    vec2(pbrInfo.NdotV, 1.0 - pbrInfo.perceptualRoughness))).rgb;
  vec3 diffuseLight = SRGBtoLINEAR(texture(pbr_diffuseEnvSampler, n)).rgb;

#ifdef USE_TEX_LOD
  vec3 specularLight = SRGBtoLINEAR(texture(pbr_specularEnvSampler, reflection, lod)).rgb;
#else
  vec3 specularLight = SRGBtoLINEAR(texture(pbr_specularEnvSampler, reflection)).rgb;
#endif

  vec3 diffuse = diffuseLight * pbrInfo.diffuseColor;
  vec3 specular = specularLight * (pbrInfo.specularColor * brdf.x + brdf.y);

  // For presentation, this allows us to disable IBL terms
  diffuse *= pbrMaterial.scaleIBLAmbient.x;
  specular *= pbrMaterial.scaleIBLAmbient.y;

  return diffuse + specular;
}
#endif

// Basic Lambertian diffuse
// Implementation from Lambert's Photometria https://archive.org/details/lambertsphotome00lambgoog
// See also [1], Equation 1
vec3 diffuse(PBRInfo pbrInfo)
{
  return pbrInfo.diffuseColor / M_PI;
}

// The following equation models the Fresnel reflectance term of the spec equation (aka F())
// Implementation of fresnel from [4], Equation 15
vec3 specularReflection(PBRInfo pbrInfo)
{
  return pbrInfo.reflectance0 +
    (pbrInfo.reflectance90 - pbrInfo.reflectance0) *
    pow(clamp(1.0 - pbrInfo.VdotH, 0.0, 1.0), 5.0);
}

// This calculates the specular geometric attenuation (aka G()),
// where rougher material will reflect less light back to the viewer.
// This implementation is based on [1] Equation 4, and we adopt their modifications to
// alphaRoughness as input as originally proposed in [2].
float geometricOcclusion(PBRInfo pbrInfo)
{
  float NdotL = pbrInfo.NdotL;
  float NdotV = pbrInfo.NdotV;
  float r = pbrInfo.alphaRoughness;

  float attenuationL = 2.0 * NdotL / (NdotL + sqrt(r * r + (1.0 - r * r) * (NdotL * NdotL)));
  float attenuationV = 2.0 * NdotV / (NdotV + sqrt(r * r + (1.0 - r * r) * (NdotV * NdotV)));
  return attenuationL * attenuationV;
}

// The following equation(s) model the distribution of microfacet normals across
// the area being drawn (aka D())
// Implementation from "Average Irregularity Representation of a Roughened Surface
// for Ray Reflection" by T. S. Trowbridge, and K. P. Reitz
// Follows the distribution function recommended in the SIGGRAPH 2013 course notes
// from EPIC Games [1], Equation 3.
float microfacetDistribution(PBRInfo pbrInfo)
{
  float roughnessSq = pbrInfo.alphaRoughness * pbrInfo.alphaRoughness;
  float f = (pbrInfo.NdotH * roughnessSq - pbrInfo.NdotH) * pbrInfo.NdotH + 1.0;
  return roughnessSq / (M_PI * f * f);
}

void PBRInfo_setAmbientLight(inout PBRInfo pbrInfo) {
  pbrInfo.NdotL = 1.0;
  pbrInfo.NdotH = 0.0;
  pbrInfo.LdotH = 0.0;
  pbrInfo.VdotH = 1.0;
}

void PBRInfo_setDirectionalLight(inout PBRInfo pbrInfo, vec3 lightDirection) {
  vec3 n = pbrInfo.n;
  vec3 v = pbrInfo.v;
  vec3 l = normalize(lightDirection);             // Vector from surface point to light
  vec3 h = normalize(l+v);                        // Half vector between both l and v

  pbrInfo.NdotL = clamp(dot(n, l), 0.001, 1.0);
  pbrInfo.NdotH = clamp(dot(n, h), 0.0, 1.0);
  pbrInfo.LdotH = clamp(dot(l, h), 0.0, 1.0);
  pbrInfo.VdotH = clamp(dot(v, h), 0.0, 1.0);
}

void PBRInfo_setPointLight(inout PBRInfo pbrInfo, PointLight pointLight) {
  vec3 light_direction = normalize(pointLight.position - pbr_vPosition);
  PBRInfo_setDirectionalLight(pbrInfo, light_direction);
}

vec3 calculateFinalColor(PBRInfo pbrInfo, vec3 lightColor) {
  // Calculate the shading terms for the microfacet specular shading model
  vec3 F = specularReflection(pbrInfo);
  float G = geometricOcclusion(pbrInfo);
  float D = microfacetDistribution(pbrInfo);

  // Calculation of analytical lighting contribution
  vec3 diffuseContrib = (1.0 - F) * diffuse(pbrInfo);
  vec3 specContrib = F * G * D / (4.0 * pbrInfo.NdotL * pbrInfo.NdotV);
  // Obtain final intensity as reflectance (BRDF) scaled by the energy of the light (cosine law)
  return pbrInfo.NdotL * lightColor * (diffuseContrib + specContrib);
}

vec4 pbr_filterColor(vec4 colorUnused)
{
  // The albedo may be defined from a base texture or a flat color
#ifdef HAS_BASECOLORMAP
  vec4 baseColor = SRGBtoLINEAR(texture(pbr_baseColorSampler, pbr_vUV)) * pbrMaterial.baseColorFactor;
#else
  vec4 baseColor = pbrMaterial.baseColorFactor;
#endif

#ifdef ALPHA_CUTOFF
  if (baseColor.a < pbrMaterial.alphaCutoff) {
    discard;
  }
#endif

  vec3 color = vec3(0, 0, 0);

  if(pbrMaterial.unlit){
    color.rgb = baseColor.rgb;
  }
  else{
    // Metallic and Roughness material properties are packed together
    // In glTF, these factors can be specified by fixed scalar values
    // or from a metallic-roughness map
    float perceptualRoughness = pbrMaterial.metallicRoughnessValues.y;
    float metallic = pbrMaterial.metallicRoughnessValues.x;
#ifdef HAS_METALROUGHNESSMAP
    // Roughness is stored in the 'g' channel, metallic is stored in the 'b' channel.
    // This layout intentionally reserves the 'r' channel for (optional) occlusion map data
    vec4 mrSample = texture(pbr_metallicRoughnessSampler, pbr_vUV);
    perceptualRoughness = mrSample.g * perceptualRoughness;
    metallic = mrSample.b * metallic;
#endif
    perceptualRoughness = clamp(perceptualRoughness, c_MinRoughness, 1.0);
    metallic = clamp(metallic, 0.0, 1.0);
    // Roughness is authored as perceptual roughness; as is convention,
    // convert to material roughness by squaring the perceptual roughness [2].
    float alphaRoughness = perceptualRoughness * perceptualRoughness;

    vec3 f0 = vec3(0.04);
    vec3 diffuseColor = baseColor.rgb * (vec3(1.0) - f0);
    diffuseColor *= 1.0 - metallic;
    vec3 specularColor = mix(f0, baseColor.rgb, metallic);

    // Compute reflectance.
    float reflectance = max(max(specularColor.r, specularColor.g), specularColor.b);

    // For typical incident reflectance range (between 4% to 100%) set the grazing
    // reflectance to 100% for typical fresnel effect.
    // For very low reflectance range on highly diffuse objects (below 4%),
    // incrementally reduce grazing reflecance to 0%.
    float reflectance90 = clamp(reflectance * 25.0, 0.0, 1.0);
    vec3 specularEnvironmentR0 = specularColor.rgb;
    vec3 specularEnvironmentR90 = vec3(1.0, 1.0, 1.0) * reflectance90;

    vec3 n = getNormal();                          // normal at surface point
    vec3 v = normalize(pbrProjection.camera - pbr_vPosition);  // Vector from surface point to camera

    float NdotV = clamp(abs(dot(n, v)), 0.001, 1.0);
    vec3 reflection = -normalize(reflect(v, n));

    PBRInfo pbrInfo = PBRInfo(
      0.0, // NdotL
      NdotV,
      0.0, // NdotH
      0.0, // LdotH
      0.0, // VdotH
      perceptualRoughness,
      metallic,
      specularEnvironmentR0,
      specularEnvironmentR90,
      alphaRoughness,
      diffuseColor,
      specularColor,
      n,
      v
    );


#ifdef USE_LIGHTS
    // Apply ambient light
    PBRInfo_setAmbientLight(pbrInfo);
    color += calculateFinalColor(pbrInfo, lighting.ambientColor);

    // Apply directional light
    for(int i = 0; i < lighting.directionalLightCount; i++) {
      if (i < lighting.directionalLightCount) {
        PBRInfo_setDirectionalLight(pbrInfo, lighting_getDirectionalLight(i).direction);
        color += calculateFinalColor(pbrInfo, lighting_getDirectionalLight(i).color);
      }
    }

    // Apply point light
    for(int i = 0; i < lighting.pointLightCount; i++) {
      if (i < lighting.pointLightCount) {
        PBRInfo_setPointLight(pbrInfo, lighting_getPointLight(i));
        float attenuation = getPointLightAttenuation(lighting_getPointLight(i), distance(lighting_getPointLight(i).position, pbr_vPosition));
        color += calculateFinalColor(pbrInfo, lighting_getPointLight(i).color / attenuation);
      }
    }
#endif

    // Calculate lighting contribution from image based lighting source (IBL)
#ifdef USE_IBL
    if (pbrMaterial.IBLenabled) {
      color += getIBLContribution(pbrInfo, n, reflection);
    }
#endif

 // Apply optional PBR terms for additional (optional) shading
#ifdef HAS_OCCLUSIONMAP
    if (pbrMaterial.occlusionMapEnabled) {
      float ao = texture(pbr_occlusionSampler, pbr_vUV).r;
      color = mix(color, color * ao, pbrMaterial.occlusionStrength);
    }
#endif

#ifdef HAS_EMISSIVEMAP
    if (pbrMaterial.emissiveMapEnabled) {
      vec3 emissive = SRGBtoLINEAR(texture(pbr_emissiveSampler, pbr_vUV)).rgb * pbrMaterial.emissiveFactor;
      color += emissive;
    }
#endif

    // This section uses mix to override final color for reference app visualization
    // of various parameters in the lighting equation.
#ifdef PBR_DEBUG
    // TODO: Figure out how to debug multiple lights

    // color = mix(color, F, pbr_scaleFGDSpec.x);
    // color = mix(color, vec3(G), pbr_scaleFGDSpec.y);
    // color = mix(color, vec3(D), pbr_scaleFGDSpec.z);
    // color = mix(color, specContrib, pbr_scaleFGDSpec.w);

    // color = mix(color, diffuseContrib, pbr_scaleDiffBaseMR.x);
    color = mix(color, baseColor.rgb, pbrMaterial.scaleDiffBaseMR.y);
    color = mix(color, vec3(metallic), pbrMaterial.scaleDiffBaseMR.z);
    color = mix(color, vec3(perceptualRoughness), pbrMaterial.scaleDiffBaseMR.w);
#endif

  }

  return vec4(pow(color,vec3(1.0/2.2)), baseColor.a);
}
`,Ms=`struct PBRFragmentInputs {
  pbr_vPosition: vec3f,
  pbr_vUV: vec2f,
  pbr_vTBN: mat3f,
  pbr_vNormal: vec3f
};

var fragmentInputs: PBRFragmentInputs;

fn pbr_setPositionNormalTangentUV(position: vec4f, normal: vec4f, tangent: vec4f, uv: vec2f)
{
  var pos: vec4f = pbrProjection.modelMatrix * position;
  pbr_vPosition = vec3(pos.xyz) / pos.w;

#ifdef HAS_NORMALS
#ifdef HAS_TANGENTS
  let normalW: vec3f = normalize(vec3(pbrProjection.normalMatrix * vec4(normal.xyz, 0.0)));
  let tangentW: vec3f = normalize(vec3(pbrProjection.modelMatrix * vec4(tangent.xyz, 0.0)));
  let bitangentW: vec3f = cross(normalW, tangentW) * tangent.w;
  fragmentInputs,pbr_vTBN = mat3(tangentW, bitangentW, normalW);
#else // HAS_TANGENTS != 1
  fragmentInputs.pbr_vNormal = normalize(vec3(pbrProjection.modelMatrix * vec4(normal.xyz, 0.0)));
#endif
#endif

#ifdef HAS_UV
  pbr_vUV = uv;
#else
  pbr_vUV = vec2(0.,0.);
#endif
}

struct pbrMaterialUniforms {
  // Material is unlit
  unlit: uint32,

  // Base color map
  baseColorMapEnabled: uint32,
  baseColorFactor: vec4f,

  normalMapEnabled : uint32,
  normalScale: f32,  // #ifdef HAS_NORMALMAP

  emissiveMapEnabled: uint32,
  emissiveFactor: vec3f, // #ifdef HAS_EMISSIVEMAP

  metallicRoughnessValues: vec2f,
  metallicRoughnessMapEnabled: uint32,

  occlusionMapEnabled: i32,
  occlusionStrength: f32, // #ifdef HAS_OCCLUSIONMAP
  
  alphaCutoffEnabled: i32,
  alphaCutoff: f32, // #ifdef ALPHA_CUTOFF
  
  // IBL
  IBLenabled: i32,
  scaleIBLAmbient: vec2f, // #ifdef USE_IBL
  
  // debugging flags used for shader output of intermediate PBR variables
  // #ifdef PBR_DEBUG
  scaleDiffBaseMR: vec4f,
  scaleFGDSpec: vec4f
  // #endif
} 
  
@binding(2) @group(0) var<uniform> material : pbrMaterialUniforms;

// Samplers
#ifdef HAS_BASECOLORMAP
uniform sampler2D pbr_baseColorSampler;
#endif
#ifdef HAS_NORMALMAP
uniform sampler2D pbr_normalSampler;
#endif
#ifdef HAS_EMISSIVEMAP
uniform sampler2D pbr_emissiveSampler;
#endif
#ifdef HAS_METALROUGHNESSMAP
uniform sampler2D pbr_metallicRoughnessSampler;
#endif
#ifdef HAS_OCCLUSIONMAP
uniform sampler2D pbr_occlusionSampler;
#endif
#ifdef USE_IBL
uniform samplerCube pbr_diffuseEnvSampler;
uniform samplerCube pbr_specularEnvSampler;
uniform sampler2D pbr_brdfLUT;
#endif

// Encapsulate the various inputs used by the various functions in the shading equation
// We store values in this struct to simplify the integration of alternative implementations
// of the shading terms, outlined in the Readme.MD Appendix.
struct PBRInfo {
  NdotL: f32,                  // cos angle between normal and light direction
  NdotV: f32,                  // cos angle between normal and view direction
  NdotH: f32,                  // cos angle between normal and half vector
  LdotH: f32,                  // cos angle between light direction and half vector
  VdotH: f32,                  // cos angle between view direction and half vector
  perceptualRoughness: f32,    // roughness value, as authored by the model creator (input to shader)
  metalness: f32,              // metallic value at the surface
  reflectance0: vec3f,            // full reflectance color (normal incidence angle)
  reflectance90: vec3f,           // reflectance color at grazing angle
  alphaRoughness: f32,         // roughness mapped to a more linear change in the roughness (proposed by [2])
  diffuseColor: vec3f,            // color contribution from diffuse lighting
  specularColor: vec3f,           // color contribution from specular lighting
  n: vec3f,                       // normal at surface point
  v: vec3f,                       // vector from surface point to camera
};

const M_PI = 3.141592653589793;
const c_MinRoughness = 0.04;

fn SRGBtoLINEAR(srgbIn: vec4f ) -> vec4f
{
#ifdef MANUAL_SRGB
#ifdef SRGB_FAST_APPROXIMATION
  var linOut: vec3f = pow(srgbIn.xyz,vec3(2.2));
#else // SRGB_FAST_APPROXIMATION
  var bLess: vec3f = step(vec3(0.04045),srgbIn.xyz);
  var linOut: vec3f = mix( srgbIn.xyz/vec3(12.92), pow((srgbIn.xyz+vec3(0.055))/vec3(1.055),vec3(2.4)), bLess );
#endif //SRGB_FAST_APPROXIMATION
  return vec4f(linOut,srgbIn.w);;
#else //MANUAL_SRGB
  return srgbIn;
#endif //MANUAL_SRGB
}

// Find the normal for this fragment, pulling either from a predefined normal map
// or from the interpolated mesh normal and tangent attributes.
fn getNormal() -> vec3f
{
  // Retrieve the tangent space matrix
#ifndef HAS_TANGENTS
  var pos_dx: vec3f = dFdx(pbr_vPosition);
  var pos_dy: vec3f = dFdy(pbr_vPosition);
  var tex_dx: vec3f = dFdx(vec3(pbr_vUV, 0.0));
  var tex_dy: vec3f = dFdy(vec3(pbr_vUV, 0.0));
  var t: vec3f = (tex_dy.t * pos_dx - tex_dx.t * pos_dy) / (tex_dx.s * tex_dy.t - tex_dy.s * tex_dx.t);

#ifdef HAS_NORMALS
  var ng: vec3f = normalize(pbr_vNormal);
#else
  var ng: vec3f = cross(pos_dx, pos_dy);
#endif

  t = normalize(t - ng * dot(ng, t));
  var b: vec3f = normalize(cross(ng, t));
  var tbn: mat3f = mat3f(t, b, ng);
#else // HAS_TANGENTS
  var tbn: mat3f = pbr_vTBN;
#endif

#ifdef HAS_NORMALMAP
  vec3 n = texture(pbr_normalSampler, pbr_vUV).rgb;
  n = normalize(tbn * ((2.0 * n - 1.0) * vec3(pbrMaterial.normalScale, pbrMaterial.normalScale, 1.0)));
#else
  // The tbn matrix is linearly interpolated, so we need to re-normalize
  vec3 n = normalize(tbn[2].xyz);
#endif

  return n;
}

// Calculation of the lighting contribution from an optional Image Based Light source.
// Precomputed Environment Maps are required uniform inputs and are computed as outlined in [1].
// See our README.md on Environment Maps [3] for additional discussion.
#ifdef USE_IBL
fn getIBLContribution(PBRInfo pbrInfo, vec3 n, vec3 reflection) -> vec3f
{
  float mipCount = 9.0; // resolution of 512x512
  float lod = (pbrInfo.perceptualRoughness * mipCount);
  // retrieve a scale and bias to F0. See [1], Figure 3
  vec3 brdf = SRGBtoLINEAR(texture(pbr_brdfLUT,
    vec2(pbrInfo.NdotV, 1.0 - pbrInfo.perceptualRoughness))).rgb;
  vec3 diffuseLight = SRGBtoLINEAR(texture(pbr_diffuseEnvSampler, n)).rgb;

#ifdef USE_TEX_LOD
  vec3 specularLight = SRGBtoLINEAR(texture(pbr_specularEnvSampler, reflection, lod)).rgb;
#else
  vec3 specularLight = SRGBtoLINEAR(texture(pbr_specularEnvSampler, reflection)).rgb;
#endif

  vec3 diffuse = diffuseLight * pbrInfo.diffuseColor;
  vec3 specular = specularLight * (pbrInfo.specularColor * brdf.x + brdf.y);

  // For presentation, this allows us to disable IBL terms
  diffuse *= pbrMaterial.scaleIBLAmbient.x;
  specular *= pbrMaterial.scaleIBLAmbient.y;

  return diffuse + specular;
}
#endif

// Basic Lambertian diffuse
// Implementation from Lambert's Photometria https://archive.org/details/lambertsphotome00lambgoog
// See also [1], Equation 1
fn diffuse(pbrInfo: PBRInfo) -> vec3<f32> {
  return pbrInfo.diffuseColor / PI;
}

// The following equation models the Fresnel reflectance term of the spec equation (aka F())
// Implementation of fresnel from [4], Equation 15
fn specularReflection(pbrInfo: PBRInfo) -> vec3<f32> {
  return pbrInfo.reflectance0 +
    (pbrInfo.reflectance90 - pbrInfo.reflectance0) *
    pow(clamp(1.0 - pbrInfo.VdotH, 0.0, 1.0), 5.0);
}

// This calculates the specular geometric attenuation (aka G()),
// where rougher material will reflect less light back to the viewer.
// This implementation is based on [1] Equation 4, and we adopt their modifications to
// alphaRoughness as input as originally proposed in [2].
fn geometricOcclusion(pbrInfo: PBRInfo) -> f32 {
  let NdotL: f32 = pbrInfo.NdotL;
  let NdotV: f32 = pbrInfo.NdotV;
  let r: f32 = pbrInfo.alphaRoughness;

  let attenuationL = 2.0 * NdotL / (NdotL + sqrt(r * r + (1.0 - r * r) * (NdotL * NdotL)));
  let attenuationV = 2.0 * NdotV / (NdotV + sqrt(r * r + (1.0 - r * r) * (NdotV * NdotV)));
  return attenuationL * attenuationV;
}

// The following equation(s) model the distribution of microfacet normals across
// the area being drawn (aka D())
// Implementation from "Average Irregularity Representation of a Roughened Surface
// for Ray Reflection" by T. S. Trowbridge, and K. P. Reitz
// Follows the distribution function recommended in the SIGGRAPH 2013 course notes
// from EPIC Games [1], Equation 3.
fn microfacetDistribution(pbrInfo: PBRInfo) -> f32 {
  let roughnessSq = pbrInfo.alphaRoughness * pbrInfo.alphaRoughness;
  let f = (pbrInfo.NdotH * roughnessSq - pbrInfo.NdotH) * pbrInfo.NdotH + 1.0;
  return roughnessSq / (PI * f * f);
}

fn PBRInfo_setAmbientLight(pbrInfo: ptr<function, PBRInfo>) {
  (*pbrInfo).NdotL = 1.0;
  (*pbrInfo).NdotH = 0.0;
  (*pbrInfo).LdotH = 0.0;
  (*pbrInfo).VdotH = 1.0;
}

fn PBRInfo_setDirectionalLight(pbrInfo: ptr<function, PBRInfo>, lightDirection: vec3<f32>) {
  let n = (*pbrInfo).n;
  let v = (*pbrInfo).v;
  let l = normalize(lightDirection);             // Vector from surface point to light
  let h = normalize(l + v);                      // Half vector between both l and v

  (*pbrInfo).NdotL = clamp(dot(n, l), 0.001, 1.0);
  (*pbrInfo).NdotH = clamp(dot(n, h), 0.0, 1.0);
  (*pbrInfo).LdotH = clamp(dot(l, h), 0.0, 1.0);
  (*pbrInfo).VdotH = clamp(dot(v, h), 0.0, 1.0);
}

fn PBRInfo_setPointLight(pbrInfo: ptr<function, PBRInfo>, pointLight: PointLight) {
  let light_direction = normalize(pointLight.position - pbr_vPosition);
  PBRInfo_setDirectionalLight(pbrInfo, light_direction);
}

fn calculateFinalColor(pbrInfo: PBRInfo, lightColor: vec3<f32>) -> vec3<f32> {
  // Calculate the shading terms for the microfacet specular shading model
  let F = specularReflection(pbrInfo);
  let G = geometricOcclusion(pbrInfo);
  let D = microfacetDistribution(pbrInfo);

  // Calculation of analytical lighting contribution
  let diffuseContrib = (1.0 - F) * diffuse(pbrInfo);
  let specContrib = F * G * D / (4.0 * pbrInfo.NdotL * pbrInfo.NdotV);
  // Obtain final intensity as reflectance (BRDF) scaled by the energy of the light (cosine law)
  return pbrInfo.NdotL * lightColor * (diffuseContrib + specContrib);
}

fn pbr_filterColor(colorUnused: vec4<f32>) -> vec4<f32> {
  // The albedo may be defined from a base texture or a flat color
  var baseColor: vec4<f32>;
  #ifdef HAS_BASECOLORMAP
  baseColor = SRGBtoLINEAR(textureSample(pbr_baseColorSampler, pbr_baseColorSampler, pbr_vUV)) * pbrMaterial.baseColorFactor;
  #else
  baseColor = pbrMaterial.baseColorFactor;
  #endif

  #ifdef ALPHA_CUTOFF
  if (baseColor.a < pbrMaterial.alphaCutoff) {
    discard;
  }
  #endif

  var color = vec3<f32>(0.0, 0.0, 0.0);

  if (pbrMaterial.unlit) {
    color = baseColor.rgb;
  } else {
    // Metallic and Roughness material properties are packed together
    // In glTF, these factors can be specified by fixed scalar values
    // or from a metallic-roughness map
    var perceptualRoughness = pbrMaterial.metallicRoughnessValues.y;
    var metallic = pbrMaterial.metallicRoughnessValues.x;
    #ifdef HAS_METALROUGHNESSMAP
    // Roughness is stored in the 'g' channel, metallic is stored in the 'b' channel.
    // This layout intentionally reserves the 'r' channel for (optional) occlusion map data
    let mrSample = textureSample(pbr_metallicRoughnessSampler, pbr_metallicRoughnessSampler, pbr_vUV);
    perceptualRoughness = mrSample.g * perceptualRoughness;
    metallic = mrSample.b * metallic;
    #endif
    perceptualRoughness = clamp(perceptualRoughness, c_MinRoughness, 1.0);
    metallic = clamp(metallic, 0.0, 1.0);
    // Roughness is authored as perceptual roughness; as is convention,
    // convert to material roughness by squaring the perceptual roughness [2].
    let alphaRoughness = perceptualRoughness * perceptualRoughness;

    let f0 = vec3<f32>(0.04);
    var diffuseColor = baseColor.rgb * (vec3<f32>(1.0) - f0);
    diffuseColor *= 1.0 - metallic;
    let specularColor = mix(f0, baseColor.rgb, metallic);

    // Compute reflectance.
    let reflectance = max(max(specularColor.r, specularColor.g), specularColor.b);

    // For typical incident reflectance range (between 4% to 100%) set the grazing
    // reflectance to 100% for typical fresnel effect.
    // For very low reflectance range on highly diffuse objects (below 4%),
    // incrementally reduce grazing reflectance to 0%.
    let reflectance90 = clamp(reflectance * 25.0, 0.0, 1.0);
    let specularEnvironmentR0 = specularColor;
    let specularEnvironmentR90 = vec3<f32>(1.0, 1.0, 1.0) * reflectance90;

    let n = getNormal();                          // normal at surface point
    let v = normalize(pbrProjection.camera - pbr_vPosition);  // Vector from surface point to camera

    let NdotV = clamp(abs(dot(n, v)), 0.001, 1.0);
    let reflection = -normalize(reflect(v, n));

    var pbrInfo = PBRInfo(
      0.0, // NdotL
      NdotV,
      0.0, // NdotH
      0.0, // LdotH
      0.0, // VdotH
      perceptualRoughness,
      metallic,
      specularEnvironmentR0,
      specularEnvironmentR90,
      alphaRoughness,
      diffuseColor,
      specularColor,
      n,
      v
    );

    #ifdef USE_LIGHTS
    // Apply ambient light
    PBRInfo_setAmbientLight(&pbrInfo);
    color += calculateFinalColor(pbrInfo, lighting.ambientColor);

    // Apply directional light
    for (var i = 0; i < lighting.directionalLightCount; i++) {
      if (i < lighting.directionalLightCount) {
        PBRInfo_setDirectionalLight(&pbrInfo, lighting_getDirectionalLight(i).direction);
        color += calculateFinalColor(pbrInfo, lighting_getDirectionalLight(i).color);
      }
    }

    // Apply point light
    for (var i = 0; i < lighting.pointLightCount; i++) {
      if (i < lighting.pointLightCount) {
        PBRInfo_setPointLight(&pbrInfo, lighting_getPointLight(i));
        let attenuation = getPointLightAttenuation(lighting_getPointLight(i), distance(lighting_getPointLight(i).position, pbr_vPosition));
        color += calculateFinalColor(pbrInfo, lighting_getPointLight(i).color / attenuation);
      }
    }
    #endif

    // Calculate lighting contribution from image based lighting source (IBL)
    #ifdef USE_IBL
    if (pbrMaterial.IBLenabled) {
      color += getIBLContribution(pbrInfo, n, reflection);
    }
    #endif

    // Apply optional PBR terms for additional (optional) shading
    #ifdef HAS_OCCLUSIONMAP
    if (pbrMaterial.occlusionMapEnabled) {
      let ao = textureSample(pbr_occlusionSampler, pbr_occlusionSampler, pbr_vUV).r;
      color = mix(color, color * ao, pbrMaterial.occlusionStrength);
    }
    #endif

    #ifdef HAS_EMISSIVEMAP
    if (pbrMaterial.emissiveMapEnabled) {
      let emissive = SRGBtoLINEAR(textureSample(pbr_emissiveSampler, pbr_emissiveSampler, pbr_vUV)).rgb * pbrMaterial.emissiveFactor;
      color += emissive;
    }
    #endif

    // This section uses mix to override final color for reference app visualization
    // of various parameters in the lighting equation.
    #ifdef PBR_DEBUG
    // TODO: Figure out how to debug multiple lights

    // color = mix(color, F, pbr_scaleFGDSpec.x);
    // color = mix(color, vec3(G), pbr_scaleFGDSpec.y);
    // color = mix(color, vec3(D), pbr_scaleFGDSpec.z);
    // color = mix(color, specContrib, pbr_scaleFGDSpec.w);

    // color = mix(color, diffuseContrib, pbr_scaleDiffBaseMR.x);
    color = mix(color, baseColor.rgb, pbrMaterial.scaleDiffBaseMR.y);
    color = mix(color, vec3<f32>(metallic), pbrMaterial.scaleDiffBaseMR.z);
    color = mix(color, vec3<f32>(perceptualRoughness), pbrMaterial.scaleDiffBaseMR.w);
    #endif
  }

  return vec4<f32>(pow(color, vec3<f32>(1.0 / 2.2)), baseColor.a);
}
`,Ye=`uniform pbrProjectionUniforms {
  mat4 modelViewProjectionMatrix;
  mat4 modelMatrix;
  mat4 normalMatrix;
  vec3 camera;
} pbrProjection;
`,Ts={name:"pbrProjection",vs:Ye,fs:Ye,getUniforms:t=>t,uniformTypes:{modelViewProjectionMatrix:"mat4x4<f32>",modelMatrix:"mat4x4<f32>",normalMatrix:"mat4x4<f32>",camera:"vec3<i32>"}},Ft={props:{},uniforms:{},name:"pbrMaterial",dependencies:[qt,Ts],source:Ms,vs:Es,fs:Is,defines:{LIGHTING_FRAGMENT:!0,HAS_NORMALMAP:!1,HAS_EMISSIVEMAP:!1,HAS_OCCLUSIONMAP:!1,HAS_BASECOLORMAP:!1,HAS_METALROUGHNESSMAP:!1,ALPHA_CUTOFF:!1,USE_IBL:!1,PBR_DEBUG:!1},getUniforms:t=>t,uniformTypes:{unlit:"i32",baseColorMapEnabled:"i32",baseColorFactor:"vec4<f32>",normalMapEnabled:"i32",normalScale:"f32",emissiveMapEnabled:"i32",emissiveFactor:"vec3<f32>",metallicRoughnessValues:"vec2<f32>",metallicRoughnessMapEnabled:"i32",occlusionMapEnabled:"i32",occlusionStrength:"f32",alphaCutoffEnabled:"i32",alphaCutoff:"f32",IBLenabled:"i32",scaleIBLAmbient:"vec2<f32>",scaleDiffBaseMR:"vec4<f32>",scaleFGDSpec:"vec4<f32>"}};class re{id;matrix=new x;display=!0;position=new G;rotation=new G;scale=new G(1,1,1);userData={};props={};constructor(e={}){const{id:n}=e;this.id=n||yn(this.constructor.name),this._setScenegraphNodeProps(e)}getBounds(){return null}destroy(){}delete(){this.destroy()}setProps(e){return this._setScenegraphNodeProps(e),this}toString(){return`{type: ScenegraphNode, id: ${this.id})}`}setPosition(e){return this.position=e,this}setRotation(e){return this.rotation=e,this}setScale(e){return this.scale=e,this}setMatrix(e,n=!0){n?this.matrix.copy(e):this.matrix=e}setMatrixComponents(e){const{position:n,rotation:s,scale:r,update:o=!0}=e;return n&&this.setPosition(n),s&&this.setRotation(s),r&&this.setScale(r),o&&this.updateMatrix(),this}updateMatrix(){const e=this.position,n=this.rotation,s=this.scale;return this.matrix.identity(),this.matrix.translate(e),this.matrix.rotateXYZ(n),this.matrix.scale(s),this}update(e={}){const{position:n,rotation:s,scale:r}=e;return n&&this.setPosition(n),s&&this.setRotation(s),r&&this.setScale(r),this.updateMatrix(),this}getCoordinateUniforms(e,n){n=n||this.matrix;const s=new x(e).multiplyRight(n),r=s.invert(),o=r.transpose();return{viewMatrix:e,modelMatrix:n,objectMatrix:n,worldMatrix:s,worldInverseMatrix:r,worldInverseTransposeMatrix:o}}_setScenegraphNodeProps(e){"position"in e&&this.setPosition(e.position),"rotation"in e&&this.setRotation(e.rotation),"scale"in e&&this.setScale(e.scale),"matrix"in e&&this.setMatrix(e.matrix),Object.assign(this.props,e)}}class U extends re{children;constructor(e={}){e=Array.isArray(e)?{children:e}:e;const{children:n=[]}=e;L.assert(n.every(s=>s instanceof re),"every child must an instance of ScenegraphNode"),super(e),this.children=n}getBounds(){const e=[[1/0,1/0,1/0],[-1/0,-1/0,-1/0]];return this.traverse((n,{worldMatrix:s})=>{const r=n.getBounds();if(!r)return;const[o,i]=r,a=new G(o).add(i).divide([2,2,2]);s.transformAsPoint(a,a);const c=new G(i).subtract(o).divide([2,2,2]);s.transformAsVector(c,c);for(let l=0;l<8;l++){const f=new G(l&1?-1:1,l&2?-1:1,l&4?-1:1).multiply(c).add(a);for(let u=0;u<3;u++)e[0][u]=Math.min(e[0][u],f[u]),e[1][u]=Math.max(e[1][u],f[u])}}),Number.isFinite(e[0][0])?e:null}destroy(){this.children.forEach(e=>e.destroy()),this.removeAll(),super.destroy()}add(...e){for(const n of e)Array.isArray(n)?this.add(...n):this.children.push(n);return this}remove(e){const n=this.children,s=n.indexOf(e);return s>-1&&n.splice(s,1),this}removeAll(){return this.children=[],this}traverse(e,{worldMatrix:n=new x}={}){const s=new x(n).multiplyRight(this.matrix);for(const r of this.children)r instanceof U?r.traverse(e,{worldMatrix:s}):e(r,{worldMatrix:s})}}class Re extends re{model;bounds=null;managedResources;constructor(e){super(e),this.model=e.model,this.managedResources=e.managedResources||[],this.bounds=e.bounds||null,this.setProps(e)}destroy(){this.model&&(this.model.destroy(),this.model=null),this.managedResources.forEach(e=>e.destroy()),this.managedResources=[]}getBounds(){return this.bounds}draw(e){return this.model.draw(e)}}const he=Math.PI/180,W=new Float32Array(16),ke=new Float32Array(12);function ze(t,e,n){const s=e[0]*he,r=e[1]*he,o=e[2]*he,i=Math.sin(o),a=Math.sin(s),c=Math.sin(r),l=Math.cos(o),f=Math.cos(s),u=Math.cos(r),A=n[0],d=n[1],B=n[2];t[0]=A*u*f,t[1]=A*c*f,t[2]=A*-a,t[3]=d*(-c*l+u*a*i),t[4]=d*(u*l+c*a*i),t[5]=d*f*i,t[6]=B*(c*i+u*a*l),t[7]=B*(-u*i+c*a*l),t[8]=B*f*l}function We(t){return t[0]=t[0],t[1]=t[1],t[2]=t[2],t[3]=t[4],t[4]=t[5],t[5]=t[6],t[6]=t[8],t[7]=t[9],t[8]=t[10],t[9]=t[12],t[10]=t[13],t[11]=t[14],t.subarray(0,12)}const _t={size:12,accessor:["getOrientation","getScale","getTranslation","getTransformMatrix"],shaderAttributes:{instanceModelMatrixCol0:{size:3,elementOffset:0},instanceModelMatrixCol1:{size:3,elementOffset:3},instanceModelMatrixCol2:{size:3,elementOffset:6},instanceTranslation:{size:3,elementOffset:9}},update(t,{startRow:e,endRow:n}){const{data:s,getOrientation:r,getScale:o,getTranslation:i,getTransformMatrix:a}=this.props,c=Array.isArray(a),l=c&&a.length===16,f=Array.isArray(o),u=Array.isArray(r),A=Array.isArray(i),d=l||!c&&!!a(s[0]);d?t.constant=l:t.constant=u&&f&&A;const B=t.value;if(t.constant){let m;d?(W.set(a),m=We(W)):(m=ke,ze(m,r,o),m.set(i,9)),t.value=new Float32Array(m)}else{let m=e*t.size;const{iterable:p,objectInfo:C}=$t(s,e,n);for(const I of p){C.index++;let h;if(d)W.set(l?a:a(I,C)),h=We(W);else{h=ke;const N=u?r:r(I,C),Zt=f?o:o(I,C);ze(h,N,Zt),h.set(A?i:i(I,C),9)}B[m++]=h[0],B[m++]=h[1],B[m++]=h[2],B[m++]=h[3],B[m++]=h[4],B[m++]=h[5],B[m++]=h[6],B[m++]=h[7],B[m++]=h[8],B[m++]=h[9],B[m++]=h[10],B[m++]=h[11]}}}};function Rt(t,e){return e===de.CARTESIAN||e===de.METER_OFFSETS||e===de.DEFAULT&&!t.isGeospatial}const Ze=`uniform simpleMeshUniforms {
  float sizeScale;
  bool composeModelMatrix;
  bool hasTexture;
  bool flatShading;
} simpleMesh;
`,ys={name:"simpleMesh",vs:Ze,fs:Ze,uniformTypes:{sizeScale:"f32",composeModelMatrix:"f32",hasTexture:"f32",flatShading:"f32"}},Fs=`#version 300 es
#define SHADER_NAME simple-mesh-layer-vs
in vec3 positions;
in vec3 normals;
in vec3 colors;
in vec2 texCoords;
in vec3 instancePositions;
in vec3 instancePositions64Low;
in vec4 instanceColors;
in vec3 instancePickingColors;
in vec3 instanceModelMatrixCol0;
in vec3 instanceModelMatrixCol1;
in vec3 instanceModelMatrixCol2;
in vec3 instanceTranslation;
out vec2 vTexCoord;
out vec3 cameraPosition;
out vec3 normals_commonspace;
out vec4 position_commonspace;
out vec4 vColor;
void main(void) {
geometry.worldPosition = instancePositions;
geometry.uv = texCoords;
geometry.pickingColor = instancePickingColors;
vTexCoord = texCoords;
cameraPosition = project.cameraPosition;
vColor = vec4(colors * instanceColors.rgb, instanceColors.a);
mat3 instanceModelMatrix = mat3(instanceModelMatrixCol0, instanceModelMatrixCol1, instanceModelMatrixCol2);
vec3 pos = (instanceModelMatrix * positions) * simpleMesh.sizeScale + instanceTranslation;
if (simpleMesh.composeModelMatrix) {
DECKGL_FILTER_SIZE(pos, geometry);
normals_commonspace = project_normal(instanceModelMatrix * normals);
geometry.worldPosition += pos;
gl_Position = project_position_to_clipspace(pos + instancePositions, instancePositions64Low, vec3(0.0), position_commonspace);
geometry.position = position_commonspace;
}
else {
pos = project_size(pos);
DECKGL_FILTER_SIZE(pos, geometry);
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, pos, position_commonspace);
geometry.position = position_commonspace;
normals_commonspace = project_normal(instanceModelMatrix * normals);
}
geometry.normal = normals_commonspace;
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,_s=`#version 300 es
#define SHADER_NAME simple-mesh-layer-fs
precision highp float;
uniform sampler2D sampler;
in vec2 vTexCoord;
in vec3 cameraPosition;
in vec3 normals_commonspace;
in vec4 position_commonspace;
in vec4 vColor;
out vec4 fragColor;
void main(void) {
geometry.uv = vTexCoord;
vec3 normal;
if (simpleMesh.flatShading) {
normal = normalize(cross(dFdx(position_commonspace.xyz), dFdy(position_commonspace.xyz)));
} else {
normal = normals_commonspace;
}
vec4 color = simpleMesh.hasTexture ? texture(sampler, vTexCoord) : vColor;
DECKGL_FILTER_COLOR(color, geometry);
vec3 lightColor = lighting_getLightColor(color.rgb, cameraPosition, position_commonspace.xyz, normal);
fragColor = vec4(lightColor, color.a * layer.opacity);
}
`;function pe(t){const e=t.positions||t.POSITION;ee.assert(e,'no "postions" or "POSITION" attribute in mesh');const n=e.value.length/e.size;let s=t.COLOR_0||t.colors;s||(s={size:3,value:new Float32Array(n*3).fill(1)});let r=t.NORMAL||t.normals;r||(r={size:3,value:new Float32Array(n*3).fill(0)});let o=t.TEXCOORD_0||t.texCoords;return o||(o={size:2,value:new Float32Array(n*2).fill(0)}),{positions:e,colors:s,normals:r,texCoords:o}}function qe(t){return t instanceof $?(t.attributes=pe(t.attributes),t):t.attributes?new $({...t,topology:"triangle-list",attributes:pe(t.attributes)}):new $({topology:"triangle-list",attributes:pe(t)})}const Rs=[0,0,0,255],Gs={mesh:{type:"object",value:null,async:!0},texture:{type:"image",value:null,async:!0},sizeScale:{type:"number",value:1,min:0},_instanced:!0,wireframe:!1,material:!0,getPosition:{type:"accessor",value:t=>t.position},getColor:{type:"accessor",value:Rs},getOrientation:{type:"accessor",value:[0,0,0]},getScale:{type:"accessor",value:[1,1,1]},getTranslation:{type:"accessor",value:[0,0,0]},getTransformMatrix:{type:"accessor",value:[]},textureParameters:{type:"object",ignore:!0,value:null}};class Gt extends Bt{getShaders(){return super.getShaders({vs:Fs,fs:_s,modules:[mt,en,ht,ys]})}getBounds(){if(this.props._instanced)return super.getBounds();let e=this.state.positionBounds;if(e)return e;const{mesh:n}=this.props;if(!n)return null;if(e=n.header?.boundingBox,!e){const{attributes:s}=qe(n);s.POSITION=s.POSITION||s.positions,e=It(s)}return this.state.positionBounds=e,e}initializeState(){this.getAttributeManager().addInstanced({instancePositions:{transition:!0,type:"float64",fp64:this.use64bitPositions(),size:3,accessor:"getPosition"},instanceColors:{type:"unorm8",transition:!0,size:this.props.colorFormat.length,accessor:"getColor",defaultValue:[0,0,0,255]},instanceModelMatrix:_t}),this.setState({emptyTexture:this.context.device.createTexture({data:new Uint8Array(4),width:1,height:1})})}updateState(e){super.updateState(e);const{props:n,oldProps:s,changeFlags:r}=e;if(n.mesh!==s.mesh||r.extensionsChanged){if(this.state.positionBounds=null,this.state.model?.destroy(),n.mesh){this.state.model=this.getModel(n.mesh);const o=n.mesh.attributes||n.mesh;this.setState({hasNormals:!!(o.NORMAL||o.normals)})}this.getAttributeManager().invalidateAll()}n.texture!==s.texture&&n.texture instanceof Tn&&this.setTexture(n.texture),this.state.model&&this.state.model.setTopology(this.props.wireframe?"line-strip":"triangle-list")}finalizeState(e){super.finalizeState(e),this.state.emptyTexture.delete()}draw({uniforms:e}){const{model:n}=this.state;if(!n)return;const{viewport:s,renderPass:r}=this.context,{sizeScale:o,coordinateSystem:i,_instanced:a}=this.props,c={sizeScale:o,composeModelMatrix:!a||Rt(s,i),flatShading:!this.state.hasNormals};n.shaderInputs.setProps({simpleMesh:c}),n.draw(r)}get isLoaded(){return!!(this.state?.model&&super.isLoaded)}getModel(e){const n=new bt(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),geometry:qe(e),isInstanced:!0}),{texture:s}=this.props,{emptyTexture:r}=this.state,o={sampler:s||r,hasTexture:!!s};return n.shaderInputs.setProps({simpleMesh:o}),n}setTexture(e){const{emptyTexture:n,model:s}=this.state;if(s){const r={sampler:e||n,hasTexture:!!e};s.shaderInputs.setProps({simpleMesh:r})}}}Gt.defaultProps=Gs;Gt.layerName="SimpleMeshLayer";const vs="4.3.3",oe={TRANSCODER:"basis_transcoder.js",TRANSCODER_WASM:"basis_transcoder.wasm",ENCODER:"basis_encoder.js",ENCODER_WASM:"basis_encoder.wasm"};let $e;async function et(t){Sn(t.modules);const e=On("basis");return e||($e||=Ds(t),await $e)}async function Ds(t){let e=null,n=null;return[e,n]=await Promise.all([await v(oe.TRANSCODER,"textures",t),await v(oe.TRANSCODER_WASM,"textures",t)]),e=e||globalThis.BASIS,await Ss(e,n)}function Ss(t,e){const n={};return e&&(n.wasmBinary=e),new Promise(s=>{t(n).then(r=>{const{BasisFile:o,initializeBasis:i}=r;i(),s({BasisFile:o})})})}let Ce;async function tt(t){const e=t.modules||{};return e.basisEncoder?e.basisEncoder:(Ce=Ce||Os(t),await Ce)}async function Os(t){let e=null,n=null;return[e,n]=await Promise.all([await v(oe.ENCODER,"textures",t),await v(oe.ENCODER_WASM,"textures",t)]),e=e||globalThis.BASIS,await xs(e,n)}function xs(t,e){const n={};return e&&(n.wasmBinary=e),new Promise(s=>{t(n).then(r=>{const{BasisFile:o,KTX2File:i,initializeBasis:a,BasisEncoder:c}=r;a(),s({BasisFile:o,KTX2File:i,BasisEncoder:c})})})}const D={COMPRESSED_RGB_S3TC_DXT1_EXT:33776,COMPRESSED_RGBA_S3TC_DXT5_EXT:33779,COMPRESSED_RGB_PVRTC_4BPPV1_IMG:35840,COMPRESSED_RGBA_PVRTC_4BPPV1_IMG:35842,COMPRESSED_RGB_ETC1_WEBGL:36196,COMPRESSED_RGBA_ASTC_4X4_KHR:37808},Ls=["","WEBKIT_","MOZ_"],nt={WEBGL_compressed_texture_s3tc:"dxt",WEBGL_compressed_texture_s3tc_srgb:"dxt-srgb",WEBGL_compressed_texture_etc1:"etc1",WEBGL_compressed_texture_etc:"etc2",WEBGL_compressed_texture_pvrtc:"pvrtc",WEBGL_compressed_texture_atc:"atc",WEBGL_compressed_texture_astc:"astc",EXT_texture_compression_rgtc:"rgtc"};let Z=null;function Hs(t){if(!Z){t=t||Ps()||void 0,Z=new Set;for(const e of Ls)for(const n in nt)if(t&&t.getExtension(`${e}${n}`)){const s=nt[n];Z.add(s)}}return Z}function Ps(){try{return document.createElement("canvas").getContext("webgl")}catch{return null}}const M=[171,75,84,88,32,50,48,187,13,10,26,10];function Us(t){const e=new Uint8Array(t);return!(e.byteLength<M.length||e[0]!==M[0]||e[1]!==M[1]||e[2]!==M[2]||e[3]!==M[3]||e[4]!==M[4]||e[5]!==M[5]||e[6]!==M[6]||e[7]!==M[7]||e[8]!==M[8]||e[9]!==M[9]||e[10]!==M[10]||e[11]!==M[11])}const Ns={etc1:{basisFormat:0,compressed:!0,format:D.COMPRESSED_RGB_ETC1_WEBGL},etc2:{basisFormat:1,compressed:!0},bc1:{basisFormat:2,compressed:!0,format:D.COMPRESSED_RGB_S3TC_DXT1_EXT},bc3:{basisFormat:3,compressed:!0,format:D.COMPRESSED_RGBA_S3TC_DXT5_EXT},bc4:{basisFormat:4,compressed:!0},bc5:{basisFormat:5,compressed:!0},"bc7-m6-opaque-only":{basisFormat:6,compressed:!0},"bc7-m5":{basisFormat:7,compressed:!0},"pvrtc1-4-rgb":{basisFormat:8,compressed:!0,format:D.COMPRESSED_RGB_PVRTC_4BPPV1_IMG},"pvrtc1-4-rgba":{basisFormat:9,compressed:!0,format:D.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG},"astc-4x4":{basisFormat:10,compressed:!0,format:D.COMPRESSED_RGBA_ASTC_4X4_KHR},"atc-rgb":{basisFormat:11,compressed:!0},"atc-rgba-interpolated-alpha":{basisFormat:12,compressed:!0},rgba32:{basisFormat:13,compressed:!1},rgb565:{basisFormat:14,compressed:!1},bgr565:{basisFormat:15,compressed:!1},rgba4444:{basisFormat:16,compressed:!1}};async function Js(t,e){if(e.basis.containerFormat==="auto"){if(Us(t)){const s=await tt(e);return st(s.KTX2File,t,e)}const{BasisFile:n}=await et(e);return be(n,t,e)}if(e.basis.module==="encoder"){const n=await tt(e);return e.basis.containerFormat==="ktx2"?st(n.KTX2File,t,e):be(n.BasisFile,t,e)}else{const{BasisFile:s}=await et(e);return be(s,t,e)}}function be(t,e,n){const s=new t(new Uint8Array(e));try{if(!s.startTranscoding())throw new Error("Failed to start basis transcoding");const r=s.getNumImages(),o=[];for(let i=0;i<r;i++){const a=s.getNumLevels(i),c=[];for(let l=0;l<a;l++)c.push(ws(s,i,l,n));o.push(c)}return o}finally{s.close(),s.delete()}}function ws(t,e,n,s){const r=t.getImageWidth(e,n),o=t.getImageHeight(e,n),i=t.getHasAlpha(),{compressed:a,format:c,basisFormat:l}=vt(s,i),f=t.getImageTranscodedSizeInBytes(e,n,l),u=new Uint8Array(f);if(!t.transcodeImage(u,e,n,l,0,0))throw new Error("failed to start Basis transcoding");return{width:r,height:o,data:u,compressed:a,format:c,hasAlpha:i}}function st(t,e,n){const s=new t(new Uint8Array(e));try{if(!s.startTranscoding())throw new Error("failed to start KTX2 transcoding");const r=s.getLevels(),o=[];for(let i=0;i<r;i++)o.push(Ks(s,i,n));return[o]}finally{s.close(),s.delete()}}function Ks(t,e,n){const{alphaFlag:s,height:r,width:o}=t.getImageLevelInfo(e,0,0),{compressed:i,format:a,basisFormat:c}=vt(n,s),l=t.getImageTranscodedSizeInBytes(e,0,0,c),f=new Uint8Array(l);if(!t.transcodeImage(f,e,0,0,c,0,-1,-1))throw new Error("Failed to transcode KTX2 image");return{width:o,height:r,data:f,compressed:i,levelSize:l,hasAlpha:s,format:a}}function vt(t,e){let n=t&&t.basis&&t.basis.format;return n==="auto"&&(n=Dt()),typeof n=="object"&&(n=e?n.alpha:n.noAlpha),n=n.toLowerCase(),Ns[n]}function Dt(){const t=Hs();return t.has("astc")?"astc-4x4":t.has("dxt")?{alpha:"bc3",noAlpha:"bc1"}:t.has("pvrtc")?{alpha:"pvrtc1-4-rgba",noAlpha:"pvrtc1-4-rgb"}:t.has("etc1")?"etc1":t.has("etc2")?"etc2":"rgb565"}const js={dataType:null,batchType:null,name:"Basis",id:"basis",module:"textures",version:vs,worker:!0,extensions:["basis","ktx2"],mimeTypes:["application/octet-stream","image/ktx2"],tests:["sB"],binary:!0,options:{basis:{format:"auto",libraryPath:"libs/",containerFormat:"auto",module:"transcoder"}}},Vs={...js,parse:Js};function Xs(t){return{addressModeU:rt(t.wrapS),addressModeV:rt(t.wrapT),magFilter:Qs(t.magFilter),...Ys(t.minFilter)}}function rt(t){switch(t){case 33071:return"clamp-to-edge";case 10497:return"repeat";case 33648:return"mirror-repeat";default:return}}function Qs(t){switch(t){case 9728:return"nearest";case 9729:return"linear";default:return}}function Ys(t){switch(t){case 9728:return{minFilter:"nearest"};case 9729:return{minFilter:"linear"};case 9984:return{minFilter:"nearest",mipmapFilter:"nearest"};case 9985:return{minFilter:"linear",mipmapFilter:"nearest"};case 9986:return{minFilter:"nearest",mipmapFilter:"linear"};case 9987:return{minFilter:"linear",mipmapFilter:"linear"};default:return{}}}function ks(t,e,n,s){const r={defines:{MANUAL_SRGB:!0,SRGB_FAST_APPROXIMATION:!0},bindings:{},uniforms:{camera:[0,0,0],metallicRoughnessValues:[1,1]},parameters:{},glParameters:{},generatedTextures:[]};r.defines.USE_TEX_LOD=!0;const{imageBasedLightingEnvironment:o}=s;return o&&(r.bindings.pbr_diffuseEnvSampler=o.diffuseEnvSampler.texture,r.bindings.pbr_specularEnvSampler=o.specularEnvSampler.texture,r.bindings.pbr_BrdfLUT=o.brdfLutTexture.texture,r.uniforms.scaleIBLAmbient=[1,1]),s?.pbrDebug&&(r.defines.PBR_DEBUG=!0,r.uniforms.scaleDiffBaseMR=[0,0,0,0],r.uniforms.scaleFGDSpec=[0,0,0,0]),n.NORMAL&&(r.defines.HAS_NORMALS=!0),n.TANGENT&&s?.useTangents&&(r.defines.HAS_TANGENTS=!0),n.TEXCOORD_0&&(r.defines.HAS_UV=!0),s?.imageBasedLightingEnvironment&&(r.defines.USE_IBL=!0),s?.lights&&(r.defines.USE_LIGHTS=!0),e&&zs(t,e,r),r}function zs(t,e,n){if(n.uniforms.unlit=!!e.unlit,e.pbrMetallicRoughness&&Ws(t,e.pbrMetallicRoughness,n),e.normalTexture){w(t,e.normalTexture,"pbr_normalSampler","HAS_NORMALMAP",n);const{scale:s=1}=e.normalTexture;n.uniforms.normalScale=s}if(e.occlusionTexture){w(t,e.occlusionTexture,"pbr_occlusionSampler","HAS_OCCLUSIONMAP",n);const{strength:s=1}=e.occlusionTexture;n.uniforms.occlusionStrength=s}switch(e.emissiveTexture&&(w(t,e.emissiveTexture,"pbr_emissiveSampler","HAS_EMISSIVEMAP",n),n.uniforms.emissiveFactor=e.emissiveFactor||[0,0,0]),e.alphaMode||"MASK"){case"MASK":const{alphaCutoff:s=.5}=e;n.defines.ALPHA_CUTOFF=!0,n.uniforms.alphaCutoff=s;break;case"BLEND":L.warn("glTF BLEND alphaMode might not work well because it requires mesh sorting")(),n.parameters.blend=!0,n.parameters.blendColorOperation="add",n.parameters.blendColorSrcFactor="src-alpha",n.parameters.blendColorDstFactor="one-minus-src-alpha",n.parameters.blendAlphaOperation="add",n.parameters.blendAlphaSrcFactor="one",n.parameters.blendAlphaDstFactor="one-minus-src-alpha",n.glParameters.blend=!0,n.glParameters.blendEquation=32774,n.glParameters.blendFunc=[770,771,1,771];break}}function Ws(t,e,n){e.baseColorTexture&&w(t,e.baseColorTexture,"pbr_baseColorSampler","HAS_BASECOLORMAP",n),n.uniforms.baseColorFactor=e.baseColorFactor||[1,1,1,1],e.metallicRoughnessTexture&&w(t,e.metallicRoughnessTexture,"pbr_metallicRoughnessSampler","HAS_METALROUGHNESSMAP",n);const{metallicFactor:s=1,roughnessFactor:r=1}=e;n.uniforms.metallicRoughnessValues=[s,r]}function w(t,e,n,s,r){const o=e.texture.source.image;let i;o.compressed?i=o:i={data:o};const a={wrapS:10497,wrapT:10497,...e?.texture?.sampler},c=t.createTexture({id:e.uniformName||e.id,sampler:Xs(a),...i});r.bindings[n]=c,s&&(r.defines[s]=!0),r.generatedTextures.push(c)}var _;(function(t){t[t.POINTS=0]="POINTS",t[t.LINES=1]="LINES",t[t.LINE_LOOP=2]="LINE_LOOP",t[t.LINE_STRIP=3]="LINE_STRIP",t[t.TRIANGLES=4]="TRIANGLES",t[t.TRIANGLE_STRIP=5]="TRIANGLE_STRIP",t[t.TRIANGLE_FAN=6]="TRIANGLE_FAN"})(_||(_={}));function Zs(t){switch(t){case _.POINTS:return"point-list";case _.LINES:return"line-list";case _.LINE_STRIP:return"line-strip";case _.TRIANGLES:return"triangle-list";case _.TRIANGLE_STRIP:return"triangle-strip";default:throw new Error(String(t))}}const qs=`
layout(0) positions: vec4; // in vec4 POSITION;

  #ifdef HAS_NORMALS
    in vec4 normals; // in vec4 NORMAL;
  #endif

  #ifdef HAS_TANGENTS
    in vec4 TANGENT;
  #endif

  #ifdef HAS_UV
    // in vec2 TEXCOORD_0;
    in vec2 texCoords;
  #endif

@vertex
  void main(void) {
    vec4 _NORMAL = vec4(0.);
    vec4 _TANGENT = vec4(0.);
    vec2 _TEXCOORD_0 = vec2(0.);

    #ifdef HAS_NORMALS
      _NORMAL = normals;
    #endif

    #ifdef HAS_TANGENTS
      _TANGENT = TANGENT;
    #endif

    #ifdef HAS_UV
      _TEXCOORD_0 = texCoords;
    #endif

    pbr_setPositionNormalTangentUV(positions, _NORMAL, _TANGENT, _TEXCOORD_0);
    gl_Position = u_MVPMatrix * positions;
  }

@fragment
  out vec4 fragmentColor;

  void main(void) {
    vec3 pos = pbr_vPosition;
    fragmentColor = pbr_filterColor(vec4(1.0));
  }
`,$s=`#version 300 es

  // in vec4 POSITION;
  in vec4 positions;

  #ifdef HAS_NORMALS
    // in vec4 NORMAL;
    in vec4 normals;
  #endif

  #ifdef HAS_TANGENTS
    in vec4 TANGENT;
  #endif

  #ifdef HAS_UV
    // in vec2 TEXCOORD_0;
    in vec2 texCoords;
  #endif

  void main(void) {
    vec4 _NORMAL = vec4(0.);
    vec4 _TANGENT = vec4(0.);
    vec2 _TEXCOORD_0 = vec2(0.);

    #ifdef HAS_NORMALS
      _NORMAL = normals;
    #endif

    #ifdef HAS_TANGENTS
      _TANGENT = TANGENT;
    #endif

    #ifdef HAS_UV
      _TEXCOORD_0 = texCoords;
    #endif

    pbr_setPositionNormalTangentUV(positions, _NORMAL, _TANGENT, _TEXCOORD_0);
    gl_Position = pbrProjection.modelViewProjectionMatrix * positions;
  }
`,er=`#version 300 es
  out vec4 fragmentColor;

  void main(void) {
    vec3 pos = pbr_vPosition;
    fragmentColor = pbr_filterColor(vec4(1.0));
  }
`;function tr(t,e){const{id:n,geometry:s,parsedPPBRMaterial:r,vertexCount:o,modelOptions:i={}}=e;L.info(4,"createGLTFModel defines: ",r.defines)();const a=[],c={depthWriteEnabled:!0,depthCompare:"less",depthFormat:"depth24plus",cullMode:"back"},l={id:n,source:qs,vs:$s,fs:er,geometry:s,topology:s.topology,vertexCount:o,modules:[Ft],...i,defines:{...r.defines,...i.defines},parameters:{...c,...r.parameters,...i.parameters}},f=new bt(t,l),{camera:u,...A}={...r.uniforms,...i.uniforms,...r.bindings,...i.bindings};return f.shaderInputs.setProps({pbrMaterial:A,pbrProjection:{camera:u}}),new Re({managedResources:a,model:f})}const nr={modelOptions:{},pbrDebug:!1,imageBasedLightingEnvironment:void 0,lights:!0,useTangents:!1};function sr(t,e,n={}){const s={...nr,...n};return e.scenes.map(o=>rr(t,o,e.nodes,s))}function rr(t,e,n,s){const o=(e.nodes||[]).map(a=>St(t,a,n,s));return new U({id:e.name||e.id,children:o})}function St(t,e,n,s){if(!e._node){const i=(e.children||[]).map(c=>St(t,c,n,s));e.mesh&&i.push(or(t,e.mesh,s));const a=new U({id:e.name||e.id,children:i});if(e.matrix)a.setMatrix(e.matrix);else{if(a.matrix.identity(),e.translation&&a.matrix.translate(e.translation),e.rotation){const c=new x().fromQuaternion(e.rotation);a.matrix.multiplyRight(c)}e.scale&&a.matrix.scale(e.scale)}e._node=a}const r=n.find(o=>o.id===e.id);return r._node=e._node,e._node}function or(t,e,n){if(!e._mesh){const r=(e.primitives||[]).map((i,a)=>ir(t,i,a,e,n)),o=new U({id:e.name||e.id,children:r});e._mesh=o}return e._mesh}function ir(t,e,n,s,r){const o=e.name||`${s.name||s.id}-primitive-${n}`,i=Zs(e.mode||4),a=e.indices?e.indices.count:ar(e.attributes),c=ot(o,e,i),l=ks(t,e.material,c.attributes,r),f=tr(t,{id:o,geometry:ot(o,e,i),parsedPPBRMaterial:l,modelOptions:r.modelOptions,vertexCount:a});return f.bounds=[e.attributes.POSITION.min,e.attributes.POSITION.max],f}function ar(t){throw new Error("getVertexCount not implemented")}function ot(t,e,n){const s={};for(const[r,o]of Object.entries(e.attributes)){const{components:i,size:a,value:c}=o;s[r]={size:a??i,value:c}}return new $({id:t,topology:n,indices:e.indices.value,attributes:s})}const ge=new gs;function cr(t,{input:e,interpolation:n,output:s},r,o){const i=e[e.length-1],a=t%i,c=e.findIndex(A=>A>=a),l=Math.max(0,c-1);if(!Array.isArray(r[o]))switch(o){case"translation":r[o]=[0,0,0];break;case"rotation":r[o]=[0,0,0,1];break;case"scale":r[o]=[1,1,1];break;default:L.warn(`Bad animation path ${o}`)()}const f=e[l],u=e[c];switch(n){case"STEP":ur(r,o,s[l]);break;case"LINEAR":if(u>f){const A=(a-f)/(u-f);lr(r,o,s[l],s[c],A)}break;case"CUBICSPLINE":if(u>f){const A=(a-f)/(u-f),d=u-f,B=s[3*l+1],m=s[3*l+2],p=s[3*c+0],C=s[3*c+1];fr(r,o,{p0:B,outTangent0:m,inTangent1:p,p1:C,tDiff:d,ratio:A})}break;default:L.warn(`Interpolation ${n} not supported`)();break}}function lr(t,e,n,s,r){if(!t[e])throw new Error;if(e==="rotation"){ge.slerp({start:n,target:s,ratio:r});for(let o=0;o<ge.length;o++)t[e][o]=ge[o]}else for(let o=0;o<n.length;o++)t[e][o]=r*s[o]+(1-r)*n[o]}function fr(t,e,{p0:n,outTangent0:s,inTangent1:r,p1:o,tDiff:i,ratio:a}){if(!t[e])throw new Error;for(let c=0;c<t[e].length;c++){const l=s[c]*i,f=r[c]*i;t[e][c]=(2*Math.pow(a,3)-3*Math.pow(a,2)+1)*n[c]+(Math.pow(a,3)-2*Math.pow(a,2)+a)*l+(-2*Math.pow(a,3)+3*Math.pow(a,2))*o[c]+(Math.pow(a,3)-Math.pow(a,2))*f}}function ur(t,e,n){if(!t[e])throw new Error;for(let s=0;s<n.length;s++)t[e][s]=n[s]}class Ar{animation;startTime=0;playing=!0;speed=1;constructor(e){this.animation=e.animation,this.animation.name||="unnamed",Object.assign(this,e)}setTime(e){if(!this.playing)return;const s=(e/1e3-this.startTime)*this.speed;this.animation.channels.forEach(({sampler:r,target:o,path:i})=>{cr(s,r,o,i),mr(o,o._node)})}}class dr{animations;constructor(e){this.animations=e.animations.map((n,s)=>{const r=n.name||`Animation-${s}`;return new Ar({animation:{name:r,channels:n.channels}})})}animate(e){L.warn("GLTFAnimator#animate is deprecated. Use GLTFAnimator#setTime instead")(),this.setTime(e)}setTime(e){this.animations.forEach(n=>n.setTime(e))}getAnimations(){return this.animations}}const Br=new x;function mr(t,e){if(e.matrix.identity(),t.translation&&e.matrix.translate(t.translation),t.rotation){const n=Br.fromQuaternion(t.rotation);e.matrix.multiplyRight(n)}t.scale&&e.matrix.scale(t.scale)}const hr={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT2:4,MAT3:9,MAT4:16},pr={5120:Int8Array,5121:Uint8Array,5122:Int16Array,5123:Uint16Array,5125:Uint32Array,5126:Float32Array};function Cr(t){const e=pr[t.componentType],n=hr[t.type],s=n*t.count,{buffer:r,byteOffset:o=0}=t.bufferView?.data??{};return{typedArray:new e(r,o+(t.byteOffset||0),s),components:n}}function br(t){return(t.animations||[]).map((n,s)=>{const r=n.name||`Animation-${s}`,o=n.samplers.map(({input:a,interpolation:c="LINEAR",output:l})=>({input:it(t.accessors[a]),interpolation:c,output:it(t.accessors[l])})),i=n.channels.map(({sampler:a,target:c})=>({sampler:o[a],target:t.nodes[c.node??0],path:c.path}));return{name:r,channels:i}})}function it(t){if(!t._animation){const{typedArray:e,components:n}=Cr(t);if(n===1)t._animation=Array.from(e);else{const s=[];for(let r=0;r<e.length;r+=n)s.push(Array.from(e.slice(r,r+n)));t._animation=s}}return t._animation}function Ge(t){if(ArrayBuffer.isView(t)||t instanceof ArrayBuffer||t instanceof ImageBitmap)return t;if(Array.isArray(t))return t.map(Ge);if(t&&typeof t=="object"){const e={};for(const n in t)e[n]=Ge(t[n]);return e}return t}function gr(t,e,n){e=Ge(e);const s=sr(t,e,n),r=br(e),o=new dr({animations:r});return{scenes:s,animator:o}}function T(t,e){if(!t)throw new Error(e||"assert failed: gltf")}const Ot={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT2:4,MAT3:9,MAT4:16},xt={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4},Er=1.33,at=["SCALAR","VEC2","VEC3","VEC4"],Ir=[[Int8Array,5120],[Uint8Array,5121],[Int16Array,5122],[Uint16Array,5123],[Uint32Array,5125],[Float32Array,5126],[Float64Array,5130]],Mr=new Map(Ir),Tr={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT2:4,MAT3:9,MAT4:16},yr={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4},Fr={5120:Int8Array,5121:Uint8Array,5122:Int16Array,5123:Uint16Array,5125:Uint32Array,5126:Float32Array};function Lt(t){return at[t-1]||at[0]}function ce(t){const e=Mr.get(t.constructor);if(!e)throw new Error("Illegal typed array");return e}function Le(t,e){const n=Fr[t.componentType],s=Tr[t.type],r=yr[t.componentType],o=t.count*s,i=t.count*s*r;T(i>=0&&i<=e.byteLength);const a=xt[t.componentType],c=Ot[t.type];return{ArrayType:n,length:o,byteLength:i,componentByteSize:a,numberOfComponentsInElement:c}}function za(t){let{images:e,bufferViews:n}=t;e=e||[],n=n||[];const s=e.map(i=>i.bufferView);n=n.filter(i=>!s.includes(i));const r=n.reduce((i,a)=>i+a.byteLength,0),o=e.reduce((i,a)=>{const{width:c,height:l}=a.image;return i+c*l},0);return r+Math.ceil(4*o*Er)}function _r(t,e,n){const s=t.bufferViews[n];T(s);const r=s.buffer,o=e[r];T(o);const i=(s.byteOffset||0)+o.byteOffset;return new Uint8Array(o.arrayBuffer,i,s.byteLength)}function Rr(t,e,n){const s=typeof n=="number"?t.accessors?.[n]:n;if(!s)throw new Error(`No gltf accessor ${JSON.stringify(n)}`);const r=t.bufferViews?.[s.bufferView||0];if(!r)throw new Error(`No gltf buffer view for accessor ${r}`);const{arrayBuffer:o,byteOffset:i}=e[r.buffer],a=(i||0)+(s.byteOffset||0)+(r.byteOffset||0),{ArrayType:c,length:l,componentByteSize:f,numberOfComponentsInElement:u}=Le(s,r),A=f*u,d=r.byteStride||A;if(typeof r.byteStride>"u"||r.byteStride===A)return new c(o,a,l);const B=new c(l);for(let m=0;m<s.count;m++){const p=new c(o,a+m*d,u);B.set(p,m*u)}return B}function Gr(){return{asset:{version:"2.0",generator:"loaders.gl"},buffers:[],extensions:{},extensionsRequired:[],extensionsUsed:[]}}class b{gltf;sourceBuffers;byteLength;constructor(e){this.gltf={json:e?.json||Gr(),buffers:e?.buffers||[],images:e?.images||[]},this.sourceBuffers=[],this.byteLength=0,this.gltf.buffers&&this.gltf.buffers[0]&&(this.byteLength=this.gltf.buffers[0].byteLength,this.sourceBuffers=[this.gltf.buffers[0]])}get json(){return this.gltf.json}getApplicationData(e){return this.json[e]}getExtraData(e){return(this.json.extras||{})[e]}hasExtension(e){const n=this.getUsedExtensions().find(r=>r===e),s=this.getRequiredExtensions().find(r=>r===e);return typeof n=="string"||typeof s=="string"}getExtension(e){const n=this.getUsedExtensions().find(r=>r===e),s=this.json.extensions||{};return n?s[e]:null}getRequiredExtension(e){return this.getRequiredExtensions().find(s=>s===e)?this.getExtension(e):null}getRequiredExtensions(){return this.json.extensionsRequired||[]}getUsedExtensions(){return this.json.extensionsUsed||[]}getRemovedExtensions(){return this.json.extensionsRemoved||[]}getObjectExtension(e,n){return(e.extensions||{})[n]}getScene(e){return this.getObject("scenes",e)}getNode(e){return this.getObject("nodes",e)}getSkin(e){return this.getObject("skins",e)}getMesh(e){return this.getObject("meshes",e)}getMaterial(e){return this.getObject("materials",e)}getAccessor(e){return this.getObject("accessors",e)}getTexture(e){return this.getObject("textures",e)}getSampler(e){return this.getObject("samplers",e)}getImage(e){return this.getObject("images",e)}getBufferView(e){return this.getObject("bufferViews",e)}getBuffer(e){return this.getObject("buffers",e)}getObject(e,n){if(typeof n=="object")return n;const s=this.json[e]&&this.json[e][n];if(!s)throw new Error(`glTF file error: Could not find ${e}[${n}]`);return s}getTypedArrayForBufferView(e){e=this.getBufferView(e);const n=e.buffer,s=this.gltf.buffers[n];T(s);const r=(e.byteOffset||0)+s.byteOffset;return new Uint8Array(s.arrayBuffer,r,e.byteLength)}getTypedArrayForAccessor(e){const n=this.getAccessor(e);return Rr(this.gltf.json,this.gltf.buffers,n)}getTypedArrayForImageData(e){e=this.getAccessor(e);const n=this.getBufferView(e.bufferView),r=this.getBuffer(n.buffer).data,o=n.byteOffset||0;return new Uint8Array(r,o,n.byteLength)}addApplicationData(e,n){return this.json[e]=n,this}addExtraData(e,n){return this.json.extras=this.json.extras||{},this.json.extras[e]=n,this}addObjectExtension(e,n,s){return e.extensions=e.extensions||{},e.extensions[n]=s,this.registerUsedExtension(n),this}setObjectExtension(e,n,s){const r=e.extensions||{};r[n]=s}removeObjectExtension(e,n){const s=e?.extensions||{};if(s[n]){this.json.extensionsRemoved=this.json.extensionsRemoved||[];const r=this.json.extensionsRemoved;r.includes(n)||r.push(n)}delete s[n]}addExtension(e,n={}){return T(n),this.json.extensions=this.json.extensions||{},this.json.extensions[e]=n,this.registerUsedExtension(e),n}addRequiredExtension(e,n={}){return T(n),this.addExtension(e,n),this.registerRequiredExtension(e),n}registerUsedExtension(e){this.json.extensionsUsed=this.json.extensionsUsed||[],this.json.extensionsUsed.find(n=>n===e)||this.json.extensionsUsed.push(e)}registerRequiredExtension(e){this.registerUsedExtension(e),this.json.extensionsRequired=this.json.extensionsRequired||[],this.json.extensionsRequired.find(n=>n===e)||this.json.extensionsRequired.push(e)}removeExtension(e){if(this.json.extensions?.[e]){this.json.extensionsRemoved=this.json.extensionsRemoved||[];const n=this.json.extensionsRemoved;n.includes(e)||n.push(e)}this.json.extensions&&delete this.json.extensions[e],this.json.extensionsRequired&&this._removeStringFromArray(this.json.extensionsRequired,e),this.json.extensionsUsed&&this._removeStringFromArray(this.json.extensionsUsed,e)}setDefaultScene(e){this.json.scene=e}addScene(e){const{nodeIndices:n}=e;return this.json.scenes=this.json.scenes||[],this.json.scenes.push({nodes:n}),this.json.scenes.length-1}addNode(e){const{meshIndex:n,matrix:s}=e;this.json.nodes=this.json.nodes||[];const r={mesh:n};return s&&(r.matrix=s),this.json.nodes.push(r),this.json.nodes.length-1}addMesh(e){const{attributes:n,indices:s,material:r,mode:o=4}=e,a={primitives:[{attributes:this._addAttributes(n),mode:o}]};if(s){const c=this._addIndices(s);a.primitives[0].indices=c}return Number.isFinite(r)&&(a.primitives[0].material=r),this.json.meshes=this.json.meshes||[],this.json.meshes.push(a),this.json.meshes.length-1}addPointCloud(e){const s={primitives:[{attributes:this._addAttributes(e),mode:0}]};return this.json.meshes=this.json.meshes||[],this.json.meshes.push(s),this.json.meshes.length-1}addImage(e,n){const s=Gn(e),r=n||s?.mimeType,i={bufferView:this.addBufferView(e),mimeType:r};return this.json.images=this.json.images||[],this.json.images.push(i),this.json.images.length-1}addBufferView(e,n=0,s=this.byteLength){const r=e.byteLength;T(Number.isFinite(r)),this.sourceBuffers=this.sourceBuffers||[],this.sourceBuffers.push(e);const o={buffer:n,byteOffset:s,byteLength:r};return this.byteLength+=X(r,4),this.json.bufferViews=this.json.bufferViews||[],this.json.bufferViews.push(o),this.json.bufferViews.length-1}addAccessor(e,n){const s={bufferView:e,type:Lt(n.size),componentType:n.componentType,count:n.count,max:n.max,min:n.min};return this.json.accessors=this.json.accessors||[],this.json.accessors.push(s),this.json.accessors.length-1}addBinaryBuffer(e,n={size:3}){const s=this.addBufferView(e);let r={min:n.min,max:n.max};(!r.min||!r.max)&&(r=this._getAccessorMinMax(e,n.size));const o={size:n.size,componentType:ce(e),count:Math.round(e.length/n.size),min:r.min,max:r.max};return this.addAccessor(s,Object.assign(o,n))}addTexture(e){const{imageIndex:n}=e,s={source:n};return this.json.textures=this.json.textures||[],this.json.textures.push(s),this.json.textures.length-1}addMaterial(e){return this.json.materials=this.json.materials||[],this.json.materials.push(e),this.json.materials.length-1}createBinaryChunk(){const e=this.byteLength,n=new ArrayBuffer(e),s=new Uint8Array(n);let r=0;for(const o of this.sourceBuffers||[])r=wn(o,s,r);this.json?.buffers?.[0]?this.json.buffers[0].byteLength=e:this.json.buffers=[{byteLength:e}],this.gltf.binary=n,this.sourceBuffers=[n],this.gltf.buffers=[{arrayBuffer:n,byteOffset:0,byteLength:n.byteLength}]}_removeStringFromArray(e,n){let s=!0;for(;s;){const r=e.indexOf(n);r>-1?e.splice(r,1):s=!1}}_addAttributes(e={}){const n={};for(const s in e){const r=e[s],o=this._getGltfAttributeName(s),i=this.addBinaryBuffer(r.value,r);n[o]=i}return n}_addIndices(e){return this.addBinaryBuffer(e,{size:1})}_getGltfAttributeName(e){switch(e.toLowerCase()){case"position":case"positions":case"vertices":return"POSITION";case"normal":case"normals":return"NORMAL";case"color":case"colors":return"COLOR_0";case"texcoord":case"texcoords":return"TEXCOORD_0";default:return e}}_getAccessorMinMax(e,n){const s={min:null,max:null};if(e.length<n)return s;s.min=[],s.max=[];const r=e.subarray(0,n);for(const o of r)s.min.push(o),s.max.push(o);for(let o=n;o<e.length;o+=n)for(let i=0;i<n;i++)s.min[0+i]=Math.min(s.min[0+i],e[o+i]),s.max[0+i]=Math.max(s.max[0+i],e[o+i]);return s}}function ct(t){return(t%1+1)%1}const Ht={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT2:4,MAT3:9,MAT4:16,BOOLEAN:1,STRING:1,ENUM:1},vr={INT8:Int8Array,UINT8:Uint8Array,INT16:Int16Array,UINT16:Uint16Array,INT32:Int32Array,UINT32:Uint32Array,INT64:BigInt64Array,UINT64:BigUint64Array,FLOAT32:Float32Array,FLOAT64:Float64Array},Pt={INT8:1,UINT8:1,INT16:2,UINT16:2,INT32:4,UINT32:4,INT64:8,UINT64:8,FLOAT32:4,FLOAT64:8};function He(t,e){return Pt[e]*Ht[t]}function le(t,e,n,s){if(n!=="UINT8"&&n!=="UINT16"&&n!=="UINT32"&&n!=="UINT64")return null;const r=t.getTypedArrayForBufferView(e),o=fe(r,"SCALAR",n,s+1);return o instanceof BigInt64Array||o instanceof BigUint64Array?null:o}function fe(t,e,n,s=1){const r=Ht[e],o=vr[n],i=Pt[n],a=s*r,c=a*i;let l=t.buffer,f=t.byteOffset;return f%i!==0&&(l=new Uint8Array(l).slice(f,f+c).buffer,f=0),new o(l,f,a)}function Pe(t,e,n){const s=`TEXCOORD_${e.texCoord||0}`,r=n.attributes[s],o=t.getTypedArrayForAccessor(r),i=t.gltf.json,a=e.index,c=i.textures?.[a]?.source;if(typeof c<"u"){const l=i.images?.[c]?.mimeType,f=t.gltf.images?.[c];if(f&&typeof f.width<"u"){const u=[];for(let A=0;A<o.length;A+=2){const d=Dr(f,l,o,A,e.channels);u.push(d)}return u}}return[]}function Ut(t,e,n,s,r){if(!n?.length)return;const o=[];for(const f of n){let u=s.findIndex(A=>A===f);u===-1&&(u=s.push(f)-1),o.push(u)}const i=new Uint32Array(o),a=t.gltf.buffers.push({arrayBuffer:i.buffer,byteOffset:i.byteOffset,byteLength:i.byteLength})-1,c=t.addBufferView(i,a,0),l=t.addAccessor(c,{size:1,componentType:ce(i),count:i.length});r.attributes[e]=l}function Dr(t,e,n,s,r=[0]){const o={r:{offset:0,shift:0},g:{offset:1,shift:8},b:{offset:2,shift:16},a:{offset:3,shift:24}},i=n[s],a=n[s+1];let c=1;e&&(e.indexOf("image/jpeg")!==-1||e.indexOf("image/png")!==-1)&&(c=4);const l=Sr(i,a,t,c);let f=0;for(const u of r){const A=typeof u=="number"?Object.values(o)[u]:o[u],d=l+A.offset,B=vn(t);if(B.data.length<=d)throw new Error(`${B.data.length} <= ${d}`);const m=B.data[d];f|=m<<A.shift}return f}function Sr(t,e,n,s=1){const r=n.width,o=ct(t)*(r-1),i=Math.round(o),a=n.height,c=ct(e)*(a-1),l=Math.round(c),f=n.components?n.components:s;return(l*r+i)*f}function Nt(t,e,n,s,r){const o=[];for(let i=0;i<e;i++){const a=n[i],c=n[i+1]-n[i];if(c+a>s)break;const l=a/r,f=c/r;o.push(t.slice(l,l+f))}return o}function Jt(t,e,n){const s=[];for(let r=0;r<e;r++){const o=r*n;s.push(t.slice(o,o+n))}return s}function wt(t,e,n,s){if(n)throw new Error("Not implemented - arrayOffsets for strings is specified");if(s){const r=[],o=new TextDecoder("utf8");let i=0;for(let a=0;a<t;a++){const c=s[a+1]-s[a];if(c+i<=e.length){const l=e.subarray(i,c+i),f=o.decode(l);r.push(f),i+=c}}return r}return[]}const O="EXT_mesh_features",Or=O;async function xr(t,e){const n=new b(t);Hr(n,e)}function Lr(t,e){const n=new b(t);return Ur(n),n.createBinaryChunk(),n.gltf}function Hr(t,e){const n=t.gltf.json;if(n.meshes)for(const s of n.meshes)for(const r of s.primitives)Pr(t,r,e)}function Pr(t,e,n){if(!n?.gltf?.loadBuffers)return;const r=e.extensions?.[O]?.featureIds;if(r)for(const o of r){let i;if(typeof o.attribute<"u"){const a=`_FEATURE_ID_${o.attribute}`,c=e.attributes[a];i=t.getTypedArrayForAccessor(c)}else typeof o.texture<"u"&&n?.gltf?.loadImages?i=Pe(t,o.texture,e):i=[];o.data=i}}function Ur(t,e){const n=t.gltf.json.meshes;if(n)for(const s of n)for(const r of s.primitives)Jr(t,r)}function Nr(t,e,n,s){e.extensions||(e.extensions={});let r=e.extensions[O];r||(r={featureIds:[]},e.extensions[O]=r);const{featureIds:o}=r,i={featureCount:n.length,propertyTable:s,data:n};o.push(i),t.addObjectExtension(e,O,r)}function Jr(t,e){const n=e.extensions?.[O];if(!n)return;const s=n.featureIds;s.forEach((r,o)=>{if(r.data){const{accessorKey:i,index:a}=wr(e.attributes),c=new Uint32Array(r.data);s[o]={featureCount:c.length,propertyTable:r.propertyTable,attribute:a},t.gltf.buffers.push({arrayBuffer:c.buffer,byteOffset:c.byteOffset,byteLength:c.byteLength});const l=t.addBufferView(c),f=t.addAccessor(l,{size:1,componentType:ce(c),count:c.length});e.attributes[i]=f}})}function wr(t){const e="_FEATURE_ID_",n=Object.keys(t).filter(o=>o.indexOf(e)===0);let s=-1;for(const o of n){const i=Number(o.substring(e.length));i>s&&(s=i)}return s++,{accessorKey:`${e}${s}`,index:s}}const Kr=Object.freeze(Object.defineProperty({__proto__:null,createExtMeshFeatures:Nr,decode:xr,encode:Lr,name:Or},Symbol.toStringTag,{value:"Module"})),H="EXT_structural_metadata",jr=H;async function Vr(t,e){const n=new b(t);Qr(n,e)}function Xr(t,e){const n=new b(t);return co(n),n.createBinaryChunk(),n.gltf}function Qr(t,e){if(!e.gltf?.loadBuffers)return;const n=t.getExtension(H);n&&(e.gltf?.loadImages&&Yr(t,n),kr(t,n))}function Yr(t,e){const n=e.propertyTextures,s=t.gltf.json;if(n&&s.meshes)for(const r of s.meshes)for(const o of r.primitives)Wr(t,n,o,e)}function kr(t,e){const n=e.schema;if(!n)return;const s=n.classes,r=e.propertyTables;if(s&&r)for(const o in s){const i=zr(r,o);i&&qr(t,n,i)}}function zr(t,e){for(const n of t)if(n.class===e)return n;return null}function Wr(t,e,n,s){if(!e)return;const o=n.extensions?.[H]?.propertyTextures;if(o)for(const i of o){const a=e[i];Zr(t,a,n,s)}}function Zr(t,e,n,s){if(!e.properties)return;s.dataAttributeNames||(s.dataAttributeNames=[]);const r=e.class;for(const o in e.properties){const i=`${r}_${o}`,a=e.properties?.[o];if(!a)continue;a.data||(a.data=[]);const c=a.data,l=Pe(t,a,n);l!==null&&(Ut(t,i,l,c,n),a.data=c,s.dataAttributeNames.push(i))}}function qr(t,e,n){const s=e.classes?.[n.class];if(!s)throw new Error(`Incorrect data in the EXT_structural_metadata extension: no schema class with name ${n.class}`);const r=n.count;for(const o in s.properties){const i=s.properties[o],a=n.properties?.[o];if(a){const c=$r(t,e,i,r,a);a.data=c}}}function $r(t,e,n,s,r){let o=[];const i=r.values,a=t.getTypedArrayForBufferView(i),c=eo(t,n,r,s),l=to(t,r,s);switch(n.type){case"SCALAR":case"VEC2":case"VEC3":case"VEC4":case"MAT2":case"MAT3":case"MAT4":{o=no(n,s,a,c);break}case"BOOLEAN":throw new Error(`Not implemented - classProperty.type=${n.type}`);case"STRING":{o=wt(s,a,c,l);break}case"ENUM":{o=so(e,n,s,a,c);break}default:throw new Error(`Unknown classProperty type ${n.type}`)}return o}function eo(t,e,n,s){return e.array&&typeof e.count>"u"&&typeof n.arrayOffsets<"u"?le(t,n.arrayOffsets,n.arrayOffsetType||"UINT32",s):null}function to(t,e,n){return typeof e.stringOffsets<"u"?le(t,e.stringOffsets,e.stringOffsetType||"UINT32",n):null}function no(t,e,n,s){const r=t.array,o=t.count,i=He(t.type,t.componentType),a=n.byteLength/i;let c;return t.componentType?c=fe(n,t.type,t.componentType,a):c=n,r?s?Nt(c,e,s,n.length,i):o?Jt(c,e,o):[]:c}function so(t,e,n,s,r){const o=e.enumType;if(!o)throw new Error("Incorrect data in the EXT_structural_metadata extension: classProperty.enumType is not set for type ENUM");const i=t.enums?.[o];if(!i)throw new Error(`Incorrect data in the EXT_structural_metadata extension: schema.enums does't contain ${o}`);const a=i.valueType||"UINT16",c=He(e.type,a),l=s.byteLength/c;let f=fe(s,e.type,a,l);if(f||(f=s),e.array){if(r)return ro({valuesData:f,numberOfElements:n,arrayOffsets:r,valuesDataBytesLength:s.length,elementSize:c,enumEntry:i});const u=e.count;return u?oo(f,n,u,i):[]}return Ue(f,0,n,i)}function ro(t){const{valuesData:e,numberOfElements:n,arrayOffsets:s,valuesDataBytesLength:r,elementSize:o,enumEntry:i}=t,a=[];for(let c=0;c<n;c++){const l=s[c],f=s[c+1]-s[c];if(f+l>r)break;const u=l/o,A=f/o,d=Ue(e,u,A,i);a.push(d)}return a}function oo(t,e,n,s){const r=[];for(let o=0;o<e;o++){const i=n*o,a=Ue(t,i,n,s);r.push(a)}return r}function Ue(t,e,n,s){const r=[];for(let o=0;o<n;o++)if(t instanceof BigInt64Array||t instanceof BigUint64Array)r.push("");else{const i=t[e+o],a=io(s,i);a?r.push(a.name):r.push("")}return r}function io(t,e){for(const n of t.values)if(n.value===e)return n;return null}const ao="schemaClassId";function co(t,e){const n=t.getExtension(H);if(n&&n.propertyTables)for(const s of n.propertyTables){const r=s.class,o=n.schema?.classes?.[r];s.properties&&o&&lo(s,o,t)}}function lo(t,e,n){for(const s in t.properties){const r=t.properties[s].data;if(r){const o=e.properties[s];if(o){const i=Bo(r,o,n);t.properties[s]=i}}}}function fo(t,e,n=ao){let s=t.getExtension(H);s||(s=t.addExtension(H)),s.schema=uo(e,n,s.schema);const r=Ao(e,n,s.schema);return s.propertyTables||(s.propertyTables=[]),s.propertyTables.push(r)-1}function uo(t,e,n){const s=n??{id:"schema_id"},r={properties:{}};for(const o of t){const i={type:o.elementType,componentType:o.componentType};r.properties[o.name]=i}return s.classes={},s.classes[e]=r,s}function Ao(t,e,n){const s={class:e,count:0};let r=0;const o=n.classes?.[e];for(const i of t){if(r===0&&(r=i.values.length),r!==i.values.length&&i.values.length)throw new Error("Illegal values in attributes");o?.properties[i.name]&&(s.properties||(s.properties={}),s.properties[i.name]={values:0,data:i.values})}return s.count=r,s}function Bo(t,e,n){const s={values:0};if(e.type==="STRING"){const{stringData:r,stringOffsets:o}=po(t);s.stringOffsets=Ee(o,n),s.values=Ee(r,n)}else if(e.type==="SCALAR"&&e.componentType){const r=ho(t,e.componentType);s.values=Ee(r,n)}return s}const mo={INT8:Int8Array,UINT8:Uint8Array,INT16:Int16Array,UINT16:Uint16Array,INT32:Int32Array,UINT32:Uint32Array,INT64:Int32Array,UINT64:Uint32Array,FLOAT32:Float32Array,FLOAT64:Float64Array};function ho(t,e){const n=[];for(const r of t)n.push(Number(r));const s=mo[e];if(!s)throw new Error("Illegal component type");return new s(n)}function po(t){const e=new TextEncoder,n=[];let s=0;for(const c of t){const l=e.encode(c);s+=l.length,n.push(l)}const r=new Uint8Array(s),o=[];let i=0;for(const c of n)r.set(c,i),o.push(i),i+=c.length;o.push(i);const a=new Uint32Array(o);return{stringData:r,stringOffsets:a}}function Ee(t,e){return e.gltf.buffers.push({arrayBuffer:t.buffer,byteOffset:t.byteOffset,byteLength:t.byteLength}),e.addBufferView(t)}const Co=Object.freeze(Object.defineProperty({__proto__:null,createExtStructuralMetadata:fo,decode:Vr,encode:Xr,name:jr},Symbol.toStringTag,{value:"Module"})),Kt="EXT_feature_metadata",bo=Kt;async function go(t,e){const n=new b(t);Eo(n,e)}function Eo(t,e){if(!e.gltf?.loadBuffers)return;const n=t.getExtension(Kt);n&&(e.gltf?.loadImages&&Io(t,n),Mo(t,n))}function Io(t,e){const n=e.schema;if(!n)return;const s=n.classes,{featureTextures:r}=e;if(s&&r)for(const o in s){const i=s[o],a=yo(r,o);a&&_o(t,a,i)}}function Mo(t,e){const n=e.schema;if(!n)return;const s=n.classes,r=e.featureTables;if(s&&r)for(const o in s){const i=To(r,o);i&&Fo(t,n,i)}}function To(t,e){for(const n in t){const s=t[n];if(s.class===e)return s}return null}function yo(t,e){for(const n in t){const s=t[n];if(s.class===e)return s}return null}function Fo(t,e,n){if(!n.class)return;const s=e.classes?.[n.class];if(!s)throw new Error(`Incorrect data in the EXT_structural_metadata extension: no schema class with name ${n.class}`);const r=n.count;for(const o in s.properties){const i=s.properties[o],a=n.properties?.[o];if(a){const c=Ro(t,e,i,r,a);a.data=c}}}function _o(t,e,n){const s=e.class;for(const r in n.properties){const o=e?.properties?.[r];if(o){const i=Oo(t,o,s);o.data=i}}}function Ro(t,e,n,s,r){let o=[];const i=r.bufferView,a=t.getTypedArrayForBufferView(i),c=Go(t,n,r,s),l=vo(t,n,r,s);return n.type==="STRING"||n.componentType==="STRING"?o=wt(s,a,c,l):Do(n)&&(o=So(n,s,a,c)),o}function Go(t,e,n,s){return e.type==="ARRAY"&&typeof e.componentCount>"u"&&typeof n.arrayOffsetBufferView<"u"?le(t,n.arrayOffsetBufferView,n.offsetType||"UINT32",s):null}function vo(t,e,n,s){return typeof n.stringOffsetBufferView<"u"?le(t,n.stringOffsetBufferView,n.offsetType||"UINT32",s):null}function Do(t){const e=["UINT8","INT16","UINT16","INT32","UINT32","INT64","UINT64","FLOAT32","FLOAT64"];return e.includes(t.type)||typeof t.componentType<"u"&&e.includes(t.componentType)}function So(t,e,n,s){const r=t.type==="ARRAY",o=t.componentCount,i="SCALAR",a=t.componentType||t.type,c=He(i,a),l=n.byteLength/c,f=fe(n,i,a,l);return r?s?Nt(f,e,s,n.length,c):o?Jt(f,e,o):[]:f}function Oo(t,e,n){const s=t.gltf.json;if(!s.meshes)return[];const r=[];for(const o of s.meshes)for(const i of o.primitives)xo(t,n,e,r,i);return r}function xo(t,e,n,s,r){const o={channels:n.channels,...n.texture},i=Pe(t,o,r);i&&Ut(t,e,i,s,r)}const Lo=Object.freeze(Object.defineProperty({__proto__:null,decode:go,name:bo},Symbol.toStringTag,{value:"Module"})),Ho="4.3.3",P=!0,lt=1735152710,Ne=12,ie=8,Po=1313821514,Uo=5130562,No=0,Jo=0,wo=1;function Ko(t,e=0){return`${String.fromCharCode(t.getUint8(e+0))}${String.fromCharCode(t.getUint8(e+1))}${String.fromCharCode(t.getUint8(e+2))}${String.fromCharCode(t.getUint8(e+3))}`}function jo(t,e=0,n={}){const s=new DataView(t),{magic:r=lt}=n,o=s.getUint32(e,!1);return o===r||o===lt}function Vo(t,e,n=0,s={}){const r=new DataView(e),o=Ko(r,n+0),i=r.getUint32(n+4,P),a=r.getUint32(n+8,P);switch(Object.assign(t,{header:{byteOffset:n,byteLength:a,hasBinChunk:!1},type:o,version:i,json:{},binChunks:[]}),n+=Ne,t.version){case 1:return Xo(t,r,n);case 2:return Qo(t,r,n,s={});default:throw new Error(`Invalid GLB version ${t.version}. Only supports version 1 and 2.`)}}function Xo(t,e,n){K(t.header.byteLength>Ne+ie);const s=e.getUint32(n+0,P),r=e.getUint32(n+4,P);return n+=ie,K(r===No),ve(t,e,n,s),n+=s,n+=De(t,e,n,t.header.byteLength),n}function Qo(t,e,n,s){return K(t.header.byteLength>Ne+ie),Yo(t,e,n,s),n+t.header.byteLength}function Yo(t,e,n,s){for(;n+8<=t.header.byteLength;){const r=e.getUint32(n+0,P),o=e.getUint32(n+4,P);switch(n+=ie,o){case Po:ve(t,e,n,r);break;case Uo:De(t,e,n,r);break;case Jo:s.strict||ve(t,e,n,r);break;case wo:s.strict||De(t,e,n,r);break}n+=X(r,4)}return n}function ve(t,e,n,s){const r=new Uint8Array(e.buffer,n,s),i=new TextDecoder("utf8").decode(r);return t.json=JSON.parse(i),X(s,4)}function De(t,e,n,s){return t.header.hasBinChunk=!0,t.binChunks.push({byteOffset:n,byteLength:s,arrayBuffer:e.buffer}),X(s,4)}function jt(t,e){if(t.startsWith("data:")||t.startsWith("http:")||t.startsWith("https:"))return t;const s=e.baseUri||e.uri;if(!s)throw new Error(`'baseUri' must be provided to resolve relative url ${t}`);return s.substr(0,s.lastIndexOf("/")+1)+t}const ko="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",zo="B9h9z9tFBBBF8dL9gBB9gLaaaaaFa9gEaaaB9gGaaB9gFaFaEQSBBFBFFGEGEGIILF9wFFFLEFBFKNFaFCx/aFMO/LFVK9tv9t9vq95GBt9f9f939h9z9t9f9j9h9s9s9f9jW9vq9zBBp9tv9z9o9v9wW9f9kv9j9v9kv9WvqWv94h919m9mvqBG8Z9tv9z9o9v9wW9f9kv9j9v9kv9J9u9kv94h919m9mvqBIy9tv9z9o9v9wW9f9kv9j9v9kv9J9u9kv949TvZ91v9u9jvBLn9tv9z9o9v9wW9f9kv9j9v9kv69p9sWvq9P9jWBKi9tv9z9o9v9wW9f9kv9j9v9kv69p9sWvq9R919hWBNn9tv9z9o9v9wW9f9kv9j9v9kv69p9sWvq9F949wBcI9z9iqlBMc/j9JSIBTEM9+FLa8jUUUUBCTlRBCBRFEXCBRGCBREEXABCNJAGJAECUaAFAGrCFZHIy86BBAEAIJREAGCFJHGCN9HQBMAFCx+YUUBJAE86BBAFCEWCxkUUBJAB8pEN83EBAFCFJHFCUG9HQBMMkRIbaG97FaK978jUUUUBCU/KBlHL8kUUUUBC9+RKGXAGCFJAI9LQBCaRKAE2BBC+gF9HQBALAEAIJHOAGlAG/8cBBCUoBAG9uC/wgBZHKCUGAKCUG9JyRNAECFJRKCBRVGXEXAVAF9PQFANAFAVlAVANJAF9JyRcGXGXAG9FQBAcCbJHIC9wZHMCE9sRSAMCFWRQAICIrCEJCGrRfCBRbEXAKRTCBRtGXEXGXAOATlAf9PQBCBRKSLMALCU/CBJAtAM9sJRmATAfJRKCBREGXAMCoB9JQBAOAKlC/gB9JQBCBRIEXAmAIJREGXGXGXGXGXATAICKrJ2BBHYCEZfIBFGEBMAECBDtDMIBSEMAEAKDBBIAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnHPCGD+MFAPDQBTFtGmEYIPLdKeOnC0+G+MiDtD9OHdCEDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBAeCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMIBAKCIJAnDeBJAeCx+YUUBJ2BBJRKSGMAEAKDBBNAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnC+P+e+8/4BDtD9OHdCbDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBAeCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMIBAKCNJAnDeBJAeCx+YUUBJ2BBJRKSFMAEAKDBBBDMIBAKCTJRKMGXGXGXGXGXAYCGrCEZfIBFGEBMAECBDtDMITSEMAEAKDBBIAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnHPCGD+MFAPDQBTFtGmEYIPLdKeOnC0+G+MiDtD9OHdCEDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBAeCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMITAKCIJAnDeBJAeCx+YUUBJ2BBJRKSGMAEAKDBBNAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnC+P+e+8/4BDtD9OHdCbDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBAeCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMITAKCNJAnDeBJAeCx+YUUBJ2BBJRKSFMAEAKDBBBDMITAKCTJRKMGXGXGXGXGXAYCIrCEZfIBFGEBMAECBDtDMIASEMAEAKDBBIAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnHPCGD+MFAPDQBTFtGmEYIPLdKeOnC0+G+MiDtD9OHdCEDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBAeCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMIAAKCIJAnDeBJAeCx+YUUBJ2BBJRKSGMAEAKDBBNAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnC+P+e+8/4BDtD9OHdCbDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBAeCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMIAAKCNJAnDeBJAeCx+YUUBJ2BBJRKSFMAEAKDBBBDMIAAKCTJRKMGXGXGXGXGXAYCKrfIBFGEBMAECBDtDMI8wSEMAEAKDBBIAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnHPCGD+MFAPDQBTFtGmEYIPLdKeOnC0+G+MiDtD9OHdCEDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HYCEWCxkUUBJDBEBAYCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HYCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMI8wAKCIJAnDeBJAYCx+YUUBJ2BBJRKSGMAEAKDBBNAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnC+P+e+8/4BDtD9OHdCbDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HYCEWCxkUUBJDBEBAYCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HYCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMI8wAKCNJAnDeBJAYCx+YUUBJ2BBJRKSFMAEAKDBBBDMI8wAKCTJRKMAICoBJREAICUFJAM9LQFAERIAOAKlC/fB9LQBMMGXAEAM9PQBAECErRIEXGXAOAKlCi9PQBCBRKSOMAmAEJRYGXGXGXGXGXATAECKrJ2BBAICKZrCEZfIBFGEBMAYCBDtDMIBSEMAYAKDBBIAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnHPCGD+MFAPDQBTFtGmEYIPLdKeOnC0+G+MiDtD9OHdCEDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBAeCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMIBAKCIJAnDeBJAeCx+YUUBJ2BBJRKSGMAYAKDBBNAKDBBBHPCID+MFAPDQBTFtGmEYIPLdKeOnC+P+e+8/4BDtD9OHdCbDbD8jHPD8dBhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBAeCx+YUUBJDBBBHnAnDQBBBBBBBBBBBBBBBBAPD8dFhUg/8/4/w/goB9+h84k7HeCEWCxkUUBJDBEBD9uDQBFGEILKOTtmYPdenDfAdAPD9SDMIBAKCNJAnDeBJAeCx+YUUBJ2BBJRKSFMAYAKDBBBDMIBAKCTJRKMAICGJRIAECTJHEAM9JQBMMGXAK9FQBAKRTAtCFJHtCI6QGSFMMCBRKSEMGXAM9FQBALCUGJAbJREALAbJDBGBRnCBRYEXAEALCU/CBJAYJHIDBIBHdCFD9tAdCFDbHPD9OD9hD9RHdAIAMJDBIBHiCFD9tAiAPD9OD9hD9RHiDQBTFtGmEYIPLdKeOnH8ZAIAQJDBIBHpCFD9tApAPD9OD9hD9RHpAIASJDBIBHyCFD9tAyAPD9OD9hD9RHyDQBTFtGmEYIPLdKeOnH8cDQBFTtGEmYILPdKOenHPAPDQBFGEBFGEBFGEBFGEAnD9uHnDyBjGBAEAGJHIAnAPAPDQILKOILKOILKOILKOD9uHnDyBjGBAIAGJHIAnAPAPDQNVcMNVcMNVcMNVcMD9uHnDyBjGBAIAGJHIAnAPAPDQSQfbSQfbSQfbSQfbD9uHnDyBjGBAIAGJHIAnA8ZA8cDQNVi8ZcMpySQ8c8dfb8e8fHPAPDQBFGEBFGEBFGEBFGED9uHnDyBjGBAIAGJHIAnAPAPDQILKOILKOILKOILKOD9uHnDyBjGBAIAGJHIAnAPAPDQNVcMNVcMNVcMNVcMD9uHnDyBjGBAIAGJHIAnAPAPDQSQfbSQfbSQfbSQfbD9uHnDyBjGBAIAGJHIAnAdAiDQNiV8ZcpMyS8cQ8df8eb8fHdApAyDQNiV8ZcpMyS8cQ8df8eb8fHiDQBFTtGEmYILPdKOenHPAPDQBFGEBFGEBFGEBFGED9uHnDyBjGBAIAGJHIAnAPAPDQILKOILKOILKOILKOD9uHnDyBjGBAIAGJHIAnAPAPDQNVcMNVcMNVcMNVcMD9uHnDyBjGBAIAGJHIAnAPAPDQSQfbSQfbSQfbSQfbD9uHnDyBjGBAIAGJHIAnAdAiDQNVi8ZcMpySQ8c8dfb8e8fHPAPDQBFGEBFGEBFGEBFGED9uHnDyBjGBAIAGJHIAnAPAPDQILKOILKOILKOILKOD9uHnDyBjGBAIAGJHIAnAPAPDQNVcMNVcMNVcMNVcMD9uHnDyBjGBAIAGJHIAnAPAPDQSQfbSQfbSQfbSQfbD9uHnDyBjGBAIAGJREAYCTJHYAM9JQBMMAbCIJHbAG9JQBMMABAVAG9sJALCUGJAcAG9s/8cBBALALCUGJAcCaJAG9sJAG/8cBBMAcCBAKyAVJRVAKQBMC9+RKSFMCBC99AOAKlAGCAAGCA9Ly6yRKMALCU/KBJ8kUUUUBAKMNBT+BUUUBM+KmFTa8jUUUUBCoFlHL8kUUUUBC9+RKGXAFCE9uHOCtJAI9LQBCaRKAE2BBHNC/wFZC/gF9HQBANCbZHVCF9LQBALCoBJCgFCUF/8MBALC84Jha83EBALC8wJha83EBALC8oJha83EBALCAJha83EBALCiJha83EBALCTJha83EBALha83ENALha83EBAEAIJC9wJRcAECFJHNAOJRMGXAF9FQBCQCbAVCF6yRSABRECBRVCBRQCBRfCBRICBRKEXGXAMAcuQBC9+RKSEMGXGXAN2BBHOC/vF9LQBALCoBJAOCIrCa9zAKJCbZCEWJHb8oGIRTAb8oGBRtGXAOCbZHbAS9PQBALAOCa9zAIJCbZCGWJ8oGBAVAbyROAb9FRbGXGXAGCG9HQBABAt87FBABCIJAO87FBABCGJAT87FBSFMAEAtjGBAECNJAOjGBAECIJATjGBMAVAbJRVALCoBJAKCEWJHmAOjGBAmATjGIALAICGWJAOjGBALCoBJAKCFJCbZHKCEWJHTAtjGBATAOjGIAIAbJRIAKCFJRKSGMGXGXAbCb6QBAQAbJAbC989zJCFJRQSFMAM1BBHbCgFZROGXGXAbCa9MQBAMCFJRMSFMAM1BFHbCgBZCOWAOCgBZqROGXAbCa9MQBAMCGJRMSFMAM1BGHbCgBZCfWAOqROGXAbCa9MQBAMCEJRMSFMAM1BEHbCgBZCdWAOqROGXAbCa9MQBAMCIJRMSFMAM2BIC8cWAOqROAMCLJRMMAOCFrCBAOCFZl9zAQJRQMGXGXAGCG9HQBABAt87FBABCIJAQ87FBABCGJAT87FBSFMAEAtjGBAECNJAQjGBAECIJATjGBMALCoBJAKCEWJHOAQjGBAOATjGIALAICGWJAQjGBALCoBJAKCFJCbZHKCEWJHOAtjGBAOAQjGIAICFJRIAKCFJRKSFMGXAOCDF9LQBALAIAcAOCbZJ2BBHbCIrHTlCbZCGWJ8oGBAVCFJHtATyROALAIAblCbZCGWJ8oGBAtAT9FHmJHtAbCbZHTyRbAT9FRTGXGXAGCG9HQBABAV87FBABCIJAb87FBABCGJAO87FBSFMAEAVjGBAECNJAbjGBAECIJAOjGBMALAICGWJAVjGBALCoBJAKCEWJHYAOjGBAYAVjGIALAICFJHICbZCGWJAOjGBALCoBJAKCFJCbZCEWJHYAbjGBAYAOjGIALAIAmJCbZHICGWJAbjGBALCoBJAKCGJCbZHKCEWJHOAVjGBAOAbjGIAKCFJRKAIATJRIAtATJRVSFMAVCBAM2BBHYyHTAOC/+F6HPJROAYCbZRtGXGXAYCIrHmQBAOCFJRbSFMAORbALAIAmlCbZCGWJ8oGBROMGXGXAtQBAbCFJRVSFMAbRVALAIAYlCbZCGWJ8oGBRbMGXGXAP9FQBAMCFJRYSFMAM1BFHYCgFZRTGXGXAYCa9MQBAMCGJRYSFMAM1BGHYCgBZCOWATCgBZqRTGXAYCa9MQBAMCEJRYSFMAM1BEHYCgBZCfWATqRTGXAYCa9MQBAMCIJRYSFMAM1BIHYCgBZCdWATqRTGXAYCa9MQBAMCLJRYSFMAMCKJRYAM2BLC8cWATqRTMATCFrCBATCFZl9zAQJHQRTMGXGXAmCb6QBAYRPSFMAY1BBHMCgFZROGXGXAMCa9MQBAYCFJRPSFMAY1BFHMCgBZCOWAOCgBZqROGXAMCa9MQBAYCGJRPSFMAY1BGHMCgBZCfWAOqROGXAMCa9MQBAYCEJRPSFMAY1BEHMCgBZCdWAOqROGXAMCa9MQBAYCIJRPSFMAYCLJRPAY2BIC8cWAOqROMAOCFrCBAOCFZl9zAQJHQROMGXGXAtCb6QBAPRMSFMAP1BBHMCgFZRbGXGXAMCa9MQBAPCFJRMSFMAP1BFHMCgBZCOWAbCgBZqRbGXAMCa9MQBAPCGJRMSFMAP1BGHMCgBZCfWAbqRbGXAMCa9MQBAPCEJRMSFMAP1BEHMCgBZCdWAbqRbGXAMCa9MQBAPCIJRMSFMAPCLJRMAP2BIC8cWAbqRbMAbCFrCBAbCFZl9zAQJHQRbMGXGXAGCG9HQBABAT87FBABCIJAb87FBABCGJAO87FBSFMAEATjGBAECNJAbjGBAECIJAOjGBMALCoBJAKCEWJHYAOjGBAYATjGIALAICGWJATjGBALCoBJAKCFJCbZCEWJHYAbjGBAYAOjGIALAICFJHICbZCGWJAOjGBALCoBJAKCGJCbZCEWJHOATjGBAOAbjGIALAIAm9FAmCb6qJHICbZCGWJAbjGBAIAt9FAtCb6qJRIAKCEJRKMANCFJRNABCKJRBAECSJREAKCbZRKAICbZRIAfCEJHfAF9JQBMMCBC99AMAc6yRKMALCoFJ8kUUUUBAKM/tIFGa8jUUUUBCTlRLC9+RKGXAFCLJAI9LQBCaRKAE2BBC/+FZC/QF9HQBALhB83ENAECFJRKAEAIJC98JREGXAF9FQBGXAGCG6QBEXGXAKAE9JQBC9+bMAK1BBHGCgFZRIGXGXAGCa9MQBAKCFJRKSFMAK1BFHGCgBZCOWAICgBZqRIGXAGCa9MQBAKCGJRKSFMAK1BGHGCgBZCfWAIqRIGXAGCa9MQBAKCEJRKSFMAK1BEHGCgBZCdWAIqRIGXAGCa9MQBAKCIJRKSFMAK2BIC8cWAIqRIAKCLJRKMALCNJAICFZCGWqHGAICGrCBAICFrCFZl9zAG8oGBJHIjGBABAIjGBABCIJRBAFCaJHFQBSGMMEXGXAKAE9JQBC9+bMAK1BBHGCgFZRIGXGXAGCa9MQBAKCFJRKSFMAK1BFHGCgBZCOWAICgBZqRIGXAGCa9MQBAKCGJRKSFMAK1BGHGCgBZCfWAIqRIGXAGCa9MQBAKCEJRKSFMAK1BEHGCgBZCdWAIqRIGXAGCa9MQBAKCIJRKSFMAK2BIC8cWAIqRIAKCLJRKMABAICGrCBAICFrCFZl9zALCNJAICFZCGWqHI8oGBJHG87FBAIAGjGBABCGJRBAFCaJHFQBMMCBC99AKAE6yRKMAKM/xLGEaK978jUUUUBCAlHE8kUUUUBGXGXAGCI9HQBGXAFC98ZHI9FQBABRGCBRLEXAGAGDBBBHKCiD+rFCiD+sFD/6FHOAKCND+rFCiD+sFD/6FAOD/gFAKCTD+rFCiD+sFD/6FHND/gFD/kFD/lFHVCBDtD+2FHcAOCUUUU94DtHMD9OD9RD/kFHO9DBB/+hDYAOAOD/mFAVAVD/mFANAcANAMD9OD9RD/kFHOAOD/mFD/kFD/kFD/jFD/nFHND/mF9DBBX9LDYHcD/kFCgFDtD9OAKCUUU94DtD9OD9QAOAND/mFAcD/kFCND+rFCU/+EDtD9OD9QAVAND/mFAcD/kFCTD+rFCUU/8ODtD9OD9QDMBBAGCTJRGALCIJHLAI9JQBMMAIAF9PQFAEAFCEZHLCGWHGqCBCTAGl/8MBAEABAICGWJHIAG/8cBBGXAL9FQBAEAEDBIBHKCiD+rFCiD+sFD/6FHOAKCND+rFCiD+sFD/6FAOD/gFAKCTD+rFCiD+sFD/6FHND/gFD/kFD/lFHVCBDtD+2FHcAOCUUUU94DtHMD9OD9RD/kFHO9DBB/+hDYAOAOD/mFAVAVD/mFANAcANAMD9OD9RD/kFHOAOD/mFD/kFD/kFD/jFD/nFHND/mF9DBBX9LDYHcD/kFCgFDtD9OAKCUUU94DtD9OD9QAOAND/mFAcD/kFCND+rFCU/+EDtD9OD9QAVAND/mFAcD/kFCTD+rFCUU/8ODtD9OD9QDMIBMAIAEAG/8cBBSFMABAFC98ZHGT+HUUUBAGAF9PQBAEAFCEZHICEWHLJCBCAALl/8MBAEABAGCEWJHGAL/8cBBAEAIT+HUUUBAGAEAL/8cBBMAECAJ8kUUUUBM+yEGGaO97GXAF9FQBCBRGEXABCTJHEAEDBBBHICBDtHLCUU98D8cFCUU98D8cEHKD9OABDBBBHOAIDQILKOSQfbPden8c8d8e8fCggFDtD9OD/6FAOAIDQBFGENVcMTtmYi8ZpyHICTD+sFD/6FHND/gFAICTD+rFCTD+sFD/6FHVD/gFD/kFD/lFHI9DB/+g6DYAVAIALD+2FHLAVCUUUU94DtHcD9OD9RD/kFHVAVD/mFAIAID/mFANALANAcD9OD9RD/kFHIAID/mFD/kFD/kFD/jFD/nFHND/mF9DBBX9LDYHLD/kFCTD+rFAVAND/mFALD/kFCggEDtD9OD9QHVAIAND/mFALD/kFCaDbCBDnGCBDnECBDnKCBDnOCBDncCBDnMCBDnfCBDnbD9OHIDQNVi8ZcMpySQ8c8dfb8e8fD9QDMBBABAOAKD9OAVAIDQBFTtGEmYILPdKOenD9QDMBBABCAJRBAGCIJHGAF9JQBMMM94FEa8jUUUUBCAlHE8kUUUUBABAFC98ZHIT+JUUUBGXAIAF9PQBAEAFCEZHLCEWHFJCBCAAFl/8MBAEABAICEWJHBAF/8cBBAEALT+JUUUBABAEAF/8cBBMAECAJ8kUUUUBM/hEIGaF97FaL978jUUUUBCTlRGGXAF9FQBCBREEXAGABDBBBHIABCTJHLDBBBHKDQILKOSQfbPden8c8d8e8fHOCTD+sFHNCID+rFDMIBAB9DBBU8/DY9D/zI818/DYANCEDtD9QD/6FD/nFHNAIAKDQBFGENVcMTtmYi8ZpyHICTD+rFCTD+sFD/6FD/mFHKAKD/mFANAICTD+sFD/6FD/mFHVAVD/mFANAOCTD+rFCTD+sFD/6FD/mFHOAOD/mFD/kFD/kFD/lFCBDtD+4FD/jF9DB/+g6DYHND/mF9DBBX9LDYHID/kFCggEDtHcD9OAVAND/mFAID/kFCTD+rFD9QHVAOAND/mFAID/kFCTD+rFAKAND/mFAID/kFAcD9OD9QHNDQBFTtGEmYILPdKOenHID8dBAGDBIBDyB+t+J83EBABCNJAID8dFAGDBIBDyF+t+J83EBALAVANDQNVi8ZcMpySQ8c8dfb8e8fHND8dBAGDBIBDyG+t+J83EBABCiJAND8dFAGDBIBDyE+t+J83EBABCAJRBAECIJHEAF9JQBMMM/3FGEaF978jUUUUBCoBlREGXAGCGrAF9sHIC98ZHL9FQBCBRGABRFEXAFAFDBBBHKCND+rFCND+sFD/6FAKCiD+sFCnD+rFCUUU/8EDtD+uFD/mFDMBBAFCTJRFAGCIJHGAL9JQBMMGXALAI9PQBAEAICEZHGCGWHFqCBCoBAFl/8MBAEABALCGWJHLAF/8cBBGXAG9FQBAEAEDBIBHKCND+rFCND+sFD/6FAKCiD+sFCnD+rFCUUU/8EDtD+uFD/mFDMIBMALAEAF/8cBBMM9TFEaCBCB8oGUkUUBHFABCEJC98ZJHBjGUkUUBGXGXAB8/BCTWHGuQBCaREABAGlCggEJCTrXBCa6QFMAFREMAEMMMFBCUNMIT9tBB",Wo=new Uint8Array([0,97,115,109,1,0,0,0,1,4,1,96,0,0,3,3,2,0,0,5,3,1,0,1,12,1,0,10,22,2,12,0,65,0,65,0,65,0,252,10,0,0,11,7,0,65,0,253,15,26,11]),Zo=new Uint8Array([32,0,65,253,3,1,2,34,4,106,6,5,11,8,7,20,13,33,12,16,128,9,116,64,19,113,127,15,10,21,22,14,255,66,24,54,136,107,18,23,192,26,114,118,132,17,77,101,130,144,27,87,131,44,45,74,156,154,70,167]),qo={0:"",1:"meshopt_decodeFilterOct",2:"meshopt_decodeFilterQuat",3:"meshopt_decodeFilterExp",NONE:"",OCTAHEDRAL:"meshopt_decodeFilterOct",QUATERNION:"meshopt_decodeFilterQuat",EXPONENTIAL:"meshopt_decodeFilterExp"},$o={0:"meshopt_decodeVertexBuffer",1:"meshopt_decodeIndexBuffer",2:"meshopt_decodeIndexSequence",ATTRIBUTES:"meshopt_decodeVertexBuffer",TRIANGLES:"meshopt_decodeIndexBuffer",INDICES:"meshopt_decodeIndexSequence"};async function ei(t,e,n,s,r,o="NONE"){const i=await ti();ri(i,i.exports[$o[r]],t,e,n,s,i.exports[qo[o||"NONE"]])}let Ie;async function ti(){return Ie||(Ie=ni()),Ie}async function ni(){let t=ko;WebAssembly.validate(Wo)&&(t=zo,console.log("Warning: meshopt_decoder is using experimental SIMD support"));const e=await WebAssembly.instantiate(si(t),{});return await e.instance.exports.__wasm_call_ctors(),e.instance}function si(t){const e=new Uint8Array(t.length);for(let s=0;s<t.length;++s){const r=t.charCodeAt(s);e[s]=r>96?r-71:r>64?r-65:r>47?r+4:r>46?63:62}let n=0;for(let s=0;s<t.length;++s)e[n++]=e[s]<60?Zo[e[s]]:(e[s]-60)*64+e[++s];return e.buffer.slice(0,n)}function ri(t,e,n,s,r,o,i){const a=t.exports.sbrk,c=s+3&-4,l=a(c*r),f=a(o.length),u=new Uint8Array(t.exports.memory.buffer);u.set(o,f);const A=e(l,s,r,f,o.length);if(A===0&&i&&i(l,c,r),n.set(u.subarray(l,l+s*r)),a(l-a(0)),A!==0)throw new Error(`Malformed buffer data: ${A}`)}const ae="EXT_meshopt_compression",oi=ae;async function ii(t,e){const n=new b(t);if(!e?.gltf?.decompressMeshes||!e.gltf?.loadBuffers)return;const s=[];for(const r of t.json.bufferViews||[])s.push(ai(n,r));await Promise.all(s),n.removeExtension(ae)}async function ai(t,e){const n=t.getObjectExtension(e,ae);if(n){const{byteOffset:s=0,byteLength:r=0,byteStride:o,count:i,mode:a,filter:c="NONE",buffer:l}=n,f=t.gltf.buffers[l],u=new Uint8Array(f.arrayBuffer,f.byteOffset+s,r),A=new Uint8Array(t.gltf.buffers[e.buffer].arrayBuffer,e.byteOffset,e.byteLength);await ei(A,i,o,u,a,c),t.removeObjectExtension(e,ae)}}const ci=Object.freeze(Object.defineProperty({__proto__:null,decode:ii,name:oi},Symbol.toStringTag,{value:"Module"})),S="EXT_texture_webp",li=S;function fi(t,e){const n=new b(t);if(!Xn("image/webp")){if(n.getRequiredExtensions().includes(S))throw new Error(`gltf: Required extension ${S} not supported by browser`);return}const{json:s}=n;for(const r of s.textures||[]){const o=n.getObjectExtension(r,S);o&&(r.source=o.source),n.removeObjectExtension(r,S)}n.removeExtension(S)}const ui=Object.freeze(Object.defineProperty({__proto__:null,name:li,preprocess:fi},Symbol.toStringTag,{value:"Module"})),ne="KHR_texture_basisu",Ai=ne;function di(t,e){const n=new b(t),{json:s}=n;for(const r of s.textures||[]){const o=n.getObjectExtension(r,ne);o&&(r.source=o.source,n.removeObjectExtension(r,ne))}n.removeExtension(ne)}const Bi=Object.freeze(Object.defineProperty({__proto__:null,name:Ai,preprocess:di},Symbol.toStringTag,{value:"Module"})),mi="4.3.3",hi={dataType:null,batchType:null,name:"Draco",id:"draco",module:"draco",version:mi,worker:!0,extensions:["drc"],mimeTypes:["application/octet-stream"],binary:!0,tests:["DRACO"],options:{draco:{decoderType:typeof WebAssembly=="object"?"wasm":"js",libraryPath:"libs/",extraAttributes:{},attributeNameEntry:void 0}}};function pi(t,e,n){const s=Vt(e.metadata),r=[],o=Ci(e.attributes);for(const i in t){const a=t[i],c=ft(i,a,o[i]);r.push(c)}if(n){const i=ft("indices",n);r.push(i)}return{fields:r,metadata:s}}function Ci(t){const e={};for(const n in t){const s=t[n];e[s.name||"undefined"]=s}return e}function ft(t,e,n){const s=n?Vt(n.metadata):void 0;return jn(t,e,s)}function Vt(t){Object.entries(t);const e={};for(const n in t)e[`${n}.string`]=JSON.stringify(t[n]);return e}const ut={POSITION:"POSITION",NORMAL:"NORMAL",COLOR:"COLOR_0",TEX_COORD:"TEXCOORD_0"},bi={1:Int8Array,2:Uint8Array,3:Int16Array,4:Uint16Array,5:Int32Array,6:Uint32Array,9:Float32Array},gi=4;class Ei{draco;decoder;metadataQuerier;constructor(e){this.draco=e,this.decoder=new this.draco.Decoder,this.metadataQuerier=new this.draco.MetadataQuerier}destroy(){this.draco.destroy(this.decoder),this.draco.destroy(this.metadataQuerier)}parseSync(e,n={}){const s=new this.draco.DecoderBuffer;s.Init(new Int8Array(e),e.byteLength),this._disableAttributeTransforms(n);const r=this.decoder.GetEncodedGeometryType(s),o=r===this.draco.TRIANGULAR_MESH?new this.draco.Mesh:new this.draco.PointCloud;try{let i;switch(r){case this.draco.TRIANGULAR_MESH:i=this.decoder.DecodeBufferToMesh(s,o);break;case this.draco.POINT_CLOUD:i=this.decoder.DecodeBufferToPointCloud(s,o);break;default:throw new Error("DRACO: Unknown geometry type.")}if(!i.ok()||!o.ptr){const A=`DRACO decompression failed: ${i.error_msg()}`;throw new Error(A)}const a=this._getDracoLoaderData(o,r,n),c=this._getMeshData(o,a,n),l=It(c.attributes),f=pi(c.attributes,a,c.indices);return{loader:"draco",loaderData:a,header:{vertexCount:o.num_points(),boundingBox:l},...c,schema:f}}finally{this.draco.destroy(s),o&&this.draco.destroy(o)}}_getDracoLoaderData(e,n,s){const r=this._getTopLevelMetadata(e),o=this._getDracoAttributes(e,s);return{geometry_type:n,num_attributes:e.num_attributes(),num_points:e.num_points(),num_faces:e instanceof this.draco.Mesh?e.num_faces():0,metadata:r,attributes:o}}_getDracoAttributes(e,n){const s={};for(let r=0;r<e.num_attributes();r++){const o=this.decoder.GetAttribute(e,r),i=this._getAttributeMetadata(e,r);s[o.unique_id()]={unique_id:o.unique_id(),attribute_type:o.attribute_type(),data_type:o.data_type(),num_components:o.num_components(),byte_offset:o.byte_offset(),byte_stride:o.byte_stride(),normalized:o.normalized(),attribute_index:r,metadata:i};const a=this._getQuantizationTransform(o,n);a&&(s[o.unique_id()].quantization_transform=a);const c=this._getOctahedronTransform(o,n);c&&(s[o.unique_id()].octahedron_transform=c)}return s}_getMeshData(e,n,s){const r=this._getMeshAttributes(n,e,s);if(!r.POSITION)throw new Error("DRACO: No position attribute found.");return e instanceof this.draco.Mesh?s.topology==="triangle-strip"?{topology:"triangle-strip",mode:4,attributes:r,indices:{value:this._getTriangleStripIndices(e),size:1}}:{topology:"triangle-list",mode:5,attributes:r,indices:{value:this._getTriangleListIndices(e),size:1}}:{topology:"point-list",mode:0,attributes:r}}_getMeshAttributes(e,n,s){const r={};for(const o of Object.values(e.attributes)){const i=this._deduceAttributeName(o,s);o.name=i;const a=this._getAttributeValues(n,o);if(a){const{value:c,size:l}=a;r[i]={value:c,size:l,byteOffset:o.byte_offset,byteStride:o.byte_stride,normalized:o.normalized}}}return r}_getTriangleListIndices(e){const s=e.num_faces()*3,r=s*gi,o=this.draco._malloc(r);try{return this.decoder.GetTrianglesUInt32Array(e,r,o),new Uint32Array(this.draco.HEAPF32.buffer,o,s).slice()}finally{this.draco._free(o)}}_getTriangleStripIndices(e){const n=new this.draco.DracoInt32Array;try{return this.decoder.GetTriangleStripsFromMesh(e,n),Ti(n)}finally{this.draco.destroy(n)}}_getAttributeValues(e,n){const s=bi[n.data_type];if(!s)return console.warn(`DRACO: Unsupported attribute type ${n.data_type}`),null;const r=n.num_components,i=e.num_points()*r,a=i*s.BYTES_PER_ELEMENT,c=Ii(this.draco,s);let l;const f=this.draco._malloc(a);try{const u=this.decoder.GetAttribute(e,n.attribute_index);this.decoder.GetAttributeDataArrayForAllPoints(e,u,c,a,f),l=new s(this.draco.HEAPF32.buffer,f,i).slice()}finally{this.draco._free(f)}return{value:l,size:r}}_deduceAttributeName(e,n){const s=e.unique_id;for(const[i,a]of Object.entries(n.extraAttributes||{}))if(a===s)return i;const r=e.attribute_type;for(const i in ut)if(this.draco[i]===r)return ut[i];const o=n.attributeNameEntry||"name";return e.metadata[o]?e.metadata[o].string:`CUSTOM_ATTRIBUTE_${s}`}_getTopLevelMetadata(e){const n=this.decoder.GetMetadata(e);return this._getDracoMetadata(n)}_getAttributeMetadata(e,n){const s=this.decoder.GetAttributeMetadata(e,n);return this._getDracoMetadata(s)}_getDracoMetadata(e){if(!e||!e.ptr)return{};const n={},s=this.metadataQuerier.NumEntries(e);for(let r=0;r<s;r++){const o=this.metadataQuerier.GetEntryName(e,r);n[o]=this._getDracoMetadataField(e,o)}return n}_getDracoMetadataField(e,n){const s=new this.draco.DracoInt32Array;try{this.metadataQuerier.GetIntEntryArray(e,n,s);const r=Mi(s);return{int:this.metadataQuerier.GetIntEntry(e,n),string:this.metadataQuerier.GetStringEntry(e,n),double:this.metadataQuerier.GetDoubleEntry(e,n),intArray:r}}finally{this.draco.destroy(s)}}_disableAttributeTransforms(e){const{quantizedAttributes:n=[],octahedronAttributes:s=[]}=e,r=[...n,...s];for(const o of r)this.decoder.SkipAttributeTransform(this.draco[o])}_getQuantizationTransform(e,n){const{quantizedAttributes:s=[]}=n,r=e.attribute_type();if(s.map(i=>this.decoder[i]).includes(r)){const i=new this.draco.AttributeQuantizationTransform;try{if(i.InitFromAttribute(e))return{quantization_bits:i.quantization_bits(),range:i.range(),min_values:new Float32Array([1,2,3]).map(a=>i.min_value(a))}}finally{this.draco.destroy(i)}}return null}_getOctahedronTransform(e,n){const{octahedronAttributes:s=[]}=n,r=e.attribute_type();if(s.map(i=>this.decoder[i]).includes(r)){const i=new this.draco.AttributeQuantizationTransform;try{if(i.InitFromAttribute(e))return{quantization_bits:i.quantization_bits()}}finally{this.draco.destroy(i)}}return null}}function Ii(t,e){switch(e){case Float32Array:return t.DT_FLOAT32;case Int8Array:return t.DT_INT8;case Int16Array:return t.DT_INT16;case Int32Array:return t.DT_INT32;case Uint8Array:return t.DT_UINT8;case Uint16Array:return t.DT_UINT16;case Uint32Array:return t.DT_UINT32;default:return t.DT_INVALID}}function Mi(t){const e=t.size(),n=new Int32Array(e);for(let s=0;s<e;s++)n[s]=t.GetValue(s);return n}function Ti(t){const e=t.size(),n=new Int32Array(e);for(let s=0;s<e;s++)n[s]=t.GetValue(s);return n}const yi="1.5.6",Fi="1.4.1",Me=`https://www.gstatic.com/draco/versioned/decoders/${yi}`,E={DECODER:"draco_wasm_wrapper.js",DECODER_WASM:"draco_decoder.wasm",FALLBACK_DECODER:"draco_decoder.js",ENCODER:"draco_encoder.js"},Te={[E.DECODER]:`${Me}/${E.DECODER}`,[E.DECODER_WASM]:`${Me}/${E.DECODER_WASM}`,[E.FALLBACK_DECODER]:`${Me}/${E.FALLBACK_DECODER}`,[E.ENCODER]:`https://raw.githubusercontent.com/google/draco/${Fi}/javascript/${E.ENCODER}`};let ye;async function _i(t){const e=t.modules||{};return e.draco3d?ye||=e.draco3d.createDecoderModule({}).then(n=>({draco:n})):ye||=Ri(t),await ye}async function Ri(t){let e,n;return(t.draco&&t.draco.decoderType)==="js"?e=await v(Te[E.FALLBACK_DECODER],"draco",t,E.FALLBACK_DECODER):[e,n]=await Promise.all([await v(Te[E.DECODER],"draco",t,E.DECODER),await v(Te[E.DECODER_WASM],"draco",t,E.DECODER_WASM)]),e=e||globalThis.DracoDecoderModule,await Gi(e,n)}function Gi(t,e){const n={};return e&&(n.wasmBinary=e),new Promise(s=>{t({...n,onModuleLoaded:r=>s({draco:r})})})}const vi={...hi,parse:Di};async function Di(t,e){const{draco:n}=await _i(e),s=new Ei(n);try{return s.parseSync(t,e?.draco)}finally{s.destroy()}}function Si(t){const e={};for(const n in t){const s=t[n];if(n!=="indices"){const r=Xt(s);e[n]=r}}return e}function Xt(t){const{buffer:e,size:n,count:s}=Oi(t);return{value:e,size:n,byteOffset:0,count:s,type:Lt(n),componentType:ce(e)}}function Oi(t){let e=t,n=1,s=0;return t&&t.value&&(e=t.value,n=t.size||1),e&&(ArrayBuffer.isView(e)||(e=xi(e,Float32Array)),s=e.length/n),{buffer:e,size:n,count:s}}function xi(t,e,n=!1){return t?Array.isArray(t)?new e(t):n&&!(t instanceof e)?new e(t):t:null}const F="KHR_draco_mesh_compression",Li=F;function Hi(t,e,n){const s=new b(t);for(const r of Qt(s))s.getObjectExtension(r,F)}async function Pi(t,e,n){if(!e?.gltf?.decompressMeshes)return;const s=new b(t),r=[];for(const o of Qt(s))s.getObjectExtension(o,F)&&r.push(Ni(s,o,e,n));await Promise.all(r),s.removeExtension(F)}function Ui(t,e={}){const n=new b(t);for(const s of n.json.meshes||[])Ji(s),n.addRequiredExtension(F)}async function Ni(t,e,n,s){const r=t.getObjectExtension(e,F);if(!r)return;const o=t.getTypedArrayForBufferView(r.bufferView),i=gt(o.buffer,o.byteOffset),a={...n};delete a["3d-tiles"];const c=await Et(i,vi,a,s),l=Si(c.attributes);for(const[f,u]of Object.entries(l))if(f in e.attributes){const A=e.attributes[f],d=t.getAccessor(A);d?.min&&d?.max&&(u.min=d.min,u.max=d.max)}e.attributes=l,c.indices&&(e.indices=Xt(c.indices)),t.removeObjectExtension(e,F),wi(e)}function Ji(t,e,n=4,s,r){if(!s.DracoWriter)throw new Error("options.gltf.DracoWriter not provided");const o=s.DracoWriter.encodeSync({attributes:t}),i=r?.parseSync?.({attributes:t}),a=s._addFauxAttributes(i.attributes),c=s.addBufferView(o);return{primitives:[{attributes:a,mode:n,extensions:{[F]:{bufferView:c,attributes:a}}}]}}function wi(t){if(!t.attributes&&Object.keys(t.attributes).length>0)throw new Error("glTF: Empty primitive detected: Draco decompression failure?")}function*Qt(t){for(const e of t.json.meshes||[])for(const n of e.primitives)yield n}const Ki=Object.freeze(Object.defineProperty({__proto__:null,decode:Pi,encode:Ui,name:Li,preprocess:Hi},Symbol.toStringTag,{value:"Module"})),ue="KHR_texture_transform",ji=ue,q=new G,Vi=new Q,Xi=new Q;async function Qi(t,e){if(!new b(t).hasExtension(ue)||!e.gltf?.loadBuffers)return;const r=t.json.materials||[];for(let o=0;o<r.length;o++)Yi(o,t)}function Yi(t,e){const n=e.json.materials?.[t],s=[n?.pbrMetallicRoughness?.baseColorTexture,n?.emissiveTexture,n?.normalTexture,n?.occlusionTexture,n?.pbrMetallicRoughness?.metallicRoughnessTexture],r=[];for(const o of s)o&&o?.extensions?.[ue]&&ki(e,t,o,r)}function ki(t,e,n,s){const r=zi(n,s);if(!r)return;const o=t.json.meshes||[];for(const i of o)for(const a of i.primitives){const c=a.material;Number.isFinite(c)&&e===c&&Wi(t,a,r)}}function zi(t,e){const n=t.extensions?.[ue],{texCoord:s=0}=t,{texCoord:r=s}=n;if(!(e.findIndex(([i,a])=>i===s&&a===r)!==-1)){const i=$i(n);return s!==r&&(t.texCoord=r),e.push([s,r]),{originalTexCoord:s,texCoord:r,matrix:i}}return null}function Wi(t,e,n){const{originalTexCoord:s,texCoord:r,matrix:o}=n,i=e.attributes[`TEXCOORD_${s}`];if(Number.isFinite(i)){const a=t.json.accessors?.[i];if(a&&a.bufferView){const c=t.json.bufferViews?.[a.bufferView];if(c){const{arrayBuffer:l,byteOffset:f}=t.buffers[c.buffer],u=(f||0)+(a.byteOffset||0)+(c.byteOffset||0),{ArrayType:A,length:d}=Le(a,c),B=xt[a.componentType],m=Ot[a.type],p=c.byteStride||B*m,C=new Float32Array(d);for(let I=0;I<a.count;I++){const h=new A(l,u+I*p,2);q.set(h[0],h[1],1),q.transformByMatrix3(o),C.set([q[0],q[1]],I*m)}s===r?Zi(a,c,t.buffers,C):qi(r,a,e,t,C)}}}}function Zi(t,e,n,s){t.componentType=5126,n.push({arrayBuffer:s.buffer,byteOffset:0,byteLength:s.buffer.byteLength}),e.buffer=n.length-1,e.byteLength=s.buffer.byteLength,e.byteOffset=0,delete e.byteStride}function qi(t,e,n,s,r){s.buffers.push({arrayBuffer:r.buffer,byteOffset:0,byteLength:r.buffer.byteLength});const o=s.json.bufferViews;if(!o)return;o.push({buffer:s.buffers.length-1,byteLength:r.buffer.byteLength,byteOffset:0});const i=s.json.accessors;i&&(i.push({bufferView:o?.length-1,byteOffset:0,componentType:5126,count:e.count,type:"VEC2"}),n.attributes[`TEXCOORD_${t}`]=i.length-1)}function $i(t){const{offset:e=[0,0],rotation:n=0,scale:s=[1,1]}=t,r=new Q().set(1,0,0,0,1,0,e[0],e[1],1),o=Vi.set(Math.cos(n),Math.sin(n),0,-Math.sin(n),Math.cos(n),0,0,0,1),i=Xi.set(s[0],0,0,0,s[1],0,0,0,1);return r.multiplyRight(o).multiplyRight(i)}const ea=Object.freeze(Object.defineProperty({__proto__:null,decode:Qi,name:ji},Symbol.toStringTag,{value:"Module"})),R="KHR_lights_punctual",ta=R;async function na(t){const e=new b(t),{json:n}=e,s=e.getExtension(R);s&&(e.json.lights=s.lights,e.removeExtension(R));for(const r of n.nodes||[]){const o=e.getObjectExtension(r,R);o&&(r.light=o.light),e.removeObjectExtension(r,R)}}async function sa(t){const e=new b(t),{json:n}=e;if(n.lights){const s=e.addExtension(R);T(!s.lights),s.lights=n.lights,delete n.lights}if(e.json.lights){for(const s of e.json.lights){const r=s.node;e.addObjectExtension(r,R,s)}delete e.json.lights}}const ra=Object.freeze(Object.defineProperty({__proto__:null,decode:na,encode:sa,name:ta},Symbol.toStringTag,{value:"Module"})),j="KHR_materials_unlit",oa=j;async function ia(t){const e=new b(t),{json:n}=e;for(const s of n.materials||[])s.extensions&&s.extensions.KHR_materials_unlit&&(s.unlit=!0),e.removeObjectExtension(s,j);e.removeExtension(j)}function aa(t){const e=new b(t),{json:n}=e;if(e.materials)for(const s of n.materials||[])s.unlit&&(delete s.unlit,e.addObjectExtension(s,j,{}),e.addExtension(j))}const ca=Object.freeze(Object.defineProperty({__proto__:null,decode:ia,encode:aa,name:oa},Symbol.toStringTag,{value:"Module"})),J="KHR_techniques_webgl",la=J;async function fa(t){const e=new b(t),{json:n}=e,s=e.getExtension(J);if(s){const r=Aa(s,e);for(const o of n.materials||[]){const i=e.getObjectExtension(o,J);i&&(o.technique=Object.assign({},i,r[i.technique]),o.technique.values=da(o.technique,e)),e.removeObjectExtension(o,J)}e.removeExtension(J)}}async function ua(t,e){}function Aa(t,e){const{programs:n=[],shaders:s=[],techniques:r=[]}=t,o=new TextDecoder;return s.forEach(i=>{if(Number.isFinite(i.bufferView))i.code=o.decode(e.getTypedArrayForBufferView(i.bufferView));else throw new Error("KHR_techniques_webgl: no shader code")}),n.forEach(i=>{i.fragmentShader=s[i.fragmentShader],i.vertexShader=s[i.vertexShader]}),r.forEach(i=>{i.program=n[i.program]}),r}function da(t,e){const n=Object.assign({},t.values);return Object.keys(t.uniforms||{}).forEach(s=>{t.uniforms[s].value&&!(s in n)&&(n[s]=t.uniforms[s].value)}),Object.keys(n).forEach(s=>{typeof n[s]=="object"&&n[s].index!==void 0&&(n[s].texture=e.getTexture(n[s].index))}),n}const Ba=Object.freeze(Object.defineProperty({__proto__:null,decode:fa,encode:ua,name:la},Symbol.toStringTag,{value:"Module"})),Yt=[Co,Kr,ci,ui,Bi,Ki,ra,ca,Ba,ea,Lo];function ma(t,e={},n){const s=Yt.filter(r=>kt(r.name,e));for(const r of s)r.preprocess?.(t,e,n)}async function ha(t,e={},n){const s=Yt.filter(r=>kt(r.name,e));for(const r of s)await r.decode?.(t,e,n)}function kt(t,e){const n=e?.gltf?.excludeExtensions||{};return!(t in n&&!n[t])}const Fe="KHR_binary_glTF";function pa(t){const e=new b(t),{json:n}=e;for(const s of n.images||[]){const r=e.getObjectExtension(s,Fe);r&&Object.assign(s,r),e.removeObjectExtension(s,Fe)}n.buffers&&n.buffers[0]&&delete n.buffers[0].uri,e.removeExtension(Fe)}const At={accessors:"accessor",animations:"animation",buffers:"buffer",bufferViews:"bufferView",images:"image",materials:"material",meshes:"mesh",nodes:"node",samplers:"sampler",scenes:"scene",skins:"skin",textures:"texture"},Ca={accessor:"accessors",animations:"animation",buffer:"buffers",bufferView:"bufferViews",image:"images",material:"materials",mesh:"meshes",node:"nodes",sampler:"samplers",scene:"scenes",skin:"skins",texture:"textures"};class ba{idToIndexMap={animations:{},accessors:{},buffers:{},bufferViews:{},images:{},materials:{},meshes:{},nodes:{},samplers:{},scenes:{},skins:{},textures:{}};json;normalize(e,n){this.json=e.json;const s=e.json;switch(s.asset&&s.asset.version){case"2.0":return;case void 0:case"1.0":break;default:console.warn(`glTF: Unknown version ${s.asset.version}`);return}if(!n.normalize)throw new Error("glTF v1 is not supported.");console.warn("Converting glTF v1 to glTF v2 format. This is experimental and may fail."),this._addAsset(s),this._convertTopLevelObjectsToArrays(s),pa(e),this._convertObjectIdsToArrayIndices(s),this._updateObjects(s),this._updateMaterial(s)}_addAsset(e){e.asset=e.asset||{},e.asset.version="2.0",e.asset.generator=e.asset.generator||"Normalized to glTF 2.0 by loaders.gl"}_convertTopLevelObjectsToArrays(e){for(const n in At)this._convertTopLevelObjectToArray(e,n)}_convertTopLevelObjectToArray(e,n){const s=e[n];if(!(!s||Array.isArray(s))){e[n]=[];for(const r in s){const o=s[r];o.id=o.id||r;const i=e[n].length;e[n].push(o),this.idToIndexMap[n][r]=i}}}_convertObjectIdsToArrayIndices(e){for(const n in At)this._convertIdsToIndices(e,n);"scene"in e&&(e.scene=this._convertIdToIndex(e.scene,"scene"));for(const n of e.textures)this._convertTextureIds(n);for(const n of e.meshes)this._convertMeshIds(n);for(const n of e.nodes)this._convertNodeIds(n);for(const n of e.scenes)this._convertSceneIds(n)}_convertTextureIds(e){e.source&&(e.source=this._convertIdToIndex(e.source,"image"))}_convertMeshIds(e){for(const n of e.primitives){const{attributes:s,indices:r,material:o}=n;for(const i in s)s[i]=this._convertIdToIndex(s[i],"accessor");r&&(n.indices=this._convertIdToIndex(r,"accessor")),o&&(n.material=this._convertIdToIndex(o,"material"))}}_convertNodeIds(e){e.children&&(e.children=e.children.map(n=>this._convertIdToIndex(n,"node"))),e.meshes&&(e.meshes=e.meshes.map(n=>this._convertIdToIndex(n,"mesh")))}_convertSceneIds(e){e.nodes&&(e.nodes=e.nodes.map(n=>this._convertIdToIndex(n,"node")))}_convertIdsToIndices(e,n){e[n]||(console.warn(`gltf v1: json doesn't contain attribute ${n}`),e[n]=[]);for(const s of e[n])for(const r in s){const o=s[r],i=this._convertIdToIndex(o,r);s[r]=i}}_convertIdToIndex(e,n){const s=Ca[n];if(s in this.idToIndexMap){const r=this.idToIndexMap[s][e];if(!Number.isFinite(r))throw new Error(`gltf v1: failed to resolve ${n} with id ${e}`);return r}return e}_updateObjects(e){for(const n of this.json.buffers)delete n.type}_updateMaterial(e){for(const n of e.materials){n.pbrMetallicRoughness={baseColorFactor:[1,1,1,1],metallicFactor:1,roughnessFactor:1};const s=n.values?.tex||n.values?.texture2d_0||n.values?.diffuseTex,r=e.textures.findIndex(o=>o.id===s);r!==-1&&(n.pbrMetallicRoughness.baseColorTexture={index:r})}}}function ga(t,e={}){return new ba().normalize(t,e)}async function Ea(t,e,n=0,s,r){return Ia(t,e,n,s),ga(t,{normalize:s?.gltf?.normalize}),ma(t,s,r),s?.gltf?.loadBuffers&&t.json.buffers&&await Ma(t,s,r),s?.gltf?.loadImages&&await Ta(t,s,r),await ha(t,s,r),t}function Ia(t,e,n,s){if(s.uri&&(t.baseUri=s.uri),e instanceof ArrayBuffer&&!jo(e,n,s)&&(e=new TextDecoder().decode(e)),typeof e=="string")t.json=Jn(e);else if(e instanceof ArrayBuffer){const i={};n=Vo(i,e,n,s.glb),T(i.type==="glTF",`Invalid GLB magic string ${i.type}`),t._glb=i,t.json=i.json}else T(!1,"GLTF: must be ArrayBuffer or string");const r=t.json.buffers||[];if(t.buffers=new Array(r.length).fill(null),t._glb&&t._glb.header.hasBinChunk){const{binChunks:i}=t._glb;t.buffers[0]={arrayBuffer:i[0].arrayBuffer,byteOffset:i[0].byteOffset,byteLength:i[0].byteLength}}const o=t.json.images||[];t.images=new Array(o.length).fill({})}async function Ma(t,e,n){const s=t.json.buffers||[];for(let r=0;r<s.length;++r){const o=s[r];if(o.uri){const{fetch:i}=n;T(i);const a=jt(o.uri,e),l=await(await n?.fetch?.(a))?.arrayBuffer?.();t.buffers[r]={arrayBuffer:l,byteOffset:0,byteLength:l.byteLength},delete o.uri}else t.buffers[r]===null&&(t.buffers[r]={arrayBuffer:new ArrayBuffer(o.byteLength),byteOffset:0,byteLength:o.byteLength})}}async function Ta(t,e,n){const s=ya(t),r=t.json.images||[],o=[];for(const i of s)o.push(Fa(t,r[i],i,e,n));return await Promise.all(o)}function ya(t){const e=new Set,n=t.json.textures||[];for(const s of n)s.source!==void 0&&e.add(s.source);return Array.from(e).sort()}async function Fa(t,e,n,s,r){let o;if(e.uri&&!e.hasOwnProperty("bufferView")){const a=jt(e.uri,s),{fetch:c}=r;o=await(await c(a)).arrayBuffer(),e.bufferView={data:o}}if(Number.isFinite(e.bufferView)){const a=_r(t.json,t.buffers,e.bufferView);o=gt(a.buffer,a.byteOffset,a.byteLength)}T(o,"glTF image has no data");let i=await Et(o,[Dn,Vs],{...s,mimeType:e.mimeType,basis:s.basis||{format:Dt()}},r);i&&i[0]&&(i={compressed:!0,mipmaps:!1,width:i[0].width,height:i[0].height,data:i[0]}),t.images=t.images||[],t.images[n]=i}const Se={dataType:null,batchType:null,name:"glTF",id:"gltf",module:"gltf",version:Ho,extensions:["gltf","glb"],mimeTypes:["model/gltf+json","model/gltf-binary"],text:!0,binary:!0,tests:["glTF"],parse:_a,options:{gltf:{normalize:!0,loadBuffers:!0,loadImages:!0,decompressMeshes:!0},log:console}};async function _a(t,e={},n){e={...Se.options,...e},e.gltf={...Se.options.gltf,...e.gltf};const{byteOffset:s=0}=e;return await Ea({},t,s,e,n)}const Ra={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT2:4,MAT3:9,MAT4:16},Ga={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4},y={TEXTURE_MAG_FILTER:10240,TEXTURE_MIN_FILTER:10241,TEXTURE_WRAP_S:10242,TEXTURE_WRAP_T:10243,REPEAT:10497,LINEAR:9729,NEAREST_MIPMAP_LINEAR:9986},va={magFilter:y.TEXTURE_MAG_FILTER,minFilter:y.TEXTURE_MIN_FILTER,wrapS:y.TEXTURE_WRAP_S,wrapT:y.TEXTURE_WRAP_T},Da={[y.TEXTURE_MAG_FILTER]:y.LINEAR,[y.TEXTURE_MIN_FILTER]:y.NEAREST_MIPMAP_LINEAR,[y.TEXTURE_WRAP_S]:y.REPEAT,[y.TEXTURE_WRAP_T]:y.REPEAT};function Sa(){return{id:"default-sampler",parameters:Da}}function Oa(t){return Ga[t]}function xa(t){return Ra[t]}class La{baseUri="";jsonUnprocessed;json;buffers=[];images=[];postProcess(e,n={}){const{json:s,buffers:r=[],images:o=[]}=e,{baseUri:i=""}=e;return T(s),this.baseUri=i,this.buffers=r,this.images=o,this.jsonUnprocessed=s,this.json=this._resolveTree(e.json,n),this.json}_resolveTree(e,n={}){const s={...e};return this.json=s,e.bufferViews&&(s.bufferViews=e.bufferViews.map((r,o)=>this._resolveBufferView(r,o))),e.images&&(s.images=e.images.map((r,o)=>this._resolveImage(r,o))),e.samplers&&(s.samplers=e.samplers.map((r,o)=>this._resolveSampler(r,o))),e.textures&&(s.textures=e.textures.map((r,o)=>this._resolveTexture(r,o))),e.accessors&&(s.accessors=e.accessors.map((r,o)=>this._resolveAccessor(r,o))),e.materials&&(s.materials=e.materials.map((r,o)=>this._resolveMaterial(r,o))),e.meshes&&(s.meshes=e.meshes.map((r,o)=>this._resolveMesh(r,o))),e.nodes&&(s.nodes=e.nodes.map((r,o)=>this._resolveNode(r,o)),s.nodes=s.nodes.map((r,o)=>this._resolveNodeChildren(r))),e.skins&&(s.skins=e.skins.map((r,o)=>this._resolveSkin(r,o))),e.scenes&&(s.scenes=e.scenes.map((r,o)=>this._resolveScene(r,o))),typeof this.json.scene=="number"&&s.scenes&&(s.scene=s.scenes[this.json.scene]),s}getScene(e){return this._get(this.json.scenes,e)}getNode(e){return this._get(this.json.nodes,e)}getSkin(e){return this._get(this.json.skins,e)}getMesh(e){return this._get(this.json.meshes,e)}getMaterial(e){return this._get(this.json.materials,e)}getAccessor(e){return this._get(this.json.accessors,e)}getCamera(e){return this._get(this.json.cameras,e)}getTexture(e){return this._get(this.json.textures,e)}getSampler(e){return this._get(this.json.samplers,e)}getImage(e){return this._get(this.json.images,e)}getBufferView(e){return this._get(this.json.bufferViews,e)}getBuffer(e){return this._get(this.json.buffers,e)}_get(e,n){if(typeof n=="object")return n;const s=e&&e[n];return s||console.warn(`glTF file error: Could not find ${e}[${n}]`),s}_resolveScene(e,n){return{...e,id:e.id||`scene-${n}`,nodes:(e.nodes||[]).map(s=>this.getNode(s))}}_resolveNode(e,n){const s={...e,id:e?.id||`node-${n}`};return e.mesh!==void 0&&(s.mesh=this.getMesh(e.mesh)),e.camera!==void 0&&(s.camera=this.getCamera(e.camera)),e.skin!==void 0&&(s.skin=this.getSkin(e.skin)),e.meshes!==void 0&&e.meshes.length&&(s.mesh=e.meshes.reduce((r,o)=>{const i=this.getMesh(o);return r.id=i.id,r.primitives=r.primitives.concat(i.primitives),r},{primitives:[]})),s}_resolveNodeChildren(e){return e.children&&(e.children=e.children.map(n=>this.getNode(n))),e}_resolveSkin(e,n){const s=typeof e.inverseBindMatrices=="number"?this.getAccessor(e.inverseBindMatrices):void 0;return{...e,id:e.id||`skin-${n}`,inverseBindMatrices:s}}_resolveMesh(e,n){const s={...e,id:e.id||`mesh-${n}`,primitives:[]};return e.primitives&&(s.primitives=e.primitives.map(r=>{const o={...r,attributes:{},indices:void 0,material:void 0},i=r.attributes;for(const a in i)o.attributes[a]=this.getAccessor(i[a]);return r.indices!==void 0&&(o.indices=this.getAccessor(r.indices)),r.material!==void 0&&(o.material=this.getMaterial(r.material)),o})),s}_resolveMaterial(e,n){const s={...e,id:e.id||`material-${n}`};if(s.normalTexture&&(s.normalTexture={...s.normalTexture},s.normalTexture.texture=this.getTexture(s.normalTexture.index)),s.occlusionTexture&&(s.occlusionTexture={...s.occlusionTexture},s.occlusionTexture.texture=this.getTexture(s.occlusionTexture.index)),s.emissiveTexture&&(s.emissiveTexture={...s.emissiveTexture},s.emissiveTexture.texture=this.getTexture(s.emissiveTexture.index)),s.emissiveFactor||(s.emissiveFactor=s.emissiveTexture?[1,1,1]:[0,0,0]),s.pbrMetallicRoughness){s.pbrMetallicRoughness={...s.pbrMetallicRoughness};const r=s.pbrMetallicRoughness;r.baseColorTexture&&(r.baseColorTexture={...r.baseColorTexture},r.baseColorTexture.texture=this.getTexture(r.baseColorTexture.index)),r.metallicRoughnessTexture&&(r.metallicRoughnessTexture={...r.metallicRoughnessTexture},r.metallicRoughnessTexture.texture=this.getTexture(r.metallicRoughnessTexture.index))}return s}_resolveAccessor(e,n){const s=Oa(e.componentType),r=xa(e.type),o=s*r,i={...e,id:e.id||`accessor-${n}`,bytesPerComponent:s,components:r,bytesPerElement:o,value:void 0,bufferView:void 0,sparse:void 0};if(e.bufferView!==void 0&&(i.bufferView=this.getBufferView(e.bufferView)),i.bufferView){const a=i.bufferView.buffer,{ArrayType:c,byteLength:l}=Le(i,i.bufferView),f=(i.bufferView.byteOffset||0)+(i.byteOffset||0)+a.byteOffset;let u=a.arrayBuffer.slice(f,f+l);i.bufferView.byteStride&&(u=this._getValueFromInterleavedBuffer(a,f,i.bufferView.byteStride,i.bytesPerElement,i.count)),i.value=new c(u)}return i}_getValueFromInterleavedBuffer(e,n,s,r,o){const i=new Uint8Array(o*r);for(let a=0;a<o;a++){const c=n+a*s;i.set(new Uint8Array(e.arrayBuffer.slice(c,c+r)),a*r)}return i.buffer}_resolveTexture(e,n){return{...e,id:e.id||`texture-${n}`,sampler:typeof e.sampler=="number"?this.getSampler(e.sampler):Sa(),source:typeof e.source=="number"?this.getImage(e.source):void 0}}_resolveSampler(e,n){const s={id:e.id||`sampler-${n}`,...e,parameters:{}};for(const r in s){const o=this._enumSamplerParameter(r);o!==void 0&&(s.parameters[o]=s[r])}return s}_enumSamplerParameter(e){return va[e]}_resolveImage(e,n){const s={...e,id:e.id||`image-${n}`,image:null,bufferView:e.bufferView!==void 0?this.getBufferView(e.bufferView):void 0},r=this.images[n];return r&&(s.image=r),s}_resolveBufferView(e,n){const s=e.buffer,r=this.buffers[s].arrayBuffer;let o=this.buffers[s].byteOffset||0;return e.byteOffset&&(o+=e.byteOffset),{id:`bufferView-${n}`,...e,buffer:this.buffers[s],data:new Uint8Array(r,o,e.byteLength)}}_resolveCamera(e,n){const s={...e,id:e.id||`camera-${n}`};return s.perspective,s.orthographic,s}}function Ha(t,e){return new La().postProcess(t,e)}async function Pa(t){const e=[];return t.scenes.forEach(n=>{n.traverse(s=>{})}),await Ua(()=>e.some(n=>!n.loaded))}async function Ua(t){for(;t();)await new Promise(e=>requestAnimationFrame(e))}const dt=`uniform scenegraphUniforms {
  float sizeScale;
  float sizeMinPixels;
  float sizeMaxPixels;
  mat4 sceneModelMatrix;
  bool composeModelMatrix;
} scenegraph;
`,Na={name:"scenegraph",vs:dt,fs:dt,uniformTypes:{sizeScale:"f32",sizeMinPixels:"f32",sizeMaxPixels:"f32",sceneModelMatrix:"mat4x4<f32>",composeModelMatrix:"f32"}},Ja=`#version 300 es
#define SHADER_NAME scenegraph-layer-vertex-shader
in vec3 instancePositions;
in vec3 instancePositions64Low;
in vec4 instanceColors;
in vec3 instancePickingColors;
in vec3 instanceModelMatrixCol0;
in vec3 instanceModelMatrixCol1;
in vec3 instanceModelMatrixCol2;
in vec3 instanceTranslation;
in vec3 positions;
#ifdef HAS_UV
in vec2 texCoords;
#endif
#ifdef LIGHTING_PBR
#ifdef HAS_NORMALS
in vec3 normals;
#endif
#endif
out vec4 vColor;
#ifndef LIGHTING_PBR
#ifdef HAS_UV
out vec2 vTEXCOORD_0;
#endif
#endif
void main(void) {
#if defined(HAS_UV) && !defined(LIGHTING_PBR)
vTEXCOORD_0 = texCoords;
geometry.uv = texCoords;
#endif
geometry.worldPosition = instancePositions;
geometry.pickingColor = instancePickingColors;
mat3 instanceModelMatrix = mat3(instanceModelMatrixCol0, instanceModelMatrixCol1, instanceModelMatrixCol2);
vec3 normal = vec3(0.0, 0.0, 1.0);
#ifdef LIGHTING_PBR
#ifdef HAS_NORMALS
normal = instanceModelMatrix * (scenegraph.sceneModelMatrix * vec4(normals, 0.0)).xyz;
#endif
#endif
float originalSize = project_size_to_pixel(scenegraph.sizeScale);
float clampedSize = clamp(originalSize, scenegraph.sizeMinPixels, scenegraph.sizeMaxPixels);
vec3 pos = (instanceModelMatrix * (scenegraph.sceneModelMatrix * vec4(positions, 1.0)).xyz) * scenegraph.sizeScale * (clampedSize / originalSize) + instanceTranslation;
if(scenegraph.composeModelMatrix) {
DECKGL_FILTER_SIZE(pos, geometry);
geometry.normal = project_normal(normal);
geometry.worldPosition += pos;
gl_Position = project_position_to_clipspace(pos + instancePositions, instancePositions64Low, vec3(0.0), geometry.position);
}
else {
pos = project_size(pos);
DECKGL_FILTER_SIZE(pos, geometry);
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, pos, geometry.position);
geometry.normal = project_normal(normal);
}
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
#ifdef LIGHTING_PBR
pbr_vPosition = geometry.position.xyz;
#ifdef HAS_NORMALS
pbr_vNormal = geometry.normal;
#endif
#ifdef HAS_UV
pbr_vUV = texCoords;
#else
pbr_vUV = vec2(0., 0.);
#endif
geometry.uv = pbr_vUV;
#endif
vColor = instanceColors;
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,wa=`#version 300 es
#define SHADER_NAME scenegraph-layer-fragment-shader
in vec4 vColor;
out vec4 fragColor;
#ifndef LIGHTING_PBR
#if defined(HAS_UV) && defined(HAS_BASECOLORMAP)
in vec2 vTEXCOORD_0;
uniform sampler2D pbr_baseColorSampler;
#endif
#endif
void main(void) {
#ifdef LIGHTING_PBR
fragColor = vColor * pbr_filterColor(vec4(0));
geometry.uv = pbr_vUV;
#else
#if defined(HAS_UV) && defined(HAS_BASECOLORMAP)
fragColor = vColor * texture(pbr_baseColorSampler, vTEXCOORD_0);
geometry.uv = vTEXCOORD_0;
#else
fragColor = vColor;
#endif
#endif
fragColor.a *= layer.opacity;
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,zt=[255,255,255,255],Ka={scenegraph:{type:"object",value:null,async:!0},getScene:t=>t&&t.scenes?typeof t.scene=="object"?t.scene:t.scenes[t.scene||0]:t,getAnimator:t=>t&&t.animator,_animations:null,sizeScale:{type:"number",value:1,min:0},sizeMinPixels:{type:"number",min:0,value:0},sizeMaxPixels:{type:"number",min:0,value:Number.MAX_SAFE_INTEGER},getPosition:{type:"accessor",value:t=>t.position},getColor:{type:"accessor",value:zt},_lighting:"flat",_imageBasedLightingEnvironment:void 0,getOrientation:{type:"accessor",value:[0,0,0]},getScale:{type:"accessor",value:[1,1,1]},getTranslation:{type:"accessor",value:[0,0,0]},getTransformMatrix:{type:"accessor",value:[]},loaders:[Se]};class Wt extends Bt{getShaders(){const e={};let n;this.props._lighting==="pbr"?(n=Ft,e.LIGHTING_PBR=1):n={name:"pbrMaterial"};const s=[mt,ht,Na,n];return super.getShaders({defines:e,vs:Ja,fs:wa,modules:s})}initializeState(){this.getAttributeManager().addInstanced({instancePositions:{size:3,type:"float64",fp64:this.use64bitPositions(),accessor:"getPosition",transition:!0},instanceColors:{type:"unorm8",size:this.props.colorFormat.length,accessor:"getColor",defaultValue:zt,transition:!0},instanceModelMatrix:_t})}updateState(e){super.updateState(e);const{props:n,oldProps:s}=e;n.scenegraph!==s.scenegraph?this._updateScenegraph():n._animations!==s._animations&&this._applyAnimationsProp(this.state.animator,n._animations)}finalizeState(e){super.finalizeState(e),this.state.scenegraph?.destroy()}get isLoaded(){return!!(this.state?.scenegraph&&super.isLoaded)}_updateScenegraph(){const e=this.props,{device:n}=this.context;let s=null;if(e.scenegraph instanceof re)s={scenes:[e.scenegraph]};else if(e.scenegraph&&typeof e.scenegraph=="object"){const a=e.scenegraph,c=a.json?Ha(a):a,l=gr(n,c,this._getModelOptions());s={gltf:c,...l},Pa(l).then(()=>{this.setNeedsRedraw()}).catch(f=>{this.raiseError(f,"loading glTF")})}const r={layer:this,device:this.context.device},o=e.getScene(s,r),i=e.getAnimator(s,r);if(o instanceof U){this.state.scenegraph?.destroy(),this._applyAnimationsProp(i,e._animations);const a=[];o.traverse(c=>{c instanceof Re&&a.push(c.model)}),this.setState({scenegraph:o,animator:i,models:a}),this.getAttributeManager().invalidateAll()}else o!==null&&ee.warn("invalid scenegraph:",o)()}_applyAnimationsProp(e,n){if(!e||!n)return;const s=e.getAnimations();Object.keys(n).sort().forEach(r=>{const o=n[r];if(r==="*")s.forEach(i=>{Object.assign(i,o)});else if(Number.isFinite(Number(r))){const i=Number(r);i>=0&&i<s.length?Object.assign(s[i],o):ee.warn(`animation ${r} not found`)()}else{const i=s.find(({animation:a})=>a.name===r);i?Object.assign(i,o):ee.warn(`animation ${r} not found`)()}})}_getModelOptions(){const{_imageBasedLightingEnvironment:e}=this.props;let n;return e&&(typeof e=="function"?n=e({gl:this.context.gl,layer:this}):n=e),{imageBasedLightingEnvironment:n,modelOptions:{id:this.props.id,isInstanced:!0,bufferLayout:this.getAttributeManager().getBufferLayouts(),...this.getShaders()},useTangents:!1}}draw({context:e}){if(!this.state.scenegraph)return;this.props._animations&&this.state.animator&&(this.state.animator.animate(e.timeline.getTime()),this.setNeedsRedraw());const{viewport:n,renderPass:s}=this.context,{sizeScale:r,sizeMinPixels:o,sizeMaxPixels:i,coordinateSystem:a}=this.props,c={camera:n.cameraPosition},l=this.getNumInstances();this.state.scenegraph.traverse((f,{worldMatrix:u})=>{if(f instanceof Re){const{model:A}=f;A.setInstanceCount(l);const d={sizeScale:r,sizeMinPixels:o,sizeMaxPixels:i,composeModelMatrix:Rt(n,a),sceneModelMatrix:u};A.shaderInputs.setProps({pbrProjection:c,scenegraph:d}),A.draw(s)}})}}Wt.defaultProps=Ka;Wt.layerName="ScenegraphLayer";export{vi as D,Se as G,Q as M,gs as Q,Gt as S,ks as a,Et as b,Ha as c,Wt as d,za as g,Ft as p};
//# sourceMappingURL=mesh-layers-wiqredoy.js.map
