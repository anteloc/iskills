# Types

MuJoCo defines a large number of types:

- Four [primitive types](APItypes.md): [mjtNum](APItypes.md), [mjtByte](APItypes.md), [mjtBool](APItypes.md), and [mjtSize](APItypes.md).

- [C enum types](APItypes.md) used to define categorical values. These can be classified as:

  - Enums used in [mjModel](APItypes.md).
  - Enums used in [mjData](APItypes.md).
  - Enums for abstract [visualization](APItypes.md).
  - Enums used by the [classic renderer](APItypes.md).
  - Enums used by the [filament renderer](APItypes.md).
  - Enums used by the [mjUI](APItypes.md) user interface package.
  - Enums used by [engine plugins](APItypes.md).
  - Enums used for [procedural model manipulation](APItypes.md).

  Note that the API does not use these enum types directly. Instead it uses ints, and the documentation/comments state that certain ints correspond to certain enum types. This is because we want the API to be compiler-independent, and the C standard does not dictate how many bytes must be used to represent an enum type. Nevertheless, for improved readability, we recommend using these types when calling API functions which take them as arguments.

- [C struct types](APItypes.md). These can be classified as:

  - Main structs:
    - [mjModel](APItypes.md).
    - [mjOption](APItypes.md) (embedded in [mjModel](APItypes.md)).
    - [mjData](APItypes.md).
  - [Auxiliary struct types](APItypes.md), also used by the engine.
  - Structs for collecting [simulation statistics](APItypes.md).
  - Structs for [abstract visualization](APItypes.md).
  - Structs used by the [classic renderer](APItypes.md).
  - Structs used by the [filament renderer](APItypes.md).
  - Structs used by the [UI framework](APItypes.md).
  - Structs used for [procedural model manipulation](APItypes.md).
  - Structs used by [engine plugins](APItypes.md).

- Several [function types](APItypes.md) for user-defined callbacks.

- [Notes](APItypes.md) regarding specific data structures that require detailed description.

## Primitive types

The three types below are defined in [mjtype.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjtype.h).

### mjtNum

This is the floating-point type used throughout the simulator. When using the default build configuration, `mjtNum` is defined as `double`. If the symbol `mjUSESINGLE` is defined, `mjtNum` is defined as `float`.

Currently only the double-precision version of MuJoCo is distributed, although the entire code base works with single-precision as well. We may release the single-precision version in the future, but the double-precision version will always be available. Thus it is safe to write user code assuming double precision. However, our preference is to write code that works with either single or double precision. To this end we provide math utility functions that are always defined with the correct floating-point type.

Note that changing `mjUSESINGLE` in `mjtype.h` will not change how the library was compiled, and instead will result in numerous link errors. In general, the header files distributed with precompiled MuJoCo should never be changed by the user.

``` C
// floating point data type and minval
#ifndef mjUSESINGLE
  typedef double mjtNum;
  #define mjMINVAL    1E-15       // minimum value in any denominator
#else
  typedef float mjtNum;
  #define mjMINVAL    1E-15f
#endif
```

### mjtByte

Byte type used to represent small integers and binary data.

``` C
typedef unsigned char mjtByte;
```

### mjtBool

Boolean type used to represent true/false values.

``` C
#ifndef __cplusplus
  typedef _Bool mjtBool;
#else
  typedef bool mjtBool;
#endif
```

### mjtSize

Size type used to represent buffer sizes.

``` C
typedef int64_t mjtSize;
```

## Enum types

All enum types use the `mjt` prefix.

### Model

The enums below are defined in [mjtype.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjtype.h).

#### mjtDisableBit

Constants which are powers of 2. They are used as bitmasks for the field `disableflags` of [mjOption](APItypes.md). At runtime this field is `m->opt.disableflags`. The number of these constants is given by `mjNDISABLE` which is also the length of the global string array [mjDISABLESTRING](APIglobals.md) with text descriptions of these flags.


mjtDisableBit


#### mjtEnableBit

Constants which are powers of 2. They are used as bitmasks for the field `enableflags` of [mjOption](APItypes.md). At runtime this field is `m->opt.enableflags`. The number of these constants is given by `mjNENABLE` which is also the length of the global string array [mjENABLESTRING](APIglobals.md) with text descriptions of these flags.


mjtEnableBit


#### mjtJoint

Primitive joint types. These values are used in `m->jnt_type`. The numbers in the comments indicate how many positional coordinates each joint type has. Note that ball joints and rotational components of free joints are represented as unit quaternions - which have 4 positional coordinates but 3 degrees of freedom each.


mjtJoint


#### mjtGeom

Geometric types supported by MuJoCo. The first group are "official" geom types that can be used in the model. The second group are geom types that cannot be used in the model but are used by the visualizer to add decorative elements. These values are used in `m->geom_type` and `m->site_type`.


mjtGeom


#### mjtProjection

Type of camera projection. Used in `m->cam_projection`.


mjtProjection


#### mjtCamLight

Dynamic modes for cameras and lights, specifying how the camera/light position and orientation are computed. These values are used in `m->cam_mode` and `m->light_mode`.


mjtCamLight


#### mjtLightType

The type of a light source describing how its position, orientation and other properties will interact with the objects in the scene. These values are used in `m->light_type`.


mjtLightType


#### mjtTexture

Texture types, specifying how the texture will be mapped. These values are used in `m->tex_type`.


mjtTexture


#### mjtTextureRole

Texture roles, specifying how the renderer should interpret the texture. Note that the MuJoCo built-in renderer only uses RGB textures. These values are used to store the texture index in the material's array `m->mat_texid`.


mjtTextureRole


#### mjtColorSpace

Type of color space encoding for textures.


mjtColorSpace


#### mjtIntegrator

Numerical integrator types. These values are used in `m->opt.integrator`.


mjtIntegrator


#### mjtCone

Available friction cone types. These values are used in `m->opt.cone`.


