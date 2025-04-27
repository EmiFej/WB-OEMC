# WB-OEMC
Western Balkan Open Energy Modelling Community

This repository contains the combined [OSeMOSYS](https://github.com/OSeMOSYS)+[PyPSA](https://github.com/PyPSA/PyPSA) power sector models and a workflow to get insights from combined modelling for the Western Balkan Six (WB6) countries. 

## Contents of the repository
- docs
- workflow
- scripts
  - __get_data_XXX.py__ scripts for collecting and harmonizing power sector data from local WB6 TSO's and power utilities.
  - __get_resource_options_XXX.py__ for assessing the variable renewable energy (VRE) potential within the WB6 countries.
- models
  - Submodule repos sourced from Versions of [_OSeMOSYS_](https://github.com/OSeMOSYS/osemosys_global) and [_PyPSA_](https://github.com/PyPSA/pypsa-eur) framework based models.
- data
  - modelling input datasets.
  - copyright/license information about source/processed datasets.
  - links to example/scenario analysis dataset uploaded to zenodo.
- env
  - Config files to reproduce modelling and simulation environments.
- config
  - Configuration files (.yaml/.json) associated to steer the data sourcing, processing, modelling and overall workflow.
- store
  - single file Database/netcdf/hdf5 files to store key inputs,assumptions,results and visuals.
- examples
  - Information about complete setup (data, results, store and instructions) of example scenario runs.


### Additional links and resources
- [Western Balkan Open Energy Modelling Community](www.wb-oemc.com)
  - The webpage includes information about the motivation for creating a fully open-source and open-data model for the region.
- [Google discussion forum](https://groups.google.com/g/wb-oemc)
  - Intended for Q&A, data and experience exchanges, and community building for WB6 modellers and reserachers
 
# Licence
Copyright 2025 WB-OEMC developers<br />The WB-OEMC model is licenced under the open source [MIT Licence](https://github.com/eliasinul/Combined_Modelling_Western_Balkan_Region/blob/main/LICENSE). However, different licenses and terms of use may apply to the various input data.

# Developers
The following individuals have made significant [contributions](https://github.com/eliasinul/Combined_Modelling_Western_Balkan_Region/graphs/contributors) to the development of the WB-OEMC model.

- [Will Usher](https://github.com/willu47) (KTH)
- [Muhammad Elias Islam](https://github.com/eliasinul) (SFU)
- [Emir Fejzic](https://github.com/EmiFej) (KTH)
