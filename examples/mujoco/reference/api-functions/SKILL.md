---
name: api-functions
description: 'MuJoCo C API functions by group: parse and compile, main simulation (mj_step, mj_forward), support (mj_jac, mj_contactForce, mj_name2id), components, ray casting, printing, virtual file system, initialization, visualization, OpenGL/Filament rendering, UI, derivatives, plugins, threads, batched simulation, math and quaternion utilities, and the mjSpec editing functions (mjs_addBody, mjs_attach, attribute setters/getters, find utilities). Use when looking up the signature or semantics of a mj_*, mjv_*, mjr_*, mju_*, mjd_* or mjs_* function.'
---

# MuJoCo API Functions

Find the right `mj_*`, `mjv_*`, `mjr_*`, `mjrf_*`, `mjui_*`, `mjd_*`, `mjp_*`,
`mjb_*`, `mju_*` or `mjs_*` function and its semantics, grouped as in the
MuJoCo API reference. The other references are summarized in
[reference](../SKILL.md).

> **Signatures:** this copy of the docs lists each function by name and
> description, but the C prototypes are not rendered. Get exact argument
> types and order from
> [mujoco.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mujoco.h)
> (batched functions: `mujoco/mjbatch.h`). Argument names below (`vfs`,
> `error`, `jacp`, ...) are those the docs mention. "Nullable" lists the
> arguments that may be `NULL`.

## Conventions

- Most users need a small fraction of these functions; for simulation,
  most only call `mj_step`.
- If `error` is not NULL, it must have size `error_sz`.
- If `vfs` is not NULL, files are looked up in the VFS before the disk.
- Derivative functions put outputs in the **trailing** arguments, unlike most
  of the API.
- `mju_error` is always fatal; see Error and memory below.
- Structs and enums named here (`mjtState`, `mjtObj`, `mjtStage`, `mjtMouse`,
  ...) are in [api-types](../api-types/SKILL.md). Callbacks such as
  `mjcb_control` are in [api-globals](../api-globals/SKILL.md).

## Parse and compile

`mj_loadXML` runs the parser and compiler, returns a valid `mjModel*` or NULL
(then read the error string). For the spec-based workflow see
[model-editing](../../model-editing/SKILL.md).

| Function | Semantics |
|----|----|
| `mj_loadXML` | Parse MJCF or URDF file, compile, return model. Nullable: `vfs`, `error`. |
| `mj_parseXML` / `mj_parseXMLString` / `mj_parse` | Parse spec from XML file / XML string / a file. Nullable: `vfs`, `error`. |
| `mj_compile` | Compile `mjSpec` to a new `mjModel`; NULL on failure, read error with `mjs_getError`. Completes keyframes (sized for the model, added up to `nkey`); `discardvisual`/`fusestatic` compiler attributes apply `mjs_discardVisual`/`mjs_fuseStatic` to the spec first, invalidating pointers to removed elements. |
| `mj_recompile` | Recompile spec into existing `mjModel`/`mjData` in place, preserving integration state across added/removed DoFs. Returns 0 on success; on failure model and data are deleted. |
| `mj_copyBack` | Copy values changed in a compiled `mjModel` back to its `mjSpec`. Returns 1 on success, 0 if the model no longer matches the spec structure or a change cannot be expressed (nothing copied; see `mjs_getError`). |
| `mj_encode` | Encode `mjSpec` or `mjModel` to a file; format from extension or `content_type` (`.xml`, `.mjb`, `.txt`, `.mjz`). Returns bytes written or -1. Nullable: `s`, `m`, `vfs`, `error`. |
| `mj_saveXML` | Save spec to XML file; 0 on success, -1 otherwise. `savecompiled`/`savecanonical` choose compiled vs written values; compiled values need a (re)compile after structural edits. |
| `mj_saveXMLString` | Save spec to XML string; 0 / -1; returns required size if buffer too small. |
| `mj_saveLastXML` / `mj_freeLastXML` | Save / free the last model loaded with legacy `mj_loadXML`. |
| `mj_loadTexture` | Decode texture id to raw bytes (as in `tex_data`); buffer from `mju_malloc`, caller frees. 0 on success. Nullable: `width`, `height`, `colorspace`, `error`. |
| `mj_embedAssets` | Copy of `m` with all by-reference assets loaded; NULL with error if a file does not resolve. Nullable: `error`. |
| `mju_getXMLDependencies` | Recursively list asset files an MJCF file depends on (including itself). |

`mj_copyBack` details: copies `opt`, `vis`, `stat`, real-valued parameters of
bodies, joints, geoms, sites, cameras, lights, materials, pairs, equalities,
tendons, actuators, sensors, custom numeric/tuple data, keyframes and height
field elevation. Changed orientations are written as quaternions; angles in the
spec's `unit`. Changed mass/inertia gives the body an explicit `inertial`.
Errors include mass/inertia changes under `inertiafromgeom="true"` or
`settotalmass`, world body pose, free-joint anchor/axis, ball-joint axis, and
mesh/height-field geom sizes. The full list is in the verbatim source.