mjtCone


#### mjtJacobian

Available Jacobian types. These values are used in `m->opt.jacobian`.


mjtJacobian


#### mjtSolver

Available constraint solver algorithms. These values are used in `m->opt.solver`.


mjtSolver


#### mjtEq

Equality constraint types. These values are used in `m->eq_type`.


mjtEq


#### mjtTendon

Tendon types. These values are used in `m->tendon_type`.


mjtTendon


#### mjtWrap

Tendon wrapping object types. These values are used in `m->wrap_type`.


mjtWrap


#### mjtTrn

Actuator transmission types. These values are used in `m->actuator_trntype`.


mjtTrn


#### mjtDyn

Actuator dynamics types. These values are used in `m->actuator_dyntype`.


mjtDyn


#### mjtGain

Actuator gain types. These values are used in `m->actuator_gaintype`.


mjtGain


#### mjtBias

Actuator bias types. These values are used in `m->actuator_biastype`.


mjtBias


#### mjtCtrlChart

Orientation input charts of so3 actuators. These values are used in `m->actuator_ctrlspec`.


mjtCtrlChart


#### mjtCtrlInput

Input bitflags of actuators: the input subset of pid and dcmotor actuators, and the declared input of actuators with fixed or affine gain. These values are used in `m->actuator_ctrlspec`.


mjtCtrlInput


#### mjtObj

MuJoCo object types. These are used, for example, in the support functions *mj_name2id* and *mj_id2name* to convert between object names and integer ids.


mjtObj


#### mjtSensor

Sensor types. These values are used in `m->sensor_type`.


mjtSensor


#### mjtStage

These are the compute stages for the skipstage parameters of *mj_forwardSkip* and *mj_inverseSkip*.


mjtStage


#### mjtDataType

These are the possible sensor data types, used in `mjData.sensor_datatype`.


mjtDataType


#### mjtConDataField

Types of data fields returned by contact sensors.


mjtConDataField


#### mjtRayDataField

Data fields returned by rangefinder sensors.


mjtRayDataField


#### mjtCamOutBit

Camera output type bitflags. These are used in `m->cam_output`.


mjtCamOutBit


#### mjtSameFrame

Types of frame alignment of elements with their parent bodies. Used as shortcuts during *mj_kinematics* in the last argument to *mj_local2global*.


mjtSameFrame


#### mjtSleepPolicy

Sleep policy associated with a tree. The compiler automatically chooses between `NEVER` and `ALLOWED`, but the user can override this choice. Only the user can set the `INIT` policy (initialized as asleep).


mjtSleepPolicy


#### mjtLRMode

Mode for actuator length range computation. Used in `mjLROpt.mode`.


mjtLRMode


#### mjtFlexSelf

Types of flex self-collisions midphase.


mjtFlexSelf


#### mjtSDFType

Formulas used to combine SDFs when calling mjc_distance and mjc_gradient.


mjtSDFType


### Data

The enums below are defined in [mjtype.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjtype.h).

#### mjtState

State component elements as integer bitflags and several convenient combinations of these flags. Used by *mj_getState*, *mj_setState* and *mj_stateSize*.


mjtState


#### mjtConstraint

Constraint types. These values are not used in mjModel, but are used in the mjData field `d->efc_type` when the list of active constraints is constructed at each simulation time step.


mjtConstraint


#### mjtConstraintState

These values are used by the solver internally to keep track of the constraint states.


mjtConstraintState


#### mjtWarning

Warning types. The number of warning types is given by `mjNWARNING` which is also the length of the array `mjData.warning`.


mjtWarning


#### mjtTimer

Timer types. The number of timer types is given by `mjNTIMER` which is also the length of the array `mjData.timer`, as well as the length of the string array [mjTIMERSTRING](APIglobals.md) with timer names.


mjtTimer


#### mjtSleepState

Sleep state of an object.


mjtSleepState


#### Logging

##### mjtLogLevel

Log message severity level.


mjtLogLevel


##### mjtLogTopic

Topic identifiers for informational messages. Used with *mju_info* for topic-based filtering. Topic 0 (`mjTOPIC_NONE`) always passes through the default handler's filter. Other topics must be enabled in the [mjLogConfig](APItypes.md) bitmask. Since topics are 1-indexed, the bitmask for topic `t` is `(1 << (t - 1))`. The number of filterable topics is given by `mjNTOPIC`, which is also the length of the string array [mjTOPICSTRING](APIglobals.md).


mjtLogTopic


### Visualization

The enums below are defined in [mjvisualize.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjvisualize.h).

#### mjtCatBit

These are the available categories of geoms in the abstract visualizer. The bitmask can be used in the function *mjr_render* to specify which categories should be rendered.


mjtCatBit


#### mjtMouse

These are the mouse actions that the abstract visualizer recognizes. It is up to the user to intercept mouse events and translate them into these actions, as illustrated in [simulate.cc](../programming/samples.md).


mjtMouse


#### mjtPertBit

These bitmasks enable the translational and rotational components of the mouse perturbation. For the regular mouse, only one can be enabled at a time. For the 3D mouse (SpaceNavigator) both can be enabled simultaneously. They are used in `mjvPerturb.active`.


mjtPertBit


#### mjtCamera

These are the possible camera types, used in `mjvCamera.type`.


mjtCamera


#### mjtLabel

These are the abstract visualization elements that can have text labels. Used in `mjvOption.label`. The corresponding string array is [mjLABELSTRING](APIglobals.md).


mjtLabel


#### mjtFrame

These are the MuJoCo objects whose spatial frames can be rendered. Used in `mjvOption.frame`. The corresponding string array is [mjFRAMESTRING](APIglobals.md).


mjtFrame


#### mjtVisFlag

These are indices in the array `mjvOption.flags`, whose elements enable/disable the visualization of the corresponding model or decoration element. The corresponding string array is [mjVISSTRING](APIglobals.md).


