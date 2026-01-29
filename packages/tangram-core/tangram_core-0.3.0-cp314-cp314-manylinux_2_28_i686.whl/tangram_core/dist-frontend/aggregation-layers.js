import{C as Ye}from"./assets/tesselator-CENyUZ2p.js";import{m as ht,B as pt,f as le,L as Ke,d as mt,G as ft,p as V,c as qe,j as vt}from"./assets/layer-DPcO4AXQ.js";import{M as Z,u as xt}from"./assets/shader-Cbdysp2j.js";import{i as F,x as Q,V as ce,b as bt,O as z}from"./assets/deep-equal-BTW2ZN6S.js";import{C as Ze,P as yt,S as Ct}from"./assets/solid-polygon-layer-DJFl_7Ca.js";import{C as St}from"./assets/cube-geometry-v0HQ793i.js";import"./assets/webgl-developer-tools-utTNOsNf.js";import"./assets/assert-cyW4mg7q.js";import"./assets/project-BTjD2Imj.js";import"./assets/array-utils-flat-BBMak426.js";import"./assets/webgl-device-BYRB-GQX.js";import"./assets/_commonjsHelpers-CqkleIqs.js";const Tt="transform_output";class he{device;model;sampler;currentIndex=0;samplerTextureMap=null;bindings=[];resources={};constructor(e,t){this.device=e,this.sampler=e.createSampler({addressModeU:"clamp-to-edge",addressModeV:"clamp-to-edge",minFilter:"nearest",magFilter:"nearest",mipmapFilter:"nearest"}),this.model=new Z(this.device,{id:t.id||xt("texture-transform-model"),fs:t.fs||ht({input:t.targetTextureVarying,inputChannels:t.targetTextureChannels,output:Tt}),vertexCount:t.vertexCount,...t}),this._initialize(t),Object.seal(this)}destroy(){this.model.destroy();for(const e of this.bindings)e.framebuffer?.destroy()}delete(){this.destroy()}run(e){const{framebuffer:t}=this.bindings[this.currentIndex],o=this.device.beginRenderPass({framebuffer:t,...e});this.model.draw(o),o.end(),this.device.submit()}getTargetTexture(){const{targetTexture:e}=this.bindings[this.currentIndex];return e}getFramebuffer(){return this.bindings[this.currentIndex].framebuffer}_initialize(e){this._updateBindings(e)}_updateBindings(e){this.bindings[this.currentIndex]=this._updateBinding(this.bindings[this.currentIndex],e)}_updateBinding(e,{sourceBuffers:t,sourceTextures:o,targetTexture:i}){if(e||(e={sourceBuffers:{},sourceTextures:{},targetTexture:null}),Object.assign(e.sourceTextures,o),Object.assign(e.sourceBuffers,t),i){e.targetTexture=i;const{width:n,height:s}=i;e.framebuffer&&e.framebuffer.destroy(),e.framebuffer=this.device.createFramebuffer({id:"transform-framebuffer",width:n,height:s,colorAttachments:[i]}),e.framebuffer.resize({width:n,height:s})}return e}_setSourceTextureParameters(){const e=this.currentIndex,{sourceTextures:t}=this.bindings[e];for(const o in t)t[o].sampler=this.sampler}}function At({pointCount:r,getBinId:e}){const t=new Map;for(let o=0;o<r;o++){const i=e(o);if(i===null)continue;let n=t.get(String(i));n?n.points.push(o):(n={id:i,index:t.size,points:[o]},t.set(String(i),n))}return Array.from(t.values())}function Pt({bins:r,dimensions:e,target:t}){const o=r.length*e;(!t||t.length<o)&&(t=new Float32Array(o));for(let i=0;i<r.length;i++){const{id:n}=r[i];Array.isArray(n)?t.set(n,i*e):t[i]=n}return t}const wt=r=>r.length,Qe=(r,e)=>{let t=0;for(const o of r)t+=e(o);return t},Nt=(r,e)=>r.length===0?NaN:Qe(r,e)/r.length,_t=(r,e)=>{let t=1/0;for(const o of r){const i=e(o);i<t&&(t=i)}return t},Et=(r,e)=>{let t=-1/0;for(const o of r){const i=e(o);i>t&&(t=i)}return t},Mt={COUNT:wt,SUM:Qe,MEAN:Nt,MIN:_t,MAX:Et};function It({bins:r,getValue:e,operation:t,target:o}){(!o||o.length<r.length)&&(o=new Float32Array(r.length));let i=1/0,n=-1/0;for(let s=0;s<r.length;s++){const{points:c}=r[s];o[s]=t(c,e),o[s]<i&&(i=o[s]),o[s]>n&&(n=o[s])}return{value:o,domain:[i,n]}}function pe(r,e,t){const o={};for(const n of r.sources||[]){const s=e[n];if(s)o[n]=Ot(s);else throw new Error(`Cannot find attribute ${n}`)}const i={};return n=>{for(const s in o)i[s]=o[s](n);return r.getValue(i,n,t)}}function Ot(r){const e=r.value,{offset:t=0,stride:o,size:i}=r.getAccessor(),n=e.BYTES_PER_ELEMENT,s=t/n,c=o?o/n:i;if(i===1)return r.isConstant?()=>e[0]:u=>{const g=s+c*u;return e[g]};let l;return r.isConstant?(l=Array.from(e),()=>l):(l=new Array(i),u=>{const g=s+c*u;for(let f=0;f<i;f++)l[f]=e[g+f];return l})}class G{constructor(e){this.bins=[],this.binIds=null,this.results=[],this.dimensions=e.dimensions,this.channelCount=e.getValue.length,this.props={...e,binOptions:{},pointCount:0,operations:[],customOperations:[],attributes:{}},this.needsUpdate=!0,this.setProps(e)}destroy(){}get binCount(){return this.bins.length}setProps(e){const t=this.props;if(e.binOptions&&(F(e.binOptions,t.binOptions,2)||this.setNeedsUpdate()),e.operations)for(let o=0;o<this.channelCount;o++)e.operations[o]!==t.operations[o]&&this.setNeedsUpdate(o);if(e.customOperations)for(let o=0;o<this.channelCount;o++)!!e.customOperations[o]!=!!t.customOperations[o]&&this.setNeedsUpdate(o);e.pointCount!==void 0&&e.pointCount!==t.pointCount&&this.setNeedsUpdate(),e.attributes&&(e.attributes={...t.attributes,...e.attributes}),Object.assign(this.props,e)}setNeedsUpdate(e){e===void 0?this.needsUpdate=!0:this.needsUpdate!==!0&&(this.needsUpdate=this.needsUpdate||[],this.needsUpdate[e]=!0)}update(){if(this.needsUpdate===!0){this.bins=At({pointCount:this.props.pointCount,getBinId:pe(this.props.getBin,this.props.attributes,this.props.binOptions)});const e=Pt({bins:this.bins,dimensions:this.dimensions,target:this.binIds?.value});this.binIds={value:e,type:"float32",size:this.dimensions}}for(let e=0;e<this.channelCount;e++)if(this.needsUpdate===!0||this.needsUpdate[e]){const t=this.props.customOperations[e]||Mt[this.props.operations[e]],{value:o,domain:i}=It({bins:this.bins,getValue:pe(this.props.getValue[e],this.props.attributes,void 0),operation:t,target:this.results[e]?.value});this.results[e]={value:o,domain:i,type:"float32",size:1},this.props.onUpdate?.({channel:e})}this.needsUpdate=!1}preDraw(){}getBins(){return this.binIds}getResult(e){return this.results[e]}getResultDomain(e){return this.results[e]?.domain??[1/0,-1/0]}getBin(e){const t=this.bins[e];if(!t)return null;const o=new Array(this.channelCount);for(let i=0;i<o.length;i++){const n=this.results[i];o[i]=n?.value[e]}return{id:t.id,value:o,count:t.points.length,pointIndices:t.points}}}function Je(r,e,t){return r.createFramebuffer({width:e,height:t,colorAttachments:[r.createTexture({width:e,height:t,format:"rgba32float",sampler:{minFilter:"nearest",magFilter:"nearest"}})]})}const Lt=`uniform binSorterUniforms {
  ivec4 binIdRange;
  ivec2 targetSize;
} binSorter;
`,Dt={name:"binSorter",vs:Lt,uniformTypes:{binIdRange:"vec4<i32>",targetSize:"vec2<i32>"}},et=[1,2,4,8],me=3e38,Wt={SUM:0,MEAN:0,MIN:0,MAX:0,COUNT:0},Y=1024;class Rt{constructor(e,t){this.binsFBO=null,this.device=e,this.model=zt(e,t)}get texture(){return this.binsFBO?this.binsFBO.colorAttachments[0].texture:null}destroy(){this.model.destroy(),this.binsFBO?.colorAttachments[0].texture.destroy(),this.binsFBO?.destroy()}getBinValues(e){if(!this.binsFBO)return null;const t=e%Y,o=Math.floor(e/Y),i=this.device.readPixelsToArrayWebGL(this.binsFBO,{sourceX:t,sourceY:o,sourceWidth:1,sourceHeight:1}).buffer;return new Float32Array(i)}setDimensions(e,t){const o=Y,i=Math.ceil(e/o);this.binsFBO?this.binsFBO.height<i&&this.binsFBO.resize({width:o,height:i}):this.binsFBO=Je(this.device,o,i);const n={binIdRange:[t[0][0],t[0][1],t[1]?.[0]||0,t[1]?.[1]||0],targetSize:[this.binsFBO.width,this.binsFBO.height]};this.model.shaderInputs.setProps({binSorter:n})}setModelProps(e){const t=this.model;e.attributes&&t.setAttributes(e.attributes),e.constantAttributes&&t.setConstantAttributes(e.constantAttributes),e.vertexCount!==void 0&&t.setVertexCount(e.vertexCount),e.shaderModuleProps&&t.shaderInputs.setProps(e.shaderModuleProps)}update(e){if(!this.binsFBO)return;const t=Bt(e);this._updateBins("SUM",t.SUM+t.MEAN),this._updateBins("MIN",t.MIN),this._updateBins("MAX",t.MAX)}_updateBins(e,t){if(t===0)return;t|=et[3];const o=this.model,i=this.binsFBO,n=e==="MAX"?-me:e==="MIN"?me:0,s=this.device.beginRenderPass({id:`gpu-aggregation-${e}`,framebuffer:i,parameters:{viewport:[0,0,i.width,i.height],colorMask:t},clearColor:[n,n,n,0],clearDepth:!1,clearStencil:!1});o.setParameters({blend:!0,blendColorSrcFactor:"one",blendColorDstFactor:"one",blendAlphaSrcFactor:"one",blendAlphaDstFactor:"one",blendColorOperation:e==="MAX"?"max":e==="MIN"?"min":"add",blendAlphaOperation:"add"}),o.draw(s),s.end()}}function Bt(r){const e={...Wt};for(let t=0;t<r.length;t++){const o=r[t];o&&(e[o]+=et[t])}return e}function zt(r,e){let t=e.vs;e.dimensions===2&&(t+=`
void getBin(out int binId) {
  ivec2 binId2;
  getBin(binId2);
  if (binId2.x < binSorter.binIdRange.x || binId2.x >= binSorter.binIdRange.y) {
    binId = -1;
  } else {
    binId = (binId2.y - binSorter.binIdRange.z) * (binSorter.binIdRange.y - binSorter.binIdRange.x) + binId2.x;
  }
}
`);const o=`#version 300 es
#define SHADER_NAME gpu-aggregation-sort-bins-vertex

${t}

out vec3 v_Value;

void main() {
  int binIndex;
  getBin(binIndex);
  binIndex = binIndex - binSorter.binIdRange.x;
  if (binIndex < 0) {
    gl_Position = vec4(0.);
    return;
  }
  int row = binIndex / binSorter.targetSize.x;
  int col = binIndex - row * binSorter.targetSize.x;
  vec2 position = (vec2(col, row) + 0.5) / vec2(binSorter.targetSize) * 2.0 - 1.0;
  gl_Position = vec4(position, 0.0, 1.0);
  gl_PointSize = 1.0;

#if NUM_CHANNELS == 3
  getValue(v_Value);
#elif NUM_CHANNELS == 2
  getValue(v_Value.xy);
#else
  getValue(v_Value.x);
#endif
}
`,i=`#version 300 es
#define SHADER_NAME gpu-aggregation-sort-bins-fragment

precision highp float;

in vec3 v_Value;
out vec4 fragColor;

void main() {
  fragColor.xyz = v_Value;

  #ifdef MODULE_GEOMETRY
  geometry.uv = vec2(0.);
  DECKGL_FILTER_COLOR(fragColor, geometry);
  #endif

  fragColor.w = 1.0;
}
`;return new Z(r,{bufferLayout:e.bufferLayout,modules:[...e.modules||[],Dt],defines:{...e.defines,NON_INSTANCED_MODEL:1,NUM_CHANNELS:e.channelCount},isInstanced:!1,vs:o,fs:i,topology:"point-list",disableWarnings:!0})}const Vt=`uniform aggregatorTransformUniforms {
  ivec4 binIdRange;
  bvec3 isCount;
  bvec3 isMean;
  float naN;
} aggregatorTransform;
`,Ut={name:"aggregatorTransform",vs:Vt,uniformTypes:{binIdRange:"vec4<i32>",isCount:"vec3<f32>",isMean:"vec3<f32>"}};class Ft{constructor(e,t){this.binBuffer=null,this.valueBuffer=null,this._domains=null,this.device=e,this.channelCount=t.channelCount,this.transform=Gt(e,t),this.domainFBO=Je(e,2,1)}destroy(){this.transform.destroy(),this.binBuffer?.destroy(),this.valueBuffer?.destroy(),this.domainFBO.colorAttachments[0].texture.destroy(),this.domainFBO.destroy()}get domains(){if(!this._domains){const e=this.device.readPixelsToArrayWebGL(this.domainFBO).buffer,t=new Float32Array(e);this._domains=[[-t[4],t[0]],[-t[5],t[1]],[-t[6],t[2]]].slice(0,this.channelCount)}return this._domains}setDimensions(e,t){const{model:o,transformFeedback:i}=this.transform;o.setVertexCount(e);const n={binIdRange:[t[0][0],t[0][1],t[1]?.[0]||0,t[1]?.[1]||0]};o.shaderInputs.setProps({aggregatorTransform:n});const s=e*t.length*4;(!this.binBuffer||this.binBuffer.byteLength<s)&&(this.binBuffer?.destroy(),this.binBuffer=this.device.createBuffer({byteLength:s}),i.setBuffer("binIds",this.binBuffer));const c=e*this.channelCount*4;(!this.valueBuffer||this.valueBuffer.byteLength<c)&&(this.valueBuffer?.destroy(),this.valueBuffer=this.device.createBuffer({byteLength:c}),i.setBuffer("values",this.valueBuffer))}update(e,t){if(!e)return;const o=this.transform,i=this.domainFBO,n=[0,1,2].map(l=>t[l]==="COUNT"?1:0),s=[0,1,2].map(l=>t[l]==="MEAN"?1:0),c={isCount:n,isMean:s,bins:e};o.model.shaderInputs.setProps({aggregatorTransform:c}),o.run({id:"gpu-aggregation-domain",framebuffer:i,parameters:{viewport:[0,0,2,1]},clearColor:[-3e38,-3e38,-3e38,0],clearDepth:!1,clearStencil:!1}),this._domains=null}}function Gt(r,e){const t=`#version 300 es
#define SHADER_NAME gpu-aggregation-domain-vertex

uniform sampler2D bins;

#if NUM_DIMS == 1
out float binIds;
#else
out vec2 binIds;
#endif

#if NUM_CHANNELS == 1
flat out float values;
#elif NUM_CHANNELS == 2
flat out vec2 values;
#else
flat out vec3 values;
#endif

const float NAN = intBitsToFloat(-1);

void main() {
  int row = gl_VertexID / SAMPLER_WIDTH;
  int col = gl_VertexID - row * SAMPLER_WIDTH;
  vec4 weights = texelFetch(bins, ivec2(col, row), 0);
  vec3 value3 = mix(
    mix(weights.rgb, vec3(weights.a), aggregatorTransform.isCount),
    weights.rgb / max(weights.a, 1.0),
    aggregatorTransform.isMean
  );
  if (weights.a == 0.0) {
    value3 = vec3(NAN);
  }

#if NUM_DIMS == 1
  binIds = float(gl_VertexID + aggregatorTransform.binIdRange.x);
#else
  int y = gl_VertexID / (aggregatorTransform.binIdRange.y - aggregatorTransform.binIdRange.x);
  int x = gl_VertexID - y * (aggregatorTransform.binIdRange.y - aggregatorTransform.binIdRange.x);
  binIds.y = float(y + aggregatorTransform.binIdRange.z);
  binIds.x = float(x + aggregatorTransform.binIdRange.x);
#endif

#if NUM_CHANNELS == 3
  values = value3;
#elif NUM_CHANNELS == 2
  values = value3.xy;
#else
  values = value3.x;
#endif

  gl_Position = vec4(0., 0., 0., 1.);
  // This model renders into a 2x1 texture to obtain min and max simultaneously.
  // See comments in fragment shader
  gl_PointSize = 2.0;
}
`,o=`#version 300 es
#define SHADER_NAME gpu-aggregation-domain-fragment

precision highp float;

#if NUM_CHANNELS == 1
flat in float values;
#elif NUM_CHANNELS == 2
flat in vec2 values;
#else
flat in vec3 values;
#endif

out vec4 fragColor;

void main() {
  vec3 value3;
#if NUM_CHANNELS == 3
  value3 = values;
#elif NUM_CHANNELS == 2
  value3.xy = values;
#else
  value3.x = values;
#endif
  if (isnan(value3.x)) discard;
  // This shader renders into a 2x1 texture with blending=max
  // The left pixel yields the max value of each channel
  // The right pixel yields the min value of each channel
  if (gl_FragCoord.x < 1.0) {
    fragColor = vec4(value3, 1.0);
  } else {
    fragColor = vec4(-value3, 1.0);
  }
}
`;return new pt(r,{vs:t,fs:o,topology:"point-list",modules:[Ut],parameters:{blend:!0,blendColorSrcFactor:"one",blendColorDstFactor:"one",blendColorOperation:"max",blendAlphaSrcFactor:"one",blendAlphaDstFactor:"one",blendAlphaOperation:"max"},defines:{NUM_DIMS:e.dimensions,NUM_CHANNELS:e.channelCount,SAMPLER_WIDTH:Y},varyings:["binIds","values"],disableWarnings:!0})}class P{static isSupported(e){return e.features.has("float32-renderable-webgl")&&e.features.has("texture-blend-float-webgl")}constructor(e,t){this.binCount=0,this.binIds=null,this.results=[],this.device=e,this.dimensions=t.dimensions,this.channelCount=t.channelCount,this.props={...t,pointCount:0,binIdRange:[[0,0]],operations:[],attributes:{},binOptions:{}},this.needsUpdate=new Array(this.channelCount).fill(!0),this.binSorter=new Rt(e,t),this.aggregationTransform=new Ft(e,t),this.setProps(t)}getBins(){const e=this.aggregationTransform.binBuffer;return e?(this.binIds?.buffer!==e&&(this.binIds={buffer:e,type:"float32",size:this.dimensions}),this.binIds):null}getResult(e){const t=this.aggregationTransform.valueBuffer;return!t||e>=this.channelCount?null:(this.results[e]?.buffer!==t&&(this.results[e]={buffer:t,type:"float32",size:1,stride:this.channelCount*4,offset:e*4}),this.results[e])}getResultDomain(e){return this.aggregationTransform.domains[e]}getBin(e){if(e<0||e>=this.binCount)return null;const{binIdRange:t}=this.props;let o;if(this.dimensions===1)o=[e+t[0][0]];else{const[[c,l],[u]]=t,g=l-c;o=[e%g+c,Math.floor(e/g)+u]}const i=this.binSorter.getBinValues(e);if(!i)return null;const n=i[3],s=[];for(let c=0;c<this.channelCount;c++){const l=this.props.operations[c];l==="COUNT"?s[c]=n:n===0?s[c]=NaN:s[c]=l==="MEAN"?i[c]/n:i[c]}return{id:o,value:s,count:n}}destroy(){this.binSorter.destroy(),this.aggregationTransform.destroy()}setProps(e){const t=this.props;if("binIdRange"in e&&!F(e.binIdRange,t.binIdRange,2)){const o=e.binIdRange;if(Q.assert(o.length===this.dimensions),this.dimensions===1){const[[i,n]]=o;this.binCount=n-i}else{const[[i,n],[s,c]]=o;this.binCount=(n-i)*(c-s)}this.binSorter.setDimensions(this.binCount,o),this.aggregationTransform.setDimensions(this.binCount,o),this.setNeedsUpdate()}if(e.operations)for(let o=0;o<this.channelCount;o++)e.operations[o]!==t.operations[o]&&this.setNeedsUpdate(o);if(e.pointCount!==void 0&&e.pointCount!==t.pointCount&&(this.binSorter.setModelProps({vertexCount:e.pointCount}),this.setNeedsUpdate()),e.binOptions&&(F(e.binOptions,t.binOptions,2)||this.setNeedsUpdate(),this.binSorter.model.shaderInputs.setProps({binOptions:e.binOptions})),e.attributes){const o={},i={};for(const n of Object.values(e.attributes))for(const[s,c]of Object.entries(n.getValue()))ArrayBuffer.isView(c)?i[s]=c:c&&(o[s]=c);this.binSorter.setModelProps({attributes:o,constantAttributes:i})}e.shaderModuleProps&&this.binSorter.setModelProps({shaderModuleProps:e.shaderModuleProps}),Object.assign(this.props,e)}setNeedsUpdate(e){e===void 0?this.needsUpdate.fill(!0):this.needsUpdate[e]=!0}update(){}preDraw(){if(!this.needsUpdate.some(Boolean))return;const{operations:e}=this.props,t=this.needsUpdate.map((o,i)=>o?e[i]:null);this.binSorter.update(t),this.aggregationTransform.update(this.binSorter.texture,e);for(let o=0;o<this.channelCount;o++)this.needsUpdate[o]&&(this.needsUpdate[o]=!1,this.props.onUpdate?.({channel:o}))}}let j=class extends Ye{get isDrawable(){return!0}initializeState(){this.getAttributeManager().remove(["instancePickingColors"])}updateState(e){super.updateState(e);const t=this.getAggregatorType();if(e.changeFlags.extensionsChanged||this.state.aggregatorType!==t){this.state.aggregator?.destroy();const o=this.createAggregator(t);return o.setProps({attributes:this.getAttributeManager()?.attributes}),this.setState({aggregator:o,aggregatorType:t}),!0}return!1}finalizeState(e){super.finalizeState(e),this.state.aggregator.destroy()}updateAttributes(e){const{aggregator:t}=this.state;t.setProps({attributes:e});for(const o in e)this.onAttributeChange(o);t.update()}draw({shaderModuleProps:e}){const{aggregator:t}=this.state;t.setProps({shaderModuleProps:e}),t.preDraw()}_getAttributeManager(){return new le(this.context.device,{id:this.props.id,stats:this.context.stats})}};j.layerName="AggregationLayer";const J=[[255,255,178],[254,217,118],[254,178,76],[253,141,60],[240,59,32],[189,0,38]];function tt(r,e=!1,t=Float32Array){let o;if(Number.isFinite(r[0]))o=new t(r);else{o=new t(r.length*4);let i=0;for(let n=0;n<r.length;n++){const s=r[n];o[i++]=s[0],o[i++]=s[1],o[i++]=s[2],o[i++]=Number.isFinite(s[3])?s[3]:255}}if(e)for(let i=0;i<o.length;i++)o[i]/=255;return o}const K={linear:"linear",quantile:"nearest",quantize:"nearest",ordinal:"nearest"};function ue(r,e){r.setSampler({minFilter:K[e],magFilter:K[e]})}function ge(r,e,t="linear"){const o=tt(e,!1,Uint8Array);return r.createTexture({format:"rgba8unorm",sampler:{minFilter:K[t],magFilter:K[t],addressModeU:"clamp-to-edge",addressModeV:"clamp-to-edge"},data:o,width:o.length/4,height:1})}const jt=`#version 300 es
#define SHADER_NAME screen-grid-layer-vertex-shader
#define RANGE_COUNT 6
in vec2 positions;
in vec2 instancePositions;
in float instanceWeights;
in vec3 instancePickingColors;
uniform sampler2D colorRange;
out vec4 vColor;
vec4 interp(float value, vec2 domain, sampler2D range) {
float r = (value - domain.x) / (domain.y - domain.x);
return texture(range, vec2(r, 0.5));
}
void main(void) {
if (isnan(instanceWeights)) {
gl_Position = vec4(0.);
return;
}
vec2 pos = instancePositions * screenGrid.gridSizeClipspace + positions * screenGrid.cellSizeClipspace;
pos.x = pos.x - 1.0;
pos.y = 1.0 - pos.y;
gl_Position = vec4(pos, 0., 1.);
vColor = interp(instanceWeights, screenGrid.colorDomain, colorRange);
vColor.a *= layer.opacity;
picking_setPickingColor(instancePickingColors);
}
`,Ht=`#version 300 es
#define SHADER_NAME screen-grid-layer-fragment-shader
precision highp float;
in vec4 vColor;
out vec4 fragColor;
void main(void) {
fragColor = vColor;
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,kt=`uniform screenGridUniforms {
  vec2 cellSizeClipspace;
  vec2 gridSizeClipspace;
  vec2 colorDomain;
} screenGrid;
`,$t={name:"screenGrid",vs:kt,uniformTypes:{cellSizeClipspace:"vec2<f32>",gridSizeClipspace:"vec2<f32>",colorDomain:"vec2<f32>"}};class ot extends Ke{getShaders(){return super.getShaders({vs:jt,fs:Ht,modules:[mt,$t]})}initializeState(){this.getAttributeManager().addInstanced({instancePositions:{size:2,type:"float32",accessor:"getBin"},instanceWeights:{size:1,type:"float32",accessor:"getWeight"}}),this.state.model=this._getModel()}updateState(e){super.updateState(e);const{props:t,oldProps:o,changeFlags:i}=e,n=this.state.model;if(o.colorRange!==t.colorRange){this.state.colorTexture?.destroy(),this.state.colorTexture=ge(this.context.device,t.colorRange,t.colorScaleType);const s={colorRange:this.state.colorTexture};n.shaderInputs.setProps({screenGrid:s})}else o.colorScaleType!==t.colorScaleType&&ue(this.state.colorTexture,t.colorScaleType);if(o.cellMarginPixels!==t.cellMarginPixels||o.cellSizePixels!==t.cellSizePixels||i.viewportChanged){const{width:s,height:c}=this.context.viewport,{cellSizePixels:l,cellMarginPixels:u}=this.props,g=Math.max(l-u,0),f={gridSizeClipspace:[l/s*2,l/c*2],cellSizeClipspace:[g/s*2,g/c*2]};n.shaderInputs.setProps({screenGrid:f})}}finalizeState(e){super.finalizeState(e),this.state.colorTexture?.destroy()}draw({uniforms:e}){const t=this.props.colorDomain(),o=this.state.model,i={colorDomain:t};o.shaderInputs.setProps({screenGrid:i}),o.draw(this.context.renderPass)}_getModel(){return new Z(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),geometry:new ft({topology:"triangle-strip",attributes:{positions:{value:new Float32Array([0,0,1,0,0,1,1,1]),size:2}}}),isInstanced:!0})}}ot.layerName="ScreenGridCellLayer";const Xt=`uniform binOptionsUniforms {
  float cellSizePixels;
} binOptions;
`,Yt={name:"binOptions",vs:Xt,uniformTypes:{cellSizePixels:"f32"}},Kt={cellSizePixels:{type:"number",value:100,min:1},cellMarginPixels:{type:"number",value:2,min:0},colorRange:J,colorScaleType:"linear",getPosition:{type:"accessor",value:r=>r.position},getWeight:{type:"accessor",value:1},gpuAggregation:!0,aggregation:"SUM"};class it extends j{getAggregatorType(){return this.props.gpuAggregation&&P.isSupported(this.context.device)?"gpu":"cpu"}createAggregator(e){return e==="cpu"||!P.isSupported(this.context.device)?new G({dimensions:2,getBin:{sources:["positions"],getValue:({positions:t},o,i)=>{const n=this.context.viewport,s=n.project(t),c=i.cellSizePixels;return s[0]<0||s[0]>=n.width||s[1]<0||s[1]>=n.height?null:[Math.floor(s[0]/c),Math.floor(s[1]/c)]}},getValue:[{sources:["counts"],getValue:({counts:t})=>t}]}):new P(this.context.device,{dimensions:2,channelCount:1,bufferLayout:this.getAttributeManager().getBufferLayouts({isInstanced:!1}),...super.getShaders({modules:[V,Yt],vs:`
  in vec3 positions;
  in vec3 positions64Low;
  in float counts;
  
  void getBin(out ivec2 binId) {
    vec4 pos = project_position_to_clipspace(positions, positions64Low, vec3(0.0));
    vec2 screenCoords = vec2(pos.x / pos.w + 1.0, 1.0 - pos.y / pos.w) / 2.0 * project.viewportSize / project.devicePixelRatio;
    vec2 gridCoords = floor(screenCoords / binOptions.cellSizePixels);
    binId = ivec2(gridCoords);
  }
  void getValue(out float weight) {
    weight = counts;
  }
  `})})}initializeState(){super.initializeState(),this.getAttributeManager().add({positions:{size:3,accessor:"getPosition",type:"float64",fp64:this.use64bitPositions()},counts:{size:1,accessor:"getWeight"}})}shouldUpdateState({changeFlags:e}){return e.somethingChanged}updateState(e){const t=super.updateState(e),{props:o,oldProps:i,changeFlags:n}=e,{cellSizePixels:s,aggregation:c}=o;if(t||n.dataChanged||n.updateTriggersChanged||n.viewportChanged||c!==i.aggregation||s!==i.cellSizePixels){const{width:l,height:u}=this.context.viewport,{aggregator:g}=this.state;g instanceof P&&g.setProps({binIdRange:[[0,Math.ceil(l/s)],[0,Math.ceil(u/s)]]}),g.setProps({pointCount:this.getNumInstances(),operations:[c],binOptions:{cellSizePixels:s}})}return n.viewportChanged&&this.state.aggregator.setNeedsUpdate(),t}onAttributeChange(e){const{aggregator:t}=this.state;switch(e){case"positions":t.setNeedsUpdate();break;case"counts":t.setNeedsUpdate(0);break}}renderLayers(){const{aggregator:e}=this.state,t=this.getSubLayerClass("cells",ot),o=e.getBins(),i=e.getResult(0);return new t(this.props,this.getSubLayerProps({id:"cell-layer"}),{data:{length:e.binCount,attributes:{getBin:o,getWeight:i}},dataComparator:(n,s)=>n.length===s.length,updateTriggers:{getBin:[o],getWeight:[i]},parameters:{depthWriteEnabled:!1,...this.props.parameters},colorDomain:()=>this.props.colorDomain||e.getResultDomain(0),extensions:[]})}getPickingInfo(e){const t=e.info,{index:o}=t;if(o>=0){const i=this.state.aggregator.getBin(o);let n;i&&(n={col:i.id[0],row:i.id[1],value:i.value[0],count:i.count},i.pointIndices&&(n.pointIndices=i.pointIndices,n.points=Array.isArray(this.props.data)?i.pointIndices.map(s=>this.props.data[s]):[])),t.object=n}return t}}it.layerName="ScreenGridLayer";it.defaultProps=Kt;class q{constructor(e,t){this.props={scaleType:"linear",lowerPercentile:0,upperPercentile:100},this.domain=null,this.cutoff=null,this.input=e,this.inputLength=t,this.attribute=e}getScalePercentile(){if(!this._percentile){const e=fe(this.input,this.inputLength);this._percentile=Zt(e)}return this._percentile}getScaleOrdinal(){if(!this._ordinal){const e=fe(this.input,this.inputLength);this._ordinal=qt(e)}return this._ordinal}getCutoff({scaleType:e,lowerPercentile:t,upperPercentile:o}){if(e==="quantile")return[t,o-1];if(t>0||o<100){const{domain:i}=this.getScalePercentile();let n=i[Math.floor(t)-1]??-1/0,s=i[Math.floor(o)-1]??1/0;if(e==="ordinal"){const{domain:c}=this.getScaleOrdinal();n=c.findIndex(l=>l>=n),s=c.findIndex(l=>l>s)-1,s===-2&&(s=c.length-1)}return[n,s]}return null}update(e){const t=this.props;if(e.scaleType!==t.scaleType)switch(e.scaleType){case"quantile":{const{attribute:o}=this.getScalePercentile();this.attribute=o,this.domain=[0,99];break}case"ordinal":{const{attribute:o,domain:i}=this.getScaleOrdinal();this.attribute=o,this.domain=[0,i.length-1];break}default:this.attribute=this.input,this.domain=null}return(e.scaleType!==t.scaleType||e.lowerPercentile!==t.lowerPercentile||e.upperPercentile!==t.upperPercentile)&&(this.cutoff=this.getCutoff(e)),this.props=e,this}}function qt(r){const e=new Set;for(const i of r)Number.isFinite(i)&&e.add(i);const t=Array.from(e).sort(),o=new Map;for(let i=0;i<t.length;i++)o.set(t[i],i);return{attribute:{value:r.map(i=>Number.isFinite(i)?o.get(i):NaN),type:"float32",size:1},domain:t}}function Zt(r,e=100){const t=Array.from(r).filter(Number.isFinite).sort(Qt);let o=0;const i=Math.max(1,e),n=new Array(i-1);for(;++o<i;)n[o-1]=Jt(t,o/i);return{attribute:{value:r.map(s=>Number.isFinite(s)?eo(n,s):NaN),type:"float32",size:1},domain:n}}function fe(r,e){const t=(r.stride??4)/4,o=(r.offset??0)/4;let i=r.value;if(!i){const s=r.buffer?.readSyncWebGL(0,t*4*e);s&&(i=new Float32Array(s.buffer),r.value=i)}if(t===1)return i.subarray(0,e);const n=new Float32Array(e);for(let s=0;s<e;s++)n[s]=i[s*t+o];return n}function Qt(r,e){return r-e}function Jt(r,e){const t=r.length;if(e<=0||t<2)return r[0];if(e>=1)return r[t-1];const o=(t-1)*e,i=Math.floor(o),n=r[i],s=r[i+1];return n+(s-n)*(o-i)}function eo(r,e){let t=0,o=r.length;for(;t<o;){const i=t+o>>>1;r[i]>e?o=i:t=i+1}return t}function de({dataBounds:r,getBinId:e,padding:t=0}){const o=[r[0],r[1],[r[0][0],r[1][1]],[r[1][0],r[0][1]]].map(l=>e(l)),i=Math.min(...o.map(l=>l[0]))-t,n=Math.min(...o.map(l=>l[1]))-t,s=Math.max(...o.map(l=>l[0]))+t+1,c=Math.max(...o.map(l=>l[1]))+t+1;return[[i,s],[n,c]]}const nt=Math.PI/3,ee=2*Math.sin(nt),te=1.5,to=Array.from({length:6},(r,e)=>{const t=e*nt;return[Math.sin(t),-Math.cos(t)]});function ne([r,e],t){let o=Math.round(e=e/t/te),i=Math.round(r=r/t/ee-(o&1)/2);const n=e-o;if(Math.abs(n)*3>1){const s=r-i,c=i+(r<i?-1:1)/2,l=o+(e<o?-1:1),u=r-c,g=e-l;s*s+n*n>u*u+g*g&&(i=c+(o&1?1:-1)/2,o=l)}return[i,o]}const oo=`
