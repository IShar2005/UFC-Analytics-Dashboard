"""
UFC Fighter Analytics & Health Risk Dashboard
=============================================
A Streamlit web application for exploring UFC fighter statistics, event
locations, and fight analytics, with a health-and-safety focus: a Career
Damage Index (CDI) that estimates cumulative head-trauma exposure to help
flag fighters at elevated risk for CTE.

Author: Isa Sharief
Course: CAP 4104 - Human-Computer Interaction (FIU)

APIs:
    1. TheSportsDB   - UFC event data
    2. REST Countries - fighter nationality details (flags, region, capital)
    3. NCBI PubMed (E-utilities) - CTE research literature and publication trends

Every API call has a fallback, so the app still works offline.
"""

from datetime import date

import pandas as pd
import requests
import streamlit as st

from data import load_events, load_fighters

st.set_page_config(page_title="UFC Fighter Analytics", page_icon="🥊", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2.4rem; font-weight: 700; color: #D20A0A; text-align: center; margin-bottom: 0.2rem; }
    .sub-header  { font-size: 1.05rem; color: #888; text-align: center; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

TIMEOUT = 8
UFC_LEAGUE_ID = 4443
PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


# ──────────────────────────────────────────────
# CAREER DAMAGE INDEX
# ──────────────────────────────────────────────
def compute_cdi(df: pd.DataFrame) -> pd.DataFrame:
    """CDI = (SApM x Total Fights x 0.5) + (KO Losses x 15) + (Years Active x 1.5)

    KO losses are weighted heavily because each loss of consciousness is a
    severe traumatic brain event.
    """
    df = df.copy()
    df["CDI"] = (df["SApM"] * df["Total Fights"] * 0.5
                 + df["KO Losses"] * 15
                 + df["Years Active"] * 1.5).round(1)
    df["Risk Level"] = pd.cut(df["CDI"], bins=[-1, 70, 120, float("inf")],
                              labels=["🟢 LOW", "🟡 MODERATE", "🔴 HIGH"]).astype(str)
    return df


# ──────────────────────────────────────────────
# API LAYER
# ──────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ufc_events():
    """TheSportsDB: past UFC events (eventspastleague endpoint)."""
    try:
        r = requests.get(f"https://www.thesportsdb.com/api/v1/json/3/eventspastleague.php?id={UFC_LEAGUE_ID}",
                         timeout=TIMEOUT)
        r.raise_for_status()
        events = r.json().get("events") or []
        if not events:
            return pd.DataFrame(), False
        df = pd.DataFrame(events)
        keep = {"strEvent": "Event", "dateEvent": "Date", "strVenue": "Venue",
                "strCity": "City", "strCountry": "Country"}
        df = df[[c for c in keep if c in df.columns]].rename(columns=keep)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False), True
    except (requests.RequestException, ValueError, KeyError):
        return pd.DataFrame(), False


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_country(name: str):
    """REST Countries: flag, region, capital, population for one country."""
    try:
        r = requests.get(f"https://restcountries.com/v3.1/name/{name}",
                         params={"fullText": "true", "fields": "name,flags,region,subregion,capital,population"},
                         timeout=TIMEOUT)
        r.raise_for_status()
        c = r.json()[0]
        return {
            "flag": c.get("flags", {}).get("png", ""),
            "region": c.get("region", "Unknown"),
            "subregion": c.get("subregion", ""),
            "capital": ", ".join(c.get("capital", [])) or "—",
            "population": c.get("population", 0),
        }, True
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None, False


FALLBACK_REGIONS = {
    "Russia": "Europe", "United States": "Americas", "Brazil": "Americas", "Ireland": "Europe",
    "Spain": "Europe", "Australia": "Oceania", "Nigeria": "Africa", "United Kingdom": "Europe",
    "New Zealand": "Oceania", "Cameroon": "Africa", "Kyrgyzstan": "Asia", "China": "Asia",
}


@st.cache_data(ttl=86400, show_spinner=False)
def search_pubmed(query: str, max_results: int = 10):
    """PubMed: esearch for IDs, then esummary for article details."""
    try:
        r = requests.get(f"{PUBMED}/esearch.fcgi",
                         params={"db": "pubmed", "term": query, "retmode": "json",
                                 "retmax": max_results, "sort": "relevance"},
                         timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()["esearchresult"]
        ids, total = result.get("idlist", []), int(result.get("count", 0))
        if not ids:
            return pd.DataFrame(), total, True
        s = requests.get(f"{PUBMED}/esummary.fcgi",
                         params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
                         timeout=TIMEOUT)
        s.raise_for_status()
        docs = s.json()["result"]
        rows = []
        for pid in ids:
            d = docs.get(pid, {})
            authors = [a.get("name", "") for a in d.get("authors", [])]
            rows.append({
                "Title": d.get("title", ""),
                "Authors": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
                "Journal": d.get("source", ""),
                "Published": d.get("pubdate", ""),
                "Link": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
            })
        return pd.DataFrame(rows), total, True
    except (requests.RequestException, ValueError, KeyError):
        return pd.DataFrame(), 0, False


@st.cache_data(ttl=86400, show_spinner=False)
def pubmed_trends(start: int = 2005, end: int = 2025):
    """PubMed: count CTE papers per publication year."""
    counts = []
    try:
        for year in range(start, end + 1):
            r = requests.get(f"{PUBMED}/esearch.fcgi",
                             params={"db": "pubmed", "term": f"chronic traumatic encephalopathy AND {year}[pdat]",
                                     "retmode": "json", "retmax": 0},
                             timeout=TIMEOUT)
            r.raise_for_status()
            counts.append({"Year": year, "Papers": int(r.json()["esearchresult"]["count"])})
        return pd.DataFrame(counts).set_index("Year"), True
    except (requests.RequestException, ValueError, KeyError):
        return pd.DataFrame(), False


# ──────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────
fighters = compute_cdi(load_fighters())
fallback_events = load_events()

with st.spinner("Connecting to APIs..."):
    api_events, events_ok = fetch_ufc_events()
    country_info = {c: fetch_country(c) for c in sorted(fighters["Country"].unique())}
    countries_ok = any(ok for _, ok in country_info.values())
    cte_papers, cte_total, pubmed_ok = search_pubmed("chronic traumatic encephalopathy combat sports")

fighters["Region"] = fighters["Country"].map(
    lambda c: (country_info[c][0] or {}).get("region") if country_info[c][1] else FALLBACK_REGIONS.get(c, "Unknown"))

# ──────────────────────────────────────────────
# SIDEBAR: navigation, global filters, API status
# ──────────────────────────────────────────────
st.sidebar.title("🥊 UFC Analytics")
page = st.sidebar.radio("Navigate", ["📊 Dashboard", "🔎 Fighter Database", "📈 Fight Analytics",
                                     "🗺️ Event Map", "⚔️ Fighter Comparison", "🧠 Health & Safety"])

st.sidebar.markdown("### Filters")
all_classes = sorted(fighters["Weight Class"].unique())
selected_classes = st.sidebar.multiselect("Weight class", all_classes, default=all_classes)
min_wins = st.sidebar.slider("Minimum wins", 0, int(fighters["Wins"].max()), 0)

filtered = fighters[fighters["Weight Class"].isin(selected_classes) & (fighters["Wins"] >= min_wins)]

st.sidebar.markdown("### API Status")
for label, ok in [("TheSportsDB Events", events_ok), ("REST Countries", countries_ok),
                  ("PubMed CTE Research", pubmed_ok)]:
    st.sidebar.markdown(f"{'🟢' if ok else '🔴'} {label}")
if not all([events_ok, countries_ok, pubmed_ok]):
    st.sidebar.caption("Offline APIs fall back to the built-in dataset.")

if filtered.empty:
    st.warning("No fighters match the current filters. Widen the weight classes or lower the minimum wins.")
    st.stop()


# ──────────────────────────────────────────────
# PAGES
# ──────────────────────────────────────────────
def page_dashboard():
    st.markdown('<p class="main-header">UFC Fighter Analytics & Health Risk Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Fight statistics with a focus on fighter safety and CTE risk</p>',
                unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fighters", len(filtered))
    c2.metric("Avg Win %", f"{filtered['Win %'].mean():.1f}%")
    c3.metric("Total KO Wins", int(filtered["KO Wins"].sum()))
    c4.metric("High-Risk Fighters", int((filtered["Risk Level"] == "🔴 HIGH").sum()))

    left, right = st.columns(2)
    with left:
        st.subheader("Fighters by Weight Class")
        st.bar_chart(filtered["Weight Class"].value_counts())
    with right:
        st.subheader("How Fights Were Won")
        st.bar_chart(filtered[["KO Wins", "Sub Wins", "Dec Wins"]].sum().rename("Wins"))

    st.subheader("Fighters by World Region")
    st.bar_chart(filtered["Region"].value_counts())
    st.caption("Regions come from the REST Countries API" + ("" if countries_ok else " (offline fallback in use)."))

    if st.checkbox("Show recent UFC events"):
        events = api_events if events_ok else fallback_events.drop(columns=["lat", "lon"])
        if not events_ok:
            st.info("TheSportsDB is unreachable, so these are built-in sample events.")
        st.dataframe(events.head(15), width="stretch", hide_index=True)

    with st.expander("About this app"):
        st.write("This dashboard lets fans, analysts, trainers, and athletic commissions explore UFC fighter "
                 "data. Its Health & Safety page computes a Career Damage Index that estimates cumulative "
                 "head-trauma exposure, connecting fight statistics to CTE research pulled live from PubMed. "
                 "Data sources: TheSportsDB (events), REST Countries (nationalities), and PubMed (research).")


def page_database():
    st.header("🔎 Fighter Database")
    query = st.text_input("Search by fighter name", placeholder="e.g. McGregor")
    sort_by = st.selectbox("Sort by", ["Wins", "Win %", "SLpM", "SApM", "CDI", "Years Active"])

    view = filtered
    if query:
        view = filtered[filtered["Name"].str.contains(query, case=False)]
        if view.empty:
            st.warning(f"No fighters found matching “{query}”.")
            return
        st.success(f"Found {len(view)} fighter(s) matching “{query}”.")

    view = view.sort_values(sort_by, ascending=False)
    cols = ["Name", "Country", "Weight Class", "Wins", "Losses", "Win %", "KO Wins", "Sub Wins",
            "SLpM", "SApM", "CDI", "Risk Level"]
    st.dataframe(view[cols], width="stretch", hide_index=True)
    st.download_button("⬇️ Export as CSV", view[cols].to_csv(index=False), "ufc_fighters.csv", "text/csv")

    st.subheader("Fighter Country Details")
    name = st.selectbox("Select a fighter", view["Name"])
    country = view.loc[view["Name"] == name, "Country"].iloc[0]
    info, ok = country_info.get(country, (None, False))
    if ok and info:
        c1, c2 = st.columns([1, 3])
        if info["flag"]:
            c1.image(info["flag"], width=140)
        c2.markdown(f"**{country}**  \nRegion: {info['region']} ({info['subregion']})  \n"
                    f"Capital: {info['capital']}  \nPopulation: {info['population']:,}")
    else:
        st.info(f"{name} represents {country}. Live country details are unavailable right now.")


def page_analytics():
    st.header("📈 Fight Analytics")
    top_n = st.number_input("Weight classes to display", min_value=1, max_value=len(all_classes),
                            value=min(6, len(all_classes)))
    by_class = filtered.groupby("Weight Class").agg(
        SLpM=("SLpM", "mean"), SApM=("SApM", "mean"), TD_Avg=("TD Avg", "mean"),
        Sub_Wins=("Sub Wins", "sum"), Fighters=("Name", "count"),
    ).sort_values("Fighters", ascending=False).head(int(top_n))

    t1, t2, t3 = st.tabs(["Striking", "Grappling", "Event Attendance"])
    with t1:
        st.subheader("Average strikes landed vs absorbed per minute")
        st.bar_chart(by_class[["SLpM", "SApM"]])
    with t2:
        st.subheader("Takedown average and submission wins")
        st.area_chart(by_class[["TD_Avg", "Sub_Wins"]])
    with t3:
        st.subheader("Attendance at recent events")
        st.line_chart(fallback_events.set_index("Date")["Attendance"])
        st.caption("Attendance figures come from the built-in event dataset.")


def page_map():
    st.header("🗺️ Event Map")
    c1, c2 = st.columns(2)
    start = c1.date_input("Start date", fallback_events["Date"].min().date())
    end = c2.date_input("End date", date.today())
    if start > end:
        st.error("The start date must come before the end date.")
        return
    mask = (fallback_events["Date"].dt.date >= start) & (fallback_events["Date"].dt.date <= end)
    shown = fallback_events[mask]
    if shown.empty:
        st.warning("No events fall inside that date range.")
        return
    st.map(shown, latitude="lat", longitude="lon", size=40000)
    st.dataframe(shown.drop(columns=["lat", "lon"]), width="stretch", hide_index=True)


def page_compare():
    st.header("⚔️ Fighter Comparison")
    names = list(filtered["Name"])
    if len(names) < 2:
        st.warning("At least two fighters are needed. Loosen the sidebar filters.")
        return
    c1, c2 = st.columns(2)
    a = c1.selectbox("Red corner", names, index=0)
    b = c2.selectbox("Blue corner", names, index=1)
    red_color = c1.color_picker("Red corner color", "#D20A0A")
    blue_color = c2.color_picker("Blue corner color", "#1F4E9E")
    if a == b:
        st.warning("Pick two different fighters.")
        return

    fa = filtered.set_index("Name").loc[a]
    fb = filtered.set_index("Name").loc[b]
    for col, f, name, color in [(c1, fa, a, red_color), (c2, fb, b, blue_color)]:
        info, ok = country_info.get(f["Country"], (None, False))
        if ok and info and info["flag"]:
            col.image(info["flag"], width=80)
        col.markdown(f"<h3 style='color:{color}'>{name}</h3>", unsafe_allow_html=True)
        col.write(f"{f['Weight Class']} · {int(f['Wins'])}-{int(f['Losses'])} · CDI {f['CDI']} ({f['Risk Level']})")

    stats = ["Win %", "SLpM", "Str Acc %", "Str Def %", "TD Avg", "KO Wins", "Sub Wins"]
    st.bar_chart(pd.DataFrame({a: fa[stats].astype(float), b: fb[stats].astype(float)}),
                 color=[red_color, blue_color])

    if st.button("Generate Verdict"):
        a_pts = sum(fa[s] > fb[s] for s in stats)
        b_pts = sum(fb[s] > fa[s] for s in stats)
        if a_pts == b_pts:
            st.info(f"Dead even: {a_pts}–{b_pts} across {len(stats)} categories.")
        else:
            winner = a if a_pts > b_pts else b
            st.success(f"Edge: **{winner}** wins {max(a_pts, b_pts)} of {len(stats)} statistical categories.")


def page_health():
    st.header("🧠 Health & Safety: CTE Risk Analytics")
    st.warning("The Career Damage Index is an educational metric for exploring exposure to head trauma. "
               "It is not a medical diagnosis.")

    counts = filtered["Risk Level"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 High risk", int(counts.get("🔴 HIGH", 0)))
    c2.metric("🟡 Moderate risk", int(counts.get("🟡 MODERATE", 0)))
    c3.metric("🟢 Low risk", int(counts.get("🟢 LOW", 0)))

    st.subheader("Career Damage Index Rankings")
    st.latex(r"CDI = (SApM \times Fights \times 0.5) + (KO\ Losses \times 15) + (Years\ Active \times 1.5)")
    ranked = filtered.sort_values("CDI", ascending=False)
    st.dataframe(ranked[["Name", "Weight Class", "SApM", "Total Fights", "KO Losses", "Years Active",
                         "CDI", "Risk Level"]], width="stretch", hide_index=True)
    st.bar_chart(ranked.set_index("Name")["CDI"])

    t1, t2 = st.tabs(["Strike Absorption", "Strike Differential"])
    with t1:
        threshold = st.select_slider("Absorption warning threshold (strikes absorbed per minute)",
                                     options=[2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0], value=4.0)
        st.bar_chart(ranked.set_index("Name")["SApM"])
        flagged = ranked[ranked["SApM"] > threshold]
        if flagged.empty:
            st.success(f"No fighters absorb more than {threshold} strikes per minute.")
        else:
            lines = "\n".join(f"- **{r['Name']}** ({r['Weight Class']}): {r['SApM']} per min, {r['Risk Level']}"
                              for _, r in flagged.iterrows())
            st.error(f"{len(flagged)} fighter(s) exceed {threshold} strikes absorbed per minute:\n{lines}")
    with t2:
        st.caption("Negative values mean a fighter absorbs more than they land, which can signal declining defense.")
        st.bar_chart(ranked.set_index("Name")["Strike Differential"].sort_values())

    st.subheader("KO Loss Tracker")
    ko = ranked[ranked["KO Losses"] > 0].sort_values("KO Losses", ascending=False)
    st.bar_chart(ko.set_index("Name")["KO Losses"])

    st.subheader("Career Length vs Damage")
    st.scatter_chart(ranked, x="Years Active", y="CDI", color="Weight Class", size="SApM")

    st.subheader("Weight Class Risk Comparison")
    wc = ranked.groupby("Weight Class").agg(**{"Avg CDI": ("CDI", "mean"), "Avg SApM": ("SApM", "mean"),
                                               "Fighters": ("Name", "count")}).round(1)
    st.dataframe(wc.sort_values("Avg CDI", ascending=False), width="stretch")

    st.markdown("---")
    st.subheader("📚 CTE Research Literature (via PubMed)")
    if pubmed_ok and not cte_papers.empty:
        st.success(f"PubMed lists {cte_total:,} papers on CTE in combat sports. The most relevant are below.")
        st.dataframe(cte_papers, width="stretch", hide_index=True,
                     column_config={"Link": st.column_config.LinkColumn("Link")})
    else:
        st.info("PubMed is unreachable right now, so live research results can't be shown.")

    st.subheader("🔍 Custom Research Search")
    custom = st.text_area("PubMed query", "chronic traumatic encephalopathy mixed martial arts")
    if st.button("Search PubMed"):
        results, total, ok = search_pubmed(custom)
        if not ok:
            st.error("The PubMed search failed. Check your connection and try again.")
        elif results.empty:
            st.warning("No papers matched that query.")
        else:
            st.success(f"{total:,} matching papers. Showing the top {len(results)}.")
            st.dataframe(results, width="stretch", hide_index=True,
                         column_config={"Link": st.column_config.LinkColumn("Link")})

    st.subheader("📈 CTE Publication Trends")
    if st.checkbox("Load papers-per-year trend (about 20 PubMed requests)"):
        with st.spinner("Counting CTE papers by year..."):
            trends, ok = pubmed_trends()
        if ok:
            st.line_chart(trends)
        else:
            st.error("Couldn't load publication trends from PubMed.")

    with st.expander("How this data could be used"):
        st.markdown("- **Athletic commissions:** flag fighters for extra neurological screening before licensing.\n"
                    "- **Trainers:** watch for rising absorption or a negative strike differential.\n"
                    "- **Researchers:** compare exposure metrics against clinical outcomes.\n"
                    "- **Policy makers:** inform rules on sparring limits and medical suspensions.")


PAGES = {
    "📊 Dashboard": page_dashboard,
    "🔎 Fighter Database": page_database,
    "📈 Fight Analytics": page_analytics,
    "🗺️ Event Map": page_map,
    "⚔️ Fighter Comparison": page_compare,
    "🧠 Health & Safety": page_health,
}
PAGES[page]()
