# Fantastic Four — Earth Defence (README & Config Guide)

## 1) Quick start

1. **Requirements**
   - Python 3.13  
   - Tkinter (usually preinstalled on Windows/macOS; on Ubuntu: `sudo apt install python3-tk`)

2. **Run**
   ```bash
   # from the project root
   PYTHONPATH=cps7004c_assessment1 python cps7004c_assessment1/controller/simulator.py
   ```
   - Use the GUI buttons: **Pause/Resume**, **Reset**, and **Speed** slider (steps/sec).

## 3) Files you’ll tweak most

### A) Simulation pacing — `controller/simulator.py`

- **Spawn steps**
  ```python
  #self.surfer_spawn_step = 12    # early pressure (default)
  #self.galactus_spawn_step = 24  # causes short, high-fail runs in this build
  ```
- **World size / bridge count**
  ```python
  target_sites = 7  # number of bridge locations
  ```
- **Default speed**
  ```python
  #self.simulation_speed = 5.0  # steps per second
  ```

### B) Hero energy & recharge — `model/hero.py`

- **Low-energy retreat threshold**
  ```python
  #if self.energy <= 10:
  ```
- **HQ recharge rate**
  ```python
  #self.energy = min(self.max_energy, self.energy + 20)
  ```

### C) Silver Surfer behaviour — `model/silver_surfer.py`

- **Movement speed**
  ```python
  steps = 2
  ```
- **Retreat thresholds / recover**
  ```python
  #if self.energy < 20:
  #if self.energy >= 40:
  ```
- **Cooldown to avoid re-targeting the same bridge**
  ```python
  #self.target_cooldown = 6
  ```
### D) Colours and shapes — `view/gui.py` & `controller/simulator.py`

- **Distinct colours**
  ```For eg. 
  JohnnyStorm:  "#f59e0b",  # orange
  BenGrimm:     "#e11d48",  # rose/pink
  ```
## 4) Difficulty “recipes”

**Easier:**
- Delay Galactus: `self.galactus_spawn_step = 40`
- Reduce bridge count: `target_sites = 5`
- Faster hero recharge: `+25` at HQ
- Slow Surfer: `steps = 1`

**Harder:**
- Earlier Galactus: `self.galactus_spawn_step = 20`
- Increase bridge count: `target_sites = 8`
- Lower HQ recharge: `+10`
- Surfer revisits sooner: `self.target_cooldown = 3`

## 5) Known behaviours

- With **Surfer at 12** and **Galactus at 24** plus **7 bridges**, missions often end quickly and fail frequently.
- Heroes return to HQ and recharge properly.
- To extend runs: tweak `self.galactus_spawn_step`.
