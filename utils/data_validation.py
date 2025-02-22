import ee
from datetime import date, timedelta, datetime


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

    # Check if satelite is a non-empty string
    if opts.satelite not in ['SENTINEL','Sentinel-1','Sentinel-2', 'LANDSAT','Landsat-8','Landsat-9', 'ALL'] or not isinstance(opts.satelite, str):
        errors.append(f"satelite should be one or more of ['Sentinel','Sentinel-1','Sentinel-2', 'Landsat','Landsat-8','Landsat-9', 'ALL'], the ones in caps-lock pick more than 1 satelite, and should be a non-empty string. Got: {opts.satelite}")

    # Check if enable_mask is a boolean
    if not isinstance(opts.enable_mask, bool):
        errors.append(f"enable_mask should be a boolean. Got: {opts.enable_mask}")

    # Check if super_image is a boolean
    if not isinstance(opts.super_image, bool):
        errors.append(f"super_image should be a boolean. Got: {opts.super_image}")

    # Check if max_cloud_coverage is an integer between 0 and 100
    if not isinstance(opts.max_cloud_coverage, int) or not (0 <= opts.max_cloud_coverage <= 100):
        errors.append(f"max_cloud_coverage should be an integer between 0 and 100. Got: {opts.max_cloud_coverage}")

    # Return errors if any
    if errors:
        raise ValueError("Input validation failed with the following errors:\n" + "\n".join(errors))
