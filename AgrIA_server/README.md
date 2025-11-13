# AgrIA_server

This is the server side of the Agricultural Imaging Assistant (AgrIA). It includes information on how to setup and run the server side of AgrIA.

## Requirements:
- Python 3.10+
- `conda`, for simplified virtual environment package managing.

## Installation & Setup

### Python enviroment creation and activation:
Run the following commnands to create and activate the `agria_server_env` environment.
```bash
conda env create -f environment.yml
conda activate agria_server_env
```

You will also need to install `mamba` locally like this:
```
pip install mamba --no-build-isolation
```
>NOTE: this package requires NVIDIA CUDA Toolkit: `sudo apt install nvidia-cuda-toolkit`
After that, manually install `sen2sr` if needed:
```
pip install sen2sr mlstac git+https://github.com/ESDS-Leipzig/cubo.git -q
```
### System environment setup:
You will need to rename the `.env_example` file to `.env` and complete it with your own data.

**Content of your `.env` file:**
```bash
# Replace variables with your data and rename file to ".env"
GEMINI_API_KEY=YOUR_API_KEY
UI_URL=YOUR_FRONTEND_URL
API_PORT=XXXX
API_URL=http://yourApiDomain.com
```
The folowwing are legacy variables, but needed if you want to use the benchmark pipelines:
```bash
# Contact authors to gain access to these database credentials and files
MINIO_ENDPOINT=255.000.000.000:0000
MINIO_ACCESS_KEY=minio-access-key
MINIO_SECRET_KEY="minio-secret-key"
bucket_name="bucket-name"

GEOMETRY_FILE = path/to/geometry-file.kml

COPERNICUS_CLIENT_ID=copernicusl-client-id
COPERNICUS_CLIENT_SECRET=copernicus-client-secret
COPERNICUS_CONFIG_NAME=any-config-name

```
**To get credentials to access the MinIO image database, contact [KHAOS Research](https://khaos.uma.es/?page_id=101) group.**

### SR Module Dependencies
The current implementation of the SR module is derived from the [SEN2SR](https://github.com/ESAOpenSR/SEN2SR.git) repository, developed by the [ESAOpenSR](https://opensr.eu/) teamby the [ESAOpenSR](https://opensr.eu/) team. Modifications have been made from its original source. For more documentation, please refer to it.

>### NOTE:
> At the time of development, `torch` package would not work with `numpy`'s latest version. Downgrades had to be made to the `numpy` package and the `opencv-python` package as a consequence. The SR module requires `torch`, `rasterio`, `Pillow`, `opencv-python<4.12` and `numpy<2`. These are included in the provided `environment.yml`. If you install the project manually, ensure these packages are present in the correct version.


## Server initialization:
After activating and setting up all environment requirements, run the server by simply using:

```bash
python run.py
```

## Project structure:
By the end of the setup process, your directory structure should look like this:


### Directory overview:
This is a brief overview of each main directory in the project structure:
- `assets`: All resources the server uses are stored here.
  - `geojson_assets`: Ideally, where you'd put your `GEOMETRY_FILE`, but as long as you assign the variable the correct path to the `.kml` file, it doesn't matter. It also stores the country's BBox data
  - `llm_assets`: Stores context files and prompts for LLM initialization and role assignment. JSON files contain file paths information and are accessed by the server to pass to AgrIA as system instructions.
- `server`: Contains all server's main logic components and directories:
  - `benchmar`: Saves benchmark pipelines for both the SR and VLM modules of the project. It generates the corresponding metrics when ran (all credentials needed).
  - `config`: Holds configuration-related files: from constants used all-over to initialization configuration.
  - `endpoints`: Keeps all endpoints access and methods to a single file for each UI component.
  - `services`: Stores files with all the methods that call external services outside of our project scope.
    - `sen2sr`: Super-resolution (SR) module for satellite imagery. Handles image retrieving and upscaling (B02, B03, B04, B08 bands) using a deep learning model.
    - `sigpac_tools_V2`: An updated version of KHAOS Research's [`sigpac-tools`](https://github.com/KhaosResearch/sigpac-tools.git@07145bcaebcdf37bc5b24191950a3f0a666841b4) implementation. Endpoints have been updated and functionality has been added.
    - `sr4s`: Previous SR module. Used only for benchmarking.
  - `utils`: An assortment of functions and methods that  help  all the data processing that mainly comes from endpoint input requests.
- `tests`: A batery of integration tests for the server **(TODO)**.

