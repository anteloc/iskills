---
name: api-globals
description: 'MuJoCo C API globals: error, memory and physics callbacks (mjcb_*), the collision function table, string and numeric constants (mjMINVAL, mjNEQDATA, ...), macros and X macros. Use when installing callbacks or needing a MuJoCo constant or macro.'
---

# MuJoCo API Globals

Look up MuJoCo's global function pointers (error, memory and physics
callbacks), the narrow-phase collision table, string and numeric constants,
macros and X macros. Use it to install a callback or to get the exact value
of a constant. The other references are summarized in
[reference](../SKILL.md).

## Callbacks: rules that apply to all of them

- All user callbacks (global function pointers whose name starts with
  `mjcb`) start as NULL. NULL disables them and the default processing runs.
- To install one, set the global pointer to a user function of the correct
  type (function types such as `mjfGeneric` are in
  [api-types](../api-types/SKILL.md)).
- Callbacks are global, not model-specific. Models simulated in parallel share
  the same set.
- There is no automated error checking. Callbacks that need custom MJCF
  parameters (custom fields, user data arrays) should check the model for them
  first, so they disable themselves on a regular model instead of crashing.

## Physics callbacks

| Global | Declaration | What it must do |
|----|----|----|
| `mjcb_control` | `extern mjfGeneric mjcb_control;` | Write `mjData.ctrl`; may also write `mjData.qfrc_applied` and `mjData.xfrc_applied`. The most commonly used callback. |
| `mjcb_passive` | `extern mjfGeneric mjcb_passive;` | Add a custom passive force (depends on position and velocity, not control) in joint space. **Add** to `mjData.qfrc_passive`; do not overwrite it. |
| `mjcb_contactfilter` | `extern mjfConFilt mjcb_contactfilter;` | Replace default collision filtering for each geom pair that passed the broad phase (or is a predefined MJCF pair). |
| `mjcb_sensor` | `extern mjfSensor mjcb_sensor;` | Fill `mjData.sensordata` for user-defined sensors. |
| `mjcb_time` | `extern mjfTime mjcb_time;` | Return time as `mjtNum`; enables the built-in profiler (`mjData.timer`). |
| `mjcb_act_dyn` | `extern mjfAct mjcb_act_dyn;` | Return `mjData.act_dot` for actuators with user dynamics (`mjDYN_USER`). |
| `mjcb_act_gain` | `extern mjfAct mjcb_act_gain;` | Return the gain for actuators with `mjModel.actuator_gaintype` = `mjGAIN_USER`. |
| `mjcb_act_bias` | `extern mjfAct mjcb_act_bias;` | Return the bias for actuators with `mjModel.actuator_biastype` = `mjBIAS_USER`. |

Details that matter:

- **`mjcb_control`** is called from within `mj_forward` and `mj_step`, just
  before controls and applied forces are needed. With the RK integrator it is
  called 4 times per step. Values may depend on position, velocity and
  quantities derived from them, but not on contact forces or anything computed
  later; such fields do not correspond to the current time step. Alternatives:
  set controls before `mj_step`, or call `mj_step1`, set controls, then
  `mj_step2`. Only the callback can change controls between RK sub-steps.
- **`mjcb_passive`**: standard passive forces (springs, dampers, viscosity,
  medium density) are already in `mjData.qfrc_passive` when it runs. For a
  Cartesian force, map it to joint space with the end-effector Jacobian.
- **`mjcb_contactfilter`** replaces the entire default mechanism (contype and
  conaffinity masks, the parent-child filter, welded-body rules). To keep
  contype/conaffinity behaviour, re-implement it in the callback.
- **`mjcb_sensor`** runs only if installed and the model has user-defined
  sensors. It is called once per stage (`mjSTAGE_POS`, `mjSTAGE_VEL`,
  `mjSTAGE_ACC`) and must fill all user sensor values for that stage, with the
  dimensions and data types defined in the MJCF model.
- **`mjcb_time`**: time units are up to you, but `simulate.cc` and the
  `mjTOPIC_TIME_STP` topic assume 1 millisecond. Use a high-resolution timer
  with at least microsecond precision.
- **Actuator callbacks, when not installed**: user dynamics get a
  time-derivative of 0, user gains are set to 1, user biases are set to 0.

## Error callbacks (deprecated)

Use `mju_setLogHandler` instead. See
[simulation-loop](../../c-programming/simulation-loop/SKILL.md) (Installing a
handler). If a custom log handler is installed via `mju_setLogHandler`, these
callbacks are not consulted.

``` C
extern void (*mju_user_error)(const char*);
extern void (*mju_user_warning)(const char*);
```