Hermetic MJB: `mj_embedAssets`, then `mj_saveModel`, then `mj_deleteModel`.

## Main simulation

| Function | Semantics |
|----|----|
| `mj_step` | Advance simulation; uses control callback for controls and forces. |
| `mj_step1` / `mj_step2` | Split step: before / after the user sets controls and forces. RK4 does not work with them. |
| `mj_forward` | Same as `mj_step` without integration. Use after load/reset and for sampling or finite differences. |
| `mj_inverse` | Inverse dynamics into `mjData.qfrc_inverse`; set `mjData.qacc` first. |
| `mj_forwardSkip` / `mj_inverseSkip` | Same with `skipstage` (`mjtStage`); `mjSTAGE_POS` skips position computations when only `qvel` changed. |

Set controls in `mjData.{ctrl, qfrc_applied, xfrc_applied}` before stepping, or
install `mjcb_control`. Check forward/inverse consistency with
`mj_compareFwdInv`. See
[simulation-loop](../../c-programming/simulation-loop/SKILL.md).

## Support (need mjModel and mjData)

| Function | Semantics |
|----|----|
| `mj_stateSize` | Number of `mjtNum`s for state signature `sig` (bits of `mjtState`). |
| `mj_getState` / `mj_setState` | Copy state components in `sig` from `d` into `state` / from `state` into `d`. `mju_error` if `sig` invalid. |
| `mj_extractState` | Extract `dstsig` components from a state with `srcsig`; `dstsig` must be a subset. |
| `mj_copyState` | Copy state from src to dst. |
| `mj_readCtrl` / `mj_readSensor` | Read control / sensor at `time`, accounting for delays. Without history (`nsample` = 0) returns pointer into `ctrl` / `sensordata`; with `interp` 1 or 2 returns NULL and writes `result`. `interp`: 0 hold, 1 linear, 2 Catmull-Rom, -1 use element's `interp`. |
| `mj_initCtrlHistory` / `mj_initSensorHistory` | Fill an actuator / sensor history buffer; `times` NULL keeps timestamps. Sensor version has `phase`. |
| `mj_setKeyframe` | Copy current state to keyframe k. |
| `mj_addContact` | Add contact to `d->contact`; 0 success, 1 buffer full. |
| `mj_isPyramidal` / `mj_isSparse` / `mj_isDual` | Friction cone type / constraint Jacobian type / solver type (PGS dual; CG, Newton primal). |
| `mj_mulJacVec` / `mj_mulJacTVec` | Multiply `efc_J` (dense or sparse) / its transpose by a vector. |
| `mj_jac` | Jacobian of world `point` attached to `body`: `jacp`, `jacr`, each 3 x nv, frame at body CoM aligned with world. Needs `mj_kinematics` then `mj_comPos`. Nullable: `jacp`, `jacr`. |
| `mj_jacBody` / `mj_jacBodyCom` / `mj_jacSubtreeCom` / `mj_jacGeom` / `mj_jacSite` | Jacobian at body center / body CoM / subtree CoM / geom / site. The body, geom and site variants are shortcuts for `mj_jac`. |
| `mj_jacPointAxis` | Translation Jacobian of point and rotation Jacobian of axis. Nullable: `jacPoint`, `jacAxis`. |
| `mj_jacDot` | Time-derivative of `mj_jac`; needs `mj_kinematics`, `mj_comPos`, `mj_comVel`. |
| `mj_angmomMat` | 3 x nv matrix H with subtree angular momentum h = H qvel. |
| `mj_name2id` / `mj_id2name` | Object id from `mjtObj` type and name (-1 if not found) / name from id (NULL). |
| `mj_actuatorInputName` | Name of actuator input; NULL if the type defines none. |
| `mj_fullM` / `mj_mulM` / `mj_mulM2` / `mj_addM` | Sparse inertia to dense / multiply `mjData.M` by vector / by M^(1/2) / add M to a matrix (lower triangle; dense when int* are NULL). |
| `mj_applyFT` | Apply Cartesian force and torque at a point on a body, added to a `qfrc_applied`-style vector you pass. |
| `mj_objectVelocity` / `mj_objectAcceleration` | 6D (rot:lin) velocity / acceleration in object-centered frame. Acceleration needs `mj_rnePostConstraint` if no acc/force sensors. |
| `mj_geomDistance` | Smallest signed distance between two geoms, bounded by `distmax`; optional `fromto` segment (zeros if none found). Inaccurate under legacy CCD. |
| `mj_insideSite` | 1 if point is inside a site (convex hull for meshes). |
| `mj_contactForce` | 6D force:torque of a contact id, in the contact frame. |
| `mj_differentiatePos` / `mj_integratePos` | qpos difference / qvel added to qpos (scaled by dt), quaternion-aware. |
| `mj_normalizeQuat` | Normalize all quaternions in a qpos-type vector. |
| `mj_local2Global` | Body-local to global coordinates; `sameframe` from `mjtSameFrame`. |
| `mj_getTotalmass` / `mj_setTotalmass` | Sum body masses / scale masses and inertias to a total. |
| `mj_getPluginConfig` | Config attribute of a plugin instance; NULL if invalid. |
| `mj_loadPluginLibrary` / `mj_loadAllPluginLibraries` | Load one plugin library / all in a directory (failures skipped with warning). |
| `mj_version` / `mj_versionString` | Version number (1.0.2 is 102) / version string. |