mjtVisFlag


#### mjtRndFlag

These are indices in the array `mjvScene.flags`, whose elements enable/disable OpenGL rendering effects. The corresponding string array is [mjRNDSTRING](APIglobals.md).


mjtRndFlag


#### mjtStereo

These are the possible stereo rendering types. They are used in `mjvScene.stereo`.


mjtStereo


### Rendering

The enums below are defined in [mjrender.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjrender.h).

#### mjtGridPos

These are the possible grid positions for text overlays. They are used as an argument to the function *mjr_overlay*.


mjtGridPos


#### mjtFramebuffer

These are the possible framebuffers. They are used as an argument to the function *mjr_setBuffer*.


mjtFramebuffer


#### mjtDepthMap

These are the depth mapping options. They are used as a value for the `readPixelDepth` attribute of the [mjrContext](APItypes.md) struct, to control how the depth returned by *mjr_readPixels* is mapped from `znear` to `zfar`.


mjtDepthMap


#### mjtFontScale

These are the possible font sizes. The fonts are predefined bitmaps stored in the dynamic library at three different sizes.


mjtFontScale


#### mjtFont

These are the possible font types.


mjtFont


#### mjrPixelFormat

These are the possible values:


mjrPixelFormat


#### mjrVertexAttributeUsage

These are the possible values:


mjrVertexAttributeUsage


#### mjrVertexAttributeType

These are the possible values:


mjrVertexAttributeType


#### mjrIndexType

These are the possible values:


mjrIndexType


#### mjrMeshPrimitiveType

There are the possible values:


mjrMeshPrimitiveType


### Filament Rendering

The enums below are defined in [mjrfilament.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjrfilament.h).

#### mjrGraphicsApi

The underlying graphics API to use for Filament rendering.


mjrGraphicsApi


#### mjrDrawMode

High-level control for how to draw objects in the scene for Filament rendering.


mjrDrawMode


#### mjrQuality

Rendering quality level that affects performance and visual fidelity for different options.


mjrQuality


#### mjrToneMapper

Tone mapping operators available to use for color grading during post-processing.


mjrToneMapper


#### mjrShadowType

Types of shadow algorithms available to use.


mjrShadowType


#### mjrAmbientOcclusionType

Types of ambient occlusion algorithms available to use.


mjrAmbientOcclusionType


#### mjrDitheringType

Types of dithering algorithms available to use.


mjrDitheringType


### User Interface

The enums below are defined in [mjui.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjui.h).

#### mjtButton

Mouse button IDs used in the UI framework.


mjtButton


#### mjtEvent

Event types used in the UI framework.


mjtEvent


#### mjtItem

Item types used in the UI framework.


mjtItem


#### mjtSection

State of a UI section.


mjtSection


### Spec

The enums below are defined in [mjspec.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjspec.h).

#### mjtGeomInertia

Type of inertia inference.


mjtGeomInertia


#### mjtBuiltin

Type of built-in procedural texture.


mjtBuiltin


#### mjtMark

Mark type for procedural textures.


mjtMark


#### mjtLimited

Type of limit specification.


mjtLimited


#### mjtAlignFree

Whether to align free joints with the inertial frame.


mjtAlignFree


#### mjtPassthrough

Which assets the compiler leaves [by reference](../modeling.md) instead of loading into [mjModel](APItypes.md), a bitmask; see [compiler/passthrough](../XMLreference.md).


mjtPassthrough


#### mjtEmbed

Whether an asset's payload is in the model or the asset is [by reference](../modeling.md); see [texture/embed](../XMLreference.md).


mjtEmbed


#### mjtInertiaFromGeom

Whether to infer body inertias from child geoms.


mjtInertiaFromGeom


#### mjtOrientation

Type of orientation specifier.


mjtOrientation


#### mjtMeshInertia

Type of mesh inertia computation.


mjtMeshInertia


#### mjtMeshBuiltin

Type of built-in procedural mesh.


mjtMeshBuiltin


#### mjtFlexSection

Cross-section of 1D flex [elasticity](../XMLreference.md), see [section](../XMLreference.md).


mjtFlexSection


#### mjtConflict

Conflict resolution mode for attach.


mjtConflict


#### mjtScaling

Physical policy of a frame's [scale](../XMLreference.md), see [scaling](../XMLreference.md).


mjtScaling


#### mjtActuator

The [actuator element](../XMLreference.md) an actuator is written with: [general](../XMLreference.md) or one of its [shortcuts](../modeling.md). Set by the `mjs_setTo*` functions and by the parser; shortcut parameters are inherited only from a default written with the same shortcut.


mjtActuator


#### mjtCTimer

Compiler timing categories, used in *mjs_getTimer*. Top-level timers (`TOTAL`, `ASSETS`) measure wall-clock time. Asset sub-timers measure CPU time summed across all assets; with multi-threaded compilation their sum can exceed the `ASSETS` wall-clock time.


mjtCTimer


### Plugins

The enums below are defined in [mjplugin.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjplugin.h). See [Engine plugins](../programming/extension.md) for details.

#### mjtPluginCapabilityBit

Capabilities declared by an engine plugin.


mjtPluginCapabilityBit


## Struct types

The three central struct types for physics simulation are [mjModel](APItypes.md), [mjOption](APItypes.md) (embedded in [mjModel](APItypes.md)) and [mjData](APItypes.md). An introductory discussion of these structures can be found in the [Overview](../overview.md).

### mjModel

This is the main data structure holding the MuJoCo model. It is treated as constant by the simulator. Some specific details regarding datastructures in [mjModel](APItypes.md) can be found below in [Notes](APItypes.md).


mjModel


### mjOption

This is the data structure with simulation options. It corresponds to the MJCF element [option](../XMLreference.md). One instance of it is embedded in mjModel.


mjOption


### mjData

This is the main data structure holding the simulation state. It is the workspace where all functions read their modifiable inputs and write their outputs.


