# gymDSM.py - gymDSM: Library for publishing modified OpenAI Gym environments on PyPI.
# DSM: Didactically Supercharged Mod
###############################################################################################################
# Author: Daniel Saromo-Mori.
# Environment code adapted from OpenAI Gym's classic MountainCar (MIT licensed).
# Base code of the env: https://github.com/openai/gym/blob/master/gym/envs/classic_control/mountain_car.py
#
# License:
#   This project should be distributed under the MIT License. When publishing a fork/derivative,
#   preserve the original MIT copyright notice and license text in your package distribution.
#
# Description:
#
# The key class is:
#    ColoredActionMountainCarEnv(gym.Env)
#        MountainCar with standard physics, but the car color shows the last action:
#          - 0 (push left)  -> red
#          - 1 (no push)    -> blue
#          - 2 (push right) -> green
#
# The key user-facing function is:
#    make(env_id, **kwargs)
#        A drop-in replacement for gym.make(...) that can be used as:
#           import gymdsm as gymDSM
#           env = gymDSM.make("MountainCar-v0")
#
# NOTES
#   - gymDSM.make("MountainCar-v0") returns the modified colored-action version.
#   - If gymDSM does not support env_id, gymDSM.make(...) falls back to gym.make(env_id, ...).
#
# Timeline:
#   24 Jan 2026 - Initial gymDSM.py module scaffolded for PyPI distribution.
###############################################################################################################

__version__ = "1.0.0"

import math
from typing import Any, Dict, List

import numpy as np

try:
    import gym
    from gym import spaces
except ImportError as exc:
    raise ImportError(
        "gymDSM requires the 'gym' package (version 0.22). Install it with: `pip install gym==0.22`."
    ) from exc


# --------------------------------------------------------------------------------------
# Explicit support verification
# --------------------------------------------------------------------------------------
# gymDSM only "supports" (i.e., overrides via gymDSM.make) the IDs listed below.
# If a user calls gymDSM.make(...) with an unsupported ID, we fall back to gym.make(...).
SUPPORTED_ENV_IDS: List[str] = [
    "MountainCar-v0",
]

# This mapping is what makes gymDSM.make("MountainCar-v0") return the modified environment.
# We intentionally DO NOT re-register/override Gym's built-in "MountainCar-v0".
ENV_ALIASES: Dict[str, str] = {
    "MountainCar-v0": "ColoredActionMountainCar-v0",
}

# The set of custom env IDs provided by this library (i.e., registered by register_environments()).
CUSTOM_ENV_IDS = {
    "ColoredActionMountainCar-v0",
}


