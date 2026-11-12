from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Titanic Explorer", page_icon="🚢", layout="wide")

# Change to Path(__file__).parent / "src" / "titanic.csv" if the app sits outside src/
DATA_PATH = 'data/titanic (1).csv'

ORDERS = {
    "class": ["First", "Second", "Third"],
    "survival": ["Died", "Survived"],
    "age_group": ["child", "teen", "young adult", "adult", "senior"],
}
COLORS = {"Died": "#D95D4A", "Survived": "#0F766E"}


@st.cache_data
def load_data(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower()
    df["class"] = df["pclass"].map({1: "First", 2: "Second", 3: "Third"})
    df["survival"] = df["survived"].map({0: "Died", 1: "Survived"})
    df["port"] = df["embarked"].map({"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"})
    df["family_size"] = df["sibsp"] + df["parch"] + 1
    df["title"] = df["name"].str.extract(r",\s*([^\.]+)\.", expand=False)
    df["age_group"] = pd.cut(
        df["age"], [0, 12, 18, 35, 60, 80],
        labels=ORDERS["age_group"],
    )
    return df


full_df = load_data(DATA_PATH)

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
classes = st.sidebar.multiselect("Class", ORDERS["class"], default=ORDERS["class"])
sexes = st.sidebar.multiselect("Sex", sorted(full_df["sex"].unique()), default=sorted(full_df["sex"].unique()))
ports = st.sidebar.multiselect(
    "Port", sorted(full_df["port"].dropna().unique()), default=sorted(full_df["port"].dropna().unique())
)

df = full_df[
    full_df["class"].isin(classes)
    & full_df["sex"].isin(sexes)
    & (full_df["port"].isin(ports) | full_df["port"].isna())
]

# ---------------- Header ----------------
st.title("🚢 Interactive Titanic")
st.caption("Plotly charts from the Session 7 lab, shown in Streamlit")

st.image("utils/10294_Prod.png")

c1, c2, c3 = st.columns(3)
c1.metric("Passengers", len(df))
c2.metric("Survival rate", f"{df['survived'].mean():.1%}" if len(df) else "n/a")
c3.metric("Median fare", f"{df['fare'].median():.2f}" if len(df) else "n/a")

if df.empty:
    st.warning("No passengers match these filters.")
    st.stop()

tab_data, tab_dist, tab_groups, tab_rel = st.tabs(
    ["📋 Data", "📊 Distributions", "👥 Groups", "🔗 Relationships"]
)

# ---------------- Data ----------------
with tab_data:
    st.subheader("Dataframe view")
    default_cols = ["name", "sex", "age", "class", "fare", "port", "family_size", "survival"]
    cols = st.multiselect("Columns to show", list(df.columns), default=default_cols)
    st.dataframe(df[cols], use_container_width=True, height=400)

    with st.expander("Summary statistics"):
        st.dataframe(df.describe().T, use_container_width=True)

    st.download_button(
        "Download filtered data as CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="titanic_filtered.csv",
        mime="text/csv",
    )

# ---------------- Distributions (Ex. 2, 3) ----------------
with tab_dist:
    left, right = st.columns(2)

    with left:
        marginal = st.radio("Age marginal plot", ["box", "violin"], horizontal=True)
        fig = px.histogram(
            df, x="age", nbins=30, marginal=marginal,
            labels={"age": "Age"}, title="Age of the passengers",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        log_y = st.checkbox("Log scale for fare", value=True)
        fig = px.box(
            df, x="class", y="fare", color="class", category_orders=ORDERS, log_y=log_y,
            labels={"class": "Class", "fare": "Fare (log scale)" if log_y else "Fare"},
            title="Fare by class",
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------- Groups (Ex. 5, 6, 9) ----------------
with tab_groups:
    left, right = st.columns(2)

    with left:
        outcome = df["survival"].value_counts().reset_index()
        fig = px.pie(
            outcome, names="survival", values="count", hole=0.5, color="survival",
            color_discrete_map=COLORS, title="Died vs survived",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        port_counts = df.groupby(["port", "survival"]).size().reset_index(name="passengers")
        fig = px.bar(
            port_counts, x="port", y="passengers", color="survival", barmode="group",
            color_discrete_map=COLORS, category_orders=ORDERS,
            labels={"port": "Port", "passengers": "Passengers", "survival": ""},
            title="Passengers by port and outcome",
        )
        st.plotly_chart(fig, use_container_width=True)

    groups = (
        df.groupby(["class", "sex"])
        .agg(passengers=("survived", "size"), rate=("survived", "mean"))
        .reset_index()
    )
    chart_type = st.radio("Hierarchy chart", ["treemap", "sunburst"], horizontal=True)
    plot = px.treemap if chart_type == "treemap" else px.sunburst
    fig = plot(
        groups, path=["class", "sex"], values="passengers", color="rate",
        color_continuous_scale="Teal", range_color=[0, 1],
        title="Passengers (size) and survival rate (colour)",
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Relationships (Ex. 7, 8, 10) ----------------
with tab_rel:
    fig = px.scatter(
        df, x="age", y="fare", color="survival", facet_col="class", log_y=True, opacity=0.7,
        color_discrete_map=COLORS, category_orders=ORDERS,
        hover_name="name", hover_data=["sex", "family_size"],
        labels={"age": "Age", "fare": "Fare (log)", "survival": ""},
        title="Age vs fare, by class",
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)

    with left:
        row = st.radio("Heatmap rows", ["sex", "age_group"], horizontal=True)
        rate = df.pivot_table(index=row, columns="class", values="survived", aggfunc="mean", observed=True)
        fig = px.imshow(
            rate, text_auto=".0%", zmin=0, zmax=1, color_continuous_scale="Teal",
            labels={"x": "Class", "y": row.replace("_", " ").title(), "color": "Survival rate"},
            title=f"Survival rate by {row.replace('_', ' ')} and class",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        titles = (
            df[df["title"].isin(["Mr", "Mrs", "Miss", "Master"])]
            .groupby("title")
            .agg(mean_age=("age", "mean"), rate=("survived", "mean"), passengers=("survived", "size"))
            .reset_index()
        )
        if titles.empty:
            st.info("No passengers with these titles in the current filter.")
        else:
            fig = px.scatter(
                titles, x="mean_age", y="rate", size="passengers", color="title", size_max=60,
                hover_name="title", labels={"mean_age": "Mean age", "rate": "Survival rate"},
                title="Titles: age, survival and size",
            )
            st.plotly_chart(fig, use_container_width=True)