## Components and sub components

Called internally by `mj_step`, `mj_forward`, `mj_inverse`; rarely needed.

| Function | Semantics |
|----|----|
| `mj_fwdKinematics` | kinematics, comPos, camlight, flex, tendon. |
| `mj_fwdPosition` / `mj_fwdVelocity` | Position- / velocity-dependent computations. |
| `mj_fwdActuation` / `mj_fwdAcceleration` / `mj_fwdConstraint` | `qfrc_actuator` / sum non-constraint forces into `qacc_smooth` / run constraint solver. |
| `mj_Euler` / `mj_RungeKutta` / `mj_implicit` | Semi-implicit Euler / explicit RK order N / implicit or implicitfast integration (advances time). |
| `mj_invPosition` / `mj_invVelocity` / `mj_invConstraint` | Inverse dynamics stages. |
| `mj_compareFwdInv` | Compare forward and inverse dynamics, results in `fwdinv`. |
| `mj_sensorPos` / `mj_sensorVel` / `mj_sensorAcc` | Evaluate sensors per stage. |
| `mj_energyPos` / `mj_energyVel` | Potential / kinetic energy. |
| `mj_checkPos` / `mj_checkVel` / `mj_checkAcc` | Reset if any element of qpos / qvel / qacc is too big or nan. |
| `mj_kinematics` / `mj_comPos` / `mj_comVel` | Forward kinematics / CoM-frame inertias and dofs / `cvel`, `cdof_dot`. |
| `mj_camlight` / `mj_flex` / `mj_tendon` / `mj_transmission` | Cameras and lights / flex / tendon lengths, velocities, moments / actuator transmission. |
| `mj_crb` / `mj_makeM` | CRB inertia / full inertia incl. tendon armature, in `qM` and `M` (CSR). |
| `mj_factorM` / `mj_solveM` / `mj_solveM2` | L^T D L factorization / solve M x = y / half solve. |
| `mj_passive` | `qfrc_passive` from spring-dampers, gravity compensation, fluid forces. |
| `mj_subtreeVel` | `subtree_linvel`, `subtree_angmom`. |
| `mj_rne` | M(q) qacc + C(q, qvel); `flg_acc=0` drops the inertial term. |
| `mj_rnePostConstraint` | `cacc`, `cfrc_int`, `cfrc_ext` (nv x 6, [rotation, translation]). Auto-run with accelerometer, force, torque, framelinacc, frameangacc sensors. |
| `mj_maxContact` | Max contacts between two geoms; `has_margin` -1 reads margin from model. |
| `mj_collision` / `mj_makeConstraint` / `mj_island` | Collision detection / build constraints / find islands. |
| `mj_projectConstraint` / `mj_referenceConstraint` / `mj_constraintUpdate` | `efc_AR` / `efc_vel`, `efc_aref` / `efc_state`, `efc_force`, `qfrc_constraint` (optional `cost`). |

## Ray casting

Call after `mj_kinematics` (or a function that calls it). All return distance
to the nearest surface, or -1 if none; a ray starting inside a geom still hits.

| Function | Semantics |
|----|----|
| `mj_ray` | Ray `pnt+x*vec` vs all geoms. Writes `geomid` and outward `normal` if given. `bodyexclude` (-1 none), `geomgroup` (length `mjNGROUP`, NULL to skip), `flg_static` 0 excludes static geoms. Nullable: `geomgroup`, `geomid`, `normal`. |
| `mj_multiRay` | Many rays from one point; `vec`, `normal`, `dist` are arrays; geoms beyond `cutoff` ignored. |
| `mj_rayHfield` / `mj_rayMesh` / `mju_rayGeom` | Ray vs height field / mesh / pure geom. Nullable: `normal`. |
| `mj_rayFlex` / `mju_raySkin` | Ray vs flex / skin, also nearest `vertid`. |

## Printing

`mj_printModel`, `mj_printData`, `mj_printScene` print to a text file;
`mj_printFormattedModel`, `mj_printFormattedData`, `mj_printFormattedScene`
take `float_format`, a printf format for one float. `mju_printMat` and
`mju_printMatSparse` print to screen. `mj_printSchema` prints the XML schema as
text or HTML.

## Virtual file system, asset cache, resources

Allocate with `mj_defaultVFS`, free with `mj_deleteVFS`. Pass the VFS to
`mj_loadXML` or `mj_loadModel`; it is checked before the disk.