class ColoredActionMountainCarEnv(gym.Env):
    """
    MountainCar with standard physics, but car color shows the last action:

      - 0 (push left)  -> red
      - 1 (no push)    -> blue
      - 2 (push right) -> green

    Old-style Gym API:
      step(...) -> (obs, reward, done, info)
    """

    metadata = {
        "render.modes": ["human", "rgb_array"],
        "video.frames_per_second": 30,
    }

    def __init__(self):
        super().__init__()

        # ----- physics params (standard MountainCar) -----
        self.min_position = -1.2
        self.max_position = 0.6
        self.max_speed = 0.07
        self.goal_position = 0.5

        self.force = 0.001
        self.gravity = 0.0025

        self.low = np.array([self.min_position, -self.max_speed], dtype=np.float32)
        self.high = np.array([self.max_position, self.max_speed], dtype=np.float32)

        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(self.low, self.high, dtype=np.float32)

        # ----- render state -----
        self.screen_width = 600
        self.screen_height = 400
        self.screen = None
        self.clock = None

        # internal state
        self.state = None
        self.last_action = 1  # default: no push (blue)

        self.reset()

    # ---------- physics (same as classic MountainCar) ----------
    def step(self, action):
        position, velocity = self.state

        velocity += (action - 1) * self.force + math.cos(3 * position) * (-self.gravity)
        velocity = np.clip(velocity, -self.max_speed, self.max_speed)

        position += velocity
        position = np.clip(position, self.min_position, self.max_position)

        if position == self.min_position and velocity < 0:
            velocity = 0.0

        done = bool(position >= self.goal_position)
        reward = -1.0  # standard reward: -1 per step until goal

        self.state = (position, velocity)
        self.last_action = int(action)

        return np.array(self.state, dtype=np.float32), reward, done, {}

    def reset(self):
        # standard init: position in [-0.6, -0.4], velocity 0
        self.state = np.array(
            [np.random.uniform(low=-0.6, high=-0.4), 0.0], dtype=np.float32
        )
        self.last_action = 1  # no push (blue) at start
        return np.array(self.state, dtype=np.float32)

    # ---------- helper: hill height ----------
    def _height(self, xs):
        return np.sin(3 * xs) * 0.45 + 0.55

    # ---------- render using pygame ----------
    def render(self, mode="human"):
        try:
            import pygame
            from pygame import gfxdraw
        except ImportError:
            raise ImportError(
                "pygame is not installed. Run `pip install pygame` to use render()."
            )

        screen_width = self.screen_width
        screen_height = self.screen_height

        world_width = self.max_position - self.min_position
        scale = screen_width / world_width
        carwidth = 40
        carheight = 20

        if self.screen is None:
            pygame.init()
            if mode == "human":
                pygame.display.init()
                self.screen = pygame.display.set_mode((screen_width, screen_height))
            else:  # rgb_array
                self.screen = pygame.Surface((screen_width, screen_height))
        if self.clock is None:
            self.clock = pygame.time.Clock()

        surf = pygame.Surface((screen_width, screen_height))
        surf.fill((255, 255, 255))

        pos = self.state[0]

        xs = np.linspace(self.min_position, self.max_position, 100)
        ys = self._height(xs)
        xys = list(zip((xs - self.min_position) * scale, ys * scale))

        pygame.draw.aalines(surf, (0, 0, 0), False, xys)

        clearance = 10

        l, r, t, b = -carwidth / 2, carwidth / 2, carheight, 0
        coords = []
        for c in [(l, b), (l, t), (r, t), (r, b)]:
            c = pygame.math.Vector2(c).rotate_rad(math.cos(3 * pos))
            coords.append(
                (
                    c[0] + (pos - self.min_position) * scale,
                    c[1] + clearance + self._height(pos) * scale,
                )
            )

        # color by action:
        if self.last_action == 0:      # push left
            car_color = (255, 0, 0)    # red
        elif self.last_action == 2:    # push right
            car_color = (0, 255, 0)    # green
        else:                          # no push
            car_color = (0, 0, 255)    # blue

        gfxdraw.aapolygon(surf, coords, car_color)
        gfxdraw.filled_polygon(surf, coords, car_color)

        # wheels
        for c in [(carwidth / 4, 0), (-carwidth / 4, 0)]:
            c = pygame.math.Vector2(c).rotate_rad(math.cos(3 * pos))
            wheel = (
                int(c[0] + (pos - self.min_position) * scale),
                int(c[1] + clearance + self._height(pos) * scale),
            )

            gfxdraw.aacircle(
                surf, wheel[0], wheel[1], int(carheight / 2.5), (128, 128, 128)
            )
            gfxdraw.filled_circle(
                surf, wheel[0], wheel[1], int(carheight / 2.5), (128, 128, 128)
            )

        # flag
        flagx = int((self.goal_position - self.min_position) * scale)
        flagy1 = int(self._height(self.goal_position) * scale)
        flagy2 = flagy1 + 50
        gfxdraw.vline(surf, flagx, flagy1, flagy2, (0, 0, 0))

        gfxdraw.aapolygon(
            surf,
            [(flagx, flagy2), (flagx, flagy2 - 10), (flagx + 25, flagy2 - 5)],
            (204, 204, 0),
        )
        gfxdraw.filled_polygon(
            surf,
            [(flagx, flagy2), (flagx, flagy2 - 10), (flagx + 25, flagy2 - 5)],
            (204, 204, 0),
        )

        # flip vertically (pygame coords → usual coords)
        surf = pygame.transform.flip(surf, False, True)
        self.screen.blit(surf, (0, 0))

        if mode == "human":
            pygame.event.pump()
            self.clock.tick(self.metadata["video.frames_per_second"])
            pygame.display.flip()
            return None
        elif mode == "rgb_array":
            # return an (H,W,3) numpy array
            return np.transpose(
                np.array(pygame.surfarray.pixels3d(self.screen)), axes=(1, 0, 2)
            )
        else:
            raise NotImplementedError(f"Render mode {mode} not supported")

    def close(self):
        if self.screen is not None:
            try:
                import pygame
                pygame.display.quit()
                pygame.quit()
            except ImportError:
                pass
            self.screen = None
            self.clock = None