mjData


### Auxiliary

These struct types are used in the engine and their names are prefixed with `mj`. [mjVisual](APItypes.md) and [mjStatistic](APItypes.md) are embedded in [mjModel](APItypes.md), [mjContact](APItypes.md) is embedded in [mjData](APItypes.md), and [mjVFS](APItypes.md) is a library-level struct used for loading assets.

#### mjVisual

This is the data structure with abstract visualization options. It corresponds to the MJCF element [visual](../XMLreference.md). One instance of it is embedded in mjModel.


mjVisual


#### mjStatistic

This is the data structure with model statistics precomputed by the compiler or set by the user. It corresponds to the MJCF element [statistic](../XMLreference.md). One instance of it is embedded in mjModel.


mjStatistic


#### mjPreContact

This is the data structure holding information about one contact filled out by a narrowphase collision detector.


mjPreContact


#### mjContact

This is the data structure holding information about one contact. `mjData.contact` is a preallocated array of mjContact data structures, populated at runtime with the contacts found by the collision detector. Additional contact information is then filled-in by the simulator.


mjContact


#### mjResource

A resource is an abstraction of a file in a filesystem. The name field is the unique name of the resource while the other fields are populated by a [resource provider](../programming/extension.md).


mjResource


#### mjVFS

This is the data structure of the virtual file system. It can only be constructed programmatically, and does not have an analog in MJCF.


mjVFS


#### mjLROpt

Options for configuring the automatic [actuator length-range computation](../modeling.md).


mjLROpt


#### mjCache

Asset cache used by the compiler to avoid repeated slow recompilation. See *Asset cache*.


mjCache


### Logging

#### mjLogMessage

Structured log message passed to [mjfLogHandler](APItypes.md) callbacks. Contains the severity level, optional topic for info messages, a one-line subject, an optional multi-line body, and optional source location (function name, file name, line number).


mjLogMessage


#### mjLogConfig

Configuration for the default log handler. Controls whether messages are printed to the console and/or written to a log file (default: `MUJOCO_LOG.TXT`). The `logto_file` field enables file logging, while `logfile` specifies the file path. The `topics` field is a bitmask of [mjtLogTopic](APItypes.md) values: bit `(topic - 1)` enables that topic. Topic 0 (`mjTOPIC_NONE`) always passes through.


mjLogConfig


### Sim statistics

These structs are all embedded in [mjData](APItypes.md), and collect simulation-related statistics.

#### mjWarningStat

This is the data structure holding information about one warning type. `mjData.warning` is a preallocated array of mjWarningStat data structures, one for each warning type.


mjWarningStat


#### mjTimerStat

This is the data structure holding information about one timer. `mjData.timer` is a preallocated array of mjTimerStat data structures, one for each timer type.


mjTimerStat


#### mjSolverStat

This is the data structure holding information about one solver iteration. `mjData.solver` is a preallocated array of mjSolverStat data structures, one for each iteration of the solver, up to a maximum of mjNSOLVER. The actual number of solver iterations is given by `mjData.solver_niter`.


mjSolverStat


### Visualisation

The names of these struct types are prefixed with `mjv`.

#### mjvPerturb

This is the data structure holding information about mouse perturbations.


mjvPerturb


#### mjvCamera

This is the data structure describing one abstract camera.


mjvCamera


#### mjvGLCamera

This is the data structure describing one OpenGL camera.


mjvGLCamera


#### mjvGeom

This is the data structure describing one abstract visualization geom - which could correspond to a model geom or to a decoration element constructed by the visualizer.


mjvGeom


#### mjvLight

This is the data structure describing one OpenGL light.


mjvLight


#### mjvOption

This structure contains options that enable and disable the visualization of various elements.


mjvOption


#### mjvScene

This structure contains everything needed to render the 3D scene in OpenGL.


mjvScene


#### mjvFigure

This structure contains everything needed to render a 2D plot in OpenGL. The buffers for line points etc. are preallocated, and the user has to populate them before calling the function *mjr_figure* with this data structure as an argument.


mjvFigure


### Rendering

The names of these struct types are prefixed with `mjr`.

#### mjrRect

This structure specifies a rectangle.


mjrRect


#### mjrVertexAttribute

This structure specifies the attributes for a single vertex.


mjrVertexAttribute


#### mjrRendererInfo

This structure contains information about the available renderer and its current context.


mjrRendererInfo


#### mjrContext

This structure contains the custom OpenGL rendering context, with the ids of all OpenGL resources uploaded to the GPU.


mjrContext


### Filament Rendering

The names of these struct types are prefixed with `mjrf`. They are defined in [mjrfilament.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjrfilament.h).

There are seven key types defined by this API: [mjrfContext](APItypes.md), [mjrfTexture](APItypes.md), [mjrfMesh](APItypes.md), [mjrfLight](APItypes.md), [mjrfRenderable](APItypes.md), [mjrfScene](APItypes.md), and [mjrfRenderTarget](APItypes.md).

Each object is created using a <span class="title-ref">create</span> function and destroyed using a <span class="title-ref">destroy</span> function, e.g. <span class="title-ref">mjrf_createTexture</span> and <span class="title-ref">mjrf_destroyTexture</span>. All objects require a [Context](APItypes.md) in order to be created (with the exception of the [Context](APItypes.md) object itself). Additionally, the <span class="title-ref">create</span> functions accept a pointer to a configuration struct (e.g. <span class="title-ref">mjrTextureConfig</span>) which describes the parameters for the object to be created. Each of these structs has a corresponding <span class="title-ref">default</span> function (e.g. <span class="title-ref">mjrf_defaultTextureConfig</span>) which can be used to initialize the struct to default values. The default values are assumed to be <span class="title-ref">0</span> or <span class="title-ref">NULL</span> unless otherwise specified.

#### mjrfContext

