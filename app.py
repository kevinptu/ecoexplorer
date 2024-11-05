import os
import ee
import geemap
import streamlit as st
import json
import time
import zipfile
import glob

# Initialize Google Earth Engine
ee.Initialize()

# Set up the Streamlit app layout and title
st.title("Upload GeoJSON or Shapefile to GEE")

# Instructions for the app
st.write("This app allows you to upload a shapefile or GeoJSON file to Google Earth Engine.")

# Upload widget for file input
uploaded_file = st.file_uploader("Upload a .zip (shapefile) or .geojson file", type=["zip", "geojson"])

# Define helper functions
def get_vector(uploaded_file, out_dir=None):
    if out_dir is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    vector = None
    out_name = None

    # Save uploaded file to disk
    content = uploaded_file.getvalue()
    out_file = os.path.join(out_dir, uploaded_file.name)
    with open(out_file, "wb") as fp:
        fp.write(content)

    if uploaded_file.name.endswith(".zip"):
        out_name = uploaded_file.name[:-4]
        with zipfile.ZipFile(out_file, "r") as zip_ref:
            extract_dir = os.path.join(out_dir, out_name + "_" + geemap.random_string(3))
            zip_ref.extractall(extract_dir)
            files = glob.glob(extract_dir + "/*.shp")
            if files:
                vector = geemap.shp_to_ee(files[0])
            else:
                files = glob.glob(extract_dir + "/*.geojson")
                if files:
                    vector = geemap.geojson_to_ee(files[0])  
    else:
        out_name = uploaded_file.name.replace(".geojson", "").replace(".json", "")
        vector = geemap.geojson_to_ee(out_file)

    return vector, out_name

def import_asset_to_gee(ee_object, asset_name, asset_path="projects/ee-sthiyaku/assets/kevin-tu"):
    asset_id = f"{asset_path}/{asset_name}"
    exportTask = ee.batch.Export.table.toAsset(
        collection=ee_object,
        description="Upload to GEE",
        assetId=asset_id
    )
    exportTask.start()
    while exportTask.active():
        time.sleep(5)
    asset_permission = json.dumps({"writers": [], "all_users_can_read": True, "readers": []})
    ee.data.setAssetAcl(asset_id, asset_permission)

# Map setup
Map = geemap.Map(center=(40, -100), zoom=4, height="750px")

# Handle file upload and display
if uploaded_file:
    st.write("Processing the uploaded file...")
    try:
        fc, layer_name = get_vector(uploaded_file)
        import_asset_to_gee(fc, layer_name)
        st.write("File uploaded successfully.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a file to display it on the map.")