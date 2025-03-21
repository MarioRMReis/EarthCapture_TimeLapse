# EarthCapture_Timelapse
With a given list of regions of interst it retives all available images in a set timeframe. The available colections are [Sentinel-1](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD), [Sentinel-2](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) and [Landsat-8](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2), [Landsat-9](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC09_C02_T1_L2).

## Description
Taking as an input one or more KML files, extracts the Regions of Interest(ROI), those ROI having the any given shape or size. Those regions are then centered in the choosen window and new Areas are created. Based on the picked colections a request is made to earth engine of all images of those areas in the given timeframe. A mask of the ROI in the created window is created for each Region of the KMLs.

## Install dependencies:
`pip install -r requirements.txt`

## Setup
```sh
git clone https://github.com/MarioRMReis/EarthCapture_TimeLapse.git
cd EarthCapture_TimeLapse
pip install -r requirements.txt
```
## Maize Fields
Regions of interest in this project.
![plot](fig/fields.png)
