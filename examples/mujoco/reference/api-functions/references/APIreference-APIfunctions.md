
# Functions

> [!TIP]
> Clicking on a function name below will take you to the source implementation in the GitHub repository.

The main header [mujoco.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mujoco.h) exposes a large number of functions. However the functions that most users are likely to need are a small fraction.

API function can be classified as:

- **Main entry points**  
  - *Parse and compile* an [mjModel](APItypes.md) from XML files and assets.
  - *Main simulation* entry points, including *mj_step*.

- **Support functions**  
  - *Support* functions requiring [mjModel](APItypes.md) and [mjData](APItypes.md).
  - Pipeline *components*, called from *mj_step*, *mj_forward* and *mj_inverse*.
  - *Sub components* of the simulation pipeline.
  - *Ray casting*.
  - *Printing* of various quantities.
  - *Virtual file system*, used to load assets from memory.
  - *Asset cache*, used to speed up model compilation.
  - *Resources*, interfacing with resource providers to load assets.
  - *Initialization* of data structures.
  - *Error and memory*.
  - *Miscellaneous* functions.

- **Visualization, Rendering, UI**  
  - *Abstract interaction*: mouse control of cameras and perturbations.
  - *Abstract Visualization*.
  - *OpenGL rendering*.
  - *Filament rendering*.
  - *UI framework*.

- **Threads, Plugins, Derivatives**  
  - *Derivatives*.
  - *Signed Distance Functions*.
  - *Thread* ⁠ -related functions.
  - *Batched simulation*.
  - *Plugin* ⁠ -related functions.

- **Math**  
  - Aliases for C *standard math* functions.
  - *Vector math*.
  - *Sparse math*.
  - *Quaternions*.
  - *Pose transformations*.
  - *Matrix decompositions and solvers*.

- **Model editing**  
  - *Attachment*.
  - *Tree elements*.
  - *Non-tree elements*.
  - *Set actuator parameters*.
  - *Assets*.
  - *Find and get utilities*.
  - *Attribute setters*.
  - *Attribute getters*.
  - *Spec utilities*.
  - *Element initialization*.
  - *Element casting*.

## Parse and compile

The key function here is `mj_loadXML`. It invokes the built-in parser and compiler, and either returns a pointer to a valid mjModel, or NULL - in which case the user should check the error information in the user-provided string. The model and all files referenced in it can be loaded from disk or from a VFS when provided.

### [mj_loadXML](#mj_loadXML)


mj_loadXML


Parse XML file in MJCF or URDF format, compile it; return low-level model.

If vfs is not NULL, look up files in vfs before reading from disk.

If error is not NULL, it must have size error_sz.

*Nullable:* `vfs`, `error`

### [mj_parseXML](#mj_parseXML)


mj_parseXML


Parse spec from XML file.

*Nullable:* `vfs`, `error`

### [mj_parseXMLString](#mj_parseXMLString)


mj_parseXMLString


Parse spec from XML string.

*Nullable:* `vfs`, `error`

### [mj_parse](#mj_parse)


mj_parse


Parse spec from a file.

*Nullable:* `vfs`, `error`

### [mj_encode](#mj_encode)


mj_encode


Encode `mjSpec` or `mjModel` to a file. The output format is determined by the file extension (case insensitive) or `content_type`. Returns the number of bytes written on success, -1 on failure.

For detailed documentation, supported output formats (`.xml`, `.mjb`, `.txt`, `.mjz`), and custom encoder plugins, see `Model Encoding & Saving <meSaving>`.

*Nullable:* `s`, `m`, `vfs`, `error`

### [mj_compile](#mj_compile)


mj_compile


Compile `mjSpec` to `mjModel`. A spec can be edited and compiled multiple times, returning a new `mjModel` instance that takes the edits into account. If compilation fails, `mj_compile` returns `NULL`; the error can be read with `mjs_getError`.

Compilation leaves the spec as it is written, with two exceptions. It completes `keyframes<keyframe>`: their vectors are sized for the model, and keyframes are added up to `nkey<size-nkey>`. And the compiler attributes `discardvisual<compiler-discardvisual>` and `fusestatic<compiler-fusestatic>` apply `mjs_discardVisual` and `mjs_fuseStatic` to the spec before it is compiled, which changes it: pointers to the elements which they remove are no longer valid. An operation which fails changes nothing, but one which succeeded stays applied if a later one, or the compilation, fails; the error then says so.

### [mj_copyBack](#mj_copyBack)


mj_copyBack


Copy to an `mjSpec` the values which were changed in the `mjModel` that was compiled from it. The changes can then be read in the spec, are saved with it, and are in the models which are compiled from it afterwards. An attribute is copied if the model no longer has what compilation gave it, all of its numbers; everything else in the spec is left as it is, including what was written there since it was compiled. The position and the orientation of a pose, and the bounds of a range, are separate attributes. Returns 1 on success. Returns 0 if the model was not compiled from the spec as it is structured now, or if a value was changed which the spec cannot express; nothing is copied then, and the error can be read with `mjs_getError`. A model can also be copied back to a copy of the spec made by `mj_copySpec`.

The values which are copied are `mjModel.opt`, `mjModel.vis` and `mjModel.stat`, the real-valued parameters of bodies, joints, geoms, sites, cameras, lights, materials, contact pairs, equalities, tendons, actuators and sensors, custom numeric and tuple data, keyframes and the elevation data of height fields. Each is written as what compiles to it:

- A pose is written in the `frame<frame>` which the element is in. An orientation which was not changed stays as it was written, for example as Euler angles, and one which was changed is written as a quaternion. Where compilation offsets the position by the orientation, for a mesh geom whose mesh is not centered at its origin and a body which is `aligned<body-freejoint-align>` with its free joint, a new orientation also writes the position. The reference pose of a body with a free joint is taken from `mjModel.qpos0` if that was changed.
- Angles are written in the `unit<compiler-angle>` of the spec.
- The size and pose of a geom or site which were written as `fromto`, or computed by fitting a geom to a mesh, are written in its place. A new radius of a capsule or cylinder leaves `fromto` as it is.
- A mass or inertia which was changed gives the body an explicit `inertial<body-inertial>`, which is then no longer inferred from its geoms; a body which has one keeps it as it was written if only the mass was changed. The inertia of the other bodies still follows their geoms, including a size or pose which was copied.
- A range whose `limited` attribute is "auto" keeps the limited state which it has in the model: the attribute is set if the new range would be inferred otherwise.
- A stiffness or damping of a joint with `springdamper<body-joint-springdamper>`, and a control or activation range which was inherited with `inheritrange<actuator-position-inheritrange>`, are written in its place.
- Elevation data of a height field which was read from a file is written in place of the file.
- The relative pose of a `weld<equality-weld>` between bodies which is marked by a nonzero `mjModel.eq_data[11]` is written as computed, with a zero quaternion.

The following changes cannot be expressed in the spec and are errors: the mass or inertia of a body when `inertiafromgeom<compiler-inertiafromgeom>` is "true" or `settotalmass<compiler-settotalmass>` is set; the inertial frame of a body which is `aligned<body-freejoint-align>` with its free joint; the pose of the world body; the anchor or axis of a free joint and the axis of a ball joint; the size of a mesh or height field geom or of a mesh site, and the frame of a mesh; the field of view of a camera which has a sensor size, and the intrinsics of one which has none; and different control ranges for the inputs of an actuator which has one. So are changes which the next compilation would not keep: damping, armature, friction loss or their solver parameters which differ between the degrees of freedom of a ball or free joint; elevation data of a height field whose lowest and highest values are not 0 and 1; and the anchor of a `connect<equality-connect>` between bodies in its second body, or the relative pose of a marked weld, other than the one which `mj_setConst` computes.

### [mj_recompile](#mj_recompile)


mj_recompile


Recompile spec to model, preserving the state. Like `mj_compile`, this function compiles an `mjSpec` to an `mjModel`, with two differences. First, rather than returning an entirely new model, it will reallocate existing `mjModel` and `mjData` instances in-place. Second, it will preserve the `integration state<siIntegrationState>`, as given in the provided `mjData` instance, while accounting for newly added or removed degrees of freedom. This allows the user to continue simulation with the same model and data struct pointers while editing the model programmatically.

`mj_recompile` returns 0 if compilation succeed. In the case of failure, the given `mjModel` and `mjData` instances will be deleted; as in `mj_compile`, the compilation error can be read with `mjs_getError`.

### [mj_loadTexture](#mj_loadTexture)


mj_loadTexture


Decode texture id to raw bytes, exactly what compilation would store in tex_data, with tex_nchannel channels; embedded textures are copied from the model. The buffer is allocated with mju_malloc and freed by the caller; colorspace receives the resolved colorspace (mjtColorSpace).

Return 0 on success.

*Nullable:* `width`, `height`, `colorspace`, `error`

### [mj_embedAssets](#mj_embedAssets)


mj_embedAssets


Copy of m with every by-reference asset loaded into it, as compilation would have stored it.

Return NULL with error on a file that does not resolve. A hermetic MJB file of a model with by-reference assets is mj_embedAssets, then mj_saveModel, then mj_deleteModel.

*Nullable:* `error`

### [mj_saveLastXML](#mj_saveLastXML)


mj_saveLastXML


Update XML data structures with info from low-level model created with `mj_loadXML`, save as MJCF. If error is not NULL, it must have size error_sz.

Note that this function only saves models that have been loaded with `mj_loadXML`, the legacy loading mechanism. See the `model editing<meOverview>` chapter to understand the difference between the old and new model loading and saving mechanisms.

### [mj_freeLastXML](#mj_freeLastXML)


mj_freeLastXML


Free last XML model if loaded. Called internally at each load.

### [mj_saveXMLString](#mj_saveXMLString)


mj_saveXMLString


Save spec to XML string, return 0 on success, -1 on failure. If the length of the output buffer is too small, returns the required size. See `mj_saveXML` for what is saved.

### [mj_saveXML](#mj_saveXML)


mj_saveXML


Save spec to XML file, return 0 on success, -1 otherwise. The compiler attributes `savecompiled<compiler-savecompiled>` and `savecanonical<compiler-savecanonical>` of the spec say whether the model is saved as it was compiled or as it is written in the spec, and in which notation; see `Model Encoding & Saving <meSaving>`. Saving the compiled values requires that the spec first be compiled, and compiled again after it is structurally edited (elements added, deleted or attached).

### [mju_getXMLDependencies](#mju_getXMLDependencies)


mju_getXMLDependencies


Given MJCF filename, fills dependencies with a list of all other asset files it depends on.

The search is recursive, and the list includes the filename itself.

## Main simulation

These are the main entry points to the simulator. Most users will only need to call `mj_step`, which computes everything and advanced the simulation state by one time step. Controls and applied forces must either be set in advance (in `mjData.{ctrl, qfrc_applied, xfrc_applied}`), or a control callback `mjcb_control` must be installed which will be called just before the controls and applied forces are needed. Alternatively, one can use `mj_step1` and `mj_step2` which break down the simulation pipeline into computations that are executed before and after the controls are needed; in this way one can set controls that depend on the results from `mj_step1`. Keep in mind though that the RK4 solver does not work with mj_step1/2. See `Pipeline` for a more detailed description.

mj_forward performs the same computations as `mj_step` but without the integration. It is useful after loading or resetting a model (to put the entire mjData in a valid state), and also for out-of-order computations that involve sampling or finite-difference approximations.

`mj_inverse` runs the inverse dynamics, and writes its output in `mjData.qfrc_inverse`. Note that `mjData.qacc` must be set before calling this function. Given the state (qpos, qvel, act), mj_forward maps from force to acceleration, while mj_inverse maps from acceleration to force. Mathematically these functions are inverse of each other, but numerically this may not always be the case because the forward dynamics rely on a constraint optimization algorithm which is usually terminated early. The difference between the results of forward and inverse dynamics can be computed with the function `mj_compareFwdInv`, which can be thought of as another solver accuracy check (as well as a general sanity check).

The skip version of `mj_forward` and `mj_inverse` are useful for example when qpos was unchanged but qvel was changed (usually in the context of finite differencing). Then there is no point repeating the computations that only depend on qpos. Calling the dynamics with skipstage = `mjSTAGE_POS<mjtStage>` will achieve these savings.

### [mj_step](#mj_step)


mj_step


Advance simulation, use control callback to obtain external force and control.

### [mj_step1](#mj_step1)


mj_step1


Advance simulation in two steps: before external force and control is set by user.

### [mj_step2](#mj_step2)


mj_step2


Advance simulation in two steps: after external force and control is set by user.

### [mj_forward](#mj_forward)


mj_forward


Forward dynamics: same as mj_step but do not integrate in time.

### [mj_inverse](#mj_inverse)


mj_inverse


Inverse dynamics: qacc must be set before calling.

### [mj_forwardSkip](#mj_forwardSkip)


mj_forwardSkip


Forward dynamics with skip; skipstage is mjtStage.

### [mj_inverseSkip](#mj_inverseSkip)


mj_inverseSkip


Inverse dynamics with skip; skipstage is mjtStage.

## Support

These are support functions that need access to `mjModel` and `mjData`, unlike the utility functions which do not need such access. Support functions are called within the simulator but some of them can also be useful for custom computations, and are documented in more detail below.

### [mj_stateSize](#mj_stateSize)


mj_stateSize


Returns the number of `mjtNum` ⁠ s required for a given state signature. The bits of the integer `sig` correspond to element fields of `mjtState`.

### [mj_getState](#mj_getState)


mj_getState


Copy concatenated state components specified by `sig` from `d` into `state`. The bits of the integer `sig` correspond to element fields of `mjtState`. Fails with `mju_error` if `sig` is invalid.

### [mj_extractState](#mj_extractState)


mj_extractState


Extract into `dst` the subset of components specified by `dstsig` from a state `src` previously obtained via `mj_getState` with components specified by `srcsig`. Fails with `mju_error` if the bits set in `dstsig` is not a subset of the bits set in `srcsig`.

### [mj_setState](#mj_setState)


mj_setState


Copy concatenated state components specified by `sig` from `state` into `d`. The bits of the integer `sig` correspond to element fields of `mjtState`. Fails with `mju_error` if `sig` is invalid.

### [mj_copyState](#mj_copyState)


mj_copyState


Copy state from src to dst.

### [mj_readCtrl](#mj_readCtrl)


mj_readCtrl


Read the control value for an actuator at a given time, taking delays into account. If no history buffer exists, return a pointer to the actuator's slice of `mjData.ctrl`. If a history buffer exists (`nsample<actuator-general-nsample>` \> 0), read from the delay buffer at `time - actuator_delay[id]`. Note that the subtraction of the delay changes the semantic of the `time` argument from "time at which values were pushed into the delay buffer" to "time at which values come out of the delay buffer". See `Delays<CDelay>` for details.

**Return value semantics:**

- If no history buffer exists (`nsample<actuator-general-nsample>` = 0), returns a pointer to the actuator's slice of `mjData.ctrl`.
- If a history buffer exists (`nsample<actuator-general-nsample>` \> 0) and the requested time matches a stored sample (always true for `interp = 0`), returns a pointer to the data in the history buffer.
- If interpolation is required (`interp = 1 or 2`), returns `NULL` and writes the interpolated result to `result` (must be of size `actuator_ctrlnum[id]`).

**Interpolation:**

- `interp = 0`: Zero-order hold (piecewise constant)
- `interp = 1`: Piecewise Linear
- `interp = 2`: Cubic Spline (Catmull-Rom)
- `interp = -1`: Use the actuator's `interp<actuator-general-interp>` value.

Constant extrapolation is used outside of buffer bounds.

### [mj_readSensor](#mj_readSensor)


mj_readSensor


Read a sensor value at a given time, taking delays into account. If no history buffer exists, return a pointer to the sensor's slice of `mjData.sensordata`. If a history buffer exists (`nsample<sensor-nsample>` \> 0), read from the history buffer at `time - sensor_delay[id]`. Note that the subtraction of the delay changes the semantic of the `time` argument from "time at which values were pushed into the delay buffer" to "time at which values come out of the delay buffer". See `Delays<CDelay>` for details.

**Return value semantics:**

- If no history buffer exists (`nsample<sensor-nsample>` = 0), returns a pointer to the sensor's slice of `mjData.sensordata`.
- If a history buffer exists (`nsample<sensor-nsample>` \> 0) and the requested time matches a stored sample (always true for `interp = 0`), returns a pointer to the data in the history buffer.
- If interpolation is required (`interp = 1 or 2`), returns `NULL` and writes the interpolated result to `result` (must be of size `dim`).

**Interpolation:**

- `interp = 0`: Zero-order hold (piecewise constant)
- `interp = 1`: Piecewise Linear
- `interp = 2`: Cubic Spline (Catmull-Rom)
- `interp = -1`: Use the value in `interp<sensor-interp>`

Constant extrapolation is used outside of buffer bounds.

**Usage:**

``` C
// read sensor 0 of data size `dim` at time t
mjtNum result[dim];
const mjtNum* ptr = mj_readSensor(m, d, 0, t, result, /* interp = */ 1);
const mjtNum* data = ptr ? ptr : result;
```

### [mj_initCtrlHistory](#mj_initCtrlHistory)


mj_initCtrlHistory


Initialize the history buffer for an actuator with custom values. The `times` array specifies the timestamps for each sample (must be length `nsample<actuator-general-nsample>`), and `values` specifies the control values (must be of size `nsample * actuator_ctrlnum[id]`). If `times` is `NULL`, the existing timestamps in the buffer are used, and only the values are updated. See `Delays<CDelay>` for details.

### [mj_initSensorHistory](#mj_initSensorHistory)


mj_initSensorHistory


Initialize the history buffer for a sensor with custom values. The `times` array specifies the timestamps for each sample (must be length `nsample<sensor-nsample>`), and `values` specifies the sensor values (must be of size `nsample * dim`). If `times` is `NULL`, the existing timestamps in the buffer are used. The `phase` argument sets the user slot, which stores the last computation time for interval sensors. See `Delays<CDelay>` for details.

### [mj_setKeyframe](#mj_setKeyframe)


mj_setKeyframe


Copy current state to the k-th model keyframe.

### [mj_addContact](#mj_addContact)


mj_addContact


Add contact to d-\>contact list; return 0 if success; 1 if buffer full.

### [mj_isPyramidal](#mj_isPyramidal)


mj_isPyramidal


Determine type of friction cone.

### [mj_isSparse](#mj_isSparse)


mj_isSparse


Determine type of constraint Jacobian.

### [mj_isDual](#mj_isDual)


mj_isDual


Determine type of solver (PGS is dual, CG and Newton are primal).