The Context is the main entry point for the filament rendering library. It manages all the core filament objects that are responsible for the rendering of an image. All other objects (e.g. Textures, Meshes, Scenes, etc.) need a Context in order to be created.

Otherwise, the main function to use with the Context is *mjrf_render()* which performs the actual rendering of an image.

Filament uses a separate thread for rendering. However, despite that, this API is not thread-safe; calls are expected to be made from a single thread. Due to the asynchronous nature of filament, some APIs provide handles or callbacks to signal when an operation is complete. (Note: for WASM builds, filament does not use a separate thread.)

There are two key differences between the [mjrfContext](APItypes.md) and the classic [mjrContext](APItypes.md). Firstly, the filament context will manage the underlying graphics context itself. This means users do not need to initialize EGL or similar libraries beforehand. Secondly, the filament context is independent of a MuJoCo model. That means you can use a single [mjrfContext](APItypes.md) instance to render images for multiple models.

#### mjrfContextConfig

Parameters for creating [filament graphics context](APItypes.md).


mjrfContextConfig


#### mjrfTexture

A texture is a 2D or 3D (cubemap) image that adds visual detail to a rendered model, such as color or bumpiness, without increasing geometric complexity. A texture is simply a memory buffer holds pixel data, as well as metadata such as the dimensions of the image or the format of the pixels (e.g. 8-bit RGB).

#### mjrfTextureConfig

Parameters for creating a [texture](APItypes.md).


mjrfTextureConfig


#### mjrfTextureData

Binary data payload for a [texture](APItypes.md).


mjrfTextureData


#### mjrfMesh

A mesh describes the surface geometry of an object to be rendered. It is defined as a collection of vertices (i.e. a VertexBuffer), a set of indices (i.e. an IndexBuffer) that describes the order in which the vertices should be processed, and a primitive type that defined how the vertices are to be interpreted (e.g. triangles, lines, etc.) when rendering the surface.

Filament does not directly support normals. Instead, it encodes the normal, tangent, and bitangent into a 4-component quaternion describing the "orientation" of the vertex. Ideally, you should preprocess your assets to generate this data offline, but we will compute it on the fly if needed (at a performance cost).

Vertex data may or may not be interleaved. Interleaved data assumes that the attributes are packed in the order specified in the attributes array, with no padding in-between. Additionally, the <span class="title-ref">data</span> pointer for each attribute is assumed to point to the first element of that type. For non-interleaved data, each attribute is assumed to be stored in a separate array.

Additionally, the bounds of the mesh should be computed in order to allow the filament renderer to perform frustum-based culling. Alternatively, the bounds can be computed at runtime (though there is a small performance cost). If no bounds are provided (or calculated), then frustum culling will not be performed.

#### mjrfMeshConfig

Parameters for creating a [mesh](APItypes.md).


mjrfMeshConfig


#### mjrfMeshData

Binary data for a [mesh](APItypes.md).


mjrfMeshData


#### mjrfScene

A Scene is a collection of [Lights](APItypes.md) and [Renderables](APItypes.md) that describes what is to be rendered.

#### mjrfSceneParams

Parameters for creating a [scene](APItypes.md).

#### mjrfLight

A light is a source of illumination. (Without lights, a rendered image will be completely black.) There are several different types of lights such as directional, spot, point, and image lights.

The primary light in a scene is the image light (also sometimes known as the environment light). This is a light that "surrounds" the entire scene and is defined as a 3D texture. Each "pixel" of the cubemap is interpreted as the color of projected into the scene from a particular direction.

The texture used for image-based lighting can be generated using filament's <span class="title-ref">cmgen</span> tool. The tool should be configured to output a KTX file from your source image. This tool calculates additional data (i.e. the spherical harmonics) and encodes that information into the KTX file.

Directional lights are the next most common type of light and is usually used to simulate the sun; a uniformly colored light that is emitted in a single direction.

Filament only supports a single image and directional light. You can define as many point or spot lights as you want. Each light source (except image based lights) may or may not cast shadows. Each shadow-casting light incurs a performance cost.

#### mjrfLightParams

Parameters for creating a [light](APItypes.md).


mjrfLightParams


#### mjrfRenderable

A renderable is a single object that is to be drawn. It is defined as a combination of a [mjrfMesh](APItypes.md) (i.e. the shape or surface geometry, as described above) and a [mjrfMaterial](APItypes.md) (i.e. a description of how the surface interacts with lights to product the final visual appearance).

#### mjrfRenderableParams

Parameters for creating a [renderable](APItypes.md).


mjrfRenderableParams


#### mjrfMaterial

Materials describe the properties of the surface of a renderable, effectively dictating how the surface interacts with lights to produce a final pixel color in the output image. Different lighting models will be applied to the surface depending on the values of the material properties. There there are three lighting models currently supported:

1\. Metallic-roughness (PBR): this is the preferred model for rendering models based standard metallic-roughness workflows.

2\. Specular-glossiness (non-PBR): this is a legacy model designed to be compatible with classic [mjr](../programming/rendering.md) renderer, though it is not 100% identical.

3\. Unlit: this model ignores lighting and is used for rendering UX or decorative elements like contact forces and labels.


mjrfMaterial


#### mjrfRenderTarget

A RenderTarget is a memory buffer that holds the results of a rendering operation. (This is an alternative to rendering directly to the screen.)

#### mjrfRenderTargetConfig

Parameters for creating a [render target](APItypes.md).


mjrfRenderTargetConfig


#### mjrfRenderRequest

A single rendering operation.


mjrfRenderRequest


#### mjrfReadRequest

A single pixel read operation.


mjrfReadRequest


#### mjrfFrameStats

Information about a single frame of rendering.


mjrfFrameStats


#### mjrfAmbientOcclusionOpts

Rendering options for ambient occlusion. Ambient occlusion is a rendering effect that simulates the blocking of ambient light in small spaces.


mjrfAmbientOcclusionOpts


