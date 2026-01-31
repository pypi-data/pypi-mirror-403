# RebelAI

**Text → Physics Simulation in one line.**
```python
import rebelai

model = rebelai.generate("kitchen table with coffee mugs")
# That's it. You have a physics-ready MuJoCo model.
```

## The Problem

You want to simulate a robot in a realistic environment. Today that means:
- Manually modeling scenes in Blender (hours)
- Writing collision geometry by hand (tedious)
- Tuning physics properties (trial and error)

## The Solution

Describe what you want. Get a MuJoCo model.
```python
import rebelai
import mujoco

# Generate any scene from text
model = rebelai.generate("cluttered office desk with laptop and coffee cup")

# Full MuJoCo API - do whatever you want
data = mujoco.MjData(model)
mujoco.mj_step(model, data)
```

RebelAI handles:
- **World Labs API** → Generate 3D scenes from text
- **Collision geometry** → Automatic convex decomposition
- **Physics properties** → Mass, friction, contacts
- **MJCF generation** → Ready for MuJoCo

## Install
```bash
pip install rebelai
```

## Quick Start
```bash
# Set your World Labs API key
export WORLD_LABS_API_KEY="wl_xxx"
```
```python
import rebelai

# From text prompt
model = rebelai.generate("red sports car on a driveway")

# Or from existing mesh file
model = rebelai.load("scene.glb")
```

## Why RebelAI?

| Without RebelAI | With RebelAI |
|-----------------|--------------|
| Model scene in Blender | `generate("kitchen")` |
| Export, fix mesh issues | Automatic |
| Write collision geometry | Automatic |
| Tune mass/friction | Automatic |
| Debug MJCF XML | Just works |

---

## Configuration

```python
from rebelai import generate, ConversionConfig, CollisionMethod

config = ConversionConfig(
    collision_method=CollisionMethod.CONVEX_DECOMPOSITION,
    coacd_threshold=0.08,  # Coarser = fewer hulls, faster sim
    density=500.0,         # kg/m³
)

model = generate("wooden desk", config=config)
```

### Collision Methods

| Method | Description |
|--------|-------------|
| `CONVEX_DECOMPOSITION` | Multiple convex hulls via CoACD (default) |
| `CONVEX_HULL` | Single convex hull |
| `BOUNDING_BOX` | Axis-aligned box |
| `PRIMITIVES` | Fit box/sphere/cylinder |

### Error Handling

```python
from rebelai import generate, WorldLabsAuthError, WorldLabsAPIError

try:
    model = generate("office chair")
except WorldLabsAuthError:
    print("Check your API key")
except WorldLabsAPIError as e:
    print(f"Generation failed: {e}")
```

## API Reference

### `rebelai.generate(prompt, api_key=None, config=None, quality="standard")`
Generate scene from text → MuJoCo model

### `rebelai.load(source, config=None)`
Load mesh file → MuJoCo model

### `rebelai.to_mjcf(source, config=None)`
Convert mesh → MJCF XML string

## License

MIT
