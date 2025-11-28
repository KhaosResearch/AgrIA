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

# Fronted config (default values)
UI_PORT=4200
UI_HOST=locahost
UI_URL=http://${UI_HOST}:${UI_PORT}*

# BackendFronted config (default values)
API_PORT=5000
API_HOST=127.0.0.1
API_URL=http://${API_HOST}:${API_PORT}

# Docker config (default values | for deployment)
DOCKER_PORT=5001
DOCKER_HOST=backend
DOCKER_BACKEND_URL=/api/

```
The folowwing are legacy variables, but needed if you want to use the benchmark pipelines:
```bash
# Contact authors to gain access to these database credentials and files
MINIO_ACCESS_PORT=0000
MINIO_ENDPOINT=255.000.000.000:${MINIO_ACCESS_PORT}
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
  - `benchmark`: Saves benchmark pipelines for both the SR and VLM modules of the project. It generates the corresponding metrics when ran (all credentials needed).
  - `config`: Holds configuration-related files: from constants used all-over to initialization configuration.
  - `endpoints`: Keeps all endpoints access and methods to a single file for each UI component.
  - `services`: Stores files with all the methods that call external services outside of our project scope.
    - `sen2sr`: Super-resolution (SR) module for satellite imagery. Handles image retrieving and upscaling (B02, B03, B04, B08 bands) using a deep learning model.
    - `sigpac_tools_V2`: An updated version of KHAOS Research's [`sigpac-tools`](https://github.com/KhaosResearch/sigpac-tools.git) implementation. Endpoints have been updated and additional functionality has been added.
    - `sr4s`: Previous SR module. Used only for comparisons and benchmarking.
  - `utils`: An assortment of functions and methods that  help all the data processing that mainly comes from endpoint input requests.
- `tests`: A batery of unit tests to test system's main functions and logic, including:
  - Endpoints.
  - Satellite band image retrieval and Super-Resolution.
  - Land Uses - Ecoschemes Classification Algorithm.

```bash
Agria_server
│
├── Dockerfile                            # Docker instructions to build the backend server image.
├── environment-docker.yml                # Conda env used in Docker builds.
├── environment.yml                       # Local development Conda environment file.
├── README.md                             # Project documentation and setup instructions.
├── run.py                                # Application entrypoint used by Gunicorn/Flask.
│
├── assets                                # Stores all server asset files.
│   ├── geojson_assets                    # Geometry files (+ country BBoxes/polygons). GEOMETRY_FILE can live here.
│   │   ├── country_example.json
│   │   ├── spain.json
│   │   └── *.kml                         # GEOMETRY_FILE
│   └── llm_assets                        # LLM init assets: prompts, context files, and metadata JSON.
│       ├── context
│       └── prompts
│
├── server                                # Core backend logic and architecture.
│   ├── __init__.py                       # Marks the package and initializes app modules.
│   │
│   ├── benchmark                         # Benchmarking pipelines for SR and VLM modules.
│   │   ├── sr
│   │   └── vlm
│   │
│   ├── config                            # Core configuration: environment, constants, and clients.
│   │   ├── chat_config.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── env_config.py
│   │   ├── llm_client.py
│   │   └── minio_client.py
│   │
│   ├── endpoints                         # API endpoints grouped by feature or UI component.
│   │   ├── chat.py
│   │   └── parcel_finder.py
│   │
│   ├── services                          # Service layer: external integrations and feature modules.
│   │   ├── chat_service.py
│   │   ├── ecoscheme_payments            # Ecoschemes and CAP logic handler.
│   │   ├── llm_services.py               # Gemini API calls and Chat logic handler.
│   │   ├── parcel_finder_service.py      # Searches parcel and retrieves images from CUBO / Sentinel Hub / MinIO
│   │   ├── sen2sr                        # Satellite SR module using ML (current production).
│   │   ├── sigpac_tools_v2               # Updated SIGPAC API tools (fork + improvements).
│   │   └── sr4s                          # Legacy SR module used only for compatibility/benchmarking.
│   │
│   └── utils                             # Shared helper utilities for data parsing and internal logic.
│       ├── chat_utils.py
│       ├── config_utils.py
│       ├── llm_utils.py
│       └── parcel_finder_utils.py
│
├── temp                                  # Temporary working directory for SR and parcel outputs.
└── test                                  # Unit and integration tests for endpoints and logic.
    ├── endpoints
    │   ├── conftest.py
    │   ├── test_chat.py
    │   └── test_parcel_finder.py
    └── services
        ├── ecoschemes_payment
        ├── sen2sr
        └── sigpac_tools_v2
```