#### mjrfAntialiasingOpts

Rendering options for antialiasing used to reduce or eliminate the jagged appearance of lines and edges in a rendered image.


mjrfAntialiasingOpts


#### mjrfBloomOpts

Rendering options for bloom effects. This effect simulates the scattering of intense lights by cameras or the human eye.


mjrfBloomOpts


#### mjrfColorGradingOpts

Rendering options for color grading (e.g. tone mapping, color correction, etc.). Color grading allows you to adjust the final appearance of a rendered image by adjusting parameters such as exposure, contrast, saturation, and white balance. It also determines how the HDR (high dynamic range) colours processed by the GPU are converted to LDR (low dynamic range) colours that can be displayed on a monitor.


mjrfColorGradingOpts


#### mjrfDepthOfFieldOpts

Rendering options for depth of field effects for simulating camera focus.


mjrfDepthOfFieldOpts


#### mjrfDitheringOpts

Rendering options for dithering effects. Helps improve smoothness of gradients by adding noise into the final rendered image.


mjrfDitheringOpts


#### mjrfFogOpts

Rendering options for fog effects which can help with depth perception and reduces any "popping" of distance objects.


mjrfFogOpts


#### mjrfHazeOpts

Rendering options for haze effects. The haze is a special effect that can be added infinite planes such that they blend nicely with the skybox.


mjrfHazeOpts


#### mjrfHeadlightOpts

Rendering options for the headlight. The headlight is a special "extra" light that can be used to inspect areas of the scene that are dimly lit.


mjrfHeadlightOpts


#### mjrfMaterialOpts

Rendering options for configuring how the shader materials interpret material properties such as color, specularity, etc.


mjrfMaterialOpts


#### mjrfReflectionOpts

Rendering options for reflections. Reflections can only be applied to planes with that have a reflective material.


mjrfReflectionOpts


#### mjrfShadowOpts

Rendering options for shadows including whether to use hard or soft shadows.


mjrfShadowOpts


#### mjrfSkyboxOpts

Rendering options for the skybox.


mjrfSkyboxOpts


#### mjrfVignetteOpts

Rendering options for vignette effects which darkens the edges of an image similar to a camera lens.


mjrfVignetteOpts


#### mjrfRenderOpts

All rendering options combined into a single struct.


mjrfRenderOpts


### User Interface

For a high-level description of the UI framework, see [User Interface](../programming/ui.md). The names of these struct types are prefixed with `mjui`, except for the main [mjUI](APItypes.md) struct itself.

#### mjuiState

This C struct represents the global state of the window, keyboard and mouse, input event descriptors, and all window rectangles (including the visible UI rectangles). There is only one `mjuiState` per application, even if there are multiple UIs. This struct would normally be defined as a global variable.


mjuiState


#### mjuiThemeSpacing

This structure defines the spacing of UI items in the theme.


mjuiThemeSpacing


#### mjuiThemeColor

This structure defines the colors of UI items in the theme.


mjuiThemeColor


#### mjuiItem

This structure defines one UI item.


mjuiItem


#### mjuiSection

This structure defines one section of the UI.


mjuiSection


#### mjuiDef

This structure defines one entry in the definition table used for simplified UI construction. It contains everything needed to define one UI item. Some translation is performed by the helper functions, so that multiple mjuiDefs can be defined as a static table.


mjuiDef


#### mjUI

This C struct represents an entire UI. The same application could have multiple UIs, for example on the left and the right of the window. This would normally be defined as a global variable. As explained earlier, it contains static allocation for a maximum number of supported UI sections ([mjuiSection](APItypes.md)) each with a maximum number of supported items ([mjuiItem](APItypes.md)). It also contains the color and spacing themes, enable/disable callback, virtual window descriptor, text edit state, mouse focus. Some of these fields are set only once when the UI is initialized, others change at runtime.


mjUI


### Model Editing

The structs below are defined in [mjspec.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjspec.h) and, with the exception of the top level [mjSpec](APItypes.md) struct, begin with the `mjs` prefix. For more details, see the [Model Editing](../programming/modeledit.md) chapter.

#### mjSpec

Model specification.


mjSpec


#### mjsElement

Special type corresponding to any element. This struct is the first member of all other elements; in the low-level C++ implementation, it is not included as a member but via class inheritance. Inclusion via inheritance allows the compiler to `static_cast` an `mjsElement` to the correct C++ object class. Unlike all other attributes of the structs below, which are user-settable by design, modifying the contents of an `mjsElement` is not allowed and leads to undefined behavior.


mjsElement


#### mjsCompiler

Compiler options.


mjsCompiler


#### mjsAuthored

Authored tracking bitmasks for `mjModel` structs.


mjsAuthored


#### mjsBody

Body specification.


mjsBody


#### mjsFrame

Frame specification.


mjsFrame


#### mjsJoint

Joint specification.


mjsJoint


#### mjsGeom

Geom specification.


mjsGeom


#### mjsSite

Site specification.


mjsSite


#### mjsCamera

Camera specification.


mjsCamera


#### mjsLight

Light specification.


mjsLight


#### mjsFlex

Flex specification.

The experimental integer `elastic3d` selects the material for non-interpolated 3D flexes: `0` (the default) is Saint Venant-Kirchhoff (StVK) elasticity, and `1` is simplified Stable Neo-Hookean (SNH) elasticity. Other values are rejected. SNH requires the [discrete integrator](../XMLreference.md). The setting is available only through [mjSpec](APItypes.md), with no MJCF attribute. Specs with SNH enabled cannot be saved to MJCF; compiled models can be saved to MJB. SNH projects each element's material Hessian to positive semidefiniteness before mapping it to vertex coordinates. The discrete solver and Rayleigh damping reuse this projected operator. Energy and elastic forces are unchanged and remain defined through inversion. Material damping has non-positive instantaneous power, but projection does not guarantee inversion-free motion or stability at arbitrary timesteps.