| Function | Semantics |
|----|----|
| `mj_addFileVFS` | Add file (`directory` may be NULL); 0, 2 name collision, -1 error. |
| `mj_addBufferVFS` | Add file from buffer; 0, 2 repeated name, -1 failed. |
| `mj_deleteFileVFS` | 0, or -1 not found. |
| `mj_containsFileVFS` / `mj_containsBufferVFS` | 1 exists, 0 not found. |
| `mj_mountVFS` / `mj_unmountVFS` | Mount a provider under a path (0, 2 repeated, -1 invalid) / unmount (0, -1). |
| `mj_getCacheSize` / `mj_getCacheCapacity` / `mj_setCacheCapacity` | Asset cache bytes used / capacity / set capacity (0 disables). |
| `mj_getCache` / `mj_clearCache` | Get / clear the compiler's asset cache. |
| `mju_openResource` / `mju_closeResource` | Open (OS filesystem if no provider prefix matches) / close (NULL is no-op). |
| `mju_readResource` / `mju_writeResource` | Read bytes (negative on error) / write via provider (-1 on error). |
| `mju_getResourceDir` / `mju_isModifiedResource` | Dir part of name / compare timestamp (0 same, >0 newer, <0 older). |
| `mju_decodeResource` | Decode to spec; caller owns it; NULL and error on failure. |

## Initialization

| Function | Semantics |
|----|----|
| `mj_defaultLROpt` / `mj_defaultSolRefImp` / `mj_defaultOption` / `mj_defaultVisual` | Defaults for length-range options / solref, solimp / physics options / visual options. |
| `mj_copyModel` | Copy model; allocate if `dest` is NULL. |
| `mj_saveModel` | Save to MJB file or buffer (buffer wins). By-reference textures stay references. |
| `mj_loadModel` / `mj_loadModelBuffer` | Load MJB from file (optional `vfs`) / memory. |
| `mj_deleteModel` / `mj_sizeModel` | Free model / buffer size needed. |
| `mj_makeData` / `mj_deleteData` | Allocate / free `mjData`. |
| `mj_copyData` | Copy `mjData`; `m` needs only MJMODEL_INTS sizes. |
| `mjv_copyData` | Copy for visualization only; large arrays are NULL, not valid for simulation. |
| `mj_resetData` / `mj_resetDataDebug` / `mj_resetDataKeyframe` | Reset to defaults / fill rest with `debug_value` / from keyframe `key` if 0 <= key < nkey. |
| `mj_resetCtrl` | Ctrl to neutral: zero, quaternion inputs to identity. |
| `mj_markStack` / `mj_freeStack` | Mark / free an `mjData` stack frame; pointers from `mj_stackAlloc*` become invalid. |
| `mj_stackAllocByte` / `mj_stackAllocNum` / `mj_stackAllocInt` | Allocate on the `mjData` stack; `mju_error` on overflow. |
| `mj_resetCallbacks` | Reset all callbacks to NULL. |
| `mj_setConst` | Set constant fields of `mjModel` for qpos0. |
| `mj_setLengthRange` | Set `actuator_lengthrange`; 1 ok, 0 error. |
| `mj_makeSpec` / `mj_copySpec` / `mj_deleteSpec` | Create empty / copy / free spec. |
| `mjs_activatePlugin` / `mjs_setDeepCopy` | Activate plugin / deep copy on attach; 0 on success. |

## Error and memory

| Function | Semantics |
|----|----|
| `mju_error` | Fatal error to active log handler; if handler returns, `exit(EXIT_FAILURE)`. Recover only by `longjmp`. |
| `mju_warning` / `mju_info` | Warning (returns) / info with `mjtLogTopic` filter (`mjTOPIC_NONE` always passes; custom handlers get all). |
| `mju_message` | Dispatch a structured `mjLogMessage`; the others wrap it. |
| `mju_setLogHandler` | Set global handler; returns previous (never NULL); NULL restores default. |
| `mju_getLogConfig` / `mju_setLogConfig` | Get / set default handler config (console, file, info topics). |
| `mju_clearHandlers` | Restore default handlers and log config. |
| `mju_malloc` / `mju_free` | Allocate (64-byte aligned, padded) / free. |
| `mj_warning` / `mju_writeLog` | Count warnings in `mjData`, print first / append to MUJOCO_LOG.TXT. |
| `mjs_getError` / `mjs_numWarnings` / `mjs_getWarning` | Compiler error / warning count / i-th warning (nullptr out of bounds). `mjs_isWarning` is deprecated. |
| `mjs_getTimer` | Compiler timing, array of size `mjNCTIMER`. |

``` C
mjLogConfig config = mju_getLogConfig();
config.logto_file = false;
mju_setLogConfig(config);
```

## Miscellaneous

