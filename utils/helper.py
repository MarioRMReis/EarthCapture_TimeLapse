import ee
import json

def get_min_max(config, Satelite, image, region=None, scale=30, bands=None):
    """Compute min and max values for each band in an image."""
    
    # Reduce region to get min and max per band
    stats = image.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=region if region else image.geometry(),
        scale=scale,
        maxPixels=1e13
    )
    
    # Convert results to dictionary
    if Satelite in ["LandSat-8", "LandSat-9"]:
        min_max_values = {band: [stats.get(f'{band}_min').getInfo()/100000 - 0.3, stats.get(f'{band}_max').getInfo()/100000] for band in bands}
    else:
        min_max_values = {band: [stats.get(f'{band}_min').getInfo(), stats.get(f'{band}_max').getInfo()] for band in bands}
    if Satelite == "Sentinel-1":
        min_max_values["VV/VH"] = [0, 2]
    config[Satelite]['min_max_values'] = min_max_values

    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=3)
        