- `mju_user_error`: called by the default log handler on a fatal error and
  overrides the default error processing. It may `longjmp` out or return, but
  MuJoCo assumes error handlers do not return; if they do, behaviour is
  undefined.
- `mju_user_warning`: called by the default log handler on a warning.

## Memory callbacks

Install custom allocation, e.g. for a MATLAB wrapper whose mex files must use
MATLAB's memory mechanism.

``` C
extern void* (*mju_user_malloc)(size_t);
extern void (*mju_user_free)(void*);
```

- `mju_user_malloc` allocates all heap memory the runtime needs (instead of
  aligned malloc). It must return memory aligned on 8-byte boundaries. The
  C++ parser and compiler sometimes use `new`, which bypasses it.
- `mju_user_free` frees heap memory MuJoCo allocated (instead of aligned
  free).

## Collision table

``` C
extern mjfCollision mjCOLLISIONFUNC[mjNGEOMTYPES][mjNGEOMTYPES];
```

- Pairwise near-phase collision functions indexed by geom type. Only the
  upper-right triangle is used.
- Replace entries with custom routines to replace MuJoCo's collision
  mechanism. A NULL entry means that pair of geom types cannot collide.
- The broad phase is built in and cannot be modified.
- Custom functions get a return buffer of size `mjMAXCONPAIR` and must not
  write more contacts than that.
- Built-in colliders per geom pair are listed in
  [physics-computation](../../physics-computation/SKILL.md) (Pair-wise
  colliders).

## String constants

English names for option lists, for GUI menus and dialogs (`simulate.cc`
uses them; see [c-programming](../../c-programming/SKILL.md)).

| Constant | Names of | Enum |
|----|----|----|
| `mjDISABLESTRING` | disable bits | `mjtDisableBit` |
| `mjENABLESTRING` | enable bits | `mjtEnableBit` |
| `mjTIMERSTRING` | mjData timers | `mjtTimer` |
| `mjTOPICSTRING` | diagnostic log topics | `mjtLogTopic` |
| `mjLABELSTRING` | visual labeling modes | `mjtLabel` |
| `mjFRAMESTRING` | frame visualization modes | `mjtFrame` |
| `mjVISSTRING` | abstract visualization flags (3 strings each) | `mjtVisFlag` |
| `mjRNDSTRING` | OpenGL rendering flags (3 strings each) | `mjtRndFlag` |

`mjVISSTRING` and `mjRNDSTRING` hold three strings per flag: `[0]` flag name;
`[1]` `"0"` or `"1"`, the default (set by `mjv_defaultOption` for
`mjVISSTRING`, by `mjv_makeScene` for `mjRNDSTRING`); `[2]` a one-character
suggested keyboard shortcut. The enums are in
[api-types](../api-types/SKILL.md). The docs do not show the declarations.

## Numeric constants

### Version (mujoco.h)

