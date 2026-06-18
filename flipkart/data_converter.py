# This will convert the csv data into the Document and then it will return that...

#------------------------------------------------------------------------
# Import Statements
#------------------------------------------------------------------------

import pandas as pd 
from langchain_core.documents import Document


#------------------------------------------------------------------------
# Function Creation for converter
#------------------------------------------------------------------------

def data_converter():

    # Try to fetch the data from CSV file
    try:
        product_data = pd.read_csv('../content/flipkart_product_review.csv')
        data = product_data[['product_title' , 'review']]
        product_list = []
    except Exception as e:
        print("Error in file loading :-" , str(e))
        raise ValueError("File not found")

    # Now iter through all the rows and make an product list that is list of Dict
    for index,row in data.iterrows():
        # Making a temp object
        object = {
            "product_name" : row["product_title"],
            "review" : row['review']
        }
        # Append the object to the product list
        product_list.append(object)

    # Converting that list of Dict into the Document
    docs = []
    for object in product_list:
        metadata = {"product_name":object['product_name']}
        page_content = object['review']
        doc = Document(page_content=page_content , metadata = metadata)
        docs.append(doc)

    return docs
