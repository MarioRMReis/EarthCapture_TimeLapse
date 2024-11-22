from datetime import datetime

def check_date(start_date, end_date):
    st_bool = bool(datetime.strptime(start_date, format))
    ed_bool = bool(datetime.strptime(end_date, format))
    if st_bool and ed_bool:
        return
    else:
        raise Exception("The date formate is incorrect, YYYY-MM-DD. Example: 2000-01-11")