Muscle: `mju_muscleGain`, `mju_muscleBias` (prm = range[2], force, scale,
lmin, lmax, vmax, fpmax, fvmax), `mju_muscleDynamics` (tau_act, tau_deact,
smoothing_width). Contacts: `mju_encodePyramid`, `mju_decodePyramid`. Scalars:
`mju_springDamper`, `mju_min`, `mju_max`, `mju_clip`, `mju_sign`, `mju_round`,
`mju_sigmoid` (quintic), `mju_isBad` (nan or > `mjMAXVAL`), `mju_isZero`,
`mju_standardNormal`, `mju_Halton`. Conversion: `mju_type2Str`,
`mju_str2Type` (`mjtObj`), `mju_f2n`, `mju_n2f`, `mju_d2n`, `mju_n2d`,
`mju_writeNumBytes`, `mju_warningText`. Other: `mju_insertionSort`,
`mju_insertionSortInt`, `mju_strncpy`.

## Interaction and visualization

See [visualization-rendering](../../c-programming/visualization-rendering/SKILL.md)
for the render loop.

| Function | Semantics |
|----|----|
| `mjv_defaultCamera` / `mjv_defaultFreeCamera` / `mjv_defaultPerturb` | Defaults. |
| `mjv_moveCamera` / `mjv_movePerturb` / `mjv_moveModel` | Mouse motion; `action` is `mjtMouse`. |
| `mjv_initPerturb` / `mjv_applyPerturbPose` / `mjv_applyPerturbForce` | Start perturbation / set pose (mocap, or qpos if paused and free) / force into `xfrc_applied`. |
| `mjv_select` | Geom id under viewport point `relx`, `rely` (-1 none); 3D point in `selpnt`. |
| `mjv_room2model` / `mjv_model2room` / `mjv_cameraInModel` / `mjv_cameraInRoom` / `mjv_frustumHeight` / `mjv_alignToCamera` / `mjv_averageCamera` / `mjv_camera2GLCamera` | Camera and room-space helpers. |
| `mjv_defaultOption` / `mjv_defaultFigure` / `mjv_defaultScene` | Defaults. |
| `mjv_makeScene` / `mjv_freeScene` / `mjv_updateScene` | Allocate / free / update the abstract scene. |
| `mjv_initGeom` / `mjv_connector` | Init a scene geom (NULL fields default) / connector between points (`mjGEOM_LINE` width in pixels). |
| `mjv_copyModel` | Model copy without large arrays. Nullable: `dest`. |
| `mjv_addGeoms` / `mjv_makeLights` / `mjv_updateCamera` / `mjv_updateSkin` | Scene update parts. |
| `mjv_cameraFrame` / `mjv_cameraFrustum` | Camera position and axes / frustum planes. |

## OpenGL rendering (mjr_)

Context: `mjr_defaultContext`, `mjr_makeContext` (`fontscale` is
`mjtFontScale`), `mjr_freeContext`, `mjr_changeFont`, `mjr_addAux`,
`mjr_resizeOffscreen`, `mjr_defaultRendererInfo`, `mjr_getRendererInfo`.
Upload: `mjr_uploadTexture` (by-reference textures decoded with
`mj_loadTexture`), `mjr_uploadMesh`, `mjr_uploadHField`. Buffers:
`mjr_setBuffer` (`mjFB_WINDOW` or `mjFB_OFFSCREEN`), `mjr_restoreBuffer`,
`mjr_readPixels`, `mjr_drawPixels`, `mjr_blitBuffer`, `mjr_setAux`,
`mjr_blitAux`, `mjr_maxViewport`. Drawing: `mjr_render`, `mjr_text`,
`mjr_overlay` (`mjtFont`, `mjtGridPos`), `mjr_rectangle`, `mjr_label`,
`mjr_figure`, `mjr_findRect`. GL: `mjr_finish`, `mjr_getError`.

## Filament rendering (mjrf_)

Every options struct has a `mjrf_default*` initializer (`ContextConfig`,
`ShadowOpts`, `MaterialOpts`, `RenderOpts`, `RenderRequest`, `ReadRequest`,
`TextureConfig`, `MeshConfig`, `SceneParams`, `LightParams`, `Material`,
`RenderableParams`, `RenderTargetConfig`, ...). Then:

| Area | Functions |
|----|----|
| Context | `mjrf_createContext`, `mjrf_destroyContext`, `mjrf_getRendererInfo`, `mjrf_modelRenderOpts` |
| Frames | `mjrf_render` (submit render and read requests together; group by target; async callbacks), `mjrf_waitForFrame`, `mjrf_flush`, `mjrf_setClearColor`, `mjrf_getFrameStats` |
| Textures, meshes | `mjrf_createTexture` (GPU upload on `mjrf_uploadTexture`), `mjrf_destroyTexture`, `mjrf_getTextureWidth`, `mjrf_getTextureHeight`, `mjrf_getTextureSamplerType`, `mjrf_createMesh`, `mjrf_uploadMesh`, `mjrf_destroyMesh` |
| Scene | `mjrf_createScene`, `mjrf_destroyScene`, `mjrf_addSceneLight`, `mjrf_removeSceneLight`, `mjrf_addSceneRenderable`, `mjrf_removeSceneRenderable`, `mjrf_setSceneSkybox`, `mjrf_configureSceneFromModel`, `mjrf_setSceneMsaa` (<= 1 disables) |
| Lights | `mjrf_createLight`, `mjrf_destroyLight`, `mjrf_setLight*` (`Active`, `CastShadow`, `Color`, `Intensity` candela, `Range` m, `Cutoff` deg, `Softness` [0,1], `BulbRadius`, `ShadowMapSize`, `Pose`), `mjrf_getLightType` |
| Renderables | `mjrf_createRenderable`, `mjrf_destroyRenderable`, `mjrf_setRenderable*` (`Mesh`, `GeomMesh`, `Material`, `Pose`, `Size`, `CastShadow`), `mjrf_getRenderableMaterial` |
| Targets | `mjrf_createRenderTarget`, `mjrf_destroyRenderTarget`, `mjrf_resizeRenderTarget` |

