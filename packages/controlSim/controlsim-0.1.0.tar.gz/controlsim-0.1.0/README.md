# ControlSim

A Python package for simulating delay control systems with PID controller implementation.

## Overview

ControlSim provides tools to simulate control systems with input delays using state-space representations and transfer functions. It includes:

- **ProcessDefinition**: Simulates a plant model with configurable delays
- **PIDController**: Implements a PID controller with derivative filtering
- **Tuning Methods**: IIMC (Indirect-IMC-PID) and IDA2 controller tuning algorithms

## Features

- Support for transfer function and state-space representations
- Input delay simulation using circular buffer
- PID controller with filtered derivative action
- Gain and phase margin calculations
- IIMC and IDA2 automatic controller tuning methods
- Marginal stability checking

## Installation

Install from PyPI:

```bash
pip install controlSim
```

Or install from source:

```bash
git clone https://github.com/vkbharatv/controlSim.git
cd controlSim
pip install -e .
```

## Quick Start

```python
import control as ctrl
from controlsim import ProcessDefinition, PIDController
import numpy as np

# Define a transfer function
s = ctrl.TransferFunction.s
G = 1 / ((s + 1) * (0.7 * s + 1))

# Create process with 2-second delay
process = ProcessDefinition(G, delay_time=2.0, dt=0.01)

# Create and tune PID controller
pid = PIDController(dt=0.01)
Kp, Ki, Kd = pid.IIMC_tuning(process, theta=2.0, l=0.5)

# Simulate for 100 seconds
setpoint = 1.0
for _ in range(10000):
    output = process.y[-1][0]
    control_signal = pid.compute(setpoint, output)
    process.step(control_signal)

# Analyze margins
gain_margin, phase_margin, wgc, wpc = process.gain_phase_margin()
print(f"Gain Margin: {gain_margin} dB")
print(f"Phase Margin: {phase_margin}°")
```

## API Reference

### ProcessDefinition

Represents a continuous-time process with input delay.

```python
ProcessDefinition(tf, delay_time, dt=0.01, Total_time=10)
```

**Parameters:**
- `tf`: Control system transfer function
- `delay_time`: Input delay in seconds
- `dt`: Simulation step size (default: 0.01)
- `Total_time`: Total simulation time (default: 10)

**Methods:**
- `step(u)`: Advance simulation by one step with input u
- `reset()`: Reset simulation state
- `marginal_stability()`: Check if system is marginally stable
- `gain_phase_margin(omega)`: Calculate gain and phase margins

### PIDController

Implements a discrete-time PID controller with derivative filtering.

```python
PIDController(Kp=1.0, Ki=0.0, Kd=0.0, dt=0.01, N=100)
```

**Parameters:**
- `Kp`: Proportional gain
- `Ki`: Integral gain
- `Kd`: Derivative gain
- `dt`: Sampling time
- `N`: Derivative filter coefficient

**Methods:**
- `compute(setpoint, measurement)`: Calculate control output
- `reset()`: Reset integral and derivative states
- `update_gains(Kp, Ki, Kd)`: Update controller gains
- `IIMC_tuning(process, theta, l)`: IIMC-based automatic tuning
- `IDA2_tuning(rho)`: IDA2-based automatic tuning

## Requirements

- Python 3.8+
- control >= 0.9.4
- numpy >= 1.20.0
- scipy >= 1.7.0
- matplotlib >= 3.3.0

## Citation

If you use this package in your research, please cite:

```bibtex
@software{controlsim2026,
  author = {Bharat Verma},
  title = {ControlSim: Delay Control System Simulation},
  year = {2026},
  url = {https://github.com/vkbharatv/controlSim},
  orcid = {0000-0001-7600-7872}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Dr. Bharat Verma  
The LNMIIT, Jaipur, India  
ORCID: [0000-0001-7600-7872](https://orcid.org/0000-0001-7600-7872)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This software is provided for educational and research purposes. The authors are not responsible for any damages or losses resulting from the use of this software.