### [mj_mulJacVec](#mj_mulJacVec)


mj_mulJacVec


This function multiplies the constraint Jacobian mjData.efc_J by a vector. Note that the Jacobian can be either dense or sparse; the function is aware of this setting. Multiplication by J maps velocities from joint space to constraint space.

### [mj_mulJacTVec](#mj_mulJacTVec)


mj_mulJacTVec


Same as mj_mulJacVec but multiplies by the transpose of the Jacobian. This maps forces from constraint space to joint space.

### [mj_jac](#mj_jac)


mj_jac


This function computes an end-effector kinematic Jacobian, describing the local linear relationship between the degrees-of-freedom and a given point. Given a body specified by its integer id (`body`) and a 3D point in the world frame (`point`) treated as attached to the body, the Jacobian has both translational (`jacp`) and rotational (`jacr`) components. Passing `NULL` for either pointer will skip that part of the computation. Each component is a 3-by-nv matrix. Each row of this matrix is the gradient of the corresponding coordinate of the specified point with respect to the degrees-of-freedom. The frame with respect to which the Jacobian is computed is centered at the body center-of-mass but aligned with the world frame. The minimal `pipeline stages<piForward>` required for Jacobian computations to be consistent with the current generalized positions `mjData.qpos` are `mj_kinematics` followed by `mj_comPos`.

*Nullable:* `jacp`, `jacr`

### [mj_jacBody](#mj_jacBody)


mj_jacBody


This and the remaining variants of the Jacobian function call mj_jac internally, with the center of the body, geom or site. They are just shortcuts; the same can be achieved by calling mj_jac directly.

*Nullable:* `jacp`, `jacr`

### [mj_jacBodyCom](#mj_jacBodyCom)


mj_jacBodyCom


Compute body center-of-mass end-effector Jacobian.

*Nullable:* `jacp`, `jacr`

### [mj_jacSubtreeCom](#mj_jacSubtreeCom)


mj_jacSubtreeCom


Compute subtree center-of-mass end-effector Jacobian.

### [mj_jacGeom](#mj_jacGeom)


mj_jacGeom


Compute geom end-effector Jacobian.

*Nullable:* `jacp`, `jacr`

### [mj_jacSite](#mj_jacSite)


mj_jacSite


Compute site end-effector Jacobian.

*Nullable:* `jacp`, `jacr`

### [mj_jacPointAxis](#mj_jacPointAxis)


mj_jacPointAxis


Compute translation end-effector Jacobian of point, and rotation Jacobian of axis.

*Nullable:* `jacPoint`, `jacAxis`

### [mj_jacDot](#mj_jacDot)


mj_jacDot


This function computes the time-derivative of an end-effector kinematic Jacobian computed by `mj_jac`. The minimal `pipeline stages<piStages>` required for computation to be consistent with the current generalized positions and velocities `mjData.{qpos, qvel}` are `mj_kinematics`, `mj_comPos`, `mj_comVel` (in that order).

*Nullable:* `jacp`, `jacr`

### [mj_angmomMat](#mj_angmomMat)


mj_angmomMat


This function computes the `3 x nv` angular momentum matrix $`H(q)`$, providing the linear mapping from generalized velocities to subtree angular momentum. More precisely if $`h`$ is the subtree angular momentum of body index `body` in `mjData.subtree_angmom` (reported by the `subtreeangmom<sensor-subtreeangmom>` sensor) and $`\dot q`$ is the generalized velocity `mjData.qvel`, then $`h = H \dot q`$.

### [mj_name2id](#mj_name2id)


mj_name2id


Get id of object with the specified `mjtObj` type and name, returns -1 if id not found.

### [mj_id2name](#mj_id2name)


mj_id2name


Get name of object with the specified `mjtObj` type and id, returns `NULL` if name not found.

### [mj_actuatorInputName](#mj_actuatorInputName)


mj_actuatorInputName


Get name of actuator input, determined by the actuator type and input signature; return NULL if the actuator type defines no input names.

### [mj_fullM](#mj_fullM)


mj_fullM


Convert sparse inertia matrix into full (i.e. dense) matrix.

### [mj_mulM](#mj_mulM)


mj_mulM


This function multiplies the joint-space inertia matrix stored in `mjData.M` by a vector.

### [mj_mulM2](#mj_mulM2)


mj_mulM2


Multiply vector by (inertia matrix)^(1/2).

### [mj_addM](#mj_addM)


mj_addM


Add inertia matrix to destination matrix (lower triangle only).

Destination can be sparse or dense when all int\* are NULL.

*Nullable:* `rownnz`, `rowadr`, `colind`

### [mj_applyFT](#mj_applyFT)


mj_applyFT


This function can be used to apply a Cartesian force and torque to a point on a body, and add the result to the vector mjData.qfrc_applied of all applied forces. Note that the function requires a pointer to this vector, because sometimes we want to add the result to a different vector.

### [mj_objectVelocity](#mj_objectVelocity)


mj_objectVelocity


Compute object 6D velocity (rot:lin) in object-centered frame, world/local orientation.

### [mj_objectAcceleration](#mj_objectAcceleration)


mj_objectAcceleration


Compute object 6D acceleration (rot:lin) in object-centered frame, world/local orientation. If acceleration or force sensors are not present in the model, `mj_rnePostConstraint` must be manually called in order to calculate mjData.cacc -- the total body acceleration, including contributions from the constraint solver.

### [mj_geomDistance](#mj_geomDistance)


mj_geomDistance


Returns the smallest signed distance between two geoms and optionally the segment from `geom1` to `geom2`. Returned distances are bounded from above by `distmax`. <br/> If no collision of distance smaller than `distmax` is found, the function will return `distmax` and `fromto`, if given, will be set to (0, 0, 0, 0, 0, 0).

*Nullable:* `fromto`


different (correct) behavior under <span class="title-ref">nativeccd</span>

As explained in `Collision Detection<coDistance>`, distances are inaccurate when using the `legacy CCD pipeline<coCCD>`, and its use is discouraged.


### [mj_insideSite](#mj_insideSite)


mj_insideSite


Return 1 if point is inside a site (convex hull for meshes), 0 otherwise.

### [mj_contactForce](#mj_contactForce)


mj_contactForce


Extract 6D force:torque given contact id, in the contact frame.

### [mj_differentiatePos](#mj_differentiatePos)


mj_differentiatePos


This function subtracts two vectors in the format of qpos (and divides the result by dt), while respecting the properties of quaternions. Recall that unit quaternions represent spatial orientations. They are points on the unit sphere in 4D. The tangent to that sphere is a 3D plane of rotational velocities. Thus when we subtract two quaternions in the right way, the result is a 3D vector and not a 4D vector. Thus the output qvel has dimensionality nv while the inputs have dimensionality nq.

### [mj_integratePos](#mj_integratePos)


mj_integratePos


This is the opposite of mj_differentiatePos. It adds a vector in the format of qvel (scaled by dt) to a vector in the format of qpos.

### [mj_normalizeQuat](#mj_normalizeQuat)


mj_normalizeQuat


Normalize all quaternions in qpos-type vector.

### [mj_local2Global](#mj_local2Global)


mj_local2Global


Map from body local to global Cartesian coordinates, sameframe takes values from mjtSameFrame.

### [mj_getTotalmass](#mj_getTotalmass)


mj_getTotalmass


Sum all body masses.

### [mj_setTotalmass](#mj_setTotalmass)


mj_setTotalmass


Scale body masses and inertias to achieve specified total mass.

### [mj_getPluginConfig](#mj_getPluginConfig)


mj_getPluginConfig


Return a config attribute value of a plugin instance;

NULL: invalid plugin instance ID or attribute name

### [mj_loadPluginLibrary](#mj_loadPluginLibrary)


mj_loadPluginLibrary


Load a dynamic library. The dynamic library is assumed to register one or more plugins.

### [mj_loadAllPluginLibraries](#mj_loadAllPluginLibraries)


mj_loadAllPluginLibraries


Scan a directory and load all dynamic libraries. Dynamic libraries in the specified directory are assumed to register one or more plugins. Optionally, if a callback is specified, it is called for each dynamic library encountered that registers plugins. A library that fails to load is skipped with a warning.

### [mj_version](#mj_version)


mj_version


Return version number: 1.0.2 is encoded as 102.

### [mj_versionString](#mj_versionString)


mj_versionString


Return the current version of MuJoCo as a null-terminated string.

## Components

These are components of the simulation pipeline, called internally from `mj_step`, `mj_forward` and `mj_inverse`. It is unlikely that the user will need to call them.

### [mj_fwdKinematics](#mj_fwdKinematics)


mj_fwdKinematics


Run all kinematics-like computations (kinematics, comPos, camlight, flex, tendon).

### [mj_fwdPosition](#mj_fwdPosition)


mj_fwdPosition


Run position-dependent computations.

### [mj_fwdVelocity](#mj_fwdVelocity)


mj_fwdVelocity


Run velocity-dependent computations.

### [mj_fwdActuation](#mj_fwdActuation)


mj_fwdActuation


Compute actuator force qfrc_actuator.

### [mj_fwdAcceleration](#mj_fwdAcceleration)


mj_fwdAcceleration


Add up all non-constraint forces, compute qacc_smooth.

### [mj_fwdConstraint](#mj_fwdConstraint)


mj_fwdConstraint


Run selected constraint solver.

### [mj_Euler](#mj_Euler)


mj_Euler


Euler integrator, semi-implicit in velocity.

### [mj_RungeKutta](#mj_RungeKutta)


mj_RungeKutta


Runge-Kutta explicit order-N integrator.

### [mj_implicit](#mj_implicit)


mj_implicit


Integrates the simulation state using an implicit-in-velocity integrator (either "implicit" or "implicitfast", see `Numerical Integration<geIntegration>`), and advances simulation time. See [mjdata.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjdata.h) for fields computed by this function.

### [mj_invPosition](#mj_invPosition)


mj_invPosition


Run position-dependent computations in inverse dynamics.

### [mj_invVelocity](#mj_invVelocity)


mj_invVelocity


Run velocity-dependent computations in inverse dynamics.

### [mj_invConstraint](#mj_invConstraint)


mj_invConstraint


Apply the analytical formula for inverse constraint dynamics.

### [mj_compareFwdInv](#mj_compareFwdInv)


mj_compareFwdInv


Compare forward and inverse dynamics, save results in fwdinv.

## Sub components

These are sub-components of the simulation pipeline, called internally from the components above.

### [mj_sensorPos](#mj_sensorPos)


mj_sensorPos


Evaluate position-dependent sensors.

### [mj_sensorVel](#mj_sensorVel)


mj_sensorVel


Evaluate velocity-dependent sensors.

### [mj_sensorAcc](#mj_sensorAcc)


mj_sensorAcc


Evaluate acceleration and force-dependent sensors.

### [mj_energyPos](#mj_energyPos)


mj_energyPos


Evaluate position-dependent energy (potential).

### [mj_energyVel](#mj_energyVel)


mj_energyVel


Evaluate velocity-dependent energy (kinetic).

### [mj_checkPos](#mj_checkPos)


mj_checkPos


Check qpos, reset if any element is too big or nan.

### [mj_checkVel](#mj_checkVel)


mj_checkVel


Check qvel, reset if any element is too big or nan.

### [mj_checkAcc](#mj_checkAcc)


mj_checkAcc


Check qacc, reset if any element is too big or nan.

### [mj_kinematics](#mj_kinematics)


mj_kinematics


Run forward kinematics.

### [mj_comPos](#mj_comPos)


mj_comPos


Map inertias and motion dofs to global frame centered at CoM.

### [mj_camlight](#mj_camlight)


mj_camlight


Compute camera and light positions and orientations.

### [mj_flex](#mj_flex)


mj_flex


Compute flex-related quantities.

### [mj_tendon](#mj_tendon)


mj_tendon


Compute tendon lengths, velocities and moment arms.

### [mj_transmission](#mj_transmission)


mj_transmission


Compute actuator transmission lengths and moments.

### [mj_crb](#mj_crb)


mj_crb


Run composite rigid body inertia algorithm (CRB).

### [mj_makeM](#mj_makeM)


mj_makeM


Compute the composite rigid body inertia with `mj_crb`, add terms due to `tendon armature<tendon-spatial-armature>`. The joint-space inertia matrix is stored in both `mjData.qM` and `mjData.M`. These arrays represent the same quantity using different layouts (parent-based and compressed sparse row, respectively).

### [mj_factorM](#mj_factorM)


mj_factorM


Compute sparse $`L^T D L`$ factorizaton of inertia matrix.

### [mj_solveM](#mj_solveM)


mj_solveM


Solve linear system $`M x = y`$ using factorization: $`x = (L^T D L)^{-1} y`$

### [mj_solveM2](#mj_solveM2)


mj_solveM2


Half of linear solve: $`x = \sqrt{D^{-1}} (L^T)^{-1} y`$

### [mj_comVel](#mj_comVel)


mj_comVel


Compute cvel, cdof_dot.

### [mj_passive](#mj_passive)


mj_passive


Compute qfrc_passive from spring-dampers, gravity compensation and fluid forces.

### [mj_subtreeVel](#mj_subtreeVel)


mj_subtreeVel


Sub-tree linear velocity and angular momentum: compute `subtree_linvel`, `subtree_angmom`. This function is triggered automatically if the subtree `velocity<sensor-subtreelinvel>` or `momentum<sensor-subtreeangmom>` sensors are present in the model. It is also triggered for `user sensors<sensor-user>` of `stage<sensor-user-needstage>` "vel".

### [mj_rne](#mj_rne)


mj_rne


Recursive Newton Euler: compute $`M(q) \ddot q + C(q,\dot q)`$. `flg_acc=0` removes the inertial term (i.e. assumes $`\ddot q = 0`$).

### [mj_rnePostConstraint](#mj_rnePostConstraint)


mj_rnePostConstraint


Recursive Newton Euler with final computed forces and accelerations. Computes three body-level `nv x 6` arrays, all defined in the subtreecom-based `c-frame<tyNotesCom>` and arranged in `[rotation(3), translation(3)]` order.

- `cacc`: Body acceleration, required for `mj_objectAcceleration`.
- `cfrc_int`: Interaction force with the parent body.
- `cfrc_ext`: External force acting on the body.

This function is triggered automatically if the following sensors are present in the model: `accelerometer<sensor-accelerometer>`, `force<sensor-force>`, `torque<sensor-torque>`, `framelinacc<sensor-framelinacc>`, `frameangacc<sensor-frameangacc>`. It is also triggered for `user sensors<sensor-user>` of `stage<sensor-user-needstage>` "acc".

`cfrc_ext` collects the forces that are not transmitted through the joints: applied Cartesian forces (`xfrc_applied`), contacts, connect and weld constraints, and spatial tendons (spring, damper, actuator, constraint and armature forces along the tendon path). `cfrc_int` is then the wrench transmitted through the joint, and its projection on the joint axes is the total joint-space force. Forces of actuators with site, slider-crank and body transmissions, gravity compensation, fluid forces, flex forces and custom passive forces are not yet collected and are attributed to the joints.

### [mj_maxContact](#mj_maxContact)


mj_maxContact


Return the maximum number of contacts that can be generated between two geoms.

If has_margin is -1, then the margin is pulled from the model, otherwise if has_margin \> 0 indicates that the geoms have a positive margin.

### [mj_collision](#mj_collision)


mj_collision


Run collision detection.

### [mj_makeConstraint](#mj_makeConstraint)


mj_makeConstraint


Construct constraints.

### [mj_island](#mj_island)


mj_island


Find constraint islands.

### [mj_projectConstraint](#mj_projectConstraint)


mj_projectConstraint


Compute inverse constraint inertia efc_AR.

### [mj_referenceConstraint](#mj_referenceConstraint)


mj_referenceConstraint


Compute efc_vel, efc_aref.

### [mj_constraintUpdate](#mj_constraintUpdate)


mj_constraintUpdate


Compute `efc_state`, `efc_force`, `qfrc_constraint`, and (optionally) cone Hessians. If `cost` is not `NULL`, set `*cost = s(jar)` where `jar = Jac*qacc - aref`.

*Nullable:* `cost`

## Ray casting

Ray collisions, also known as ray casting, find the distance `x` of a ray's intersection with a geom, where a ray is a line emanating from the 3D point `p` in the direction `v` i.e., `(p + x*v, x >= 0)`. All functions in this family return the distance to the nearest geom surface, or -1 if there is no intersection. Note that if `p` is inside a geom, the ray will intersect the surface from the inside which still counts as an intersection.

All ray collision functions rely on quantities computed by `mj_kinematics` (see `mjData`), so must be called after `mj_kinematics`, or functions that call it (e.g. `mj_fwdPosition`). The top level functions, which intersect with all geoms types, are `mj_ray` which casts a single ray, and `mj_multiRay` which casts multiple rays from a single point.

### [mj_ray](#mj_ray)


mj_ray


Intersect ray `pnt+x*vec, x >= 0` with geoms.

- Return distance `x` to nearest surface, or -1 if no intersection.
- If `geomid` is not NULL, write the id of the intersected geom or -1 if not intersection.
- If `normal` is not NULL, write the surface normal at the intersection point. The normal always points **out of the geometry**, regardless of the ray's direction (i.e., including rays hitting the surface from the inside).
- Exclude geoms in body with id `bodyexclude`, use -1 to include all bodies.
- `geomgroup` is an array of length `mjNGROUP<glNumericVisualization>`, where 1 means the group should be included. Pass NULL to skip geom group exclusion.
- If `flg_static` is 0, static geoms will be excluded.

*Nullable:* `geomgroup`, `geomid`, `normal`

### [mj_multiRay](#mj_multiRay)


mj_multiRay


Intersect multiple rays emanating from a single point, compute normals if given.

Similar semantics to mj_ray, but vec, normal and dist are arrays.

Geoms further than cutoff are ignored.

*Nullable:* `geomgroup`, `geomid`, `normal`

### [mj_rayHfield](#mj_rayHfield)


mj_rayHfield


Intersect ray with hfield; return nearest distance or -1 if no intersection.

*Nullable:* `normal`

### [mj_rayMesh](#mj_rayMesh)


mj_rayMesh


Intersect ray with mesh; return nearest distance or -1 if no intersection.

*Nullable:* `normal`

### [mju_rayGeom](#mju_rayGeom)


mju_rayGeom


Intersect ray with pure geom; return nearest distance or -1 if no intersection.

*Nullable:* `normal`

### [mj_rayFlex](#mj_rayFlex)


mj_rayFlex


Intersect ray with flex; return nearest distance or -1 if no intersection, and also output nearest vertex id and surface normal.