const vec2 DIST = vec2(${ee}, ${te});

ivec2 pointToHexbin(vec2 p, float radius) {
  p /= radius * DIST;
  float pj = round(p.y);
  float pjm2 = mod(pj, 2.0);
  p.x -= pjm2 * 0.5;
  float pi = round(p.x);
  vec2 d1 = p - vec2(pi, pj);

  if (abs(d1.y) * 3. > 1.) {
    vec2 v2 = step(0.0, d1) - 0.5;
    v2.y *= 2.0;
    vec2 d2 = d1 - v2;
    if (dot(d1, d1) > dot(d2, d2)) {
      pi += v2.x + pjm2 - 0.5;
      pj += v2.y;
    }
  }
  return ivec2(pi, pj);
}
`;function ve([r,e],t){return[(r+(e&1)/2)*t*ee,e*t*te]}const io=`
const vec2 DIST = vec2(${ee}, ${te});

vec2 hexbinCentroid(vec2 binId, float radius) {
  binId.x += fract(binId.y * 0.5);
  return binId * DIST * radius;
}
`,no=`#version 300 es
#define SHADER_NAME hexagon-cell-layer-vertex-shader
in vec3 positions;
in vec3 normals;
in vec2 instancePositions;
in float instanceElevationValues;
in float instanceColorValues;
in vec3 instancePickingColors;
uniform sampler2D colorRange;
out vec4 vColor;
${io}
float interp(float value, vec2 domain, vec2 range) {
float r = min(max((value - domain.x) / (domain.y - domain.x), 0.), 1.);
return mix(range.x, range.y, r);
}
vec4 interp(float value, vec2 domain, sampler2D range) {
float r = (value - domain.x) / (domain.y - domain.x);
return texture(range, vec2(r, 0.5));
}
void main(void) {
geometry.pickingColor = instancePickingColors;
if (isnan(instanceColorValues) ||
instanceColorValues < hexagon.colorDomain.z ||
instanceColorValues > hexagon.colorDomain.w ||
instanceElevationValues < hexagon.elevationDomain.z ||
instanceElevationValues > hexagon.elevationDomain.w
) {
gl_Position = vec4(0.);
return;
}
vec2 commonPosition = hexbinCentroid(instancePositions, column.radius) + (hexagon.originCommon - project.commonOrigin.xy);
commonPosition += positions.xy * column.radius * column.coverage;
geometry.position = vec4(commonPosition, 0.0, 1.0);
geometry.normal = project_normal(normals);
float elevation = 0.0;
if (column.extruded) {
elevation = interp(instanceElevationValues, hexagon.elevationDomain.xy, hexagon.elevationRange);
elevation = project_size(elevation);
geometry.position.z = (positions.z + 1.0) / 2.0 * elevation;
}
gl_Position = project_common_position_to_clipspace(geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
vColor = interp(instanceColorValues, hexagon.colorDomain.xy, colorRange);
vColor.a *= layer.opacity;
if (column.extruded) {
vColor.rgb = lighting_getLightColor(vColor.rgb, project.cameraPosition, geometry.position.xyz, geometry.normal);
}
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,so=`uniform hexagonUniforms {
  vec4 colorDomain;
  vec4 elevationDomain;
  vec2 elevationRange;
  vec2 originCommon;
} hexagon;
`,ro={name:"hexagon",vs:so,uniformTypes:{colorDomain:"vec4<f32>",elevationDomain:"vec4<f32>",elevationRange:"vec2<f32>",originCommon:"vec2<f32>"}};class st extends Ze{getShaders(){const e=super.getShaders();return e.modules.push(ro),{...e,vs:no}}initializeState(){super.initializeState();const e=this.getAttributeManager();e.remove(["instanceElevations","instanceFillColors","instanceLineColors","instanceStrokeWidths"]),e.addInstanced({instancePositions:{size:2,type:"float32",accessor:"getBin"},instanceColorValues:{size:1,type:"float32",accessor:"getColorValue"},instanceElevationValues:{size:1,type:"float32",accessor:"getElevationValue"}})}updateState(e){super.updateState(e);const{props:t,oldProps:o}=e,i=this.state.fillModel;if(o.colorRange!==t.colorRange){this.state.colorTexture?.destroy(),this.state.colorTexture=ge(this.context.device,t.colorRange,t.colorScaleType);const n={colorRange:this.state.colorTexture};i.shaderInputs.setProps({hexagon:n})}else o.colorScaleType!==t.colorScaleType&&ue(this.state.colorTexture,t.colorScaleType)}finalizeState(e){super.finalizeState(e),this.state.colorTexture?.destroy()}draw({uniforms:e}){const{radius:t,hexOriginCommon:o,elevationRange:i,elevationScale:n,extruded:s,coverage:c,colorDomain:l,elevationDomain:u}=this.props,g=this.props.colorCutoff||[-1/0,1/0],f=this.props.elevationCutoff||[-1/0,1/0],m=this.state.fillModel;m.vertexArray.indexBuffer&&m.setIndexBuffer(null),m.setVertexCount(this.state.fillVertexCount);const v={colorDomain:[Math.max(l[0],g[0]),Math.min(l[1],g[1]),Math.max(l[0]-1,g[0]),Math.min(l[1]+1,g[1])],elevationDomain:[Math.max(u[0],f[0]),Math.min(u[1],f[1]),Math.max(u[0]-1,f[0]),Math.min(u[1]+1,f[1])],elevationRange:[i[0]*n,i[1]*n],originCommon:o};m.shaderInputs.setProps({column:{extruded:s,coverage:c,radius:t},hexagon:v}),m.draw(this.context.renderPass)}}st.layerName="HexagonCellLayer";const ao=`uniform binOptionsUniforms {
  vec2 hexOriginCommon;
  float radiusCommon;
} binOptions;
`,lo={name:"binOptions",vs:ao,uniformTypes:{hexOriginCommon:"vec2<f32>",radiusCommon:"f32"}};function xe(){}const co={gpuAggregation:!0,colorDomain:null,colorRange:J,getColorValue:{type:"accessor",value:null},getColorWeight:{type:"accessor",value:1},colorAggregation:"SUM",lowerPercentile:{type:"number",min:0,max:100,value:0},upperPercentile:{type:"number",min:0,max:100,value:100},colorScaleType:"quantize",onSetColorDomain:xe,elevationDomain:null,elevationRange:[0,1e3],getElevationValue:{type:"accessor",value:null},getElevationWeight:{type:"accessor",value:1},elevationAggregation:"SUM",elevationScale:{type:"number",min:0,value:1},elevationLowerPercentile:{type:"number",min:0,max:100,value:0},elevationUpperPercentile:{type:"number",min:0,max:100,value:100},elevationScaleType:"linear",onSetElevationDomain:xe,radius:{type:"number",min:1,value:1e3},coverage:{type:"number",min:0,max:1,value:1},getPosition:{type:"accessor",value:r=>r.position},hexagonAggregator:{type:"function",optional:!0,value:null},extruded:!1,material:!0};class rt extends j{getAggregatorType(){const{gpuAggregation:e,hexagonAggregator:t,getColorValue:o,getElevationValue:i}=this.props;return e&&(t||o||i)?(Q.warn("Features not supported by GPU aggregation, falling back to CPU")(),"cpu"):e&&P.isSupported(this.context.device)?"gpu":"cpu"}createAggregator(e){if(e==="cpu"){const{hexagonAggregator:t,radius:o}=this.props;return new G({dimensions:2,getBin:{sources:["positions"],getValue:({positions:i},n,s)=>{if(t)return t(i,o);const l=this.state.aggregatorViewport.projectPosition(i),{radiusCommon:u,hexOriginCommon:g}=s;return ne([l[0]-g[0],l[1]-g[1]],u)}},getValue:[{sources:["colorWeights"],getValue:({colorWeights:i})=>i},{sources:["elevationWeights"],getValue:({elevationWeights:i})=>i}]})}return new P(this.context.device,{dimensions:2,channelCount:2,bufferLayout:this.getAttributeManager().getBufferLayouts({isInstanced:!1}),...super.getShaders({modules:[V,lo],vs:`
  in vec3 positions;
  in vec3 positions64Low;
  in float colorWeights;
  in float elevationWeights;
  
  ${oo}

  void getBin(out ivec2 binId) {
    vec3 positionCommon = project_position(positions, positions64Low);
    binId = pointToHexbin(positionCommon.xy, binOptions.radiusCommon);
  }
  void getValue(out vec2 value) {
    value = vec2(colorWeights, elevationWeights);
  }
  `})})}initializeState(){super.initializeState(),this.getAttributeManager().add({positions:{size:3,accessor:"getPosition",type:"float64",fp64:this.use64bitPositions()},colorWeights:{size:1,accessor:"getColorWeight"},elevationWeights:{size:1,accessor:"getElevationWeight"}})}updateState(e){const t=super.updateState(e),{props:o,oldProps:i,changeFlags:n}=e,{aggregator:s}=this.state;if((n.dataChanged||!this.state.dataAsArray)&&(o.getColorValue||o.getElevationValue)&&(this.state.dataAsArray=Array.from(qe(o.data).iterable)),t||n.dataChanged||o.radius!==i.radius||o.getColorValue!==i.getColorValue||o.getElevationValue!==i.getElevationValue||o.colorAggregation!==i.colorAggregation||o.elevationAggregation!==i.elevationAggregation){this._updateBinOptions();const{radiusCommon:c,hexOriginCommon:l,binIdRange:u,dataAsArray:g}=this.state;if(s.setProps({binIdRange:u,pointCount:this.getNumInstances(),operations:[o.colorAggregation,o.elevationAggregation],binOptions:{radiusCommon:c,hexOriginCommon:l},onUpdate:this._onAggregationUpdate.bind(this)}),g){const{getColorValue:f,getElevationValue:m}=this.props;s.setProps({customOperations:[f&&(v=>f(v.map(x=>g[x]),{indices:v,data:o.data})),m&&(v=>m(v.map(x=>g[x]),{indices:v,data:o.data}))]})}}return n.updateTriggersChanged&&n.updateTriggersChanged.getColorValue&&s.setNeedsUpdate(0),n.updateTriggersChanged&&n.updateTriggersChanged.getElevationValue&&s.setNeedsUpdate(1),t}_updateBinOptions(){const e=this.getBounds();let t=1,o=[0,0],i=[[0,1],[0,1]],n=this.context.viewport;if(e&&Number.isFinite(e[0][0])){let s=[(e[0][0]+e[1][0])/2,(e[0][1]+e[1][1])/2];const{radius:c}=this.props,{unitsPerMeter:l}=n.getDistanceScales(s);t=l[0]*c;const u=ne(n.projectFlat(s),t);s=n.unprojectFlat(ve(u,t));const g=n.constructor;n=n.isGeospatial?new g({longitude:s[0],latitude:s[1],zoom:12}):new ce({position:[s[0],s[1],0],zoom:12}),o=[Math.fround(n.center[0]),Math.fround(n.center[1])],i=de({dataBounds:e,getBinId:f=>{const m=n.projectFlat(f);return m[0]-=o[0],m[1]-=o[1],ne(m,t)},padding:1})}this.setState({radiusCommon:t,hexOriginCommon:o,binIdRange:i,aggregatorViewport:n})}draw(e){e.shaderModuleProps.project&&(e.shaderModuleProps.project.viewport=this.state.aggregatorViewport),super.draw(e)}_onAggregationUpdate({channel:e}){const t=this.getCurrentLayer().props,{aggregator:o}=this.state;if(e===0){const i=o.getResult(0);this.setState({colors:new q(i,o.binCount)}),t.onSetColorDomain(o.getResultDomain(0))}else if(e===1){const i=o.getResult(1);this.setState({elevations:new q(i,o.binCount)}),t.onSetElevationDomain(o.getResultDomain(1))}}onAttributeChange(e){const{aggregator:t}=this.state;switch(e){case"positions":t.setNeedsUpdate(),this._updateBinOptions();const{radiusCommon:o,hexOriginCommon:i,binIdRange:n}=this.state;t.setProps({binIdRange:n,binOptions:{radiusCommon:o,hexOriginCommon:i}});break;case"colorWeights":t.setNeedsUpdate(0);break;case"elevationWeights":t.setNeedsUpdate(1);break}}renderLayers(){const{aggregator:e,radiusCommon:t,hexOriginCommon:o}=this.state,{elevationScale:i,colorRange:n,elevationRange:s,extruded:c,coverage:l,material:u,transitions:g,colorScaleType:f,lowerPercentile:m,upperPercentile:v,colorDomain:x,elevationScaleType:b,elevationLowerPercentile:S,elevationUpperPercentile:C,elevationDomain:w}=this.props,y=this.getSubLayerClass("cells",st),N=e.getBins(),T=this.state.colors?.update({scaleType:f,lowerPercentile:m,upperPercentile:v}),A=this.state.elevations?.update({scaleType:b,lowerPercentile:S,upperPercentile:C});return!T||!A?null:new y(this.getSubLayerProps({id:"cells"}),{data:{length:e.binCount,attributes:{getBin:N,getColorValue:T.attribute,getElevationValue:A.attribute}},dataComparator:(oe,ie)=>oe.length===ie.length,updateTriggers:{getBin:[N],getColorValue:[T.attribute],getElevationValue:[A.attribute]},diskResolution:6,vertices:to,radius:t,hexOriginCommon:o,elevationScale:i,colorRange:n,colorScaleType:f,elevationRange:s,extruded:c,coverage:l,material:u,colorDomain:T.domain||x||e.getResultDomain(0),elevationDomain:A.domain||w||e.getResultDomain(1),colorCutoff:T.cutoff,elevationCutoff:A.cutoff,transitions:g&&{getFillColor:g.getColorValue||g.getColorWeight,getElevation:g.getElevationValue||g.getElevationWeight},extensions:[]})}getPickingInfo(e){const t=e.info,{index:o}=t;if(o>=0){const i=this.state.aggregator.getBin(o);let n;if(i){const s=ve(i.id,this.state.radiusCommon),c=this.context.viewport.unprojectFlat(s);n={col:i.id[0],row:i.id[1],position:c,colorValue:i.value[0],elevationValue:i.value[1],count:i.count},i.pointIndices&&(n.pointIndices=i.pointIndices,n.points=Array.isArray(this.props.data)?i.pointIndices.map(l=>this.props.data[l]):[])}t.object=n}return t}}rt.layerName="HexagonLayer";rt.defaultProps=co;const d=.5,p=1/6,a={N:[0,d],E:[d,0],S:[0,-d],W:[-d,0],NE:[d,d],NW:[-d,d],SE:[d,-d],SW:[-d,-d]},_=[a.W,a.SW,a.S],E=[a.S,a.SE,a.E],M=[a.E,a.NE,a.N],I=[a.NW,a.W,a.N],O=[[-d,p],[-d,-p],[-p,-d],[p,-d]],L=[[-p,-d],[p,-d],[d,-p],[d,p]],D=[[d,-p],[d,p],[p,d],[-p,d]],W=[[-d,p],[-d,-p],[p,d],[-p,d]],be=[a.W,a.SW,a.SE,a.E],ye=[a.S,a.SE,a.NE,a.N],Ce=[a.NW,a.W,a.E,a.NE],Se=[a.NW,a.SW,a.S,a.N],Te=[[-d,p],[-d,-p],[d,-p],[d,p]],Ae=[[-p,-d],[p,-d],[p,d],[-p,d]],uo=[a.NW,a.SW,a.SE,a.NE],Pe=[a.NW,a.SW,a.SE,a.E,a.N],we=[a.W,a.SW,a.SE,a.NE,a.N],Ne=[a.NW,a.W,a.S,a.SE,a.NE],_e=[a.NW,a.SW,a.S,a.E,a.NE],Ee=[a.NW,a.W,[d,-p],[d,p],a.N],Me=[[-p,-d],[p,-d],a.E,a.NE,a.N],Ie=[[-d,p],[-d,-p],a.S,a.SE,a.E],Oe=[a.W,a.SW,a.S,[p,d],[-p,d]],Le=[a.NW,a.W,[-p,-d],[p,-d],a.N],De=[[-d,p],[-d,-p],a.E,a.NE,a.N],We=[a.S,a.SE,a.E,[p,d],[-p,d]],Re=[a.W,a.SW,a.S,[d,-p],[d,p]],Be=[a.W,a.SW,a.SE,a.E,[p,d],[-p,d]],ze=[[-d,p],[-d,-p],a.S,a.SE,a.NE,a.N],Ve=[a.NW,a.W,[-p,-d],[p,-d],a.E,a.NE],Ue=[a.NW,a.SW,a.S,[d,-p],[d,p],a.N],R=[a.W,a.SW,a.S,a.E,a.NE,a.N],B=[a.NW,a.W,a.S,a.SE,a.E,a.N],H=[[-d,p],[-d,-p],[-p,-d],[p,-d],a.E,a.NE,a.N],k=[a.W,a.SW,a.S,[d,-p],[d,p],[p,d],[-p,d]],$=[a.NW,a.W,[-p,-d],[p,-d],[d,-p],[d,p],a.N],X=[[-d,p],[-d,-p],a.S,a.SE,a.E,[p,d],[-p,d]],Fe=[[-d,p],[-d,-p],[-p,-d],[p,-d],[d,-p],[d,p],[p,d],[-p,d]],go={0:[],1:[[a.W,a.S]],2:[[a.S,a.E]],3:[[a.W,a.E]],4:[[a.N,a.E]],5:{0:[[a.W,a.S],[a.N,a.E]],1:[[a.W,a.N],[a.S,a.E]]},6:[[a.N,a.S]],7:[[a.W,a.N]],8:[[a.W,a.N]],9:[[a.N,a.S]],10:{0:[[a.W,a.N],[a.S,a.E]],1:[[a.W,a.S],[a.N,a.E]]},11:[[a.N,a.E]],12:[[a.W,a.E]],13:[[a.S,a.E]],14:[[a.W,a.S]],15:[]};function h(r){return parseInt(r,4)}const ho={[h("0000")]:[],[h("2222")]:[],[h("2221")]:[_],[h("2212")]:[E],[h("2122")]:[M],[h("1222")]:[I],[h("0001")]:[_],[h("0010")]:[E],[h("0100")]:[M],[h("1000")]:[I],[h("2220")]:[O],[h("2202")]:[L],[h("2022")]:[D],[h("0222")]:[W],[h("0002")]:[O],[h("0020")]:[L],[h("0200")]:[D],[h("2000")]:[W],[h("0011")]:[be],[h("0110")]:[ye],[h("1100")]:[Ce],[h("1001")]:[Se],[h("2211")]:[be],[h("2112")]:[ye],[h("1122")]:[Ce],[h("1221")]:[Se],[h("2200")]:[Te],[h("2002")]:[Ae],[h("0022")]:[Te],[h("0220")]:[Ae],[h("1111")]:[uo],[h("1211")]:[Pe],[h("2111")]:[we],[h("1112")]:[Ne],[h("1121")]:[_e],[h("1011")]:[Pe],[h("0111")]:[we],[h("1110")]:[Ne],[h("1101")]:[_e],[h("1200")]:[Ee],[h("0120")]:[Me],[h("0012")]:[Ie],[h("2001")]:[Oe],[h("1022")]:[Ee],[h("2102")]:[Me],[h("2210")]:[Ie],[h("0221")]:[Oe],[h("1002")]:[Le],[h("2100")]:[De],[h("0210")]:[We],[h("0021")]:[Re],[h("1220")]:[Le],[h("0122")]:[De],[h("2012")]:[We],[h("2201")]:[Re],[h("0211")]:[Be],[h("2110")]:[ze],[h("1102")]:[Ve],[h("1021")]:[Ue],[h("2011")]:[Be],[h("0112")]:[ze],[h("1120")]:[Ve],[h("1201")]:[Ue],[h("2101")]:[R],[h("0121")]:[R],[h("1012")]:[B],[h("1210")]:[B],[h("0101")]:{0:[_,M],1:[R],2:[R]},[h("1010")]:{0:[I,E],1:[B],2:[B]},[h("2121")]:{0:[R],1:[R],2:[_,M]},[h("1212")]:{0:[B],1:[B],2:[I,E]},[h("2120")]:{0:[H],1:[H],2:[O,M]},[h("2021")]:{0:[k],1:[k],2:[_,D]},[h("1202")]:{0:[$],1:[$],2:[I,L]},[h("0212")]:{0:[X],1:[X],2:[E,W]},[h("0102")]:{0:[O,M],1:[H],2:[H]},[h("0201")]:{0:[_,D],1:[k],2:[k]},[h("1020")]:{0:[I,L],1:[$],2:[$]},[h("2010")]:{0:[E,W],1:[X],2:[X]},[h("2020")]:{0:[W,L],1:[Fe],2:[O,D]},[h("0202")]:{0:[D,O],1:[Fe],2:[W,L]}};function U(r,e){return Number.isNaN(r)?0:Array.isArray(e)?r<e[0]?0:r<e[1]?1:2:r>=e?1:0}function po(r){const{x:e,y:t,xRange:o,yRange:i,getValue:n,threshold:s}=r,c=e<o[0],l=e>=o[1]-1,u=t<i[0],g=t>=i[1]-1,f=c||l||u||g;let m=0,v,x,b,S;if(c||g)b=0;else{const y=n(e,t+1);b=U(y,s),m+=y}if(l||g)S=0;else{const y=n(e+1,t+1);S=U(y,s),m+=y}if(l||u)x=0;else{const y=n(e+1,t);x=U(y,s),m+=y}if(c||u)v=0;else{const y=n(e,t);v=U(y,s),m+=y}let C=-1;Number.isFinite(s)&&(C=b<<3|S<<2|x<<1|v),Array.isArray(s)&&(C=b<<6|S<<4|x<<2|v);let w=0;return f||(w=U(m/4,s)),{code:C,meanCode:w}}function mo(r){const{x:e,y:t,z:o,code:i,meanCode:n}=r;let s=ho[i];Array.isArray(s)||(s=s[n]);const c=e+1,l=t+1,u=[];return s.forEach(g=>{const f=[];g.forEach(m=>{const v=c+m[0],x=l+m[1];f.push([v,x,o])}),u.push(f)}),u}function fo(r){const{x:e,y:t,z:o,code:i,meanCode:n}=r;let s=go[i];Array.isArray(s)||(s=s[n]);const c=e+1,l=t+1,u=[];return s.forEach(g=>{g.forEach(f=>{const m=c+f[0],v=l+f[1];u.push([m,v,o])})}),u}function vo({contours:r,getValue:e,xRange:t,yRange:o}){const i=[],n=[];let s=0,c=0;for(let l=0;l<r.length;l++){const u=r[l],g=u.zIndex??l,{threshold:f}=u;for(let m=t[0]-1;m<t[1];m++)for(let v=o[0]-1;v<o[1];v++){const{code:x,meanCode:b}=po({getValue:e,threshold:f,x:m,y:v,xRange:t,yRange:o}),S={x:m,y:v,z:g,code:x,meanCode:b};if(Array.isArray(f)){const C=mo(S);for(const w of C)n[c++]={vertices:w,contour:u}}else{const C=fo(S);C.length>0&&(i[s++]={vertices:C,contour:u})}}}return{lines:i,polygons:n}}function xo(r){const{aggregator:e,binIdRange:t,channel:o}=r;if(e instanceof P){const i=e.getResult(o)?.buffer;if(i){const n=new Float32Array(i.readSyncWebGL().buffer);return bo(n,t)}}if(e instanceof G){const i=e.getResult(o)?.value,n=e.getBins()?.value;if(n&&i)return yo(i,n,e.binCount)}return null}function bo(r,e){const[[t,o],[i,n]]=e,s=o-t,c=n-i;return(l,u)=>(l-=t,u-=i,l<0||l>=s||u<0||u>=c?NaN:r[u*s+l])}function yo(r,e,t){const o={};for(let i=0;i<t;i++){const n=e[i*2],s=e[i*2+1];o[n]=o[n]||{},o[n][s]=r[i]}return(i,n)=>o[i]?.[n]??NaN}const Co=`uniform binOptionsUniforms {
  vec2 cellOriginCommon;
  vec2 cellSizeCommon;
} binOptions;
`,So={name:"binOptions",vs:Co,uniformTypes:{cellOriginCommon:"vec2<f32>",cellSizeCommon:"vec2<f32>"}},Ge=[255,255,255,255],To=1,Ao={cellSize:{type:"number",min:1,value:1e3},gridOrigin:{type:"array",compare:!0,value:[0,0]},getPosition:{type:"accessor",value:r=>r.position},getWeight:{type:"accessor",value:1},gpuAggregation:!0,aggregation:"SUM",contours:{type:"object",value:[{threshold:1}],optional:!0,compare:3},zOffset:.005};let at=class extends j{getAggregatorType(){return this.props.gpuAggregation&&P.isSupported(this.context.device)?"gpu":"cpu"}createAggregator(e){return e==="cpu"?new G({dimensions:2,getBin:{sources:["positions"],getValue:({positions:t},o,i)=>{const s=this.state.aggregatorViewport.projectPosition(t),{cellSizeCommon:c,cellOriginCommon:l}=i;return[Math.floor((s[0]-l[0])/c[0]),Math.floor((s[1]-l[1])/c[1])]}},getValue:[{sources:["counts"],getValue:({counts:t})=>t}],onUpdate:this._onAggregationUpdate.bind(this)}):new P(this.context.device,{dimensions:2,channelCount:1,bufferLayout:this.getAttributeManager().getBufferLayouts({isInstanced:!1}),...super.getShaders({modules:[V,So],vs:`
  in vec3 positions;
  in vec3 positions64Low;
  in float counts;

  void getBin(out ivec2 binId) {
    vec3 positionCommon = project_position(positions, positions64Low);
    vec2 gridCoords = floor(positionCommon.xy / binOptions.cellSizeCommon);
    binId = ivec2(gridCoords);
  }
  void getValue(out float value) {
    value = counts;
  }
  `}),onUpdate:this._onAggregationUpdate.bind(this)})}initializeState(){super.initializeState(),this.getAttributeManager().add({positions:{size:3,accessor:"getPosition",type:"float64",fp64:this.use64bitPositions()},counts:{size:1,accessor:"getWeight"}})}updateState(e){const t=super.updateState(e),{props:o,oldProps:i,changeFlags:n}=e,{aggregator:s}=this.state;if(t||n.dataChanged||o.cellSize!==i.cellSize||!F(o.gridOrigin,i.gridOrigin,1)||o.aggregation!==i.aggregation){this._updateBinOptions();const{cellSizeCommon:c,cellOriginCommon:l,binIdRange:u}=this.state;s.setProps({binIdRange:u,pointCount:this.getNumInstances(),operations:[o.aggregation],binOptions:{cellSizeCommon:c,cellOriginCommon:l}})}return F(i.contours,o.contours,2)||this.setState({contourData:null}),t}_updateBinOptions(){const e=this.getBounds(),t=[1,1];let o=[0,0],i=[[0,1],[0,1]],n=this.context.viewport;if(e&&Number.isFinite(e[0][0])){let s=[(e[0][0]+e[1][0])/2,(e[0][1]+e[1][1])/2];const{cellSize:c,gridOrigin:l}=this.props,{unitsPerMeter:u}=n.getDistanceScales(s);t[0]=u[0]*c,t[1]=u[1]*c;const g=n.projectFlat(s);o=[Math.floor((g[0]-l[0])/t[0])*t[0]+l[0],Math.floor((g[1]-l[1])/t[1])*t[1]+l[1]],s=n.unprojectFlat(o);const f=n.constructor;n=n.isGeospatial?new f({longitude:s[0],latitude:s[1],zoom:12}):new ce({position:[s[0],s[1],0],zoom:12}),o=[Math.fround(n.center[0]),Math.fround(n.center[1])],i=de({dataBounds:e,getBinId:m=>{const v=n.projectFlat(m);return[Math.floor((v[0]-o[0])/t[0]),Math.floor((v[1]-o[1])/t[1])]}})}this.setState({cellSizeCommon:t,cellOriginCommon:o,binIdRange:i,aggregatorViewport:n})}draw(e){e.shaderModuleProps.project&&(e.shaderModuleProps.project.viewport=this.state.aggregatorViewport),super.draw(e)}_onAggregationUpdate(){const{aggregator:e,binIdRange:t}=this.state;this.setState({aggregatedValueReader:xo({aggregator:e,binIdRange:t,channel:0}),contourData:null})}_getContours(){const{aggregatedValueReader:e}=this.state;if(!e)return null;if(!this.state.contourData){const{binIdRange:t}=this.state,{contours:o}=this.props,i=vo({contours:o,getValue:e,xRange:t[0],yRange:t[1]});this.state.contourData=i}return this.state.contourData}onAttributeChange(e){const{aggregator:t}=this.state;switch(e){case"positions":t.setNeedsUpdate(),this._updateBinOptions();const{cellSizeCommon:o,cellOriginCommon:i,binIdRange:n}=this.state;t.setProps({binIdRange:n,binOptions:{cellSizeCommon:o,cellOriginCommon:i}});break;case"counts":t.setNeedsUpdate(0);break}}renderLayers(){const e=this._getContours();if(!e)return null;const{lines:t,polygons:o}=e,{zOffset:i}=this.props,{cellOriginCommon:n,cellSizeCommon:s}=this.state,c=this.getSubLayerClass("lines",yt),l=this.getSubLayerClass("bands",Ct),u=new bt().translate([n[0],n[1],0]).scale([s[0],s[1],i]),g=t&&t.length>0&&new c(this.getSubLayerProps({id:"lines"}),{data:t,coordinateSystem:z.CARTESIAN,modelMatrix:u,getPath:m=>m.vertices,getColor:m=>m.contour.color??Ge,getWidth:m=>m.contour.strokeWidth??To,widthUnits:"pixels"}),f=o&&o.length>0&&new l(this.getSubLayerProps({id:"bands"}),{data:o,coordinateSystem:z.CARTESIAN,modelMatrix:u,getPolygon:m=>m.vertices,getFillColor:m=>m.contour.color??Ge});return[g,f]}getPickingInfo(e){const t=e.info,{object:o}=t;return o&&(t.object={contour:o.contour}),t}};at.layerName="ContourLayer";at.defaultProps=Ao;const Po=`#version 300 es
#define SHADER_NAME grid-cell-layer-vertex-shader
in vec3 positions;
in vec3 normals;
in vec2 instancePositions;
in float instanceElevationValues;
in float instanceColorValues;
in vec3 instancePickingColors;
uniform sampler2D colorRange;
out vec4 vColor;
float interp(float value, vec2 domain, vec2 range) {
float r = min(max((value - domain.x) / (domain.y - domain.x), 0.), 1.);
return mix(range.x, range.y, r);
}
vec4 interp(float value, vec2 domain, sampler2D range) {
float r = (value - domain.x) / (domain.y - domain.x);
return texture(range, vec2(r, 0.5));
}
void main(void) {
geometry.pickingColor = instancePickingColors;
if (isnan(instanceColorValues) ||
instanceColorValues < grid.colorDomain.z ||
instanceColorValues > grid.colorDomain.w ||
instanceElevationValues < grid.elevationDomain.z ||
instanceElevationValues > grid.elevationDomain.w
) {
gl_Position = vec4(0.);
return;
}
vec2 commonPosition = (instancePositions + (positions.xy + 1.0) / 2.0 * column.coverage) * grid.sizeCommon + grid.originCommon - project.commonOrigin.xy;
geometry.position = vec4(commonPosition, 0.0, 1.0);
geometry.normal = project_normal(normals);
float elevation = 0.0;
if (column.extruded) {
elevation = interp(instanceElevationValues, grid.elevationDomain.xy, grid.elevationRange);
elevation = project_size(elevation);
geometry.position.z = (positions.z + 1.0) / 2.0 * elevation;
}
gl_Position = project_common_position_to_clipspace(geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
vColor = interp(instanceColorValues, grid.colorDomain.xy, colorRange);
vColor.a *= layer.opacity;
if (column.extruded) {
vColor.rgb = lighting_getLightColor(vColor.rgb, project.cameraPosition, geometry.position.xyz, geometry.normal);
}
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,wo=`uniform gridUniforms {
  vec4 colorDomain;
  vec4 elevationDomain;
  vec2 elevationRange;
  vec2 originCommon;
  vec2 sizeCommon;
} grid;
`,No={name:"grid",vs:wo,uniformTypes:{colorDomain:"vec4<f32>",elevationDomain:"vec4<f32>",elevationRange:"vec2<f32>",originCommon:"vec2<f32>",sizeCommon:"vec2<f32>"}};class lt extends Ze{getShaders(){const e=super.getShaders();return e.modules.push(No),{...e,vs:Po}}initializeState(){super.initializeState();const e=this.getAttributeManager();e.remove(["instanceElevations","instanceFillColors","instanceLineColors","instanceStrokeWidths"]),e.addInstanced({instancePositions:{size:2,type:"float32",accessor:"getBin"},instanceColorValues:{size:1,type:"float32",accessor:"getColorValue"},instanceElevationValues:{size:1,type:"float32",accessor:"getElevationValue"}})}updateState(e){super.updateState(e);const{props:t,oldProps:o}=e,i=this.state.fillModel;if(o.colorRange!==t.colorRange){this.state.colorTexture?.destroy(),this.state.colorTexture=ge(this.context.device,t.colorRange,t.colorScaleType);const n={colorRange:this.state.colorTexture};i.shaderInputs.setProps({grid:n})}else o.colorScaleType!==t.colorScaleType&&ue(this.state.colorTexture,t.colorScaleType)}finalizeState(e){super.finalizeState(e),this.state.colorTexture?.destroy()}_updateGeometry(){const e=new St;this.state.fillModel.setGeometry(e)}draw({uniforms:e}){const{cellOriginCommon:t,cellSizeCommon:o,elevationRange:i,elevationScale:n,extruded:s,coverage:c,colorDomain:l,elevationDomain:u}=this.props,g=this.props.colorCutoff||[-1/0,1/0],f=this.props.elevationCutoff||[-1/0,1/0],m=this.state.fillModel,v={colorDomain:[Math.max(l[0],g[0]),Math.min(l[1],g[1]),Math.max(l[0]-1,g[0]),Math.min(l[1]+1,g[1])],elevationDomain:[Math.max(u[0],f[0]),Math.min(u[1],f[1]),Math.max(u[0]-1,f[0]),Math.min(u[1]+1,f[1])],elevationRange:[i[0]*n,i[1]*n],originCommon:t,sizeCommon:o};m.shaderInputs.setProps({column:{extruded:s,coverage:c},grid:v}),m.draw(this.context.renderPass)}}lt.layerName="GridCellLayer";const _o=`uniform binOptionsUniforms {
  vec2 cellOriginCommon;
  vec2 cellSizeCommon;
} binOptions;
`,Eo={name:"binOptions",vs:_o,uniformTypes:{cellOriginCommon:"vec2<f32>",cellSizeCommon:"vec2<f32>"}};function je(){}const Mo={gpuAggregation:!0,colorDomain:null,colorRange:J,getColorValue:{type:"accessor",value:null},getColorWeight:{type:"accessor",value:1},colorAggregation:"SUM",lowerPercentile:{type:"number",min:0,max:100,value:0},upperPercentile:{type:"number",min:0,max:100,value:100},colorScaleType:"quantize",onSetColorDomain:je,elevationDomain:null,elevationRange:[0,1e3],getElevationValue:{type:"accessor",value:null},getElevationWeight:{type:"accessor",value:1},elevationAggregation:"SUM",elevationScale:{type:"number",min:0,value:1},elevationLowerPercentile:{type:"number",min:0,max:100,value:0},elevationUpperPercentile:{type:"number",min:0,max:100,value:100},elevationScaleType:"linear",onSetElevationDomain:je,cellSize:{type:"number",min:0,value:1e3},coverage:{type:"number",min:0,max:1,value:1},getPosition:{type:"accessor",value:r=>r.position},gridAggregator:{type:"function",optional:!0,value:null},extruded:!1,material:!0};class ct extends j{getAggregatorType(){const{gpuAggregation:e,gridAggregator:t,getColorValue:o,getElevationValue:i}=this.props;return e&&(t||o||i)?(Q.warn("Features not supported by GPU aggregation, falling back to CPU")(),"cpu"):e&&P.isSupported(this.context.device)?"gpu":"cpu"}createAggregator(e){if(e==="cpu"){const{gridAggregator:t,cellSize:o}=this.props;return new G({dimensions:2,getBin:{sources:["positions"],getValue:({positions:i},n,s)=>{if(t)return t(i,o);const l=this.state.aggregatorViewport.projectPosition(i),{cellSizeCommon:u,cellOriginCommon:g}=s;return[Math.floor((l[0]-g[0])/u[0]),Math.floor((l[1]-g[1])/u[1])]}},getValue:[{sources:["colorWeights"],getValue:({colorWeights:i})=>i},{sources:["elevationWeights"],getValue:({elevationWeights:i})=>i}]})}return new P(this.context.device,{dimensions:2,channelCount:2,bufferLayout:this.getAttributeManager().getBufferLayouts({isInstanced:!1}),...super.getShaders({modules:[V,Eo],vs:`
  in vec3 positions;
  in vec3 positions64Low;
  in float colorWeights;
  in float elevationWeights;

  void getBin(out ivec2 binId) {
    vec3 positionCommon = project_position(positions, positions64Low);
    vec2 gridCoords = floor(positionCommon.xy / binOptions.cellSizeCommon);
    binId = ivec2(gridCoords);
  }
  void getValue(out vec2 value) {
    value = vec2(colorWeights, elevationWeights);
  }
  `})})}initializeState(){super.initializeState(),this.getAttributeManager().add({positions:{size:3,accessor:"getPosition",type:"float64",fp64:this.use64bitPositions()},colorWeights:{size:1,accessor:"getColorWeight"},elevationWeights:{size:1,accessor:"getElevationWeight"}})}updateState(e){const t=super.updateState(e),{props:o,oldProps:i,changeFlags:n}=e,{aggregator:s}=this.state;if((n.dataChanged||!this.state.dataAsArray)&&(o.getColorValue||o.getElevationValue)&&(this.state.dataAsArray=Array.from(qe(o.data).iterable)),t||n.dataChanged||o.cellSize!==i.cellSize||o.getColorValue!==i.getColorValue||o.getElevationValue!==i.getElevationValue||o.colorAggregation!==i.colorAggregation||o.elevationAggregation!==i.elevationAggregation){this._updateBinOptions();const{cellSizeCommon:c,cellOriginCommon:l,binIdRange:u,dataAsArray:g}=this.state;if(s.setProps({binIdRange:u,pointCount:this.getNumInstances(),operations:[o.colorAggregation,o.elevationAggregation],binOptions:{cellSizeCommon:c,cellOriginCommon:l},onUpdate:this._onAggregationUpdate.bind(this)}),g){const{getColorValue:f,getElevationValue:m}=this.props;s.setProps({customOperations:[f&&(v=>f(v.map(x=>g[x]),{indices:v,data:o.data})),m&&(v=>m(v.map(x=>g[x]),{indices:v,data:o.data}))]})}}return n.updateTriggersChanged&&n.updateTriggersChanged.getColorValue&&s.setNeedsUpdate(0),n.updateTriggersChanged&&n.updateTriggersChanged.getElevationValue&&s.setNeedsUpdate(1),t}_updateBinOptions(){const e=this.getBounds(),t=[1,1];let o=[0,0],i=[[0,1],[0,1]],n=this.context.viewport;if(e&&Number.isFinite(e[0][0])){let s=[(e[0][0]+e[1][0])/2,(e[0][1]+e[1][1])/2];const{cellSize:c}=this.props,{unitsPerMeter:l}=n.getDistanceScales(s);t[0]=l[0]*c,t[1]=l[1]*c;const u=n.projectFlat(s);o=[Math.floor(u[0]/t[0])*t[0],Math.floor(u[1]/t[1])*t[1]],s=n.unprojectFlat(o);const g=n.constructor;n=n.isGeospatial?new g({longitude:s[0],latitude:s[1],zoom:12}):new ce({position:[s[0],s[1],0],zoom:12}),o=[Math.fround(n.center[0]),Math.fround(n.center[1])],i=de({dataBounds:e,getBinId:f=>{const m=n.projectFlat(f);return[Math.floor((m[0]-o[0])/t[0]),Math.floor((m[1]-o[1])/t[1])]}})}this.setState({cellSizeCommon:t,cellOriginCommon:o,binIdRange:i,aggregatorViewport:n})}draw(e){e.shaderModuleProps.project&&(e.shaderModuleProps.project.viewport=this.state.aggregatorViewport),super.draw(e)}_onAggregationUpdate({channel:e}){const t=this.getCurrentLayer().props,{aggregator:o}=this.state;if(e===0){const i=o.getResult(0);this.setState({colors:new q(i,o.binCount)}),t.onSetColorDomain(o.getResultDomain(0))}else if(e===1){const i=o.getResult(1);this.setState({elevations:new q(i,o.binCount)}),t.onSetElevationDomain(o.getResultDomain(1))}}onAttributeChange(e){const{aggregator:t}=this.state;switch(e){case"positions":t.setNeedsUpdate(),this._updateBinOptions();const{cellSizeCommon:o,cellOriginCommon:i,binIdRange:n}=this.state;t.setProps({binIdRange:n,binOptions:{cellSizeCommon:o,cellOriginCommon:i}});break;case"colorWeights":t.setNeedsUpdate(0);break;case"elevationWeights":t.setNeedsUpdate(1);break}}renderLayers(){const{aggregator:e,cellOriginCommon:t,cellSizeCommon:o}=this.state,{elevationScale:i,colorRange:n,elevationRange:s,extruded:c,coverage:l,material:u,transitions:g,colorScaleType:f,lowerPercentile:m,upperPercentile:v,colorDomain:x,elevationScaleType:b,elevationLowerPercentile:S,elevationUpperPercentile:C,elevationDomain:w}=this.props,y=this.getSubLayerClass("cells",lt),N=e.getBins(),T=this.state.colors?.update({scaleType:f,lowerPercentile:m,upperPercentile:v}),A=this.state.elevations?.update({scaleType:b,lowerPercentile:S,upperPercentile:C});return!T||!A?null:new y(this.getSubLayerProps({id:"cells"}),{data:{length:e.binCount,attributes:{getBin:N,getColorValue:T.attribute,getElevationValue:A.attribute}},dataComparator:(oe,ie)=>oe.length===ie.length,updateTriggers:{getBin:[N],getColorValue:[T.attribute],getElevationValue:[A.attribute]},cellOriginCommon:t,cellSizeCommon:o,elevationScale:i,colorRange:n,colorScaleType:f,elevationRange:s,extruded:c,coverage:l,material:u,colorDomain:T.domain||x||e.getResultDomain(0),elevationDomain:A.domain||w||e.getResultDomain(1),colorCutoff:T.cutoff,elevationCutoff:A.cutoff,transitions:g&&{getFillColor:g.getColorValue||g.getColorWeight,getElevation:g.getElevationValue||g.getElevationWeight},extensions:[]})}getPickingInfo(e){const t=e.info,{index:o}=t;if(o>=0){const i=this.state.aggregator.getBin(o);let n;i&&(n={col:i.id[0],row:i.id[1],colorValue:i.value[0],elevationValue:i.value[1],count:i.count},i.pointIndices&&(n.pointIndices=i.pointIndices,n.points=Array.isArray(this.props.data)?i.pointIndices.map(s=>this.props.data[s]):[])),t.object=n}return t}}ct.layerName="GridLayer";ct.defaultProps=Mo;function Io(r){const e=r.map(c=>c[0]),t=r.map(c=>c[1]),o=Math.min.apply(null,e),i=Math.max.apply(null,e),n=Math.min.apply(null,t),s=Math.max.apply(null,t);return[o,n,i,s]}function Oo(r,e){return e[0]>=r[0]&&e[2]<=r[2]&&e[1]>=r[1]&&e[3]<=r[3]}const He=new Float32Array(12);function ke(r,e=2){let t=0;for(const o of r)for(let i=0;i<e;i++)He[t++]=o[i]||0;return He}function Lo(r,e,t){const[o,i,n,s]=r,c=n-o,l=s-i;let u=c,g=l;c/l<e/t?u=e/t*l:g=t/e*c,u<e&&(u=e,g=t);const f=(n+o)/2,m=(s+i)/2;return[f-u/2,m-g/2,f+u/2,m+g/2]}function Do(r,e){const[t,o,i,n]=e;return[(r[0]-t)/(i-t),(r[1]-o)/(n-o)]}const Wo=`#version 300 es
#define SHADER_NAME heatp-map-layer-vertex-shader
uniform sampler2D maxTexture;
in vec3 positions;
in vec2 texCoords;
out vec2 vTexCoords;
out float vIntensityMin;
out float vIntensityMax;
void main(void) {
gl_Position = project_position_to_clipspace(positions, vec3(0.0), vec3(0.0));
vTexCoords = texCoords;
vec4 maxTexture = texture(maxTexture, vec2(0.5));
float maxValue = triangle.aggregationMode < 0.5 ? maxTexture.r : maxTexture.g;
float minValue = maxValue * triangle.threshold;
if (triangle.colorDomain[1] > 0.) {
maxValue = triangle.colorDomain[1];
minValue = triangle.colorDomain[0];
}
vIntensityMax = triangle.intensity / maxValue;
vIntensityMin = triangle.intensity / minValue;
}
`,Ro=`#version 300 es
#define SHADER_NAME triangle-layer-fragment-shader
precision highp float;
uniform sampler2D weightsTexture;
uniform sampler2D colorTexture;
in vec2 vTexCoords;
in float vIntensityMin;
in float vIntensityMax;
out vec4 fragColor;
vec4 getLinearColor(float value) {
float factor = clamp(value * vIntensityMax, 0., 1.);
vec4 color = texture(colorTexture, vec2(factor, 0.5));
color.a *= min(value * vIntensityMin, 1.0);
return color;
}
void main(void) {
vec4 weights = texture(weightsTexture, vTexCoords);
float weight = weights.r;
if (triangle.aggregationMode > 0.5) {
weight /= max(1.0, weights.a);
}
if (weight <= 0.) {
discard;
}
vec4 linearColor = getLinearColor(weight);
linearColor.a *= layer.opacity;
fragColor = linearColor;
}
`,$e=`uniform triangleUniforms {
  float aggregationMode;
  vec2 colorDomain;
  float intensity;
  float threshold;
} triangle;
`,Bo={name:"triangle",vs:$e,fs:$e,uniformTypes:{aggregationMode:"f32",colorDomain:"vec2<f32>",intensity:"f32",threshold:"f32"}};class ut extends Ke{getShaders(){return super.getShaders({vs:Wo,fs:Ro,modules:[V,Bo]})}initializeState({device:e}){this.setState({model:this._getModel(e)})}_getModel(e){const{vertexCount:t,data:o}=this.props;return new Z(e,{...this.getShaders(),id:this.props.id,attributes:o.attributes,bufferLayout:[{name:"positions",format:"float32x3"},{name:"texCoords",format:"float32x2"}],topology:"triangle-strip",vertexCount:t})}draw(){const{model:e}=this.state,{aggregationMode:t,colorDomain:o,intensity:i,threshold:n,colorTexture:s,maxTexture:c,weightsTexture:l}=this.props,u={aggregationMode:t,colorDomain:o,intensity:i,threshold:n,colorTexture:s,maxTexture:c,weightsTexture:l};e.shaderInputs.setProps({triangle:u}),e.draw(this.context.renderPass)}}ut.layerName="TriangleLayer";function zo(r,e){const t={};for(const o in r)e.includes(o)||(t[o]=r[o]);return t}class gt extends Ye{initializeAggregationLayer(e){super.initializeState(this.context),this.setState({ignoreProps:zo(this.constructor._propTypes,e.data.props),dimensions:e})}updateState(e){super.updateState(e);const{changeFlags:t}=e;if(t.extensionsChanged){const o=this.getShaders({});o&&o.defines&&(o.defines.NON_INSTANCED_MODEL=1),this.updateShaders(o)}this._updateAttributes()}updateAttributes(e){this.setState({changedAttributes:e})}getAttributes(){return this.getAttributeManager().getAttributes()}getModuleSettings(){const{viewport:e,mousePosition:t,device:o}=this.context;return Object.assign(Object.create(this.props),{viewport:e,mousePosition:t,picking:{isActive:0},devicePixelRatio:o.canvasContext.cssToDeviceRatio()})}updateShaders(e){}isAggregationDirty(e,t={}){const{props:o,oldProps:i,changeFlags:n}=e,{compareAll:s=!1,dimension:c}=t,{ignoreProps:l}=this.state,{props:u,accessors:g=[]}=c,{updateTriggersChanged:f}=n;if(n.dataChanged)return!0;if(f){if(f.all)return!0;for(const m of g)if(f[m])return!0}if(s)return n.extensionsChanged?!0:vt({oldProps:i,newProps:o,ignoreProps:l,propTypes:this.constructor._propTypes});for(const m of u)if(o[m]!==i[m])return!0;return!1}isAttributeChanged(e){const{changedAttributes:t}=this.state;return e?t&&t[e]!==void 0:!Vo(t)}_getAttributeManager(){return new le(this.context.device,{id:this.props.id,stats:this.context.stats})}}gt.layerName="AggregationLayer";function Vo(r){let e=!0;for(const t in r){e=!1;break}return e}const se=`#version 300 es
in vec3 positions;
in vec3 positions64Low;
in float weights;
out vec4 weightsTexture;
void main()
{
weightsTexture = vec4(weights * weight.weightsScale, 0., 0., 1.);
float radiusTexels = project_pixel_size(weight.radiusPixels) * weight.textureWidth / (weight.commonBounds.z - weight.commonBounds.x);
gl_PointSize = radiusTexels * 2.;
vec3 commonPosition = project_position(positions, positions64Low);
gl_Position.xy = (commonPosition.xy - weight.commonBounds.xy) / (weight.commonBounds.zw - weight.commonBounds.xy) ;
gl_Position.xy = (gl_Position.xy * 2.) - (1.);
gl_Position.w = 1.0;
}
`,re=`#version 300 es
in vec4 weightsTexture;
out vec4 fragColor;
float gaussianKDE(float u){
return pow(2.71828, -u*u/0.05555)/(1.77245385*0.166666);
}
void main()
{
float dist = length(gl_PointCoord - vec2(0.5, 0.5));
if (dist > 0.5) {
discard;
}
fragColor = weightsTexture * gaussianKDE(2. * dist);
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,Uo=`#version 300 es
uniform sampler2D inTexture;
out vec4 outTexture;
void main()
{
int yIndex = gl_VertexID / int(maxWeight.textureSize);
int xIndex = gl_VertexID - (yIndex * int(maxWeight.textureSize));
vec2 uv = (0.5 + vec2(float(xIndex), float(yIndex))) / maxWeight.textureSize;
outTexture = texture(inTexture, uv);
gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
gl_PointSize = 1.0;
}
`,Fo=`#version 300 es
in vec4 outTexture;
out vec4 fragColor;
void main() {
fragColor = outTexture;
fragColor.g = outTexture.r / max(1.0, outTexture.a);
}
`,Go=`uniform weightUniforms {
  vec4 commonBounds;
  float radiusPixels;
  float textureWidth;
  float weightsScale;
} weight;
`,jo={name:"weight",vs:Go,uniformTypes:{commonBounds:"vec4<f32>",radiusPixels:"f32",textureWidth:"f32",weightsScale:"f32"}},Ho={name:"maxWeight",vs:`uniform maxWeightUniforms {
  float textureSize;
} maxWeight;
`,uniformTypes:{textureSize:"f32"}},ko=2,ae={format:"rgba8unorm",dimension:"2d",width:1,height:1,sampler:{minFilter:"linear",magFilter:"linear",addressModeU:"clamp-to-edge",addressModeV:"clamp-to-edge"}},Xe=[0,0],$o={SUM:0,MEAN:1},Xo={getPosition:{type:"accessor",value:r=>r.position},getWeight:{type:"accessor",value:1},intensity:{type:"number",min:0,value:1},radiusPixels:{type:"number",min:1,max:100,value:50},colorRange:J,threshold:{type:"number",min:0,max:1,value:.05},colorDomain:{type:"array",value:null,optional:!0},aggregation:"SUM",weightsTextureSize:{type:"number",min:128,max:2048,value:2048},debounceTimeout:{type:"number",min:0,max:1e3,value:500}},Yo=["float32-renderable-webgl","texture-blend-float-webgl"],Ko={data:{props:["radiusPixels"]}};class dt extends gt{getShaders(e){let t=[V];return e.modules&&(t=[...t,...e.modules]),super.getShaders({...e,modules:t})}initializeState(){super.initializeAggregationLayer(Ko),this.setState({colorDomain:Xe}),this._setupTextureParams(),this._setupAttributes(),this._setupResources()}shouldUpdateState({changeFlags:e}){return e.somethingChanged}updateState(e){super.updateState(e),this._updateHeatmapState(e)}_updateHeatmapState(e){const{props:t,oldProps:o}=e,i=this._getChangeFlags(e);if((i.dataChanged||i.viewportChanged)&&(i.boundsChanged=this._updateBounds(i.dataChanged),this._updateTextureRenderingBounds()),i.dataChanged||i.boundsChanged){if(clearTimeout(this.state.updateTimer),this.setState({isWeightMapDirty:!0}),i.dataChanged){const n=this.getShaders({vs:se,fs:re});this._createWeightsTransform(n)}}else i.viewportZoomChanged&&this._debouncedUpdateWeightmap();t.colorRange!==o.colorRange&&this._updateColorTexture(e),this.state.isWeightMapDirty&&this._updateWeightmap(),this.setState({zoom:e.context.viewport.zoom})}renderLayers(){const{weightsTexture:e,triPositionBuffer:t,triTexCoordBuffer:o,maxWeightsTexture:i,colorTexture:n,colorDomain:s}=this.state,{updateTriggers:c,intensity:l,threshold:u,aggregation:g}=this.props,f=this.getSubLayerClass("triangle",ut);return new f(this.getSubLayerProps({id:"triangle-layer",updateTriggers:c}),{coordinateSystem:z.DEFAULT,data:{attributes:{positions:t,texCoords:o}},vertexCount:4,maxTexture:i,colorTexture:n,aggregationMode:$o[g]||0,weightsTexture:e,intensity:l,threshold:u,colorDomain:s})}finalizeState(e){super.finalizeState(e);const{weightsTransform:t,weightsTexture:o,maxWeightTransform:i,maxWeightsTexture:n,triPositionBuffer:s,triTexCoordBuffer:c,colorTexture:l,updateTimer:u}=this.state;t?.destroy(),o?.destroy(),i?.destroy(),n?.destroy(),s?.destroy(),c?.destroy(),l?.destroy(),u&&clearTimeout(u)}_getAttributeManager(){return new le(this.context.device,{id:this.props.id,stats:this.context.stats})}_getChangeFlags(e){const t={},{dimensions:o}=this.state;t.dataChanged=this.isAttributeChanged()&&"attribute changed"||this.isAggregationDirty(e,{compareAll:!0,dimension:o.data})&&"aggregation is dirty",t.viewportChanged=e.changeFlags.viewportChanged;const{zoom:i}=this.state;return(!e.context.viewport||e.context.viewport.zoom!==i)&&(t.viewportZoomChanged=!0),t}_createTextures(){const{textureSize:e,format:t}=this.state;this.setState({weightsTexture:this.context.device.createTexture({...ae,width:e,height:e,format:t}),maxWeightsTexture:this.context.device.createTexture({...ae,width:1,height:1,format:t})})}_setupAttributes(){this.getAttributeManager().add({positions:{size:3,type:"float64",accessor:"getPosition"},weights:{size:1,accessor:"getWeight"}}),this.setState({positionAttributeName:"positions"})}_setupTextureParams(){const{device:e}=this.context,{weightsTextureSize:t}=this.props,o=Math.min(t,e.limits.maxTextureDimension2D),i=Yo.every(c=>e.features.has(c)),n=i?"rgba32float":"rgba8unorm",s=i?1:1/255;this.setState({textureSize:o,format:n,weightsScale:s}),i||Q.warn(`HeatmapLayer: ${this.id} rendering to float texture not supported, falling back to low precision format`)()}_createWeightsTransform(e){let{weightsTransform:t}=this.state;const{weightsTexture:o}=this.state,i=this.getAttributeManager();t?.destroy(),t=new he(this.context.device,{id:`${this.id}-weights-transform`,bufferLayout:i.getBufferLayouts(),vertexCount:1,targetTexture:o,parameters:{depthWriteEnabled:!1,blendColorOperation:"add",blendColorSrcFactor:"one",blendColorDstFactor:"one",blendAlphaSrcFactor:"one",blendAlphaDstFactor:"one"},topology:"point-list",...e,modules:[...e.modules,jo]}),this.setState({weightsTransform:t})}_setupResources(){this._createTextures();const{device:e}=this.context,{textureSize:t,weightsTexture:o,maxWeightsTexture:i}=this.state,n=this.getShaders({vs:se,fs:re});this._createWeightsTransform(n);const s=this.getShaders({vs:Uo,fs:Fo,modules:[Ho]}),c=new he(e,{id:`${this.id}-max-weights-transform`,targetTexture:i,...s,vertexCount:t*t,topology:"point-list",parameters:{depthWriteEnabled:!1,blendColorOperation:"max",blendAlphaOperation:"max",blendColorSrcFactor:"one",blendColorDstFactor:"one",blendAlphaSrcFactor:"one",blendAlphaDstFactor:"one"}}),l={inTexture:o,textureSize:t};c.model.shaderInputs.setProps({maxWeight:l}),this.setState({weightsTexture:o,maxWeightsTexture:i,maxWeightTransform:c,zoom:null,triPositionBuffer:e.createBuffer({byteLength:48}),triTexCoordBuffer:e.createBuffer({byteLength:48})})}updateShaders(e){this._createWeightsTransform({vs:se,fs:re,...e})}_updateMaxWeightValue(){const{maxWeightTransform:e}=this.state;e.run({parameters:{viewport:[0,0,1,1]},clearColor:[0,0,0,0]})}_updateBounds(e=!1){const{viewport:t}=this.context,o=[t.unproject([0,0]),t.unproject([t.width,0]),t.unproject([0,t.height]),t.unproject([t.width,t.height])].map(c=>c.map(Math.fround)),i=Io(o),n={visibleWorldBounds:i,viewportCorners:o};let s=!1;if(e||!this.state.worldBounds||!Oo(this.state.worldBounds,i)){const c=this._worldToCommonBounds(i),l=this._commonToWorldBounds(c);this.props.coordinateSystem===z.LNGLAT&&(l[1]=Math.max(l[1],-85.051129),l[3]=Math.min(l[3],85.051129),l[0]=Math.max(l[0],-360),l[2]=Math.min(l[2],360));const u=this._worldToCommonBounds(l);n.worldBounds=l,n.normalizedCommonBounds=u,s=!0}return this.setState(n),s}_updateTextureRenderingBounds(){const{triPositionBuffer:e,triTexCoordBuffer:t,normalizedCommonBounds:o,viewportCorners:i}=this.state,{viewport:n}=this.context;e.write(ke(i,3));const s=i.map(c=>Do(n.projectPosition(c),o));t.write(ke(s,2))}_updateColorTexture(e){const{colorRange:t}=e.props;let{colorTexture:o}=this.state;const i=tt(t,!1,Uint8Array);o?.destroy(),o=this.context.device.createTexture({...ae,data:i,width:t.length,height:1}),this.setState({colorTexture:o})}_updateWeightmap(){const{radiusPixels:e,colorDomain:t,aggregation:o}=this.props,{worldBounds:i,textureSize:n,weightsScale:s,weightsTexture:c}=this.state,l=this.state.weightsTransform;this.state.isWeightMapDirty=!1;const u=this._worldToCommonBounds(i,{useLayerCoordinateSystem:!0});if(t&&o==="SUM"){const{viewport:y}=this.context,N=y.distanceScales.metersPerUnit[2]*(u[2]-u[0])/n;this.state.colorDomain=t.map(T=>T*N*s)}else this.state.colorDomain=t||Xe;const f=this.getAttributeManager().getAttributes(),m=this.getModuleSettings();this._setModelAttributes(l.model,f),l.model.setVertexCount(this.getNumInstances());const v={radiusPixels:e,commonBounds:u,textureWidth:n,weightsScale:s,weightsTexture:c},{viewport:x,devicePixelRatio:b,coordinateSystem:S,coordinateOrigin:C}=m,{modelMatrix:w}=this.props;l.model.shaderInputs.setProps({project:{viewport:x,devicePixelRatio:b,modelMatrix:w,coordinateSystem:S,coordinateOrigin:C},weight:v}),l.run({parameters:{viewport:[0,0,n,n]},clearColor:[0,0,0,0]}),this._updateMaxWeightValue()}_debouncedUpdateWeightmap(e=!1){let{updateTimer:t}=this.state;const{debounceTimeout:o}=this.props;e?(t=null,this._updateBounds(!0),this._updateTextureRenderingBounds(),this.setState({isWeightMapDirty:!0})):(this.setState({isWeightMapDirty:!1}),clearTimeout(t),t=setTimeout(this._debouncedUpdateWeightmap.bind(this,!0),o)),this.setState({updateTimer:t})}_worldToCommonBounds(e,t={}){const{useLayerCoordinateSystem:o=!1}=t,[i,n,s,c]=e,{viewport:l}=this.context,{textureSize:u}=this.state,{coordinateSystem:g}=this.props,f=o&&(g===z.LNGLAT_OFFSETS||g===z.METER_OFFSETS),m=f?l.projectPosition(this.props.coordinateOrigin):[0,0],v=u*ko/l.scale;let x,b;return o&&!f?(x=this.projectPosition([i,n,0]),b=this.projectPosition([s,c,0])):(x=l.projectPosition([i,n,0]),b=l.projectPosition([s,c,0])),Lo([x[0]-m[0],x[1]-m[1],b[0]-m[0],b[1]-m[1]],v,v)}_commonToWorldBounds(e){const[t,o,i,n]=e,{viewport:s}=this.context,c=s.unprojectPosition([t,o]),l=s.unprojectPosition([i,n]);return c.slice(0,2).concat(l.slice(0,2))}}dt.layerName="HeatmapLayer";dt.defaultProps=Xo;export{G as CPUAggregator,at as ContourLayer,ct as GridLayer,dt as HeatmapLayer,rt as HexagonLayer,it as ScreenGridLayer,P as WebGLAggregator,j as _AggregationLayer};
//# sourceMappingURL=aggregation-layers.js.map
