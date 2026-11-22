---
name: api-types
description: 'MuJoCo C API types: primitive types, enums (mjtObj, mjtGeom, mjtJoint, mjtSolver, mjtCone, mjtDisableBit, mjtState, ...), structs (mjModel, mjData, mjOption, mjContact, mjSpec elements such as mjsBody, mjsGeom, mjsJoint, visualization and rendering structs) and function types. Use when the exact field name, array shape or enum value of a MuJoCo struct is needed, in C or through the Python bindings.'
---

# MuJoCo API Types

A scannable index of MuJoCo's C types: the primitive types, every `mjt*` enum and where it is used, the struct families (`mjModel`, `mjData`, `mjOption`, `mjv*`, `mjr*`, `mjrf*`, `mjui*`, `mjs*`, `mjp*`, batch) and the callback function types. Use it to find which enum a field holds, which struct a field lives in, and the exact callback signatures.

> **Where the values are:** the source page builds enum members and struct field lists from the headers, and this copy does not include them. For exact members and field declarations (with array shapes in comments), read the headers: [mjtype.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjtype.h) (model/data enums, primitive types), [mjvisualize.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjvisualize.h), [mjrender.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjrender.h), [mjrfilament.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjrfilament.h), [mjui.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjui.h), [mjspec.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjspec.h), [mjplugin.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjplugin.h), [mjdata.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjdata.h), [mjbatch.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjbatch.h). For Python naming of these types, see [python-bindings](../../python-bindings/SKILL.md).

## Conventions

- Enum types start with `mjt`. API functions take them as `int`, because C does not fix the size of an enum. The docs still recommend the enum types for readability.
- Bitmask or bitflag enums: `mjtDisableBit` and `mjtEnableBit` (powers of 2), `mjtCatBit`, `mjtPertBit`, `mjtCamOutBit`, `mjtCtrlInput`, `mjtState`, `mjtPassthrough`.
- Counts: `mjNDISABLE` is the length of [mjDISABLESTRING](../api-globals/SKILL.md), `mjNENABLE` of `mjENABLESTRING`, `mjNWARNING` of `mjData.warning`, `mjNTIMER` of `mjData.timer` and `mjTIMERSTRING`, `mjNTOPIC` of `mjTOPICSTRING`, and `mjNSOLVER` is the maximum length of `mjData.solver`.
- Do not edit the distributed headers. Changing `mjUSESINGLE` causes link errors.

## Primitive types

```C
// floating point data type and minval
#ifndef mjUSESINGLE
  typedef double mjtNum;
  #define mjMINVAL    1E-15       // minimum value in any denominator
#else
  typedef float mjtNum;
  #define mjMINVAL    1E-15f
#endif

typedef unsigned char mjtByte;   // small integers, binary data

#ifndef __cplusplus
  typedef _Bool mjtBool;
#else
  typedef bool mjtBool;
#endif

typedef int64_t mjtSize;         // buffer sizes
```

Only double-precision MuJoCo is distributed, so code that assumes `double` is safe. Use the math utilities to stay precision-agnostic.

## Enums: model (mjtype.h)

| Enum | Used in / meaning |
|---|---|
| `mjtDisableBit` | `m->opt.disableflags` bitmask |
| `mjtEnableBit` | `m->opt.enableflags` bitmask |
| `mjtJoint` | `m->jnt_type`. Ball joints and the rotation of free joints are unit quaternions (4 coordinates, 3 DoF). |
| `mjtGeom` | `m->geom_type`, `m->site_type`. The first group can be used in models. The second group is decorative, for the visualizer only. |
| `mjtProjection` | `m->cam_projection` |
| `mjtCamLight` | `m->cam_mode`, `m->light_mode` (how pose is computed) |
| `mjtLightType` | `m->light_type` |
| `mjtTexture` | `m->tex_type` (mapping) |
| `mjtTextureRole` | index into `m->mat_texid`. The built-in renderer uses only RGB. |
| `mjtColorSpace` | texture color space encoding |
| `mjtIntegrator` | `m->opt.integrator` |
| `mjtCone` | `m->opt.cone` |
| `mjtJacobian` | `m->opt.jacobian` |
| `mjtSolver` | `m->opt.solver` |
| `mjtEq` | `m->eq_type` |
| `mjtTendon` | `m->tendon_type` |
| `mjtWrap` | `m->wrap_type` |
| `mjtTrn` | `m->actuator_trntype` |
| `mjtDyn` | `m->actuator_dyntype` |
| `mjtGain` | `m->actuator_gaintype` |
| `mjtBias` | `m->actuator_biastype` |
| `mjtCtrlChart` | `m->actuator_ctrlspec` (so3 orientation input charts) |
| `mjtCtrlInput` | `m->actuator_ctrlspec` (input bitflags for pid/dcmotor and fixed/affine gain) |
| `mjtObj` | object types for `mj_name2id` / `mj_id2name` |
| `mjtSensor` | `m->sensor_type` |
| `mjtStage` | skipstage of `mj_forwardSkip` / `mj_inverseSkip` |
| `mjtDataType` | `mjData.sensor_datatype` |
| `mjtConDataField` | data fields of contact sensors |
| `mjtRayDataField` | data fields of rangefinder sensors |
| `mjtCamOutBit` | `m->cam_output` bitflags |
| `mjtSameFrame` | frame alignment shortcut, last argument of `mj_local2global` in `mj_kinematics` |
| `mjtSleepPolicy` | per-tree sleep policy. The compiler picks `NEVER` or `ALLOWED`. Only the user can set `INIT` (start asleep). |
| `mjtLRMode` | `mjLROpt.mode` |
| `mjtFlexSelf` | flex self-collision midphase |
| `mjtSDFType` | SDF combination formula for `mjc_distance` / `mjc_gradient` |

