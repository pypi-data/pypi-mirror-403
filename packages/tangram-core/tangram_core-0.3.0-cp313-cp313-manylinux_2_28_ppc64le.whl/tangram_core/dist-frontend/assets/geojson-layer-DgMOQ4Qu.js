import{L as E,p as z,d as O,c as te,G as K}from"./layer-DPcO4AXQ.js";import{U as w,u as X,O as we,m as ae,x as T}from"./deep-equal-BTW2ZN6S.js";import{M as F}from"./shader-Cbdysp2j.js";import{c as Ee}from"./color-CUNNsFV-.js";import{g as Ye,C as ie}from"./tesselator-CENyUZ2p.js";import{n as Je,S as ze,P as Oe}from"./solid-polygon-layer-DJFl_7Ca.js";import{l as Qe}from"./webgl-developer-tools-utTNOsNf.js";const le=`uniform arcUniforms {
  bool greatCircle;
  bool useShortestPath;
  float numSegments;
  float widthScale;
  float widthMinPixels;
  float widthMaxPixels;
  highp int widthUnits;
} arc;
`,et={name:"arc",vs:le,fs:le,uniformTypes:{greatCircle:"f32",useShortestPath:"f32",numSegments:"f32",widthScale:"f32",widthMinPixels:"f32",widthMaxPixels:"f32",widthUnits:"i32"}},tt=`#version 300 es
#define SHADER_NAME arc-layer-vertex-shader
in vec4 instanceSourceColors;
in vec4 instanceTargetColors;
in vec3 instanceSourcePositions;
in vec3 instanceSourcePositions64Low;
in vec3 instanceTargetPositions;
in vec3 instanceTargetPositions64Low;
in vec3 instancePickingColors;
in float instanceWidths;
in float instanceHeights;
in float instanceTilts;
out vec4 vColor;
out vec2 uv;
out float isValid;
float paraboloid(float distance, float sourceZ, float targetZ, float ratio) {
float deltaZ = targetZ - sourceZ;
float dh = distance * instanceHeights;
if (dh == 0.0) {
return sourceZ + deltaZ * ratio;
}
float unitZ = deltaZ / dh;
float p2 = unitZ * unitZ + 1.0;
float dir = step(deltaZ, 0.0);
float z0 = mix(sourceZ, targetZ, dir);
float r = mix(ratio, 1.0 - ratio, dir);
return sqrt(r * (p2 - r)) * dh + z0;
}
vec2 getExtrusionOffset(vec2 line_clipspace, float offset_direction, float width) {
vec2 dir_screenspace = normalize(line_clipspace * project.viewportSize);
dir_screenspace = vec2(-dir_screenspace.y, dir_screenspace.x);
return dir_screenspace * offset_direction * width / 2.0;
}
float getSegmentRatio(float index) {
return smoothstep(0.0, 1.0, index / (arc.numSegments - 1.0));
}
vec3 interpolateFlat(vec3 source, vec3 target, float segmentRatio) {
float distance = length(source.xy - target.xy);
float z = paraboloid(distance, source.z, target.z, segmentRatio);
float tiltAngle = radians(instanceTilts);
vec2 tiltDirection = normalize(target.xy - source.xy);
vec2 tilt = vec2(-tiltDirection.y, tiltDirection.x) * z * sin(tiltAngle);
return vec3(
mix(source.xy, target.xy, segmentRatio) + tilt,
z * cos(tiltAngle)
);
}
float getAngularDist (vec2 source, vec2 target) {
vec2 sourceRadians = radians(source);
vec2 targetRadians = radians(target);
vec2 sin_half_delta = sin((sourceRadians - targetRadians) / 2.0);
vec2 shd_sq = sin_half_delta * sin_half_delta;
float a = shd_sq.y + cos(sourceRadians.y) * cos(targetRadians.y) * shd_sq.x;
return 2.0 * asin(sqrt(a));
}
vec3 interpolateGreatCircle(vec3 source, vec3 target, vec3 source3D, vec3 target3D, float angularDist, float t) {
vec2 lngLat;
if(abs(angularDist - PI) < 0.001) {
lngLat = (1.0 - t) * source.xy + t * target.xy;
} else {
float a = sin((1.0 - t) * angularDist);
float b = sin(t * angularDist);
vec3 p = source3D.yxz * a + target3D.yxz * b;
lngLat = degrees(vec2(atan(p.y, -p.x), atan(p.z, length(p.xy))));
}
float z = paraboloid(angularDist * EARTH_RADIUS, source.z, target.z, t);
return vec3(lngLat, z);
}
void main(void) {
geometry.worldPosition = instanceSourcePositions;
geometry.worldPositionAlt = instanceTargetPositions;
float segmentIndex = float(gl_VertexID / 2);
float segmentSide = mod(float(gl_VertexID), 2.) == 0. ? -1. : 1.;
float segmentRatio = getSegmentRatio(segmentIndex);
float prevSegmentRatio = getSegmentRatio(max(0.0, segmentIndex - 1.0));
float nextSegmentRatio = getSegmentRatio(min(arc.numSegments - 1.0, segmentIndex + 1.0));
float indexDir = mix(-1.0, 1.0, step(segmentIndex, 0.0));
isValid = 1.0;
uv = vec2(segmentRatio, segmentSide);
geometry.uv = uv;
geometry.pickingColor = instancePickingColors;
vec4 curr;
vec4 next;
vec3 source;
vec3 target;
if ((arc.greatCircle || project.projectionMode == PROJECTION_MODE_GLOBE) && project.coordinateSystem == COORDINATE_SYSTEM_LNGLAT) {
source = project_globe_(vec3(instanceSourcePositions.xy, 0.0));
target = project_globe_(vec3(instanceTargetPositions.xy, 0.0));
float angularDist = getAngularDist(instanceSourcePositions.xy, instanceTargetPositions.xy);
vec3 prevPos = interpolateGreatCircle(instanceSourcePositions, instanceTargetPositions, source, target, angularDist, prevSegmentRatio);
vec3 currPos = interpolateGreatCircle(instanceSourcePositions, instanceTargetPositions, source, target, angularDist, segmentRatio);
vec3 nextPos = interpolateGreatCircle(instanceSourcePositions, instanceTargetPositions, source, target, angularDist, nextSegmentRatio);
if (abs(currPos.x - prevPos.x) > 180.0) {
indexDir = -1.0;
isValid = 0.0;
} else if (abs(currPos.x - nextPos.x) > 180.0) {
indexDir = 1.0;
isValid = 0.0;
}
nextPos = indexDir < 0.0 ? prevPos : nextPos;
nextSegmentRatio = indexDir < 0.0 ? prevSegmentRatio : nextSegmentRatio;
if (isValid == 0.0) {
nextPos.x += nextPos.x > 0.0 ? -360.0 : 360.0;
float t = ((currPos.x > 0.0 ? 180.0 : -180.0) - currPos.x) / (nextPos.x - currPos.x);
currPos = mix(currPos, nextPos, t);
segmentRatio = mix(segmentRatio, nextSegmentRatio, t);
}
vec3 currPos64Low = mix(instanceSourcePositions64Low, instanceTargetPositions64Low, segmentRatio);
vec3 nextPos64Low = mix(instanceSourcePositions64Low, instanceTargetPositions64Low, nextSegmentRatio);
curr = project_position_to_clipspace(currPos, currPos64Low, vec3(0.0), geometry.position);
next = project_position_to_clipspace(nextPos, nextPos64Low, vec3(0.0));
} else {
vec3 source_world = instanceSourcePositions;
vec3 target_world = instanceTargetPositions;
if (arc.useShortestPath) {
source_world.x = mod(source_world.x + 180., 360.0) - 180.;
target_world.x = mod(target_world.x + 180., 360.0) - 180.;
float deltaLng = target_world.x - source_world.x;
if (deltaLng > 180.) target_world.x -= 360.;
if (deltaLng < -180.) source_world.x -= 360.;
}
source = project_position(source_world, instanceSourcePositions64Low);
target = project_position(target_world, instanceTargetPositions64Low);
float antiMeridianX = 0.0;
if (arc.useShortestPath) {
if (project.projectionMode == PROJECTION_MODE_WEB_MERCATOR_AUTO_OFFSET) {
antiMeridianX = -(project.coordinateOrigin.x + 180.) / 360. * TILE_SIZE;
}
float thresholdRatio = (antiMeridianX - source.x) / (target.x - source.x);
if (prevSegmentRatio <= thresholdRatio && nextSegmentRatio > thresholdRatio) {
isValid = 0.0;
indexDir = sign(segmentRatio - thresholdRatio);
segmentRatio = thresholdRatio;
}
}
nextSegmentRatio = indexDir < 0.0 ? prevSegmentRatio : nextSegmentRatio;
vec3 currPos = interpolateFlat(source, target, segmentRatio);
vec3 nextPos = interpolateFlat(source, target, nextSegmentRatio);
if (arc.useShortestPath) {
if (nextPos.x < antiMeridianX) {
currPos.x += TILE_SIZE;
nextPos.x += TILE_SIZE;
}
}
curr = project_common_position_to_clipspace(vec4(currPos, 1.0));
next = project_common_position_to_clipspace(vec4(nextPos, 1.0));
geometry.position = vec4(currPos, 1.0);
}
float widthPixels = clamp(
project_size_to_pixel(instanceWidths * arc.widthScale, arc.widthUnits),
arc.widthMinPixels, arc.widthMaxPixels
);
vec3 offset = vec3(
getExtrusionOffset((next.xy - curr.xy) * indexDir, segmentSide, widthPixels),
0.0);
DECKGL_FILTER_SIZE(offset, geometry);
DECKGL_FILTER_GL_POSITION(curr, geometry);
gl_Position = curr + vec4(project_pixel_size_to_clipspace(offset.xy), 0.0, 0.0);
vec4 color = mix(instanceSourceColors, instanceTargetColors, segmentRatio);
vColor = vec4(color.rgb, color.a * layer.opacity);
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,it=`#version 300 es
#define SHADER_NAME arc-layer-fragment-shader
precision highp float;
in vec4 vColor;
in vec2 uv;
in float isValid;
out vec4 fragColor;
void main(void) {
if (isValid == 0.0) {
discard;
}
fragColor = vColor;
geometry.uv = uv;
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,H=[0,0,0,255],ot={getSourcePosition:{type:"accessor",value:n=>n.sourcePosition},getTargetPosition:{type:"accessor",value:n=>n.targetPosition},getSourceColor:{type:"accessor",value:H},getTargetColor:{type:"accessor",value:H},getWidth:{type:"accessor",value:1},getHeight:{type:"accessor",value:1},getTilt:{type:"accessor",value:0},greatCircle:!1,numSegments:{type:"number",value:50,min:1},widthUnits:"pixels",widthScale:{type:"number",value:1,min:0},widthMinPixels:{type:"number",value:0,min:0},widthMaxPixels:{type:"number",value:Number.MAX_SAFE_INTEGER,min:0}};class Fe extends E{getBounds(){return this.getAttributeManager()?.getBounds(["instanceSourcePositions","instanceTargetPositions"])}getShaders(){return super.getShaders({vs:tt,fs:it,modules:[z,O,et]})}get wrapLongitude(){return!1}initializeState(){this.getAttributeManager().addInstanced({instanceSourcePositions:{size:3,type:"float64",fp64:this.use64bitPositions(),transition:!0,accessor:"getSourcePosition"},instanceTargetPositions:{size:3,type:"float64",fp64:this.use64bitPositions(),transition:!0,accessor:"getTargetPosition"},instanceSourceColors:{size:this.props.colorFormat.length,type:"unorm8",transition:!0,accessor:"getSourceColor",defaultValue:H},instanceTargetColors:{size:this.props.colorFormat.length,type:"unorm8",transition:!0,accessor:"getTargetColor",defaultValue:H},instanceWidths:{size:1,transition:!0,accessor:"getWidth",defaultValue:1},instanceHeights:{size:1,transition:!0,accessor:"getHeight",defaultValue:1},instanceTilts:{size:1,transition:!0,accessor:"getTilt",defaultValue:0}})}updateState(e){super.updateState(e),e.changeFlags.extensionsChanged&&(this.state.model?.destroy(),this.state.model=this._getModel(),this.getAttributeManager().invalidateAll())}draw({uniforms:e}){const{widthUnits:t,widthScale:i,widthMinPixels:o,widthMaxPixels:s,greatCircle:r,wrapLongitude:a,numSegments:l}=this.props,c={numSegments:l,widthUnits:w[t],widthScale:i,widthMinPixels:o,widthMaxPixels:s,greatCircle:r,useShortestPath:a},d=this.state.model;d.shaderInputs.setProps({arc:c}),d.setVertexCount(l*2),d.draw(this.context.renderPass)}_getModel(){return new F(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),topology:"triangle-strip",isInstanced:!0})}}Fe.layerName="ArcLayer";Fe.defaultProps=ot;const st=new Uint32Array([0,2,1,0,3,2]),nt=new Float32Array([0,1,0,0,1,0,1,1]);function rt(n,e){if(!e)return at(n);const t=Math.max(Math.abs(n[0][0]-n[3][0]),Math.abs(n[1][0]-n[2][0])),i=Math.max(Math.abs(n[1][1]-n[0][1]),Math.abs(n[2][1]-n[3][1])),o=Math.ceil(t/e)+1,s=Math.ceil(i/e)+1,r=(o-1)*(s-1)*6,a=new Uint32Array(r),l=new Float32Array(o*s*2),c=new Float64Array(o*s*3);let d=0,g=0;for(let u=0;u<o;u++){const p=u/(o-1);for(let f=0;f<s;f++){const y=f/(s-1),h=lt(n,p,y);c[d*3+0]=h[0],c[d*3+1]=h[1],c[d*3+2]=h[2]||0,l[d*2+0]=p,l[d*2+1]=1-y,u>0&&f>0&&(a[g++]=d-s,a[g++]=d-s-1,a[g++]=d-1,a[g++]=d-s,a[g++]=d-1,a[g++]=d),d++}}return{vertexCount:r,positions:c,indices:a,texCoords:l}}function at(n){const e=new Float64Array(12);for(let t=0;t<n.length;t++)e[t*3+0]=n[t][0],e[t*3+1]=n[t][1],e[t*3+2]=n[t][2]||0;return{vertexCount:6,positions:e,indices:st,texCoords:nt}}function lt(n,e,t){return X(X(n[0],n[1],t),X(n[3],n[2],t),e)}const ce=`uniform bitmapUniforms {
  vec4 bounds;
  float coordinateConversion;
  float desaturate;
  vec3 tintColor;
  vec4 transparentColor;
} bitmap;
`,ct={name:"bitmap",vs:ce,fs:ce,uniformTypes:{bounds:"vec4<f32>",coordinateConversion:"f32",desaturate:"f32",tintColor:"vec3<f32>",transparentColor:"vec4<f32>"}},dt=`#version 300 es
#define SHADER_NAME bitmap-layer-vertex-shader

in vec2 texCoords;
in vec3 positions;
in vec3 positions64Low;

out vec2 vTexCoord;
out vec2 vTexPos;

const vec3 pickingColor = vec3(1.0, 0.0, 0.0);

void main(void) {
  geometry.worldPosition = positions;
  geometry.uv = texCoords;
  geometry.pickingColor = pickingColor;

  gl_Position = project_position_to_clipspace(positions, positions64Low, vec3(0.0), geometry.position);
  DECKGL_FILTER_GL_POSITION(gl_Position, geometry);

  vTexCoord = texCoords;

  if (bitmap.coordinateConversion < -0.5) {
    vTexPos = geometry.position.xy + project.commonOrigin.xy;
  } else if (bitmap.coordinateConversion > 0.5) {
    vTexPos = geometry.worldPosition.xy;
  }

  vec4 color = vec4(0.0);
  DECKGL_FILTER_COLOR(color, geometry);
}
`,gt=`
vec3 packUVsIntoRGB(vec2 uv) {
  // Extract the top 8 bits. We want values to be truncated down so we can add a fraction
  vec2 uv8bit = floor(uv * 256.);

  // Calculate the normalized remainders of u and v parts that do not fit into 8 bits
  // Scale and clamp to 0-1 range
  vec2 uvFraction = fract(uv * 256.);
  vec2 uvFraction4bit = floor(uvFraction * 16.);

  // Remainder can be encoded in blue channel, encode as 4 bits for pixel coordinates
  float fractions = uvFraction4bit.x + uvFraction4bit.y * 16.;

  return vec3(uv8bit, fractions) / 255.;
}
`,ut=`#version 300 es
#define SHADER_NAME bitmap-layer-fragment-shader

#ifdef GL_ES
precision highp float;
#endif

uniform sampler2D bitmapTexture;

in vec2 vTexCoord;
in vec2 vTexPos;

out vec4 fragColor;

/* projection utils */
const float TILE_SIZE = 512.0;
const float PI = 3.1415926536;
const float WORLD_SCALE = TILE_SIZE / PI / 2.0;

// from degrees to Web Mercator
vec2 lnglat_to_mercator(vec2 lnglat) {
  float x = lnglat.x;
  float y = clamp(lnglat.y, -89.9, 89.9);
  return vec2(
    radians(x) + PI,
    PI + log(tan(PI * 0.25 + radians(y) * 0.5))
  ) * WORLD_SCALE;
}

// from Web Mercator to degrees
vec2 mercator_to_lnglat(vec2 xy) {
  xy /= WORLD_SCALE;
  return degrees(vec2(
    xy.x - PI,
    atan(exp(xy.y - PI)) * 2.0 - PI * 0.5
  ));
}
/* End projection utils */

// apply desaturation
vec3 color_desaturate(vec3 color) {
  float luminance = (color.r + color.g + color.b) * 0.333333333;
  return mix(color, vec3(luminance), bitmap.desaturate);
}

// apply tint
vec3 color_tint(vec3 color) {
  return color * bitmap.tintColor;
}

// blend with background color
vec4 apply_opacity(vec3 color, float alpha) {
  if (bitmap.transparentColor.a == 0.0) {
    return vec4(color, alpha);
  }
  float blendedAlpha = alpha + bitmap.transparentColor.a * (1.0 - alpha);
  float highLightRatio = alpha / blendedAlpha;
  vec3 blendedRGB = mix(bitmap.transparentColor.rgb, color, highLightRatio);
  return vec4(blendedRGB, blendedAlpha);
}

vec2 getUV(vec2 pos) {
  return vec2(
    (pos.x - bitmap.bounds[0]) / (bitmap.bounds[2] - bitmap.bounds[0]),
    (pos.y - bitmap.bounds[3]) / (bitmap.bounds[1] - bitmap.bounds[3])
  );
}

${gt}

void main(void) {
  vec2 uv = vTexCoord;
  if (bitmap.coordinateConversion < -0.5) {
    vec2 lnglat = mercator_to_lnglat(vTexPos);
    uv = getUV(lnglat);
  } else if (bitmap.coordinateConversion > 0.5) {
    vec2 commonPos = lnglat_to_mercator(vTexPos);
    uv = getUV(commonPos);
  }
  vec4 bitmapColor = texture(bitmapTexture, uv);

  fragColor = apply_opacity(color_tint(color_desaturate(bitmapColor.rgb)), bitmapColor.a * layer.opacity);

  geometry.uv = uv;
  DECKGL_FILTER_COLOR(fragColor, geometry);

  if (bool(picking.isActive) && !bool(picking.isAttribute)) {
    // Since instance information is not used, we can use picking color for pixel index
    fragColor.rgb = packUVsIntoRGB(uv);
  }
}
`,pt={image:{type:"image",value:null,async:!0},bounds:{type:"array",value:[1,0,0,1],compare:!0},_imageCoordinateSystem:we.DEFAULT,desaturate:{type:"number",min:0,max:1,value:0},transparentColor:{type:"color",value:[0,0,0,0]},tintColor:{type:"color",value:[255,255,255]},textureParameters:{type:"object",ignore:!0,value:null}};class ke extends E{getShaders(){return super.getShaders({vs:dt,fs:ut,modules:[z,O,ct]})}initializeState(){const e=this.getAttributeManager();e.remove(["instancePickingColors"]);const t=!0;e.add({indices:{size:1,isIndexed:!0,update:i=>i.value=this.state.mesh.indices,noAlloc:t},positions:{size:3,type:"float64",fp64:this.use64bitPositions(),update:i=>i.value=this.state.mesh.positions,noAlloc:t},texCoords:{size:2,update:i=>i.value=this.state.mesh.texCoords,noAlloc:t}})}updateState({props:e,oldProps:t,changeFlags:i}){const o=this.getAttributeManager();if(i.extensionsChanged&&(this.state.model?.destroy(),this.state.model=this._getModel(),o.invalidateAll()),e.bounds!==t.bounds){const s=this.state.mesh,r=this._createMesh();this.state.model.setVertexCount(r.vertexCount);for(const a in r)s&&s[a]!==r[a]&&o.invalidate(a);this.setState({mesh:r,...this._getCoordinateUniforms()})}else e._imageCoordinateSystem!==t._imageCoordinateSystem&&this.setState(this._getCoordinateUniforms())}getPickingInfo(e){const{image:t}=this.props,i=e.info;if(!i.color||!t)return i.bitmap=null,i;const{width:o,height:s}=t;i.index=0;const r=ft(i.color);return i.bitmap={size:{width:o,height:s},uv:r,pixel:[Math.floor(r[0]*o),Math.floor(r[1]*s)]},i}disablePickingIndex(){this.setState({disablePicking:!0})}restorePickingColors(){this.setState({disablePicking:!1})}_updateAutoHighlight(e){super._updateAutoHighlight({...e,color:this.encodePickingColor(0)})}_createMesh(){const{bounds:e}=this.props;let t=e;return de(e)&&(t=[[e[0],e[1]],[e[0],e[3]],[e[2],e[3]],[e[2],e[1]]]),rt(t,this.context.viewport.resolution)}_getModel(){return new F(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),topology:"triangle-list",isInstanced:!1})}draw(e){const{shaderModuleProps:t}=e,{model:i,coordinateConversion:o,bounds:s,disablePicking:r}=this.state,{image:a,desaturate:l,transparentColor:c,tintColor:d}=this.props;if(!(t.picking.isActive&&r)&&a&&i){const g={bitmapTexture:a,bounds:s,coordinateConversion:o,desaturate:l,tintColor:d.slice(0,3).map(u=>u/255),transparentColor:c.map(u=>u/255)};i.shaderInputs.setProps({bitmap:g}),i.draw(this.context.renderPass)}}_getCoordinateUniforms(){const{LNGLAT:e,CARTESIAN:t,DEFAULT:i}=we;let{_imageCoordinateSystem:o}=this.props;if(o!==i){const{bounds:s}=this.props;if(!de(s))throw new Error("_imageCoordinateSystem only supports rectangular bounds");const r=this.context.viewport.resolution?e:t;if(o=o===e?e:t,o===e&&r===t)return{coordinateConversion:-1,bounds:s};if(o===t&&r===e){const a=ae([s[0],s[1]]),l=ae([s[2],s[3]]);return{coordinateConversion:1,bounds:[a[0],a[1],l[0],l[1]]}}}return{coordinateConversion:0,bounds:[0,0,0,0]}}}ke.layerName="BitmapLayer";ke.defaultProps=pt;function ft(n){const[e,t,i]=n,o=(i&240)/256,s=(i&15)/16;return[(e+s)/256,(t+o)/256]}function de(n){return Number.isFinite(n[0])}const ge=`uniform iconUniforms {
  float sizeScale;
  vec2 iconsTextureDim;
  float sizeBasis;
  float sizeMinPixels;
  float sizeMaxPixels;
  bool billboard;
  highp int sizeUnits;
  float alphaCutoff;
} icon;
`,ht={name:"icon",vs:ge,fs:ge,uniformTypes:{sizeScale:"f32",iconsTextureDim:"vec2<f32>",sizeBasis:"f32",sizeMinPixels:"f32",sizeMaxPixels:"f32",billboard:"f32",sizeUnits:"i32",alphaCutoff:"f32"}},yt=`#version 300 es
#define SHADER_NAME icon-layer-vertex-shader
in vec2 positions;
in vec3 instancePositions;
in vec3 instancePositions64Low;
in float instanceSizes;
in float instanceAngles;
in vec4 instanceColors;
in vec3 instancePickingColors;
in vec4 instanceIconFrames;
in float instanceColorModes;
in vec2 instanceOffsets;
in vec2 instancePixelOffset;
out float vColorMode;
out vec4 vColor;
out vec2 vTextureCoords;
out vec2 uv;
vec2 rotate_by_angle(vec2 vertex, float angle) {
float angle_radian = angle * PI / 180.0;
float cos_angle = cos(angle_radian);
float sin_angle = sin(angle_radian);
mat2 rotationMatrix = mat2(cos_angle, -sin_angle, sin_angle, cos_angle);
return rotationMatrix * vertex;
}
void main(void) {
geometry.worldPosition = instancePositions;
geometry.uv = positions;
geometry.pickingColor = instancePickingColors;
uv = positions;
vec2 iconSize = instanceIconFrames.zw;
float sizePixels = clamp(
project_size_to_pixel(instanceSizes * icon.sizeScale, icon.sizeUnits),
icon.sizeMinPixels, icon.sizeMaxPixels
);
float iconConstraint = icon.sizeBasis == 0.0 ? iconSize.x : iconSize.y;
float instanceScale = iconConstraint == 0.0 ? 0.0 : sizePixels / iconConstraint;
vec2 pixelOffset = positions / 2.0 * iconSize + instanceOffsets;
pixelOffset = rotate_by_angle(pixelOffset, instanceAngles) * instanceScale;
pixelOffset += instancePixelOffset;
pixelOffset.y *= -1.0;
if (icon.billboard)  {
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, vec3(0.0), geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
vec3 offset = vec3(pixelOffset, 0.0);
DECKGL_FILTER_SIZE(offset, geometry);
gl_Position.xy += project_pixel_size_to_clipspace(offset.xy);
} else {
vec3 offset_common = vec3(project_pixel_size(pixelOffset), 0.0);
DECKGL_FILTER_SIZE(offset_common, geometry);
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, offset_common, geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
}
vTextureCoords = mix(
instanceIconFrames.xy,
instanceIconFrames.xy + iconSize,
(positions.xy + 1.0) / 2.0
) / icon.iconsTextureDim;
vColor = instanceColors;
DECKGL_FILTER_COLOR(vColor, geometry);
vColorMode = instanceColorModes;
}
`,mt=`#version 300 es
#define SHADER_NAME icon-layer-fragment-shader
precision highp float;
uniform sampler2D iconsTexture;
in float vColorMode;
in vec4 vColor;
in vec2 vTextureCoords;
in vec2 uv;
out vec4 fragColor;
void main(void) {
geometry.uv = uv;
vec4 texColor = texture(iconsTexture, vTextureCoords);
vec3 color = mix(texColor.rgb, vColor.rgb, vColorMode);
float a = texColor.a * layer.opacity * vColor.a;
if (a < icon.alphaCutoff) {
discard;
}
fragColor = vec4(color, a);
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,vt=1024,xt=4,ue=()=>{},pe={minFilter:"linear",mipmapFilter:"linear",magFilter:"linear",addressModeU:"clamp-to-edge",addressModeV:"clamp-to-edge"},Pt={x:0,y:0,width:0,height:0};function Ct(n){return Math.pow(2,Math.ceil(Math.log2(n)))}function _t(n,e,t,i){const o=Math.min(t/e.width,i/e.height),s=Math.floor(e.width*o),r=Math.floor(e.height*o);return o===1?{image:e,width:s,height:r}:(n.canvas.height=r,n.canvas.width=s,n.clearRect(0,0,s,r),n.drawImage(e,0,0,e.width,e.height,0,0,s,r),{image:n.canvas,width:s,height:r})}function B(n){return n&&(n.id||n.url)}function Lt(n,e,t,i){const{width:o,height:s,device:r}=n,a=r.createTexture({format:"rgba8unorm",width:e,height:t,sampler:i,mipLevels:r.getMipLevelCount(e,t)}),l=r.createCommandEncoder();return l.copyTextureToTexture({sourceTexture:n,destinationTexture:a,width:o,height:s}),l.finish(),a.generateMipmapsWebGL(),n.destroy(),a}function fe(n,e,t){for(let i=0;i<e.length;i++){const{icon:o,xOffset:s}=e[i],r=B(o);n[r]={...o,x:s,y:t}}}function bt({icons:n,buffer:e,mapping:t={},xOffset:i=0,yOffset:o=0,rowHeight:s=0,canvasWidth:r}){let a=[];for(let l=0;l<n.length;l++){const c=n[l],d=B(c);if(!t[d]){const{height:g,width:u}=c;i+u+e>r&&(fe(t,a,o),i=0,o=s+o+e,s=0,a=[]),a.push({icon:c,xOffset:i}),i=i+u+e,s=Math.max(s,g)}}return a.length>0&&fe(t,a,o),{mapping:t,rowHeight:s,xOffset:i,yOffset:o,canvasWidth:r,canvasHeight:Ct(s+o+e)}}function St(n,e,t){if(!n||!e)return null;t=t||{};const i={},{iterable:o,objectInfo:s}=te(n);for(const r of o){s.index++;const a=e(r,s),l=B(a);if(!a)throw new Error("Icon is missing.");if(!a.url)throw new Error("Icon url is missing.");!i[l]&&(!t[l]||a.url!==t[l].url)&&(i[l]={...a,source:r,sourceIndex:s.index})}return i}class Tt{constructor(e,{onUpdate:t=ue,onError:i=ue}){this._loadOptions=null,this._texture=null,this._externalTexture=null,this._mapping={},this._samplerParameters=null,this._pendingCount=0,this._autoPacking=!1,this._xOffset=0,this._yOffset=0,this._rowHeight=0,this._buffer=xt,this._canvasWidth=vt,this._canvasHeight=0,this._canvas=null,this.device=e,this.onUpdate=t,this.onError=i}finalize(){this._texture?.delete()}getTexture(){return this._texture||this._externalTexture}getIconMapping(e){const t=this._autoPacking?B(e):e;return this._mapping[t]||Pt}setProps({loadOptions:e,autoPacking:t,iconAtlas:i,iconMapping:o,textureParameters:s}){e&&(this._loadOptions=e),t!==void 0&&(this._autoPacking=t),o&&(this._mapping=o),i&&(this._texture?.delete(),this._texture=null,this._externalTexture=i),s&&(this._samplerParameters=s)}get isLoaded(){return this._pendingCount===0}packIcons(e,t){if(!this._autoPacking||typeof document>"u")return;const i=Object.values(St(e,t,this._mapping)||{});if(i.length>0){const{mapping:o,xOffset:s,yOffset:r,rowHeight:a,canvasHeight:l}=bt({icons:i,buffer:this._buffer,canvasWidth:this._canvasWidth,mapping:this._mapping,rowHeight:this._rowHeight,xOffset:this._xOffset,yOffset:this._yOffset});this._rowHeight=a,this._mapping=o,this._xOffset=s,this._yOffset=r,this._canvasHeight=l,this._texture||(this._texture=this.device.createTexture({format:"rgba8unorm",data:null,width:this._canvasWidth,height:this._canvasHeight,sampler:this._samplerParameters||pe,mipLevels:this.device.getMipLevelCount(this._canvasWidth,this._canvasHeight)})),this._texture.height!==this._canvasHeight&&(this._texture=Lt(this._texture,this._canvasWidth,this._canvasHeight,this._samplerParameters||pe)),this.onUpdate(!0),this._canvas=this._canvas||document.createElement("canvas"),this._loadIcons(i)}}_loadIcons(e){const t=this._canvas.getContext("2d",{willReadFrequently:!0});for(const i of e)this._pendingCount++,Qe(i.url,this._loadOptions).then(o=>{const s=B(i),r=this._mapping[s],{x:a,y:l,width:c,height:d}=r,{image:g,width:u,height:p}=_t(t,o,c,d),f=a+(c-u)/2,y=l+(d-p)/2;this._texture?.copyExternalImage({image:g,x:f,y,width:u,height:p}),r.x=f,r.y=y,r.width=u,r.height=p,this._texture?.generateMipmapsWebGL(),this.onUpdate(u!==c||p!==d)}).catch(o=>{this.onError({url:i.url,source:i.source,sourceIndex:i.sourceIndex,loadOptions:this._loadOptions,error:o})}).finally(()=>{this._pendingCount--})}}const We=[0,0,0,255],Rt={iconAtlas:{type:"image",value:null,async:!0},iconMapping:{type:"object",value:{},async:!0},sizeScale:{type:"number",value:1,min:0},billboard:!0,sizeUnits:"pixels",sizeBasis:"height",sizeMinPixels:{type:"number",min:0,value:0},sizeMaxPixels:{type:"number",min:0,value:Number.MAX_SAFE_INTEGER},alphaCutoff:{type:"number",value:.05,min:0,max:1},getPosition:{type:"accessor",value:n=>n.position},getIcon:{type:"accessor",value:n=>n.icon},getColor:{type:"accessor",value:We},getSize:{type:"accessor",value:1},getAngle:{type:"accessor",value:0},getPixelOffset:{type:"accessor",value:[0,0]},onIconError:{type:"function",value:null,optional:!0},textureParameters:{type:"object",ignore:!0,value:null}};class Z extends E{getShaders(){return super.getShaders({vs:yt,fs:mt,modules:[z,O,ht]})}initializeState(){this.state={iconManager:new Tt(this.context.device,{onUpdate:this._onUpdate.bind(this),onError:this._onError.bind(this)})},this.getAttributeManager().addInstanced({instancePositions:{size:3,type:"float64",fp64:this.use64bitPositions(),transition:!0,accessor:"getPosition"},instanceSizes:{size:1,transition:!0,accessor:"getSize",defaultValue:1},instanceOffsets:{size:2,accessor:"getIcon",transform:this.getInstanceOffset},instanceIconFrames:{size:4,accessor:"getIcon",transform:this.getInstanceIconFrame},instanceColorModes:{size:1,type:"uint8",accessor:"getIcon",transform:this.getInstanceColorMode},instanceColors:{size:this.props.colorFormat.length,type:"unorm8",transition:!0,accessor:"getColor",defaultValue:We},instanceAngles:{size:1,transition:!0,accessor:"getAngle"},instancePixelOffset:{size:2,transition:!0,accessor:"getPixelOffset"}})}updateState(e){super.updateState(e);const{props:t,oldProps:i,changeFlags:o}=e,s=this.getAttributeManager(),{iconAtlas:r,iconMapping:a,data:l,getIcon:c,textureParameters:d}=t,{iconManager:g}=this.state;if(typeof r=="string")return;const u=r||this.internalState.isAsyncPropLoading("iconAtlas");g.setProps({loadOptions:t.loadOptions,autoPacking:!u,iconAtlas:r,iconMapping:u?a:null,textureParameters:d}),u?i.iconMapping!==t.iconMapping&&s.invalidate("getIcon"):(o.dataChanged||o.updateTriggersChanged&&(o.updateTriggersChanged.all||o.updateTriggersChanged.getIcon))&&g.packIcons(l,c),o.extensionsChanged&&(this.state.model?.destroy(),this.state.model=this._getModel(),s.invalidateAll())}get isLoaded(){return super.isLoaded&&this.state.iconManager.isLoaded}finalizeState(e){super.finalizeState(e),this.state.iconManager.finalize()}draw({uniforms:e}){const{sizeScale:t,sizeBasis:i,sizeMinPixels:o,sizeMaxPixels:s,sizeUnits:r,billboard:a,alphaCutoff:l}=this.props,{iconManager:c}=this.state,d=c.getTexture();if(d){const g=this.state.model,u={iconsTexture:d,iconsTextureDim:[d.width,d.height],sizeUnits:w[r],sizeScale:t,sizeBasis:i==="height"?1:0,sizeMinPixels:o,sizeMaxPixels:s,billboard:a,alphaCutoff:l};g.shaderInputs.setProps({icon:u}),g.draw(this.context.renderPass)}}_getModel(){const e=[-1,-1,1,-1,-1,1,1,1];return new F(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),geometry:new K({topology:"triangle-strip",attributes:{positions:{size:2,value:new Float32Array(e)}}}),isInstanced:!0})}_onUpdate(e){e?(this.getAttributeManager()?.invalidate("getIcon"),this.setNeedsUpdate()):this.setNeedsRedraw()}_onError(e){const t=this.getCurrentLayer()?.props.onIconError;t?t(e):T.error(e.error.message)()}getInstanceOffset(e){const{width:t,height:i,anchorX:o=t/2,anchorY:s=i/2}=this.state.iconManager.getIconMapping(e);return[t/2-o,i/2-s]}getInstanceColorMode(e){return this.state.iconManager.getIconMapping(e).mask?1:0}getInstanceIconFrame(e){const{x:t,y:i,width:o,height:s}=this.state.iconManager.getIconMapping(e);return[t,i,o,s]}}Z.defaultProps=Rt;Z.layerName="IconLayer";const It=`struct PointCloudUniforms {
  radiusPixels: f32,
  sizeUnits: i32,
};

