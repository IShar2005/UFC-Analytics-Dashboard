# UFC Fighter Analytics & Health Risk Dashboard

A Streamlit web app for exploring UFC fighter statistics, event locations, and fight analytics, built around one question: **which fighters are accumulating the most head trauma?**

Chronic Traumatic Encephalopathy (CTE) is a degenerative brain disease caused by repeated head impacts. This dashboard computes a **Career Damage Index (CDI)** that estimates each fighter's cumulative exposure, classifies them as high, moderate, or low risk, and connects those numbers to live CTE research from PubMed.

Originally built for CAP 4104 (Human-Computer Interaction) at Florida International University.

## Features

| Page | What it does |
|---|---|
| **Dashboard** | Key metrics, weight class and win-method charts, fighters by world region, recent UFC events |
| **Fighter Database** | Searchable, sortable fighter table with CSV export and live country details (flag, region, capital) |
| **Fight Analytics** | Striking, grappling, and event-attendance charts by weight class |
| **Event Map** | Map of UFC event venues with date-range filtering and input validation |
| **Fighter Comparison** | Side-by-side stats, a bar-chart comparison, and a category-by-category verdict |
| **Health & Safety** | CDI rankings, absorption-threshold warnings, strike differential, KO loss tracker, weight class risk, and PubMed research search |

Sidebar filters (weight class and minimum wins) apply across every page.

## Career Damage Index

```
CDI = (Strikes Absorbed per Minute × Total Fights × 0.5) + (KO Losses × 15) + (Years Active × 1.5)
```

KO losses carry the heaviest weight because each loss of consciousness is a severe traumatic brain event. Fighters scoring above 120 are classified as high risk, 70–120 as moderate, and below 70 as low.

The CDI is an educational metric for exploring exposure. It is not a medical diagnosis.

## APIs

- **[TheSportsDB](https://www.thesportsdb.com)** for past UFC events
- **[REST Countries](https://restcountries.com)** for fighter nationality details
- **[NCBI PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)** for CTE research papers and publication trends

Each API call has a timeout and a fallback, so the app keeps working offline using the built-in dataset in `data.py`. The sidebar shows which APIs are live.

## Run it locally

Requires Python 3.9 or newer.

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Project structure

```
app.py            Streamlit app: API layer, CDI calculation, and the six pages
data.py           Built-in fighter and event dataset used as the offline fallback
requirements.txt  Python dependencies
```

## Data note

The built-in fighter statistics are an approximate snapshot for demonstration. Records and per-minute striking rates change after every fight, so they should not be treated as official UFC statistics.

## Tech stack

Python · Streamlit · pandas · Requests · REST APIs
