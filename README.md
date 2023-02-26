
# Price timeseries trend forecast using price-action zones

A Python Project that forecasts price trends using price-action supply/demand zones for trading pairs in Binance.



## Features

- Gets historical price candles from binance exchange API
- Generates missing candles using interpolation techniques
- Generates average volume transferred in trades in every candles
- Finds "base" candles: RBR, RBD, DBR, DBD
- Finds Fresh S/D zones
- Appends overlapping zones
- Creates price chart that shows fresh S/D zones
## Roadmap

- Find Support/Resistance levels
- Add a boolean field as a feature for zones' that tells if a zone is formed when a S/R level breaks
- Extract more features for zones that can help predict the zone's strength
- Assign a score to every zone that represents the probability of that zone reactiong to price trend using AI tools
- Assign that score to candles after the candles that overlap with a zone as a feature for price timeseries forecasting
- Develop a AI model for forecasting price trend


## Installation

Note: This program is only being tested on Windows 10-11 x64, Python 3.11, so:

- Clone this repository on your PC and extract the folder
- Run the commands below in the Windows CLI:
```
cd "PATH/TO/PROGRAMS/MAIN/FOLDER" 
pip install -r requirements.txt
```
## Examples
![Chart](https://user-images.githubusercontent.com/90606110/221410992-015786e9-87d3-4fe2-ad13-5e9335a2bb36.jpeg)
## Authors

- [@MirbahaMoein](https://www.github.com/MirbahaMoein)