*Nullable:* `vertid`, `normal`

### [mju_raySkin](#mju_raySkin)


mju_raySkin


Intersect ray with skin; return nearest distance or -1 if no intersection, and also output nearest vertex id.

*Nullable:* `vertid`

## Printing

These functions can be used to print various quantities to the screen for debugging purposes.

### [mj_printFormattedModel](#mj_printFormattedModel)


mj_printFormattedModel


Print mjModel to text file, specifying format. float_format must be a valid printf-style format string for a single float value.

### [mj_printModel](#mj_printModel)


mj_printModel


Print model to text file.

### [mj_printFormattedData](#mj_printFormattedData)


mj_printFormattedData


Print mjData to text file, specifying format. float_format must be a valid printf-style format string for a single float value.

### [mj_printData](#mj_printData)


mj_printData


Print data to text file.

### [mju_printMat](#mju_printMat)


mju_printMat


Print matrix to screen.

### [mju_printMatSparse](#mju_printMatSparse)


mju_printMatSparse


Print sparse matrix to screen.

### [mj_printSchema](#mj_printSchema)


mj_printSchema


Print internal XML schema as plain text or HTML, with style-padding or `&nbsp;`.

### [mj_printScene](#mj_printScene)


mj_printScene


Print scene to text file.

### [mj_printFormattedScene](#mj_printFormattedScene)


mj_printFormattedScene


Print scene to text file, specifying format. float_format must be a valid printf-style format string for a single float value.

## Virtual file system

Virtual file system (VFS) enables the user to load all necessary files in memory, including MJB binary model files, XML files (MJCF, URDF and included files), STL meshes, PNGs for textures and height fields, and HF files in our custom height field format. Model and resource files in the VFS can also be constructed programmatically (say using a Python library that writes to memory). Once all desired files are in the VFS, the user can call `mj_loadModel` or `mj_loadXML` with a pointer to the VFS. When this pointer is not NULL, the loaders will first check the VFS for any files they are about to load, and only access the disk if the file is not found in the VFS.

The VFS must first be allocated using `mj_defaultVFS` and must be freed with `mj_deleteVFS`.

### [mj_defaultVFS](#mj_defaultVFS)


mj_defaultVFS


Initialize an empty VFS, `mj_deleteVFS` must be called to deallocate the VFS.

### [mj_mountVFS](#mj_mountVFS)


mj_mountVFS


Mount a provider to handle file operations under the given path; return 0: success, 2: repeated name, -1: invalid provider.

### [mj_unmountVFS](#mj_unmountVFS)


mj_unmountVFS


Unmount a previously mounted provider; return 0: success, -1: not found in VFS.

### [mj_addFileVFS](#mj_addFileVFS)


mj_addFileVFS


Add file to VFS. The directory argument is optional and can be NULL or empty. Returns 0 on success, 2 on name collision, or -1 when an internal error occurs.

*Nullable:* `directory`

### [mj_addBufferVFS](#mj_addBufferVFS)


mj_addBufferVFS


Add file to VFS from buffer; return 0: success, 2: repeated name, -1: failed to load.

### [mj_deleteFileVFS](#mj_deleteFileVFS)


mj_deleteFileVFS


Delete file from VFS; return 0: success, -1: not found in VFS.

### [mj_containsBufferVFS](#mj_containsBufferVFS)


mj_containsBufferVFS


Check if buffer exists in VFS; return 1: exists, 0: not found.

### [mj_containsFileVFS](#mj_containsFileVFS)


mj_containsFileVFS


Check if file exists in VFS; return 1: exists, 0: not found.

### [mj_deleteVFS](#mj_deleteVFS)


mj_deleteVFS


Delete all files from VFS and deallocates VFS internal memory.

## Asset cache

The asset cache is a mechanism for caching assets (e.g. textures, meshes, etc.) to avoid repeated slow recompilation. The following methods provide way to control the capacity of the cache or to disable it altogether.

### [mj_getCacheSize](#mj_getCacheSize)


mj_getCacheSize


Get the current size of the asset cache in bytes.

### [mj_getCacheCapacity](#mj_getCacheCapacity)


mj_getCacheCapacity


Get the capacity of the asset cache in bytes.

### [mj_setCacheCapacity](#mj_setCacheCapacity)


mj_setCacheCapacity


Set the capacity of the asset cache in bytes (0 to disable); return the new capacity.

### [mj_getCache](#mj_getCache)


mj_getCache


Get the internal asset cache used by the compiler.

### [mj_clearCache](#mj_clearCache)


mj_clearCache


Clear the asset cache.

## Resources

Resources are the interface between `resource providers <exProvider>` and MuJoCo model compilation code. These functions provide the means to query the resource provider and obtain resources.

### [mju_openResource](#mju_openResource)


mju_openResource


Open a resource; if the name doesn't have a prefix matching a registered provider, then the OS filesystem is used.

*Nullable:* `dir`, `vfs`, `error`

### [mju_closeResource](#mju_closeResource)


mju_closeResource


Close a resource; no-op if resource is NULL.

### [mju_readResource](#mju_readResource)


mju_readResource


Set buffer to bytes read from the resource and return number of bytes in buffer; return negative value if error.

### [mju_writeResource](#mju_writeResource)


mju_writeResource


Write resource data via its provider, return bytes written or -1 on error.

*Nullable:* `vfs`, `error`

### [mju_getResourceDir](#mju_getResourceDir)


mju_getResourceDir


For a resource with a name partitioned as {dir}{filename}, get the dir and ndir pointers.

### [mju_isModifiedResource](#mju_isModifiedResource)


mju_isModifiedResource


Compare resource timestamp to provided timestamp.

Return 0 if timestamps match, \>0 if resource is newer, \<0 if resource is older.

### [mju_decodeResource](#mju_decodeResource)


mju_decodeResource


Find the decoder for a resource and return the decoded spec.

The caller takes ownership of the spec and is responsible for cleaning it up.

On failure, return NULL and write the reason to error.

*Nullable:* `vfs`, `error`

## Initialization

This section contains functions that load/initialize the model or other data structures. Their use is well illustrated in the code samples.

### [mj_defaultLROpt](#mj_defaultLROpt)


mj_defaultLROpt


Set default options for length range computation.

### [mj_defaultSolRefImp](#mj_defaultSolRefImp)


mj_defaultSolRefImp


Set solver parameters to default values.

*Nullable:* `solref`, `solimp`

### [mj_defaultOption](#mj_defaultOption)


mj_defaultOption


Set physics options to default values.

### [mj_defaultVisual](#mj_defaultVisual)


mj_defaultVisual


Set visual options to default values.

### [mj_copyModel](#mj_copyModel)


mj_copyModel


Copy mjModel, allocate new if dest is NULL.

*Nullable:* `dest`

### [mj_saveModel](#mj_saveModel)


mj_saveModel


Save model to binary MJB file or memory buffer; buffer has precedence when given. The model is written as it is: a model with `by-reference<CAssetReference>` textures keeps them as references, and the file loads wherever the paths resolve. A hermetic file is `mj_embedAssets`, then `mj_saveModel` on the result, then `mj_deleteModel`.

*Nullable:* `filename`, `buffer`

### [mj_loadModel](#mj_loadModel)


mj_loadModel


Load model from binary MJB file.

If vfs is not NULL, look up file in vfs before reading from disk.

*Nullable:* `vfs`

### [mj_loadModelBuffer](#mj_loadModelBuffer)


mj_loadModelBuffer


Load model from memory buffer.

### [mj_deleteModel](#mj_deleteModel)


mj_deleteModel


Free memory allocation in model.

### [mj_sizeModel](#mj_sizeModel)


mj_sizeModel


Return size of buffer needed to hold model.

### [mj_makeData](#mj_makeData)


mj_makeData


Allocate mjData corresponding to given model.

If the model buffer is unallocated the initial configuration will not be set.

### [mj_copyData](#mj_copyData)


mj_copyData


Copy mjData. m is only required to contain the size fields from MJMODEL_INTS.

### [mjv_copyData](#mjv_copyData)


mjv_copyData


Copy `mjData`, skipping large arrays not required for visualization, like the constraint Jacobian. The copy is meant for visualization, e.g. with `mjv_updateScene`; the skipped arrays are `NULL`, so it is not a valid input to simulation functions.

### [mj_resetCtrl](#mj_resetCtrl)


mj_resetCtrl


Reset ctrl to neutral values: zero, except quaternion inputs which reset to the identity.

### [mj_resetData](#mj_resetData)


mj_resetData


Reset data to defaults.

### [mj_resetDataDebug](#mj_resetDataDebug)


mj_resetDataDebug


Reset data to defaults, fill everything else with debug_value.

### [mj_resetDataKeyframe](#mj_resetDataKeyframe)


mj_resetDataKeyframe


Reset data. If 0 \<= key \< nkey, set fields from specified keyframe.

### [mj_markStack](#mj_markStack)


mj_markStack


Mark a new frame on the mjData stack.

### [mj_freeStack](#mj_freeStack)


mj_freeStack


Free the current mjData stack frame. All pointers returned by mj_stackAlloc since the last call to mj_markStack must no longer be used afterwards.

### [mj_stackAllocByte](#mj_stackAllocByte)


mj_stackAllocByte


Allocate a number of bytes on mjData stack at a specific alignment.

Call mju_error on stack overflow.

### [mj_stackAllocNum](#mj_stackAllocNum)


mj_stackAllocNum


Allocate array of mjtNums on mjData stack. Call mju_error on stack overflow.

### [mj_stackAllocInt](#mj_stackAllocInt)


mj_stackAllocInt


Allocate array of ints on mjData stack. Call mju_error on stack overflow.

### [mj_deleteData](#mj_deleteData)


mj_deleteData


Free memory allocation in mjData.

### [mj_resetCallbacks](#mj_resetCallbacks)


mj_resetCallbacks


Reset all callbacks to NULL pointers (NULL is the default).

### [mj_setConst](#mj_setConst)


mj_setConst


Set constant fields of mjModel, corresponding to qpos0 configuration.

### [mj_setLengthRange](#mj_setLengthRange)


mj_setLengthRange


Set actuator_lengthrange for specified actuator; return 1 if ok, 0 if error.

*Nullable:* `error`

### [mj_makeSpec](#mj_makeSpec)


mj_makeSpec


Create empty spec.

### [mj_copySpec](#mj_copySpec)


mj_copySpec


Copy spec.

### [mj_deleteSpec](#mj_deleteSpec)


mj_deleteSpec


Free memory allocation in mjSpec.

### [mjs_activatePlugin](#mjs_activatePlugin)


mjs_activatePlugin


Activate plugin; return 0 on success.

### [mjs_setDeepCopy](#mjs_setDeepCopy)


mjs_setDeepCopy


Turn deep copy on or off attach; return 0 on success.

## Error and memory

### [mju_error](#mju_error)


mju_error


Main error function. The error message is dispatched to the active log handler (see `mju_setLogHandler`). Errors are always fatal: if the handler returns, the process is terminated with `exit(EXIT_FAILURE)`. Handlers wishing to recover must `longjmp` or otherwise transfer control before returning.

### [mju_warning](#mju_warning)


mju_warning


Main warning function; returns to caller. The warning message is dispatched to the active log handler.

### [mju_clearHandlers](#mju_clearHandlers)


mju_clearHandlers


Clear all user handlers and restore defaults. Resets the legacy error/warning/memory callbacks to `NULL`, restores the default log handler, and resets the log configuration to its defaults (console and file output enabled, all info topics disabled).

### [mju_setLogHandler](#mju_setLogHandler)


mju_setLogHandler


Set the active global log handler. Returns the previous handler (which is never `NULL`), intended for save/restore or callback chaining. If `handler` is `NULL`, the default handler is restored. The handler receives all errors, warnings and informational messages as a structured `mjLogMessage`. See `siLogHandler` for usage examples.

### [mju_getLogConfig](#mju_getLogConfig)


mju_getLogConfig


Get the current default handler configuration. See `mjLogConfig`.

### [mju_setLogConfig](#mju_setLogConfig)


mju_setLogConfig


Set the default handler configuration. Controls console output, file output, and info topic filtering. See `mjLogConfig`.

Example usage (disabling file output):

``` C
mjLogConfig config = mju_getLogConfig();
config.logto_file = false;
mju_setLogConfig(config);
```

### [mju_info](#mju_info)


mju_info


Log an informational message with optional topic filtering. The `topic` argument is a `mjtLogTopic` value. Topic 0 (`mjTOPIC_NONE`) always passes through. Other topics must be enabled in the default handler configuration via `mju_setLogConfig`. Note that topic filtering is implemented in the default handler; custom handlers receive all info messages regardless.

### [mju_message](#mju_message)


mju_message


Dispatch a structured `mjLogMessage` to the active log handler. This is the primary entry point for emitting log messages with full control over all fields. The convenience functions `mju_error`, `mju_warning`, and `mju_info` are thin wrappers that populate an `mjLogMessage` and call this function.

The `subject` field is a one-line summary (up to 1024 bytes, inline in the struct). The `body` field is an optional `const char*` pointer to multi-line detail text, owned by the caller. When `body` is `NULL`, only the subject line is printed.

The default handler formats the output as follows:

``` text
LEVEL FUNC (FILE:LINE) TIME: SUBJECT
BODY
```

where:

- `LEVEL` is `ERROR`, `WARNING`, `INFO`, or `DEBUG`.
- `FUNC` is present when the `func` field is set.
- `(FILE:LINE)` is present when the `file` and `line` fields are set.
- `TIME` is present when the `timestamp` field is set or file logging is active.
- `SUBJECT` is the contents of the `subject` field.
- `BODY` follows on the next line(s), printed raw without indentation or separators, only if non-NULL.

The default handler appends a trailing blank line after `ERROR`, `WARNING`, and `INFO` messages for visual separation. `DEBUG` messages are printed compactly without a trailing blank line.

Example usage:

``` C
mjLogMessage msg = {
  .level = mjLOG_INFO,
  .timestamp = true,
  .body = "  height:     0.001 m\n  velocity:   0.000 m/s\n  bounces:    47",
};
snprintf(msg.subject, sizeof(msg.subject), "The ball has come to rest");
mju_message(&msg);
```

This produces:

``` text
INFO Mon Jun  9 15:04:05 2026: The ball has come to rest
  height:     0.001 m
  velocity:   0.000 m/s
  bounces:    47
```

### [mju_malloc](#mju_malloc)


mju_malloc


Allocate memory; byte-align on 64; pad size to multiple of 64.

### [mju_free](#mju_free)


mju_free


Free memory, using free() by default.

### [mj_warning](#mj_warning)


mj_warning


High-level warning function: count warnings in mjData, print only the first.

### [mju_writeLog](#mju_writeLog)


mju_writeLog


Write \[datetime, type: message\] to MUJOCO_LOG.TXT.

### [mjs_getError](#mjs_getError)


mjs_getError


Get compiler error message from spec.

### [mjs_getTimer](#mjs_getTimer)


mjs_getTimer


Get compiler timing diagnostics from spec, returns pointer to array of size mjNCTIMER.

### [mjs_isWarning](#mjs_isWarning)


mjs_isWarning


Return 1 if compiler error is a warning. Deprecated: use mjs_numWarnings(s) \> 0.

### [mjs_numWarnings](#mjs_numWarnings)


mjs_numWarnings


Get number of warnings accumulated in the spec.

### [mjs_getWarning](#mjs_getWarning)


mjs_getWarning


Get the i-th warning message (returns nullptr if index out of bounds).

## Miscellaneous

### [mju_muscleGain](#mju_muscleGain)


mju_muscleGain


Muscle active force, prm = (range\[2\], force, scale, lmin, lmax, vmax, fpmax, fvmax).

### [mju_muscleBias](#mju_muscleBias)


mju_muscleBias


Muscle passive force, prm = (range\[2\], force, scale, lmin, lmax, vmax, fpmax, fvmax).

### [mju_muscleDynamics](#mju_muscleDynamics)


mju_muscleDynamics


Muscle activation dynamics, prm = (tau_act, tau_deact, smoothing_width).

### [mju_encodePyramid](#mju_encodePyramid)


mju_encodePyramid


Convert contact force to pyramid representation.

### [mju_decodePyramid](#mju_decodePyramid)


mju_decodePyramid


Convert pyramid representation to contact force.

### [mju_springDamper](#mju_springDamper)


mju_springDamper


Integrate spring-damper analytically; return pos(dt).

### [mju_min](#mju_min)


mju_min


Return min(a,b) with single evaluation of a and b.

### [mju_max](#mju_max)


mju_max


Return max(a,b) with single evaluation of a and b.

### [mju_clip](#mju_clip)


mju_clip


Clip x to the range \[min, max\].

### [mju_sign](#mju_sign)


mju_sign


Return sign of x: +1, -1 or 0.

### [mju_round](#mju_round)


mju_round


Round x to nearest integer.

### [mju_type2Str](#mju_type2Str)


mju_type2Str


Convert type id (mjtObj) to type name.

### [mju_str2Type](#mju_str2Type)


mju_str2Type


Convert type name to type id (mjtObj).

### [mju_writeNumBytes](#mju_writeNumBytes)


mju_writeNumBytes


Return human readable number of bytes using standard letter suffix.

### [mju_warningText](#mju_warningText)


mju_warningText


Construct a warning message given the warning type and info.

### [mju_isBad](#mju_isBad)


mju_isBad


Return 1 if nan or abs(x)\>mjMAXVAL, 0 otherwise. Used by check functions.

### [mju_isZero](#mju_isZero)


mju_isZero


Return 1 if all elements are 0.

### [mju_standardNormal](#mju_standardNormal)


mju_standardNormal


Standard normal random number generator (optional second number).

### [mju_f2n](#mju_f2n)


mju_f2n


Convert from float to mjtNum.

### [mju_n2f](#mju_n2f)


mju_n2f


Convert from mjtNum to float.

### [mju_d2n](#mju_d2n)


mju_d2n


Convert from double to mjtNum.

### [mju_n2d](#mju_n2d)


mju_n2d


Convert from mjtNum to double.

### [mju_insertionSort](#mju_insertionSort)


mju_insertionSort


Insertion sort, resulting list is in increasing order.

### [mju_insertionSortInt](#mju_insertionSortInt)


mju_insertionSortInt


Integer insertion sort, resulting list is in increasing order.

### [mju_Halton](#mju_Halton)


mju_Halton


Generate Halton sequence.

### [mju_strncpy](#mju_strncpy)


mju_strncpy


Call strncpy, then set dst\[n-1\] = 0.

### [mju_sigmoid](#mju_sigmoid)


mju_sigmoid


Twice continuously differentiable sigmoid function using a quintic polynomial:

``` math
\begin{aligned}
s(x) =
\begin{cases}
0,                    &       & x \le 0  \\
6x^5 - 15x^4 + 10x^3, & 0 \lt & x \lt 1  \\
1,                    & 1 \le & x \qquad
\end{cases}
\end{aligned}
```

## Interaction

These functions implement abstract mouse interactions, allowing control over cameras and perturbations. Their use is well illustrated in `simulate<saSimulate>`.

### [mjv_defaultCamera](#mjv_defaultCamera)


mjv_defaultCamera


Set default camera.

### [mjv_defaultFreeCamera](#mjv_defaultFreeCamera)


mjv_defaultFreeCamera


Set default free camera.

### [mjv_defaultPerturb](#mjv_defaultPerturb)


mjv_defaultPerturb


Set default perturbation.

### [mjv_room2model](#mjv_room2model)


mjv_room2model


Transform pose from room to model space.

### [mjv_model2room](#mjv_model2room)


mjv_model2room


Transform pose from model to room space.

### [mjv_cameraInModel](#mjv_cameraInModel)


mjv_cameraInModel


Get camera info in model space; average left and right OpenGL cameras.

### [mjv_cameraInRoom](#mjv_cameraInRoom)


mjv_cameraInRoom


Get camera info in room space; average left and right OpenGL cameras.

### [mjv_frustumHeight](#mjv_frustumHeight)


mjv_frustumHeight


Get frustum height at unit distance from camera; average left and right OpenGL cameras.

### [mjv_alignToCamera](#mjv_alignToCamera)


mjv_alignToCamera


Rotate 3D vec in horizontal plane by angle between (0,1) and (forward_x,forward_y).

### [mjv_moveCamera](#mjv_moveCamera)


mjv_moveCamera


Move camera with mouse; action is mjtMouse.

### [mjv_movePerturb](#mjv_movePerturb)


mjv_movePerturb


Move perturb object with mouse; action is mjtMouse.

### [mjv_moveModel](#mjv_moveModel)


mjv_moveModel


Move model with mouse; action is mjtMouse.

### [mjv_initPerturb](#mjv_initPerturb)


mjv_initPerturb


Copy perturb pos,quat from selected body; set scale for perturbation.

### [mjv_applyPerturbPose](#mjv_applyPerturbPose)


mjv_applyPerturbPose


Set perturb pos,quat in d-\>mocap when selected body is mocap, and in d-\>qpos otherwise.

Write d-\>qpos only if flg_paused and subtree root for selected body has free joint.

### [mjv_applyPerturbForce](#mjv_applyPerturbForce)


mjv_applyPerturbForce


Set perturb force,torque in d-\>xfrc_applied, if selected body is dynamic.

### [mjv_averageCamera](#mjv_averageCamera)


mjv_averageCamera


Return the average of two OpenGL cameras.

### [mjv_camera2GLCamera](#mjv_camera2GLCamera)


mjv_camera2GLCamera


Converts a mjvCamera to a mjvGLCamera.

### [mjv_select](#mjv_select)


mjv_select


This function is used for mouse selection, relying on ray intersections. aspectratio is the viewport width/height. relx and rely are the relative coordinates of the 2D point of interest in the viewport (usually mouse cursor). The function returns the id of the geom under the specified 2D point, or -1 if there is no geom (note that they skybox if present is not a model geom). The 3D coordinates of the clicked point are returned in selpnt. See `simulate<saSimulate>` for an illustration.

## Visualization

The functions in this section implement abstract visualization. The results are used by the OpenGL renderer, and can also be used by users wishing to implement their own renderer, or hook up MuJoCo to advanced rendering tools such as Unity or Unreal Engine. See `simulate<saSimulate>` for illustration of how to use these functions.

### [mjv_defaultOption](#mjv_defaultOption)


mjv_defaultOption


Set default visualization options.

### [mjv_defaultFigure](#mjv_defaultFigure)


mjv_defaultFigure


Set default figure.

### [mjv_initGeom](#mjv_initGeom)


mjv_initGeom


Initialize given geom fields when not NULL, set the rest to their default values.

*Nullable:* `size`, `pos`, `mat`, `rgba`

### [mjv_connector](#mjv_connector)


mjv_connector


Set (type, size, pos, mat) for connector-type geom between given points.

Assume that mjv_initGeom was already called to set all other properties.

Width of mjGEOM_LINE is denominated in pixels.

### [mjv_defaultScene](#mjv_defaultScene)


mjv_defaultScene


Set default abstract scene.

### [mjv_makeScene](#mjv_makeScene)


mjv_makeScene


Allocate resources in abstract scene.

### [mjv_freeScene](#mjv_freeScene)


mjv_freeScene


Free abstract scene.

### [mjv_updateScene](#mjv_updateScene)


mjv_updateScene


Update entire scene given model state.

### [mjv_copyModel](#mjv_copyModel)


mjv_copyModel


Copy mjModel, skip large arrays not required for abstract visualization.

*Nullable:* `dest`

### [mjv_addGeoms](#mjv_addGeoms)


mjv_addGeoms


Add geoms from selected categories.

### [mjv_makeLights](#mjv_makeLights)


mjv_makeLights


Make list of lights.

### [mjv_updateCamera](#mjv_updateCamera)


mjv_updateCamera


Update camera.

### [mjv_updateSkin](#mjv_updateSkin)


mjv_updateSkin


Update skins.

### [mjv_cameraFrame](#mjv_cameraFrame)


mjv_cameraFrame


Compute camera position and forward, up, and right vectors.

*Nullable:* `headpos`, `forward`, `up`, `right`

### [mjv_cameraFrustum](#mjv_cameraFrustum)


mjv_cameraFrustum


Compute camera frustum: vertical, horizontal, and clip planes.

*Nullable:* `zver`, `zhor`, `zclip`

## OpenGL rendering

These functions expose the OpenGL renderer. See `simulate<saSimulate>` for an illustration of how to use these functions.

### [mjr_defaultContext](#mjr_defaultContext)


mjr_defaultContext


Set default mjrContext.

### [mjr_defaultRendererInfo](#mjr_defaultRendererInfo)


mjr_defaultRendererInfo


Set default mjrRendererInfo.

### [mjr_getRendererInfo](#mjr_getRendererInfo)


mjr_getRendererInfo


Get active renderer information.

### [mjr_makeContext](#mjr_makeContext)


mjr_makeContext


Allocate resources in custom OpenGL context; fontscale is mjtFontScale.

### [mjr_changeFont](#mjr_changeFont)


mjr_changeFont


Change font of existing context.

### [mjr_addAux](#mjr_addAux)


mjr_addAux


Add Aux buffer with given index to context; free previous Aux buffer.

### [mjr_freeContext](#mjr_freeContext)


mjr_freeContext


Free resources in custom OpenGL context, set to default.

### [mjr_resizeOffscreen](#mjr_resizeOffscreen)


mjr_resizeOffscreen


Resize offscreen buffers.

### [mjr_uploadTexture](#mjr_uploadTexture)


mjr_uploadTexture


Upload texture to GPU, overwriting previous upload if any. A by-reference texture (tex_adr == -1) is decoded with mj_loadTexture.

### [mjr_uploadMesh](#mjr_uploadMesh)


mjr_uploadMesh


Upload mesh to GPU, overwriting previous upload if any.

### [mjr_uploadHField](#mjr_uploadHField)


mjr_uploadHField


Upload height field to GPU, overwriting previous upload if any.

### [mjr_restoreBuffer](#mjr_restoreBuffer)


mjr_restoreBuffer


Make con-\>currentBuffer current again.

### [mjr_setBuffer](#mjr_setBuffer)


mjr_setBuffer


Set OpenGL framebuffer for rendering: mjFB_WINDOW or mjFB_OFFSCREEN.

If only one buffer is available, set that buffer and ignore framebuffer argument.

### [mjr_readPixels](#mjr_readPixels)


mjr_readPixels


Read pixels from current OpenGL framebuffer to client buffer.

Viewport is in OpenGL framebuffer; client buffer starts at (0,0).

### [mjr_drawPixels](#mjr_drawPixels)


mjr_drawPixels


Draw pixels from client buffer to current OpenGL framebuffer.

Viewport is in OpenGL framebuffer; client buffer starts at (0,0).

### [mjr_blitBuffer](#mjr_blitBuffer)


mjr_blitBuffer


Blit from src viewpoint in current framebuffer to dst viewport in other framebuffer.

If src, dst have different size and flg_depth==0, color is interpolated with GL_LINEAR.

### [mjr_setAux](#mjr_setAux)


mjr_setAux


Set Aux buffer for custom OpenGL rendering (call restoreBuffer when done).

### [mjr_blitAux](#mjr_blitAux)


mjr_blitAux


Blit from Aux buffer to con-\>currentBuffer.

### [mjr_text](#mjr_text)


mjr_text


Draw text at (x,y) in relative coordinates; font is mjtFont.

### [mjr_overlay](#mjr_overlay)


mjr_overlay


Draw text overlay; font is mjtFont; gridpos is mjtGridPos.

### [mjr_maxViewport](#mjr_maxViewport)


mjr_maxViewport


Get maximum viewport for active buffer.

### [mjr_rectangle](#mjr_rectangle)


mjr_rectangle


Draw rectangle.

### [mjr_label](#mjr_label)


mjr_label


Draw rectangle with centered text.

### [mjr_figure](#mjr_figure)


mjr_figure


Draw 2D figure.

### [mjr_render](#mjr_render)


mjr_render


Render 3D scene.

### [mjr_finish](#mjr_finish)


mjr_finish


Call glFinish.

### [mjr_getError](#mjr_getError)


mjr_getError


Call glGetError and return result.

### [mjr_findRect](#mjr_findRect)


mjr_findRect


Find first rectangle containing mouse, -1: not found.

## Filament rendering

Rendering functions using the Filament rendering engine. These functions are prefixed with `mjrf`. See `Filament Rendering<tyFilamentRenderStructure>` for an overview of the core types and their uses.

### [mjrf_defaultContextConfig](#mjrf_defaultContextConfig)


mjrf_defaultContextConfig


Initializes the mjrfContextConfig to default values.

### [mjrf_createContext](#mjrf_createContext)


mjrf_createContext


Creates a filament rendering context.

### [mjrf_destroyContext](#mjrf_destroyContext)


mjrf_destroyContext


Destroys the filament rendering context.

### [mjrf_getRendererInfo](#mjrf_getRendererInfo)


mjrf_getRendererInfo


Gets active renderer information for the given filament context.

### [mjrf_defaultShadowOpts](#mjrf_defaultShadowOpts)


mjrf_defaultShadowOpts


Initializes the mjrfShadowOpts to default values.

### [mjrf_defaultMaterialOpts](#mjrf_defaultMaterialOpts)


mjrf_defaultMaterialOpts


Initializes the mjrfMaterialOpts to default values.

### [mjrf_defaultHeadlightOpts](#mjrf_defaultHeadlightOpts)


mjrf_defaultHeadlightOpts


Initializes the mjrfHeadlightOpts to default values.

### [mjrf_defaultSkyboxOpts](#mjrf_defaultSkyboxOpts)


mjrf_defaultSkyboxOpts


Initializes the mjrfSkyboxOpts to default values.

### [mjrf_defaultHazeOpts](#mjrf_defaultHazeOpts)


mjrf_defaultHazeOpts


Initializes the mjrfHazeOpts to default values.

### [mjrf_defaultFogOpts](#mjrf_defaultFogOpts)


mjrf_defaultFogOpts


Initializes the mjrfFogOpts to default values.

### [mjrf_defaultBloomOpts](#mjrf_defaultBloomOpts)


mjrf_defaultBloomOpts


Initializes the mjrfBloomOpts to default values.

### [mjrf_defaultVignetteOpts](#mjrf_defaultVignetteOpts)


mjrf_defaultVignetteOpts


Initializes the mjrfVignetteOpts to default values.

### [mjrf_defaultReflectionOpts](#mjrf_defaultReflectionOpts)


mjrf_defaultReflectionOpts


Initializes the mjrfReflectionOpts to default values.

### [mjrf_defaultDepthOfFieldOpts](#mjrf_defaultDepthOfFieldOpts)


mjrf_defaultDepthOfFieldOpts


Initializes the mjrfDepthOfFieldOpts to default values.

### [mjrf_defaultDitheringOpts](#mjrf_defaultDitheringOpts)


mjrf_defaultDitheringOpts


Initializes the mjrfDitheringOpts to default values.

### [mjrf_defaultColorGradingOpts](#mjrf_defaultColorGradingOpts)


mjrf_defaultColorGradingOpts


Initializes the mjrfColorGradingOpts to default values.

### [mjrf_defaultAntialiasingOpts](#mjrf_defaultAntialiasingOpts)


mjrf_defaultAntialiasingOpts


Initializes the mjrfAntialiasingOpts to default values.

### [mjrf_defaultAmbientOcclusionOpts](#mjrf_defaultAmbientOcclusionOpts)


mjrf_defaultAmbientOcclusionOpts


Initializes the mjrfAmbientOcclusionOpts to default values.

### [mjrf_defaultRenderOpts](#mjrf_defaultRenderOpts)


mjrf_defaultRenderOpts


Initializes the mjrfRenderOpts to default values.

### [mjrf_modelRenderOpts](#mjrf_modelRenderOpts)


mjrf_modelRenderOpts


Configures the rendering options based on the parameters in an mjModel.

### [mjrf_defaultRenderRequest](#mjrf_defaultRenderRequest)


mjrf_defaultRenderRequest


Initializes the mjrfRenderRequest to default values.

### [mjrf_defaultReadRequest](#mjrf_defaultReadRequest)


mjrf_defaultReadRequest


Initializes the mjrfReadRequest to default values.

### [mjrf_render](#mjrf_render)


mjrf_render


Submits the given requests for rendering. Because rendering happens asynchronously, callers have to submit both the render and read requests in the same call. Multiple requests and reads can be submitted in a single call. These requests will be processed in order, so some care must be taken. Firstly, requests should be grouped by target. Next, the combined area of the viewports for all requests for a given target must be contained within the dimensions of the target itself.

Callbacks will be invoked from within this function, though there is no guarantee on which invocation of this function it will be done.

### [mjrf_waitForFrame](#mjrf_waitForFrame)


mjrf_waitForFrame


Waits for all rendering operations to complete for the given frame handle, triggering any callbacks as needed.

### [mjrf_flush](#mjrf_flush)


mjrf_flush


Flushes pending operations to the rendering backend and invokes any completed callbacks.

### [mjrf_setClearColor](#mjrf_setClearColor)


mjrf_setClearColor


Sets the clear color for the renderer.

### [mjrf_defaultFrameStats](#mjrf_defaultFrameStats)


mjrf_defaultFrameStats


Initializes the mjrFrameStats to default values.

### [mjrf_getFrameStats](#mjrf_getFrameStats)


mjrf_getFrameStats


Returns the stats for the given frame but updating the given <span class="title-ref">stats_out</span>.

### [mjrf_defaultTextureConfig](#mjrf_defaultTextureConfig)


mjrf_defaultTextureConfig


Initializes the mjrfTextureConfig to default values.

### [mjrf_createTexture](#mjrf_createTexture)


mjrf_createTexture


Creates a filament texture. Note that the texture will not be created on the GPU until <span class="title-ref">mjrf_uploadTexture()</span> is called.

### [mjrf_destroyTexture](#mjrf_destroyTexture)


mjrf_destroyTexture


Destroys the texture.

### [mjrf_defaultTextureData](#mjrf_defaultTextureData)


mjrf_defaultTextureData


Initializes the mjrfTextureData to default values.

### [mjrf_uploadTexture](#mjrf_uploadTexture)


mjrf_uploadTexture


Uploads the given texture data to the texture.

### [mjrf_getTextureWidth](#mjrf_getTextureWidth)


mjrf_getTextureWidth


Returns the width of the texture.

### [mjrf_getTextureHeight](#mjrf_getTextureHeight)


mjrf_getTextureHeight


Returns the height of the texture.

### [mjrf_getTextureSamplerType](#mjrf_getTextureSamplerType)


mjrf_getTextureSamplerType


Returns the sampler type (mjrSamplerType) used by the texture. \[returns: mjrSamplerType\]

### [mjrf_defaultMeshConfig](#mjrf_defaultMeshConfig)


mjrf_defaultMeshConfig


Initializes the mjrfMeshConfig to default values.

### [mjrf_createMesh](#mjrf_createMesh)


mjrf_createMesh


Creates an empty mesh with the given config.

### [mjrf_destroyMesh](#mjrf_destroyMesh)


mjrf_destroyMesh


Destroys the mesh.

### [mjrf_defaultMeshData](#mjrf_defaultMeshData)


mjrf_defaultMeshData


Initializes the mjrfMeshData to default values.

### [mjrf_uploadMesh](#mjrf_uploadMesh)


mjrf_uploadMesh


Uploads the given mesh data to the mesh.

### [mjrf_defaultSceneParams](#mjrf_defaultSceneParams)


mjrf_defaultSceneParams


Initializes the mjrfSceneParams to default values.

### [mjrf_createScene](#mjrf_createScene)


mjrf_createScene


Creates a scene with the given parameters.

### [mjrf_destroyScene](#mjrf_destroyScene)


mjrf_destroyScene


Destroys the scene.

### [mjrf_addSceneLight](#mjrf_addSceneLight)


mjrf_addSceneLight


Adds a light to the scene.

### [mjrf_removeSceneLight](#mjrf_removeSceneLight)


mjrf_removeSceneLight


Removes the light from the scene.

### [mjrf_addSceneRenderable](#mjrf_addSceneRenderable)


mjrf_addSceneRenderable


Adds a renderable to the scene.

### [mjrf_removeSceneRenderable](#mjrf_removeSceneRenderable)


mjrf_removeSceneRenderable


Removes the renderable from the scene.

### [mjrf_setSceneSkybox](#mjrf_setSceneSkybox)


mjrf_setSceneSkybox


Sets the skybox (cube texture) for the scene.

### [mjrf_configureSceneFromModel](#mjrf_configureSceneFromModel)


mjrf_configureSceneFromModel


Configures the scene based on the parameters in an mjModel.

### [mjrf_setSceneMsaa](#mjrf_setSceneMsaa)


mjrf_setSceneMsaa


Sets the number of multi-sample anti-aliasing samples; values \<= 1 disable MSAA.

### [mjrf_defaultLightParams](#mjrf_defaultLightParams)


mjrf_defaultLightParams


Initializes the mjrfLightParams to default values.

### [mjrf_createLight](#mjrf_createLight)


mjrf_createLight


