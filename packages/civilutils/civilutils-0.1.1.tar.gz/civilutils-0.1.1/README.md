# civilutils

A lightweight Civil Engineering Python utility package.
 
 ![PyPI - Downloads](https://img.shields.io/pypi/dm/civilutils?color=darkgreen) ![GitHub License](https://img.shields.io/github/license/amrajacivil/civilutils?color=darkgreen) ![PyPI - Status](https://img.shields.io/pypi/status/civilutils) 


![Release](https://img.shields.io/badge/release-automated-blue) ![CI](https://img.shields.io/github/actions/workflow/status/amrajacivil/civilutils/release.yaml?label=CI%2FCD) ![PR Approval](https://img.shields.io/badge/PR%20Approval-required-orange) ![Code Quality](https://img.shields.io/badge/quality-high-success) 


![GitHub tag (with filter)](https://img.shields.io/github/v/tag/amrajacivil/civilutils) ![Static Badge](https://img.shields.io/badge/coverage-93%25-blue) ![Static Badge](https://img.shields.io/badge/covered_lines_of_code-506-blue) 



Overview
--------
civilutils provides practical utilities for civil engineering workflows. The initial focus is a concrete mix design implementation based on Indian Standards (IS). The package is designed to be extended later to support other standards (e.g. ACI) and additional domains such as structural analysis and survey calculations.

Installation
------------
Install from source (example):

```sh
pip install civilutils
```

Quick start
-----------
Example usage (basic):

```python
from civilutils.indian_standards.concrete import (
    ConcreteMixDesign, ConcreteGrade, MaximumNominalSize,
    ExposureCondition, SpecificGravity, Materials
)

sg_list = [
    SpecificGravity(Materials.CEMENT, 3.15),
    SpecificGravity(Materials.FINE_AGGREGATE, 2.60),
    SpecificGravity(Materials.COARSE_AGGREGATE, 2.70),
    SpecificGravity(Materials.WATER, 1.00),
    SpecificGravity(Materials.ADMIXTURE, 1.145),
]

design = ConcreteMixDesign(
    concrete_grade=ConcreteGrade.M25,
    exposure_condition=ExposureCondition.MODERATE,
    specific_gravities=sg_list,
    maximum_nominal_size=MaximumNominalSize.SIZE_20,
    slump_mm=50.0
)

# compute and optionally print summary
result = design.compute_mix_design(display_result=True)
```

API and source
--------------
Detailed documentation is available at:  https://civilutils.readthedocs.io/en/latest/. The documentation site provides downloadable formats — you can download the docs as PDF or EPUB from the Read the Docs site.


Running tests
-------------
Run unit tests:

```sh
python -m unittest discover -s tests -p "test_*.py"
```

Roadmap
-------
- Add support for other standards (ACI, Eurocode).
- Extend modules for structural calculations (beams, columns, load combinations).
- Add survey utilities (coordinate transforms, area/volume computations).
- Improve documentation and examples.

## Contributing

Contributions via PRs are welcome. Please:

- Follow standard Python packaging practices.
- Include tests for new features.
- Keep changes small and documented.


## License

MIT — see [LICENSE](https://github.com/amrajacivil/civilutils)

## If you find this project useful, A small cup helps a lot!

<a href="https://buymeacoffee.com/amraja" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

## More from the developer

Reach out or explore other projects by the developer at: https://amraja.in/


If any link in this README does not redirect or returns "Not Found", please locate the referenced document in the parent GitHub repository: https://github.com/amrajacivil/civilutils