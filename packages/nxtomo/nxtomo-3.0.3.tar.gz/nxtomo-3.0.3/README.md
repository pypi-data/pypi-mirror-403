<p align="left">
  <img src="nxtomo/resources/nxtomo.png" alt="nxtomo" width="180">
</p>

The goal of the `nxtomo` project is to provide a powerful and user-friendly API to create, edit or read [NXtomo](https://manual.nexusformat.org/classes/applications/NXtomo.html) application definition files.


Please find at https://tomotools.gitlab-pages.esrf.fr/nxtomo the latest documentation

```bash
pip install nxtomo
```

Add the optional extras when you need documentation or development tooling:

```bash
pip install nxtomo[doc,test]
```

## Quick Start
Create a minimal NXtomo scan, populate detector data, and save it to disk:

```python
import numpy as np
from pint import get_application_registry

from nxtomo.application.nxtomo import NXtomo
from nxtomo.nxobject.nxdetector import ImageKey

ureg = get_application_registry()

nx = NXtomo()
nx.title = "Demo scan"
nx.energy = 18 * ureg.keV

n_frames = 180
nx.instrument.detector.data = np.random.rand(n_frames, 64, 64).astype(np.float32)
nx.instrument.detector.image_key_control = np.full
    n_frames, ImageKey.PROJECTION.value, dtype=np.uint8
)
nx.sample.rotation_angle = np.linspace(0.0, 180.0, n_frames, endpoint=False) * ureg.degree

output_file = "demo_scan.nx"
nx.save(output_file, data_path="/entry0000")

loaded = NXtomo().load(output_file, data_path="/entry0000")
print(f"Energy: {loaded.energy}, Rotation angles: {loaded.sample.rotation_angle}")

```

Explore additional workflows in the [tutorials](https://tomotools.gitlab-pages.esrf.fr/nxtomo/tutorials/index.html), such as splitting large acquisitions or working with TIFF backends.

## Documentation and Support
- Latest documentation: https://tomotools.gitlab-pages.esrf.fr/nxtomo/
- API reference: https://tomotools.gitlab-pages.esrf.fr/nxtomo/api.html
- Report issues and follow development on GitLab: https://gitlab.esrf.fr/tomotools/nxtomo

## Contributing
Contributions and feedback are welcome. Please open an issue or submit a merge request on GitLab. See the development guide in `doc/development` for details on setting up a local environment and running the test suite.

## License
nxtomo is released under the MIT License. See `LICENSE` for the full text.