## UI framework (mjui_)

`mjui_add` adds an `mjuiDef` array (terminated by type -1) after the last
section; `mjui_addToSection` targets a section; limits `mjMAXUISECT`,
`mjMAXUIITEM`. `mjui_resize` computes sizes. `mjui_update` redraws after data
or state changes (-1 = all sections/items). `mjui_event` handles an event and
returns the item hit or NULL. `mjui_render` copies the UI buffer to the window
each refresh. Themes: `mjui_themeSpacing` (0-1), `mjui_themeColor` (0-3).

## Derivatives (mjd_)

| Function | Semantics |
|----|----|
| `mjd_transitionFD` | FD transition matrices of `mj_step`: `A` (2nv+na)², `B` (2nv+na) x nu, `C` nsensordata x (2nv+na), `D` nsensordata x nu. `eps`, `flg_centered` (0 forward, 1 centered). Not supported: RK4, sleeping, delays. All outputs nullable. |
| `mjd_inverseFD` | FD inverse-dynamics Jacobians `DfDq`, `DfDv`, `DfDa` (nv x nv), `DsDq`, `DsDv`, `DsDa` (nv x nsensordata), `DmDq` (nv x nC). Column major. `flg_actuation` subtracts `qfrc_actuator`. Not supported: RK4, noslip, sleeping. |
| `mjd_subQuat` / `mjd_quatIntegrate` | Derivatives of `mju_subQuat` / `mju_quatIntegrate`. |

Speed-up: `mj_forward` first, reduce solver `iterations`, call
`mjd_transitionFD`, restore. Accuracy: solver `tolerance` 0 with few
iterations. A batched example is under Batched simulation.

## SDF, plugins, threads

| Function | Semantics |
|----|----|
| `mjc_getSDF` / `mjc_distance` / `mjc_gradient` | SDF from geom id / signed distance / gradient. |
| `mjp_defaultPlugin` / `mjp_registerPlugin` | Default / register plugin (thread-safe; identical is no-op, same name differing raises `mju_error`). |
| `mjp_pluginCount` / `mjp_getPlugin` / `mjp_getPluginAtSlot` | Count / by name (optional `slot`) / by slot. |
| `mjp_defaultProvider` / `mjp_registerProvider` | Resource provider; prefix must not overlap others; slot >= 0 or -1. |
| `mjp_providerCount` / `mjp_findProvider` / `mjp_getProviderAtSlot` | Lookups; NULL if none. |
| `mjp_defaultDecoder` / `mjp_registerDecoder` / `mjp_findDecoder` | Resource decoders. |
| `mjp_defaultEncoder` / `mjp_registerEncoder` / `mjp_findEncoder` | Resource encoders. |
| `mjp_registerArchiveProvider` / `mjp_findArchiveProvider` / `mjp_archiveProviderCount` | Archive providers; `provider->prefix` is the extension(s), e.g. `.mjz\|.zip`. |
| `mju_threadpool` | Thread pool with `nthread` workers. |

See [engine-plugins](../../c-programming/engine-plugins/SKILL.md).

## Batched simulation (mjb_, mjbatch.h)

Run functions take `ids` (`nid` sorted unique indices, or NULL for all) and
return the number of simulations that raised an error; those keep their prior
state. Bad arguments raise `mju_error` on the caller's thread. Callbacks,
plugins and `mjb_apply` functions must not call `mju_error` or throw.

| Function | Semantics |
|----|----|
| `mjb_defaultConfig` | Defaults: one thread per logical CPU, one mjData per thread. |
| `mjb_makeBatch` | `nsim` simulations of a copy of `m`; `config` NULL uses defaults; NULL + `error` on failure. `nthread <= 0` uses all CPUs. `persistent` keeps one mjData per simulation (required for sleep or IPC). |
| `mjb_deleteBatch` | Free batch, threads and returned arrays; `b` may be NULL. |
| `mjb_step` | `nstep` calls of `mj_step`, then `mj_forward` stages up to `stage` (`mjSTAGE_NONE`, `mjSTAGE_VEL`, `mjSTAGE_ACC`). |
| `mjb_forward` / `mjb_reset` | Compute stages / reset (`key` per simulation, -1 or NULL for defaults). |
| `mjb_rollout` | `nstep` steps with `control` per substep (`control_spec` within `mjSTATE_USER`) and `nrecord` `mjBatchRecord`s. |
| `mjb_apply` | Run `func` (`mjfBatchFunc`) per simulation with `arg`; `save` nonzero writes state back. |
| `mjb_nstate` / `mjb_state` / `mjb_stateComponent` | State row size / `nsim x nstate` rows (writable) / component address and `size`. |
| `mjb_status` / `mjb_error` / `mjb_warning` | Per-simulation status / message / `mjWarningStat` counters. |
| `mjb_output` / `mjb_expand` / `mjb_expanded` | Register `mjData` output field / per-simulation `mjModel` field (`"opt.<name>"` for options) / read expanded storage. |
| `mjb_setConst` / `mjb_setModels` | `mj_setConst` per simulation / caller-owned models with identical mjData layout. |
| `mjb_getModel` / `mjb_getData` / `mjb_model` | Simulation's model / state into `d` / batch's model copy. |
| `mjb_nsim` / `mjb_nthread` / `mjb_persistent` | Counts and persistence flag. |