@group(0) @binding(3)
var<uniform> pointCloud: PointCloudUniforms;
`,he=`uniform pointCloudUniforms {
  float radiusPixels;
  highp int sizeUnits;
} pointCloud;
`,Mt={name:"pointCloud",source:It,vs:he,fs:he,uniformTypes:{radiusPixels:"f32",sizeUnits:"i32"}},At=`#version 300 es
#define SHADER_NAME point-cloud-layer-vertex-shader
in vec3 positions;
in vec3 instanceNormals;
in vec4 instanceColors;
in vec3 instancePositions;
in vec3 instancePositions64Low;
in vec3 instancePickingColors;
out vec4 vColor;
out vec2 unitPosition;
void main(void) {
geometry.worldPosition = instancePositions;
geometry.normal = project_normal(instanceNormals);
unitPosition = positions.xy;
geometry.uv = unitPosition;
geometry.pickingColor = instancePickingColors;
vec3 offset = vec3(positions.xy * project_size_to_pixel(pointCloud.radiusPixels, pointCloud.sizeUnits), 0.0);
DECKGL_FILTER_SIZE(offset, geometry);
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, vec3(0.), geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
gl_Position.xy += project_pixel_size_to_clipspace(offset.xy);
vec3 lightColor = lighting_getLightColor(instanceColors.rgb, project.cameraPosition, geometry.position.xyz, geometry.normal);
vColor = vec4(lightColor, instanceColors.a * layer.opacity);
DECKGL_FILTER_COLOR(vColor, geometry);
}
`,wt=`#version 300 es
#define SHADER_NAME point-cloud-layer-fragment-shader
precision highp float;
in vec4 vColor;
in vec2 unitPosition;
out vec4 fragColor;
void main(void) {
geometry.uv = unitPosition.xy;
float distToCenter = length(unitPosition);
if (distToCenter > 1.0) {
discard;
}
fragColor = vColor;
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,Et=`struct ConstantAttributes {
  instanceNormals: vec3<f32>,
  instanceColors: vec4<f32>,
  instancePositions: vec3<f32>,
  instancePositions64Low: vec3<f32>,
  instancePickingColors: vec3<f32>
};

const constants = ConstantAttributes(
  vec3<f32>(1.0, 0.0, 0.0),
  vec4<f32>(0.0, 0.0, 0.0, 1.0),
  vec3<f32>(0.0),
  vec3<f32>(0.0),
  vec3<f32>(0.0)
);

struct Attributes {
  @builtin(instance_index) instanceIndex : u32,
  @builtin(vertex_index) vertexIndex : u32,
  @location(0) positions: vec3<f32>,
  @location(1) instancePositions: vec3<f32>,
  @location(2) instancePositions64Low: vec3<f32>,
  @location(3) instanceNormals: vec3<f32>,
  @location(4) instanceColors: vec4<f32>,
  @location(5) instancePickingColors: vec3<f32>
};

struct Varyings {
  @builtin(position) position: vec4<f32>,
  @location(0) vColor: vec4<f32>,
  @location(1) unitPosition: vec2<f32>,
};

@vertex
fn vertexMain(attributes: Attributes) -> Varyings {
  var varyings: Varyings;
  
  // var geometry: Geometry;
  // geometry.worldPosition = instancePositions;
  // geometry.normal = project_normal(instanceNormals);

  // position on the containing square in [-1, 1] space
  varyings.unitPosition = attributes.positions.xy;
  geometry.uv = varyings.unitPosition;
  geometry.pickingColor = attributes.instancePickingColors;

  // Find the center of the point and add the current vertex
  let offset = vec3<f32>(attributes.positions.xy * project_unit_size_to_pixel(pointCloud.radiusPixels, pointCloud.sizeUnits), 0.0);
  // DECKGL_FILTER_SIZE(offset, geometry);

  varyings.position = project_position_to_clipspace(attributes.instancePositions, attributes.instancePositions64Low, vec3<f32>(0.0)); // TODO , geometry.position);
  // DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
  let clipPixels = project_pixel_size_to_clipspace(offset.xy);
  varyings.position.x += clipPixels.x;
  varyings.position.y += clipPixels.y;

  // Apply lighting
  let lightColor = lighting_getLightColor2(attributes.instanceColors.rgb, project.cameraPosition, geometry.position.xyz, geometry.normal);

  // Apply opacity to instance color, or return instance picking color
  varyings.vColor = vec4(lightColor, attributes.instanceColors.a * color.opacity);
  // DECKGL_FILTER_COLOR(vColor, geometry);

  return varyings;
}

@fragment
fn fragmentMain(varyings: Varyings) -> @location(0) vec4<f32> {
  // var geometry: Geometry;
  // geometry.uv = unitPosition.xy;

  let distToCenter = length(varyings.unitPosition);
  if (distToCenter > 1.0) {
    discard;
  }

  var fragColor: vec4<f32>;

  fragColor = varyings.vColor;
  // DECKGL_FILTER_COLOR(fragColor, geometry);

  // Apply premultiplied alpha as required by transparent canvas
  fragColor = deckgl_premultiplied_alpha(fragColor);

  return fragColor;
}
`,De=[0,0,0,255],Be=[0,0,1],zt={sizeUnits:"pixels",pointSize:{type:"number",min:0,value:10},getPosition:{type:"accessor",value:n=>n.position},getNormal:{type:"accessor",value:Be},getColor:{type:"accessor",value:De},material:!0,radiusPixels:{deprecatedFor:"pointSize"}};function Ot(n){const{header:e,attributes:t}=n;if(!(!e||!t)&&(n.length=e.vertexCount,t.POSITION&&(t.instancePositions=t.POSITION),t.NORMAL&&(t.instanceNormals=t.NORMAL),t.COLOR_0)){const{size:i,value:o}=t.COLOR_0;t.instanceColors={size:i,type:"unorm8",value:o}}}class Ue extends E{getShaders(){return super.getShaders({vs:At,fs:wt,source:Et,modules:[z,Ee,Ye,O,Mt]})}initializeState(){this.getAttributeManager().addInstanced({instancePositions:{size:3,type:"float64",fp64:this.use64bitPositions(),transition:!0,accessor:"getPosition"},instanceNormals:{size:3,transition:!0,accessor:"getNormal",defaultValue:Be},instanceColors:{size:this.props.colorFormat.length,type:"unorm8",transition:!0,accessor:"getColor",defaultValue:De}})}updateState(e){const{changeFlags:t,props:i}=e;super.updateState(e),t.extensionsChanged&&(this.state.model?.destroy(),this.state.model=this._getModel(),this.getAttributeManager().invalidateAll()),t.dataChanged&&Ot(i.data)}draw({uniforms:e}){const{pointSize:t,sizeUnits:i}=this.props,o=this.state.model,s={sizeUnits:w[i],radiusPixels:t};o.shaderInputs.setProps({pointCloud:s}),this.context.device.type==="webgpu"&&(o.instanceCount=this.props.data.length),o.draw(this.context.renderPass)}_getModel(){const e=this.context.device.type==="webgpu"?{depthWriteEnabled:!0,depthCompare:"less-equal"}:void 0,t=[];for(let i=0;i<3;i++){const o=i/3*Math.PI*2;t.push(Math.cos(o)*2,Math.sin(o)*2,0)}return new F(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),geometry:new K({topology:"triangle-list",attributes:{positions:new Float32Array(t)}}),parameters:e,isInstanced:!0})}}Ue.layerName="PointCloudLayer";Ue.defaultProps=zt;const ye=`uniform scatterplotUniforms {
  float radiusScale;
  float radiusMinPixels;
  float radiusMaxPixels;
  float lineWidthScale;
  float lineWidthMinPixels;
  float lineWidthMaxPixels;
  float stroked;
  float filled;
  bool antialiasing;
  bool billboard;
  highp int radiusUnits;
  highp int lineWidthUnits;
} scatterplot;
`,Ft={name:"scatterplot",vs:ye,fs:ye,source:"",uniformTypes:{radiusScale:"f32",radiusMinPixels:"f32",radiusMaxPixels:"f32",lineWidthScale:"f32",lineWidthMinPixels:"f32",lineWidthMaxPixels:"f32",stroked:"f32",filled:"f32",antialiasing:"f32",billboard:"f32",radiusUnits:"i32",lineWidthUnits:"i32"}},kt=`#version 300 es
#define SHADER_NAME scatterplot-layer-vertex-shader
in vec3 positions;
in vec3 instancePositions;
in vec3 instancePositions64Low;
in float instanceRadius;
in float instanceLineWidths;
in vec4 instanceFillColors;
in vec4 instanceLineColors;
in vec3 instancePickingColors;
out vec4 vFillColor;
out vec4 vLineColor;
out vec2 unitPosition;
out float innerUnitRadius;
out float outerRadiusPixels;
void main(void) {
geometry.worldPosition = instancePositions;
outerRadiusPixels = clamp(
project_size_to_pixel(scatterplot.radiusScale * instanceRadius, scatterplot.radiusUnits),
scatterplot.radiusMinPixels, scatterplot.radiusMaxPixels
);
float lineWidthPixels = clamp(
project_size_to_pixel(scatterplot.lineWidthScale * instanceLineWidths, scatterplot.lineWidthUnits),
scatterplot.lineWidthMinPixels, scatterplot.lineWidthMaxPixels
);
outerRadiusPixels += scatterplot.stroked * lineWidthPixels / 2.0;
float edgePadding = scatterplot.antialiasing ? (outerRadiusPixels + SMOOTH_EDGE_RADIUS) / outerRadiusPixels : 1.0;
unitPosition = edgePadding * positions.xy;
geometry.uv = unitPosition;
geometry.pickingColor = instancePickingColors;
innerUnitRadius = 1.0 - scatterplot.stroked * lineWidthPixels / outerRadiusPixels;
if (scatterplot.billboard) {
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, vec3(0.0), geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
vec3 offset = edgePadding * positions * outerRadiusPixels;
DECKGL_FILTER_SIZE(offset, geometry);
gl_Position.xy += project_pixel_size_to_clipspace(offset.xy);
} else {
vec3 offset = edgePadding * positions * project_pixel_size(outerRadiusPixels);
DECKGL_FILTER_SIZE(offset, geometry);
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, offset, geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
}
vFillColor = vec4(instanceFillColors.rgb, instanceFillColors.a * layer.opacity);
DECKGL_FILTER_COLOR(vFillColor, geometry);
vLineColor = vec4(instanceLineColors.rgb, instanceLineColors.a * layer.opacity);
DECKGL_FILTER_COLOR(vLineColor, geometry);
}
`,Wt=`#version 300 es
#define SHADER_NAME scatterplot-layer-fragment-shader
precision highp float;
in vec4 vFillColor;
in vec4 vLineColor;
in vec2 unitPosition;
in float innerUnitRadius;
in float outerRadiusPixels;
out vec4 fragColor;
void main(void) {
geometry.uv = unitPosition;
float distToCenter = length(unitPosition) * outerRadiusPixels;
float inCircle = scatterplot.antialiasing ?
smoothedge(distToCenter, outerRadiusPixels) :
step(distToCenter, outerRadiusPixels);
if (inCircle == 0.0) {
discard;
}
if (scatterplot.stroked > 0.5) {
float isLine = scatterplot.antialiasing ?
smoothedge(innerUnitRadius * outerRadiusPixels, distToCenter) :
step(innerUnitRadius * outerRadiusPixels, distToCenter);
if (scatterplot.filled > 0.5) {
fragColor = mix(vFillColor, vLineColor, isLine);
} else {
if (isLine == 0.0) {
discard;
}
fragColor = vec4(vLineColor.rgb, vLineColor.a * isLine);
}
} else if (scatterplot.filled < 0.5) {
discard;
} else {
fragColor = vFillColor;
}
fragColor.a *= inCircle;
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,Dt=`// Main shaders