Creates a light for the filament renderer.

### [mjrf_destroyLight](#mjrf_destroyLight)


mjrf_destroyLight


Destroys the light.

### [mjrf_setLightActive](#mjrf_setLightActive)


mjrf_setLightActive


Activates or deactivates the light.

### [mjrf_setLightCastShadow](#mjrf_setLightCastShadow)


mjrf_setLightCastShadow


Enables or disables whether or not the light casts shadows.

### [mjrf_setLightColor](#mjrf_setLightColor)


mjrf_setLightColor


Sets the RGB color of the light.

### [mjrf_setLightIntensity](#mjrf_setLightIntensity)


mjrf_setLightIntensity


Sets the intensity of the light, in candela.

### [mjrf_setLightRange](#mjrf_setLightRange)


mjrf_setLightRange


Sets the effective range of the light, in meters.

### [mjrf_setLightCutoff](#mjrf_setLightCutoff)


mjrf_setLightCutoff


Sets the cutoff angle of the light, in degrees. Only used for spot lights.

### [mjrf_setLightSoftness](#mjrf_setLightSoftness)


mjrf_setLightSoftness


Sets the softness of the light, in the range \[0, 1\]. Only used for spot lights.

### [mjrf_setLightBulbRadius](#mjrf_setLightBulbRadius)


mjrf_setLightBulbRadius


Sets the radius of the light bulb.

### [mjrf_setLightShadowMapSize](#mjrf_setLightShadowMapSize)


mjrf_setLightShadowMapSize


Sets the resolution of the light's shadow map, in texels.

### [mjrf_setLightPose](#mjrf_setLightPose)


mjrf_setLightPose


Sets the position and direction of the light.

### [mjrf_getLightType](#mjrf_getLightType)


mjrf_getLightType


Returns the type of the light (mjrLightType).

### [mjrf_defaultMaterial](#mjrf_defaultMaterial)


mjrf_defaultMaterial


Initializes the mjrfMaterial to default values.

### [mjrf_defaultRenderableParams](#mjrf_defaultRenderableParams)


mjrf_defaultRenderableParams


Initializes the mjrfRenderableParams to default values.

### [mjrf_createRenderable](#mjrf_createRenderable)


mjrf_createRenderable


Creates a renderable with the given parameters.

### [mjrf_destroyRenderable](#mjrf_destroyRenderable)


mjrf_destroyRenderable


Destroys the renderable.

### [mjrf_setRenderableMesh](#mjrf_setRenderableMesh)


mjrf_setRenderableMesh


Sets the mesh of the renderable.

### [mjrf_setRenderableGeomMesh](#mjrf_setRenderableGeomMesh)


mjrf_setRenderableGeomMesh


Sets the mesh of the renderable to a built-in mesh based on the geom type. Note: using the same parameters (nstack, nslice, nquad) will have better performance as the internal mesh data can be shared across renderables. \[type: mjtGeom\]

### [mjrf_setRenderableMaterial](#mjrf_setRenderableMaterial)


mjrf_setRenderableMaterial


Sets the material properties and textures of the renderable.

### [mjrf_getRenderableMaterial](#mjrf_getRenderableMaterial)


mjrf_getRenderableMaterial


Copies the material properties of the renderable into the given mjrfMaterial.

### [mjrf_setRenderablePose](#mjrf_setRenderablePose)


mjrf_setRenderablePose


Sets the position and rotation of the renderable.

### [mjrf_setRenderableSize](#mjrf_setRenderableSize)


mjrf_setRenderableSize


Sets the size of the renderable. Note that, for most renderables, this is equivalent to setting the scale. However, for some geom-based renderables, the size scale is not applied uniformly (e.g. the spherical ends of a capsule are scaled such that they always remain spherical).

### [mjrf_setRenderableCastShadow](#mjrf_setRenderableCastShadow)


mjrf_setRenderableCastShadow


Enables or disables whether or not the renderable casts shadows.

### [mjrf_defaultRenderTargetConfig](#mjrf_defaultRenderTargetConfig)


mjrf_defaultRenderTargetConfig


Initializes the mjrfRenderTargetConfig to default values.

### [mjrf_createRenderTarget](#mjrf_createRenderTarget)


mjrf_createRenderTarget


Creates a render target for the filament renderer.

### [mjrf_destroyRenderTarget](#mjrf_destroyRenderTarget)


mjrf_destroyRenderTarget


Destroys the render target.

### [mjrf_resizeRenderTarget](#mjrf_resizeRenderTarget)


mjrf_resizeRenderTarget


Resizes the render target to the given width and height.

## UI framework

For a high-level description of the UI framework, see `UI`.

### [mjui_themeSpacing](#mjui_themeSpacing)


mjui_themeSpacing


Get builtin UI theme spacing (ind: 0-1).

### [mjui_themeColor](#mjui_themeColor)


mjui_themeColor


Get builtin UI theme color (ind: 0-3).

### [mjui_add](#mjui_add)


mjui_add


This is the helper function used to construct a UI. The second argument points to an array of `mjuiDef` structs, each corresponding to one item. The last (unused) item has its type set to -1, to mark termination. The items are added after the end of the last used section. There is also another version of this function (`mjui_addToSection<mjui_addToSection>`) which adds items to a specified section instead of adding them at the end of the UI. Keep in mind that there is a maximum preallocated number of sections and items per section, given by `mjMAXUISECT<glNumericUI>` and `mjMAXUIITEM<glNumericUI>`. Exceeding these maxima results in low-level errors.

### [mjui_addToSection](#mjui_addToSection)


mjui_addToSection


Add definitions to UI section.

### [mjui_resize](#mjui_resize)


mjui_resize


Compute UI sizes.

### [mjui_update](#mjui_update)


mjui_update


This is the main UI update function. It needs to be called whenever the user data (pointed to by the item data pointers) changes, or when the UI state itself changes. It is normally called by a higher-level function implemented by the user (`UiModify` in `simulate.cc <saSimulate>`) which also recomputes the layout of all rectangles and associated auxiliary buffers. The function updates the pixels in the offscreen OpenGL buffer. To perform minimal updates, the user specifies the section and the item that was modified. A value of -1 means all items and/or sections need to be updated (which is needed following major changes.)

### [mjui_event](#mjui_event)


mjui_event


This function is the low-level event handler. It makes the necessary changes in the UI and returns a pointer to the item that received the event (or `NULL` if no valid event was recorded). This is normally called within the event handler implemented by the user (`UiEvent` in `simulate.cc <saSimulate>`), and then some action is taken by user code depending on which UI item was modified and what the state of that item is after the event is handled.

### [mjui_render](#mjui_render)


mjui_render


This function is called in the screen refresh loop. It copies the offscreen OpenGL buffer to the window framebuffer. If there are multiple UIs in the application, it should be called once for each UI. Thus `mjui_render` is called all the time, while `mjui_update` is called only when changes in the UI take place. dsffsdg

## Derivatives

The functions below provide useful derivatives of various functions, both analytic and finite-differenced. The latter have names with the suffix `FD`. Note that unlike much of the API, outputs of derivative functions are the trailing rather than leading arguments.

### [mjd_transitionFD](#mjd_transitionFD)


mjd_transitionFD


Compute finite-differenced discrete-time transition matrices.

Letting $`x, u`$ denote the current `state<siPhysicsState>` and `control<siInput>` vector in an mjData instance, and letting $`y, s`$ denote the next state and sensor values, the top-level `mj_step` function computes $`(x,u) \rightarrow (y,s)`$ `mjd_transitionFD` computes the four associated Jacobians using finite-differencing. These matrices and their dimensions are:

| matrix | Jacobian                    | dimension               |
|--------|-----------------------------|-------------------------|
| `A`    | $`\partial y / \partial x`$ | `2*nv+na x 2*nv+na`     |
| `B`    | $`\partial y / \partial u`$ | `2*nv+na x nu`          |
| `C`    | $`\partial s / \partial x`$ | `nsensordata x 2*nv+na` |
| `D`    | $`\partial s / \partial u`$ | `nsensordata x nu`      |

- All outputs are optional (can be NULL).
- `eps` is the finite-differencing epsilon.
- `flg_centered` denotes whether to use forward (0) or centered (1) differences.
- The Runge-Kutta integrator (`mjINT_RK4<mjtIntegrator>`) is not supported.
- `Sleeping<Sleeping>` is not supported. Disable the `sleep<option-flag-sleep>` flag before calling.
- `Delays<CDelay>` are not supported.


Improving speed and accuracy

warmstart  
If warm-starts are not `disabled<option-flag-warmstart>`, the warm-start accelerations `mjData.qacc_warmstart` which are present at call-time are loaded at the start of every relevant pipeline call, to preserve determinism. If solver computations are an expensive part of the simulation, the following trick can lead to significant speed-ups: First call `mj_forward` to let the solver converge, then reduce `solver
iterations<option-iterations>` significantly, then call `mjd_transitionFD`, finally, restore the original value of `iterations<option-iterations>`. Because we are already near the solution, few iteration are required to find the new minimum. This is especially true for the `Newton<option-solver>` solver, where the required number of iteration for convergence near the minimum can be as low as 1.

tolerance  
Accuracy can be improved if solver `tolerance<option-tolerance>` is set to 0. This means that all calls to the solver will perform exactly the same number of iterations, preventing numerical errors due to early termination. Of course, this means that `solver iterations<option-iterations>` should be small, to not tread water at the minimum. This method and the one described above can and should be combined.


*Nullable:* `A`, `B`, `D`, `C`

### [mjd_inverseFD](#mjd_inverseFD)


mjd_inverseFD


Finite differenced continuous-time inverse-dynamics Jacobians.

Letting $`x, a`$ denote the current `state<siPhysicsState>` and acceleration vectors in an mjData instance, and letting $`f, s`$ denote the forces computed by the inverse dynamics (`qfrc_inverse`), the function `mj_inverse` computes $`(x,a) \rightarrow (f,s)`$. `mjd_inverseFD` computes seven associated Jacobians using finite-differencing. These matrices and their dimensions are:

| matrix | Jacobian                    | dimension          |
|--------|-----------------------------|--------------------|
| `DfDq` | $`\partial f / \partial q`$ | `nv x nv`          |
| `DfDv` | $`\partial f / \partial v`$ | `nv x nv`          |
| `DfDa` | $`\partial f / \partial a`$ | `nv x nv`          |
| `DsDq` | $`\partial s / \partial q`$ | `nv x nsensordata` |
| `DsDv` | $`\partial s / \partial v`$ | `nv x nsensordata` |
| `DsDa` | $`\partial s / \partial a`$ | `nv x nsensordata` |
| `DmDq` | $`\partial M / \partial q`$ | `nv x nC`          |

- All outputs are optional (can be NULL).
- All outputs are transposed relative to Control Theory convention (i.e., column major).
- `DmDq`, which contains a sparse representation of the `nv x nv x nv` tensor $`\partial M / \partial q`$, is not strictly an inverse dynamics Jacobian but is useful in related applications. It is provided as a convenience to the user, since the required values are already computed if either of the other two $`\partial / \partial q`$ Jacobians are requested.
- `eps` is the (forward) finite-differencing epsilon.
- `flg_actuation` denotes whether to subtract actuation forces (`qfrc_actuator`) from the output of the inverse dynamics. If this flag is positive, actuator forces are not considered as external.
- The model option flag `invdiscrete` should correspond to the representation of `mjData.qacc` in order to compute the correct derivative information.



Attention


\- The Runge-Kutta 4th-order integrator (`mjINT_RK4`) is not supported. - The noslip solver is not supported. - `Sleeping<Sleeping>` is not supported. Disable the `sleep<option-flag-sleep>` flag before calling.


*Nullable:* `DfDq`, `DfDv`, `DfDa`, `DsDq`, `DsDv`, `DsDa`, `DmDq`

### [mjd_subQuat](#mjd_subQuat)


mjd_subQuat


Derivatives of `mju_subQuat` (quaternion difference).

*Nullable:* `Da`, `Db`

### [mjd_quatIntegrate](#mjd_quatIntegrate)


mjd_quatIntegrate


Derivatives of `mju_quatIntegrate`.

$`{\tt \small mju\_quatIntegrate}(q, v, h)`$ performs the in-place rotation $`q \leftarrow q + v h`$, where $`q \in \mathbf{S}^3`$ is a unit quaternion, $`v \in \mathbf{R}^3`$ is a 3D angular velocity and $`h \in \mathbf{R^+}`$ is a timestep. This is equivalent to $`{\tt \small mju\_quatIntegrate}(q, s, 1.0)`$, where $`s`$ is the scaled velocity $`s = h v`$.

$`{\tt \small mjd\_quatIntegrate}(v, h, D_q, D_v, D_h)`$ computes the Jacobians of the output $`q`$ with respect to the inputs. Below, $`\bar q`$ denotes the pre-modified quaternion:

``` math
\begin{aligned}
\begin{aligned}
D_q &= \partial q / \partial \bar q \\
D_v &= \partial q / \partial v \\
D_h &= \partial q / \partial h
\end{aligned}
\end{aligned}
```

Note that derivatives depend only on $`h`$ and $`v`$ (in fact, on $`s = h v`$). All outputs are optional.

*Nullable:* `Dquat`, `Dvel`, `Dscale`

## Signed Distance Functions

### [mjc_getSDF](#mjc_getSDF)


mjc_getSDF


get sdf from geom id

### [mjc_distance](#mjc_distance)


mjc_distance


signed distance function

### [mjc_gradient](#mjc_gradient)


mjc_gradient


gradient of sdf

## Plugins

### [mjp_defaultPlugin](#mjp_defaultPlugin)


mjp_defaultPlugin


Set default plugin definition.

### [mjp_registerPlugin](#mjp_registerPlugin)


mjp_registerPlugin


Globally register a plugin. This function is thread-safe.

If an identical mjpPlugin is already registered, this function does nothing.

If a non-identical mjpPlugin with the same name is already registered, an mju_error is raised.

Two mjpPlugins are considered identical if all member function pointers and numbers are equal, and the name and attribute strings are all identical, however the char pointers to the strings need not be the same.

### [mjp_pluginCount](#mjp_pluginCount)


mjp_pluginCount


Return the number of globally registered plugins.

### [mjp_getPlugin](#mjp_getPlugin)


mjp_getPlugin


Look up a plugin by name. If slot is not NULL, also write its registered slot number into it.

### [mjp_getPluginAtSlot](#mjp_getPluginAtSlot)


mjp_getPluginAtSlot


Look up a plugin by the registered slot number that was returned by mjp_registerPlugin.

### [mjp_defaultProvider](#mjp_defaultProvider)


mjp_defaultProvider


Set default provider definition.

### [mjp_registerProvider](#mjp_registerProvider)


mjp_registerProvider


Globally register a provider in a thread-safe manner. The provider must have a prefix that is not a sub-prefix or super-prefix of any current registered providers.

Return a slot number \>= 0 on success, -1 on failure.

### [mjp_providerCount](#mjp_providerCount)


mjp_providerCount


Return the number of globally registered providers.

### [mjp_findProvider](#mjp_findProvider)


mjp_findProvider


Return the provider with the prefix that matches against the resource name.

If no match, return NULL.

### [mjp_getProviderAtSlot](#mjp_getProviderAtSlot)


mjp_getProviderAtSlot


Look up a provider by slot number returned by mjp_registerProvider.

If invalid slot number, return NULL.

### [mjp_registerDecoder](#mjp_registerDecoder)


mjp_registerDecoder


Globally register a decoder. This function is thread-safe.

If an identical mjpDecoder is already registered, this function does nothing.

If a non-identical mjpDecoder with the same name is already registered, an mju_error is raised.

### [mjp_defaultDecoder](#mjp_defaultDecoder)


mjp_defaultDecoder


Set default resource decoder definition.

### [mjp_findDecoder](#mjp_findDecoder)


mjp_findDecoder


Return the decoder that matches against the resource or content type.

If no match, return NULL.

### [mjp_registerEncoder](#mjp_registerEncoder)


mjp_registerEncoder


Globally register an encoder. This function is thread-safe.

If an identical mjpEncoder is already registered, this function does nothing.

If a non-identical mjpEncoder with the same name is already registered, an mju_error is raised.

### [mjp_defaultEncoder](#mjp_defaultEncoder)


mjp_defaultEncoder


Set default resource encoder definition.

### [mjp_findEncoder](#mjp_findEncoder)


mjp_findEncoder


Return the encoder that matches against the content type or filename extension.

If no match, return NULL.

### [mjp_registerArchiveProvider](#mjp_registerArchiveProvider)


mjp_registerArchiveProvider


Globally register an archive provider. This function is thread-safe. provider-\>prefix specifies the filename extension(s) (e.g. .mjz\|.zip).

### [mjp_findArchiveProvider](#mjp_findArchiveProvider)


mjp_findArchiveProvider


Return the archive provider that matches against the resource name.

If no match, return NULL.

### [mjp_archiveProviderCount](#mjp_archiveProviderCount)


mjp_archiveProviderCount


Return the number of globally registered archive providers.

## Threads

### [mju_threadpool](#mju_threadpool)


mju_threadpool


Create a thread pool with nthread worker threads.

## Batched simulation

Functions for running many simulations of one model on a thread pool, declared in `mujoco/mjbatch.h`. See `Batched simulation<siBatch>` for an overview and an example.

The functions that run simulations take a selection: `ids` holds `nid` sorted, unique simulation indices, or is `NULL` to select every simulation, in which case `nid` is ignored. They return the number of simulations in which MuJoCo raised an error. Those simulations keep the state they had before the call, and the others run to completion. `mjb_status` and `mjb_error` report the outcome of each simulation's last call.

Invalid arguments, such as unsorted `ids` or an unknown `stage`, are a different kind of error: the function raises it with `mju_error` on the caller's thread, before any simulation runs, and it is not counted in the return value.

Errors in simulations are trapped by a thread-local log handler. Therefore, `physics callbacks<glPhysics>`, engine plugins and functions run by `mjb_apply` must not raise errors with `mju_error` or throw exceptions. Other messages, such as warnings, go to the log handler the thread would use anyway. On the batch's threads this is the `global handler<mju_setLogHandler>`. On the caller's thread it can also be a thread-local handler, such as the one the Python bindings install. Either way, the counters of `mjb_warning` count every simulation's warnings.

The arrays that the batch returns, such as the state rows, outputs and expanded fields, are owned by the batch. They stay at the same address until `mjb_deleteBatch` frees them.

Timers (`mjData.timer`, see `mjTimerStat`) are not part of the state. In a persistent batch, each simulation's mjData times that simulation, and `mjb_getData` copies its timers. Otherwise, each thread's mjData accumulates the timing of every simulation the thread runs, until a reset of one of them clears it. These timers profile the batch as a whole rather than any one simulation.

