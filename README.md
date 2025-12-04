# nanopub-cito-wx

## Overview
The nanopub-cito-creator project is a GUI application designed to facilitate the creation of citation ontologies (CiTOs) from academic papers. It interacts with the CrossRef API to retrieve cited papers and allows users to select citation types for each cited work. The application then generates and publishes a nanopublication containing the selected citations.

## Installation
To install the required dependencies, run the following command:

```
pip install -r requirements.txt
```

## Usage
To start the application, run the following command:

```
python src/cito_creator.py -h
```

This will launch the main window of the application, where you can enter a DOI to fetch cited papers and select citation types.

## Contributing
Contributions to the nanopub-cito-wx project are welcome! Please feel free to submit issues or pull requests.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
