import{y as Ft,c as Ut,t as Nt,O as T,a1 as Mt,W as zt,B as S,a2 as jt,$ as Dt,v as W,a3 as G,x as P,a4 as Vt,u as Gt,i as U,a5 as $t}from"./deep-equal-BTW2ZN6S.js";import{p as Yt,b as Ht,m as yt}from"./project-BTjD2Imj.js";import{M as it,u as qt,a as Wt,m as nt}from"./shader-Cbdysp2j.js";import{a as L}from"./assert-cyW4mg7q.js";import{b as Xt,T as tt,d as _,P as x,C as j,A as I,c as w,D as $,e as R,L as Zt,l as st}from"./webgl-developer-tools-utTNOsNf.js";import{T as vt}from"./array-utils-flat-BBMak426.js";import{WebGLDevice as rt}from"./webgl-device-BYRB-GQX.js";const Kt=`out vec4 transform_output;
void main() {
  transform_output = vec4(0);
}`,Jt=`#version 300 es
${Kt}`;function Qt(s){const{input:t,inputChannels:e,output:i}=s||{};if(!t)return Jt;if(!e)throw new Error("inputChannels");const n=te(e),r=ee(t,e);return`#version 300 es
in ${n} ${t};
out vec4 ${i};
void main() {
  ${i} = ${r};
}`}function te(s){switch(s){case 1:return"float";case 2:return"vec2";case 3:return"vec3";case 4:return"vec4";default:throw new Error(`invalid channels: ${s}`)}}function ee(s,t){switch(t){case 1:return`vec4(${s}, 0.0, 0.0, 1.0)`;case 2:return`vec4(${s}, 0.0, 1.0)`;case 3:return`vec4(${s}, 1.0)`;case 4:return s;default:throw new Error(`invalid channels: ${t}`)}}const ie=[0,1,1,1],ne=`uniform pickingUniforms {
  float isActive;
  float isAttribute;
  float isHighlightActive;
  float useFloatColors;
  vec3 highlightedObjectColor;
  vec4 highlightColor;
} picking;

out vec4 picking_vRGBcolor_Avalid;

// Normalize unsigned byte color to 0-1 range
vec3 picking_normalizeColor(vec3 color) {
  return picking.useFloatColors > 0.5 ? color : color / 255.0;
}

// Normalize unsigned byte color to 0-1 range
vec4 picking_normalizeColor(vec4 color) {
  return picking.useFloatColors > 0.5 ? color : color / 255.0;
}

bool picking_isColorZero(vec3 color) {
  return dot(color, vec3(1.0)) < 0.00001;
}

bool picking_isColorValid(vec3 color) {
  return dot(color, vec3(1.0)) > 0.00001;
}

// Check if this vertex is highlighted 
bool isVertexHighlighted(vec3 vertexColor) {
  vec3 highlightedObjectColor = picking_normalizeColor(picking.highlightedObjectColor);
  return
    bool(picking.isHighlightActive) && picking_isColorZero(abs(vertexColor - highlightedObjectColor));
}

// Set the current picking color
void picking_setPickingColor(vec3 pickingColor) {
  pickingColor = picking_normalizeColor(pickingColor);

  if (bool(picking.isActive)) {
    // Use alpha as the validity flag. If pickingColor is [0, 0, 0] fragment is non-pickable
    picking_vRGBcolor_Avalid.a = float(picking_isColorValid(pickingColor));

    if (!bool(picking.isAttribute)) {
      // Stores the picking color so that the fragment shader can render it during picking
      picking_vRGBcolor_Avalid.rgb = pickingColor;
    }
  } else {
    // Do the comparison with selected item color in vertex shader as it should mean fewer compares
    picking_vRGBcolor_Avalid.a = float(isVertexHighlighted(pickingColor));
  }
}

void picking_setPickingAttribute(float value) {
  if (bool(picking.isAttribute)) {
    picking_vRGBcolor_Avalid.r = value;
  }
}

void picking_setPickingAttribute(vec2 value) {
  if (bool(picking.isAttribute)) {
    picking_vRGBcolor_Avalid.rg = value;
  }
}

void picking_setPickingAttribute(vec3 value) {
  if (bool(picking.isAttribute)) {
    picking_vRGBcolor_Avalid.rgb = value;
  }
}
`,se=`uniform pickingUniforms {
  float isActive;
  float isAttribute;
  float isHighlightActive;
  float useFloatColors;
  vec3 highlightedObjectColor;
  vec4 highlightColor;
} picking;

in vec4 picking_vRGBcolor_Avalid;

/*
 * Returns highlight color if this item is selected.
 */
vec4 picking_filterHighlightColor(vec4 color) {
  // If we are still picking, we don't highlight
  if (picking.isActive > 0.5) {
    return color;
  }

  bool selected = bool(picking_vRGBcolor_Avalid.a);

  if (selected) {
    // Blend in highlight color based on its alpha value
    float highLightAlpha = picking.highlightColor.a;
    float blendedAlpha = highLightAlpha + color.a * (1.0 - highLightAlpha);
    float highLightRatio = highLightAlpha / blendedAlpha;

    vec3 blendedRGB = mix(color.rgb, picking.highlightColor.rgb, highLightRatio);
    return vec4(blendedRGB, blendedAlpha);
  } else {
    return color;
  }
}

/*
 * Returns picking color if picking enabled else unmodified argument.
 */
vec4 picking_filterPickingColor(vec4 color) {
  if (bool(picking.isActive)) {
    if (picking_vRGBcolor_Avalid.a == 0.0) {
      discard;
    }
    return picking_vRGBcolor_Avalid;
  }
  return color;
}

/*
 * Returns picking color if picking is enabled if not
 * highlight color if this item is selected, otherwise unmodified argument.
 */
vec4 picking_filterColor(vec4 color) {
  vec4 highlightColor = picking_filterHighlightColor(color);
  return picking_filterPickingColor(highlightColor);
}
`,ot={props:{},uniforms:{},name:"picking",uniformTypes:{isActive:"f32",isAttribute:"f32",isHighlightActive:"f32",useFloatColors:"f32",highlightedObjectColor:"vec3<f32>",highlightColor:"vec4<f32>"},defaultUniforms:{isActive:!1,isAttribute:!1,isHighlightActive:!1,useFloatColors:!0,highlightedObjectColor:[0,0,0],highlightColor:ie},vs:ne,fs:se,getUniforms:re};function re(s={},t){const e={};if(s.highlightedObjectColor!==void 0)if(s.highlightedObjectColor===null)e.isHighlightActive=!1;else{e.isHighlightActive=!0;const i=s.highlightedObjectColor.slice(0,3);e.highlightedObjectColor=i}if(s.highlightColor){const i=Array.from(s.highlightColor,n=>n/255);Number.isFinite(i[3])||(i[3]=1),e.highlightColor=i}return s.isActive!==void 0&&(e.isActive=!!s.isActive,e.isAttribute=!!s.isAttribute),s.useFloatColors!==void 0&&(e.useFloatColors=!!s.useFloatColors),e}const at=`precision highp int;

// #if (defined(SHADER_TYPE_FRAGMENT) && defined(LIGHTING_FRAGMENT)) || (defined(SHADER_TYPE_VERTEX) && defined(LIGHTING_VERTEX))
struct AmbientLight {
  vec3 color;
};

struct PointLight {
  vec3 color;
  vec3 position;
  vec3 attenuation; // 2nd order x:Constant-y:Linear-z:Exponential
};

struct DirectionalLight {
  vec3 color;
  vec3 direction;
};

uniform lightingUniforms {
  int enabled;
  int lightType;

  int directionalLightCount;
  int pointLightCount;

  vec3 ambientColor;

  vec3 lightColor0;
  vec3 lightPosition0;
  vec3 lightDirection0;
  vec3 lightAttenuation0;

  vec3 lightColor1;
  vec3 lightPosition1;
  vec3 lightDirection1;
  vec3 lightAttenuation1;

  vec3 lightColor2;
  vec3 lightPosition2;
  vec3 lightDirection2;
  vec3 lightAttenuation2;
} lighting;

PointLight lighting_getPointLight(int index) {
  switch (index) {
    case 0:
      return PointLight(lighting.lightColor0, lighting.lightPosition0, lighting.lightAttenuation0);
    case 1:
      return PointLight(lighting.lightColor1, lighting.lightPosition1, lighting.lightAttenuation1);
    case 2:
    default:  
      return PointLight(lighting.lightColor2, lighting.lightPosition2, lighting.lightAttenuation2);
  }
}

DirectionalLight lighting_getDirectionalLight(int index) {
  switch (index) {
    case 0:
      return DirectionalLight(lighting.lightColor0, lighting.lightDirection0);
    case 1:
      return DirectionalLight(lighting.lightColor1, lighting.lightDirection1);
    case 2:
    default:   
      return DirectionalLight(lighting.lightColor2, lighting.lightDirection2);
  }
} 

float getPointLightAttenuation(PointLight pointLight, float distance) {
  return pointLight.attenuation.x
       + pointLight.attenuation.y * distance
       + pointLight.attenuation.z * distance * distance;
}

// #endif
`,oe=`// #if (defined(SHADER_TYPE_FRAGMENT) && defined(LIGHTING_FRAGMENT)) || (defined(SHADER_TYPE_VERTEX) && defined(LIGHTING_VERTEX))
struct AmbientLight {
  color: vec3<f32>,
};

struct PointLight {
  color: vec3<f32>,
  position: vec3<f32>,
  attenuation: vec3<f32>, // 2nd order x:Constant-y:Linear-z:Exponential
};

struct DirectionalLight {
  color: vec3<f32>,
  direction: vec3<f32>,
};

struct lightingUniforms {
  enabled: i32,
  pointLightCount: i32,
  directionalLightCount: i32,

  ambientColor: vec3<f32>,

  // TODO - support multiple lights by uncommenting arrays below
  lightType: i32,
  lightColor: vec3<f32>,
  lightDirection: vec3<f32>,
  lightPosition: vec3<f32>,
  lightAttenuation: vec3<f32>,

  // AmbientLight ambientLight;
  // PointLight pointLight[MAX_LIGHTS];
  // DirectionalLight directionalLight[MAX_LIGHTS];
};

// Binding 0:1 is reserved for lighting (Note: could go into separate bind group as it is stable across draw calls)
@binding(1) @group(0) var<uniform> lighting : lightingUniforms;

fn lighting_getPointLight(index: i32) -> PointLight {
  return PointLight(lighting.lightColor, lighting.lightPosition, lighting.lightAttenuation);
}

fn lighting_getDirectionalLight(index: i32) -> DirectionalLight {
  return DirectionalLight(lighting.lightColor, lighting.lightDirection);
} 

fn getPointLightAttenuation(pointLight: PointLight, distance: f32) -> f32 {
  return pointLight.attenuation.x
       + pointLight.attenuation.y * distance
       + pointLight.attenuation.z * distance * distance;
}
`,ae=5,le=255;var B;(function(s){s[s.POINT=0]="POINT",s[s.DIRECTIONAL=1]="DIRECTIONAL"})(B||(B={}));const M={props:{},uniforms:{},name:"lighting",defines:{},uniformTypes:{enabled:"i32",lightType:"i32",directionalLightCount:"i32",pointLightCount:"i32",ambientColor:"vec3<f32>",lightColor0:"vec3<f32>",lightPosition0:"vec3<f32>",lightDirection0:"vec3<f32>",lightAttenuation0:"vec3<f32>",lightColor1:"vec3<f32>",lightPosition1:"vec3<f32>",lightDirection1:"vec3<f32>",lightAttenuation1:"vec3<f32>",lightColor2:"vec3<f32>",lightPosition2:"vec3<f32>",lightDirection2:"vec3<f32>",lightAttenuation2:"vec3<f32>"},defaultUniforms:{enabled:1,lightType:B.POINT,directionalLightCount:0,pointLightCount:0,ambientColor:[.1,.1,.1],lightColor0:[1,1,1],lightPosition0:[1,1,2],lightDirection0:[1,1,1],lightAttenuation0:[1,0,0],lightColor1:[1,1,1],lightPosition1:[1,1,2],lightDirection1:[1,1,1],lightAttenuation1:[1,0,0],lightColor2:[1,1,1],lightPosition2:[1,1,2],lightDirection2:[1,1,1],lightAttenuation2:[1,0,0]},source:oe,vs:at,fs:at,getUniforms:ce};function ce(s,t={}){if(s=s&&{...s},!s)return{...M.defaultUniforms};s.lights&&(s={...s,...fe(s.lights),lights:void 0});const{ambientLight:e,pointLights:i,directionalLights:n}=s||{};if(!(e||i&&i.length>0||n&&n.length>0))return{...M.defaultUniforms,enabled:0};const o={...M.defaultUniforms,...t,...ue({ambientLight:e,pointLights:i,directionalLights:n})};return s.enabled!==void 0&&(o.enabled=s.enabled?1:0),o}function ue({ambientLight:s,pointLights:t=[],directionalLights:e=[]}){const i={};i.ambientColor=Y(s);let n=0;for(const r of t){i.lightType=B.POINT;const o=n;i[`lightColor${o}`]=Y(r),i[`lightPosition${o}`]=r.position,i[`lightAttenuation${o}`]=r.attenuation||[1,0,0],n++}for(const r of e){i.lightType=B.DIRECTIONAL;const o=n;i[`lightColor${o}`]=Y(r),i[`lightDirection${o}`]=r.direction,n++}return n>ae&&Ft.warn("MAX_LIGHTS exceeded")(),i.directionalLightCount=e.length,i.pointLightCount=t.length,i}function fe(s){const t={pointLights:[],directionalLights:[]};for(const e of s||[])switch(e.type){case"ambient":t.ambientLight=e;break;case"directional":t.directionalLights?.push(e);break;case"point":t.pointLights?.push(e);break}return t}function Y(s={}){const{color:t=[0,0,0],intensity:e=1}=s;return t.map(i=>i*e/le)}const he=`uniform phongMaterialUniforms {
  uniform float ambient;
  uniform float diffuse;
  uniform float shininess;
  uniform vec3  specularColor;
} material;
`,de=`#define MAX_LIGHTS 3

uniform phongMaterialUniforms {
  uniform float ambient;
  uniform float diffuse;
  uniform float shininess;
  uniform vec3  specularColor;
} material;

vec3 lighting_getLightColor(vec3 surfaceColor, vec3 light_direction, vec3 view_direction, vec3 normal_worldspace, vec3 color) {
  vec3 halfway_direction = normalize(light_direction + view_direction);
  float lambertian = dot(light_direction, normal_worldspace);
  float specular = 0.0;
  if (lambertian > 0.0) {
    float specular_angle = max(dot(normal_worldspace, halfway_direction), 0.0);
    specular = pow(specular_angle, material.shininess);
  }
  lambertian = max(lambertian, 0.0);
  return (lambertian * material.diffuse * surfaceColor + specular * material.specularColor) * color;
}

vec3 lighting_getLightColor(vec3 surfaceColor, vec3 cameraPosition, vec3 position_worldspace, vec3 normal_worldspace) {
  vec3 lightColor = surfaceColor;

  if (lighting.enabled == 0) {
    return lightColor;
  }

  vec3 view_direction = normalize(cameraPosition - position_worldspace);
  lightColor = material.ambient * surfaceColor * lighting.ambientColor;

  for (int i = 0; i < lighting.pointLightCount; i++) {
    PointLight pointLight = lighting_getPointLight(i);
    vec3 light_position_worldspace = pointLight.position;
    vec3 light_direction = normalize(light_position_worldspace - position_worldspace);
    float light_attenuation = getPointLightAttenuation(pointLight, distance(light_position_worldspace, position_worldspace));
    lightColor += lighting_getLightColor(surfaceColor, light_direction, view_direction, normal_worldspace, pointLight.color / light_attenuation);
  }

  int totalLights = min(MAX_LIGHTS, lighting.pointLightCount + lighting.directionalLightCount);
  for (int i = lighting.pointLightCount; i < totalLights; i++) {
    DirectionalLight directionalLight = lighting_getDirectionalLight(i);
    lightColor += lighting_getLightColor(surfaceColor, -directionalLight.direction, view_direction, normal_worldspace, directionalLight.color);
  }
  
  return lightColor;
}
`,ge=`struct phongMaterialUniforms {
  ambient: f32,
  diffuse: f32,
  shininess: f32,
  specularColor: vec3<f32>,
};

@binding(2) @group(0) var<uniform> phongMaterial : phongMaterialUniforms;

fn lighting_getLightColor(surfaceColor: vec3<f32>, light_direction: vec3<f32>, view_direction: vec3<f32>, normal_worldspace: vec3<f32>, color: vec3<f32>) -> vec3<f32> {
  let halfway_direction: vec3<f32> = normalize(light_direction + view_direction);
  var lambertian: f32 = dot(light_direction, normal_worldspace);
  var specular: f32 = 0.0;
  if (lambertian > 0.0) {
    let specular_angle = max(dot(normal_worldspace, halfway_direction), 0.0);
    specular = pow(specular_angle, phongMaterial.shininess);
  }
  lambertian = max(lambertian, 0.0);
  return (lambertian * phongMaterial.diffuse * surfaceColor + specular * phongMaterial.specularColor) * color;
}

fn lighting_getLightColor2(surfaceColor: vec3<f32>, cameraPosition: vec3<f32>, position_worldspace: vec3<f32>, normal_worldspace: vec3<f32>) -> vec3<f32> {
  var lightColor: vec3<f32> = surfaceColor;

  if (lighting.enabled == 0) {
    return lightColor;
  }

  let view_direction: vec3<f32> = normalize(cameraPosition - position_worldspace);
  lightColor = phongMaterial.ambient * surfaceColor * lighting.ambientColor;

  if (lighting.lightType == 0) {
    let pointLight: PointLight  = lighting_getPointLight(0);
    let light_position_worldspace: vec3<f32> = pointLight.position;
    let light_direction: vec3<f32> = normalize(light_position_worldspace - position_worldspace);
    lightColor += lighting_getLightColor(surfaceColor, light_direction, view_direction, normal_worldspace, pointLight.color);
  } else if (lighting.lightType == 1) {
    var directionalLight: DirectionalLight = lighting_getDirectionalLight(0);
    lightColor += lighting_getLightColor(surfaceColor, -directionalLight.direction, view_direction, normal_worldspace, directionalLight.color);
  }
  
  return lightColor;
  /*
  for (int i = 0; i < MAX_LIGHTS; i++) {
    if (i >= lighting.pointLightCount) {
      break;
    }
    PointLight pointLight = lighting.pointLight[i];
    vec3 light_position_worldspace = pointLight.position;
    vec3 light_direction = normalize(light_position_worldspace - position_worldspace);
    lightColor += lighting_getLightColor(surfaceColor, light_direction, view_direction, normal_worldspace, pointLight.color);
  }

  for (int i = 0; i < MAX_LIGHTS; i++) {
    if (i >= lighting.directionalLightCount) {
      break;
    }
    DirectionalLight directionalLight = lighting.directionalLight[i];
    lightColor += lighting_getLightColor(surfaceColor, -directionalLight.direction, view_direction, normal_worldspace, directionalLight.color);
  }
  */
}

fn lighting_getSpecularLightColor(cameraPosition: vec3<f32>, position_worldspace: vec3<f32>, normal_worldspace: vec3<f32>) -> vec3<f32>{
  var lightColor = vec3<f32>(0, 0, 0);
  let surfaceColor = vec3<f32>(0, 0, 0);

  if (lighting.enabled == 0) {
    let view_direction = normalize(cameraPosition - position_worldspace);

    switch (lighting.lightType) {
      case 0, default: {
        let pointLight: PointLight = lighting_getPointLight(0);
        let light_position_worldspace: vec3<f32> = pointLight.position;
        let light_direction: vec3<f32> = normalize(light_position_worldspace - position_worldspace);
        lightColor += lighting_getLightColor(surfaceColor, light_direction, view_direction, normal_worldspace, pointLight.color);
      }
      case 1: {
        let directionalLight: DirectionalLight = lighting_getDirectionalLight(0);
        lightColor += lighting_getLightColor(surfaceColor, -directionalLight.direction, view_direction, normal_worldspace, directionalLight.color);
      }
    }
  }
  return lightColor;
}
`,pe={name:"phongMaterial",dependencies:[M],source:ge,vs:he,fs:de,defines:{LIGHTING_FRAGMENT:!0},uniformTypes:{ambient:"f32",diffuse:"f32",shininess:"f32",specularColor:"vec3<f32>"},defaultUniforms:{ambient:.35,diffuse:.6,shininess:32,specularColor:[.15,.15,.15]},getUniforms(s){const t={...s};return t.specularColor&&(t.specularColor=t.specularColor.map(e=>e/255)),{...pe.defaultUniforms,...t}}},me=`// Define a structure to hold both the clip-space position and the common position.
struct ProjectResult {
  clipPosition: vec4<f32>,
  commonPosition: vec4<f32>,
};

// This function mimics the GLSL version with the 'out' parameter by returning both values.
fn project_position_to_clipspace_and_commonspace(
    position: vec3<f32>,
    position64Low: vec3<f32>,
    offset: vec3<f32>
) -> ProjectResult {
  // Compute the projected position.
  let projectedPosition: vec3<f32> = project_position_vec3_f64(position, position64Low);

  // Start with the provided offset.
  var finalOffset: vec3<f32> = offset;

  // Get whether a rotation is needed and the rotation matrix.
  let rotationResult = project_needs_rotation(projectedPosition);

  // If rotation is needed, update the offset.
  if (rotationResult.needsRotation) {
    finalOffset = rotationResult.transform * offset;
  }

  // Compute the common position.
  let commonPosition: vec4<f32> = vec4<f32>(projectedPosition + finalOffset, 1.0);

  // Convert to clip-space.
  let clipPosition: vec4<f32> = project_common_position_to_clipspace(commonPosition);

  return ProjectResult(clipPosition, commonPosition);
}

// A convenience overload that returns only the clip-space position.
fn project_position_to_clipspace(
    position: vec3<f32>,
    position64Low: vec3<f32>,
    offset: vec3<f32>
) -> vec4<f32> {
  return project_position_to_clipspace_and_commonspace(position, position64Low, offset).clipPosition;
}
`,be=`vec4 project_position_to_clipspace(
  vec3 position, vec3 position64Low, vec3 offset, out vec4 commonPosition
) {
  vec3 projectedPosition = project_position(position, position64Low);
  mat3 rotation;
  if (project_needs_rotation(projectedPosition, rotation)) {
    // offset is specified as ENU
    // when in globe projection, rotate offset so that the ground alighs with the surface of the globe
    offset = rotation * offset;
  }
  commonPosition = vec4(projectedPosition + offset, 1.0);
  return project_common_position_to_clipspace(commonPosition);
}

vec4 project_position_to_clipspace(
  vec3 position, vec3 position64Low, vec3 offset
) {
  vec4 commonPosition;
  return project_position_to_clipspace(position, position64Low, offset, commonPosition);
}
`,Xi={name:"project32",dependencies:[Yt],source:me,vs:be},Zi={...ot,defaultUniforms:{...ot.defaultUniforms,useFloatColors:!1},inject:{"vs:DECKGL_FILTER_GL_POSITION":`
    // for picking depth values
    picking_setPickingAttribute(position.z / position.w);
  `,"vs:DECKGL_FILTER_COLOR":`
  picking_setPickingColor(geometry.pickingColor);
  `,"fs:DECKGL_FILTER_COLOR":{order:99,injection:`
  // use highlight color if this fragment belongs to the selected object.
  color = picking_filterHighlightColor(color);

  // use picking color if rendering to picking FBO.
  color = picking_filterPickingColor(color);
    `}}},lt=[0,0,0];function H(s,t,e=!1){const i=t.projectPosition(s);if(e&&t instanceof zt){const[n,r,o=0]=s,a=t.getDistanceScales([n,r]);i[2]=o*a.unitsPerMeter[2]}return i}function ye(s){const{viewport:t,modelMatrix:e,coordinateOrigin:i}=s;let{coordinateSystem:n,fromCoordinateSystem:r,fromCoordinateOrigin:o}=s;return n===T.DEFAULT&&(n=t.isGeospatial?T.LNGLAT:T.CARTESIAN),r===void 0&&(r=n),o===void 0&&(o=i),{viewport:t,coordinateSystem:n,coordinateOrigin:i,modelMatrix:e,fromCoordinateSystem:r,fromCoordinateOrigin:o}}function _t(s,{viewport:t,modelMatrix:e,coordinateSystem:i,coordinateOrigin:n,offsetMode:r}){let[o,a,c=0]=s;switch(e&&([o,a,c]=Nt([],[o,a,c,1],e)),i){case T.LNGLAT:return H([o,a,c],t,r);case T.LNGLAT_OFFSETS:return H([o+n[0],a+n[1],c+(n[2]||0)],t,r);case T.METER_OFFSETS:return H(Mt(n,[o,a,c]),t,r);case T.CARTESIAN:default:return t.isGeospatial?[o+n[0],a+n[1],c+n[2]]:t.projectPosition([o,a,c])}}function ve(s,t){const{viewport:e,coordinateSystem:i,coordinateOrigin:n,modelMatrix:r,fromCoordinateSystem:o,fromCoordinateOrigin:a}=ye(t),{autoOffset:c=!0}=t,{geospatialOrigin:l=lt,shaderCoordinateOrigin:u=lt,offsetMode:f=!1}=c?Ht(e,i,n):{},d=_t(s,{viewport:e,modelMatrix:r,coordinateSystem:o,coordinateOrigin:a,offsetMode:f});if(f){const b=e.projectPosition(l||u);Ut(d,d,b)}return d}class O{device;model;transformFeedback;static defaultProps={...it.defaultProps,outputs:void 0,feedbackBuffers:void 0};static isSupported(t){return t?.info?.type==="webgl"}constructor(t,e=O.defaultProps){if(!O.isSupported(t))throw new Error("BufferTransform not yet implemented on WebGPU");this.device=t,this.model=new it(this.device,{id:e.id||"buffer-transform-model",fs:e.fs||Qt(),topology:e.topology||"point-list",varyings:e.outputs||e.varyings,...e}),this.transformFeedback=this.device.createTransformFeedback({layout:this.model.pipeline.shaderLayout,buffers:e.feedbackBuffers}),this.model.setTransformFeedback(this.transformFeedback),Object.seal(this)}destroy(){this.model&&this.model.destroy()}delete(){this.destroy()}run(t){t?.inputBuffers&&this.model.setAttributes(t.inputBuffers),t?.outputBuffers&&this.transformFeedback.setBuffers(t.outputBuffers);const e=this.device.beginRenderPass(t);this.model.draw(e),e.end()}getBuffer(t){return this.transformFeedback.getBuffer(t)}readAsync(t){const e=this.getBuffer(t);if(!e)throw new Error("BufferTransform#getBuffer");if(e instanceof S)return e.readAsync();const{buffer:i,byteOffset:n=0,byteLength:r=i.byteLength}=e;return i.readAsync(n,r)}}class Ki{id;topology;vertexCount;indices;attributes;userData={};constructor(t){const{attributes:e={},indices:i=null,vertexCount:n=null}=t;this.id=t.id||qt("geometry"),this.topology=t.topology,i&&(this.indices=ArrayBuffer.isView(i)?{value:i,size:1}:i),this.attributes={};for(const[r,o]of Object.entries(e)){const a=ArrayBuffer.isView(o)?{value:o}:o;if(!ArrayBuffer.isView(a.value))throw new Error(`${this._print(r)}: must be typed array or object with value as typed array`);if((r==="POSITION"||r==="positions")&&!a.size&&(a.size=3),r==="indices"){if(this.indices)throw new Error("Multiple indices detected");this.indices=a}else this.attributes[r]=a}this.indices&&this.indices.isIndexed!==void 0&&(this.indices=Object.assign({},this.indices),delete this.indices.isIndexed),this.vertexCount=n||this._calculateVertexCount(this.attributes,this.indices)}getVertexCount(){return this.vertexCount}getAttributes(){return this.indices?{indices:this.indices,...this.attributes}:this.attributes}_print(t){return`Geometry ${this.id} attribute ${t}`}_setAttributes(t,e){return this}_calculateVertexCount(t,e){if(e)return e.value.length;let i=1/0;for(const n of Object.values(t)){const{value:r,size:o,constant:a}=n;!a&&r&&o!==void 0&&o>=1&&(i=Math.min(i,r.length/o))}return i}}function _e(s){switch(s){case"float64":return Float64Array;case"uint8":case"unorm8":return Uint8ClampedArray;default:return Dt(s)}}const Ae=jt;function N(s,t,e){const i=e==="webgpu"&&t.type==="uint8"?"unorm8":t.type;return{attribute:s,format:t.size>1?`${i}x${t.size}`:t.type,byteOffset:t.offset||0}}function E(s){return s.stride||s.size*s.bytesPerElement}function Te(s,t){return s.type===t.type&&s.size===t.size&&E(s)===E(t)&&(s.offset||0)===(t.offset||0)}function X(s,t){t.offset&&P.removed("shaderAttribute.offset","vertexOffset, elementOffset")();const e=E(s),i=t.vertexOffset!==void 0?t.vertexOffset:s.vertexOffset||0,n=t.elementOffset||0,r=i*e+n*s.bytesPerElement+(s.offset||0);return{...t,offset:r,stride:e}}function Ce(s,t){const e=X(s,t);return{high:e,low:{...e,offset:e.offset+s.size*4}}}class Pe{constructor(t,e,i){this._buffer=null,this.device=t,this.id=e.id||"",this.size=e.size||1;const n=e.logicalType||e.type,r=n==="float64";let{defaultValue:o}=e;o=Number.isFinite(o)?[o]:o||new Array(this.size).fill(0);let a;r?a="float32":!n&&e.isIndexed?a="uint32":a=n||"float32";let c=_e(n||a);this.doublePrecision=r,r&&e.fp64===!1&&(c=Float32Array),this.value=null,this.settings={...e,defaultType:c,defaultValue:o,logicalType:n,type:a,normalized:a.includes("norm"),size:this.size,bytesPerElement:c.BYTES_PER_ELEMENT},this.state={...i,externalBuffer:null,bufferAccessor:this.settings,allocatedValue:null,numInstances:0,bounds:null,constant:!1}}get isConstant(){return this.state.constant}get buffer(){return this._buffer}get byteOffset(){const t=this.getAccessor();return t.vertexOffset?t.vertexOffset*E(t):0}get numInstances(){return this.state.numInstances}set numInstances(t){this.state.numInstances=t}delete(){this._buffer&&(this._buffer.delete(),this._buffer=null),W.release(this.state.allocatedValue)}getBuffer(){return this.state.constant?null:this.state.externalBuffer||this._buffer}getValue(t=this.id,e=null){const i={};if(this.state.constant){const n=this.value;if(e){const r=X(this.getAccessor(),e),o=r.offset/n.BYTES_PER_ELEMENT,a=r.size||this.size;i[t]=n.subarray(o,o+a)}else i[t]=n}else i[t]=this.getBuffer();return this.doublePrecision&&(this.value instanceof Float64Array?i[`${t}64Low`]=i[t]:i[`${t}64Low`]=new Float32Array(this.size)),i}_getBufferLayout(t=this.id,e=null){const i=this.getAccessor(),n=[],r={name:this.id,byteStride:E(i),attributes:n};if(this.doublePrecision){const o=Ce(i,e||{});n.push(N(t,{...i,...o.high},this.device.type),N(`${t}64Low`,{...i,...o.low},this.device.type))}else if(e){const o=X(i,e);n.push(N(t,{...i,...o},this.device.type))}else n.push(N(t,i,this.device.type));return r}setAccessor(t){this.state.bufferAccessor=t}getAccessor(){return this.state.bufferAccessor}getBounds(){if(this.state.bounds)return this.state.bounds;let t=null;if(this.state.constant&&this.value){const e=Array.from(this.value);t=[e,e]}else{const{value:e,numInstances:i,size:n}=this,r=i*n;if(e&&r&&e.length>=r){const o=new Array(n).fill(1/0),a=new Array(n).fill(-1/0);for(let c=0;c<r;)for(let l=0;l<n;l++){const u=e[c++];u<o[l]&&(o[l]=u),u>a[l]&&(a[l]=u)}t=[o,a]}}return this.state.bounds=t,t}setData(t){const{state:e}=this;let i;ArrayBuffer.isView(t)?i={value:t}:t instanceof S?i={buffer:t}:i=t;const n={...this.settings,...i};if(ArrayBuffer.isView(i.value)){if(!i.type)if(this.doublePrecision&&i.value instanceof Float64Array)n.type="float32";else{const o=Ae(i.value);n.type=n.normalized?o.replace("int","norm"):o}n.bytesPerElement=i.value.BYTES_PER_ELEMENT,n.stride=E(n)}if(e.bounds=null,i.constant){let r=i.value;if(r=this._normalizeValue(r,[],0),this.settings.normalized&&(r=this.normalizeConstant(r)),!(!e.constant||!this._areValuesEqual(r,this.value)))return!1;e.externalBuffer=null,e.constant=!0,this.value=ArrayBuffer.isView(r)?r:new Float32Array(r)}else if(i.buffer){const r=i.buffer;e.externalBuffer=r,e.constant=!1,this.value=i.value||null}else if(i.value){this._checkExternalBuffer(i);let r=i.value;e.externalBuffer=null,e.constant=!1,this.value=r;let{buffer:o}=this;const a=E(n),c=(n.vertexOffset||0)*a;if(this.doublePrecision&&r instanceof Float64Array&&(r=G(r,n)),this.settings.isIndexed){const u=this.settings.defaultType;r.constructor!==u&&(r=new u(r))}const l=r.byteLength+c+a*2;(!o||o.byteLength<l)&&(o=this._createBuffer(l)),o.write(r,c)}return this.setAccessor(n),!0}updateSubBuffer(t={}){this.state.bounds=null;const e=this.value,{startOffset:i=0,endOffset:n}=t;this.buffer.write(this.doublePrecision&&e instanceof Float64Array?G(e,{size:this.size,startIndex:i,endIndex:n}):e.subarray(i,n),i*e.BYTES_PER_ELEMENT+this.byteOffset)}allocate(t,e=!1){const{state:i}=this,n=i.allocatedValue,r=W.allocate(n,t+1,{size:this.size,type:this.settings.defaultType,copy:e});this.value=r;const{byteOffset:o}=this;let{buffer:a}=this;return(!a||a.byteLength<r.byteLength+o)&&(a=this._createBuffer(r.byteLength+o),e&&n&&a.write(n instanceof Float64Array?G(n,this):n,o)),i.allocatedValue=r,i.constant=!1,i.externalBuffer=null,this.setAccessor(this.settings),!0}_checkExternalBuffer(t){const{value:e}=t;if(!ArrayBuffer.isView(e))throw new Error(`Attribute ${this.id} value is not TypedArray`);const i=this.settings.defaultType;let n=!1;if(this.doublePrecision&&(n=e.BYTES_PER_ELEMENT<4),n)throw new Error(`Attribute ${this.id} does not support ${e.constructor.name}`);!(e instanceof i)&&this.settings.normalized&&!("normalized"in t)&&P.warn(`Attribute ${this.id} is normalized`)()}normalizeConstant(t){switch(this.settings.type){case"snorm8":return new Float32Array(t).map(e=>(e+128)/255*2-1);case"snorm16":return new Float32Array(t).map(e=>(e+32768)/65535*2-1);case"unorm8":return new Float32Array(t).map(e=>e/255);case"unorm16":return new Float32Array(t).map(e=>e/65535);default:return t}}_normalizeValue(t,e,i){const{defaultValue:n,size:r}=this.settings;if(Number.isFinite(t))return e[i]=t,e;if(!t){let o=r;for(;--o>=0;)e[i+o]=n[o];return e}switch(r){case 4:e[i+3]=Number.isFinite(t[3])?t[3]:n[3];case 3:e[i+2]=Number.isFinite(t[2])?t[2]:n[2];case 2:e[i+1]=Number.isFinite(t[1])?t[1]:n[1];case 1:e[i+0]=Number.isFinite(t[0])?t[0]:n[0];break;default:let o=r;for(;--o>=0;)e[i+o]=Number.isFinite(t[o])?t[o]:n[o]}return e}_areValuesEqual(t,e){if(!t||!e)return!1;const{size:i}=this;for(let n=0;n<i;n++)if(t[n]!==e[n])return!1;return!0}_createBuffer(t){this._buffer&&this._buffer.destroy();const{isIndexed:e,type:i}=this.settings;return this._buffer=this.device.createBuffer({...this._buffer?.props,id:this.id,usage:(e?S.INDEX:S.VERTEX)|S.COPY_DST,indexType:e?i:void 0,byteLength:t}),this._buffer}}const ct=[],ut=[];function Le(s,t=0,e=1/0){let i=ct;const n={index:-1,data:s,target:[]};return s?typeof s[Symbol.iterator]=="function"?i=s:s.length>0&&(ut.length=s.length,i=ut):i=ct,(t>0||Number.isFinite(e))&&(i=(Array.isArray(i)?i:Array.from(i)).slice(t,e),n.index=t-1),{iterable:i,objectInfo:n}}function At(s){return s&&s[Symbol.asyncIterator]}function we(s,t){const{size:e,stride:i,offset:n,startIndices:r,nested:o}=t,a=s.BYTES_PER_ELEMENT,c=i?i/a:e,l=n?n/a:0,u=Math.floor((s.length-l)/c);return(f,{index:d,target:b})=>{if(!r){const g=d*c+l;for(let p=0;p<e;p++)b[p]=s[g+p];return b}const y=r[d],m=r[d+1]||u;let C;if(o){C=new Array(m-y);for(let g=y;g<m;g++){const p=g*c+l;b=new Array(e);for(let h=0;h<e;h++)b[h]=s[p+h];C[g-y]=b}}else if(c===e)C=s.subarray(y*e+l,m*e+l);else{C=new s.constructor((m-y)*e);let g=0;for(let p=y;p<m;p++){const h=p*c+l;for(let v=0;v<e;v++)C[g++]=s[h+v]}}return C}}const Ee=[],z=[[0,1/0]];function xe(s,t){if(s===z||(t[0]<0&&(t[0]=0),t[0]>=t[1]))return s;const e=[],i=s.length;let n=0;for(let r=0;r<i;r++){const o=s[r];o[1]<t[0]?(e.push(o),n=r+1):o[0]>t[1]?e.push(o):t=[Math.min(o[0],t[0]),Math.max(o[1],t[1])]}return e.splice(n,0,t),e}const Ie={interpolation:{duration:0,easing:s=>s},spring:{stiffness:.05,damping:.5}};function Tt(s,t){if(!s)return null;Number.isFinite(s)&&(s={type:"interpolation",duration:s});const e=s.type||"interpolation";return{...Ie[e],...t,...s,type:e}}class Ct extends Pe{constructor(t,e){super(t,e,{startIndices:null,lastExternalBuffer:null,binaryValue:null,binaryAccessor:null,needsUpdate:!0,needsRedraw:!1,layoutChanged:!1,updateRanges:z}),this.constant=!1,this.settings.update=e.update||(e.accessor?this._autoUpdater:void 0),Object.seal(this.settings),Object.seal(this.state),this._validateAttributeUpdaters()}get startIndices(){return this.state.startIndices}set startIndices(t){this.state.startIndices=t}needsUpdate(){return this.state.needsUpdate}needsRedraw({clearChangedFlags:t=!1}={}){const e=this.state.needsRedraw;return this.state.needsRedraw=e&&!t,e}layoutChanged(){return this.state.layoutChanged}setAccessor(t){var e;(e=this.state).layoutChanged||(e.layoutChanged=!Te(t,this.getAccessor())),super.setAccessor(t)}getUpdateTriggers(){const{accessor:t}=this.settings;return[this.id].concat(typeof t!="function"&&t||[])}supportsTransition(){return!!this.settings.transition}getTransitionSetting(t){if(!t||!this.supportsTransition())return null;const{accessor:e}=this.settings,i=this.settings.transition,n=Array.isArray(e)?t[e.find(r=>t[r])]:t[e];return Tt(n,i)}setNeedsUpdate(t=this.id,e){if(this.state.needsUpdate=this.state.needsUpdate||t,this.setNeedsRedraw(t),e){const{startRow:i=0,endRow:n=1/0}=e;this.state.updateRanges=xe(this.state.updateRanges,[i,n])}else this.state.updateRanges=z}clearNeedsUpdate(){this.state.needsUpdate=!1,this.state.updateRanges=Ee}setNeedsRedraw(t=this.id){this.state.needsRedraw=this.state.needsRedraw||t}allocate(t){const{state:e,settings:i}=this;return i.noAlloc?!1:i.update?(super.allocate(t,e.updateRanges!==z),!0):!1}updateBuffer({numInstances:t,data:e,props:i,context:n}){if(!this.needsUpdate())return!1;const{state:{updateRanges:r},settings:{update:o,noAlloc:a}}=this;let c=!0;if(o){for(const[l,u]of r)o.call(n,this,{data:e,startRow:l,endRow:u,props:i,numInstances:t});if(this.value)if(this.constant||!this.buffer||this.buffer.byteLength<this.value.byteLength+this.byteOffset)this.setData({value:this.value,constant:this.constant}),this.constant=!1;else for(const[l,u]of r){const f=Number.isFinite(l)?this.getVertexOffset(l):0,d=Number.isFinite(u)?this.getVertexOffset(u):a||!Number.isFinite(t)?this.value.length:t*this.size;super.updateSubBuffer({startOffset:f,endOffset:d})}this._checkAttributeArray()}else c=!1;return this.clearNeedsUpdate(),this.setNeedsRedraw(),c}setConstantValue(t,e){const i=this.device.type==="webgpu";if(i||e===void 0||typeof e=="function"){if(i&&typeof e!="function"){const o=this._normalizeValue(e,[],0);this._areValuesEqual(o,this.value)||this.setNeedsUpdate("WebGPU constant updated")}return!1}const n=this.settings.transform&&t?this.settings.transform.call(t,e):e;return this.setData({constant:!0,value:n})&&this.setNeedsRedraw(),this.clearNeedsUpdate(),!0}setExternalBuffer(t){const{state:e}=this;return t?(this.clearNeedsUpdate(),e.lastExternalBuffer===t||(e.lastExternalBuffer=t,this.setNeedsRedraw(),this.setData(t)),!0):(e.lastExternalBuffer=null,!1)}setBinaryValue(t,e=null){const{state:i,settings:n}=this;if(!t)return i.binaryValue=null,i.binaryAccessor=null,!1;if(n.noAlloc)return!1;if(i.binaryValue===t)return this.clearNeedsUpdate(),!0;if(i.binaryValue=t,this.setNeedsRedraw(),n.transform||e!==this.startIndices){ArrayBuffer.isView(t)&&(t={value:t});const o=t;L(ArrayBuffer.isView(o.value),`invalid ${n.accessor}`);const a=!!o.size&&o.size!==this.size;return i.binaryAccessor=we(o.value,{size:o.size||this.size,stride:o.stride,offset:o.offset,startIndices:e,nested:a}),!1}return this.clearNeedsUpdate(),this.setData(t),!0}getVertexOffset(t){const{startIndices:e}=this;return(e?t<e.length?e[t]:this.numInstances:t)*this.size}getValue(){const t=this.settings.shaderAttributes,e=super.getValue();if(!t)return e;for(const i in t)Object.assign(e,super.getValue(i,t[i]));return e}getBufferLayout(t){this.state.layoutChanged=!1;const e=this.settings.shaderAttributes,i=super._getBufferLayout(),{stepMode:n}=this.settings;if(n==="dynamic"?i.stepMode=t?t.isInstanced?"instance":"vertex":"instance":i.stepMode=n??"vertex",!e)return i;for(const r in e){const o=super._getBufferLayout(r,e[r]);i.attributes.push(...o.attributes)}return i}_autoUpdater(t,{data:e,startRow:i,endRow:n,props:r,numInstances:o}){if(t.constant&&this.context.device.type!=="webgpu")return;const{settings:a,state:c,value:l,size:u,startIndices:f}=t,{accessor:d,transform:b}=a;let y=c.binaryAccessor||(typeof d=="function"?d:r[d]);typeof y!="function"&&typeof d=="string"&&(y=()=>r[d]),L(typeof y=="function",`accessor "${d}" is not a function`);let m=t.getVertexOffset(i);const{iterable:C,objectInfo:g}=Le(e,i,n);for(const p of C){g.index++;let h=y(p,g);if(b&&(h=b.call(this,h)),f){const v=(g.index<f.length-1?f[g.index+1]:o)-f[g.index];if(h&&Array.isArray(h[0])){let F=m;for(const Bt of h)t._normalizeValue(Bt,l,F),F+=u}else h&&h.length>u?l.set(h,m):(t._normalizeValue(h,g.target,0),Xt({target:l,source:g.target,start:m,count:v}));m+=v*u}else t._normalizeValue(h,l,m),m+=u}}_validateAttributeUpdaters(){const{settings:t}=this;if(!(t.noAlloc||typeof t.update=="function"))throw new Error(`Attribute ${this.id} missing update or accessor`)}_checkAttributeArray(){const{value:t}=this,e=Math.min(4,this.size);if(t&&t.length>=e){let i=!0;switch(e){case 4:i=i&&Number.isFinite(t[3]);case 3:i=i&&Number.isFinite(t[2]);case 2:i=i&&Number.isFinite(t[1]);case 1:i=i&&Number.isFinite(t[0]);break;default:i=!1}if(!i)throw new Error(`Illegal attribute generated for ${this.id}`)}}}function q(s){const{source:t,target:e,start:i=0,size:n,getData:r}=s,o=s.end||e.length,a=t.length,c=o-i;if(a>c){e.set(t.subarray(0,c),i);return}if(e.set(t,i),!r)return;let l=a;for(;l<c;){const u=r(l,t);for(let f=0;f<n;f++)e[i+l]=u[f]||0,l++}}function Se({source:s,target:t,size:e,getData:i,sourceStartIndices:n,targetStartIndices:r}){if(!n||!r)return q({source:s,target:t,size:e,getData:i}),t;let o=0,a=0;const c=i&&((u,f)=>i(u+a,f)),l=Math.min(n.length,r.length);for(let u=1;u<l;u++){const f=n[u]*e,d=r[u]*e;q({source:s.subarray(o,f),target:t,start:a,end:d,size:e,getData:c}),o=f,a=d}return a<t.length&&q({source:[],target:t,start:a,size:e,getData:c}),t}function Re(s){const{device:t,settings:e,value:i}=s,n=new Ct(t,e);return n.setData({value:i instanceof Float64Array?new Float64Array(0):new Float32Array(0),normalized:e.normalized}),n}function Pt(s){switch(s){case 1:return"float";case 2:return"vec2";case 3:return"vec3";case 4:return"vec4";default:throw new Error(`No defined attribute type for size "${s}"`)}}function Lt(s){switch(s){case 1:return"float32";case 2:return"float32x2";case 3:return"float32x3";case 4:return"float32x4";default:throw new Error("invalid type size")}}function wt(s){s.push(s.shift())}function Oe(s,t){const{doublePrecision:e,settings:i,value:n,size:r}=s,o=e&&n instanceof Float64Array?2:1;let a=0;const{shaderAttributes:c}=s.settings;if(c)for(const l of Object.values(c))a=Math.max(a,l.vertexOffset??0);return(i.noAlloc?n.length:(t+a)*r)*o}function Et({device:s,source:t,target:e}){return(!e||e.byteLength<t.byteLength)&&(e?.destroy(),e=s.createBuffer({byteLength:t.byteLength,usage:t.usage})),e}function xt({device:s,buffer:t,attribute:e,fromLength:i,toLength:n,fromStartIndices:r,getData:o=a=>a}){const a=e.doublePrecision&&e.value instanceof Float64Array?2:1,c=e.size*a,l=e.byteOffset,u=e.settings.bytesPerElement<4?l/e.settings.bytesPerElement*4:l,f=e.startIndices,d=r&&f,b=e.isConstant;if(!d&&t&&i>=n)return t;const y=e.value instanceof Float64Array?Float32Array:e.value.constructor,m=b?e.value:new y(e.getBuffer().readSyncWebGL(l,n*y.BYTES_PER_ELEMENT).buffer);if(e.settings.normalized&&!b){const h=o;o=(v,F)=>e.normalizeConstant(h(v,F))}const C=b?(h,v)=>o(m,v):(h,v)=>o(m.subarray(h+l,h+l+c),v),g=t?new Float32Array(t.readSyncWebGL(u,i*4).buffer):new Float32Array(0),p=new Float32Array(n);return Se({source:g,target:p,sourceStartIndices:r,targetStartIndices:f,size:c,getData:C}),(!t||t.byteLength<p.byteLength+u)&&(t?.destroy(),t=s.createBuffer({byteLength:p.byteLength+u,usage:35050})),t.write(p,u),t}class It{constructor({device:t,attribute:e,timeline:i}){this.buffers=[],this.currentLength=0,this.device=t,this.transition=new tt(i),this.attribute=e,this.attributeInTransition=Re(e),this.currentStartIndices=e.startIndices}get inProgress(){return this.transition.inProgress}start(t,e,i=1/0){this.settings=t,this.currentStartIndices=this.attribute.startIndices,this.currentLength=Oe(this.attribute,e),this.transition.start({...t,duration:i})}update(){const t=this.transition.update();return t&&this.onUpdate(),t}setBuffer(t){this.attributeInTransition.setData({buffer:t,normalized:this.attribute.settings.normalized,value:this.attributeInTransition.value})}cancel(){this.transition.cancel()}delete(){this.cancel();for(const t of this.buffers)t.destroy();this.buffers.length=0}}class ke extends It{constructor({device:t,attribute:e,timeline:i}){super({device:t,attribute:e,timeline:i}),this.type="interpolation",this.transform=Ne(t,e)}start(t,e){const i=this.currentLength,n=this.currentStartIndices;if(super.start(t,e,t.duration),t.duration<=0){this.transition.cancel();return}const{buffers:r,attribute:o}=this;wt(r),r[0]=xt({device:this.device,buffer:r[0],attribute:o,fromLength:i,toLength:this.currentLength,fromStartIndices:n,getData:t.enter}),r[1]=Et({device:this.device,source:r[0],target:r[1]}),this.setBuffer(r[1]);const{transform:a}=this,c=a.model;let l=Math.floor(this.currentLength/o.size);St(o)&&(l/=2),c.setVertexCount(l),o.isConstant?(c.setAttributes({aFrom:r[0]}),c.setConstantAttributes({aTo:o.value})):c.setAttributes({aFrom:r[0],aTo:o.getBuffer()}),a.transformFeedback.setBuffers({vCurrent:r[1]})}onUpdate(){const{duration:t,easing:e}=this.settings,{time:i}=this.transition;let n=i/t;e&&(n=e(n));const{model:r}=this.transform,o={time:n};r.shaderInputs.setProps({interpolation:o}),this.transform.run({discard:!0})}delete(){super.delete(),this.transform.destroy()}}const Be=`uniform interpolationUniforms {
  float time;
} interpolation;
`,ft={name:"interpolation",vs:Be,uniformTypes:{time:"f32"}},Fe=`#version 300 es
#define SHADER_NAME interpolation-transition-vertex-shader

in ATTRIBUTE_TYPE aFrom;
in ATTRIBUTE_TYPE aTo;
out ATTRIBUTE_TYPE vCurrent;

void main(void) {
  vCurrent = mix(aFrom, aTo, interpolation.time);
  gl_Position = vec4(0.0);
}
`,Ue=`#version 300 es
#define SHADER_NAME interpolation-transition-vertex-shader

in ATTRIBUTE_TYPE aFrom;
in ATTRIBUTE_TYPE aFrom64Low;
in ATTRIBUTE_TYPE aTo;
in ATTRIBUTE_TYPE aTo64Low;
out ATTRIBUTE_TYPE vCurrent;
out ATTRIBUTE_TYPE vCurrent64Low;

vec2 mix_fp64(vec2 a, vec2 b, float x) {
  vec2 range = sub_fp64(b, a);
  return sum_fp64(a, mul_fp64(range, vec2(x, 0.0)));
}

void main(void) {
  for (int i=0; i<ATTRIBUTE_SIZE; i++) {
    vec2 value = mix_fp64(vec2(aFrom[i], aFrom64Low[i]), vec2(aTo[i], aTo64Low[i]), interpolation.time);
    vCurrent[i] = value.x;
    vCurrent64Low[i] = value.y;
  }
  gl_Position = vec4(0.0);
}
`;function St(s){return s.doublePrecision&&s.value instanceof Float64Array}function Ne(s,t){const e=t.size,i=Pt(e),n=Lt(e),r=t.getBufferLayout();return St(t)?new O(s,{vs:Ue,bufferLayout:[{name:"aFrom",byteStride:8*e,attributes:[{attribute:"aFrom",format:n,byteOffset:0},{attribute:"aFrom64Low",format:n,byteOffset:4*e}]},{name:"aTo",byteStride:8*e,attributes:[{attribute:"aTo",format:n,byteOffset:0},{attribute:"aTo64Low",format:n,byteOffset:4*e}]}],modules:[Wt,ft],defines:{ATTRIBUTE_TYPE:i,ATTRIBUTE_SIZE:e},moduleSettings:{},varyings:["vCurrent","vCurrent64Low"],bufferMode:35980,disableWarnings:!0}):new O(s,{vs:Fe,bufferLayout:[{name:"aFrom",format:n},{name:"aTo",format:r.attributes[0].format}],modules:[ft],defines:{ATTRIBUTE_TYPE:i},varyings:["vCurrent"],disableWarnings:!0})}class Me extends It{constructor({device:t,attribute:e,timeline:i}){super({device:t,attribute:e,timeline:i}),this.type="spring",this.texture=$e(t),this.framebuffer=Ye(t,this.texture),this.transform=Ge(t,e)}start(t,e){const i=this.currentLength,n=this.currentStartIndices;super.start(t,e);const{buffers:r,attribute:o}=this;for(let c=0;c<2;c++)r[c]=xt({device:this.device,buffer:r[c],attribute:o,fromLength:i,toLength:this.currentLength,fromStartIndices:n,getData:t.enter});r[2]=Et({device:this.device,source:r[0],target:r[2]}),this.setBuffer(r[1]);const{model:a}=this.transform;a.setVertexCount(Math.floor(this.currentLength/o.size)),o.isConstant?a.setConstantAttributes({aTo:o.value}):a.setAttributes({aTo:o.getBuffer()})}onUpdate(){const{buffers:t,transform:e,framebuffer:i,transition:n}=this,r=this.settings;e.model.setAttributes({aPrev:t[0],aCur:t[1]}),e.transformFeedback.setBuffers({vNext:t[2]});const o={stiffness:r.stiffness,damping:r.damping};e.model.shaderInputs.setProps({spring:o}),e.run({framebuffer:i,discard:!1,parameters:{viewport:[0,0,1,1]},clearColor:[0,0,0,0]}),wt(t),this.setBuffer(t[1]),this.device.readPixelsToArrayWebGL(i)[0]>0||n.end()}delete(){super.delete(),this.transform.destroy(),this.texture.destroy(),this.framebuffer.destroy()}}const ze=`uniform springUniforms {
  float damping;
  float stiffness;
} spring;
`,je={name:"spring",vs:ze,uniformTypes:{damping:"f32",stiffness:"f32"}},De=`#version 300 es
#define SHADER_NAME spring-transition-vertex-shader

#define EPSILON 0.00001

in ATTRIBUTE_TYPE aPrev;
in ATTRIBUTE_TYPE aCur;
in ATTRIBUTE_TYPE aTo;
out ATTRIBUTE_TYPE vNext;
out float vIsTransitioningFlag;

ATTRIBUTE_TYPE getNextValue(ATTRIBUTE_TYPE cur, ATTRIBUTE_TYPE prev, ATTRIBUTE_TYPE dest) {
  ATTRIBUTE_TYPE velocity = cur - prev;
  ATTRIBUTE_TYPE delta = dest - cur;
  ATTRIBUTE_TYPE force = delta * spring.stiffness;
  ATTRIBUTE_TYPE resistance = velocity * spring.damping;
  return force - resistance + velocity + cur;
}

void main(void) {
  bool isTransitioning = length(aCur - aPrev) > EPSILON || length(aTo - aCur) > EPSILON;
  vIsTransitioningFlag = isTransitioning ? 1.0 : 0.0;

  vNext = getNextValue(aCur, aPrev, aTo);
  gl_Position = vec4(0, 0, 0, 1);
  gl_PointSize = 100.0;
}
`,Ve=`#version 300 es
#define SHADER_NAME spring-transition-is-transitioning-fragment-shader

in float vIsTransitioningFlag;

out vec4 fragColor;

void main(void) {
  if (vIsTransitioningFlag == 0.0) {
    discard;
  }
  fragColor = vec4(1.0);
}`;function Ge(s,t){const e=Pt(t.size),i=Lt(t.size);return new O(s,{vs:De,fs:Ve,bufferLayout:[{name:"aPrev",format:i},{name:"aCur",format:i},{name:"aTo",format:t.getBufferLayout().attributes[0].format}],varyings:["vNext"],modules:[je],defines:{ATTRIBUTE_TYPE:e},parameters:{depthCompare:"always",blendColorOperation:"max",blendColorSrcFactor:"one",blendColorDstFactor:"one",blendAlphaOperation:"max",blendAlphaSrcFactor:"one",blendAlphaDstFactor:"one"}})}function $e(s){return s.createTexture({data:new Uint8Array(4),format:"rgba8unorm",width:1,height:1})}function Ye(s,t){return s.createFramebuffer({id:"spring-transition-is-transitioning-framebuffer",width:1,height:1,colorAttachments:[t]})}const He={interpolation:ke,spring:Me};class qe{constructor(t,{id:e,timeline:i}){if(!t)throw new Error("AttributeTransitionManager is constructed without device");this.id=e,this.device=t,this.timeline=i,this.transitions={},this.needsRedraw=!1,this.numInstances=1}finalize(){for(const t in this.transitions)this._removeTransition(t)}update({attributes:t,transitions:e,numInstances:i}){this.numInstances=i||1;for(const n in t){const r=t[n],o=r.getTransitionSetting(e);o&&this._updateAttribute(n,r,o)}for(const n in this.transitions){const r=t[n];(!r||!r.getTransitionSetting(e))&&this._removeTransition(n)}}hasAttribute(t){const e=this.transitions[t];return e&&e.inProgress}getAttributes(){const t={};for(const e in this.transitions){const i=this.transitions[e];i.inProgress&&(t[e]=i.attributeInTransition)}return t}run(){if(this.numInstances===0)return!1;for(const e in this.transitions)this.transitions[e].update()&&(this.needsRedraw=!0);const t=this.needsRedraw;return this.needsRedraw=!1,t}_removeTransition(t){this.transitions[t].delete(),delete this.transitions[t]}_updateAttribute(t,e,i){const n=this.transitions[t];let r=!n||n.type!==i.type;if(r){n&&this._removeTransition(t);const o=He[i.type];o?this.transitions[t]=new o({attribute:e,timeline:this.timeline,device:this.device}):(P.error(`unsupported transition type '${i.type}'`)(),r=!1)}(r||e.needsRedraw())&&(this.needsRedraw=!0,this.transitions[t].start(i,this.numInstances))}}const ht="attributeManager.invalidate",We="attributeManager.updateStart",Xe="attributeManager.updateEnd",Ze="attribute.updateStart",Ke="attribute.allocate",Je="attribute.updateEnd";class Qe{constructor(t,{id:e="attribute-manager",stats:i,timeline:n}={}){this.mergeBoundsMemoized=yt(Vt),this.id=e,this.device=t,this.attributes={},this.updateTriggers={},this.needsRedraw=!0,this.userData={},this.stats=i,this.attributeTransitionManager=new qe(t,{id:`${e}-transitions`,timeline:n}),Object.seal(this)}finalize(){for(const t in this.attributes)this.attributes[t].delete();this.attributeTransitionManager.finalize()}getNeedsRedraw(t={clearRedrawFlags:!1}){const e=this.needsRedraw;return this.needsRedraw=this.needsRedraw&&!t.clearRedrawFlags,e&&this.id}setNeedsRedraw(){this.needsRedraw=!0}add(t){this._add(t)}addInstanced(t){this._add(t,{stepMode:"instance"})}remove(t){for(const e of t)this.attributes[e]!==void 0&&(this.attributes[e].delete(),delete this.attributes[e])}invalidate(t,e){const i=this._invalidateTrigger(t,e);_(ht,this,t,i)}invalidateAll(t){for(const e in this.attributes)this.attributes[e].setNeedsUpdate(e,t);_(ht,this,"all")}update({data:t,numInstances:e,startIndices:i=null,transitions:n,props:r={},buffers:o={},context:a={}}){let c=!1;_(We,this),this.stats&&this.stats.get("Update Attributes").timeStart();for(const l in this.attributes){const u=this.attributes[l],f=u.settings.accessor;u.startIndices=i,u.numInstances=e,r[l]&&P.removed(`props.${l}`,`data.attributes.${l}`)(),u.setExternalBuffer(o[l])||u.setBinaryValue(typeof f=="string"?o[f]:void 0,t.startIndices)||typeof f=="string"&&!o[f]&&u.setConstantValue(a,r[f])||u.needsUpdate()&&(c=!0,this._updateAttribute({attribute:u,numInstances:e,data:t,props:r,context:a})),this.needsRedraw=this.needsRedraw||u.needsRedraw()}c&&_(Xe,this,e),this.stats&&this.stats.get("Update Attributes").timeEnd(),this.attributeTransitionManager.update({attributes:this.attributes,numInstances:e,transitions:n})}updateTransition(){const{attributeTransitionManager:t}=this,e=t.run();return this.needsRedraw=this.needsRedraw||e,e}getAttributes(){return{...this.attributes,...this.attributeTransitionManager.getAttributes()}}getBounds(t){const e=t.map(i=>this.attributes[i]?.getBounds());return this.mergeBoundsMemoized(e)}getChangedAttributes(t={clearChangedFlags:!1}){const{attributes:e,attributeTransitionManager:i}=this,n={...i.getAttributes()};for(const r in e){const o=e[r];o.needsRedraw(t)&&!i.hasAttribute(r)&&(n[r]=o)}return n}getBufferLayouts(t){return Object.values(this.getAttributes()).map(e=>e.getBufferLayout(t))}_add(t,e){for(const i in t){const n=t[i],r={...n,id:i,size:n.isIndexed&&1||n.size||1,...e};this.attributes[i]=new Ct(this.device,r)}this._mapUpdateTriggersToAttributes()}_mapUpdateTriggersToAttributes(){const t={};for(const e in this.attributes)this.attributes[e].getUpdateTriggers().forEach(n=>{t[n]||(t[n]=[]),t[n].push(e)});this.updateTriggers=t}_invalidateTrigger(t,e){const{attributes:i,updateTriggers:n}=this,r=n[t];return r&&r.forEach(o=>{const a=i[o];a&&a.setNeedsUpdate(a.id,e)}),r}_updateAttribute(t){const{attribute:e,numInstances:i}=t;if(_(Ze,e),e.constant){e.setConstantValue(t.context,e.value);return}e.allocate(i)&&_(Ke,e,i),e.updateBuffer(t)&&(this.needsRedraw=!0,_(Je,e,i))}}class ti extends tt{get value(){return this._value}_onUpdate(){const{time:t,settings:{fromValue:e,toValue:i,duration:n,easing:r}}=this,o=r(t/n);this._value=Gt(e,i,o)}}const dt=1e-5;function gt(s,t,e,i,n){const r=t-s,a=(e-t)*n,c=-r*i;return a+c+r+t}function ei(s,t,e,i,n){if(Array.isArray(e)){const r=[];for(let o=0;o<e.length;o++)r[o]=gt(s[o],t[o],e[o],i,n);return r}return gt(s,t,e,i,n)}function pt(s,t){if(Array.isArray(s)){let e=0;for(let i=0;i<s.length;i++){const n=s[i]-t[i];e+=n*n}return Math.sqrt(e)}return Math.abs(s-t)}class ii extends tt{get value(){return this._currValue}_onUpdate(){const{fromValue:t,toValue:e,damping:i,stiffness:n}=this.settings,{_prevValue:r=t,_currValue:o=t}=this;let a=ei(r,o,e,i,n);const c=pt(a,e),l=pt(a,o);c<dt&&l<dt&&(a=e,this.end()),this._prevValue=o,this._currValue=a}}const ni={interpolation:ti,spring:ii};class si{constructor(t){this.transitions=new Map,this.timeline=t}get active(){return this.transitions.size>0}add(t,e,i,n){const{transitions:r}=this;if(r.has(t)){const c=r.get(t),{value:l=c.settings.fromValue}=c;e=l,this.remove(t)}if(n=Tt(n),!n)return;const o=ni[n.type];if(!o){P.error(`unsupported transition type '${n.type}'`)();return}const a=new o(this.timeline);a.start({...n,fromValue:e,toValue:i}),r.set(t,a)}remove(t){const{transitions:e}=this;e.has(t)&&(e.get(t).cancel(),e.delete(t))}update(){const t={};for(const[e,i]of this.transitions)i.update(),t[e]=i.value,i.inProgress||this.remove(e);return t}clear(){for(const t of this.transitions.keys())this.remove(t)}}function ri(s){const t=s[x];for(const e in t){const i=t[e],{validate:n}=i;if(n&&!n(s[e],i))throw new Error(`Invalid prop ${e}: ${s[e]}`)}}function oi(s,t){const e=Rt({newProps:s,oldProps:t,propTypes:s[x],ignoreProps:{data:null,updateTriggers:null,extensions:null,transitions:null}}),i=li(s,t);let n=!1;return i||(n=ci(s,t)),{dataChanged:i,propsChanged:e,updateTriggersChanged:n,extensionsChanged:ui(s,t),transitionsChanged:ai(s,t)}}function ai(s,t){if(!s.transitions)return!1;const e={},i=s[x];let n=!1;for(const r in s.transitions){const o=i[r],a=o&&o.type;(a==="number"||a==="color"||a==="array")&&Z(s[r],t[r],o)&&(e[r]=!0,n=!0)}return n?e:!1}function Rt({newProps:s,oldProps:t,ignoreProps:e={},propTypes:i={},triggerName:n="props"}){if(t===s)return!1;if(typeof s!="object"||s===null)return`${n} changed shallowly`;if(typeof t!="object"||t===null)return`${n} changed shallowly`;for(const r of Object.keys(s))if(!(r in e)){if(!(r in t))return`${n}.${r} added`;const o=Z(s[r],t[r],i[r]);if(o)return`${n}.${r} ${o}`}for(const r of Object.keys(t))if(!(r in e)){if(!(r in s))return`${n}.${r} dropped`;if(!Object.hasOwnProperty.call(s,r)){const o=Z(s[r],t[r],i[r]);if(o)return`${n}.${r} ${o}`}}return!1}function Z(s,t,e){let i=e&&e.equal;return i&&!i(s,t,e)||!i&&(i=s&&t&&s.equals,i&&!i.call(s,t))?"changed deeply":!i&&t!==s?"changed shallowly":null}function li(s,t){if(t===null)return"oldProps is null, initial diff";let e=!1;const{dataComparator:i,_dataDiff:n}=s;return i?i(s.data,t.data)||(e="Data comparator detected a change"):s.data!==t.data&&(e="A new data container was supplied"),e&&n&&(e=n(s.data,t.data)||e),e}function ci(s,t){if(t===null)return{all:!0};if("all"in s.updateTriggers&&mt(s,t,"all"))return{all:!0};const e={};let i=!1;for(const n in s.updateTriggers)n!=="all"&&mt(s,t,n)&&(e[n]=!0,i=!0);return i?e:!1}function ui(s,t){if(t===null)return!0;const e=t.extensions,{extensions:i}=s;if(i===e)return!1;if(!e||!i||i.length!==e.length)return!0;for(let n=0;n<i.length;n++)if(!i[n].equals(e[n]))return!0;return!1}function mt(s,t,e){let i=s.updateTriggers[e];i=i??{};let n=t.updateTriggers[e];return n=n??{},Rt({oldProps:n,newProps:i,triggerName:e})}const fi="count(): argument not an object",hi="count(): argument not a container";function di(s){if(!pi(s))throw new Error(fi);if(typeof s.count=="function")return s.count();if(Number.isFinite(s.size))return s.size;if(Number.isFinite(s.length))return s.length;if(gi(s))return Object.keys(s).length;throw new Error(hi)}function gi(s){return s!==null&&typeof s=="object"&&s.constructor===Object}function pi(s){return s!==null&&typeof s=="object"}const mi={minFilter:"linear",mipmapFilter:"linear",magFilter:"linear",addressModeU:"clamp-to-edge",addressModeV:"clamp-to-edge"},K={};function bi(s,t,e,i){if(e instanceof vt)return e;e.constructor&&e.constructor.name!=="Object"&&(e={data:e});let n=null;e.compressed&&(n={minFilter:"linear",mipmapFilter:e.data.length>1?"nearest":"linear"});const{width:r,height:o}=e.data,a=t.createTexture({...e,sampler:{...mi,...n,...i},mipLevels:t.getMipLevelCount(r,o)});return a.generateMipmapsWebGL(),K[a.id]=s,a}function yi(s,t){!t||!(t instanceof vt)||K[t.id]===s&&(t.delete(),delete K[t.id])}const vi={boolean:{validate(s,t){return!0},equal(s,t,e){return!!s==!!t}},number:{validate(s,t){return Number.isFinite(s)&&(!("max"in t)||s<=t.max)&&(!("min"in t)||s>=t.min)}},color:{validate(s,t){return t.optional&&!s||J(s)&&(s.length===3||s.length===4)},equal(s,t,e){return U(s,t,1)}},accessor:{validate(s,t){const e=D(s);return e==="function"||e===D(t.value)},equal(s,t,e){return typeof t=="function"?!0:U(s,t,1)}},array:{validate(s,t){return t.optional&&!s||J(s)},equal(s,t,e){const{compare:i}=e,n=Number.isInteger(i)?i:i?1:0;return i?U(s,t,n):s===t}},object:{equal(s,t,e){if(e.ignore)return!0;const{compare:i}=e,n=Number.isInteger(i)?i:i?1:0;return i?U(s,t,n):s===t}},function:{validate(s,t){return t.optional&&!s||typeof s=="function"},equal(s,t,e){return!e.compare&&e.ignore!==!1||s===t}},data:{transform:(s,t,e)=>{if(!s)return s;const{dataTransform:i}=e.props;return i?i(s):typeof s.shape=="string"&&s.shape.endsWith("-table")&&Array.isArray(s.data)?s.data:s}},image:{transform:(s,t,e)=>{const i=e.context;return!i||!i.device?null:bi(e.id,i.device,s,{...t.parameters,...e.props.textureParameters})},release:(s,t,e)=>{yi(e.id,s)}}};function _i(s){const t={},e={},i={};for(const[n,r]of Object.entries(s)){const o=r?.deprecatedFor;if(o)i[n]=Array.isArray(o)?o:[o];else{const a=Ai(n,r);t[n]=a,e[n]=a.value}}return{propTypes:t,defaultProps:e,deprecatedProps:i}}function Ai(s,t){switch(D(t)){case"object":return k(s,t);case"array":return k(s,{type:"array",value:t,compare:!1});case"boolean":return k(s,{type:"boolean",value:t});case"number":return k(s,{type:"number",value:t});case"function":return k(s,{type:"function",value:t,compare:!0});default:return{name:s,type:"unknown",value:t}}}function k(s,t){return"type"in t?{name:s,...vi[t.type],...t}:"value"in t?{name:s,type:D(t.value),...t}:{name:s,type:"object",value:t}}function J(s){return Array.isArray(s)||ArrayBuffer.isView(s)}function D(s){return J(s)?"array":s===null?"null":typeof s}function Ti(s,t){let e;for(let r=t.length-1;r>=0;r--){const o=t[r];"extensions"in o&&(e=o.extensions)}const i=Q(s.constructor,e),n=Object.create(i);n[j]=s,n[I]={},n[w]={};for(let r=0;r<t.length;++r){const o=t[r];for(const a in o)n[a]=o[a]}return Object.freeze(n),n}const Ci="_mergedDefaultProps";function Q(s,t){if(!(s instanceof V.constructor))return{};let e=Ci;if(t)for(const n of t){const r=n.constructor;r&&(e+=`:${r.extensionName||r.name}`)}const i=Ot(s,e);return i||(s[e]=Pi(s,t||[]))}function Pi(s,t){if(!s.prototype)return null;const i=Object.getPrototypeOf(s),n=Q(i),r=Ot(s,"defaultProps")||{},o=_i(r),a=Object.assign(Object.create(null),n,o.defaultProps),c=Object.assign(Object.create(null),n?.[x],o.propTypes),l=Object.assign(Object.create(null),n?.[$],o.deprecatedProps);for(const u of t){const f=Q(u.constructor);f&&(Object.assign(a,f),Object.assign(c,f[x]),Object.assign(l,f[$]))}return Li(a,s),Ei(a,c),wi(a,l),a[x]=c,a[$]=l,t.length===0&&!et(s,"_propTypes")&&(s._propTypes=c),a}function Li(s,t){const e=Ii(t);Object.defineProperties(s,{id:{writable:!0,value:e}})}function wi(s,t){for(const e in t)Object.defineProperty(s,e,{enumerable:!1,set(i){const n=`${this.id}: ${e}`;for(const r of t[e])et(this,r)||(this[r]=i);P.deprecated(n,t[e].join("/"))()}})}function Ei(s,t){const e={},i={};for(const n in t){const r=t[n],{name:o,value:a}=r;r.async&&(e[o]=a,i[o]=xi(o))}s[R]=e,s[I]={},Object.defineProperties(s,i)}function xi(s){return{enumerable:!0,set(t){typeof t=="string"||t instanceof Promise||At(t)?this[I][s]=t:this[w][s]=t},get(){if(this[w]){if(s in this[w])return this[w][s]||this[R][s];if(s in this[I]){const t=this[j]&&this[j].internalState;if(t&&t.hasAsyncProp(s))return t.getAsyncProp(s)||this[R][s]}}return this[R][s]}}}function et(s,t){return Object.prototype.hasOwnProperty.call(s,t)}function Ot(s,t){return et(s,t)&&s[t]}function Ii(s){const t=s.componentName;return t||P.warn(`${s.name}.componentName not specified`)(),t||s.name}let Si=0;class V{constructor(...t){this.props=Ti(this,t),this.id=this.props.id,this.count=Si++}clone(t){const{props:e}=this,i={};for(const n in e[R])n in e[w]?i[n]=e[w][n]:n in e[I]&&(i[n]=e[I][n]);return new this.constructor({...e,...i,...t})}}V.componentName="Component";V.defaultProps={};const Ri=Object.freeze({});class Oi{constructor(t){this.component=t,this.asyncProps={},this.onAsyncPropUpdated=()=>{},this.oldProps=null,this.oldAsyncProps=null}finalize(){for(const t in this.asyncProps){const e=this.asyncProps[t];e&&e.type&&e.type.release&&e.type.release(e.resolvedValue,e.type,this.component)}this.asyncProps={},this.component=null,this.resetOldProps()}getOldProps(){return this.oldAsyncProps||this.oldProps||Ri}resetOldProps(){this.oldAsyncProps=null,this.oldProps=this.component?this.component.props:null}hasAsyncProp(t){return t in this.asyncProps}getAsyncProp(t){const e=this.asyncProps[t];return e&&e.resolvedValue}isAsyncPropLoading(t){if(t){const e=this.asyncProps[t];return!!(e&&e.pendingLoadCount>0&&e.pendingLoadCount!==e.resolvedLoadCount)}for(const e in this.asyncProps)if(this.isAsyncPropLoading(e))return!0;return!1}reloadAsyncProp(t,e){this._watchPromise(t,Promise.resolve(e))}setAsyncProps(t){this.component=t[j]||this.component;const e=t[w]||{},i=t[I]||t,n=t[R]||{};for(const r in e){const o=e[r];this._createAsyncPropData(r,n[r]),this._updateAsyncProp(r,o),e[r]=this.getAsyncProp(r)}for(const r in i){const o=i[r];this._createAsyncPropData(r,n[r]),this._updateAsyncProp(r,o)}}_fetch(t,e){return null}_onResolve(t,e){}_onError(t,e){}_updateAsyncProp(t,e){if(this._didAsyncInputValueChange(t,e)){if(typeof e=="string"&&(e=this._fetch(t,e)),e instanceof Promise){this._watchPromise(t,e);return}if(At(e)){this._resolveAsyncIterable(t,e);return}this._setPropValue(t,e)}}_freezeAsyncOldProps(){if(!this.oldAsyncProps&&this.oldProps){this.oldAsyncProps=Object.create(this.oldProps);for(const t in this.asyncProps)Object.defineProperty(this.oldAsyncProps,t,{enumerable:!0,value:this.oldProps[t]})}}_didAsyncInputValueChange(t,e){const i=this.asyncProps[t];return e===i.resolvedValue||e===i.lastValue?!1:(i.lastValue=e,!0)}_setPropValue(t,e){this._freezeAsyncOldProps();const i=this.asyncProps[t];i&&(e=this._postProcessValue(i,e),i.resolvedValue=e,i.pendingLoadCount++,i.resolvedLoadCount=i.pendingLoadCount)}_setAsyncPropValue(t,e,i){const n=this.asyncProps[t];n&&i>=n.resolvedLoadCount&&e!==void 0&&(this._freezeAsyncOldProps(),n.resolvedValue=e,n.resolvedLoadCount=i,this.onAsyncPropUpdated(t,e))}_watchPromise(t,e){const i=this.asyncProps[t];if(i){i.pendingLoadCount++;const n=i.pendingLoadCount;e.then(r=>{this.component&&(r=this._postProcessValue(i,r),this._setAsyncPropValue(t,r,n),this._onResolve(t,r))}).catch(r=>{this._onError(t,r)})}}async _resolveAsyncIterable(t,e){if(t!=="data"){this._setPropValue(t,e);return}const i=this.asyncProps[t];if(!i)return;i.pendingLoadCount++;const n=i.pendingLoadCount;let r=[],o=0;for await(const a of e){if(!this.component)return;const{dataTransform:c}=this.component.props;c?r=c(a,r):r=r.concat(a),Object.defineProperty(r,"__diff",{enumerable:!1,value:[{startRow:o,endRow:r.length}]}),o=r.length,this._setAsyncPropValue(t,r,n)}this._onResolve(t,r)}_postProcessValue(t,e){const i=t.type;return i&&this.component&&(i.release&&i.release(t.resolvedValue,i,this.component),i.transform)?i.transform(e,i,this.component):e}_createAsyncPropData(t,e){if(!this.asyncProps[t]){const n=this.component&&this.component.props[x];this.asyncProps[t]={type:n&&n[t],lastValue:null,resolvedValue:e,pendingLoadCount:0,resolvedLoadCount:0}}}}class ki extends Oi{constructor({attributeManager:t,layer:e}){super(e),this.attributeManager=t,this.needsRedraw=!0,this.needsUpdate=!0,this.subLayers=null,this.usesPickingColorCache=!1}get layer(){return this.component}_fetch(t,e){const i=this.layer,n=i?.props.fetch;return n?n(e,{propName:t,layer:i}):super._fetch(t,e)}_onResolve(t,e){const i=this.layer;if(i){const n=i.props.onDataLoad;t==="data"&&n&&n(e,{propName:t,layer:i})}}_onError(t,e){const i=this.layer;i&&i.raiseError(e,`loading ${t} of ${this.layer}`)}}const Bi="layer.changeFlag",Fi="layer.initialize",Ui="layer.update",Ni="layer.finalize",Mi="layer.matched",bt=2**24-1,zi=Object.freeze([]),ji=yt(({oldViewport:s,viewport:t})=>s.equals(t));let A=new Uint8ClampedArray(0);const Di={data:{type:"data",value:zi,async:!0},dataComparator:{type:"function",value:null,optional:!0},_dataDiff:{type:"function",value:s=>s&&s.__diff,optional:!0},dataTransform:{type:"function",value:null,optional:!0},onDataLoad:{type:"function",value:null,optional:!0},onError:{type:"function",value:null,optional:!0},fetch:{type:"function",value:(s,{propName:t,layer:e,loaders:i,loadOptions:n,signal:r})=>{const{resourceManager:o}=e.context;n=n||e.getLoadOptions(),i=i||e.props.loaders,r&&(n={...n,fetch:{...n?.fetch,signal:r}});let a=o.contains(s);return!a&&!n&&(o.add({resourceId:s,data:st(s,i),persistent:!1}),a=!0),a?o.subscribe({resourceId:s,onChange:c=>e.internalState?.reloadAsyncProp(t,c),consumerId:e.id,requestId:t}):st(s,i,n)}},updateTriggers:{},visible:!0,pickable:!1,opacity:{type:"number",min:0,max:1,value:1},operation:"draw",onHover:{type:"function",value:null,optional:!0},onClick:{type:"function",value:null,optional:!0},onDragStart:{type:"function",value:null,optional:!0},onDrag:{type:"function",value:null,optional:!0},onDragEnd:{type:"function",value:null,optional:!0},coordinateSystem:T.DEFAULT,coordinateOrigin:{type:"array",value:[0,0,0],compare:!0},modelMatrix:{type:"array",value:null,compare:!0,optional:!0},wrapLongitude:!1,positionFormat:"XYZ",colorFormat:"RGBA",parameters:{type:"object",value:{},optional:!0,compare:2},loadOptions:{type:"object",value:null,optional:!0,ignore:!0},transitions:null,extensions:[],loaders:{type:"array",value:[],optional:!0,ignore:!0},getPolygonOffset:{type:"function",value:({layerIndex:s})=>[0,-s*100]},highlightedObjectIndex:null,autoHighlight:!1,highlightColor:{type:"accessor",value:[0,0,128,128]}};class kt extends V{constructor(){super(...arguments),this.internalState=null,this.lifecycle=Zt.NO_STATE,this.parent=null}static get componentName(){return Object.prototype.hasOwnProperty.call(this,"layerName")?this.layerName:""}get root(){let t=this;for(;t.parent;)t=t.parent;return t}toString(){return`${this.constructor.layerName||this.constructor.name}({id: '${this.props.id}'})`}project(t){L(this.internalState);const e=this.internalState.viewport||this.context.viewport,i=_t(t,{viewport:e,modelMatrix:this.props.modelMatrix,coordinateOrigin:this.props.coordinateOrigin,coordinateSystem:this.props.coordinateSystem}),[n,r,o]=$t(i,e.pixelProjectionMatrix);return t.length===2?[n,r]:[n,r,o]}unproject(t){return L(this.internalState),(this.internalState.viewport||this.context.viewport).unproject(t)}projectPosition(t,e){L(this.internalState);const i=this.internalState.viewport||this.context.viewport;return ve(t,{viewport:i,modelMatrix:this.props.modelMatrix,coordinateOrigin:this.props.coordinateOrigin,coordinateSystem:this.props.coordinateSystem,...e})}get isComposite(){return!1}get isDrawable(){return!0}setState(t){this.setChangeFlags({stateChanged:!0}),Object.assign(this.state,t),this.setNeedsRedraw()}setNeedsRedraw(){this.internalState&&(this.internalState.needsRedraw=!0)}setNeedsUpdate(){this.internalState&&(this.context.layerManager.setNeedsUpdate(String(this)),this.internalState.needsUpdate=!0)}get isLoaded(){return this.internalState?!this.internalState.isAsyncPropLoading():!1}get wrapLongitude(){return this.props.wrapLongitude}isPickable(){return this.props.pickable&&this.props.visible}getModels(){const t=this.state;return t&&(t.models||t.model&&[t.model])||[]}setShaderModuleProps(...t){for(const e of this.getModels())e.shaderInputs.setProps(...t)}getAttributeManager(){return this.internalState&&this.internalState.attributeManager}getCurrentLayer(){return this.internalState&&this.internalState.layer}getLoadOptions(){return this.props.loadOptions}use64bitPositions(){const{coordinateSystem:t}=this.props;return t===T.DEFAULT||t===T.LNGLAT||t===T.CARTESIAN}onHover(t,e){return this.props.onHover&&this.props.onHover(t,e)||!1}onClick(t,e){return this.props.onClick&&this.props.onClick(t,e)||!1}nullPickingColor(){return[0,0,0]}encodePickingColor(t,e=[]){return e[0]=t+1&255,e[1]=t+1>>8&255,e[2]=t+1>>8>>8&255,e}decodePickingColor(t){L(t instanceof Uint8Array);const[e,i,n]=t;return e+i*256+n*65536-1}getNumInstances(){return Number.isFinite(this.props.numInstances)?this.props.numInstances:this.state&&this.state.numInstances!==void 0?this.state.numInstances:di(this.props.data)}getStartIndices(){return this.props.startIndices?this.props.startIndices:this.state&&this.state.startIndices?this.state.startIndices:null}getBounds(){return this.getAttributeManager()?.getBounds(["positions","instancePositions"])}getShaders(t){t=nt(t,{disableWarnings:!0,modules:this.context.defaultShaderModules});for(const e of this.props.extensions)t=nt(t,e.getShaders.call(this,e));return t}shouldUpdateState(t){return t.changeFlags.propsOrDataChanged}updateState(t){const e=this.getAttributeManager(),{dataChanged:i}=t.changeFlags;if(i&&e)if(Array.isArray(i))for(const n of i)e.invalidateAll(n);else e.invalidateAll();if(e){const{props:n}=t,r=this.internalState.hasPickingBuffer,o=Number.isInteger(n.highlightedObjectIndex)||n.pickable||n.extensions.some(a=>a.getNeedsPickingBuffer.call(this,a));if(r!==o){this.internalState.hasPickingBuffer=o;const{pickingColors:a,instancePickingColors:c}=e.attributes,l=a||c;l&&(o&&l.constant&&(l.constant=!1,e.invalidate(l.id)),!l.value&&!o&&(l.constant=!0,l.value=[0,0,0]))}}}finalizeState(t){for(const i of this.getModels())i.destroy();const e=this.getAttributeManager();e&&e.finalize(),this.context&&this.context.resourceManager.unsubscribe({consumerId:this.id}),this.internalState&&(this.internalState.uniformTransitions.clear(),this.internalState.finalize())}draw(t){for(const e of this.getModels())e.draw(t.renderPass)}getPickingInfo({info:t,mode:e,sourceLayer:i}){const{index:n}=t;return n>=0&&Array.isArray(this.props.data)&&(t.object=this.props.data[n]),t}raiseError(t,e){e&&(t=new Error(`${e}: ${t.message}`,{cause:t})),this.props.onError?.(t)||this.context?.onError?.(t,this)}getNeedsRedraw(t={clearRedrawFlags:!1}){return this._getNeedsRedraw(t)}needsUpdate(){return this.internalState?this.internalState.needsUpdate||this.hasUniformTransition()||this.shouldUpdateState(this._getUpdateParams()):!1}hasUniformTransition(){return this.internalState?.uniformTransitions.active||!1}activateViewport(t){if(!this.internalState)return;const e=this.internalState.viewport;this.internalState.viewport=t,(!e||!ji({oldViewport:e,viewport:t}))&&(this.setChangeFlags({viewportChanged:!0}),this.isComposite?this.needsUpdate()&&this.setNeedsUpdate():this._update())}invalidateAttribute(t="all"){const e=this.getAttributeManager();e&&(t==="all"?e.invalidateAll():e.invalidate(t))}updateAttributes(t){let e=!1;for(const i in t)t[i].layoutChanged()&&(e=!0);for(const i of this.getModels())this._setModelAttributes(i,t,e)}_updateAttributes(){const t=this.getAttributeManager();if(!t)return;const e=this.props,i=this.getNumInstances(),n=this.getStartIndices();t.update({data:e.data,numInstances:i,startIndices:n,props:e,transitions:e.transitions,buffers:e.data.attributes,context:this});const r=t.getChangedAttributes({clearChangedFlags:!0});this.updateAttributes(r)}_updateAttributeTransition(){const t=this.getAttributeManager();t&&t.updateTransition()}_updateUniformTransition(){const{uniformTransitions:t}=this.internalState;if(t.active){const e=t.update(),i=Object.create(this.props);for(const n in e)Object.defineProperty(i,n,{value:e[n]});return i}return this.props}calculateInstancePickingColors(t,{numInstances:e}){if(t.constant)return;const i=Math.floor(A.length/4);if(this.internalState.usesPickingColorCache=!0,i<e){e>bt&&P.warn("Layer has too many data objects. Picking might not be able to distinguish all objects.")(),A=W.allocate(A,e,{size:4,copy:!0,maxCount:Math.max(e,bt)});const n=Math.floor(A.length/4),r=[0,0,0];for(let o=i;o<n;o++)this.encodePickingColor(o,r),A[o*4+0]=r[0],A[o*4+1]=r[1],A[o*4+2]=r[2],A[o*4+3]=0}t.value=A.subarray(0,e*4)}_setModelAttributes(t,e,i=!1){if(!Object.keys(e).length)return;if(i){const a=this.getAttributeManager();t.setBufferLayout(a.getBufferLayouts(t)),e=a.getAttributes()}const n=t.userData?.excludeAttributes||{},r={},o={};for(const a in e){if(n[a])continue;const c=e[a].getValue();for(const l in c){const u=c[l];u instanceof S?e[a].settings.isIndexed?t.setIndexBuffer(u):r[l]=u:u&&(o[l]=u)}}t.setAttributes(r),t.setConstantAttributes(o)}disablePickingIndex(t){const e=this.props.data;if(!("attributes"in e)){this._disablePickingIndex(t);return}const{pickingColors:i,instancePickingColors:n}=this.getAttributeManager().attributes,r=i||n,o=r&&e.attributes&&e.attributes[r.id];if(o&&o.value){const a=o.value,c=this.encodePickingColor(t);for(let l=0;l<e.length;l++){const u=r.getVertexOffset(l);a[u]===c[0]&&a[u+1]===c[1]&&a[u+2]===c[2]&&this._disablePickingIndex(l)}}else this._disablePickingIndex(t)}_disablePickingIndex(t){const{pickingColors:e,instancePickingColors:i}=this.getAttributeManager().attributes,n=e||i;if(!n)return;const r=n.getVertexOffset(t),o=n.getVertexOffset(t+1);n.buffer.write(new Uint8Array(o-r),r)}restorePickingColors(){const{pickingColors:t,instancePickingColors:e}=this.getAttributeManager().attributes,i=t||e;i&&(this.internalState.usesPickingColorCache&&i.value.buffer!==A.buffer&&(i.value=A.subarray(0,i.value.length)),i.updateSubBuffer({startOffset:0}))}_initialize(){L(!this.internalState),L(Number.isFinite(this.props.coordinateSystem)),_(Fi,this);const t=this._getAttributeManager();t&&t.addInstanced({instancePickingColors:{type:"uint8",size:4,noAlloc:!0,update:this.calculateInstancePickingColors}}),this.internalState=new ki({attributeManager:t,layer:this}),this._clearChangeFlags(),this.state={},Object.defineProperty(this.state,"attributeManager",{get:()=>(P.deprecated("layer.state.attributeManager","layer.getAttributeManager()")(),t)}),this.internalState.uniformTransitions=new si(this.context.timeline),this.internalState.onAsyncPropUpdated=this._onAsyncPropUpdated.bind(this),this.internalState.setAsyncProps(this.props),this.initializeState(this.context);for(const e of this.props.extensions)e.initializeState.call(this,this.context,e);this.setChangeFlags({dataChanged:"init",propsChanged:"init",viewportChanged:!0,extensionsChanged:!0}),this._update()}_transferState(t){_(Mi,this,this===t);const{state:e,internalState:i}=t;this!==t&&(this.internalState=i,this.state=e,this.internalState.setAsyncProps(this.props),this._diffProps(this.props,this.internalState.getOldProps()))}_update(){const t=this.needsUpdate();if(_(Ui,this,t),!t)return;const e=this.props,i=this.context,n=this.internalState,r=i.viewport,o=this._updateUniformTransition();n.propsInTransition=o,i.viewport=n.viewport||r,this.props=o;try{const a=this._getUpdateParams(),c=this.getModels();if(i.device)this.updateState(a);else try{this.updateState(a)}catch{}for(const u of this.props.extensions)u.updateState.call(this,a,u);this.setNeedsRedraw(),this._updateAttributes();const l=this.getModels()[0]!==c[0];this._postUpdate(a,l)}finally{i.viewport=r,this.props=e,this._clearChangeFlags(),n.needsUpdate=!1,n.resetOldProps()}}_finalize(){_(Ni,this),this.finalizeState(this.context);for(const t of this.props.extensions)t.finalizeState.call(this,this.context,t)}_drawLayer({renderPass:t,shaderModuleProps:e=null,uniforms:i={},parameters:n={}}){this._updateAttributeTransition();const r=this.props,o=this.context;this.props=this.internalState.propsInTransition||r;try{e&&this.setShaderModuleProps(e);const{getPolygonOffset:a}=this.props,c=a&&a(i)||[0,0];o.device instanceof rt&&o.device.setParametersWebGL({polygonOffset:c});for(const l of this.getModels())l.device.type==="webgpu"?l.setParameters({...l.parameters,...n}):l.setParameters(n);if(o.device instanceof rt)o.device.withParametersWebGL(n,()=>{const l={renderPass:t,shaderModuleProps:e,uniforms:i,parameters:n,context:o};for(const u of this.props.extensions)u.draw.call(this,l,u);this.draw(l)});else{const l={renderPass:t,shaderModuleProps:e,uniforms:i,parameters:n,context:o};for(const u of this.props.extensions)u.draw.call(this,l,u);this.draw(l)}}finally{this.props=r}}getChangeFlags(){return this.internalState?.changeFlags}setChangeFlags(t){if(!this.internalState)return;const{changeFlags:e}=this.internalState;for(const n in t)if(t[n]){let r=!1;switch(n){case"dataChanged":const o=t[n],a=e[n];o&&Array.isArray(a)&&(e.dataChanged=Array.isArray(o)?a.concat(o):o,r=!0);default:e[n]||(e[n]=t[n],r=!0)}r&&_(Bi,this,n,t)}const i=!!(e.dataChanged||e.updateTriggersChanged||e.propsChanged||e.extensionsChanged);e.propsOrDataChanged=i,e.somethingChanged=i||e.viewportChanged||e.stateChanged}_clearChangeFlags(){this.internalState.changeFlags={dataChanged:!1,propsChanged:!1,updateTriggersChanged:!1,viewportChanged:!1,stateChanged:!1,extensionsChanged:!1,propsOrDataChanged:!1,somethingChanged:!1}}_diffProps(t,e){const i=oi(t,e);if(i.updateTriggersChanged)for(const n in i.updateTriggersChanged)i.updateTriggersChanged[n]&&this.invalidateAttribute(n);if(i.transitionsChanged)for(const n in i.transitionsChanged)this.internalState.uniformTransitions.add(n,e[n],t[n],t.transitions?.[n]);return this.setChangeFlags(i)}validateProps(){ri(this.props)}updateAutoHighlight(t){this.props.autoHighlight&&!Number.isInteger(this.props.highlightedObjectIndex)&&this._updateAutoHighlight(t)}_updateAutoHighlight(t){const e={highlightedObjectColor:t.picked?t.color:null},{highlightColor:i}=this.props;t.picked&&typeof i=="function"&&(e.highlightColor=i(t)),this.setShaderModuleProps({picking:e}),this.setNeedsRedraw()}_getAttributeManager(){const t=this.context;return new Qe(t.device,{id:this.props.id,stats:t.stats,timeline:t.timeline})}_postUpdate(t,e){const{props:i,oldProps:n}=t,r=this.state.model;r?.isInstanced&&r.setInstanceCount(this.getNumInstances());const{autoHighlight:o,highlightedObjectIndex:a,highlightColor:c}=i;if(e||n.autoHighlight!==o||n.highlightedObjectIndex!==a||n.highlightColor!==c){const l={};Array.isArray(c)&&(l.highlightColor=c),(e||n.autoHighlight!==o||a!==n.highlightedObjectIndex)&&(l.highlightedObjectColor=Number.isFinite(a)&&a>=0?this.encodePickingColor(a):null),this.setShaderModuleProps({picking:l})}}_getUpdateParams(){return{props:this.props,oldProps:this.internalState.getOldProps(),context:this.context,changeFlags:this.internalState.changeFlags}}_getNeedsRedraw(t){if(!this.internalState)return!1;let e=!1;e=e||this.internalState.needsRedraw&&this.id;const i=this.getAttributeManager(),n=i?i.getNeedsRedraw(t):!1;if(e=e||n,e)for(const r of this.props.extensions)r.onNeedsRedraw.call(this,r);return this.internalState.needsRedraw=this.internalState.needsRedraw&&!t.clearRedrawFlags,e}_onAsyncPropUpdated(){this._diffProps(this.props,this.internalState.getOldProps()),this.setNeedsUpdate()}}kt.defaultProps=Di;kt.layerName="Layer";export{Ct as A,O as B,V as C,Ki as G,kt as L,ge as P,he as a,de as b,Le as c,Zi as d,ve as e,Qe as f,we as g,pe as h,di as i,Rt as j,Oi as k,M as l,Qt as m,Xi as p};
//# sourceMappingURL=layer-DPcO4AXQ.js.map
