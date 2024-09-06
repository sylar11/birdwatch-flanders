# Birdwatch visualizations

This repository contains the code used to modify and merge data for the
Birdwatch Flanders visualizations.

Note: `/qgis` contains the QGIS (3.34.10-Prizren LTR) project file used to create the visualizations as well as the labels. To use the symbology load the dataset from `/data/merged.tiff`

## Modifications to the datasets

    - The hedges dataset originally contained values ranging from 0 to just over 9700. I am assuming this is a miscalculation problem so I am dividing all values by 10000 to get our desired range of 0 to 0.97.

    - The datasets had no nodata value set, which makes it a pain to visualize so the nodata value has been set to -9999.

## Installation

This project was set up using `poetry`

From the root of the project, run the following commands:

```zsh
poetry install
```

```zsh
poetry shell
```

## Contact
For questions regarding the code or methodology, get in touch with me on:
- [GitHub](https://github.com/jzvolensky)
- [Email](mailto:juraj.zvolensky@eurac.edu)

or simply open an issue in this repository.
