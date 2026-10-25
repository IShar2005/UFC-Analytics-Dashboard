"""
Built-in fallback dataset for the UFC Fighter Analytics & Health Risk Dashboard.

The fighter figures are an approximate snapshot assembled for demonstration and
coursework. Career records and per-minute striking rates change after every
fight, so treat them as illustrative rather than official statistics.
"""

import pandas as pd

# Columns:
#   slpm  = significant strikes landed per minute
#   sapm  = significant strikes absorbed per minute
#   ko_losses = losses by KO/TKO
FIGHTERS = [
    # name, country, weight_class, wins, losses, ko_wins, sub_wins, ko_losses, slpm, sapm, str_acc, str_def, td_avg, debut, last
    ("Khabib Nurmagomedov", "Russia", "Lightweight", 29, 0, 8, 11, 0, 4.10, 1.75, 48, 65, 5.32, 2008, 2020),
    ("Islam Makhachev", "Russia", "Lightweight", 27, 1, 5, 13, 1, 2.50, 1.40, 59, 61, 3.20, 2010, 2025),
    ("Dustin Poirier", "United States", "Lightweight", 30, 9, 15, 8, 3, 5.40, 4.36, 50, 54, 1.30, 2010, 2025),
    ("Justin Gaethje", "United States", "Lightweight", 26, 5, 20, 1, 3, 7.30, 7.60, 60, 54, 0.10, 2011, 2025),
    ("Charles Oliveira", "Brazil", "Lightweight", 35, 11, 10, 21, 3, 3.40, 3.20, 53, 50, 2.30, 2008, 2025),
    ("Conor McGregor", "Ireland", "Lightweight", 22, 6, 19, 1, 2, 5.30, 4.60, 49, 54, 0.70, 2008, 2021),
    ("Ilia Topuria", "Spain", "Lightweight", 17, 0, 7, 8, 0, 4.40, 3.30, 47, 64, 1.90, 2015, 2025),
    ("Max Holloway", "United States", "Featherweight", 27, 8, 12, 2, 1, 7.20, 4.80, 47, 59, 0.20, 2010, 2025),
    ("Alexander Volkanovski", "Australia", "Featherweight", 27, 4, 13, 3, 2, 6.20, 3.40, 57, 59, 1.60, 2012, 2025),
    ("Sean O'Malley", "United States", "Bantamweight", 18, 3, 12, 1, 1, 6.30, 3.60, 60, 62, 0.30, 2015, 2025),
    ("Kamaru Usman", "Nigeria", "Welterweight", 20, 4, 9, 1, 1, 4.40, 2.60, 52, 60, 2.70, 2012, 2025),
    ("Leon Edwards", "United Kingdom", "Welterweight", 22, 5, 7, 3, 0, 2.60, 2.30, 52, 54, 1.20, 2011, 2025),
    ("Robbie Lawler", "United States", "Welterweight", 30, 17, 22, 1, 6, 3.50, 4.20, 45, 60, 0.60, 2001, 2024),
    ("Israel Adesanya", "New Zealand", "Middleweight", 24, 5, 16, 0, 2, 3.90, 3.00, 49, 60, 0.00, 2012, 2025),
    ("Alex Pereira", "Brazil", "Light Heavyweight", 12, 3, 10, 0, 1, 5.20, 3.60, 62, 51, 0.00, 2015, 2025),
    ("Jon Jones", "United States", "Heavyweight", 28, 1, 10, 7, 0, 4.30, 2.20, 58, 64, 1.90, 2008, 2024),
    ("Stipe Miocic", "United States", "Heavyweight", 20, 5, 15, 0, 4, 4.80, 3.60, 50, 55, 1.80, 2010, 2024),
    ("Francis Ngannou", "Cameroon", "Heavyweight", 17, 3, 12, 4, 0, 2.50, 1.40, 52, 41, 0.60, 2013, 2024),
    ("Donald Cerrone", "United States", "Lightweight", 36, 17, 10, 17, 7, 4.50, 4.40, 46, 52, 1.20, 2006, 2022),
    ("Amanda Nunes", "Brazil", "Women's Bantamweight", 23, 5, 13, 4, 2, 5.00, 2.60, 53, 58, 1.80, 2008, 2023),
    ("Valentina Shevchenko", "Kyrgyzstan", "Women's Flyweight", 25, 4, 8, 7, 0, 3.10, 2.20, 51, 63, 2.20, 2003, 2025),
    ("Zhang Weili", "China", "Women's Strawweight", 25, 3, 11, 8, 1, 5.40, 3.50, 51, 56, 2.30, 2013, 2025),
]

COLUMNS = ["Name", "Country", "Weight Class", "Wins", "Losses", "KO Wins", "Sub Wins",
           "KO Losses", "SLpM", "SApM", "Str Acc %", "Str Def %", "TD Avg",
           "Debut Year", "Last Fight Year"]


def load_fighters() -> pd.DataFrame:
    df = pd.DataFrame(FIGHTERS, columns=COLUMNS)
    df["Dec Wins"] = df["Wins"] - df["KO Wins"] - df["Sub Wins"]
    df["Total Fights"] = df["Wins"] + df["Losses"]
    df["Years Active"] = df["Last Fight Year"] - df["Debut Year"]
    df["Win %"] = (df["Wins"] / df["Total Fights"] * 100).round(1)
    df["Strike Differential"] = (df["SLpM"] - df["SApM"]).round(2)
    return df


# Notable UFC venues (fallback for the event map when TheSportsDB is unreachable)
EVENTS = [
    ("UFC 300", "2024-04-13", "T-Mobile Arena", "Las Vegas", "United States", 36.1029, -115.1784, 19165),
    ("UFC 302", "2024-06-01", "Prudential Center", "Newark", "United States", 40.7334, -74.1711, 17640),
    ("UFC 303", "2024-06-29", "T-Mobile Arena", "Las Vegas", "United States", 36.1029, -115.1784, 19265),
    ("UFC 304", "2024-07-27", "Co-op Live", "Manchester", "United Kingdom", 53.4833, -2.2003, 20126),
    ("UFC 305", "2024-08-18", "RAC Arena", "Perth", "Australia", -31.9488, 115.8519, 16053),
    ("UFC 306", "2024-09-14", "Sphere", "Las Vegas", "United States", 36.1209, -115.1622, 16019),
    ("UFC 308", "2024-10-26", "Etihad Arena", "Abu Dhabi", "United Arab Emirates", 24.4673, 54.6047, 12000),
    ("UFC 309", "2024-11-16", "Madison Square Garden", "New York", "United States", 40.7505, -73.9934, 20200),
    ("UFC 311", "2025-01-18", "Intuit Dome", "Inglewood", "United States", 33.9455, -118.3418, 17914),
    ("UFC 312", "2025-02-09", "Qudos Bank Arena", "Sydney", "Australia", -33.8443, 151.0687, 18043),
    ("UFC 314", "2025-04-12", "Kaseya Center", "Miami", "United States", 25.7814, -80.1870, 19442),
    ("UFC 316", "2025-06-07", "Prudential Center", "Newark", "United States", 40.7334, -74.1711, 17905),
]


def load_events() -> pd.DataFrame:
    df = pd.DataFrame(EVENTS, columns=["Event", "Date", "Venue", "City", "Country", "lat", "lon", "Attendance"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df