mjsFlex


#### mjsMesh

Mesh specification.


mjsMesh


#### mjsHField

Height field specification.


mjsHField


#### mjsSkin

Skin specification.


mjsSkin


#### mjsTexture

Texture specification.


mjsTexture


#### mjsMaterial

Material specification.


mjsMaterial


#### mjsPair

Pair specification.


mjsPair


#### mjsExclude

Exclude specification.


mjsExclude


#### mjsEquality

Equality specification.


mjsEquality


#### mjsTendon

Tendon specification.


mjsTendon


#### mjsWrap

Wrapping object specification.


mjsWrap


#### mjsActuator

Actuator specification.


mjsActuator


#### mjsSensor

Sensor specification.


mjsSensor


#### mjsNumeric

Custom numeric field specification.


mjsNumeric


#### mjsText

Custom text specification.


mjsText


#### mjsTuple

Tuple specification.


mjsTuple


#### mjsKey

Keyframe specification.


mjsKey


#### mjsDefault

Default specification.


mjsDefault


#### mjsPlugin

Plugin specification.


mjsPlugin


#### mjsOrientation

Alternative orientation specifiers.


mjsOrientation


#### Array handles<span id="mjFloatVecVec"></span><span id="mjFloatVec"></span><span id="mjIntVecVec"></span><span id="mjIntVec"></span><span id="mjStringVec"></span><span id="mjString"></span><span id="mjByteVec"></span><span id="ArrayHandles"></span>

C handles for C++ strings and vector types. When using from C, use the provided *getters* and *setters*.

``` C++
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

### Plugins

The names of these struct types are prefixed with `mjp`. See [Engine plugins](../programming/extension.md) for more details.

#### mjpPlugin

This structure contains the definition of a single engine plugin. It mostly contains a set of callbacks, which are triggered by the compiler and the engine during various phases of the computation pipeline.


mjpPlugin


#### mjSDF

Data structure used by the *Signed Distance Functions* API for computing distances and gradients between SDF geoms.


mjSDF


#### mjpResourceProvider

This data structure contains the definition of a [resource provider](../programming/extension.md). It contains a set of callbacks used for opening and reading resources.


mjpResourceProvider


#### mjpDecoder

This data structure defines a decoder. It contains a set of callbacks used for decoding [mjResource](APItypes.md) into [mjSpec](APItypes.md).


mjpDecoder


#### mjpEncoder

This data structure defines an encoder. It contains a set of callbacks used for encoding of [mjSpec](APItypes.md) and [mjModel](APItypes.md) into [mjResource](APItypes.md).


mjpEncoder


### Batched simulation

These types are used by the *batch API*, declared in [mjbatch.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjbatch.h).

#### mjBatch

An opaque handle to `nsim` simulations of one model and the thread pool that runs them, created by *mjb_makeBatch* and freed by *mjb_deleteBatch*. See [Batched simulation](../programming/simulation.md).

#### mjBatchConfig

The parameters of *mjb_makeBatch*, set to their defaults by *mjb_defaultConfig*.


mjBatchConfig


#### mjBatchRecord

A field or state recorded by *mjb_rollout* after every substep. `buf` holds `n x nstep x size` values for the `n` simulations of the call, in call order, where `size` is the field's number of elements per simulation, or `mj_stateSize(m, spec)` for a state given by the [mjtState](APItypes.md) bits `spec`, in which case the values are [mjtNum](APItypes.md).


mjBatchRecord


## Function types

MuJoCo callbacks have corresponding function types. They are defined in [mjdata.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjdata.h) and in [mjui.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjui.h). The actual callback functions are documented in the [globals](APIglobals.md) page.

### Physics Callbacks

These function types are used by [physics callbacks](APIglobals.md).

#### mjfGeneric

``` C
typedef void (*mjfGeneric)(const mjModel* m, mjData* d);
```

This is the function type of the callbacks [mjcb_passive](APIglobals.md) and [mjcb_control](APIglobals.md).

#### mjfConFilt

``` C
typedef int (*mjfConFilt)(const mjModel* m, mjData* d, int geom1, int geom2);
```

This is the function type of the callback [mjcb_contactfilter](APIglobals.md). The return value is 1: discard, 0: proceed with collision check.

#### mjfSensor

``` C
typedef void (*mjfSensor)(const mjModel* m, mjData* d, int stage);
```

This is the function type of the callback [mjcb_sensor](APIglobals.md).

#### mjfTime

``` C
typedef mjtNum (*mjfTime)(void);
```

This is the function type of the callback [mjcb_time](APIglobals.md).

#### mjfAct

``` C
typedef mjtNum (*mjfAct)(const mjModel* m, const mjData* d, int id);
```

This is the function type of the callbacks [mjcb_act_dyn](APIglobals.md), [mjcb_act_gain](APIglobals.md) and [mjcb_act_bias](APIglobals.md).

#### mjfCollision

``` C
typedef int (*mjfCollision)(const mjModel* m, const mjData* d,
                            mjPreContact* con, int g1, int g2, mjtNum margin);