### [mjb_defaultConfig](#mjb_defaultConfig)


mjb_defaultConfig


Set the default `mjBatchConfig` parameters: one thread per logical CPU, and one mjData per thread. Call it first, then change the parameters you need.

### [mjb_makeBatch](#mjb_makeBatch)


mjb_makeBatch


Allocate a batch of `nsim` simulations of a copy of `m`, and return it. `config` holds the `mjBatchConfig` parameters; if it is `NULL`, the defaults of `mjb_defaultConfig` apply. If the model cannot be batched, or making an mjData raises an error, return `NULL` and write the reason into `error`, a buffer of `error_sz` bytes.

The batch runs on `config->nthread` threads, including the caller's. If `nthread <= 0`, it uses one thread per logical CPU. Either way, it uses at most `nsim` threads. The number of logical CPUs is the machine's, which can exceed what the process may use, for example in a container; set `nthread` explicitly there.

If `config->persistent` is nonzero, the batch keeps one mjData per simulation instead of one per thread. Models with `sleep<option-flag-sleep>` or `IPC<option-flag-ipc>` enabled require this. In a batch that is not persistent, `engine plugins<exPlugin>` that keep state outside `plugin_state` share that state among the simulations a thread runs.

### [mjb_deleteBatch](#mjb_deleteBatch)


mjb_deleteBatch


Free the batch, its threads, and every array it returned. `b` may be `NULL`. A function run by `mjb_apply` must not delete its own batch.

### [mjb_nstate](#mjb_nstate)


mjb_nstate


Return size of a state row: mj_stateSize(m, mjSTATE_INTEGRATION).

### [mjb_state](#mjb_state)


mjb_state


Return the state rows, `nsim x nstate`. Row `i` is simulation `i`'s `integration state<siIntegrationState>`, in `mj_getState` order. Writing to a row sets the simulation's state for its next call, which then overwrites the row with the new state.

### [mjb_stateComponent](#mjb_stateComponent)


mjb_stateComponent


Return the address of state component `component` (one bit of `mjtState`) in the first state row, and write its number of elements into `size`. Simulation `i`'s component is `mjb_nstate(b) * i` elements further on. Raise an error if `component` is not one bit of `mjSTATE_INTEGRATION`.

### [mjb_warning](#mjb_warning)


mjb_warning


Return the warning counters, `nsim x mjNWARNING` `mjWarningStat` ⁠ s. They are saved and restored with the state.

### [mjb_step](#mjb_step)


mjb_step


Advance each selected simulation by `nstep` calls to `mj_step`, then compute the stages of `mj_forward` up to `stage` (an `mjtStage`) at the new state. Return the number of simulations in which MuJoCo raised an error.

As with `mj_step`, derived fields after the steps describe the state before the last substep. `stage` brings them up to date:

- `mjSTAGE_NONE` leaves them as `mj_step` does.
- `mjSTAGE_VEL` makes position- and velocity-dependent fields and sensors current, as `mj_step1` does. Acceleration-dependent fields remain those of the last substep, under the controls it applied.
- `mjSTAGE_ACC` runs `mj_forward`, at nearly the cost of another step. Its acceleration-dependent values use controls that the next step will replace.

In a persistent batch, a simulation's next step continues from these stages with `mj_step2`, so `mjSTAGE_VEL` costs nothing extra. The step does not continue if anything the stages depend on changed in between, other than `ctrl`, `qfrc_applied` and `xfrc_applied`; the results are the same either way. As with `mj_step1` and `mj_step2`, this assumes that plugins do not make the position and velocity stages depend on those inputs. A loop of `mj_forward` and `mj_step` computes these stages twice at the same state, while a continued step computes them once; this matters only to plugins whose computations have side effects. Installed `physics
callbacks<glPhysics>` turn the continuation off, but removing one between a call and the next step is not detected. A continued step counts as one step in `mjData.timer`, but its `mjTIMER_STEP` duration excludes the position and velocity stages, which are timed in the call that computed them.

### [mjb_forward](#mjb_forward)


mjb_forward


Compute the stages of `mj_forward` up to `stage` (an `mjtStage`) on each selected simulation. `mjSTAGE_ACC` runs `mj_forward`. Return the number of simulations in which MuJoCo raised an error.

### [mjb_reset](#mjb_reset)


mjb_reset


Reset each selected simulation, then compute the stages of `mj_forward` up to `stage` (an `mjtStage`). Return the number of simulations in which MuJoCo raised an error.

`key` holds one keyframe per selected simulation, in call order; a keyframe of -1, or a `NULL` `key`, resets to the model's defaults. `mjSTAGE_ACC` runs `mj_forward`. `mjSTAGE_NONE` suits a reset that is followed by writes to the state and `mjb_forward`. Writes to the state rows made before the call are discarded.

### [mjb_status](#mjb_status)


mjb_status


Return the status of each simulation's last call: `nsim` values, nonzero where MuJoCo raised an error. Each call updates the values of the simulations it runs.

### [mjb_error](#mjb_error)


mjb_error


Return the error message of simulation `sim`'s last call, or `""` if there was none. The string remains valid until the next call on the simulation.

### [mjb_output](#mjb_output)


mjb_output


Register `mjData` field `name` as an output, and return its storage: `nsim x size` elements of the field's type. Write the number of elements per simulation into `size` and the element size in bytes into `elemsize`. After every call on a simulation except `mjb_apply`, the batch copies the field from the simulation's mjData into its row of the storage. Registering a field again returns the same storage.

`name` can be an array field, or one of the counts `ncon`, `ne`, `nf`, `nl`, `nefc`, `nJ`, `nA`, `nisland` and `nidof`. Return `NULL` for unknown fields, and for fields of the state row, which `mjb_state` already holds.

In a persistent batch, the storage starts with each simulation's current values. Otherwise, it is zero until the next call on a simulation, and a field that the call does not compute holds another simulation's value. Examples are `qfrc_inverse` after `mj_step`, quantities computed only for the sensors that need them, and fields of stages above the call's `stage`.

### [mjb_expand](#mjb_expand)


mjb_expand


Give `mjModel` field `name` per-simulation values, and return their storage: `nsim x size` elements of the field's type, initialized from the model. Before each call on a simulation, the batch copies the simulation's row into its model. `size` and `elemsize` are written as by `mjb_output`. Expanding a field again returns the same storage.

Array fields are named as in `mjModel`, and `mjOption` fields as `"opt.<name>"`. The storage of `bvh_aabb` holds only the bodies' bounding volumes, which come before the meshes'. Return `NULL` for unknown fields and for asset fields (meshes, heightfields, textures, skins), which all simulations share.

Writing a field that `mj_setConst` reads, an input in `MJSETCONST_ARRAYS` of `mjxmacro.h` or an `mjOption` field, does not update the constants derived from it until `mjb_setConst` runs.

Expanding a field that `mjb_setConst` expanded makes it an input of later calls to `mjb_setConst`, if `mj_setConst` reads it before writing it. To read such a field without that effect, use `mjb_expanded`.

### [mjb_expanded](#mjb_expanded)


mjb_expanded


Return the per-simulation storage of `mjModel` field `name` if it is expanded, by `mjb_expand` or by `mjb_setConst`. Otherwise, return `NULL`: every simulation has the model's value. Unlike `mjb_expand`, this expands nothing, and fields that `mjb_setConst` derives stay derived. Treat the storage as read-only, since `mjb_setConst` overwrites derived fields. `size` and `elemsize` are written as by `mjb_expand`, also when the field is not expanded.

### [mjb_setConst](#mjb_setConst)


mjb_setConst


Run `mj_setConst` on each selected simulation's model. Return the number of simulations in which MuJoCo raised an error; those simulations keep their constants.

Every model field that `mj_setConst` changes becomes per-simulation, as with `mjb_expand`, so each simulation gets its own derived constants; only the arrays marked `mjSC_OUT` in `MJSETCONST_ARRAYS` and the scalars in `MJSETCONST_SCALARS` can change. If a call makes a new field per-simulation, `mj_setConst` runs again on the call's simulations. Simulations outside the call need no update, since the new field starts from the model's value, which is theirs.

Only the groups of `mj_setConst` computations (the columns of `MJSETCONST_ARRAYS`) that read a per-simulation field, or what an earlier such group writes, run; the others would give every simulation the model's values. With no per-simulation field that `mj_setConst` reads, for example only friction or actuator gains, the call does nothing. Per-simulation `mjOption` fields count as read by every group. Skipping groups assumes that the constants of the model given to `mjb_makeBatch` are current, as after compilation or `mj_setConst`.

On each call, the fields that `mj_setConst` derives are recomputed from the model's values. Expanding such a field with `mjb_expand` makes its values inputs instead if `mj_setConst` reads it before writing it, as the anchors of connect constraints are in `eq_data`; otherwise they are recomputed all the same. `mjb_expanded` reads them without that effect.

### [mjb_setModels](#mjb_setModels)


mjb_setModels


Run each simulation `i` on `models[i]`, a model of the caller's, instead of the batch's model. If `models` is `NULL`, return to the batch's model.

Each model must give mjData the same layout as the batch's model, that is, the same sizes for everything mjData holds. Models compiled from one spec with different parameters qualify, and so do models whose meshes have other shapes but the same numbers of vertices and faces. The batch only reads the models, so one model can serve several simulations. After editing a model, call `mjb_setModels` again; otherwise a persistent batch may continue a step from stages computed before the edit.

Caller models replace per-simulation fields, and the two cannot be combined: raise an error if the batch has fields from `mjb_expand`. While caller models are set:

- `mjb_expand` and `mjb_setConst` raise an error.
- Keyframes are those of each simulation's model.
- `mjb_getModel` copies the simulation's model.

### [mjb_rollout](#mjb_rollout)


mjb_rollout


Advance each selected simulation by `nstep` calls to `mj_step`, as `rollout<PyRollout>` does, recording after each substep. Return the number of simulations in which MuJoCo raised an error.

Before each substep, set the state components in `control_spec` (a subset of the `mjtState` bits in `mjSTATE_USER`) from `control`. `control` is `n x nstep x mj_stateSize(m, control_spec)`, for the `n` selected simulations in call order; if it is `NULL`, the inputs are left as they are. After each substep, copy each of the `nrecord` `mjBatchRecord` ⁠ s in `record` into its buffer. A simulation whose warning counters rise stops stepping, and its remaining records repeat its last ones.

### [mjb_apply](#mjb_apply)


mjb_apply


Run `func` (an `mjfBatchFunc`) on each selected simulation's model and data, on the batch's threads, passing it the simulation's index and `arg`. If `save` is nonzero, save the state back afterwards. Return the number of simulations in which MuJoCo raised an error.

Fields registered with `mjb_output` are not refreshed; `func` returns its results through `arg`. `func` may call other batches, as long as they do not call back into this one; a call on its own batch raises an error in the simulation. An error raised by a MuJoCo function that `func` calls unwinds to the batch with `longjmp`, so `func` must not hold C++ objects with destructors across MuJoCo calls.

In a persistent batch:

- With `save` zero, `func` should not change the simulation's state. The mjData keeps what lies outside the state, such as the sleep bookkeeping, which would then no longer match the row.
- The mjData that `func` receives may hold the stages that `mjb_step` computed at the new state. Its contacts are then those of the new state, but its constraint forces are not yet computed, so do not read contact forces before the acceleration stage runs.

For example, this computes the finite-differenced transition matrices of every simulation at its current state, into arrays indexed by simulation. `mjd_transitionFD` restores the state it perturbs, so `save` is zero:

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

A function can also read one field of one simulation. The mjData it receives holds the simulation's state, but in a batch that is not persistent its derived fields belong to another simulation, so the function computes what it reads. In a persistent batch, it can instead read the fields that the simulation's last call left in its mjData:

``` C
// mjb_apply function: subtree centers of mass, into arg (3*nbody)
void SubtreeCom(const mjModel* m, mjData* d, int sim, void* arg) {
  mj_kinematics(m, d);
  mj_comPos(m, d);
  mju_copy(arg, d->subtree_com, 3*m->nbody);
}

