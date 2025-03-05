# SentiScan

This project is a SAPP (Sentiment Analysis and Processing Pipeline), a Python-based system for scraping, sentiment analysis, and Google Sheets integration specifically designed for MC Taxi ride hailing app reviews. It automates data extraction, classification, and storage efficiently.

## Features
- **Web Scraping**: Collects data from online sources.
- **Sentiment Analysis**: Classifies text into sentiment categories.
- **Google Sheets Integration**: Stores processed data in Google Sheets.

## Installation
1. Clone this repository:
   ```sh
   git clone https://github.com/your-username/SentiScan.git
   cd SAPP
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Configure your `config.json` file.

## Usage
Run the scraper:
```sh
python SAPP_Scraper.py
```
Run sentiment analysis:
```sh
python SAPP_SentimentAnalysis.py
```
Push data to Google Sheets:
```sh
python SAPP_GoogleSheets.py
```

## License
[MIT License](LICENSE)