## Enums: data (mjtype.h)

| Enum | Used in / meaning |
|---|---|
| `mjtState` | state bitflags and combinations for `mj_getState`, `mj_setState`, `mj_stateSize` |
| `mjtConstraint` | `d->efc_type` (not used in mjModel) |
| `mjtConstraintState` | internal solver constraint states |
| `mjtWarning` | indexes `mjData.warning` (`mjNWARNING`) |
| `mjtTimer` | indexes `mjData.timer` (`mjNTIMER`) |
| `mjtSleepState` | sleep state of an object |
| `mjtLogLevel` | log message severity |
| `mjtLogTopic` | topics for `mju_info`. Topic 0 `mjTOPIC_NONE` always passes. Topic `t` needs bit `(1 << (t - 1))` in `mjLogConfig.topics`. |

## Enums: visualization, rendering, UI, spec, plugins

| Enum | Header | Used in / meaning |
|---|---|---|
| `mjtCatBit` | mjvisualize.h | geom categories rendered by `mjr_render` |
| `mjtMouse` | mjvisualize.h | mouse actions. You translate events yourself, as in [simulate.cc](../../c-programming/SKILL.md). |
| `mjtPertBit` | mjvisualize.h | `mjvPerturb.active`. A regular mouse sets one at a time; a 3D mouse can set both. |
| `mjtCamera` | mjvisualize.h | `mjvCamera.type` |
| `mjtLabel` | mjvisualize.h | `mjvOption.label` (`mjLABELSTRING`) |
| `mjtFrame` | mjvisualize.h | `mjvOption.frame` (`mjFRAMESTRING`) |
| `mjtVisFlag` | mjvisualize.h | indexes `mjvOption.flags` (`mjVISSTRING`) |
| `mjtRndFlag` | mjvisualize.h | indexes `mjvScene.flags` (`mjRNDSTRING`) |
| `mjtStereo` | mjvisualize.h | `mjvScene.stereo` |
| `mjtGridPos` | mjrender.h | `mjr_overlay` position |
| `mjtFramebuffer` | mjrender.h | `mjr_setBuffer` |
| `mjtDepthMap` | mjrender.h | `mjrContext.readPixelDepth` (depth mapping of `mjr_readPixels`) |
| `mjtFontScale`, `mjtFont` | mjrender.h | font size (three built-in bitmap sizes) and type |
| `mjrPixelFormat`, `mjrVertexAttributeUsage`, `mjrVertexAttributeType`, `mjrIndexType`, `mjrMeshPrimitiveType` | mjrender.h | values listed only in the header |
| `mjrGraphicsApi`, `mjrDrawMode`, `mjrQuality`, `mjrToneMapper`, `mjrShadowType`, `mjrAmbientOcclusionType`, `mjrDitheringType` | mjrfilament.h | Filament graphics API, draw mode, quality, tone mapper, shadow, AO, dithering |
| `mjtButton`, `mjtEvent`, `mjtItem`, `mjtSection` | mjui.h | UI mouse buttons, events, item types, section state |
| `mjtGeomInertia` | mjspec.h | inertia inference type |
| `mjtBuiltin`, `mjtMark` | mjspec.h | procedural texture type and mark |
| `mjtLimited` | mjspec.h | limit specification |
| `mjtAlignFree` | mjspec.h | align free joints with the inertial frame |
| `mjtPassthrough` | mjspec.h | bitmask of assets left [by reference](../../mjcf-modeling/SKILL.md) (see [compiler/passthrough](../xml-reference/SKILL.md)) |
| `mjtEmbed` | mjspec.h | asset payload in the model or by reference (see [texture/embed](../xml-reference/SKILL.md)) |
| `mjtInertiaFromGeom` | mjspec.h | infer body inertia from child geoms |
| `mjtOrientation` | mjspec.h | orientation specifier type |
| `mjtMeshInertia`, `mjtMeshBuiltin` | mjspec.h | mesh inertia computation, built-in procedural mesh |
| `mjtFlexSection` | mjspec.h | cross-section of 1D flex elasticity |
| `mjtConflict` | mjspec.h | conflict resolution for attach |
| `mjtScaling` | mjspec.h | physical policy of a frame's scale |
| `mjtActuator` | mjspec.h | element an actuator is written with: `general` or a shortcut. Set by `mjs_setTo*` and the parser. Shortcut parameters inherit only from a default written with the same shortcut. |
| `mjtCTimer` | mjspec.h | compiler timers for `mjs_getTimer`. `TOTAL` and `ASSETS` are wall-clock. Asset sub-timers sum CPU time and can exceed `ASSETS`. |
| `mjtPluginCapabilityBit` | mjplugin.h | capabilities an [engine plugin](../../c-programming/engine-plugins/SKILL.md) declares |