struct ScatterplotUniforms {
  radiusScale: f32,
  radiusMinPixels: f32,
  radiusMaxPixels: f32,
  lineWidthScale: f32,
  lineWidthMinPixels: f32,
  lineWidthMaxPixels: f32,
  stroked: f32,
  filled: i32,
  antialiasing: i32,
  billboard: i32,
  radiusUnits: i32,
  lineWidthUnits: i32,
};

struct ConstantAttributeUniforms {
 instancePositions: vec3<f32>,
 instancePositions64Low: vec3<f32>,
 instanceRadius: f32,
 instanceLineWidths: f32,
 instanceFillColors: vec4<f32>,
 instanceLineColors: vec4<f32>,
 instancePickingColors: vec3<f32>,

 instancePositionsConstant: i32,
 instancePositions64LowConstant: i32,
 instanceRadiusConstant: i32,
 instanceLineWidthsConstant: i32,
 instanceFillColorsConstant: i32,
 instanceLineColorsConstant: i32,
 instancePickingColorsConstant: i32
};

@group(0) @binding(2) var<uniform> scatterplot: ScatterplotUniforms;

struct ConstantAttributes {
  instancePositions: vec3<f32>,
  instancePositions64Low: vec3<f32>,
  instanceRadius: f32,
  instanceLineWidths: f32,
  instanceFillColors: vec4<f32>,
  instanceLineColors: vec4<f32>,
  instancePickingColors: vec3<f32>
};

