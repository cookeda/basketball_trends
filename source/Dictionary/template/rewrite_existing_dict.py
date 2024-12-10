import hashlib
import json
import zlib
from sklearn.preprocessing import OneHotEncoder
import numpy as np

# Function to hash the Team Rankings Name
def get_hash(value):
    return format(zlib.crc32(value.encode()), 'x')

# Function to encode a categorical feature and return encoding index mapping
def onehot_encode_column(data, column_name):
    # Extract the values for the column
    column_values = [item[column_name] for item in data]
    # Fit and transform the data
    encoder = OneHotEncoder(sparse_output=False)  # Use sparse_output instead of sparse
    encoded_array = encoder.fit_transform(np.array(column_values).reshape(-1, 1))
    # Create mapping of team names to their encoding index
    encoding_index_map = {team: idx for idx, team in enumerate(column_values)}
    return encoding_index_map, encoder

def reformat_data(input_filename, output_filename, mapping_filename):
    # Step 1: Load the data from the input JSON file
    with open(input_filename, 'r') as file:
        data = json.load(file)

    # Step 2: One-hot encode the "Team Rankings Name" column
    encoding_index_map, encoder = onehot_encode_column(data, "Team Rankings Name")

    # Reformatted data
    reformatted_data = []
    for item in data:
        new_item = {
            "Team Rankings Index": encoding_index_map[item["Team Rankings Name"]],  # Use encoding index
            "Team Rankings Name": item["Team Rankings Name"],
            "DraftKings Name": item["DraftKings Name"],
            "ESPNBet": item["ESPNBet"],  
            "BetMGM": item["BetMGM"],  
            "TeamID": item["TeamID"],
            "PlainText": 'Unknown',
            "Bovada": 'Unkown',
            "Full Name": 'Unknown',
            "Covers": 'Unkown'
        }
        reformatted_data.append(new_item)

    # Step 3: Save the reformatted data back to the output JSON file
    with open(output_filename, 'w') as file:
        json.dump(reformatted_data, file, indent=4)

    # Step 4: Save the encoding mapping to a separate JSON file
    mapping_data = {
        "Team Encoding Mapping": encoding_index_map,
        "OneHotEncoder Categories": encoder.categories_[0].tolist()  # Save category order
    }
    with open(mapping_filename, 'w') as file:
        json.dump(mapping_data, file, indent=4)

# Replace 'input.json' with the path to your actual input file,
# 'output.json' with your desired output file name,
# and 'mapping.json' for the mapping file.
reformat_data('../College/NCB.json', 'NCB.json', 'NCB_mapping.json')