Transition matrices of every simulation (`mjd_transitionFD` restores the
state it perturbs, so `save` is zero):

``` C
// arrays of TransitionFD, nx = 2*nv + na
struct TransitionArgs {
  mjtNum* A;  // nsim x nx x nx
  mjtNum* B;  // nsim x nx x nu
};

// mjb_apply function: transition matrices of simulation sim
void TransitionFD(const mjModel* m, mjData* d, int sim, void* arg) {
  struct TransitionArgs* a = arg;
  int nx = 2*m->nv + m->na;
  mjd_transitionFD(m, d, 1e-6, /*flg_centered=*/0, a->A + sim*nx*nx, a->B + sim*nx*m->nu, NULL, NULL);
}

struct TransitionArgs args = {A, B};
mjb_apply(b, /*ids=*/NULL, 0, TransitionFD, &args, /*save=*/0);
```

In a non-persistent batch, the mjData passed to `func` holds the simulation's
state but other simulations' derived fields; compute what you read.

## Math (mju_)

Standard math macros map to C: `mju_sqrt`, `mju_exp`, `mju_sin`, `mju_cos`,
`mju_tan`, `mju_asin`, `mju_acos`, `mju_atan2`, `mju_tanh`, `mju_pow`,
`mju_abs` (`fabs`), `mju_log`, `mju_log10`, `mju_floor`, `mju_ceil`.

| Group | Functions |
|----|----|
| 3D/4D vectors | `mju_zero3`, `mju_copy3`, `mju_scl3`, `mju_add3`, `mju_sub3`, `mju_addTo3`, `mju_subFrom3`, `mju_addToScl3`, `mju_addScl3`, `mju_normalize3`, `mju_norm3`, `mju_dot3`, `mju_dist3`, `mju_mulMatVec3`, `mju_mulMatTVec3`, `mju_cross`, `mju_zero4`, `mju_unit4`, `mju_copy4`, `mju_normalize4` |
| n-vectors | `mju_zero`, `mju_fill`, `mju_copy`, `mju_sum`, `mju_L1`, `mju_scl`, `mju_add`, `mju_sub`, `mju_addTo`, `mju_subFrom`, `mju_addToScl`, `mju_addScl`, `mju_normalize`, `mju_norm`, `mju_dot` |
| Matrices | `mju_mulMatVec`, `mju_mulMatTVec`, `mju_mulVecMatVec`, `mju_transpose`, `mju_symmetrize`, `mju_eye`, `mju_mulMatMat`, `mju_mulMatMatT`, `mju_mulMatTMat`, `mju_sqrMatTD`, `mju_transformSpatial` |
| Sparse | `mju_dense2sparse` (1 if `nnz` too small), `mju_sparse2dense`, `mju_sym2dense` |
| Quaternions | `mju_rotVecQuat`, `mju_negQuat`, `mju_mulQuat`, `mju_mulQuatAxis`, `mju_axisAngle2Quat`, `mju_quat2Vel`, `mju_subQuat`, `mju_quat2Mat`, `mju_mat2Quat`, `mju_derivQuat`, `mju_quatIntegrate`, `mju_quatZ2Vec`, `mju_mat2Rot`, `mju_euler2Quat` (`seq` in 'xyzXYZ', lower intrinsic, upper extrinsic) |
| Poses | `mju_mulPose`, `mju_negPose`, `mju_trnVecPose` |
| Solvers | `mju_cholFactor`, `mju_cholSolve`, `mju_cholUpdate`, `mju_cholFactorBand`, `mju_cholSolveBand`, `mju_band2Dense`, `mju_dense2Band`, `mju_bandMulMatVec`, `mju_bandDiag`, `mju_eig3`, `mju_boxQP`, `mju_boxQPmalloc`, `mju_QP` |

