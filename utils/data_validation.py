from datetime import  datetime


def check_opts(opts):
    errors = []
    
    # Check if save_folder is a non-empty string
    if not isinstance(opts.save_folder, str) or not opts.save_folder.strip():
        errors.append(f"save_folder should be a non-empty string. Got: {opts.save_folder}")

    # Check if start_date and end_date are valid dates
    try:
        start_date = datetime.strptime(opts.start_date, '%Y-%m-%d')
    except ValueError:
        errors.append(f"Invalid start_date format. Expected YYYY-MM-DD. Got: {opts.start_date}")
    try:
        end_date = datetime.strptime(opts.end_date, '%Y-%m-%d')
    except ValueError:
        errors.append(f"Invalid end_date format. Expected YYYY-MM-DD. Got: {opts.end_date}")

    if int((end_date.date() - start_date.date()).days) <= 0:
        errors.append(f"The end_date sould be later than the starting date:")
    else:
        opts.numImgs = int((end_date.date() - start_date.date()).days)
        
    # Check if window_size is one of the allowed values
    if opts.window_size < 64 and not isinstance(opts.window_size, int):
        errors.append(f"window_size should be a number greater than 64. Got: {opts.window_size}")

    # List of all opted satelites
    if not isinstance(opts.satelites, str):
        errors.append(f"satelites should be a non-empty string.")
    else:
        aux_sSatelites = opts.satelites.replace(" ", "")
        opts.satelites = [satelite.lower() for satelite in aux_sSatelites.split(',')]
    # Check if satelite is a non-empty string
    if not set(opts.satelites).issubset(set(['sentinel','sentinel-1','sentinel-2', 'landsat','landsat-8','Landsat-9', 'all'])):
        errors.append(f"satelites should be one or more of ['sentinel','sentinel-1','sentinel-2', 'landsat','landsat-8','LandSat-9', 'all'], the ones in caps-lock pick more than 1 satelite. Got: {opts.satelites}")

    # Check if enable_mask is a boolean
    if not isinstance(opts.enable_mask, bool):
        errors.append(f"enable_mask should be a boolean. Got: {opts.enable_mask}")

    # Check if super_image is a boolean
    if not isinstance(opts.super_image, bool):
        errors.append(f"super_image should be a boolean. Got: {opts.super_image}")

    # Check if max_cloud_coverage is an integer between 0 and 100
    if not isinstance(opts.max_cloud_coverage, int) or not (0 <= opts.max_cloud_coverage <= 100):
        errors.append(f"max_cloud_coverage should be an integer between 0 and 100. Got: {opts.max_cloud_coverage}")
        
    if opts.image_format not in ['.tiff', '.png', '.jpg']:
        errors.append(f"image_format should be one of ['.tiff', '.png', '.jpg']. Got: {opts.image_format}")

    # Return errors if any
    if errors:
        raise ValueError("Input validation failed with the following errors:\n" + "\n".join(errors))
