import json
from pykml import parser

def kml_reader(kml_files):
    aoi_names, aois = [], []  # Initialize lists to store AOI names and coordinates
    for kml in kml_files:
        # Open and parse the KML file
        with open('roi/' + kml, 'r') as f:
            root = parser.parse(f).getroot()
            
        # Define the KML namespace
        namespace = {"kml": 'http://www.opengis.net/kml/2.2'}
        
        # Find all Placemark elements that contain a Polygon
        pms = root.xpath(".//kml:Placemark[.//kml:Polygon]", namespaces=namespace)
        
        roi_string = []  # List to store the coordinates of the regions of interest
        for p in pms:
            # Check if the Placemark has a MultiGeometry element
            if hasattr(p, 'MultiGeometry'):
                # If it does, iterate through all Polygons in the MultiGeometry
                for poly in p.MultiGeometry.Polygon:
                    roi_string.append(poly.outerBoundaryIs.LinearRing.coordinates)
            else:
                # Otherwise, get the coordinates of the single Polygon
                roi_string.append(p.Polygon.outerBoundaryIs.LinearRing.coordinates)

        # Extract the base name of the KML file (without extension)
        dot = kml_files[0].find('.')
        name_kml = kml_files[0][:dot] + '-'
        
        # Process each set of coordinates
        for jdx, r in enumerate(roi_string):
            aoi_names.append(name_kml + str(jdx))  # Create a unique name for each AOI
            roi_str = str(r).split(' ')  # Split the coordinates string into individual points
            aux = []
            for idx, rs in enumerate(roi_str):
                if idx == 0:
                    # Process the first coordinate point
                    n = rs[7::].split(',')
                    aux.append([float(n[i]) for i in range(len(n)-1)])
                elif idx == (len(roi_str)-1):
                    # Skip the last coordinate point
                    break
                else:
                    # Process the intermediate coordinate points
                    n = rs.split(',')
                    aux.append([float(n[i]) for i in range(len(n)-1)])
            aois.append([aux])  # Add the processed coordinates to the AOIs list

    return aoi_names, aois 

def load_config(config_path):
    # Load the configuration file
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

def get_config_param(config, bands_s2, satellite):
    # Remove the bands that we want to skip
    bands_s2 = [b for b in bands_s2 if b not in config[satellite]['skip_bands']]
    
    # [Name, Band] this will be usefill when band combinations are added, [RGB,["B4","B3","B2"]]
    bands_info = []
    for b in bands_s2:
        min_max_band = config[satellite]['min_max_values'][b]
        bands_info.append({"name":b,"bands":b,"min":min_max_band[0],"max":min_max_band[1]})
        
    # Get the added band combinations to the list of bands
    for b in config[satellite]['add_bands']: 
        b_comb = config[satellite]['band_combinations'][b]
        min_band = []
        max_band = []
        for b_c in b_comb:
            min_band.append(config[satellite]['min_max_values'][b_c][0])
            max_band.append(config[satellite]['min_max_values'][b_c][1])
            
        bands_info.insert(0, {"name":b,"bands":b_comb,"min":min_band,"max":max_band})

    # Returns a list with [name, [band1, band2], [min_value1, min_value2], [max_value1, max_value2]]
    return bands_info

def Sentinel1_band_composition(img, channel_bands):
    # In the case of Sentinel-1, the rgb is composed by the devision of the other two used bands Band1/Band2
    #   this splits the Band2 and Band1 if '/' is found in the band name, if not just adds the band to the list
    img_array = []
    if type(channel_bands) == str:
        img_array.append(img.select(channel_bands))
    else:   
        for b in channel_bands:
            if '/' in b:
                b = b.split('/')
                img_array.append(img.select(b[0]).divide(img.select(b[1])))
            else:
                img_array.append(img.select(b))
    
    # Returns an array with the bands to be used in the image composition          
    return img_array