## Structs

| Struct | Role |
|---|---|
| `mjModel` | The model. The simulator treats it as constant. Embeds `mjOption`, `mjVisual`, `mjStatistic`. |
| `mjOption` | Simulation options, the MJCF [option](../xml-reference/SKILL.md) element (`m->opt`). |
| `mjData` | Simulation state and workspace. All functions read modifiable inputs from it and write outputs to it. Embeds `mjContact` and the stats structs. |
| `mjVisual` / `mjStatistic` | MJCF `visual` / `statistic` (compiler-computed or user-set). |
| `mjPreContact` | One contact as filled in by a narrowphase collider. |
| `mjContact` | One contact. `mjData.contact` is a preallocated array that the collision detector and simulator fill. |
| `mjResource` | Abstract file. `name` is unique. A [resource provider](../../c-programming/engine-plugins/SKILL.md) fills the other fields. |
| `mjVFS` | Virtual file system. Programmatic only, no MJCF analog. |
| `mjLROpt` | Options for automatic actuator length-range computation. |
| `mjCache` | Compiler asset cache that avoids slow recompiles. |
| `mjLogMessage` | Passed to `mjfLogHandler`: level, optional topic, one-line subject, optional body, optional source location. |
| `mjLogConfig` | Default log handler config: console and/or file (`logto_file`, `logfile`, default `MUJOCO_LOG.TXT`), `topics` bitmask. |
| `mjWarningStat` / `mjTimerStat` | One entry of `mjData.warning` / `mjData.timer`. |
| `mjSolverStat` | One solver iteration in `mjData.solver` (up to `mjNSOLVER`). The actual count is `mjData.solver_niter`. |
| `mjvPerturb`, `mjvCamera`, `mjvGLCamera`, `mjvGeom`, `mjvLight`, `mjvOption`, `mjvScene`, `mjvFigure` | Abstract visualization: mouse perturbation, abstract and OpenGL cameras, geoms (model or decor), lights, visibility options, the full 3D scene, and 2D plots (fill buffers, then call `mjr_figure`). |
| `mjrRect`, `mjrVertexAttribute`, `mjrRendererInfo`, `mjrContext` | Classic renderer: rectangle, vertex attributes, renderer info, OpenGL context with the GPU resource ids. |
| `mjrf*` | Filament renderer (see below). |
| `mjuiState`, `mjuiThemeSpacing`, `mjuiThemeColor`, `mjuiItem`, `mjuiSection`, `mjuiDef`, `mjUI` | [UI framework](../../c-programming/visualization-rendering/SKILL.md). One `mjuiState` per app. `mjUI` is a whole UI with statically allocated sections and items. `mjuiDef` is a table entry for simplified construction. |
| `mjSpec`, `mjs*` | [Model editing](../../model-editing/SKILL.md) (see below). |
| `mjpPlugin` | Engine plugin definition, mostly callbacks. |
| `mjSDF` | Used by the SDF API for distances and gradients between SDF geoms. |
| `mjpResourceProvider` | Callbacks to open and read resources. |
| `mjpDecoder` / `mjpEncoder` | Callbacks to decode an `mjResource` into an `mjSpec` / encode an `mjSpec` and `mjModel` into an `mjResource`. |
| `mjBatch` | Opaque handle to `nsim` simulations of one model plus a thread pool. Create it with `mjb_makeBatch`, free it with `mjb_deleteBatch`. See [batched simulation](../../c-programming/simulation-loop/SKILL.md). |
| `mjBatchConfig` | Parameters of `mjb_makeBatch`. `mjb_defaultConfig` sets the defaults. |
| `mjBatchRecord` | Field or state recorded by `mjb_rollout` after each substep. `buf` holds `n x nstep x size` values, in call order. For a state, `size = mj_stateSize(m, spec)` and the values are `mjtNum`. |