const constants = ConstantAttributes(
  vec3<f32>(0.0),
  vec3<f32>(0.0),
  0.0,
  0.0,
  vec4<f32>(0.0, 0.0, 0.0, 1.0),
  vec4<f32>(0.0, 0.0, 0.0, 1.0),
  vec3<f32>(0.0)
);

struct Attributes {
  @builtin(instance_index) instanceIndex : u32,
  @builtin(vertex_index) vertexIndex : u32,
  @location(0) positions: vec3<f32>,
  @location(1) instancePositions: vec3<f32>,
  @location(2) instancePositions64Low: vec3<f32>,
  @location(3) instanceRadius: f32,
  @location(4) instanceLineWidths: f32,
  @location(5) instanceFillColors: vec4<f32>,
  @location(6) instanceLineColors: vec4<f32>,
  @location(7) instancePickingColors: vec3<f32>
};

struct Varyings {
  @builtin(position) position: vec4<f32>,
  @location(0) vFillColor: vec4<f32>,
  @location(1) vLineColor: vec4<f32>,
  @location(2) unitPosition: vec2<f32>,
  @location(3) innerUnitRadius: f32,
  @location(4) outerRadiusPixels: f32,
};

@vertex
fn vertexMain(attributes: Attributes) -> Varyings {
  var varyings: Varyings;

  // Draw an inline geometry constant array clip space triangle to verify that rendering works.
  // var positions = array<vec2<f32>, 3>(vec2(0.0, 0.5), vec2(-0.5, -0.5), vec2(0.5, -0.5));
  // if (attributes.instanceIndex == 0) {
  //   varyings.position = vec4<f32>(positions[attributes.vertexIndex], 0.0, 1.0);
  //   return varyings;
  // }

  // var geometry: Geometry;
  // geometry.worldPosition = instancePositions;

  // Multiply out radius and clamp to limits
  varyings.outerRadiusPixels = clamp(
    project_unit_size_to_pixel(scatterplot.radiusScale * attributes.instanceRadius, scatterplot.radiusUnits),
    scatterplot.radiusMinPixels, scatterplot.radiusMaxPixels
  );

  // Multiply out line width and clamp to limits
  let lineWidthPixels = clamp(
    project_unit_size_to_pixel(scatterplot.lineWidthScale * attributes.instanceLineWidths, scatterplot.lineWidthUnits),
    scatterplot.lineWidthMinPixels, scatterplot.lineWidthMaxPixels
  );

  // outer radius needs to offset by half stroke width
  varyings.outerRadiusPixels += scatterplot.stroked * lineWidthPixels / 2.0;
  // Expand geometry to accommodate edge smoothing
  let edgePadding = select(
    (varyings.outerRadiusPixels + SMOOTH_EDGE_RADIUS) / varyings.outerRadiusPixels,
    1.0,
    scatterplot.antialiasing != 0
  );

  // position on the containing square in [-1, 1] space
  varyings.unitPosition = edgePadding * attributes.positions.xy;
  geometry.uv = varyings.unitPosition;
  geometry.pickingColor = attributes.instancePickingColors;

  varyings.innerUnitRadius = 1.0 - scatterplot.stroked * lineWidthPixels / varyings.outerRadiusPixels;

  if (scatterplot.billboard != 0) {
    varyings.position = project_position_to_clipspace(attributes.instancePositions, attributes.instancePositions64Low, vec3<f32>(0.0)); // TODO , geometry.position);
    // DECKGL_FILTER_GL_POSITION(varyings.position, geometry);
    let offset = attributes.positions; // * edgePadding * varyings.outerRadiusPixels;
    // DECKGL_FILTER_SIZE(offset, geometry);
    let clipPixels = project_pixel_size_to_clipspace(offset.xy);
    varyings.position.x = clipPixels.x;
    varyings.position.y = clipPixels.y;
  } else {
    let offset = edgePadding * attributes.positions * project_pixel_size_float(varyings.outerRadiusPixels);
    // DECKGL_FILTER_SIZE(offset, geometry);
    varyings.position = project_position_to_clipspace(attributes.instancePositions, attributes.instancePositions64Low, offset); // TODO , geometry.position);
    // DECKGL_FILTER_GL_POSITION(varyings.position, geometry);
  }

  // Apply opacity to instance color, or return instance picking color
  varyings.vFillColor = vec4<f32>(attributes.instanceFillColors.rgb, attributes.instanceFillColors.a * color.opacity);
  // DECKGL_FILTER_COLOR(varyings.vFillColor, geometry);
  varyings.vLineColor = vec4<f32>(attributes.instanceLineColors.rgb, attributes.instanceLineColors.a * color.opacity);
  // DECKGL_FILTER_COLOR(varyings.vLineColor, geometry);

  return varyings;
}

