# Aletheia

| | |
| :--- | :--- |
| **Author** | Ariel Sánchez and The Aletheia Team |
| **Contributors** | Ariel Sánchez, Andres Ruiz, Facundo Rodriguez, Carlos Correa, Andrea Fiorilli, Matteo Esposito, Jenny Gonzalez Jara, Nelson D. Padilla|
| **Source** | [Source code at GitLab](https://gitlab.mpcdf.mpg.de/arielsan/aletheia) |
| **Documentation** | [Documentation at MPCDF Pages](https://aletheia-46606f.pages.mpcdf.de/) |
| **Installation** | `pip install AletheiaCosmo` |
| **Reference** | Sánchez et al. (2025, *in prep*) |

---

**Aletheia** is an accurate and robust Python package that provides emulated predictions for the non-linear matter power spectrum.

At its core, **Aletheia** is based on the **evolution mapping** framework, which provides a high degree of flexibility and allows the emulator to cover a wide cosmology parameter space at continuous redshifts up to $z \approx 4$.

*Aletheia* (Ἀλήθεια), in ancient Greek, means *truth* or *unconcealment*. In mythology, she was the personification of Truth.

## Emulated Parameters

The current release of `Aletheia` is trained on the following key parameters (for more details, see the [full documentation](https://aletheia-46606f.pages.mpcdf.de/emulator_parameters.html)):

| Parameter | Description |
| :--- | :--- |
| $\omega_b$ | Physical baryon density parameter |
| $\omega_c$ | Physical cold dark matter density parameter|
| $n_s$ | Primordial scalar spectral index |
| $\sigma_{12}$ | RMS of matter fluctuations at $R=12\,{\rm Mpc}$ |

The emulator is trained on shape parameters spanning $\pm 5\sigma$ of Planck 2018 constraints and a wide clustering range of $0.2 < \sigma_{12} < 1.0$.

It also robustly handles variations in dark energy through the evolution mapping technique, allowing for inputs of $A_{\rm{s}}$, $w_0$, $w_a$, $\omega_{\rm DE}$ and $\omega_k$.

## Getting Started

You can install the latest stable release of the code directly from PyPI:

```bash
pip install AletheiaCosmo
```

Once installed, you can follow the [Jupyter Notebook tutorial](https://gitlab.mpcdf.mpg.de/arielsan/aletheia/-/blob/main/examples/demo.ipynb) or the [Quick Start Guide](https://aletheia-46606f.pages.mpcdf.de/quick_start.html) for an example of how to make predictions.

A minimal example is as simple as:

```python
import numpy as np
from aletheiacosmo import AletheiaEmu

# 1. Define cosmology using the built-in helper
cosmo_params = AletheiaEmu.create_cosmo_dict(
    h=0.67,
    omega_b=0.0224,
    omega_c=0.120,
    n_s=0.96,
    A_s=2.1e-9,
    model='LCDM'
)

# 2. Initialize the emulator
emu = AletheiaEmu()

# 3. Get the non-linear P(k) at z=1.0
# Scales to be considered, in 1/Mpc
k = np.logspace(-2, 0.3, 100)
z = 1.0
# Return the non-linear power spectrum in units of Mpc^3
p_nonlinear = emu.get_pnl(k, cosmo_params, z)
```

## Developer Version

If you wish to modify the code or contribute to development, you can install the developer version:

```bash
# Clone the repository
git clone [https://gitlab.mpcdf.mpg.de/arielsan/aletheia.git](https://gitlab.mpcdf.mpg.de/arielsan/aletheia.git)
cd aletheia

# Install in editable mode
pip install -e .
```

## License

This package is made publicly available under the [MIT License](LICENSE).

## Project Status

`Aletheia` is under active development. Follow the public repository at <https://gitlab.mpcdf.mpg.de/arielsan/aletheia> to ensure you are always up-to-date with the latest release.