def _is_env_registered(env_id: str) -> bool:
    """Best-effort check across Gym versions to avoid re-registering."""
    try:
        return env_id in gym.envs.registry
    except Exception:
        try:
            gym.spec(env_id)
            return True
        except Exception:
            return False


def register_environments() -> None:
    """Registers gymDSM environments with Gym under their custom IDs."""
    try:
        from gym.envs.registration import register
    except Exception:
        return

    env_id = "ColoredActionMountainCar-v0"
    if not _is_env_registered(env_id):
        register(
            id=env_id,
            entry_point="gymDSM:ColoredActionMountainCarEnv",
            max_episode_steps=200,
        )


def _supports_env_id(env_id: str) -> bool:
    """
    Explicit verification of whether gymDSM supports env_id.

    Current behavior:
      - gymDSM supports ONLY the IDs listed in SUPPORTED_ENV_IDS (by design).
      - Any other env_id will be passed through to gym.make(...).
    """
    return env_id in SUPPORTED_ENV_IDS or env_id in CUSTOM_ENV_IDS


def make(env_id: str, *args: Any, **kwargs: Any):
    """
    Drop-in replacement for gym.make(...).

    Explicit verification:
      - If env_id is supported by gymDSM (currently only "MountainCar-v0" plus the custom ID),
        gymDSM.make(...) will try to create the gymDSM version.
      - If env_id is not supported by gymDSM, it will fall back to gym.make(env_id, ...).
      - If creating the gymDSM version fails for any reason, it will also fall back to gym.make(...).

    Example:
      import gymdsm as gymDSM
      env = gymDSM.make("MountainCar-v0")   # returns the colored-action env
    """
    register_environments()

    # Explicit verification: do we support this env_id?
    if _supports_env_id(env_id):
        mapped_id = ENV_ALIASES.get(env_id, env_id)
        try:
            return gym.make(mapped_id, *args, **kwargs)
        except Exception:
            # If anything goes wrong with the gymDSM env, fall back to Gym's env.
            return gym.make(env_id, *args, **kwargs)

    # Not supported by gymDSM -> fall back to Gym.
    return gym.make(env_id, *args, **kwargs)


# Register on import for convenience (so gym.make("ColoredActionMountainCar-v0") works).
register_environments()

__all__ = [
    "ColoredActionMountainCarEnv",
    "register_environments",
    "make",
]

if __name__ == "__main__":
    # Basic self-test / demo when running this file directly:
    #   python gymDSM.py
    #
    # It checks that:
    #   1) gymDSM.make("MountainCar-v0") returns the modified environment (via alias).
    #   2) Unsupported env IDs fall back to gym.make(...).
    #   3) step/reset work without requiring rendering.

    print("gymDSM version:", __version__)

    # 1) Supported ID (should map to the gymDSM variant)
    env_id = "MountainCar-v0"
    env = make(env_id)
    print(f"Created env via gymDSM.make('{env_id}'):", env)

    try:
        obs = env.reset()
        print("Reset returned:", obs)

        done = False
        steps = 0
        while not done and steps < 10:
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            steps += 1

        print("Ran", steps, "steps. done =", done)
    finally:
        env.close()

    # 2) Unsupported ID (should fall back to Gym)
    fallback_id = "CartPole-v1"
    try:
        env2 = make(fallback_id)
        print(f"Created env via gymDSM.make('{fallback_id}') (fallback to Gym):", env2)
        env2.close()
    except Exception as e:
        print(f"Fallback test failed for '{fallback_id}'. Error:", repr(e))