```

This is the function type of the callbacks in the collision table [mjCOLLISIONFUNC](APIglobals.md).

### Log Callbacks

#### mjfLogHandler

``` C
typedef void (*mjfLogHandler)(const mjLogMessage*);
```

This is the function type of the log handler callback installed via *mju_setLogHandler*. The handler receives all errors, warnings and informational messages as structured [mjLogMessage](APItypes.md) data. It must be thread-safe.

It must not call *mju_error* from within the callback.

### UI Callbacks

These function types are used by the UI framework.

#### mjfItemEnable

``` C
typedef int (*mjfItemEnable)(int category, void* data);
```

This is the function type of the predicate function used by the UI framework to determine if each item is enabled or disabled.

### Resource Provider Callbacks

These callbacks are used by [resource providers](../programming/extension.md).

#### mjfOpenResource

``` C
typedef int (*mjfOpenResource)(mjResource* resource);
```

This callback is for opening a resource; returns zero on failure. Note that if this callback returns zero, the `close` callback will not be called. Therefore, the `open` callback is responsible for cleaning up any allocated memory or resources before returning zero to avoid memory leaks.

#### mjfReadResource

``` C
typedef int (*mjfReadResource)(mjResource* resource, const void** buffer);
```

This callback is for reading a resource. Returns number of bytes stored in buffer and returns -1 on error.

#### mjfCloseResource

``` C
typedef void (*mjfCloseResource)(mjResource* resource);
```

This callback is for closing a resource, and is responsible for freeing any allocated memory.

#### mjfGetResourceDir

``` C
typedef void (*mjfGetResourceDir)(mjResource* resource, const char** dir, int* ndir);
```

This callback is for returning the directory of a resource, by setting dir to the directory string with ndir being size of directory string.

#### mjfResourceModified

``` C
typedef int (*mjfResourceModified)(const mjResource* resource);
```

This callback is for checking if a resource was modified since it was last read. Returns positive value if the resource was modified since last open, 0 if resource was not modified, and negative value if inconclusive.

#### mjfDecode

``` C
typedef mjSpec* (*mjfDecode)(mjResource* resource, const mjVFS* vfs, char* error, int error_sz);
```

This callback is given an opened resource, and is responsible for decoding it into a [mjSpec](APItypes.md). Ownership of the resource and the returned spec is responsibility of the caller. When decoding fails, the callback should return NULL and, if `error` is not NULL, write a description of the failure into `error` (of size `error_sz`).

#### mjfCanDecode

``` C
typedef int (*mjfCanDecode)(const mjResource* resource);
```

This callback is given an opened resource, and is responsible for returning true if the resource can be decoded by the [mjpDecoder](APItypes.md).

#### mjfEncode

``` C
typedef mjtSize (*mjfEncode)(const mjSpec* s, const mjModel* m, const mjVFS* vfs,
                             mjResource* resource);
```

This callback populates the [mjResource](APItypes.md) <span class="title-ref">data</span> member with bytes representing the given spec in the format associated with the owning plugin. This may be called with the associated compiled [mjModel](APItypes.md).

### Batch callbacks

This function type is used by the *batch API*.

#### mjfBatchFunc

``` C
typedef void (*mjfBatchFunc)(const mjModel* m, mjData* d, int sim, void* arg);
```

This is the function type run by *mjb_apply* on simulation `sim`, on a batch thread. The model has the simulation's per-simulation fields applied, and `d` holds its state.

## Notes

This section contains miscellaneous notes regarding data-structure conventions in MuJoCo struct types.

### c-frame variables

[mjData](APItypes.md) contains two arrays with the `c` prefix, which are used for internal calculations: `cdof` and `cinert`, both computed by *mj_comPos*. The `c` prefix means that quantities are with respect to the "c-frame", a frame at the center-of-mass of the local kinematic subtree (`mjData.subtree_com`), oriented like the world frame. This choice increases the precision of kinematic computations for mechanisms that are distant from the global origin.

`cdof`:  
These 6D motion vectors (3 rotation, 3 translation) describe the instantaneous axis of a degree-of-freedom and are used by all Jacobian functions. The minimal computation required for analytic Jacobians is *mj_kinematics* followed by *mj_comPos*.

`cinert`:  
These 10-vectors describe the inertial properties of a body in the c-frame and are used by the Composite Rigid Body algorithm (*mj_crb*). The 10 numbers are packed arrays of lengths (6, 3, 1) with semantics:

`cinert[0-5]`: Upper triangle of the body's inertia matrix.

`cinert[6-8]`: Body mass multiplied by the body CoM's offset from the c-frame origin.

`cinert[9]`: Body mass.

### Convex hulls

The convex hull descriptors are stored in [mjModel](APItypes.md):

``` C
int*      mesh_graphadr;     // graph data address; -1: no graph      (nmesh x 1)
int*      mesh_graph;        // convex graph data                     (nmeshgraph x 1)
```

If mesh `N` has a convex hull stored in [mjModel](APItypes.md) (which is optional), then `m->mesh_graphadr[N]` is the offset of mesh `N`'s convex hull data in `m->mesh_graph`. The convex hull data for each mesh is a record with the following format:

``` C
int numvert;
int numface;
int vert_edgeadr[numvert];
int vert_globalid[numvert];
int edge_localid[numvert+3*numface];
int face_globalid[3*numface];
```

Note that the convex hull contains a subset of the vertices of the full mesh. We use the nomenclature `globalid` to refer to vertex indices in the full mesh, and `localid` to refer to vertex indices in the convex hull. The meaning of the fields is as follows:

`numvert`  
Number of vertices in the convex hull.

`numface`  
Number of faces in the convex hull.

`vert_edgeadr[numvert]`  
For each vertex in the convex hull, this is the offset of the edge record for that vertex in edge_localid.

`vert_globalid[numvert]`  
For each vertex in the convex hull, this is the corresponding vertex index in the full mesh

`edge_localid[numvert+3*numface]`  
This contains a sequence of edge records, one for each vertex in the convex hull. Each edge record is an array of vertex indices (in localid format) terminated with -1. For example, say the record for vertex 7 is: 3, 4, 5, 9, -1. This means that vertex 7 belongs to 4 edges, and the other ends of these edges are vertices 3, 4, 5, 9. In this way every edge is represented twice, in the edge records of its two vertices. Note that for a closed triangular mesh (such as the convex hulls used here), the number of edges is `3*numface/2`. Thus when each edge is represented twice, we have `3*numface edges`. And since we are using the separator -1 at the end of each edge record (one separator per vertex), the length of `edge_localid` is `numvert+3*numface`.

`face_globalid[3*numface]`  
For each face of the convex hull, this contains the indices of the three vertices in the full mesh
