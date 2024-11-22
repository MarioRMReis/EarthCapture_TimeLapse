from datetime import date
import pickle
import os

S128 = [0.014854925631009616, 0.011377373345324189]

coords_dict = {
    128:S128
}
"""

with open('utils/coords_dict.pkl', 'wb') as f:
    pickle.dump(coords_dict, f)
        
with open('utils/coords_dict.pkl', 'rb') as f:
    coords_dict = pickle.load(f)

"""

with open('utils/coords_dict.pkl', 'rb') as f:
    coords_dict = pickle.load(f)
    
print(coords_dict)