| Symbol | Value | Meaning |
|----|----|----|
| `mjVERSION_HEADER` | 4000002 | Version of the headers: `(S * 1e6) + (M * 1e3) + P` for "S.M.P" (4.2.1 is 4002001). `mj_version` returns the same for the compiled library. See [VERSIONING.md](https://github.com/google-deepmind/mujoco/blob/main/VERSIONING.md). |

### Engine constants (mjmodel.h unless noted)

| Symbol | Value | Meaning |
|----|----|----|
| `mjMINVAL` | 1E-15 | Minimal value in any denominator or operation where 0 is not allowed; smaller values are almost always silently clamped. (mjtype.h) |
| `mjPI` | π | Used in trig functions and degree-to-radian conversion in the compiler. (mjtype.h) |
| `mjMAXVAL` | 1E+10 | Maximal absolute value in `qpos`, `qvel`, `qacc`; `mj_checkPos`, `mj_checkVel`, `mj_checkAcc` use it to detect instability. (mjtype.h) |
| `mjMINMU` | 1E-5 | Minimal friction coefficient for any included friction dimension (see `condim`); smaller values are clamped. |
| `mjMINIMP` | 0.0001 | Minimal constraint impedance; smaller values are clamped. |
| `mjMAXIMP` | 0.9999 | Maximal constraint impedance; larger values are clamped. |
| `mjMAXCONPAIR` | 50 | Maximal contacts per geom pair; user collision functions must respect it. |
| `mjMAXTREEDEPTH` | 50 | Maximal depth of body and mesh bounding volume hierarchies; exceeding it warns and may prevent ray casting. |
| `mjMAXFLEXNODES` | 27 | Maximal nodes in a trilinear flex element. |
| `mjMINAWAKE` | 10 | Minimal timesteps after a tree wakes before it may sleep again. |

### Array sizes (mjmodel.h)

These sizes are symbolic because they may grow in the future.

| Symbol | Value | Determines |
|----|----|----|
| `mjNEQDATA` | 12 | `mjModel.eq_data` (parameters per equality constraint) |
| `mjNDYN` | 10 | `mjModel.actuator_dynprm` |
| `mjNGAIN` | 10 | `mjModel.actuator_gainprm` |
| `mjNBIAS` | 10 | `mjModel.actuator_biasprm` |
| `mjNPOLY` | 2 | `mjModel.{jnt,tendon}_{stiffness,damping}poly` (nonlinear polynomial coefficients; see [physics-computation](../../physics-computation/SKILL.md)) |
| `mjNFLUID` | 12 | Per-geom fluid parameters of the ellipsoidal model |
| `mjNREF` | 2 | All `mjModel.XXX_solref` fields |
| `mjNIMP` | 5 | All `mjModel.XXX_solimp` fields |
| `mjNSENS` | 3 | `mjModel.sensor_intprm` |
| `mjNSOLVER` | 200 | Iterations with stored statistics in `mjData.solver`; actual count in `mjData.solver_niter` |
| `mjNISLAND` | 20 | Islands with stored statistics in `mjData.solver`; actual count in `mjData.nsolver_island` |

### Visualization (mjvisualize.h)

| Symbol | Value | Meaning |
|----|----|----|
| `mjNGROUP` | 6 | Geom, site, joint, tendon and actuator groups toggled via `mjvOption` |
| `mjMAXLIGHT` | 100 | Lights per scene |
| `mjMAXOVERLAY` | 500 | Characters in overlay text |
| `mjMAXLINE` | 100 | Lines per 2D figure (`mjvFigure`) |
| `mjMAXLINEPNT` | 1001 | Points per figure line; `mjvFigure.linepnt` has length `2*mjMAXLINEPNT` (X and Y) |
| `mjMAXPLANEGRID` | 200 | Grid lines per dimension when rendering planes |

### Rendering (mjrender.h)

| Symbol | Value | Meaning |
|----|----|----|
| `mjNAUX` | 10 | Auxiliary buffers in `mjrContext` |
| `mjMAXTEXTURE` | 1000 | Textures |
| `mjMAXMATERIAL` | 1000 | Materials with textures |

### UI (mjui.h)

| Symbol | Value | Meaning |
|----|----|----|
| `mjMAXUISECT` | 10 | UI sections |
| `mjMAXUIITEM` | 200 | Items per UI section |
| `mjMAXUITEXT` | 300 | Characters in UI fields 'edittext' and 'other' |
| `mjMAXUINAME` | 40 | Characters in any UI name |
| `mjMAXUIMULTI` | 35 | Radio and select items in a UI group |
| `mjMAXUIEDIT` | 7 | Elements in a UI edit list |
| `mjMAXUIRECT` | 25 | UI rectangles |

[mjui.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjui.h)
also defines extended key codes `mjKEY_XXX`, matching GLFW key codes; they are
not listed in the docs.

## Macros

``` C
#define mjDISABLED(x) (m->opt.disableflags & (x))
#define mjENABLED(x) (m->opt.enableflags & (x))
#define mjMAX(a,b) (((a) > (b)) ? (a) : (b))
#define mjMIN(a,b) (((a) < (b)) ? (a) : (b))
#define mjPLUGIN_LIB_INIT(n)                                      \
     static void _mj_init_##n(void) __attribute__((constructor)); \
     static void _mj_init_##n(void)
```

| Macro | Use |
|----|----|
| `mjUSESINGLE` | Compile-time flag; see `mjtNum` in [api-types](../api-types/SKILL.md). |
| `mjDISABLED(x)` | Is a standard feature disabled in the physics options? Assumes `mjModel* m` is defined; `x` is an `mjtDisableBit`. |
| `mjENABLED(x)` | Is an optional feature enabled? Assumes `mjModel* m`; `x` is an `mjtEnableBit`. |
| `mjMAX(a,b)` / `mjMIN(a,b)` | Max / min. For `mjtNum`, use `mju_max` / `mju_min` to avoid repeated evaluation. |
| `mjPLUGIN_LIB_INIT(n)` | Register a plugin before `main()` runs. `n` is a unique identifier that avoids name collisions between plugin init functions. See [engine-plugins](../../c-programming/engine-plugins/SKILL.md). |

## X Macros

Most projects do not need them. MuJoCo uses them internally to allocate the
model. They help wrappers for scripting languages build dynamic structures that
match MuJoCo's data structures. The definitions are in
[mjxmacro.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjxmacro.h)
and
[mjspecmacro.h](https://github.com/google-deepmind/mujoco/blob/main/include/mujoco/mjspecmacro.h).

## Source docs

Verbatim copies, for details not covered above:

- [APIreference/APIglobals.md](references/APIreference-APIglobals.md)