### Model editing structs (mjspec.h)

`mjSpec` (the spec), then `mjs`-prefixed elements: `mjsElement`, `mjsCompiler`, `mjsAuthored` (authored-tracking bitmasks for mjModel structs), `mjsBody`, `mjsFrame`, `mjsJoint`, `mjsGeom`, `mjsSite`, `mjsCamera`, `mjsLight`, `mjsFlex`, `mjsMesh`, `mjsHField`, `mjsSkin`, `mjsTexture`, `mjsMaterial`, `mjsPair`, `mjsExclude`, `mjsEquality`, `mjsTendon`, `mjsWrap`, `mjsActuator`, `mjsSensor`, `mjsNumeric`, `mjsText`, `mjsTuple`, `mjsKey`, `mjsDefault`, `mjsPlugin`, `mjsOrientation`.

- `mjsElement` is the first member of every element (in C++ it is inherited, which allows `static_cast`). **Never modify it.** That is undefined behaviour. All other attributes are user-settable.
- `mjsFlex.elastic3d` (experimental, mjSpec only, no MJCF attribute) picks the material for non-interpolated 3D flexes. `0` (default) is StVK. `1` is simplified Stable Neo-Hookean, which needs the [discrete integrator](../xml-reference/SKILL.md). Other values are rejected. Specs with SNH cannot be saved to MJCF; the compiled model can be saved to MJB.

Array handles. From C, use the getters and setters:

```C++
#ifdef __cplusplus
  // C++: defined to be compatible with corresponding std types
  using mjString      = std::string;
  using mjStringVec   = std::vector<std::string>;
  using mjIntVec      = std::vector<int>;
  using mjIntVecVec   = std::vector<std::vector<int>>;
  using mjFloatVec    = std::vector<float>;
  using mjFloatVecVec = std::vector<std::vector<float>>;
  using mjDoubleVec   = std::vector<double>;
  using mjByteVec     = std::vector<std::byte>;
#else
  // C: opaque types
  typedef void mjString;
  typedef void mjStringVec;
  typedef void mjIntVec;
  typedef void mjIntVecVec;
  typedef void mjFloatVec;
  typedef void mjFloatVecVec;
  typedef void mjDoubleVec;
  typedef void mjByteVec;
#endif
```

### Filament renderer structs (mjrfilament.h)

There are seven object types: `mjrfContext`, `mjrfTexture`, `mjrfMesh`, `mjrfLight`, `mjrfRenderable`, `mjrfScene`, `mjrfRenderTarget`. Create each with `mjrf_create*` and free it with `mjrf_destroy*` (for example `mjrf_createTexture` / `mjrf_destroyTexture`). Every object except the context needs a context. The create functions take a config struct that you initialize with its default function (for example `mjrf_defaultTextureConfig`). Unspecified defaults are `0`/`NULL`.

- `mjrfContext`: the entry point. Render with `mjrf_render()`. It is **not thread-safe**, so call it from one thread. It manages its own graphics context (no EGL setup) and is independent of any model, so one context can render several models.
- Configs and data: `mjrfContextConfig`, `mjrfTextureConfig`, `mjrfTextureData`, `mjrfMeshConfig`, `mjrfMeshData`, `mjrfSceneParams`, `mjrfLightParams`, `mjrfRenderableParams`, `mjrfMaterial`, `mjrfRenderTargetConfig`, `mjrfRenderRequest`, `mjrfReadRequest`, `mjrfFrameStats`.
- Meshes: normals are encoded as a tangent-frame quaternion and computed on the fly if missing, at a cost. Provide bounds, or frustum culling is skipped.
- Lights: one image light and one directional light at most. Any number of point and spot lights. Each shadow-casting light costs performance. Generate image-light KTX files with `cmgen`.
- Materials: metallic-roughness (PBR), specular-glossiness (legacy, close to the classic renderer) and unlit.
- Options: `mjrfAmbientOcclusionOpts`, `mjrfAntialiasingOpts`, `mjrfBloomOpts`, `mjrfColorGradingOpts`, `mjrfDepthOfFieldOpts`, `mjrfDitheringOpts`, `mjrfFogOpts`, `mjrfHazeOpts`, `mjrfHeadlightOpts`, `mjrfMaterialOpts`, `mjrfReflectionOpts` (reflective planes only), `mjrfShadowOpts`, `mjrfSkyboxOpts`, `mjrfVignetteOpts`, all combined in `mjrfRenderOpts`.

