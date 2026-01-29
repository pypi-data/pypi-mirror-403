# gymDSM
gymDSM (Didactically Supercharged Mod): A modified version of OpenAI Gym.

## What is gymDSM?
**gymDSM** is a small Python package that provides **didactically enhanced** (teaching-friendly) variants of classic OpenAI Gym environments.

### MountainCar

At the moment, gymDSM focuses on **MountainCar** with a small (but important) visual modification: the car’s color reflects the **last action** taken:
- `0` (push left)  → red  
- `1` (no push)    → blue  
- `2` (push right) → green  

The goal is to make it easier to understand what an agent is doing while interacting with the environment.

## Installation

The library gymDSM is on the [Python Package Index](https://pypi.org/project/gymDSM/ "gymDSM page on PyPI").
To install the library, first install `pip` and then use the command `pip install gymDSM`. Alternatively, you can use `pip install gymdsm`. Remember that pip/PyPI treat distribution names case-insensitively.

This project is intended to work with **Gym 0.22**. You can install it with the command `pip install gym==0.22`.

On the other hand, if you want to use `render()`, you need to use the following installation command:

```bash
pip install gymDSM[render]
```

(The command above installs `pygame` as an optional dependency.)


---

## Minimal Working Example (MWE)

### 1) Create the environment using gymDSM.make
This is designed to be easily replaceable with the usual Gym pattern:

```python
import gymDSM as gymDSM

env = gymDSM.make("MountainCar-v0")

obs = env.reset()
done = False

while not done:
    action = env.action_space.sample()  # random policy
    obs, reward, done, info = env.step(action)

env.close()
```

### 2) Render (optional)
```python
import gymDSM as gymDSM
import time

env = gymDSM.make("MountainCar-v0")
obs = env.reset()

done = False
while not done:
    env.render()  # requires pygame
    action = env.action_space.sample()
    obs, reward, done, info = env.step(action)
    time.sleep(0.02)

env.close()
```

## Behavior and supported environments

For now, only the gym's [Mountain Car](https://github.com/openai/gym/blob/master/gym/envs/classic_control/mountain_car.py) environment is supported.

- If you call:
  ```python
  env = gymDSM.make("MountainCar-v0")
  ```
  gymDSM will try to create the gymDSM MountainCar variant (with action-based colors).

- If `env_id` is not supported by gymDSM, or if creating the gymDSM version fails for any reason, `gymDSM.make(...)` falls back to:
  ```python
  gym.make(env_id, ...)
  ```
  using the standard Gym environment.


## License and Acknowledgments

**gymDSM** is an independent open-source project that originates from a fork of OpenAI Gym. This project is **not** affiliated with or endorsed by OpenAI. gymDSM is developed for research and educational purposes. It builds upon the foundation laid by the OpenAI Gym library, and we acknowledge and thank the original OpenAI Gym authors and contributors for their pioneering work.

Both gymDSM and the original OpenAI Gym are released under the MIT License. We have retained the original project's MIT licensing for gymDSM, ensuring that any use or distribution of this fork complies with the same terms. Please see the `LICENSE` file in this repository for the full text of the MIT License.