int sim = 7;
mjb_apply(b, &sim, 1, SubtreeCom, com, /*save=*/0);
```

### [mjb_getModel](#mjb_getModel)


mjb_getModel


Write simulation `sim`'s model into `m`, ready to render or to pass to any function. Normally, this is the batch's model with the simulation's per-simulation fields and the constants `mjb_setConst` computed for it; `m` must then have the batch's sizes, such as a copy of `mjb_model`. With caller models from `mjb_setModels`, it is a copy of the simulation's model, and `m` must have that model's sizes. Raise an error if `sim` is out of range or the sizes differ.

### [mjb_getData](#mjb_getData)


mjb_getData


Write simulation `sim`'s state and warning counters into `d`, including writes to its row since its last call; `d` must have the batch's sizes. In a persistent batch, first copy the simulation's mjData, so that `d` also holds its derived fields and sleep state. Otherwise, run `mj_forward` with the model from `mjb_getModel` to compute them. Raise an error if `sim` is out of range or the sizes differ.

### [mjb_nsim](#mjb_nsim)


mjb_nsim


Return number of simulations.

### [mjb_nthread](#mjb_nthread)


mjb_nthread


Return number of threads, including the caller's.

### [mjb_persistent](#mjb_persistent)


mjb_persistent


Return 1 if the batch keeps one mjData per simulation, 0 otherwise.

### [mjb_model](#mjb_model)


mjb_model


Return the batch's copy of the model, made by `mjb_makeBatch`. Per-simulation fields and caller models never change it; `mjb_getModel` gives a simulation's own model.

## Standard math

The "functions" in this section are preprocessor macros replaced with the corresponding C standard library math functions. When MuJoCo is compiled with single precision (which is not currently available to the public, but we sometimes use it internally) these macros are replaced with the corresponding single-precision functions (not shown here). So one can think of them as having inputs and outputs of type mjtNum, where mjtNum is defined as double or float depending on how MuJoCo is compiled. We will not document these functions here; see the C standard library specification.

### mju_sqrt

``` C
#define mju_sqrt    sqrt
```

### mju_exp

``` C
#define mju_exp     exp
```

### mju_sin

``` C
#define mju_sin     sin
```

### mju_cos

``` C
#define mju_cos     cos
```

### mju_tan

``` C
#define mju_tan     tan
```

### mju_asin

``` C
#define mju_asin    asin
```

### mju_acos

``` C
#define mju_acos    acos
```

### mju_atan2

``` C
#define mju_atan2   atan2
```

### mju_tanh

``` C
#define mju_tanh    tanh
```

### mju_pow

``` C
#define mju_pow     pow
```

### mju_abs

``` C
#define mju_abs     fabs
```

### mju_log

``` C
#define mju_log     log
```

### mju_log10

``` C
#define mju_log10   log10
```

### mju_floor

``` C
#define mju_floor   floor
```

### mju_ceil

``` C
#define mju_ceil    ceil
```

## Vector math

### [mju_zero3](#mju_zero3)


mju_zero3


Set res = 0.

### [mju_copy3](#mju_copy3)


mju_copy3


Set res = vec.

### [mju_scl3](#mju_scl3)


mju_scl3


Set res = vec\*scl.

### [mju_add3](#mju_add3)


mju_add3


Set res = vec1 + vec2.

### [mju_sub3](#mju_sub3)


mju_sub3


Set res = vec1 - vec2.

### [mju_addTo3](#mju_addTo3)


mju_addTo3


Set res = res + vec.

### [mju_subFrom3](#mju_subFrom3)


mju_subFrom3


Set res = res - vec.

### [mju_addToScl3](#mju_addToScl3)


mju_addToScl3


Set res = res + vec\*scl.

### [mju_addScl3](#mju_addScl3)


mju_addScl3


Set res = vec1 + vec2\*scl.

### [mju_normalize3](#mju_normalize3)


mju_normalize3


Normalize vector; return length before normalization.

### [mju_norm3](#mju_norm3)


mju_norm3


Return vector length (without normalizing the vector).

### [mju_dot3](#mju_dot3)


mju_dot3


Return dot-product of vec1 and vec2.

### [mju_dist3](#mju_dist3)


mju_dist3


Return Cartesian distance between 3D vectors pos1 and pos2.

### [mju_mulMatVec3](#mju_mulMatVec3)


mju_mulMatVec3


Multiply 3-by-3 matrix by vector: res = mat \* vec.

### [mju_mulMatTVec3](#mju_mulMatTVec3)


mju_mulMatTVec3


Multiply transposed 3-by-3 matrix by vector: res = mat' \* vec.

### [mju_cross](#mju_cross)


mju_cross


Compute cross-product: res = cross(a, b).

### [mju_zero4](#mju_zero4)


mju_zero4


Set res = 0.

### [mju_unit4](#mju_unit4)


mju_unit4


Set res = (1,0,0,0).

### [mju_copy4](#mju_copy4)


mju_copy4


Set res = vec.

### [mju_normalize4](#mju_normalize4)


mju_normalize4


Normalize vector; return length before normalization.

### [mju_zero](#mju_zero)


mju_zero


Set res = 0.

### [mju_fill](#mju_fill)


mju_fill


Set res = val.

### [mju_copy](#mju_copy)


mju_copy


Set res = vec.

### [mju_sum](#mju_sum)


mju_sum


Return sum(vec).

### [mju_L1](#mju_L1)


mju_L1


Return L1 norm: sum(abs(vec)).

### [mju_scl](#mju_scl)


mju_scl


Set res = vec\*scl.

### [mju_add](#mju_add)


mju_add


Set res = vec1 + vec2.

### [mju_sub](#mju_sub)


mju_sub


Set res = vec1 - vec2.

### [mju_addTo](#mju_addTo)


mju_addTo


Set res = res + vec.

### [mju_subFrom](#mju_subFrom)


mju_subFrom


Set res = res - vec.

### [mju_addToScl](#mju_addToScl)


mju_addToScl


Set res = res + vec\*scl.

### [mju_addScl](#mju_addScl)


mju_addScl


Set res = vec1 + vec2\*scl.

### [mju_normalize](#mju_normalize)


mju_normalize


Normalize vector; return length before normalization.

### [mju_norm](#mju_norm)


mju_norm


Return vector length (without normalizing vector).

### [mju_dot](#mju_dot)


mju_dot


Return dot-product of vec1 and vec2.

### [mju_mulMatVec](#mju_mulMatVec)


mju_mulMatVec


Multiply matrix and vector: res = mat \* vec.

### [mju_mulMatTVec](#mju_mulMatTVec)


mju_mulMatTVec


Multiply transposed matrix and vector: res = mat' \* vec.

### [mju_mulVecMatVec](#mju_mulVecMatVec)


mju_mulVecMatVec


Multiply square matrix with vectors on both sides: return vec1' \* mat \* vec2.

### [mju_transpose](#mju_transpose)


mju_transpose


Transpose matrix: res = mat'.

### [mju_symmetrize](#mju_symmetrize)


mju_symmetrize


Symmetrize square matrix $`R = \frac{1}{2}(M + M^T)`$.

### [mju_eye](#mju_eye)


mju_eye


Set mat to the identity matrix.

### [mju_mulMatMat](#mju_mulMatMat)


mju_mulMatMat


Multiply matrices: res = mat1 \* mat2.

### [mju_mulMatMatT](#mju_mulMatMatT)


mju_mulMatMatT


Multiply matrices, second argument transposed: res = mat1 \* mat2'.

### [mju_mulMatTMat](#mju_mulMatTMat)


mju_mulMatTMat


Multiply matrices, first argument transposed: res = mat1' \* mat2.

### [mju_sqrMatTD](#mju_sqrMatTD)


mju_sqrMatTD


Set res = mat' \* diag \* mat if diag is not NULL, and res = mat' \* mat otherwise.

### [mju_transformSpatial](#mju_transformSpatial)


mju_transformSpatial


Coordinate transform of 6D motion or force vector in rotation:translation format. rotnew2old is 3-by-3, NULL means no rotation; flg_force specifies force or motion type.

*Nullable:* `rotnew2old`

## Sparse math

### [mju_dense2sparse](#mju_dense2sparse)


mju_dense2sparse


Convert matrix from dense to sparse.  
nnz is size of res and colind; return 1 if too small, 0 otherwise.

### [mju_sparse2dense](#mju_sparse2dense)


mju_sparse2dense


Convert matrix from sparse to dense.

### [mju_sym2dense](#mju_sym2dense)


mju_sym2dense


Convert lower-triangular symmetric CSR matrix to full dense matrix.

## Quaternions

### [mju_rotVecQuat](#mju_rotVecQuat)


mju_rotVecQuat


Rotate vector by quaternion.

### [mju_negQuat](#mju_negQuat)


mju_negQuat


Conjugate quaternion, corresponding to opposite rotation.

### [mju_mulQuat](#mju_mulQuat)


mju_mulQuat


Multiply quaternions.

### [mju_mulQuatAxis](#mju_mulQuatAxis)


mju_mulQuatAxis


Multiply quaternion and axis.

### [mju_axisAngle2Quat](#mju_axisAngle2Quat)


mju_axisAngle2Quat


Convert axisAngle to quaternion.

### [mju_quat2Vel](#mju_quat2Vel)


mju_quat2Vel


Convert quaternion (corresponding to orientation difference) to 3D velocity.

### [mju_subQuat](#mju_subQuat)


mju_subQuat


Subtract quaternions, express as 3D velocity: qb\*quat(res) = qa.

### [mju_quat2Mat](#mju_quat2Mat)


mju_quat2Mat


Convert quaternion to 3D rotation matrix.

### [mju_mat2Quat](#mju_mat2Quat)


mju_mat2Quat


Convert 3D rotation matrix to quaternion.

### [mju_derivQuat](#mju_derivQuat)


mju_derivQuat


Compute time-derivative of quaternion, given 3D rotational velocity.

### [mju_quatIntegrate](#mju_quatIntegrate)


mju_quatIntegrate


Integrate quaternion given 3D angular velocity.

### [mju_quatZ2Vec](#mju_quatZ2Vec)


mju_quatZ2Vec


Construct quaternion performing rotation from z-axis to given vector.

### [mju_mat2Rot](#mju_mat2Rot)


mju_mat2Rot


Extract 3D rotation from an arbitrary 3x3 matrix by refining the input quaternion.

Return the number of iterations required to converge.

### [mju_euler2Quat](#mju_euler2Quat)


mju_euler2Quat


Convert sequence of Euler angles (radians) to quaternion. seq\[0,1,2\] must be in 'xyzXYZ', lower/upper-case mean intrinsic/extrinsic rotations.

## Poses

### [mju_mulPose](#mju_mulPose)


mju_mulPose


Multiply two poses.

### [mju_negPose](#mju_negPose)


mju_negPose


Conjugate pose, corresponding to the opposite spatial transformation.

### [mju_trnVecPose](#mju_trnVecPose)


mju_trnVecPose


Transform vector by pose.

## Decompositions / Solvers

### [mju_cholFactor](#mju_cholFactor)


mju_cholFactor


Cholesky decomposition: mat = L\*L'; return rank, decomposition performed in-place into mat.

### [mju_cholSolve](#mju_cholSolve)


mju_cholSolve


Solve (mat\*mat') \* res = vec, where mat is a Cholesky factor.

### [mju_cholUpdate](#mju_cholUpdate)


mju_cholUpdate


Cholesky rank-one update: L\*L' +/- x\*x'; return rank.

### [mju_cholFactorBand](#mju_cholFactorBand)


mju_cholFactorBand


Band-dense Cholesky decomposition. <br/> Add `diagadd + diagmul*mat_ii` to diagonal before decomposition. <br/> Returns the minimum value of the factorized diagonal or 0 if rank-deficient.

> **Symmetric band-dense matrices**
>
> `mju_cholFactorBand` and subsequent functions containing the substring "band" operate on matrices which are a generalization of symmetric [band matrices](https://en.wikipedia.org/wiki/Band_matrix). *Symmetric band-dense* or "arrowhead" matrices have non-zeros along proximal diagonal bands and dense blocks on the bottom rows and right columns. These matrices have the property that Cholesky factorization creates no fill-in and can therefore be performed efficiently in-place. Matrix structure is defined by three integers:
>
> - `ntotal`: the number of rows (columns) of the symmetric matrix.
> - `nband`: the number of bands under (over) the diagonal, inclusive of the diagonal.
> - `ndense`: the number of dense rows (columns) at the bottom (right).
>
> The non-zeros are stored in memory as two contiguous row-major blocks, colored green and blue in the illustration below. The first block has size `nband x (ntotal-ndense)` and contains the diagonal and the bands below it. The second block has size `ndense x ntotal` and contains the dense part. Total required memory is the sum of the block sizes.
>
> <figure class="align-left">
> <img src="/images/APIreference/arrowhead.svg" width="750" />
> </figure>
>
> For example, consider an arrowhead matrix with `nband = 3`, `ndense = 2` and `ntotal = 8`. In this example, the total memory required is `3*(8-2) + 2*8 = 34` mjtNum's, laid out as follows:
>
> ``` 
> 0   1   2
>     3   4   5
>         6   7   8
>             9   10  11
>                 12  13  14
>                     15  16  17
>         18  19  20  21  22  23  24  25
>         26  27  28  29  30  31  32  33
> ```
>
> The diagonal elements are `2, 5, 8, 11, 14, 17, 24, 33`. <br/> Elements `0, 1, 3, 25` are present in memory but never touched.

### [mju_cholSolveBand](#mju_cholSolveBand)


mju_cholSolveBand


Solve (mat\*mat')\*res = vec where mat is a band-dense Cholesky factor.

### [mju_band2Dense](#mju_band2Dense)


mju_band2Dense


Convert banded matrix to dense matrix, fill upper triangle if flg_sym\>0.

### [mju_dense2Band](#mju_dense2Band)


mju_dense2Band


Convert dense matrix to banded matrix.

### [mju_bandMulMatVec](#mju_bandMulMatVec)


mju_bandMulMatVec


Multiply band-diagonal matrix with nvec vectors, include upper triangle if flg_sym\>0.

### [mju_bandDiag](#mju_bandDiag)


mju_bandDiag


Address of diagonal element i in band-dense matrix representation.

### [mju_eig3](#mju_eig3)


mju_eig3


Eigenvalue decomposition of symmetric 3x3 matrix, mat = eigvec \* diag(eigval) \* eigvec'.

### [mju_boxQP](#mju_boxQP)


mju_boxQP


Solve the box-constrained quadratic program

``` math
\min_x \; \tfrac{1}{2} x^T H x + x^T g \quad \text{s.t.} \quad l \le x \le u
```

Return the rank of the unconstrained subspace, or -1 on failure.

inputs:  
| Argument | Size | Description |
|----|----|----|
| `n` |  | Problem dimension. |
| `H` | $`n \times n`$ | Symmetric positive definite matrix $`H`$. |
| `g` | $`n`$ | Bias vector $`g`$. |
| `lower` | $`n`$ | Lower bounds $`l`$ on $`x`$. Optional. |
| `upper` | $`n`$ | Upper bounds $`u`$ on $`x`$. Optional. |
| `res` | $`n`$ | Initial value of $`x`$, used to warmstart the solver. |

outputs:  
| Argument | Size | Description |
|----|----|----|
| `res` | $`n`$ | Solution $`x`$. |
| `R` | $`n_{free} \times n_{free}`$ | Cholesky factor of the unconstrained subspace. Allocated size $`n (n + 7)`$. |
| `index` | $`n_{free}`$ | Integer array, the set of free dimensions. Allocated size $`n`$. Optional. |
| return value |  | Rank $`n_{free} \le n`$ of the unconstrained subspace, or -1 on failure. |

notes:  
`R` must have allocated size $`n (n + 7)`$, but only $`n_{free} \times n_{free}`$ values are used as output. `index` (if given) must have allocated size $`n`$, but only $`n_{free}`$ values are used as output.

The convenience function `mju_boxQPmalloc` allocates the required data structures.

Only the lower triangles of $`H`$ and `R` are read from and written to, respectively.

### [mju_boxQPmalloc](#mju_boxQPmalloc)


mju_boxQPmalloc


Allocate heap memory for box-constrained Quadratic Program. As in `mju_boxQP`, `index`, `lower`, and `upper` are optional. Free all pointers with `mju_free()`.

### [mju_QP](#mju_QP)


mju_QP


Solve the quadratic program

``` math
\min_x \; \tfrac{1}{2} x^T H x + x^T g \quad \text{s.t.} \quad l \le x \le u, \quad l_A \le A x \le u_A
```

with a dual active-set method. Return the number of active constraints, or a negative value on failure.

inputs:  
| Argument | Size | Description |
|----|----|----|
| `n` |  | Number of variables. |
| `m` |  | Number of rows of $`A`$. |
| `H` | $`n \times n`$ | Positive semidefinite matrix $`H`$. |
| `g` | $`n`$ | Bias vector $`g`$. |
| `lower` | $`n`$ | Lower bounds $`l`$ on $`x`$. Optional. |
| `upper` | $`n`$ | Upper bounds $`u`$ on $`x`$. Optional. |
| `A` | $`m \times n`$ | Constraint matrix $`A`$. Optional. |
| `alower` | $`m`$ | Lower bounds $`l_A`$ on $`A x`$. Optional. |
| `aupper` | $`m`$ | Upper bounds $`u_A`$ on $`A x`$. Optional. |
| `threshold` | $`n + m`$ | Multiplier thresholds of soft constraints. Optional. |
| `compliance` | $`n + m`$ | Constraint compliances, positive for soft constraints. Optional. |
| `active` | $`n + m`$ | Integer array, the active set used to warmstart the solver. Optional. |
| `work` | see below | Workspace. Optional. |

outputs:  
<table>
<colgroup>
<col style="width: 20%" />
<col style="width: 15%" />
<col style="width: 65%" />
</colgroup>
<thead>
<tr>
<th>Argument</th>
<th>Size</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>res</code></td>
<td><span class="math inline"><em>n</em></span></td>
<td>Solution <span class="math inline"><em>x</em></span>.</td>
</tr>
<tr>
<td><code>dual</code></td>
<td><span class="math inline"><em>n</em> + <em>m</em></span></td>
<td>Constraint multipliers <span class="math inline"><em>λ</em></span>. Optional.</td>
</tr>
<tr>
<td><code>active</code></td>
<td><span class="math inline"><em>n</em> + <em>m</em></span></td>
<td>Integer array, the constraint states. Optional.</td>
</tr>
<tr>
<td>return value</td>
<td></td>
<td><div class="line-block">Number of active constraints, or<br />
-1: <span class="math inline"><em>H</em></span> is not positive semidefinite<br />
-2: constraints are infeasible<br />
-3: objective is unbounded on the feasible set<br />
-4: iteration limit reached</div></td>
</tr>
</tbody>
</table>

notes:  
Constraints are the $`n`$ bounds on $`x`$ followed by the $`m`$ rows of $`A`$. This is the order of `dual`, `active`, `threshold` and `compliance`, so that $`\lambda = (\lambda_x, \lambda_A)`$.

A bound with absolute value `mjMAXVAL<glNumeric>` or larger is ignored. Equal lower and upper bounds define an equality constraint.

A positive multiplier corresponds to an upper bound and a negative one to a lower bound, so that at the solution $`H x + g + \lambda_x + A^T \lambda_A = 0`$.

Constraint states are 0: inactive, ±1: holds at its upper/lower bound, ±2: yields.

A constraint with positive `compliance` is soft. It holds exactly while the absolute value of its multiplier is below its threshold $`w`$. Beyond that it yields, and is violated by $`c \, (|\lambda| - w)`$, where $`c`$ is its compliance. This is the minimizer of the penalty $`w s + s^2 / (2 c)`$ on the violation $`s`$. A zero threshold gives a quadratic penalty. A large compliance approaches the exact $`\ell_1`$ penalty: the constraint yields with constant force. Problems where all constraints are soft are always feasible.

Nonzero values of `active` are used to warmstart the solver. Passing the states returned by a previous call speeds up the solution of a sequence of similar problems.

On failure, `res` is the unconstrained minimum corrected by the multipliers found so far.

Only the lower triangle of $`H`$ is read.

$`H`$ can be singular, in which case a proximal term is added and iterated to convergence. This includes linear programs, where $`H = 0`$. If the objective is unbounded on the feasible set, this is detected when a step of the proximal iteration has no curvature, decreases the objective and approaches no bound.

The method follows the dual active-set approach of [Arnström, Bemporad and Axehill (2022)](https://arxiv.org/abs/2103.16236).

`work` (if given) must have allocated size $`n^2 + (n+m)(2n+m+13)`$. If not given, a smaller workspace is allocated internally.

## Attachment

### [mjs_attach](#mjs_attach)


mjs_attach


Attach child to a parent; return the attached element if success or NULL otherwise.

## Tree elements

### [mjs_addBody](#mjs_addBody)


mjs_addBody


Add child body to body; return child.

*Nullable:* `def`

### [mjs_addSite](#mjs_addSite)


mjs_addSite


Add site to body; return site spec.

*Nullable:* `def`

### [mjs_addJoint](#mjs_addJoint)


mjs_addJoint


Add joint to body.

*Nullable:* `def`

### [mjs_addFreeJoint](#mjs_addFreeJoint)


mjs_addFreeJoint


Add freejoint to body.

### [mjs_addGeom](#mjs_addGeom)


mjs_addGeom


Add geom to body.

*Nullable:* `def`

### [mjs_addCamera](#mjs_addCamera)


mjs_addCamera


Add camera to body.

*Nullable:* `def`

### [mjs_addLight](#mjs_addLight)


mjs_addLight


Add light to body.

*Nullable:* `def`

### [mjs_addFrame](#mjs_addFrame)


mjs_addFrame


Add frame to body.

### [mjs_delete](#mjs_delete)


mjs_delete


Remove object corresponding to the given element; return 0 on success. Deleting a body or a frame also deletes everything inside it, along with all the elements that reference a deleted element. A `plugin instance<plugin-instance>` is deleted along with the last element that references it.

## Non-tree elements

### [mjs_addActuator](#mjs_addActuator)


mjs_addActuator


Add actuator.

*Nullable:* `def`

### [mjs_addSensor](#mjs_addSensor)


mjs_addSensor


Add sensor.

### [mjs_addFlex](#mjs_addFlex)


mjs_addFlex


Add flex.

### [mjs_makeFlex](#mjs_makeFlex)


mjs_makeFlex


Create a `flexcomp<body-flexcomp>` in `body` and return the resulting flex; the arguments correspond to the flexcomp attributes. If `file` is the name of an existing `mesh asset<asset-mesh>`, the flexcomp uses that mesh as with the `mesh<body-flexcomp-mesh>` attribute, otherwise `file` is the name of a mesh file. The flexcomp is expanded immediately, so later changes to the mesh asset do not affect the created flex.

### [mjs_addPair](#mjs_addPair)


mjs_addPair


Add contact pair.

*Nullable:* `def`

### [mjs_addExclude](#mjs_addExclude)


mjs_addExclude


Add excluded body pair.

### [mjs_addEquality](#mjs_addEquality)


mjs_addEquality


Add equality.

*Nullable:* `def`

### [mjs_addTendon](#mjs_addTendon)


mjs_addTendon


Add tendon.

*Nullable:* `def`

### [mjs_wrapSite](#mjs_wrapSite)


mjs_wrapSite


Wrap site using tendon.

### [mjs_wrapGeom](#mjs_wrapGeom)


mjs_wrapGeom


Wrap geom using tendon.

### [mjs_wrapJoint](#mjs_wrapJoint)


mjs_wrapJoint


Wrap joint using tendon.

### [mjs_wrapPulley](#mjs_wrapPulley)


mjs_wrapPulley


Wrap pulley using tendon.

### [mjs_addNumeric](#mjs_addNumeric)


mjs_addNumeric


Add numeric.

### [mjs_addText](#mjs_addText)


mjs_addText


Add text.

### [mjs_addTuple](#mjs_addTuple)


mjs_addTuple


Add tuple.

### [mjs_addKey](#mjs_addKey)


mjs_addKey


Add keyframe.

### [mjs_addPlugin](#mjs_addPlugin)


mjs_addPlugin


Add plugin.

### [mjs_addDefault](#mjs_addDefault)


mjs_addDefault


Add default.

*Nullable:* `parent`

## Set actuator parameters

### [mjs_setToMotor](#mjs_setToMotor)


mjs_setToMotor


Set actuator to motor; return error if any.

### [mjs_setToPosition](#mjs_setToPosition)


mjs_setToPosition


Set actuator to position; return error if any.

### [mjs_setToIntVelocity](#mjs_setToIntVelocity)


mjs_setToIntVelocity


Set actuator to integrated velocity; return error if any.

### [mjs_setToVelocity](#mjs_setToVelocity)


mjs_setToVelocity


Set actuator to velocity servo; return error if any.

### [mjs_setToOrientation](#mjs_setToOrientation)


mjs_setToOrientation


Set actuator to orientation servo.

### [mjs_setToPID](#mjs_setToPID)


mjs_setToPID


Set actuator to PID controller.

### [mjs_setToDamper](#mjs_setToDamper)


mjs_setToDamper


Set actuator to activate damper; return error if any.

### [mjs_setToCylinder](#mjs_setToCylinder)


mjs_setToCylinder


Set actuator to hydraulic or pneumatic cylinder; return error if any.

### [mjs_setToMuscle](#mjs_setToMuscle)


mjs_setToMuscle


Set actuator to muscle; return error if any.a

### [mjs_setToAdhesion](#mjs_setToAdhesion)


mjs_setToAdhesion


Set actuator to active adhesion; return error if any.

### [mjs_setToDCMotor](#mjs_setToDCMotor)


mjs_setToDCMotor


Set actuator to DC motor; return error if any.

*Nullable:* `motorconst`, `nominal`, `saturation`, `inductance`, `cogging`, `controller`, `thermal`, `lugre`

## Assets

### [mjs_addMesh](#mjs_addMesh)


mjs_addMesh


Add mesh.

*Nullable:* `def`

### [mjs_addHField](#mjs_addHField)


mjs_addHField


Add height field.

### [mjs_addSkin](#mjs_addSkin)


mjs_addSkin


Add skin.

### [mjs_addTexture](#mjs_addTexture)


mjs_addTexture


Add texture.

*Nullable:* `def`

### [mjs_addMaterial](#mjs_addMaterial)


mjs_addMaterial


Add material.

*Nullable:* `def`

### [mjs_makeMesh](#mjs_makeMesh)


mjs_makeMesh


Generate a built-in procedural mesh of type `mjtMeshBuiltin` with the given parameters. Returns 0 on success; on failure, returns a nonzero value and sets the error of the spec. The parameters of the sphere, hemisphere, cone, supersphere, supertorus, wedge and plate types are those of the corresponding `mesh/builtin<asset-mesh-builtin>` attribute. The procedural types below generate the same shapes as the corresponding `flexcomp<body-flexcomp>` types; their nodes are stored in double precision in `usernode`.

- `mjMESH_BUILTIN_GRID` (count\[3\], spacing\[3\], \[dim\]): A regular grid with `count[i] > 0` points along each axis, separated by `spacing[i]`. `dim` (default 3) creates tetrahedra (3) or triangles (2); `count` must be 1 along the axes beyond `dim`.
- `mjMESH_BUILTIN_BOX`, `mjMESH_BUILTIN_CYLINDER`, `mjMESH_BUILTIN_ELLIPSOID` (count\[3\], spacing\[3\], \[dim\]): The surface of a box grid with `count[i] >= 2` points along each axis, projected onto the shape. `dim` (default 3) creates tetrahedra connecting the surface to the center (3) or surface triangles (2).
- `mjMESH_BUILTIN_SQUARE`, `mjMESH_BUILTIN_DISC` (count\[3\], spacing\[3\]): A triangulated square, or a disc obtained by radial projection of the square; `count[2]` must be 1.

Types without volume (square, disc, and grid, box, cylinder and ellipsoid with `dim` \< 3) change a `legacy` `inertia<asset-mesh-inertia>` to `shell`.

## Find and get utilities

### [mjs_getSpec](#mjs_getSpec)


mjs_getSpec


Get spec from body.

### [mjs_getOriginSpec](#mjs_getOriginSpec)


mjs_getOriginSpec


get spec that originally defined an element contrary to mjs_getSpec, this does not change after attachment

### [mjs_getCompiler](#mjs_getCompiler)


mjs_getCompiler


Get compiler associated with element's origin spec.

### [mjs_findSpec](#mjs_findSpec)


mjs_findSpec


Find spec (model asset) by name.

### [mjs_findBody](#mjs_findBody)


mjs_findBody


Find body in spec by name.

### [mjs_findElement](#mjs_findElement)


mjs_findElement


Find element in spec by name.

### [mjs_findChild](#mjs_findChild)


mjs_findChild


Find child body by name.

### [mjs_getParent](#mjs_getParent)


mjs_getParent


Get parent body.

### [mjs_getFrame](#mjs_getFrame)


mjs_getFrame


Get parent frame.

### [mjs_findFrame](#mjs_findFrame)


mjs_findFrame


Find frame by name.

### [mjs_getDefault](#mjs_getDefault)


mjs_getDefault


Get default corresponding to an element.

### [mjs_findDefault](#mjs_findDefault)


mjs_findDefault


Find default in model by class name.

### [mjs_getSpecDefault](#mjs_getSpecDefault)


mjs_getSpecDefault


Get global default from model.

### [mjs_getId](#mjs_getId)


mjs_getId


Get element id.

### [mjs_firstChild](#mjs_firstChild)


mjs_firstChild


Return body's first child of given type. If recurse is nonzero, also search the body's subtree.

### [mjs_nextChild](#mjs_nextChild)


mjs_nextChild


Return body's next child of the same type; return NULL if child is last.

If recurse is nonzero, also search the body's subtree.

### [mjs_firstElement](#mjs_firstElement)


mjs_firstElement


Return spec's first element of selected type.

### [mjs_nextElement](#mjs_nextElement)


mjs_nextElement


Return spec's next element; return NULL if element is last.

### [mjs_getWrapTarget](#mjs_getWrapTarget)


mjs_getWrapTarget


Get wrapped element in tendon path.

### [mjs_getWrapSideSite](#mjs_getWrapSideSite)


mjs_getWrapSideSite


Get wrapped element side site in tendon path if it has one, nullptr otherwise.

### [mjs_getWrapDivisor](#mjs_getWrapDivisor)


mjs_getWrapDivisor


Get divisor of mjsWrap wrapping a puller.

### [mjs_getWrapCoef](#mjs_getWrapCoef)


mjs_getWrapCoef


Get coefficient of mjsWrap wrapping a joint.

## Attribute setters

### [mjs_setName](#mjs_setName)


mjs_setName


Set element's name; return 0 on success.

### [mjs_setBuffer](#mjs_setBuffer)


mjs_setBuffer


Copy buffer.

### [mjs_setString](#mjs_setString)


mjs_setString


Copy text to string.

### [mjs_setStringVec](#mjs_setStringVec)


mjs_setStringVec


Split text to entries and copy to string vector.

### [mjs_setInStringVec](#mjs_setInStringVec)


mjs_setInStringVec


Set entry in string vector.

### [mjs_appendString](#mjs_appendString)


mjs_appendString


Append text entry to string vector.

### [mjs_setInt](#mjs_setInt)


mjs_setInt


Copy int array to vector.

### [mjs_appendIntVec](#mjs_appendIntVec)


mjs_appendIntVec


Append int array to vector of arrays.

### [mjs_setFloat](#mjs_setFloat)


mjs_setFloat


Copy float array to vector.

### [mjs_appendFloatVec](#mjs_appendFloatVec)


mjs_appendFloatVec


Append float array to vector of arrays.

### [mjs_setDouble](#mjs_setDouble)


mjs_setDouble


Copy double array to vector.

### [mjs_setPluginAttributes](#mjs_setPluginAttributes)


mjs_setPluginAttributes


Set plugin attributes.

## Attribute getters

### [mjs_getName](#mjs_getName)


mjs_getName


Get element's name.

### [mjs_getString](#mjs_getString)


mjs_getString


Get string contents.

### [mjs_getInStringVec](#mjs_getInStringVec)


mjs_getInStringVec


Get entry in string vector, or NULL if out of bounds.

### [mjs_getDouble](#mjs_getDouble)


mjs_getDouble


Get double array contents and optionally its size.

*Nullable:* `size`

### [mjs_getWrapNum](#mjs_getWrapNum)


mjs_getWrapNum


Get number of elements a tendon wraps.

### [mjs_getWrap](#mjs_getWrap)


mjs_getWrap


Get mjsWrap element at position i in the tendon path.

### [mjs_getPluginAttributes](#mjs_getPluginAttributes)


mjs_getPluginAttributes


Get plugin attributes.

## Spec utilities

### [mjs_setDefault](#mjs_setDefault)


mjs_setDefault


Set element's default.

### [mjs_setFrame](#mjs_setFrame)


mjs_setFrame


Set element's enclosing frame; return 0 on success.

### [mjs_resolveOrientation](#mjs_resolveOrientation)


mjs_resolveOrientation


Resolve alternative orientations to quat; return error if any.

### [mjs_fuseStatic](#mjs_fuseStatic)


mjs_fuseStatic


Fuse the static bodies of the spec with their parents. A body without joints is replaced by a `frame<frame>` in its parent, which has the pose of the body and holds its geoms, sites, cameras, lights, frames and child bodies, in the same coordinates as before. The inertia of the body is added to that of the parent. The compiled model has the same kinematics and dynamics, with fewer bodies. Bodies which cannot be fused without changing the model are kept, see `fusestatic<compiler-fusestatic>`, which applies this function before compiling. Pointers to the bodies which were fused are no longer valid. Assets are read as in `mj_compile`. Returns the number of bodies fused, 0 if the spec is unchanged, or -1 on error, in which case nothing is fused.

### [mjs_discardVisual](#mjs_discardVisual)


mjs_discardVisual


Discard the elements of the spec which are only visual: materials and textures, the geoms which do not collide, and the meshes which are then not used; an element which another refers to by name is kept. If a discarded geom was used for inferring the inertia of its body, that inertia becomes the explicit inertial of the body, as in `mjs_adoptInertial`, so the compiled model has the same dynamics. See `discardvisual<compiler-discardvisual>`, which applies this function before compiling. Pointers to the elements which were discarded are no longer valid. Assets are read as in `mj_compile`, and only if inertia is inferred from a discarded geom. Returns the number of elements discarded, 0 if the spec is unchanged, or -1 on error, in which case nothing is discarded.

### [mjs_dedupAssets](#mjs_dedupAssets)


mjs_dedupAssets


Merge the textures and meshes of the spec which would compile to the same asset: textures with the same resolved file or buffer and the same parameters, meshes with the same resolved file or arrays and the same parameters, names excluded. The first asset of each group keeps its name, every reference to the others (materials, lights, geoms, sites, default classes, sensors, tuples) is rewritten to it, and the others are deleted as by `mjs_delete`, so pointers to them are no longer valid. An unnamed asset is left alone, as is a mesh with a plugin. Nothing is read from disk: a model which attaches the same sub-model several times is merged without its asset files. Returns the number of assets merged, 0 if the spec is unchanged, or -1 on error, in which case nothing is merged.

### [mjs_adoptInertial](#mjs_adoptInertial)


mjs_adoptInertial


Make the inertial which compilation infers for a body part of the spec. The mass, inertia and inertial frame which the compiler calculates from the geoms of the body, as the spec is now, are written as the explicit inertial of the body, so that later changes to its geoms no longer affect them. Compiling before and after gives the same model: the values are those before the scaling of `settotalmass<compiler-settotalmass>`. Nothing is done if the inertial of the body is not inferred. It is an error when `inertiafromgeom<compiler-inertiafromgeom>` is "true", which infers the inertia of every body whatever its inertial. Assets are read as in `mj_compile`. Returns 0 on success.

To read an inferred inertial without adopting it, compile and look it up in `mjModel` with `mjs_getId`.

### [mjs_bodyToFrame](#mjs_bodyToFrame)


mjs_bodyToFrame


Transform body into a frame.

### [mjs_setUserValue](#mjs_setUserValue)


mjs_setUserValue


Set user payload, overriding the existing value for the specified key if present.

### [mjs_setUserValueWithCleanup](#mjs_setUserValueWithCleanup)


mjs_setUserValueWithCleanup


Set user payload, overriding the existing value for the specified key if present. This version differs from mjs_setUserValue in that it takes a cleanup function that will be called when the user payload is deleted.

### [mjs_getUserValue](#mjs_getUserValue)


mjs_getUserValue


Return user payload or NULL if none found.

### [mjs_deleteUserValue](#mjs_deleteUserValue)


mjs_deleteUserValue


Delete user payload.

### [mjs_sensorDim](#mjs_sensorDim)


mjs_sensorDim


Return sensor dimension.

## Element initialization

### [mjs_defaultSpec](#mjs_defaultSpec)


mjs_defaultSpec


Default spec attributes.

### [mjs_defaultOrientation](#mjs_defaultOrientation)


mjs_defaultOrientation


Default orientation attributes.

### [mjs_defaultBody](#mjs_defaultBody)


mjs_defaultBody


Default body attributes.

### [mjs_defaultFrame](#mjs_defaultFrame)


mjs_defaultFrame


Default frame attributes.

### [mjs_defaultJoint](#mjs_defaultJoint)


mjs_defaultJoint


Default joint attributes.

### [mjs_defaultGeom](#mjs_defaultGeom)


mjs_defaultGeom


Default geom attributes.

### [mjs_defaultSite](#mjs_defaultSite)


mjs_defaultSite


Default site attributes.

### [mjs_defaultCamera](#mjs_defaultCamera)


mjs_defaultCamera


Default camera attributes.

### [mjs_defaultLight](#mjs_defaultLight)


mjs_defaultLight


Default light attributes.

### [mjs_defaultFlex](#mjs_defaultFlex)


mjs_defaultFlex


Default flex attributes.

### [mjs_defaultMesh](#mjs_defaultMesh)


mjs_defaultMesh


Default mesh attributes.

### [mjs_defaultHField](#mjs_defaultHField)


mjs_defaultHField


Default height field attributes.

### [mjs_defaultSkin](#mjs_defaultSkin)


mjs_defaultSkin


Default skin attributes.

### [mjs_defaultTexture](#mjs_defaultTexture)


mjs_defaultTexture


Default texture attributes.

### [mjs_defaultMaterial](#mjs_defaultMaterial)


mjs_defaultMaterial


Default material attributes.

### [mjs_defaultPair](#mjs_defaultPair)


mjs_defaultPair


Default pair attributes.

### [mjs_defaultEquality](#mjs_defaultEquality)


mjs_defaultEquality


Default equality attributes.

### [mjs_defaultTendon](#mjs_defaultTendon)


mjs_defaultTendon


Default tendon attributes.

### [mjs_defaultActuator](#mjs_defaultActuator)


mjs_defaultActuator


Default actuator attributes.

### [mjs_defaultSensor](#mjs_defaultSensor)


mjs_defaultSensor


Default sensor attributes.

### [mjs_defaultNumeric](#mjs_defaultNumeric)


mjs_defaultNumeric


Default numeric attributes.

### [mjs_defaultText](#mjs_defaultText)


mjs_defaultText


Default text attributes.

### [mjs_defaultTuple](#mjs_defaultTuple)


mjs_defaultTuple


Default tuple attributes.

### [mjs_defaultKey](#mjs_defaultKey)


mjs_defaultKey


Default keyframe attributes.

### [mjs_defaultPlugin](#mjs_defaultPlugin)


mjs_defaultPlugin


Default plugin attributes.

## Element casting

### [mjs_asBody](#mjs_asBody)


mjs_asBody


Safely cast an element as mjsBody, or return NULL if the element is not an mjsBody.

### [mjs_asGeom](#mjs_asGeom)


mjs_asGeom


Safely cast an element as mjsGeom, or return NULL if the element is not an mjsGeom.

### [mjs_asJoint](#mjs_asJoint)


mjs_asJoint


Safely cast an element as mjsJoint, or return NULL if the element is not an mjsJoint.

### [mjs_asSite](#mjs_asSite)


mjs_asSite


Safely cast an element as mjsSite, or return NULL if the element is not an mjsSite.

### [mjs_asCamera](#mjs_asCamera)


mjs_asCamera


Safely cast an element as mjsCamera, or return NULL if the element is not an mjsCamera.

### [mjs_asLight](#mjs_asLight)


mjs_asLight


Safely cast an element as mjsLight, or return NULL if the element is not an mjsLight.

### [mjs_asFrame](#mjs_asFrame)


mjs_asFrame


Safely cast an element as mjsFrame, or return NULL if the element is not an mjsFrame.

### [mjs_asActuator](#mjs_asActuator)


mjs_asActuator


Safely cast an element as mjsActuator, or return NULL if the element is not an mjsActuator.

### [mjs_asSensor](#mjs_asSensor)


mjs_asSensor


Safely cast an element as mjsSensor, or return NULL if the element is not an mjsSensor.

### [mjs_asFlex](#mjs_asFlex)


mjs_asFlex


Safely cast an element as mjsFlex, or return NULL if the element is not an mjsFlex.

### [mjs_asPair](#mjs_asPair)


mjs_asPair


Safely cast an element as mjsPair, or return NULL if the element is not an mjsPair.

### [mjs_asEquality](#mjs_asEquality)


mjs_asEquality


Safely cast an element as mjsEquality, or return NULL if the element is not an mjsEquality.

### [mjs_asExclude](#mjs_asExclude)


mjs_asExclude


Safely cast an element as mjsExclude, or return NULL if the element is not an mjsExclude.

### [mjs_asTendon](#mjs_asTendon)


mjs_asTendon


Safely cast an element as mjsTendon, or return NULL if the element is not an mjsTendon.

### [mjs_asNumeric](#mjs_asNumeric)


mjs_asNumeric


Safely cast an element as mjsNumeric, or return NULL if the element is not an mjsNumeric.

### [mjs_asText](#mjs_asText)


mjs_asText


Safely cast an element as mjsText, or return NULL if the element is not an mjsText.

### [mjs_asTuple](#mjs_asTuple)


mjs_asTuple


Safely cast an element as mjsTuple, or return NULL if the element is not an mjsTuple.

### [mjs_asKey](#mjs_asKey)


mjs_asKey


Safely cast an element as mjsKey, or return NULL if the element is not an mjsKey.

### [mjs_asMesh](#mjs_asMesh)


mjs_asMesh


Safely cast an element as mjsMesh, or return NULL if the element is not an mjsMesh.

### [mjs_asHField](#mjs_asHField)


mjs_asHField


Safely cast an element as mjsHField, or return NULL if the element is not an mjsHField.

### [mjs_asSkin](#mjs_asSkin)


mjs_asSkin


Safely cast an element as mjsSkin, or return NULL if the element is not an mjsSkin.

### [mjs_asTexture](#mjs_asTexture)


mjs_asTexture


Safely cast an element as mjsTexture, or return NULL if the element is not an mjsTexture.

### [mjs_asMaterial](#mjs_asMaterial)


mjs_asMaterial


Safely cast an element as mjsMaterial, or return NULL if the element is not an mjsMaterial.

### [mjs_asPlugin](#mjs_asPlugin)


mjs_asPlugin


Safely cast an element as mjsPlugin, or return NULL if the element is not an mjsPlugin.