## Function types

Physics callbacks (installed via the globals in [api-globals](../api-globals/SKILL.md)):

```C
typedef void (*mjfGeneric)(const mjModel* m, mjData* d);                     // mjcb_passive, mjcb_control
typedef int (*mjfConFilt)(const mjModel* m, mjData* d, int geom1, int geom2); // mjcb_contactfilter: 1 discard, 0 proceed
typedef void (*mjfSensor)(const mjModel* m, mjData* d, int stage);           // mjcb_sensor
typedef mjtNum (*mjfTime)(void);                                             // mjcb_time
typedef mjtNum (*mjfAct)(const mjModel* m, const mjData* d, int id);         // mjcb_act_dyn, mjcb_act_gain, mjcb_act_bias
typedef int (*mjfCollision)(const mjModel* m, const mjData* d,
                            mjPreContact* con, int g1, int g2, mjtNum margin); // mjCOLLISIONFUNC table
```

Logging and UI:

```C
typedef void (*mjfLogHandler)(const mjLogMessage*);       // via mju_setLogHandler; must be thread-safe; never call mju_error inside
typedef int (*mjfItemEnable)(int category, void* data);   // UI item enabled predicate
```

Resource providers, decoders and encoders:

```C
typedef int (*mjfOpenResource)(mjResource* resource);                       // 0 on failure; then close is NOT called, so clean up here
typedef int (*mjfReadResource)(mjResource* resource, const void** buffer);  // bytes in buffer, -1 on error
typedef void (*mjfCloseResource)(mjResource* resource);                     // free allocated memory
typedef void (*mjfGetResourceDir)(mjResource* resource, const char** dir, int* ndir);
typedef int (*mjfResourceModified)(const mjResource* resource);             // >0 modified, 0 not, <0 inconclusive
typedef mjSpec* (*mjfDecode)(mjResource* resource, const mjVFS* vfs, char* error, int error_sz); // NULL on failure, write error if non-NULL
typedef int (*mjfCanDecode)(const mjResource* resource);                    // true if decodable
typedef mjtSize (*mjfEncode)(const mjSpec* s, const mjModel* m, const mjVFS* vfs,
                             mjResource* resource);                         // fills resource data
```

For `mjfDecode`, the caller owns both the resource and the returned spec.

Batch:

```C
typedef void (*mjfBatchFunc)(const mjModel* m, mjData* d, int sim, void* arg); // run by mjb_apply on a batch thread
```

The model passed to `mjfBatchFunc` has that simulation's per-simulation fields applied, and `d` holds its state.

## Notes

### c-frame variables (`cdof`, `cinert`)

`mjData.cdof` and `mjData.cinert` are computed by `mj_comPos`. They are expressed in the c-frame: at the subtree center of mass (`mjData.subtree_com`), oriented like the world frame, for precision far from the origin.

- `cdof`: 6D motion vectors (3 rotation, 3 translation) for each DoF axis, used by all Jacobian functions. Analytic Jacobians need at least `mj_kinematics` then `mj_comPos`.
- `cinert`: 10-vectors used by `mj_crb`. `[0-5]` is the upper triangle of the inertia matrix, `[6-8]` is mass times the CoM offset from the c-frame origin, and `[9]` is mass.

### Convex hulls

```C
int*      mesh_graphadr;     // graph data address; -1: no graph      (nmesh x 1)
int*      mesh_graph;        // convex graph data                     (nmeshgraph x 1)
```

Mesh `N`'s hull record starts at `m->mesh_graph + m->mesh_graphadr[N]`:

```C
int numvert;
int numface;
int vert_edgeadr[numvert];
int vert_globalid[numvert];
int edge_localid[numvert+3*numface];
int face_globalid[3*numface];
```

- `globalid` indexes the full mesh and `localid` indexes the hull.
- `vert_edgeadr` gives each hull vertex's offset into `edge_localid`. `vert_globalid` maps hull vertices to mesh vertices.
- `edge_localid` holds one record per vertex: neighbour localids terminated by `-1`. Every edge appears twice, so the length is `numvert+3*numface`.
- `face_globalid` holds the three full-mesh vertex indices of each hull face.

## Source docs

Verbatim copies, for details not covered above:

- [APIreference/APItypes.md](references/APIreference-APItypes.md)