`normalize` functions return the length before normalization. Band-dense
("arrowhead") matrices are set by `ntotal`, `nband` (incl. diagonal), `ndense`;
memory is `nband*(ntotal-ndense) + ndense*ntotal`. `mju_boxQP` solves
min ½xᵀHx + xᵀg, l <= x <= u, returns rank of free subspace or -1; `R` needs
size n(n+7). `mju_QP` adds `alower <= A x <= aupper` (dual active set), returns
active count or -1 (H not PSD), -2 infeasible, -3 unbounded, -4 iteration
limit; `work` size n² + (n+m)(2n+m+13).

## Model editing (mjs_)

Task guide: [model-editing](../../model-editing/SKILL.md). `def` arguments
are nullable.

| Group | Functions |
|----|----|
| Attachment | `mjs_attach` (attached element or NULL) |
| Tree elements | `mjs_addBody`, `mjs_addSite`, `mjs_addJoint`, `mjs_addFreeJoint`, `mjs_addGeom`, `mjs_addCamera`, `mjs_addLight`, `mjs_addFrame`, `mjs_delete` (0 on success; deletes contents and referencing elements) |
| Non-tree | `mjs_addActuator`, `mjs_addSensor`, `mjs_addFlex`, `mjs_makeFlex` (flexcomp in `body`), `mjs_addPair`, `mjs_addExclude`, `mjs_addEquality`, `mjs_addTendon`, `mjs_wrapSite`, `mjs_wrapGeom`, `mjs_wrapJoint`, `mjs_wrapPulley`, `mjs_addNumeric`, `mjs_addText`, `mjs_addTuple`, `mjs_addKey`, `mjs_addPlugin`, `mjs_addDefault` (`parent` nullable) |
| Actuator presets | `mjs_setToMotor`, `mjs_setToPosition`, `mjs_setToIntVelocity`, `mjs_setToVelocity`, `mjs_setToOrientation`, `mjs_setToPID`, `mjs_setToDamper`, `mjs_setToCylinder`, `mjs_setToMuscle`, `mjs_setToAdhesion`, `mjs_setToDCMotor` (return error if any) |
| Assets | `mjs_addMesh`, `mjs_addHField`, `mjs_addSkin`, `mjs_addTexture`, `mjs_addMaterial`, `mjs_makeMesh` (`mjtMeshBuiltin`; 0 on success) |
| Find / get | `mjs_getSpec`, `mjs_getOriginSpec`, `mjs_getCompiler`, `mjs_findSpec`, `mjs_findBody`, `mjs_findElement`, `mjs_findChild`, `mjs_getParent`, `mjs_getFrame`, `mjs_findFrame`, `mjs_getDefault`, `mjs_findDefault`, `mjs_getSpecDefault`, `mjs_getId`, `mjs_firstChild`, `mjs_nextChild`, `mjs_firstElement`, `mjs_nextElement`, `mjs_getWrapTarget`, `mjs_getWrapSideSite`, `mjs_getWrapDivisor`, `mjs_getWrapCoef` |
| Setters | `mjs_setName` (0 on success), `mjs_setBuffer`, `mjs_setString`, `mjs_setStringVec`, `mjs_setInStringVec`, `mjs_appendString`, `mjs_setInt`, `mjs_appendIntVec`, `mjs_setFloat`, `mjs_appendFloatVec`, `mjs_setDouble`, `mjs_setPluginAttributes` |
| Getters | `mjs_getName`, `mjs_getString`, `mjs_getInStringVec`, `mjs_getDouble` (`size` nullable), `mjs_getWrapNum`, `mjs_getWrap`, `mjs_getPluginAttributes` |
| Utilities | `mjs_setDefault`, `mjs_setFrame`, `mjs_resolveOrientation`, `mjs_fuseStatic`, `mjs_discardVisual`, `mjs_dedupAssets`, `mjs_adoptInertial`, `mjs_bodyToFrame`, `mjs_setUserValue`, `mjs_setUserValueWithCleanup`, `mjs_getUserValue`, `mjs_deleteUserValue`, `mjs_sensorDim` |
| Defaults | `mjs_default<Type>` for Spec, Orientation, Body, Frame, Joint, Geom, Site, Camera, Light, Flex, Mesh, HField, Skin, Texture, Material, Pair, Equality, Tendon, Actuator, Sensor, Numeric, Text, Tuple, Key, Plugin |
| Casting | `mjs_as<Type>` returns the typed pointer or NULL, for Body, Geom, Joint, Site, Camera, Light, Frame, Actuator, Sensor, Flex, Pair, Equality, Exclude, Tendon, Numeric, Text, Tuple, Key, Mesh, HField, Skin, Texture, Material, Plugin |

`mjs_fuseStatic` replaces joint-less bodies by frames in their parent;
`mjs_discardVisual` removes materials, textures, non-colliding geoms and unused
meshes; `mjs_dedupAssets` merges identical textures and meshes (no disk
reads). Each returns the count changed, 0 if unchanged, -1 on error (nothing
changed) and invalidates pointers to removed elements. `mjs_adoptInertial`
writes the inferred inertial explicitly (0 on success; error under
`inertiafromgeom="true"`).

## Source docs

Verbatim copies, for details not covered above:

- [APIreference/APIfunctions.md](references/APIreference-APIfunctions.md)