@fragment
fn fragmentMain(varyings: Varyings) -> @location(0) vec4<f32> {
  // var geometry: Geometry;
  // geometry.uv = unitPosition;

  let distToCenter = length(varyings.unitPosition) * varyings.outerRadiusPixels;
  let inCircle = select(
    smoothedge(distToCenter, varyings.outerRadiusPixels),
    step(distToCenter, varyings.outerRadiusPixels),
    scatterplot.antialiasing != 0
  );

  if (inCircle == 0.0) {
    discard;
  }

  var fragColor: vec4<f32>;

  if (scatterplot.stroked != 0) {
    let isLine = select(
      smoothedge(varyings.innerUnitRadius * varyings.outerRadiusPixels, distToCenter),
      step(varyings.innerUnitRadius * varyings.outerRadiusPixels, distToCenter),
      scatterplot.antialiasing != 0
    );

    if (scatterplot.filled != 0) {
      fragColor = mix(varyings.vFillColor, varyings.vLineColor, isLine);
    } else {
      if (isLine == 0.0) {
        discard;
      }
      fragColor = vec4<f32>(varyings.vLineColor.rgb, varyings.vLineColor.a * isLine);
    }
  } else if (scatterplot.filled == 0) {
    discard;
  } else {
    fragColor = varyings.vFillColor;
  }

  fragColor.a *= inCircle;
  // DECKGL_FILTER_COLOR(fragColor, geometry);

  // Apply premultiplied alpha as required by transparent canvas
  fragColor = deckgl_premultiplied_alpha(fragColor);

  return fragColor;
  // return vec4<f32>(0, 0, 1, 1);
}
`,me=[0,0,0,255],Bt={radiusUnits:"meters",radiusScale:{type:"number",min:0,value:1},radiusMinPixels:{type:"number",min:0,value:0},radiusMaxPixels:{type:"number",min:0,value:Number.MAX_SAFE_INTEGER},lineWidthUnits:"meters",lineWidthScale:{type:"number",min:0,value:1},lineWidthMinPixels:{type:"number",min:0,value:0},lineWidthMaxPixels:{type:"number",min:0,value:Number.MAX_SAFE_INTEGER},stroked:!1,filled:!0,billboard:!1,antialiasing:!0,getPosition:{type:"accessor",value:n=>n.position},getRadius:{type:"accessor",value:1},getFillColor:{type:"accessor",value:me},getLineColor:{type:"accessor",value:me},getLineWidth:{type:"accessor",value:1},strokeWidth:{deprecatedFor:"getLineWidth"},outline:{deprecatedFor:"stroked"},getColor:{deprecatedFor:["getFillColor","getLineColor"]}};class oe extends E{getShaders(){return super.getShaders({vs:kt,fs:Wt,source:Dt,modules:[z,Ee,O,Ft]})}initializeState(){this.getAttributeManager().addInstanced({instancePositions:{size:3,type:"float64",fp64:this.use64bitPositions(),transition:!0,accessor:"getPosition"},instanceRadius:{size:1,transition:!0,accessor:"getRadius",defaultValue:1},instanceFillColors:{size:this.props.colorFormat.length,transition:!0,type:"unorm8",accessor:"getFillColor",defaultValue:[0,0,0,255]},instanceLineColors:{size:this.props.colorFormat.length,transition:!0,type:"unorm8",accessor:"getLineColor",defaultValue:[0,0,0,255]},instanceLineWidths:{size:1,transition:!0,accessor:"getLineWidth",defaultValue:1}})}updateState(e){super.updateState(e),e.changeFlags.extensionsChanged&&(this.state.model?.destroy(),this.state.model=this._getModel(),this.getAttributeManager().invalidateAll())}draw({uniforms:e}){const{radiusUnits:t,radiusScale:i,radiusMinPixels:o,radiusMaxPixels:s,stroked:r,filled:a,billboard:l,antialiasing:c,lineWidthUnits:d,lineWidthScale:g,lineWidthMinPixels:u,lineWidthMaxPixels:p}=this.props,f={stroked:r,filled:a,billboard:l,antialiasing:c,radiusUnits:w[t],radiusScale:i,radiusMinPixels:o,radiusMaxPixels:s,lineWidthUnits:w[d],lineWidthScale:g,lineWidthMinPixels:u,lineWidthMaxPixels:p},y=this.state.model;y.shaderInputs.setProps({scatterplot:f}),this.context.device.type==="webgpu"&&(y.instanceCount=this.props.data.length),y.draw(this.context.renderPass)}_getModel(){const e=this.context.device.type==="webgpu"?{depthWriteEnabled:!0,depthCompare:"less-equal"}:void 0,t=[-1,-1,0,1,-1,0,-1,1,0,1,1,0];return new F(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),geometry:new K({topology:"triangle-strip",attributes:{positions:{size:3,value:new Float32Array(t)}}}),isInstanced:!0,parameters:e})}}oe.defaultProps=Bt;oe.layerName="ScatterplotLayer";function Ne({data:n,getIndex:e,dataRange:t,replace:i}){const{startRow:o=0,endRow:s=1/0}=t,r=n.length;let a=r,l=r;for(let u=0;u<r;u++){const p=e(n[u]);if(a>u&&p>=o&&(a=u),p>=s){l=u;break}}let c=a;const g=l-a!==i.length?n.slice(l):void 0;for(let u=0;u<i.length;u++)n[c++]=i[u];if(g){for(let u=0;u<g.length;u++)n[c++]=g[u];n.length=c}return{startRow:a,endRow:a+i.length}}const Ge=[0,0,0,255],Ut=[0,0,0,255],Nt={stroked:!0,filled:!0,extruded:!1,elevationScale:1,wireframe:!1,_normalize:!0,_windingOrder:"CW",lineWidthUnits:"meters",lineWidthScale:1,lineWidthMinPixels:0,lineWidthMaxPixels:Number.MAX_SAFE_INTEGER,lineJointRounded:!1,lineMiterLimit:4,getPolygon:{type:"accessor",value:n=>n.polygon},getFillColor:{type:"accessor",value:Ut},getLineColor:{type:"accessor",value:Ge},getLineWidth:{type:"accessor",value:1},getElevation:{type:"accessor",value:1e3},material:!0};class je extends ie{initializeState(){this.state={paths:[],pathsDiff:null},this.props.getLineDashArray&&T.removed("getLineDashArray","PathStyleExtension")()}updateState({changeFlags:e}){const t=e.dataChanged||e.updateTriggersChanged&&(e.updateTriggersChanged.all||e.updateTriggersChanged.getPolygon);if(t&&Array.isArray(e.dataChanged)){const i=this.state.paths.slice(),o=e.dataChanged.map(s=>Ne({data:i,getIndex:r=>r.__source.index,dataRange:s,replace:this._getPaths(s)}));this.setState({paths:i,pathsDiff:o})}else t&&this.setState({paths:this._getPaths(),pathsDiff:null})}_getPaths(e={}){const{data:t,getPolygon:i,positionFormat:o,_normalize:s}=this.props,r=[],a=o==="XY"?2:3,{startRow:l,endRow:c}=e,{iterable:d,objectInfo:g}=te(t,l,c);for(const u of d){g.index++;let p=i(u,g);s&&(p=Je(p,a));const{holeIndices:f}=p,y=p.positions||p;if(f)for(let h=0;h<=f.length;h++){const m=y.slice(f[h-1]||0,f[h]||y.length);r.push(this.getSubLayerRow({path:m},u,g.index))}else r.push(this.getSubLayerRow({path:y},u,g.index))}return r}renderLayers(){const{data:e,_dataDiff:t,stroked:i,filled:o,extruded:s,wireframe:r,_normalize:a,_windingOrder:l,elevationScale:c,transitions:d,positionFormat:g}=this.props,{lineWidthUnits:u,lineWidthScale:p,lineWidthMinPixels:f,lineWidthMaxPixels:y,lineJointRounded:h,lineMiterLimit:m,lineDashJustified:L}=this.props,{getFillColor:C,getLineColor:S,getLineWidth:x,getLineDashArray:v,getElevation:I,getPolygon:R,updateTriggers:_,material:U}=this.props,{paths:M,pathsDiff:k}=this.state,b=this.getSubLayerClass("fill",ze),P=this.getSubLayerClass("stroke",Oe),N=this.shouldRenderSubLayer("fill",M)&&new b({_dataDiff:t,extruded:s,elevationScale:c,filled:o,wireframe:r,_normalize:a,_windingOrder:l,getElevation:I,getFillColor:C,getLineColor:s&&r?S:Ge,material:U,transitions:d},this.getSubLayerProps({id:"fill",updateTriggers:_&&{getPolygon:_.getPolygon,getElevation:_.getElevation,getFillColor:_.getFillColor,lineColors:s&&r,getLineColor:_.getLineColor}}),{data:e,positionFormat:g,getPolygon:R}),q=!s&&i&&this.shouldRenderSubLayer("stroke",M)&&new P({_dataDiff:k&&(()=>k),widthUnits:u,widthScale:p,widthMinPixels:f,widthMaxPixels:y,jointRounded:h,miterLimit:m,dashJustified:L,_pathType:"loop",transitions:d&&{getWidth:d.getLineWidth,getColor:d.getLineColor,getPath:d.getPolygon},getColor:this.getSubLayerAccessor(S),getWidth:this.getSubLayerAccessor(x),getDashArray:this.getSubLayerAccessor(v)},this.getSubLayerProps({id:"stroke",updateTriggers:_&&{getWidth:_.getLineWidth,getColor:_.getLineColor,getDashArray:_.getLineDashArray}}),{data:M,positionFormat:g,getPath:Xe=>Xe.path});return[!s&&N,q,s&&N]}}je.layerName="PolygonLayer";je.defaultProps=Nt;function Gt(n,e){if(!n)return null;const t="startIndices"in n?n.startIndices[e]:e,i=n.featureIds.value[t];return t!==-1?jt(n,i,t):null}function jt(n,e,t){const i={properties:{...n.properties[e]}};for(const o in n.numericProps)i.properties[o]=n.numericProps[o].value[t];return i}function $t(n,e){const t={points:null,lines:null,polygons:null};for(const i in t){const o=n[i].globalFeatureIds.value;t[i]=new Uint8ClampedArray(o.length*4);const s=[];for(let r=0;r<o.length;r++)e(o[r],s),t[i][r*4+0]=s[0],t[i][r*4+1]=s[1],t[i][r*4+2]=s[2],t[i][r*4+3]=255}return t}const ve=`uniform sdfUniforms {
  float gamma;
  bool enabled;
  float buffer;
  float outlineBuffer;
  vec4 outlineColor;
} sdf;
`,Ht={name:"sdf",vs:ve,fs:ve,uniformTypes:{gamma:"f32",enabled:"f32",buffer:"f32",outlineBuffer:"f32",outlineColor:"vec4<f32>"}},Vt=`#version 300 es
#define SHADER_NAME multi-icon-layer-fragment-shader
precision highp float;
uniform sampler2D iconsTexture;
in vec4 vColor;
in vec2 vTextureCoords;
in vec2 uv;
out vec4 fragColor;
void main(void) {
geometry.uv = uv;
if (!bool(picking.isActive)) {
float alpha = texture(iconsTexture, vTextureCoords).a;
vec4 color = vColor;
if (sdf.enabled) {
float distance = alpha;
alpha = smoothstep(sdf.buffer - sdf.gamma, sdf.buffer + sdf.gamma, distance);
if (sdf.outlineBuffer > 0.0) {
float inFill = alpha;
float inBorder = smoothstep(sdf.outlineBuffer - sdf.gamma, sdf.outlineBuffer + sdf.gamma, distance);
color = mix(sdf.outlineColor, vColor, inFill);
alpha = inBorder;
}
}
float a = alpha * color.a;
if (a < icon.alphaCutoff) {
discard;
}
fragColor = vec4(color.rgb, a * layer.opacity);
}
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,Y=192/256,xe=[],Kt={getIconOffsets:{type:"accessor",value:n=>n.offsets},alphaCutoff:.001,smoothing:.1,outlineWidth:0,outlineColor:{type:"color",value:[0,0,0,255]}};class se extends Z{getShaders(){const e=super.getShaders();return{...e,modules:[...e.modules,Ht],fs:Vt}}initializeState(){super.initializeState(),this.getAttributeManager().addInstanced({instanceOffsets:{size:2,accessor:"getIconOffsets"},instancePickingColors:{type:"uint8",size:3,accessor:(t,{index:i,target:o})=>this.encodePickingColor(i,o)}})}updateState(e){super.updateState(e);const{props:t,oldProps:i}=e;let{outlineColor:o}=t;o!==i.outlineColor&&(o=o.map(s=>s/255),o[3]=Number.isFinite(o[3])?o[3]:1,this.setState({outlineColor:o})),!t.sdf&&t.outlineWidth&&T.warn(`${this.id}: fontSettings.sdf is required to render outline`)()}draw(e){const{sdf:t,smoothing:i,outlineWidth:o}=this.props,{outlineColor:s}=this.state,r=o?Math.max(i,Y*(1-o)):-1,a=this.state.model,l={buffer:Y,outlineBuffer:r,gamma:i,enabled:!!t,outlineColor:s};if(a.shaderInputs.setProps({sdf:l}),super.draw(e),t&&o){const{iconManager:c}=this.state;c.getTexture()&&(a.shaderInputs.setProps({sdf:{...l,outlineBuffer:Y}}),a.draw(this.context.renderPass))}}getInstanceOffset(e){return e?Array.from(e).flatMap(t=>super.getInstanceOffset(t)):xe}getInstanceColorMode(e){return 1}getInstanceIconFrame(e){return e?Array.from(e).flatMap(t=>super.getInstanceIconFrame(t)):xe}}se.defaultProps=Kt;se.layerName="MultiIconLayer";const D=1e20;class Zt{constructor({fontSize:e=24,buffer:t=3,radius:i=8,cutoff:o=.25,fontFamily:s="sans-serif",fontWeight:r="normal",fontStyle:a="normal",lang:l=null}={}){this.buffer=t,this.cutoff=o,this.radius=i,this.lang=l;const c=this.size=e+t*4,d=this._createCanvas(c),g=this.ctx=d.getContext("2d",{willReadFrequently:!0});g.font=`${a} ${r} ${e}px ${s}`,g.textBaseline="alphabetic",g.textAlign="left",g.fillStyle="black",this.gridOuter=new Float64Array(c*c),this.gridInner=new Float64Array(c*c),this.f=new Float64Array(c),this.z=new Float64Array(c+1),this.v=new Uint16Array(c)}_createCanvas(e){const t=document.createElement("canvas");return t.width=t.height=e,t}draw(e){const{width:t,actualBoundingBoxAscent:i,actualBoundingBoxDescent:o,actualBoundingBoxLeft:s,actualBoundingBoxRight:r}=this.ctx.measureText(e),a=Math.ceil(i),l=0,c=Math.max(0,Math.min(this.size-this.buffer,Math.ceil(r-s))),d=Math.min(this.size-this.buffer,a+Math.ceil(o)),g=c+2*this.buffer,u=d+2*this.buffer,p=Math.max(g*u,0),f=new Uint8ClampedArray(p),y={data:f,width:g,height:u,glyphWidth:c,glyphHeight:d,glyphTop:a,glyphLeft:l,glyphAdvance:t};if(c===0||d===0)return y;const{ctx:h,buffer:m,gridInner:L,gridOuter:C}=this;this.lang&&(h.lang=this.lang),h.clearRect(m,m,c,d),h.fillText(e,m,m+a);const S=h.getImageData(m,m,c,d);C.fill(D,0,p),L.fill(0,0,p);for(let x=0;x<d;x++)for(let v=0;v<c;v++){const I=S.data[4*(x*c+v)+3]/255;if(I===0)continue;const R=(x+m)*g+v+m;if(I===1)C[R]=0,L[R]=D;else{const _=.5-I;C[R]=_>0?_*_:0,L[R]=_<0?_*_:0}}Pe(C,0,0,g,u,g,this.f,this.v,this.z),Pe(L,m,m,c,d,g,this.f,this.v,this.z);for(let x=0;x<p;x++){const v=Math.sqrt(C[x])-Math.sqrt(L[x]);f[x]=Math.round(255-255*(v/this.radius+this.cutoff))}return y}}function Pe(n,e,t,i,o,s,r,a,l){for(let c=e;c<e+i;c++)Ce(n,t*s+c,s,o,r,a,l);for(let c=t;c<t+o;c++)Ce(n,c*s+e,1,i,r,a,l)}function Ce(n,e,t,i,o,s,r){s[0]=0,r[0]=-D,r[1]=D,o[0]=n[e];for(let a=1,l=0,c=0;a<i;a++){o[a]=n[e+a*t];const d=a*a;do{const g=s[l];c=(o[a]-o[g]+d-g*g)/(a-g)/2}while(c<=r[l]&&--l>-1);l++,s[l]=a,r[l]=c,r[l+1]=D}for(let a=0,l=0;a<i;a++){for(;r[l+1]<a;)l++;const c=s[l],d=a-c;n[e+a*t]=o[c]+d*d}}const qt=32,Xt=[];function Yt(n){return Math.pow(2,Math.ceil(Math.log2(n)))}function Jt({characterSet:n,getFontWidth:e,fontHeight:t,buffer:i,maxCanvasWidth:o,mapping:s={},xOffset:r=0,yOffset:a=0}){let l=0,c=r;const d=t+i*2;for(const g of n)if(!s[g]){const u=e(g);c+u+i*2>o&&(c=0,l++),s[g]={x:c+i,y:a+l*d+i,width:u,height:d,layoutWidth:u,layoutHeight:t},c+=u+i*2}return{mapping:s,xOffset:c,yOffset:a+l*d,canvasHeight:Yt(a+(l+1)*d)}}function $e(n,e,t,i){let o=0;for(let s=e;s<t;s++){const r=n[s];o+=i[r]?.layoutWidth||0}return o}function He(n,e,t,i,o,s){let r=e,a=0;for(let l=e;l<t;l++){const c=$e(n,l,l+1,o);a+c>i&&(r<l&&s.push(l),r=l,a=0),a+=c}return a}function Qt(n,e,t,i,o,s){let r=e,a=e,l=e,c=0;for(let d=e;d<t;d++)if((n[d]===" "||n[d+1]===" "||d+1===t)&&(l=d+1),l>a){let g=$e(n,a,l,o);c+g>i&&(r<a&&(s.push(a),r=a,c=0),g>i&&(g=He(n,a,l,i,o,s),r=s[s.length-1])),a=l,c+=g}return c}function ei(n,e,t,i,o=0,s){s===void 0&&(s=n.length);const r=[];return e==="break-all"?He(n,o,s,t,i,r):Qt(n,o,s,t,i,r),r}function ti(n,e,t,i,o,s){let r=0,a=0;for(let l=e;l<t;l++){const c=n[l],d=i[c];d?(a||(a=d.layoutHeight),o[l]=r+d.layoutWidth/2,r+=d.layoutWidth):(T.warn(`Missing character: ${c} (${c.codePointAt(0)})`)(),o[l]=r,r+=qt)}s[0]=r,s[1]=a}function ii(n,e,t,i,o){const s=Array.from(n),r=s.length,a=new Array(r),l=new Array(r),c=new Array(r),d=(t==="break-word"||t==="break-all")&&isFinite(i)&&i>0,g=[0,0],u=[0,0];let p=0,f=0,y=0;for(let h=0;h<=r;h++){const m=s[h];if((m===`
`||h===r)&&(y=h),y>f){const L=d?ei(s,t,i,o,f,y):Xt;for(let C=0;C<=L.length;C++){const S=C===0?f:L[C-1],x=C<L.length?L[C]:y;ti(s,S,x,o,a,u);for(let v=S;v<x;v++){const I=s[v],R=o[I]?.layoutOffsetY||0;l[v]=p+u[1]/2+R,c[v]=u[0]}p=p+u[1]*e,g[0]=Math.max(g[0],u[0])}f=y}m===`
`&&(a[f]=0,l[f]=0,c[f]=0,f++)}return g[1]=p,{x:a,y:l,rowWidth:c,size:g}}function oi({value:n,length:e,stride:t,offset:i,startIndices:o,characterSet:s}){const r=n.BYTES_PER_ELEMENT,a=t?t/r:1,l=i?i/r:0,c=o[e]||Math.ceil((n.length-l)/a),d=s&&new Set,g=new Array(e);let u=n;if(a>1||l>0){const p=n.constructor;u=new p(c);for(let f=0;f<c;f++)u[f]=n[f*a+l]}for(let p=0;p<e;p++){const f=o[p],y=o[p+1]||c,h=u.subarray(f,y);g[p]=String.fromCodePoint.apply(null,h),d&&h.forEach(d.add,d)}if(d)for(const p of d)s.add(String.fromCodePoint(p));return{texts:g,characterCount:c}}class Ve{constructor(e=5){this._cache={},this._order=[],this.limit=e}get(e){const t=this._cache[e];return t&&(this._deleteOrder(e),this._appendOrder(e)),t}set(e,t){this._cache[e]?(this.delete(e),this._cache[e]=t,this._appendOrder(e)):(Object.keys(this._cache).length===this.limit&&this.delete(this._order[0]),this._cache[e]=t,this._appendOrder(e))}delete(e){this._cache[e]&&(delete this._cache[e],this._deleteOrder(e))}_deleteOrder(e){const t=this._order.indexOf(e);t>=0&&this._order.splice(t,1)}_appendOrder(e){this._order.push(e)}}function si(){const n=[];for(let e=32;e<128;e++)n.push(String.fromCharCode(e));return n}const A={fontFamily:"Monaco, monospace",fontWeight:"normal",characterSet:si(),fontSize:64,buffer:4,sdf:!1,cutoff:.25,radius:12,smoothing:.1},_e=1024,Le=.9,be=1.2,Ke=3;let V=new Ve(Ke);function ni(n,e){let t;typeof e=="string"?t=new Set(Array.from(e)):t=new Set(e);const i=V.get(n);if(!i)return t;for(const o in i.mapping)t.has(o)&&t.delete(o);return t}function ri(n,e){for(let t=0;t<n.length;t++)e.data[4*t+3]=n[t]}function Se(n,e,t,i){n.font=`${i} ${t}px ${e}`,n.fillStyle="#000",n.textBaseline="alphabetic",n.textAlign="left"}function ai(n){T.assert(Number.isFinite(n)&&n>=Ke,"Invalid cache limit"),V=new Ve(n)}class li{constructor(){this.props={...A}}get atlas(){return this._atlas}get mapping(){return this._atlas&&this._atlas.mapping}get scale(){const{fontSize:e,buffer:t}=this.props;return(e*be+t*2)/e}setProps(e={}){Object.assign(this.props,e),this._key=this._getKey();const t=ni(this._key,this.props.characterSet),i=V.get(this._key);if(i&&t.size===0){this._atlas!==i&&(this._atlas=i);return}const o=this._generateFontAtlas(t,i);this._atlas=o,V.set(this._key,o)}_generateFontAtlas(e,t){const{fontFamily:i,fontWeight:o,fontSize:s,buffer:r,sdf:a,radius:l,cutoff:c}=this.props;let d=t&&t.data;d||(d=document.createElement("canvas"),d.width=_e);const g=d.getContext("2d",{willReadFrequently:!0});Se(g,i,s,o);const{mapping:u,canvasHeight:p,xOffset:f,yOffset:y}=Jt({getFontWidth:h=>g.measureText(h).width,fontHeight:s*be,buffer:r,characterSet:e,maxCanvasWidth:_e,...t&&{mapping:t.mapping,xOffset:t.xOffset,yOffset:t.yOffset}});if(d.height!==p){const h=g.getImageData(0,0,d.width,d.height);d.height=p,g.putImageData(h,0,0)}if(Se(g,i,s,o),a){const h=new Zt({fontSize:s,buffer:r,radius:l,cutoff:c,fontFamily:i,fontWeight:`${o}`});for(const m of e){const{data:L,width:C,height:S,glyphTop:x}=h.draw(m);u[m].width=C,u[m].layoutOffsetY=s*Le-x;const v=g.createImageData(C,S);ri(L,v),g.putImageData(v,u[m].x,u[m].y)}}else for(const h of e)g.fillText(h,u[h].x,u[h].y+r+s*Le);return{xOffset:f,yOffset:y,mapping:u,data:d,width:d.width,height:d.height}}_getKey(){const{fontFamily:e,fontWeight:t,fontSize:i,buffer:o,sdf:s,radius:r,cutoff:a}=this.props;return s?`${e} ${t} ${i} ${o} ${r} ${a}`:`${e} ${t} ${i} ${o}`}}const Te=`uniform textBackgroundUniforms {
  bool billboard;
  float sizeScale;
  float sizeMinPixels;
  float sizeMaxPixels;
  vec4 borderRadius;
  vec4 padding;
  highp int sizeUnits;
  bool stroked;
} textBackground;
`,ci={name:"textBackground",vs:Te,fs:Te,uniformTypes:{billboard:"f32",sizeScale:"f32",sizeMinPixels:"f32",sizeMaxPixels:"f32",borderRadius:"vec4<f32>",padding:"vec4<f32>",sizeUnits:"i32",stroked:"f32"}},di=`#version 300 es
#define SHADER_NAME text-background-layer-vertex-shader
in vec2 positions;
in vec3 instancePositions;
in vec3 instancePositions64Low;
in vec4 instanceRects;
in float instanceSizes;
in float instanceAngles;
in vec2 instancePixelOffsets;
in float instanceLineWidths;
in vec4 instanceFillColors;
in vec4 instanceLineColors;
in vec3 instancePickingColors;
out vec4 vFillColor;
out vec4 vLineColor;
out float vLineWidth;
out vec2 uv;
out vec2 dimensions;
vec2 rotate_by_angle(vec2 vertex, float angle) {
float angle_radian = radians(angle);
float cos_angle = cos(angle_radian);
float sin_angle = sin(angle_radian);
mat2 rotationMatrix = mat2(cos_angle, -sin_angle, sin_angle, cos_angle);
return rotationMatrix * vertex;
}
void main(void) {
geometry.worldPosition = instancePositions;
geometry.uv = positions;
geometry.pickingColor = instancePickingColors;
uv = positions;
vLineWidth = instanceLineWidths;
float sizePixels = clamp(
project_size_to_pixel(instanceSizes * textBackground.sizeScale, textBackground.sizeUnits),
textBackground.sizeMinPixels, textBackground.sizeMaxPixels
);
dimensions = instanceRects.zw * sizePixels + textBackground.padding.xy + textBackground.padding.zw;
vec2 pixelOffset = (positions * instanceRects.zw + instanceRects.xy) * sizePixels + mix(-textBackground.padding.xy, textBackground.padding.zw, positions);
pixelOffset = rotate_by_angle(pixelOffset, instanceAngles);
pixelOffset += instancePixelOffsets;
pixelOffset.y *= -1.0;
if (textBackground.billboard)  {
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, vec3(0.0), geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
vec3 offset = vec3(pixelOffset, 0.0);
DECKGL_FILTER_SIZE(offset, geometry);
gl_Position.xy += project_pixel_size_to_clipspace(offset.xy);
} else {
vec3 offset_common = vec3(project_pixel_size(pixelOffset), 0.0);
DECKGL_FILTER_SIZE(offset_common, geometry);
gl_Position = project_position_to_clipspace(instancePositions, instancePositions64Low, offset_common, geometry.position);
DECKGL_FILTER_GL_POSITION(gl_Position, geometry);
}
vFillColor = vec4(instanceFillColors.rgb, instanceFillColors.a * layer.opacity);
DECKGL_FILTER_COLOR(vFillColor, geometry);
vLineColor = vec4(instanceLineColors.rgb, instanceLineColors.a * layer.opacity);
DECKGL_FILTER_COLOR(vLineColor, geometry);
}
`,gi=`#version 300 es
#define SHADER_NAME text-background-layer-fragment-shader
precision highp float;
in vec4 vFillColor;
in vec4 vLineColor;
in float vLineWidth;
in vec2 uv;
in vec2 dimensions;
out vec4 fragColor;
float round_rect(vec2 p, vec2 size, vec4 radii) {
vec2 pixelPositionCB = (p - 0.5) * size;
vec2 sizeCB = size * 0.5;
float maxBorderRadius = min(size.x, size.y) * 0.5;
vec4 borderRadius = vec4(min(radii, maxBorderRadius));
borderRadius.xy =
(pixelPositionCB.x > 0.0) ? borderRadius.xy : borderRadius.zw;
borderRadius.x = (pixelPositionCB.y > 0.0) ? borderRadius.x : borderRadius.y;
vec2 q = abs(pixelPositionCB) - sizeCB + borderRadius.x;
return -(min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - borderRadius.x);
}
float rect(vec2 p, vec2 size) {
vec2 pixelPosition = p * size;
return min(min(pixelPosition.x, size.x - pixelPosition.x),
min(pixelPosition.y, size.y - pixelPosition.y));
}
vec4 get_stroked_fragColor(float dist) {
float isBorder = smoothedge(dist, vLineWidth);
return mix(vFillColor, vLineColor, isBorder);
}
void main(void) {
geometry.uv = uv;
if (textBackground.borderRadius != vec4(0.0)) {
float distToEdge = round_rect(uv, dimensions, textBackground.borderRadius);
if (textBackground.stroked) {
fragColor = get_stroked_fragColor(distToEdge);
} else {
fragColor = vFillColor;
}
float shapeAlpha = smoothedge(-distToEdge, 0.0);
fragColor.a *= shapeAlpha;
} else {
if (textBackground.stroked) {
float distToEdge = rect(uv, dimensions);
fragColor = get_stroked_fragColor(distToEdge);
} else {
fragColor = vFillColor;
}
}
DECKGL_FILTER_COLOR(fragColor, geometry);
}
`,ui={billboard:!0,sizeScale:1,sizeUnits:"pixels",sizeMinPixels:0,sizeMaxPixels:Number.MAX_SAFE_INTEGER,borderRadius:{type:"object",value:0},padding:{type:"array",value:[0,0,0,0]},getPosition:{type:"accessor",value:n=>n.position},getSize:{type:"accessor",value:1},getAngle:{type:"accessor",value:0},getPixelOffset:{type:"accessor",value:[0,0]},getBoundingRect:{type:"accessor",value:[0,0,0,0]},getFillColor:{type:"accessor",value:[0,0,0,255]},getLineColor:{type:"accessor",value:[0,0,0,255]},getLineWidth:{type:"accessor",value:1}};class ne extends E{getShaders(){return super.getShaders({vs:di,fs:gi,modules:[z,O,ci]})}initializeState(){this.getAttributeManager().addInstanced({instancePositions:{size:3,type:"float64",fp64:this.use64bitPositions(),transition:!0,accessor:"getPosition"},instanceSizes:{size:1,transition:!0,accessor:"getSize",defaultValue:1},instanceAngles:{size:1,transition:!0,accessor:"getAngle"},instanceRects:{size:4,accessor:"getBoundingRect"},instancePixelOffsets:{size:2,transition:!0,accessor:"getPixelOffset"},instanceFillColors:{size:4,transition:!0,type:"unorm8",accessor:"getFillColor",defaultValue:[0,0,0,255]},instanceLineColors:{size:4,transition:!0,type:"unorm8",accessor:"getLineColor",defaultValue:[0,0,0,255]},instanceLineWidths:{size:1,transition:!0,accessor:"getLineWidth",defaultValue:1}})}updateState(e){super.updateState(e);const{changeFlags:t}=e;t.extensionsChanged&&(this.state.model?.destroy(),this.state.model=this._getModel(),this.getAttributeManager().invalidateAll())}draw({uniforms:e}){const{billboard:t,sizeScale:i,sizeUnits:o,sizeMinPixels:s,sizeMaxPixels:r,getLineWidth:a}=this.props;let{padding:l,borderRadius:c}=this.props;l.length<4&&(l=[l[0],l[1],l[0],l[1]]),Array.isArray(c)||(c=[c,c,c,c]);const d=this.state.model,g={billboard:t,stroked:!!a,borderRadius:c,padding:l,sizeUnits:w[o],sizeScale:i,sizeMinPixels:s,sizeMaxPixels:r};d.shaderInputs.setProps({textBackground:g}),d.draw(this.context.renderPass)}_getModel(){const e=[0,0,1,0,0,1,1,1];return new F(this.context.device,{...this.getShaders(),id:this.props.id,bufferLayout:this.getAttributeManager().getBufferLayouts(),geometry:new K({topology:"triangle-strip",vertexCount:4,attributes:{positions:{size:2,value:new Float32Array(e)}}}),isInstanced:!0})}}ne.defaultProps=ui;ne.layerName="TextBackgroundLayer";const Re={start:1,middle:0,end:-1},Ie={top:1,center:0,bottom:-1},J=[0,0,0,255],pi=1,fi={billboard:!0,sizeScale:1,sizeUnits:"pixels",sizeMinPixels:0,sizeMaxPixels:Number.MAX_SAFE_INTEGER,background:!1,getBackgroundColor:{type:"accessor",value:[255,255,255,255]},getBorderColor:{type:"accessor",value:J},getBorderWidth:{type:"accessor",value:0},backgroundBorderRadius:{type:"object",value:0},backgroundPadding:{type:"array",value:[0,0,0,0]},characterSet:{type:"object",value:A.characterSet},fontFamily:A.fontFamily,fontWeight:A.fontWeight,lineHeight:pi,outlineWidth:{type:"number",value:0,min:0},outlineColor:{type:"color",value:J},fontSettings:{type:"object",value:{},compare:1},wordBreak:"break-word",maxWidth:{type:"number",value:-1},getText:{type:"accessor",value:n=>n.text},getPosition:{type:"accessor",value:n=>n.position},getColor:{type:"accessor",value:J},getSize:{type:"accessor",value:32},getAngle:{type:"accessor",value:0},getTextAnchor:{type:"accessor",value:"middle"},getAlignmentBaseline:{type:"accessor",value:"center"},getPixelOffset:{type:"accessor",value:[0,0]},backgroundColor:{deprecatedFor:["background","getBackgroundColor"]}};class re extends ie{constructor(){super(...arguments),this.getBoundingRect=(e,t)=>{let{size:[i,o]}=this.transformParagraph(e,t);const{fontSize:s}=this.state.fontAtlasManager.props;i/=s,o/=s;const{getTextAnchor:r,getAlignmentBaseline:a}=this.props,l=Re[typeof r=="function"?r(e,t):r],c=Ie[typeof a=="function"?a(e,t):a];return[(l-1)*i/2,(c-1)*o/2,i,o]},this.getIconOffsets=(e,t)=>{const{getTextAnchor:i,getAlignmentBaseline:o}=this.props,{x:s,y:r,rowWidth:a,size:[l,c]}=this.transformParagraph(e,t),d=Re[typeof i=="function"?i(e,t):i],g=Ie[typeof o=="function"?o(e,t):o],u=s.length,p=new Array(u*2);let f=0;for(let y=0;y<u;y++){const h=(1-d)*(l-a[y])/2;p[f++]=(d-1)*l/2+h+s[y],p[f++]=(g-1)*c/2+r[y]}return p}}initializeState(){this.state={styleVersion:0,fontAtlasManager:new li},this.props.maxWidth>0&&T.once(1,"v8.9 breaking change: TextLayer maxWidth is now relative to text size")()}updateState(e){const{props:t,oldProps:i,changeFlags:o}=e;(o.dataChanged||o.updateTriggersChanged&&(o.updateTriggersChanged.all||o.updateTriggersChanged.getText))&&this._updateText(),(this._updateFontAtlas()||t.lineHeight!==i.lineHeight||t.wordBreak!==i.wordBreak||t.maxWidth!==i.maxWidth)&&this.setState({styleVersion:this.state.styleVersion+1})}getPickingInfo({info:e}){return e.object=e.index>=0?this.props.data[e.index]:null,e}_updateFontAtlas(){const{fontSettings:e,fontFamily:t,fontWeight:i}=this.props,{fontAtlasManager:o,characterSet:s}=this.state,r={...e,characterSet:s,fontFamily:t,fontWeight:i};if(!o.mapping)return o.setProps(r),!0;for(const a in r)if(r[a]!==o.props[a])return o.setProps(r),!0;return!1}_updateText(){const{data:e,characterSet:t}=this.props,i=e.attributes?.getText;let{getText:o}=this.props,s=e.startIndices,r;const a=t==="auto"&&new Set;if(i&&s){const{texts:l,characterCount:c}=oi({...ArrayBuffer.isView(i)?{value:i}:i,length:e.length,startIndices:s,characterSet:a});r=c,o=(d,{index:g})=>l[g]}else{const{iterable:l,objectInfo:c}=te(e);s=[0],r=0;for(const d of l){c.index++;const g=Array.from(o(d,c)||"");a&&g.forEach(a.add,a),r+=g.length,s.push(r)}}this.setState({getText:o,startIndices:s,numInstances:r,characterSet:a||t})}transformParagraph(e,t){const{fontAtlasManager:i}=this.state,o=i.mapping,s=this.state.getText,{wordBreak:r,lineHeight:a,maxWidth:l}=this.props,c=s(e,t)||"";return ii(c,a,r,l*i.props.fontSize,o)}renderLayers(){const{startIndices:e,numInstances:t,getText:i,fontAtlasManager:{scale:o,atlas:s,mapping:r},styleVersion:a}=this.state,{data:l,_dataDiff:c,getPosition:d,getColor:g,getSize:u,getAngle:p,getPixelOffset:f,getBackgroundColor:y,getBorderColor:h,getBorderWidth:m,backgroundBorderRadius:L,backgroundPadding:C,background:S,billboard:x,fontSettings:v,outlineWidth:I,outlineColor:R,sizeScale:_,sizeUnits:U,sizeMinPixels:M,sizeMaxPixels:k,transitions:b,updateTriggers:P}=this.props,N=this.getSubLayerClass("characters",se),q=this.getSubLayerClass("background",ne);return[S&&new q({getFillColor:y,getLineColor:h,getLineWidth:m,borderRadius:L,padding:C,getPosition:d,getSize:u,getAngle:p,getPixelOffset:f,billboard:x,sizeScale:_,sizeUnits:U,sizeMinPixels:M,sizeMaxPixels:k,transitions:b&&{getPosition:b.getPosition,getAngle:b.getAngle,getSize:b.getSize,getFillColor:b.getBackgroundColor,getLineColor:b.getBorderColor,getLineWidth:b.getBorderWidth,getPixelOffset:b.getPixelOffset}},this.getSubLayerProps({id:"background",updateTriggers:{getPosition:P.getPosition,getAngle:P.getAngle,getSize:P.getSize,getFillColor:P.getBackgroundColor,getLineColor:P.getBorderColor,getLineWidth:P.getBorderWidth,getPixelOffset:P.getPixelOffset,getBoundingRect:{getText:P.getText,getTextAnchor:P.getTextAnchor,getAlignmentBaseline:P.getAlignmentBaseline,styleVersion:a}}}),{data:l.attributes&&l.attributes.background?{length:l.length,attributes:l.attributes.background}:l,_dataDiff:c,autoHighlight:!1,getBoundingRect:this.getBoundingRect}),new N({sdf:v.sdf,smoothing:Number.isFinite(v.smoothing)?v.smoothing:A.smoothing,outlineWidth:I/(v.radius||A.radius),outlineColor:R,iconAtlas:s,iconMapping:r,getPosition:d,getColor:g,getSize:u,getAngle:p,getPixelOffset:f,billboard:x,sizeScale:_*o,sizeUnits:U,sizeMinPixels:M*o,sizeMaxPixels:k*o,transitions:b&&{getPosition:b.getPosition,getAngle:b.getAngle,getColor:b.getColor,getSize:b.getSize,getPixelOffset:b.getPixelOffset}},this.getSubLayerProps({id:"characters",updateTriggers:{all:P.getText,getPosition:P.getPosition,getAngle:P.getAngle,getColor:P.getColor,getSize:P.getSize,getPixelOffset:P.getPixelOffset,getIconOffsets:{getTextAnchor:P.getTextAnchor,getAlignmentBaseline:P.getAlignmentBaseline,styleVersion:a}}}),{data:l,_dataDiff:c,startIndices:e,numInstances:t,getIconOffsets:this.getIconOffsets,getIcon:i})]}static set fontAtlasCacheLimit(e){ai(e)}}re.defaultProps=fi;re.layerName="TextLayer";const j={circle:{type:oe,props:{filled:"filled",stroked:"stroked",lineWidthMaxPixels:"lineWidthMaxPixels",lineWidthMinPixels:"lineWidthMinPixels",lineWidthScale:"lineWidthScale",lineWidthUnits:"lineWidthUnits",pointRadiusMaxPixels:"radiusMaxPixels",pointRadiusMinPixels:"radiusMinPixels",pointRadiusScale:"radiusScale",pointRadiusUnits:"radiusUnits",pointAntialiasing:"antialiasing",pointBillboard:"billboard",getFillColor:"getFillColor",getLineColor:"getLineColor",getLineWidth:"getLineWidth",getPointRadius:"getRadius"}},icon:{type:Z,props:{iconAtlas:"iconAtlas",iconMapping:"iconMapping",iconSizeMaxPixels:"sizeMaxPixels",iconSizeMinPixels:"sizeMinPixels",iconSizeScale:"sizeScale",iconSizeUnits:"sizeUnits",iconAlphaCutoff:"alphaCutoff",iconBillboard:"billboard",getIcon:"getIcon",getIconAngle:"getAngle",getIconColor:"getColor",getIconPixelOffset:"getPixelOffset",getIconSize:"getSize"}},text:{type:re,props:{textSizeMaxPixels:"sizeMaxPixels",textSizeMinPixels:"sizeMinPixels",textSizeScale:"sizeScale",textSizeUnits:"sizeUnits",textBackground:"background",textBackgroundPadding:"backgroundPadding",textFontFamily:"fontFamily",textFontWeight:"fontWeight",textLineHeight:"lineHeight",textMaxWidth:"maxWidth",textOutlineColor:"outlineColor",textOutlineWidth:"outlineWidth",textWordBreak:"wordBreak",textCharacterSet:"characterSet",textBillboard:"billboard",textFontSettings:"fontSettings",getText:"getText",getTextAngle:"getAngle",getTextColor:"getColor",getTextPixelOffset:"getPixelOffset",getTextSize:"getSize",getTextAnchor:"getTextAnchor",getTextAlignmentBaseline:"getAlignmentBaseline",getTextBackgroundColor:"getBackgroundColor",getTextBorderColor:"getBorderColor",getTextBorderWidth:"getBorderWidth"}}},$={type:Oe,props:{lineWidthUnits:"widthUnits",lineWidthScale:"widthScale",lineWidthMinPixels:"widthMinPixels",lineWidthMaxPixels:"widthMaxPixels",lineJointRounded:"jointRounded",lineCapRounded:"capRounded",lineMiterLimit:"miterLimit",lineBillboard:"billboard",getLineColor:"getColor",getLineWidth:"getWidth"}},ee={type:ze,props:{extruded:"extruded",filled:"filled",wireframe:"wireframe",elevationScale:"elevationScale",material:"material",_full3d:"_full3d",getElevation:"getElevation",getFillColor:"getFillColor",getLineColor:"getLineColor"}};function W({type:n,props:e}){const t={};for(const i in e)t[i]=n.defaultProps[e[i]];return t}function Q(n,e){const{transitions:t,updateTriggers:i}=n.props,o={updateTriggers:{},transitions:t&&{getPosition:t.geometry}};for(const s in e){const r=e[s];let a=n.props[s];s.startsWith("get")&&(a=n.getSubLayerAccessor(a),o.updateTriggers[r]=i[s],t&&(o.transitions[r]=t[s])),o[r]=a}return o}function hi(n){if(Array.isArray(n))return n;switch(T.assert(n.type,"GeoJSON does not have type"),n.type){case"Feature":return[n];case"FeatureCollection":return T.assert(Array.isArray(n.features),"GeoJSON does not have features array"),n.features;default:return[{geometry:n}]}}function Me(n,e,t={}){const i={pointFeatures:[],lineFeatures:[],polygonFeatures:[],polygonOutlineFeatures:[]},{startRow:o=0,endRow:s=n.length}=t;for(let r=o;r<s;r++){const a=n[r],{geometry:l}=a;if(l)if(l.type==="GeometryCollection"){T.assert(Array.isArray(l.geometries),"GeoJSON does not have geometries array");const{geometries:c}=l;for(let d=0;d<c.length;d++){const g=c[d];Ae(g,i,e,a,r)}}else Ae(l,i,e,a,r)}return i}function Ae(n,e,t,i,o){const{type:s,coordinates:r}=n,{pointFeatures:a,lineFeatures:l,polygonFeatures:c,polygonOutlineFeatures:d}=e;if(!mi(s,r)){T.warn(`${s} coordinates are malformed`)();return}switch(s){case"Point":a.push(t({geometry:n},i,o));break;case"MultiPoint":r.forEach(g=>{a.push(t({geometry:{type:"Point",coordinates:g}},i,o))});break;case"LineString":l.push(t({geometry:n},i,o));break;case"MultiLineString":r.forEach(g=>{l.push(t({geometry:{type:"LineString",coordinates:g}},i,o))});break;case"Polygon":c.push(t({geometry:n},i,o)),r.forEach(g=>{d.push(t({geometry:{type:"LineString",coordinates:g}},i,o))});break;case"MultiPolygon":r.forEach(g=>{c.push(t({geometry:{type:"Polygon",coordinates:g}},i,o)),g.forEach(u=>{d.push(t({geometry:{type:"LineString",coordinates:u}},i,o))})});break}}const yi={Point:1,MultiPoint:2,LineString:2,MultiLineString:3,Polygon:3,MultiPolygon:4};function mi(n,e){let t=yi[n];for(T.assert(t,`Unknown GeoJSON type ${n}`);e&&--t>0;)e=e[0];return e&&Number.isFinite(e[0])}function Ze(){return{points:{},lines:{},polygons:{},polygonsOutline:{}}}function G(n){return n.geometry.coordinates}function vi(n,e){const t=Ze(),{pointFeatures:i,lineFeatures:o,polygonFeatures:s,polygonOutlineFeatures:r}=n;return t.points.data=i,t.points._dataDiff=e.pointFeatures&&(()=>e.pointFeatures),t.points.getPosition=G,t.lines.data=o,t.lines._dataDiff=e.lineFeatures&&(()=>e.lineFeatures),t.lines.getPath=G,t.polygons.data=s,t.polygons._dataDiff=e.polygonFeatures&&(()=>e.polygonFeatures),t.polygons.getPolygon=G,t.polygonsOutline.data=r,t.polygonsOutline._dataDiff=e.polygonOutlineFeatures&&(()=>e.polygonOutlineFeatures),t.polygonsOutline.getPath=G,t}function xi(n,e){const t=Ze(),{points:i,lines:o,polygons:s}=n,r=$t(n,e);t.points.data={length:i.positions.value.length/i.positions.size,attributes:{...i.attributes,getPosition:i.positions,instancePickingColors:{size:4,value:r.points}},properties:i.properties,numericProps:i.numericProps,featureIds:i.featureIds},t.lines.data={length:o.pathIndices.value.length-1,startIndices:o.pathIndices.value,attributes:{...o.attributes,getPath:o.positions,instancePickingColors:{size:4,value:r.lines}},properties:o.properties,numericProps:o.numericProps,featureIds:o.featureIds},t.lines._pathType="open";const a=s.positions.value.length/s.positions.size,l=Array(a).fill(1);for(const c of s.primitivePolygonIndices.value)l[c-1]=0;return t.polygons.data={length:s.polygonIndices.value.length-1,startIndices:s.polygonIndices.value,attributes:{...s.attributes,getPolygon:s.positions,instanceVertexValid:{size:1,value:new Uint16Array(l)},pickingColors:{size:4,value:r.polygons}},properties:s.properties,numericProps:s.numericProps,featureIds:s.featureIds},t.polygons._normalize=!1,s.triangles&&(t.polygons.data.attributes.indices=s.triangles.value),t.polygonsOutline.data={length:s.primitivePolygonIndices.value.length-1,startIndices:s.primitivePolygonIndices.value,attributes:{...s.attributes,getPath:s.positions,instancePickingColors:{size:4,value:r.polygons}},properties:s.properties,numericProps:s.numericProps,featureIds:s.featureIds},t.polygonsOutline._pathType="open",t}const Pi=["points","linestrings","polygons"],Ci={...W(j.circle),...W(j.icon),...W(j.text),...W($),...W(ee),stroked:!0,filled:!0,extruded:!1,wireframe:!1,_full3d:!1,iconAtlas:{type:"object",value:null},iconMapping:{type:"object",value:{}},getIcon:{type:"accessor",value:n=>n.properties.icon},getText:{type:"accessor",value:n=>n.properties.text},pointType:"circle",getRadius:{deprecatedFor:"getPointRadius"}};class qe extends ie{initializeState(){this.state={layerProps:{},features:{},featuresDiff:{}}}updateState({props:e,changeFlags:t}){if(!t.dataChanged)return;const{data:i}=this.props,o=i&&"points"in i&&"polygons"in i&&"lines"in i;this.setState({binary:o}),o?this._updateStateBinary({props:e,changeFlags:t}):this._updateStateJSON({props:e,changeFlags:t})}_updateStateBinary({props:e,changeFlags:t}){const i=xi(e.data,this.encodePickingColor);this.setState({layerProps:i})}_updateStateJSON({props:e,changeFlags:t}){const i=hi(e.data),o=this.getSubLayerRow.bind(this);let s={};const r={};if(Array.isArray(t.dataChanged)){const l=this.state.features;for(const c in l)s[c]=l[c].slice(),r[c]=[];for(const c of t.dataChanged){const d=Me(i,o,c);for(const g in l)r[g].push(Ne({data:s[g],getIndex:u=>u.__source.index,dataRange:c,replace:d[g]}))}}else s=Me(i,o);const a=vi(s,r);this.setState({features:s,featuresDiff:r,layerProps:a})}getPickingInfo(e){const t=super.getPickingInfo(e),{index:i,sourceLayer:o}=t;return t.featureType=Pi.find(s=>o.id.startsWith(`${this.id}-${s}-`)),i>=0&&o.id.startsWith(`${this.id}-points-text`)&&this.state.binary&&(t.index=this.props.data.points.globalFeatureIds.value[i]),t}_updateAutoHighlight(e){const t=`${this.id}-points-`,i=e.featureType==="points";for(const o of this.getSubLayers())o.id.startsWith(t)===i&&o.updateAutoHighlight(e)}_renderPolygonLayer(){const{extruded:e,wireframe:t}=this.props,{layerProps:i}=this.state,o="polygons-fill",s=this.shouldRenderSubLayer(o,i.polygons?.data)&&this.getSubLayerClass(o,ee.type);if(s){const r=Q(this,ee.props),a=e&&t;return a||delete r.getLineColor,r.updateTriggers.lineColors=a,new s(r,this.getSubLayerProps({id:o,updateTriggers:r.updateTriggers}),i.polygons)}return null}_renderLineLayers(){const{extruded:e,stroked:t}=this.props,{layerProps:i}=this.state,o="polygons-stroke",s="linestrings",r=!e&&t&&this.shouldRenderSubLayer(o,i.polygonsOutline?.data)&&this.getSubLayerClass(o,$.type),a=this.shouldRenderSubLayer(s,i.lines?.data)&&this.getSubLayerClass(s,$.type);if(r||a){const l=Q(this,$.props);return[r&&new r(l,this.getSubLayerProps({id:o,updateTriggers:l.updateTriggers}),i.polygonsOutline),a&&new a(l,this.getSubLayerProps({id:s,updateTriggers:l.updateTriggers}),i.lines)]}return null}_renderPointLayers(){const{pointType:e}=this.props,{layerProps:t,binary:i}=this.state;let{highlightedObjectIndex:o}=this.props;!i&&Number.isFinite(o)&&(o=t.points.data.findIndex(a=>a.__source.index===o));const s=new Set(e.split("+")),r=[];for(const a of s){const l=`points-${a}`,c=j[a],d=c&&this.shouldRenderSubLayer(l,t.points?.data)&&this.getSubLayerClass(l,c.type);if(d){const g=Q(this,c.props);let u=t.points;if(a==="text"&&i){const{instancePickingColors:p,...f}=u.data.attributes;u={...u,data:{...u.data,attributes:f}}}r.push(new d(g,this.getSubLayerProps({id:l,updateTriggers:g.updateTriggers,highlightedObjectIndex:o}),u))}}return r}renderLayers(){const{extruded:e}=this.props,t=this._renderPolygonLayer(),i=this._renderLineLayers(),o=this._renderPointLayers();return[!e&&t,i,o,e&&t]}getSubLayerAccessor(e){const{binary:t}=this.state;return!t||typeof e!="function"?super.getSubLayerAccessor(e):(i,o)=>{const{data:s,index:r}=o,a=Gt(s,r);return e(a,o)}}}qe.layerName="GeoJsonLayer";qe.defaultProps=Ci;export{Fe as A,ke as B,qe as G,Z as I,se as M,Ue as P,oe as S,re as T,je as a,ne as b};
//# sourceMappingURL=geojson-layer-DgMOQ4Qu.js.map
