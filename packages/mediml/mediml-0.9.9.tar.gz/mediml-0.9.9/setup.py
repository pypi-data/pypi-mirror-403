# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['mediml',
 'mediml.biomarkers',
 'mediml.filters',
 'mediml.learning',
 'mediml.processing',
 'mediml.utils',
 'mediml.wrangling']

package_data = \
{'': ['*']}

install_requires = \
['Pillow',
 'PyWavelets',
 'SimpleITK',
 'Sphinx',
 'ipykernel',
 'ipywidgets',
 'isort',
 'jupyter',
 'matplotlib',
 'networkx',
 'neuroCombat',
 'nibabel',
 'nilearn',
 'numpy',
 'numpyencoder',
 'pandas<2.0.0',
 'protobuf',
 'pycaret',
 'pydicom',
 'ray[default]',
 'scikit_image',
 'scikit_learn',
 'scipy',
 'seaborn',
 'setuptools',
 'sphinx-carousel==1.2.0',
 'sphinx-jsonschema==1.19.1',
 'sphinx-rtd-dark-mode==1.2.4',
 'tabulate',
 'tqdm',
 'wget',
 'xgboost']

setup_kwargs = {
    'name': 'mediml',
    'version': '0.9.9',
    'description': 'MEDiml is a Python package for processing and extracting features from medical images',
    'long_description': '<div align="center">\n\n<img src="https://github.com/MEDomicsLab/MEDiml/blob/main/docs/figures/MEDimlLogo150.png?raw=true" style="width:150px;"/>\n\n[![PyPI - Python Version](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10-blue)](https://www.python.org/downloads/release/python-380/)\n[![PyPI - version](https://img.shields.io/badge/pypi-v0.9.8-blue)](https://pypi.org/project/medimage-pkg/)\n[![Continuous Integration](https://github.com/MEDomicsLab/MEDiml/actions/workflows/python-app.yml/badge.svg)](https://github.com/MEDomicsLab/MEDiml/actions/workflows/python-app.yml)\n[![Documentation Status](https://readthedocs.org/projects/mediml/badge/?version=latest)](https://mediml.readthedocs.io/en/latest/?badge=latest)\n[![License: GPL-3](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)\n[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MahdiAll99/MEDimage/blob/main/notebooks/tutorial/DataManager-Tutorial.ipynb)\n\n</div>\n\n## Table of Contents\n  * [1. Introduction](#1-introduction)\n  * [2. Installation](#2-installation)\n  * [3. Generating the documentation locally](#3-generating-the-documentation-locally)\n  * [4. A simple example](#4-a-simple-example)\n  * [5. Tutorials](#5-tutorials)\n  * [6. IBSI Standardization](#6-ibsi-standardization)\n    * [IBSI Chapter 1](#ibsi-chapter-1)\n    * [IBSI Chapter 2](#ibsi-chapter-2)\n  * [7. Acknowledgement](#7-acknowledgement)\n  * [8. Authors](#8-authors)\n  * [9. Statement](#9-statement)\n\n## 1. Introduction\nMEDiml is an open-source Python package that can be used for processing multi-modal medical images (MRI, CT or PET) and for extracting their radiomic features. This package is meant to facilitate the processing of medical images and the subsequent computation of all types of radiomic features while maintaining the reproducibility of analyses. This package has been standardized with the [IBSI](https://theibsi.github.io/) norms.\n\n![MEDiml overview](https://raw.githubusercontent.com/MahdiAll99/MEDimage/main/docs/figures/pakcage-overview.png)\n\n\n## 2. Installation\n\n### Python installation\nThe MEDiml package requires *Python 3.8* or more. If you don\'t have it installed on your machine, follow the instructions [here](https://github.com/MEDomicsLab/MEDiml/blob/main/python.md) to install it.\n\n### Package installation\nYou can easily install the ``MEDiml`` package from PyPI using:\n```\npip install MEDiml\n```\n\nFor more installation options (Conda, Poetry...) check out the [installation documentation](https://mediml.readthedocs.io/en/latest/Installation.html).\n\n## 3. Generating the documentation locally\nThe [documentation](https://mediml.readthedocs.io/en/latest/) of the MEDiml package was created using Sphinx. However, you can generate and host it locally by compiling the documentation source code using :\n\n```\ncd docs\nmake clean\nmake html\n```\n\nThen open it locally using:\n\n```\ncd _build/html\npython -m http.server\n```\n\n## 4. A simple example\n```python\nimport os\nimport pickle\n\nimport MEDiml\n\n# Load MEDiml DataManager\ndm = MEDiml.DataManager(path_dicoms=os.getcwd())\n\n# Process the DICOM files and retrieve the MEDiml object\nmed_obj = dm.process_all_dicoms()[0]\n\n# Extract ROI mask from the object\nvol_obj_init, roi_obj_init = MEDiml.processing.get_roi_from_indexes(\n            med_obj,\n            name_roi=\'{ED}+{ET}+{NET}\',\n            box_string=\'full\')\n\n# Extract features from the imaging data\nlocal_intensity = MEDiml.biomarkers.local_intensity.extract_all(\n                img_obj=vol_obj_init.data,\n                roi_obj=roi_obj_init.data,\n                res=[1, 1, 1]\n            )\n\n# Update radiomics results class\nmed_obj.update_radiomics(loc_int_features=local_intensity)\n\n# Saving radiomics results\nmed_obj.save_radiomics(\n                scan_file_name=\'STS-UdS-001__T1.MRscan.npy\',\n                path_save=os.getcwd(),\n                roi_type=\'GrossTumorVolume\',\n                roi_type_label=\'GTV\',\n            )\n```\n\n## 5. Tutorials\n\nWe have created many [tutorial notebooks](https://github.com/MEDomicsLab/MEDiml/tree/main/notebooks) to assist you in learning how to use the different parts of the package. More details can be found in the [documentation](https://mediml.readthedocs.io/en/latest/tutorials.html).\n\n## 6. IBSI Standardization\nThe image biomarker standardization initiative ([IBSI](https://theibsi.github.io)) is an independent international collaboration that aims to standardize the extraction of image biomarkers from acquired imaging. The IBSI therefore seeks to provide image biomarker nomenclature and definitions, benchmark datasets, and benchmark values to verify image processing and image biomarker calculations, as well as reporting guidelines, for high-throughput image analysis. We participate in this collaboration with our package to make sure it respects international nomenclatures and definitions. The participation was separated into two chapters:\n\n  - ### IBSI Chapter 1\n      [The IBSI chapter 1](https://theibsi.github.io/ibsi1/) is dedicated to the standardization of commonly used radiomic features. It was initiated in September 2016 and reached completion in March 2020. We have created two [jupyter notebooks](https://github.com/MEDomicsLab/MEDiml/tree/main/notebooks/ibsi) for each phase of the chapter and made them available for the users to run the IBSI tests for themselves. The tests can also be explored in interactive Colab notebooks that are directly accessible here:\n      \n      - **Phase 1**: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MahdiAll99/MEDimage/blob/main/notebooks/ibsi/ibsi1p1.ipynb)\n      - **Phase 2**: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MahdiAll99/MEDimage/blob/main/notebooks/ibsi/ibsi1p2.ipynb)\n\n  - ### IBSI Chapter 2\n      [The IBSI chapter 2](https://theibsi.github.io/ibsi2/) was launched in June 2020 and reached completion in February 2024. It is dedicated to the standardization of commonly used imaging filters in radiomic studies. We have created two [jupyter notebooks](https://github.com/MEDomicsLab/MEDiml/tree/main/notebooks/ibsi) for each phase of the chapter and made them available for the users to run the IBSI tests for themselves and validate image filtering and image biomarker calculations from filter response maps. The tests can also be explored in interactive Colab notebooks that are directly accessible here: \n      \n      - **Phase 1**: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MahdiAll99/MEDimage/blob/main/notebooks/ibsi/ibsi2p1.ipynb)\n      - **Phase 2**: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MahdiAll99/MEDimage/blob/main/notebooks/ibsi/ibsi2p2.ipynb)\n\n      Our team at *UdeS* (a.k.a. Université de Sherbrooke) has already submitted the benchmarked values to the [IBSI uploading website](https://ibsi.radiomics.hevs.ch/).\n\n---\n**Miscellaneous**\n\nYou can avoid the next steps (Jupyter installation and environment setup) if you installed the package using Conda or Poetry according to the documentation.\n\n---\n\nYou can view and run the tests locally by installing the [Jupyter Notebook](https://jupyter.org/) application on your machine:\n```\npython -m pip install jupyter\n```\nThen add the installed `MEDiml` environment to the Jupyter Notebook kernels using:\n\n```\npython -m ipykernel install --user --name=MEDiml\n```\n\nThen access the IBSI tests folder using:\n\n```\ncd notebooks/ibsi/\n```\n\nFinally, launch Jupyter Notebook to navigate through the IBSI notebooks using:\n\n```\njupyter notebook\n```\n\n## 7. Acknowledgement\nMEDiml is an open-source package developed at the [MEDomicsLab](https://www.medomicslab.com/en/) laboratory with the collaboration of the international consortium [MEDomics](https://www.medomics.ai/). We welcome any contribution and feedback. Furthermore, we wish that this package could serve the growing radiomics research community by providing a flexible as well as [IBSI](https://theibsi.github.io/) standardized tool to reimplement existing methods and develop new ones.\n\n## 8. Authors\n* [MEDomicsLab](https://www.medomicslab.com/en/): Research laboratory at Université de Sherbrooke & McGill University.\n* [MEDomics](https://github.com/medomics/): MEDomics consortium.\n\n## 9. Statement\n\nThis package is part of https://github.com/medomics, a package providing research utility tools for developing precision medicine applications.\n\n```\nCopyright (C) 2024 MEDomics consortium\n\nGPL3 LICENSE SYNOPSIS\n\nHere\'s what the license entails:\n\n1. Anyone can copy, modify and distribute this software.\n2. You have to include the license and copyright notice with each and every distribution.\n3. You can use this software privately.\n4. You can use this software for commercial purposes.\n5. If you dare build your business solely from this code, you risk open-sourcing the whole code base.\n6. If you modify it, you have to indicate changes made to the code.\n7. Any modifications of this code base MUST be distributed with the same license, GPLv3.\n8. This software is provided without warranty.\n9. The software author or license can not be held liable for any damages inflicted by the software.\n```\n\nMore information on about the [LICENSE can be found here](https://github.com/MEDomicsLab/MEDiml/blob/main/LICENSE.md)\n',
    'author': 'MEDomics Consortium',
    'author_email': 'medomics.info@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://mediml.app/',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8.0,<=3.10',
}


setup(**setup_kwargs)
