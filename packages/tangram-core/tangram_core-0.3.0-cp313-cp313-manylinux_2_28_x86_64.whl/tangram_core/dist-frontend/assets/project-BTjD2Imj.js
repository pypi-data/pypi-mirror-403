import{O as _,P as I,t as H,Y as G,U as N}from"./deep-equal-BTW2ZN6S.js";function b(e,t){if(!e)throw new Error(t||"shadertools: assertion failed.")}const C={number:{type:"number",validate(e,t){return Number.isFinite(e)&&typeof t=="object"&&(t.max===void 0||e<=t.max)&&(t.min===void 0||e>=t.min)}},array:{type:"array",validate(e,t){return Array.isArray(e)||ArrayBuffer.isView(e)}}};function ie(e){const t={};for(const[n,o]of Object.entries(e))t[n]=se(o);return t}function se(e){let t=F(e);if(t!=="object")return{value:e,...C[t],type:t};if(typeof e=="object")return e?e.type!==void 0?{...e,...C[e.type],type:e.type}:e.value===void 0?{type:"object",value:e}:(t=F(e.value),{...e,...C[t],type:t}):{type:"object",value:null};throw new Error("props")}function F(e){return Array.isArray(e)||ArrayBuffer.isView(e)?"array":typeof e}const ce=`#ifdef MODULE_LOGDEPTH
  logdepth_adjustPosition(gl_Position);
#endif
`,ae=`#ifdef MODULE_MATERIAL
  fragColor = material_filterColor(fragColor);
#endif

#ifdef MODULE_LIGHTING
  fragColor = lighting_filterColor(fragColor);
#endif

#ifdef MODULE_FOG
  fragColor = fog_filterColor(fragColor);
#endif

#ifdef MODULE_PICKING
  fragColor = picking_filterHighlightColor(fragColor);
  fragColor = picking_filterPickingColor(fragColor);
#endif

#ifdef MODULE_LOGDEPTH
  logdepth_setFragDepth();
#endif
`,fe={vertex:ce,fragment:ae},W=/void\s+main\s*\([^)]*\)\s*\{\n?/,k=/}\n?[^{}]*$/,w=[],h="__LUMA_INJECT_DECLARATIONS__";function le(e){const t={vertex:{},fragment:{}};for(const n in e){let o=e[n];const r=_e(n);typeof o=="string"&&(o={order:0,injection:o}),t[r][n]=o}return t}function _e(e){const t=e.slice(0,2);switch(t){case"vs":return"vertex";case"fs":return"fragment";default:throw new Error(t)}}function U(e,t,n,o=!1){const r=t==="vertex";for(const i in n){const c=n[i];c.sort((s,f)=>s.order-f.order),w.length=c.length;for(let s=0,f=c.length;s<f;++s)w[s]=c[s].injection;const a=`${w.join(`
`)}
`;switch(i){case"vs:#decl":r&&(e=e.replace(h,a));break;case"vs:#main-start":r&&(e=e.replace(W,s=>s+a));break;case"vs:#main-end":r&&(e=e.replace(k,s=>a+s));break;case"fs:#decl":r||(e=e.replace(h,a));break;case"fs:#main-start":r||(e=e.replace(W,s=>s+a));break;case"fs:#main-end":r||(e=e.replace(k,s=>a+s));break;default:e=e.replace(i,s=>s+a)}}return e=e.replace(h,""),o&&(e=e.replace(/\}\s*$/,i=>i+fe[t])),e}function x(e){e.map(t=>pe(t))}function pe(e){if(e.instance)return;x(e.dependencies||[]);const{propTypes:t={},deprecations:n=[],inject:o={}}=e,r={normalizedInjections:le(o),parsedDeprecations:ue(n)};t&&(r.propValidators=ie(t)),e.instance=r;let i={};t&&(i=Object.entries(t).reduce((c,[a,s])=>{const f=s?.value;return f&&(c[a]=f),c},{})),e.defaultUniforms={...e.defaultUniforms,...i}}function J(e,t,n){e.deprecations?.forEach(o=>{o.regex?.test(t)&&(o.deprecated?n.deprecated(o.old,o.new)():n.removed(o.old,o.new)())})}function ue(e){return e.forEach(t=>{t.type==="function"?t.regex=new RegExp(`\\b${t.old}\\(`):t.regex=new RegExp(`${t.type} ${t.old};`)}),e}function Y(e){x(e);const t={},n={};Z({modules:e,level:0,moduleMap:t,moduleDepth:n});const o=Object.keys(n).sort((r,i)=>n[i]-n[r]).map(r=>t[r]);return x(o),o}function Z(e){const{modules:t,level:n,moduleMap:o,moduleDepth:r}=e;if(n>=5)throw new Error("Possible loop in shader dependency graph");for(const i of t)o[i.name]=i,(r[i.name]===void 0||r[i.name]<n)&&(r[i.name]=n);for(const i of t)i.dependencies&&Z({modules:i.dependencies,level:n+1,moduleMap:o,moduleDepth:r})}function me(e){switch(e?.gpu.toLowerCase()){case"apple":return`#define APPLE_GPU
// Apple optimizes away the calculation necessary for emulated fp64
#define LUMA_FP64_CODE_ELIMINATION_WORKAROUND 1
#define LUMA_FP32_TAN_PRECISION_WORKAROUND 1
// Intel GPU doesn't have full 32 bits precision in same cases, causes overflow
#define LUMA_FP64_HIGH_BITS_OVERFLOW_WORKAROUND 1
`;case"nvidia":return`#define NVIDIA_GPU
// Nvidia optimizes away the calculation necessary for emulated fp64
#define LUMA_FP64_CODE_ELIMINATION_WORKAROUND 1
`;case"intel":return`#define INTEL_GPU
// Intel optimizes away the calculation necessary for emulated fp64
#define LUMA_FP64_CODE_ELIMINATION_WORKAROUND 1
// Intel's built-in 'tan' function doesn't have acceptable precision
#define LUMA_FP32_TAN_PRECISION_WORKAROUND 1
// Intel GPU doesn't have full 32 bits precision in same cases, causes overflow
#define LUMA_FP64_HIGH_BITS_OVERFLOW_WORKAROUND 1
`;case"amd":return`#define AMD_GPU
`;default:return`#define DEFAULT_GPU
// Prevent driver from optimizing away the calculation necessary for emulated fp64
#define LUMA_FP64_CODE_ELIMINATION_WORKAROUND 1
// Headless Chrome's software shader 'tan' function doesn't have acceptable precision
#define LUMA_FP32_TAN_PRECISION_WORKAROUND 1
// If the GPU doesn't have full 32 bits precision, will causes overflow
#define LUMA_FP64_HIGH_BITS_OVERFLOW_WORKAROUND 1
`}}function de(e,t){if(Number(e.match(/^#version[ \t]+(\d+)/m)?.[1]||100)!==300)throw new Error("luma.gl v9 only supports GLSL 3.00 shader sources");switch(t){case"vertex":return e=$(e,Ee),e;case"fragment":return e=$(e,Oe),e;default:throw new Error(t)}}const K=[[/^(#version[ \t]+(100|300[ \t]+es))?[ \t]*\n/,`#version 300 es
`],[/\btexture(2D|2DProj|Cube)Lod(EXT)?\(/g,"textureLod("],[/\btexture(2D|2DProj|Cube)(EXT)?\(/g,"texture("]],Ee=[...K,[z("attribute"),"in $1"],[z("varying"),"out $1"]],Oe=[...K,[z("varying"),"in $1"]];function $(e,t){for(const[n,o]of t)e=e.replace(n,o);return e}function z(e){return new RegExp(`\\b${e}[ \\t]+(\\w+[ \\t]+\\w+(\\[\\w+\\])?;)`,"g")}function X(e,t){let n="";for(const o in e){const r=e[o];if(n+=`void ${r.signature} {
`,r.header&&(n+=`  ${r.header}`),t[o]){const i=t[o];i.sort((c,a)=>c.order-a.order);for(const c of i)n+=`  ${c.injection}
`}r.footer&&(n+=`  ${r.footer}`),n+=`}
`}return n}function q(e){const t={vertex:{},fragment:{}};for(const n of e){let o,r;typeof n!="string"?(o=n,r=o.hook):(o={},r=n),r=r.trim();const[i,c]=r.split(":"),a=r.replace(/\(.+/,""),s=Object.assign(o,{signature:c});switch(i){case"vs":t.vertex[a]=s;break;case"fs":t.fragment[a]=s;break;default:throw new Error(i)}}return t}function ve(e,t){return{name:je(e,t),language:"glsl",version:Se(e)}}function je(e,t="unnamed"){const o=/#define[^\S\r\n]*SHADER_NAME[^\S\r\n]*([A-Za-z0-9_-]+)\s*/.exec(e);return o?o[1]:t}function Se(e){let t=100;const n=e.match(/[^\s]+/g);if(n&&n.length>=2&&n[0]==="#version"){const o=parseInt(n[1],10);Number.isFinite(o)&&(t=o)}if(t!==100&&t!==300)throw new Error(`Invalid GLSL version ${t}`);return t}const Q=`

${h}
`,ge=`precision highp float;
`;function Te(e){const t=Y(e.modules||[]);return{source:Ie(e.platformInfo,{...e,source:e.source,stage:"vertex",modules:t}),getUniforms:ee(t)}}function Ae(e){const{vs:t,fs:n}=e,o=Y(e.modules||[]);return{vs:B(e.platformInfo,{...e,source:t,stage:"vertex",modules:o}),fs:B(e.platformInfo,{...e,source:n,stage:"fragment",modules:o}),getUniforms:ee(o)}}function Ie(e,t){const{source:n,stage:o,modules:r,hookFunctions:i=[],inject:c={},log:a}=t;b(typeof n=="string","shader source must be a string");const s=n;let f="";const v=q(i),d={},T={},p={};for(const u in c){const S=typeof c[u]=="string"?{injection:c[u],order:0}:c[u],l=/^(v|f)s:(#)?([\w-]+)$/.exec(u);if(l){const E=l[2],g=l[3];E?g==="decl"?T[u]=[S]:p[u]=[S]:d[u]=[S]}else p[u]=[S]}const j=r;for(const u of j){a&&J(u,s,a);const S=te(u,"wgsl");f+=S;const l=u.injections?.[o]||{};for(const E in l){const g=/^(v|f)s:#([\w-]+)$/.exec(E);if(g){const A=g[2]==="decl"?T:p;A[E]=A[E]||[],A[E].push(l[E])}else d[E]=d[E]||[],d[E].push(l[E])}}return f+=Q,f=U(f,o,T),f+=X(v[o],d),f+=s,f=U(f,o,p),f}function B(e,t){const{source:n,stage:o,language:r="glsl",modules:i,defines:c={},hookFunctions:a=[],inject:s={},prologue:f=!0,log:v}=t;b(typeof n=="string","shader source must be a string");const d=r==="glsl"?ve(n).version:-1,T=e.shaderLanguageVersion,p=d===100?"#version 100":"#version 300 es",u=n.split(`
`).slice(1).join(`
`),S={};i.forEach(m=>{Object.assign(S,m.defines)}),Object.assign(S,c);let l="";switch(r){case"wgsl":break;case"glsl":l=f?`${p}

// ----- PROLOGUE -------------------------
${`#define SHADER_TYPE_${o.toUpperCase()}`}

${me(e)}
${o==="fragment"?ge:""}

// ----- APPLICATION DEFINES -------------------------

${Me(S)}

`:`${p}
`;break}const E=q(a),g={},P={},A={};for(const m in s){const R=typeof s[m]=="string"?{injection:s[m],order:0}:s[m],M=/^(v|f)s:(#)?([\w-]+)$/.exec(m);if(M){const O=M[2],y=M[3];O?y==="decl"?P[m]=[R]:A[m]=[R]:g[m]=[R]}else A[m]=[R]}for(const m of i){v&&J(m,u,v);const R=te(m,o);l+=R;const M=m.instance?.normalizedInjections[o]||{};for(const O in M){const y=/^(v|f)s:#([\w-]+)$/.exec(O);if(y){const D=y[2]==="decl"?P:A;D[O]=D[O]||[],D[O].push(M[O])}else g[O]=g[O]||[],g[O].push(M[O])}}return l+="// ----- MAIN SHADER SOURCE -------------------------",l+=Q,l=U(l,o,P),l+=X(E[o],g),l+=u,l=U(l,o,A),r==="glsl"&&d!==T&&(l=de(l,o)),l.trim()}function ee(e){return function(n){const o={};for(const r of e){const i=r.getUniforms?.(n,o);Object.assign(o,i)}return o}}function Me(e={}){let t="";for(const n in e){const o=e[n];(o||Number.isFinite(o))&&(t+=`#define ${n.toUpperCase()} ${e[n]}
`)}return t}function te(e,t){let n;switch(t){case"vertex":n=e.vs||"";break;case"fragment":n=e.fs||"";break;case"wgsl":n=e.source||"";break;default:b(!1)}if(!e.name)throw new Error("Shader module must have a name");const o=e.name.toUpperCase().replace(/[^0-9a-z]/gi,"_");let r=`// ----- MODULE ${e.name} ---------------

`;return t!=="wgsl"&&(r+=`#define MODULE_${o}
`),r+=`${n}
`,r}const Re=/^\s*\#\s*ifdef\s*([a-zA-Z_]+)\s*$/,Le=/^\s*\#\s*endif\s*$/;function Pe(e,t){const n=e.split(`
`),o=[];let r=!0,i=null;for(const c of n){const a=c.match(Re),s=c.match(Le);a?(i=a[1],r=!!t?.defines?.[i]):s?r=!0:r&&o.push(c)}return o.join(`
`)}class L{static defaultShaderAssembler;_hookFunctions=[];_defaultModules=[];static getDefaultShaderAssembler(){return L.defaultShaderAssembler=L.defaultShaderAssembler||new L,L.defaultShaderAssembler}addDefaultModule(t){this._defaultModules.find(n=>n.name===(typeof t=="string"?t:t.name))||this._defaultModules.push(t)}removeDefaultModule(t){const n=typeof t=="string"?t:t.name;this._defaultModules=this._defaultModules.filter(o=>o.name!==n)}addShaderHook(t,n){n&&(t=Object.assign(n,{hook:t})),this._hookFunctions.push(t)}assembleWGSLShader(t){const n=this._getModuleList(t.modules),o=this._hookFunctions,{source:r,getUniforms:i}=Te({...t,source:t.source,modules:n,hookFunctions:o});return{source:t.platformInfo.shaderLanguage==="wgsl"?Pe(r):r,getUniforms:i,modules:n}}assembleGLSLShaderPair(t){const n=this._getModuleList(t.modules),o=this._hookFunctions;return{...Ae({...t,vs:t.vs,fs:t.fs,modules:n,hookFunctions:o}),modules:n}}_getModuleList(t=[]){const n=new Array(this._defaultModules.length+t.length),o={};let r=0;for(let i=0,c=this._defaultModules.length;i<c;++i){const a=this._defaultModules[i],s=a.name;n[r++]=a,o[s]=!0}for(let i=0,c=t.length;i<c;++i){const a=t[i],s=a.name;o[s]||(n[r++]=a,o[s]=!0)}return n.length=r,x(n),n}}const ye=`#ifdef LUMA_FP32_TAN_PRECISION_WORKAROUND

// All these functions are for substituting tan() function from Intel GPU only
const float TWO_PI = 6.2831854820251465;
const float PI_2 = 1.5707963705062866;
const float PI_16 = 0.1963495463132858;

const float SIN_TABLE_0 = 0.19509032368659973;
const float SIN_TABLE_1 = 0.3826834261417389;
const float SIN_TABLE_2 = 0.5555702447891235;
const float SIN_TABLE_3 = 0.7071067690849304;

const float COS_TABLE_0 = 0.9807852506637573;
const float COS_TABLE_1 = 0.9238795042037964;
const float COS_TABLE_2 = 0.8314695954322815;
const float COS_TABLE_3 = 0.7071067690849304;

const float INVERSE_FACTORIAL_3 = 1.666666716337204e-01; // 1/3!
const float INVERSE_FACTORIAL_5 = 8.333333767950535e-03; // 1/5!
const float INVERSE_FACTORIAL_7 = 1.9841270113829523e-04; // 1/7!
const float INVERSE_FACTORIAL_9 = 2.75573188446287533e-06; // 1/9!

float sin_taylor_fp32(float a) {
  float r, s, t, x;

  if (a == 0.0) {
    return 0.0;
  }

  x = -a * a;
  s = a;
  r = a;

  r = r * x;
  t = r * INVERSE_FACTORIAL_3;
  s = s + t;

  r = r * x;
  t = r * INVERSE_FACTORIAL_5;
  s = s + t;

  r = r * x;
  t = r * INVERSE_FACTORIAL_7;
  s = s + t;

  r = r * x;
  t = r * INVERSE_FACTORIAL_9;
  s = s + t;

  return s;
}

void sincos_taylor_fp32(float a, out float sin_t, out float cos_t) {
  if (a == 0.0) {
    sin_t = 0.0;
    cos_t = 1.0;
  }
  sin_t = sin_taylor_fp32(a);
  cos_t = sqrt(1.0 - sin_t * sin_t);
}

float tan_taylor_fp32(float a) {
    float sin_a;
    float cos_a;

    if (a == 0.0) {
        return 0.0;
    }

    // 2pi range reduction
    float z = floor(a / TWO_PI);
    float r = a - TWO_PI * z;

    float t;
    float q = floor(r / PI_2 + 0.5);
    int j = int(q);

    if (j < -2 || j > 2) {
        return 1.0 / 0.0;
    }

    t = r - PI_2 * q;

    q = floor(t / PI_16 + 0.5);
    int k = int(q);
    int abs_k = int(abs(float(k)));

    if (abs_k > 4) {
        return 1.0 / 0.0;
    } else {
        t = t - PI_16 * q;
    }

    float u = 0.0;
    float v = 0.0;

    float sin_t, cos_t;
    float s, c;
    sincos_taylor_fp32(t, sin_t, cos_t);

    if (k == 0) {
        s = sin_t;
        c = cos_t;
    } else {
        if (abs(float(abs_k) - 1.0) < 0.5) {
            u = COS_TABLE_0;
            v = SIN_TABLE_0;
        } else if (abs(float(abs_k) - 2.0) < 0.5) {
            u = COS_TABLE_1;
            v = SIN_TABLE_1;
        } else if (abs(float(abs_k) - 3.0) < 0.5) {
            u = COS_TABLE_2;
            v = SIN_TABLE_2;
        } else if (abs(float(abs_k) - 4.0) < 0.5) {
            u = COS_TABLE_3;
            v = SIN_TABLE_3;
        }
        if (k > 0) {
            s = u * sin_t + v * cos_t;
            c = u * cos_t - v * sin_t;
        } else {
            s = u * sin_t - v * cos_t;
            c = u * cos_t + v * sin_t;
        }
    }

    if (j == 0) {
        sin_a = s;
        cos_a = c;
    } else if (j == 1) {
        sin_a = c;
        cos_a = -s;
    } else if (j == -1) {
        sin_a = -c;
        cos_a = s;
    } else {
        sin_a = -s;
        cos_a = -c;
    }
    return sin_a / cos_a;
}
#endif

float tan_fp32(float a) {
#ifdef LUMA_FP32_TAN_PRECISION_WORKAROUND
  return tan_taylor_fp32(a);
#else
  return tan(a);
#endif
}
`,he={name:"fp32",vs:ye},Ne=`const SMOOTH_EDGE_RADIUS: f32 = 0.5;

struct VertexGeometry {
  position: vec4<f32>,
  worldPosition: vec3<f32>,
  worldPositionAlt: vec3<f32>,
  normal: vec3<f32>,
  uv: vec2<f32>,
  pickingColor: vec3<f32>,
};

var<private> geometry_: VertexGeometry = VertexGeometry(
  vec4<f32>(0.0, 0.0, 1.0, 0.0),
  vec3<f32>(0.0, 0.0, 0.0),
  vec3<f32>(0.0, 0.0, 0.0),
  vec3<f32>(0.0, 0.0, 0.0),
  vec2<f32>(0.0, 0.0),
  vec3<f32>(0.0, 0.0, 0.0)
);

struct FragmentGeometry {
  uv: vec2<f32>,
};

var<private> fragmentGeometry: FragmentGeometry;

fn smoothedge(edge: f32, x: f32) -> f32 {
  return smoothstep(edge - SMOOTH_EDGE_RADIUS, edge + SMOOTH_EDGE_RADIUS, x);
}
`,oe="#define SMOOTH_EDGE_RADIUS 0.5",Ue=`${oe}

struct VertexGeometry {
  vec4 position;
  vec3 worldPosition;
  vec3 worldPositionAlt;
  vec3 normal;
  vec2 uv;
  vec3 pickingColor;
} geometry = VertexGeometry(
  vec4(0.0, 0.0, 1.0, 0.0),
  vec3(0.0),
  vec3(0.0),
  vec3(0.0),
  vec2(0.0),
  vec3(0.0)
);
`,xe=`${oe}

struct FragmentGeometry {
  vec2 uv;
} geometry;

float smoothedge(float edge, float x) {
  return smoothstep(edge - SMOOTH_EDGE_RADIUS, edge + SMOOTH_EDGE_RADIUS, x);
}
`,De={name:"geometry",source:Ne,vs:Ue,fs:xe};function Ce(e,t){if(e===t)return!0;if(Array.isArray(e)){const n=e.length;if(!t||t.length!==n)return!1;for(let o=0;o<n;o++)if(e[o]!==t[o])return!1;return!0}return!1}function we(e){let t={},n;return o=>{for(const r in o)if(!Ce(o[r],t[r])){n=e(o),t=o;break}return n}}const V=[0,0,0,0],ze=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],ne=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],be=[0,0,0],re=[0,0,0],Ge=we($e);function Fe(e,t,n=re){n.length<3&&(n=[n[0],n[1],0]);let o=n,r,i=!0;switch(t===_.LNGLAT_OFFSETS||t===_.METER_OFFSETS?r=n:r=e.isGeospatial?[Math.fround(e.longitude),Math.fround(e.latitude),0]:null,e.projectionMode){case I.WEB_MERCATOR:(t===_.LNGLAT||t===_.CARTESIAN)&&(r=[0,0,0],i=!1);break;case I.WEB_MERCATOR_AUTO_OFFSET:t===_.LNGLAT?o=r:t===_.CARTESIAN&&(o=[Math.fround(e.center[0]),Math.fround(e.center[1]),0],r=e.unprojectPosition(o),o[0]-=n[0],o[1]-=n[1],o[2]-=n[2]);break;case I.IDENTITY:o=e.position.map(Math.fround),o[2]=o[2]||0;break;case I.GLOBE:i=!1,r=null;break;default:i=!1}return{geospatialOrigin:r,shaderCoordinateOrigin:o,offsetMode:i}}function We(e,t,n){const{viewMatrixUncentered:o,projectionMatrix:r}=e;let{viewMatrix:i,viewProjectionMatrix:c}=e,a=V,s=V,f=e.cameraPosition;const{geospatialOrigin:v,shaderCoordinateOrigin:d,offsetMode:T}=Fe(e,t,n);return T&&(s=e.projectPosition(v||d),f=[f[0]-s[0],f[1]-s[1],f[2]-s[2]],s[3]=1,a=H([],s,c),i=o||i,c=G([],r,i),c=G([],c,ze)),{viewMatrix:i,viewProjectionMatrix:c,projectionCenter:a,originCommon:s,cameraPosCommon:f,shaderCoordinateOrigin:d,geospatialOrigin:v}}function ke({viewport:e,devicePixelRatio:t=1,modelMatrix:n=null,coordinateSystem:o=_.DEFAULT,coordinateOrigin:r=re,autoWrapLongitude:i=!1}){o===_.DEFAULT&&(o=e.isGeospatial?_.LNGLAT:_.CARTESIAN);const c=Ge({viewport:e,devicePixelRatio:t,coordinateSystem:o,coordinateOrigin:r});return c.wrapLongitude=i,c.modelMatrix=n||ne,c}function $e({viewport:e,devicePixelRatio:t,coordinateSystem:n,coordinateOrigin:o}){const{projectionCenter:r,viewProjectionMatrix:i,originCommon:c,cameraPosCommon:a,shaderCoordinateOrigin:s,geospatialOrigin:f}=We(e,n,o),v=e.getDistanceScales(),d=[e.width*t,e.height*t],T=H([],[0,0,-e.focalDistance,1],e.projectionMatrix)[3]||1,p={coordinateSystem:n,projectionMode:e.projectionMode,coordinateOrigin:s,commonOrigin:c.slice(0,3),center:r,pseudoMeters:!!e._pseudoMeters,viewportSize:d,devicePixelRatio:t,focalDistance:T,commonUnitsPerMeter:v.unitsPerMeter,commonUnitsPerWorldUnit:v.unitsPerMeter,commonUnitsPerWorldUnit2:be,scale:e.scale,wrapLongitude:!1,viewProjectionMatrix:i,modelMatrix:ne,cameraPosition:a};if(f){const j=e.getDistanceScales(f);switch(n){case _.METER_OFFSETS:p.commonUnitsPerWorldUnit=j.unitsPerMeter,p.commonUnitsPerWorldUnit2=j.unitsPerMeter2;break;case _.LNGLAT:case _.LNGLAT_OFFSETS:e._pseudoMeters||(p.commonUnitsPerMeter=j.unitsPerMeter),p.commonUnitsPerWorldUnit=j.unitsPerDegree,p.commonUnitsPerWorldUnit2=j.unitsPerDegree2;break;case _.CARTESIAN:p.commonUnitsPerWorldUnit=[1,1,j.unitsPerMeter[2]],p.commonUnitsPerWorldUnit2=[0,0,j.unitsPerMeter2[2]];break}}return p}const Be=Object.keys(_).map(e=>`const COORDINATE_SYSTEM_${e}: i32 = ${_[e]};`).join(""),Ve=Object.keys(I).map(e=>`const PROJECTION_MODE_${e}: i32 = ${I[e]};`).join(""),He=Object.keys(N).map(e=>`const UNIT_${e.toUpperCase()}: i32 = ${N[e]};`).join(""),Je=`${Be}
${Ve}
${He}

const TILE_SIZE: f32 = 512.0;
const PI: f32 = 3.1415926536;
const WORLD_SCALE: f32 = TILE_SIZE / (PI * 2.0);
const ZERO_64_LOW: vec3<f32> = vec3<f32>(0.0, 0.0, 0.0);
const EARTH_RADIUS: f32 = 6370972.0; // meters
const GLOBE_RADIUS: f32 = 256.0;

// -----------------------------------------------------------------------------
// Uniform block (converted from GLSL uniform block)
// -----------------------------------------------------------------------------
struct ProjectUniforms {
  wrapLongitude: i32,
  coordinateSystem: i32,
  commonUnitsPerMeter: vec3<f32>,
  projectionMode: i32,
  scale: f32,
  commonUnitsPerWorldUnit: vec3<f32>,
  commonUnitsPerWorldUnit2: vec3<f32>,
  center: vec4<f32>,
  modelMatrix: mat4x4<f32>,
  viewProjectionMatrix: mat4x4<f32>,
  viewportSize: vec2<f32>,
  devicePixelRatio: f32,
  focalDistance: f32,
  cameraPosition: vec3<f32>,
  coordinateOrigin: vec3<f32>,
  commonOrigin: vec3<f32>,
  pseudoMeters: i32,
};

@group(0) @binding(0)
var<uniform> project: ProjectUniforms;

// -----------------------------------------------------------------------------
// Geometry data
// (In your GLSL code, "geometry" was assumed to be available globally. In WGSL,
// you might supply this via vertex attributes or a uniform. Here we define a
// uniform struct for demonstration.)
// -----------------------------------------------------------------------------

// Structure to carry additional geometry data used by deck.gl filters.
struct Geometry {
  worldPosition: vec3<f32>,
  worldPositionAlt: vec3<f32>,
  position: vec4<f32>,
  normal: vec3<f32>,
  uv: vec2<f32>,
  pickingColor: vec3<f32>,
};

// @group(0) @binding(1)
var<private> geometry: Geometry;
`,Ye=`${Je}

// -----------------------------------------------------------------------------
// Functions
// -----------------------------------------------------------------------------

// Returns an adjustment factor for commonUnitsPerMeter
fn _project_size_at_latitude(lat: f32) -> f32 {
  let y = clamp(lat, -89.9, 89.9);
  return 1.0 / cos(radians(y));
}

// Overloaded version: scales a value in meters at a given latitude.
fn _project_size_at_latitude_m(meters: f32, lat: f32) -> f32 {
  return meters * project.commonUnitsPerMeter.z * _project_size_at_latitude(lat);
}

// Computes a non-linear scale factor based on geometry.
// (Note: This function relies on "geometry" being provided.)
fn project_size() -> f32 {
  if (project.projectionMode == PROJECTION_MODE_WEB_MERCATOR &&
      project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT &&
      project.pseudoMeters == 0) {
    if (geometry.position.w == 0.0) {
      return _project_size_at_latitude(geometry.worldPosition.y);
    }
    let y: f32 = geometry.position.y / TILE_SIZE * 2.0 - 1.0;
    let y2 = y * y;
    let y4 = y2 * y2;
    let y6 = y4 * y2;
    return 1.0 + 4.9348 * y2 + 4.0587 * y4 + 1.5642 * y6;
  }
  return 1.0;
}

// Overloads to scale offsets (meters to world units)
fn project_size_float(meters: f32) -> f32 {
  return meters * project.commonUnitsPerMeter.z * project_size();
}

fn project_size_vec2(meters: vec2<f32>) -> vec2<f32> {
  return meters * project.commonUnitsPerMeter.xy * project_size();
}

fn project_size_vec3(meters: vec3<f32>) -> vec3<f32> {
  return meters * project.commonUnitsPerMeter * project_size();
}

fn project_size_vec4(meters: vec4<f32>) -> vec4<f32> {
  return vec4<f32>(meters.xyz * project.commonUnitsPerMeter, meters.w);
}

// Returns a rotation matrix aligning the z‑axis with the given up vector.
fn project_get_orientation_matrix(up: vec3<f32>) -> mat3x3<f32> {
  let uz = normalize(up);
  let ux = select(
    vec3<f32>(1.0, 0.0, 0.0),
    normalize(vec3<f32>(uz.y, -uz.x, 0.0)),
    abs(uz.z) == 1.0
  );
  let uy = cross(uz, ux);
  return mat3x3<f32>(ux, uy, uz);
}

// Since WGSL does not support "out" parameters, we return a struct.
struct RotationResult {
  needsRotation: bool,
  transform: mat3x3<f32>,
};

fn project_needs_rotation(commonPosition: vec3<f32>) -> RotationResult {
  if (project.projectionMode == PROJECTION_MODE_GLOBE) {
    return RotationResult(true, project_get_orientation_matrix(commonPosition));
  } else {
    return RotationResult(false, mat3x3<f32>());  // identity alternative if needed
  };
}

// Projects a normal vector from the current coordinate system to world space.
fn project_normal(vector: vec3<f32>) -> vec3<f32> {
  let normal_modelspace = project.modelMatrix * vec4<f32>(vector, 0.0);
  var n = normalize(normal_modelspace.xyz * project.commonUnitsPerMeter);
  let rotResult = project_needs_rotation(geometry.position.xyz);
  if (rotResult.needsRotation) {
    n = rotResult.transform * n;
  }
  return n;
}

// Applies a scale offset based on y-offset (dy)
fn project_offset_(offset: vec4<f32>) -> vec4<f32> {
  let dy: f32 = offset.y;
  let commonUnitsPerWorldUnit = project.commonUnitsPerWorldUnit + project.commonUnitsPerWorldUnit2 * dy;
  return vec4<f32>(offset.xyz * commonUnitsPerWorldUnit, offset.w);
}

// Projects lng/lat coordinates to a unit tile [0,1]
fn project_mercator_(lnglat: vec2<f32>) -> vec2<f32> {
  var x = lnglat.x;
  if (project.wrapLongitude != 0) {
    x = ((x + 180.0) % 360.0) - 180.0;
  }
  let y = clamp(lnglat.y, -89.9, 89.9);
  return vec2<f32>(
    radians(x) + PI,
    PI + log(tan(PI * 0.25 + radians(y) * 0.5))
  ) * WORLD_SCALE;
}

// Projects lng/lat/z coordinates for a globe projection.
fn project_globe_(lnglatz: vec3<f32>) -> vec3<f32> {
  let lambda = radians(lnglatz.x);
  let phi = radians(lnglatz.y);
  let cosPhi = cos(phi);
  let D = (lnglatz.z / EARTH_RADIUS + 1.0) * GLOBE_RADIUS;
  return vec3<f32>(
    sin(lambda) * cosPhi,
    -cos(lambda) * cosPhi,
    sin(phi)
  ) * D;
}

// Projects positions (with an optional 64-bit low part) from the input
// coordinate system to the common space.
fn project_position_vec4_f64(position: vec4<f32>, position64Low: vec3<f32>) -> vec4<f32> {
  var position_world = project.modelMatrix * position;

  // Work around for a Mac+NVIDIA bug:
  if (project.projectionMode == PROJECTION_MODE_WEB_MERCATOR) {
    if (project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT) {
      return vec4<f32>(
        project_mercator_(position_world.xy),
        _project_size_at_latitude_m(position_world.z, position_world.y),
        position_world.w
      );
    }
    if (project.coordinateSystem == COORDINATE_SYSTEM_CARTESIAN) {
      position_world = vec4f(position_world.xyz + project.coordinateOrigin, position_world.w);
    }
  }
  if (project.projectionMode == PROJECTION_MODE_GLOBE) {
    if (project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT) {
      return vec4<f32>(
        project_globe_(position_world.xyz),
        position_world.w
      );
    }
  }
  if (project.projectionMode == PROJECTION_MODE_WEB_MERCATOR_AUTO_OFFSET) {
    if (project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT) {
      if (abs(position_world.y - project.coordinateOrigin.y) > 0.25) {
        return vec4<f32>(
          project_mercator_(position_world.xy) - project.commonOrigin.xy,
          project_size_float(position_world.z),
          position_world.w
        );
      }
    }
  }
  if (project.projectionMode == PROJECTION_MODE_IDENTITY ||
      (project.projectionMode == PROJECTION_MODE_WEB_MERCATOR_AUTO_OFFSET &&
       (project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT ||
        project.coordinateSystem == COORDINATE_SYSTEM_CARTESIAN))) {
    position_world = vec4f(position_world.xyz - project.coordinateOrigin, position_world.w);
  }

  return project_offset_(position_world) +
         project_offset_(project.modelMatrix * vec4<f32>(position64Low, 0.0));
}

// Overloaded versions for different input types.
fn project_position_vec4_f32(position: vec4<f32>) -> vec4<f32> {
  return project_position_vec4_f64(position, ZERO_64_LOW);
}

fn project_position_vec3_f64(position: vec3<f32>, position64Low: vec3<f32>) -> vec3<f32> {
  let projected_position = project_position_vec4_f64(vec4<f32>(position, 1.0), position64Low);
  return projected_position.xyz;
}

fn project_position_vec3_f32(position: vec3<f32>) -> vec3<f32> {
  let projected_position = project_position_vec4_f64(vec4<f32>(position, 1.0), ZERO_64_LOW);
  return projected_position.xyz;
}

fn project_position_vec2_f32(position: vec2<f32>) -> vec2<f32> {
  let projected_position = project_position_vec4_f64(vec4<f32>(position, 0.0, 1.0), ZERO_64_LOW);
  return projected_position.xy;
}

// Transforms a common space position to clip space.
fn project_common_position_to_clipspace_with_projection(position: vec4<f32>, viewProjectionMatrix: mat4x4<f32>, center: vec4<f32>) -> vec4<f32> {
  return viewProjectionMatrix * position + center;
}

// Uses the project viewProjectionMatrix and center.
fn project_common_position_to_clipspace(position: vec4<f32>) -> vec4<f32> {
  return project_common_position_to_clipspace_with_projection(position, project.viewProjectionMatrix, project.center);
}

// Returns a clip space offset corresponding to a given number of screen pixels.
fn project_pixel_size_to_clipspace(pixels: vec2<f32>) -> vec2<f32> {
  let offset = pixels / project.viewportSize * project.devicePixelRatio * 2.0;
  return offset * project.focalDistance;
}

fn project_meter_size_to_pixel(meters: f32) -> f32 {
  return project_size_float(meters) * project.scale;
}

fn project_unit_size_to_pixel(size: f32, unit: i32) -> f32 {
  if (unit == UNIT_METERS) {
    return project_meter_size_to_pixel(size);
  } else if (unit == UNIT_COMMON) {
    return size * project.scale;
  }
  // UNIT_PIXELS: no scaling applied.
  return size;
}

fn project_pixel_size_float(pixels: f32) -> f32 {
  return pixels / project.scale;
}

fn project_pixel_size_vec2(pixels: vec2<f32>) -> vec2<f32> {
  return pixels / project.scale;
}
`,Ze=Object.keys(_).map(e=>`const int COORDINATE_SYSTEM_${e} = ${_[e]};`).join(""),Ke=Object.keys(I).map(e=>`const int PROJECTION_MODE_${e} = ${I[e]};`).join(""),Xe=Object.keys(N).map(e=>`const int UNIT_${e.toUpperCase()} = ${N[e]};`).join(""),qe=`${Ze}
${Ke}
${Xe}
uniform projectUniforms {
bool wrapLongitude;
int coordinateSystem;
vec3 commonUnitsPerMeter;
int projectionMode;
float scale;
vec3 commonUnitsPerWorldUnit;
vec3 commonUnitsPerWorldUnit2;
vec4 center;
mat4 modelMatrix;
mat4 viewProjectionMatrix;
vec2 viewportSize;
float devicePixelRatio;
float focalDistance;
vec3 cameraPosition;
vec3 coordinateOrigin;
vec3 commonOrigin;
bool pseudoMeters;
} project;
const float TILE_SIZE = 512.0;
const float PI = 3.1415926536;
const float WORLD_SCALE = TILE_SIZE / (PI * 2.0);
const vec3 ZERO_64_LOW = vec3(0.0);
const float EARTH_RADIUS = 6370972.0;
const float GLOBE_RADIUS = 256.0;
float project_size_at_latitude(float lat) {
float y = clamp(lat, -89.9, 89.9);
return 1.0 / cos(radians(y));
}
float project_size() {
if (project.projectionMode == PROJECTION_MODE_WEB_MERCATOR &&
project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT &&
project.pseudoMeters == false) {
if (geometry.position.w == 0.0) {
return project_size_at_latitude(geometry.worldPosition.y);
}
float y = geometry.position.y / TILE_SIZE * 2.0 - 1.0;
float y2 = y * y;
float y4 = y2 * y2;
float y6 = y4 * y2;
return 1.0 + 4.9348 * y2 + 4.0587 * y4 + 1.5642 * y6;
}
return 1.0;
}
float project_size_at_latitude(float meters, float lat) {
return meters * project.commonUnitsPerMeter.z * project_size_at_latitude(lat);
}
float project_size(float meters) {
return meters * project.commonUnitsPerMeter.z * project_size();
}
vec2 project_size(vec2 meters) {
return meters * project.commonUnitsPerMeter.xy * project_size();
}
vec3 project_size(vec3 meters) {
return meters * project.commonUnitsPerMeter * project_size();
}
vec4 project_size(vec4 meters) {
return vec4(meters.xyz * project.commonUnitsPerMeter, meters.w);
}
mat3 project_get_orientation_matrix(vec3 up) {
vec3 uz = normalize(up);
vec3 ux = abs(uz.z) == 1.0 ? vec3(1.0, 0.0, 0.0) : normalize(vec3(uz.y, -uz.x, 0));
vec3 uy = cross(uz, ux);
return mat3(ux, uy, uz);
}
bool project_needs_rotation(vec3 commonPosition, out mat3 transform) {
if (project.projectionMode == PROJECTION_MODE_GLOBE) {
transform = project_get_orientation_matrix(commonPosition);
return true;
}
return false;
}
vec3 project_normal(vec3 vector) {
vec4 normal_modelspace = project.modelMatrix * vec4(vector, 0.0);
vec3 n = normalize(normal_modelspace.xyz * project.commonUnitsPerMeter);
mat3 rotation;
if (project_needs_rotation(geometry.position.xyz, rotation)) {
n = rotation * n;
}
return n;
}
vec4 project_offset_(vec4 offset) {
float dy = offset.y;
vec3 commonUnitsPerWorldUnit = project.commonUnitsPerWorldUnit + project.commonUnitsPerWorldUnit2 * dy;
return vec4(offset.xyz * commonUnitsPerWorldUnit, offset.w);
}
vec2 project_mercator_(vec2 lnglat) {
float x = lnglat.x;
if (project.wrapLongitude) {
x = mod(x + 180., 360.0) - 180.;
}
float y = clamp(lnglat.y, -89.9, 89.9);
return vec2(
radians(x) + PI,
PI + log(tan_fp32(PI * 0.25 + radians(y) * 0.5))
) * WORLD_SCALE;
}
vec3 project_globe_(vec3 lnglatz) {
float lambda = radians(lnglatz.x);
float phi = radians(lnglatz.y);
float cosPhi = cos(phi);
float D = (lnglatz.z / EARTH_RADIUS + 1.0) * GLOBE_RADIUS;
return vec3(
sin(lambda) * cosPhi,
-cos(lambda) * cosPhi,
sin(phi)
) * D;
}
vec4 project_position(vec4 position, vec3 position64Low) {
vec4 position_world = project.modelMatrix * position;
if (project.projectionMode == PROJECTION_MODE_WEB_MERCATOR) {
if (project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT) {
return vec4(
project_mercator_(position_world.xy),
project_size_at_latitude(position_world.z, position_world.y),
position_world.w
);
}
if (project.coordinateSystem == COORDINATE_SYSTEM_CARTESIAN) {
position_world.xyz += project.coordinateOrigin;
}
}
if (project.projectionMode == PROJECTION_MODE_GLOBE) {
if (project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT) {
return vec4(
project_globe_(position_world.xyz),
position_world.w
);
}
}
if (project.projectionMode == PROJECTION_MODE_WEB_MERCATOR_AUTO_OFFSET) {
if (project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT) {
if (abs(position_world.y - project.coordinateOrigin.y) > 0.25) {
return vec4(
project_mercator_(position_world.xy) - project.commonOrigin.xy,
project_size(position_world.z),
position_world.w
);
}
}
}
if (project.projectionMode == PROJECTION_MODE_IDENTITY ||
(project.projectionMode == PROJECTION_MODE_WEB_MERCATOR_AUTO_OFFSET &&
(project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT ||
project.coordinateSystem == COORDINATE_SYSTEM_CARTESIAN))) {
position_world.xyz -= project.coordinateOrigin;
}
return project_offset_(position_world) + project_offset_(project.modelMatrix * vec4(position64Low, 0.0));
}
vec4 project_position(vec4 position) {
return project_position(position, ZERO_64_LOW);
}
vec3 project_position(vec3 position, vec3 position64Low) {
vec4 projected_position = project_position(vec4(position, 1.0), position64Low);
return projected_position.xyz;
}
vec3 project_position(vec3 position) {
vec4 projected_position = project_position(vec4(position, 1.0), ZERO_64_LOW);
return projected_position.xyz;
}
vec2 project_position(vec2 position) {
vec4 projected_position = project_position(vec4(position, 0.0, 1.0), ZERO_64_LOW);
return projected_position.xy;
}
vec4 project_common_position_to_clipspace(vec4 position, mat4 viewProjectionMatrix, vec4 center) {
return viewProjectionMatrix * position + center;
}
vec4 project_common_position_to_clipspace(vec4 position) {
return project_common_position_to_clipspace(position, project.viewProjectionMatrix, project.center);
}
vec2 project_pixel_size_to_clipspace(vec2 pixels) {
vec2 offset = pixels / project.viewportSize * project.devicePixelRatio * 2.0;
return offset * project.focalDistance;
}
float project_size_to_pixel(float meters) {
return project_size(meters) * project.scale;
}
float project_size_to_pixel(float size, int unit) {
if (unit == UNIT_METERS) return project_size_to_pixel(size);
if (unit == UNIT_COMMON) return size * project.scale;
return size;
}
float project_pixel_size(float pixels) {
return pixels / project.scale;
}
vec2 project_pixel_size(vec2 pixels) {
return pixels / project.scale;
}
`,Qe={};function et(e=Qe){return"viewport"in e?ke(e):{}}const nt={name:"project",dependencies:[he,De],source:Ye,vs:qe,getUniforms:et,uniformTypes:{wrapLongitude:"f32",coordinateSystem:"i32",commonUnitsPerMeter:"vec3<f32>",projectionMode:"i32",scale:"f32",commonUnitsPerWorldUnit:"vec3<f32>",commonUnitsPerWorldUnit2:"vec3<f32>",center:"vec4<f32>",modelMatrix:"mat4x4<f32>",viewProjectionMatrix:"mat4x4<f32>",viewportSize:"vec2<f32>",devicePixelRatio:"f32",focalDistance:"f32",cameraPosition:"vec3<f32>",coordinateOrigin:"vec3<f32>",commonOrigin:"vec3<f32>",pseudoMeters:"f32"}};export{L as S,Y as a,Fe as b,De as c,ke as g,pe as i,we as m,nt as p};
//# sourceMappingURL=project-BTjD2Imj.js.map
