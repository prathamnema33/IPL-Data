import dash
import logging
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, URL, text
from dash import Dash, dcc, html, Input, Output

logging.basicConfig(level=logging.INFO)


# =========================================================
# 1. PostgreSQL CONNECTION
# =========================================================

url = URL.create(
    "postgresql+psycopg2",
    username="postgres",
    password="Password@33",
    host="localhost",
    port=8137,
    database="IPL_analysis"
)

engine = create_engine(url, pool_pre_ping=True)


# =========================================================
# 2. LOAD TEAM-WISE BATTING TOTALS
# =========================================================

team_query = """
SELECT
    season_id,
    team_batting,
    SUM(COALESCE(total_runs, 0)) AS total_runs
FROM public.ball_by_ball_data
GROUP BY season_id, team_batting
ORDER BY season_id;
"""

team_df = pd.read_sql(team_query, engine)


# =========================================================
# 3. LOAD PLAYER-WISE BATTING DATA
# =========================================================

player_query = """

SELECT
    season_id,
    match_id,
    team_batting,
    batter AS player_name,
    SUM(COALESCE(batter_runs, 0)) AS runs,

    COUNT(*) FILTER (
        WHERE NOT COALESCE(is_wide_ball, FALSE)
    ) AS balls_faced,

    COUNT(*) FILTER (
        WHERE batter_runs = 4
    ) AS fours,

    COUNT(*) FILTER (
        WHERE batter_runs = 6
    ) AS sixes,
    COUNT(*) FILTER (
        WHERE player_out = batter
          AND LOWER(COALESCE(wicket_kind, ''))
              NOT IN ('retired hurt', 'absent hurt')
    ) AS dismissals

FROM public.ball_by_ball_data
GROUP BY season_id, match_id, team_batting, batter
ORDER BY season_id, match_id;

"""

player_df = pd.read_sql(player_query, engine)

player_df["strike_rate"] = (
    player_df["runs"]
    / player_df["balls_faced"].replace(0, pd.NA)
    * 100
).fillna(0)


# =========================================================
# 4. LOAD PLAYER-WISE BOWLING DATA
# =========================================================

bowling_query = """
SELECT
    season_id,
    match_id,
    team_bowling,
    bowler AS player_name,

    SUM(
        COALESCE(total_runs, 0)
        - COALESCE(bye_runs, 0)
        - COALESCE(leg_bye_runs, 0)
        - COALESCE(penalty_runs, 0)
    ) AS runs_conceded,

    COUNT(*) FILTER (
        WHERE NOT COALESCE(is_no_ball, FALSE)
          AND NOT COALESCE(is_wide_ball, FALSE)
    ) AS legal_balls,

    COUNT(*) FILTER (
        WHERE LOWER(COALESCE(wicket_kind, ''))
        IN (
            'bowled',
            'caught',
            'caught and bowled',
            'lbw',
            'stumped',
            'hit wicket',
            'hit the ball twice',
            'handled the ball'
        )
    ) AS wickets

FROM public.ball_by_ball_data
GROUP BY season_id, match_id, team_bowling, bowler
ORDER BY season_id, match_id;
"""


bowling_df = pd.read_sql(bowling_query, engine)

bowling_df["overs"] = bowling_df["legal_balls"] / 6

bowling_df["economy_rate"] = (
    bowling_df["runs_conceded"] * 6
    / bowling_df["legal_balls"].replace(0, pd.NA)
).fillna(0)

bowling_df["bowling_average"] = (
    bowling_df["runs_conceded"]
    / bowling_df["wickets"].replace(0, pd.NA)
).fillna(0)

# =========================================================
# 5. COMMON TEAM OPTIONS
# =========================================================

teams = sorted(
    set(team_df["team_batting"].dropna().unique())
    | set(player_df["team_batting"].dropna().unique())
    | set(bowling_df["team_bowling"].dropna().unique())
)


team_options = (
    [{"label": "All Teams", "value": "ALL"}]
    + [{"label": team, "value": team} for team in teams]
)
year_options=(
    [{"label": "All Seasons", "value": "ALL"}]+[{"label": year, "value": year} for year in sorted(set(team_df["season_id"].dropna().unique()))]
)
bowl_style_query = text("""
    SELECT DISTINCT
        COALESCE(bowl_style, 'Unknown') AS bowl_style
    FROM public.ipl_players
    ORDER BY bowl_style
""")

with engine.connect() as conn:
    bowl_style_df = pd.read_sql(bowl_style_query, conn)

bowl_style_options = [
    {"label": "All Bowling Types", "value": "ALL"}
] + [
    {"label": style, "value": style}
    for style in bowl_style_df["bowl_style"].dropna().unique()
]
html.H2("Player Batting Performance"),


# =========================================================
# 6. DASHBOARD LAYOUT
# =========================================================

app = Dash(__name__)

app.title = "IPL Analytics Dashboard"

app.layout = html.Div([

    html.H1(
        "IPL Analytics Dashboard",
        className="dashboard-title",
        style={"textAlign": "center"}
    ),

    html.P(
        "Explore team performance, batting statistics and bowling statistics."
    ),

    # ---------------- TEAM PERFORMANCE ----------------

    html.H2("Team Performance", className="section-heading"),

    html.H2("Select Team"),

    dcc.Dropdown(
        id="team-filter",
        options=team_options,
        value="ALL",
        clearable=False
    ),

    dcc.Graph(id="team-chart"),

    html.Hr(),

    # ---------------- BATTING PERFORMANCE ----------------

    html.H2("Player Batting Performance", className="section-heading"),

    html.H2("Select Batting Team"),

    dcc.Dropdown(
        id="player-team-filter",
        options=team_options,
        value="ALL",
        clearable=False
    ),

    html.Br(),

    html.H2("Select Batter"),

    dcc.Dropdown(
        id="player-filter",
        placeholder="Choose a player",
        clearable=True
    ),
    html.H2("Select Season"),
    dcc.Dropdown(
        id="player-filter2",
        options=year_options,
        value="ALL"
        ),

    html.H3("Batting Summary"),
    html.Div(id="player-kpis"),

    html.H3("Runs by Season or Match"),
    dcc.Graph(id="runs-chart"),

    html.H3("Season-wise Batting Metrics"),
    dcc.Graph(id="season-chart"),

    html.H3("Season-wise Strike Rate vs Bowling Type"),
    html.H2("Select Bowling Type"),

    dcc.Dropdown(
    id="bowl-style-filter",
    options=bowl_style_options,
    value="ALL",
    placeholder="Select Bowling Type",
    clearable=False
),
    dcc.Graph(id="batter-vs-bowling-type-chart"),

    html.Hr(),

    # ---------------- BOWLING PERFORMANCE ----------------

    html.H2("Player Bowling Performance", className="section-heading"),

    html.H2("Select Bowling Team"),

    dcc.Dropdown(
        id="bowling-team-filter",
        options=team_options,
        value="ALL",
        clearable=False
    ),

    html.Br(),

    html.H2("Select Bowler"),

    dcc.Dropdown(
        id="bowler-filter",
        placeholder="Choose a bowler",
        clearable=True
    ),

    html.Div(id="bowler-kpis"),

    html.H3("Wickets by Season"),
    dcc.Graph(id="bowler-wicket-chart"),

    html.H3("Season-wise Bowling Metrics"),
    dcc.Graph(id="bowler-season-chart")

], style={
    "padding": "25px",
    "maxWidth": "1400px",
    "margin": "auto"
})


def apply_chart_typography(figure):
    figure.update_layout(
        font={"family": "Inter, sans-serif", "size": 14},
        title_font={"family": "Inter, sans-serif", "size": 17},
        xaxis={
            "title_font": {"family": "Inter, sans-serif", "size": 14},
            "tickfont": {"family": "Inter, sans-serif", "size": 13},
        },
        yaxis={
            "title_font": {"family": "Inter, sans-serif", "size": 14},
            "tickfont": {"family": "Inter, sans-serif", "size": 13},
        },
        legend={"font": {"family": "Inter, sans-serif", "size": 14}},
        hoverlabel={"font": {"family": "Inter, sans-serif", "size": 14}},
    )
    return figure


# =========================================================
# 7. TEAM PERFORMANCE CALLBACK
# =========================================================

@app.callback(
    Output("team-chart", "figure"),
    Input("team-filter", "value")
)
def update_team_chart(selected_team):

    data = team_df.copy()

    if selected_team != "ALL":
        data = data[data["team_batting"] == selected_team]

    fig = px.bar(
        data,
        x="season_id",
        y="total_runs",
        color="team_batting",
        barmode="group",
        title="Total Runs by Team and Season",
        labels={
            "season_id": "Season",
            "team_batting": "Team",
            "total_runs": "Total Runs"
        }
    )

    return apply_chart_typography(fig)


# =========================================================
# 8. UPDATE BATTER DROPDOWN
# =========================================================


@app.callback(
    Output("player-filter", "options"),
    Output("player-filter", "value"),
    Input("player-team-filter", "value"),
    )
def update_players(selected_team):
    data = player_df.copy()

    if selected_team and selected_team != "ALL":
        data = data[data["team_batting"] == selected_team]

    players = sorted(data["player_name"].dropna().unique())

    options = [
        {"label": player, "value": player}
        for player in players
    ]

    return options, None

@app.callback(
    Output("player-filter2", "options"),
    Output("player-filter2", "value"),
    Input("player-team-filter", "value"),
    Input("player-filter", "value")
)
def update_years(selected_team, selected_player):
    data = player_df.copy()

    if selected_team and selected_team != "ALL":
        data = data[data["team_batting"] == selected_team]

    if selected_player:
        data = data[data["player_name"] == selected_player]

    seasons = sorted(data["season_id"].dropna().unique())

    options = [{"label": "All Seasons", "value": "ALL"}] + [
        {"label": str(year), "value": year}
        for year in seasons
    ]

    return options, "ALL"


def _empty_player_dashboard(message):
    return (
        html.P(message),
        apply_chart_typography(px.bar(title=message)),
        apply_chart_typography(px.line(title=message)),
        apply_chart_typography(px.line(title=message))
    )


def _build_player_dashboard(
    selected_player,
    selected_team,
    selected_year,
    selected_style
):
    if not selected_player:
        return _empty_player_dashboard(
            "Choose a team and batter to view statistics."
        )

    required_columns = {
        "player_name",
        "team_batting",
        "season_id",
        "match_id",
        "runs",
        "balls_faced",
        "fours",
        "sixes",
        "dismissals"
    }
    if not required_columns.issubset(player_df.columns):
        missing_columns = sorted(required_columns - set(player_df.columns))
        raise ValueError(
            f"Player data is missing required columns: {missing_columns}"
        )

    data = player_df[
        player_df["player_name"] == selected_player
    ].copy()

    if selected_team and selected_team != "ALL":
        data = data[data["team_batting"] == selected_team]

    season_id = None
    if selected_year is not None and selected_year != "ALL":
        try:
            season_id = int(selected_year)
        except (TypeError, ValueError):
            return _empty_player_dashboard(
                f"Invalid season filter: {selected_year!r}"
            )
        data = data[data["season_id"] == season_id]

    if data.empty:
        return _empty_player_dashboard("No batting data found for these filters.")

    total_runs = int(data["runs"].sum())
    total_fours = int(data["fours"].sum())
    total_sixes = int(data["sixes"].sum())
    total_balls = int(data["balls_faced"].sum())

    strike_rate = (
        total_runs / total_balls * 100
        if total_balls else 0
    )

    kpis = html.Div([
        html.H3(f"Player: {selected_player}", className="kpi-value"),
        html.H3(f"Total Runs: {total_runs:,}", className="kpi-value"),
        html.H3(f"Fours: {total_fours}", className="kpi-value"),
        html.H3(f"Sixes: {total_sixes}", className="kpi-value"),
        html.H3(f"Strike Rate: {strike_rate:.2f}", className="kpi-value"),
        html.H3(f"Matches: {data['match_id'].nunique()}", className="kpi-value")
    ], className="kpi-values")

    season_scores = (
        data.groupby(
            ["season_id", "team_batting"],
            as_index=False
        )
        .agg(runs=("runs", "sum"))
    )

    if season_id is None:
        chart_data = season_scores
        x_column = "season_id"
        chart_title = (
            f"{selected_player} - Runs by Season and Batting Team"
        )
        x_label = "Season"
        hover_data = {
            "season_id": True,
            "runs": True,
            "team_batting": False
        }
    else:
        chart_data = (
            data.groupby(
                ["match_id", "team_batting"],
                as_index=False
            )
            .agg(runs=("runs", "sum"))
            .sort_values("match_id")
        )

        x_column = "match_id"
        chart_title = f"{selected_player} - Runs by Match"
        x_label = "Match ID"
        hover_data = {
            "match_id": True,
            "runs": True,
            "team_batting": False
        }

    runs_fig = px.bar(
        chart_data,
        x=x_column,
        y="runs",
        color="team_batting",
        barmode="group",
        title=chart_title,
        labels={
            x_column: x_label,
            "runs": "Total Runs",
            "team_batting": "Batting Team"
        },
        hover_data=hover_data
    )
    runs_fig.add_scatter(
        x=chart_data[x_column],
        y=chart_data["runs"],
        mode="lines+markers",
        name="Runs Trend",
        line=dict(color="red", width=3)
    )
    runs_fig.update_layout(
        xaxis_title=x_label,
        yaxis_title="Total Runs",
        legend_title="Batting Team"
    )

    player_season_scores = (
        data.groupby("season_id", as_index=False)
        .agg(
            runs=("runs", "sum"),
            balls_faced=("balls_faced", "sum"),
            dismissals=("dismissals", "sum")
        )
        .sort_values("season_id")
    )

    player_season_scores["strike_rate"] = (
        player_season_scores["runs"]
        / player_season_scores["balls_faced"].replace(0, pd.NA)
        * 100
    ).fillna(0)

    player_season_scores["Batting Average"] = (
        player_season_scores["runs"]
        / player_season_scores["dismissals"].replace(0, pd.NA)
    )

    plot_data = player_season_scores.melt(
        id_vars=["season_id"],
        value_vars=["strike_rate", "Batting Average"],
        var_name="Metric",
        value_name="Value"
    )

    season_fig = px.line(
        plot_data,
        x="season_id",
        y="Value",
        color="Metric",
        markers=True,
        title=f"{selected_player} - Strike Rate and Batting Average by Season",
        labels={
            "season_id": "Season",
            "Value": "Metric Value",
            "Metric": "Performance Metric"
        }
    )

    bowling_query = """
        SELECT
            B.season_id AS season_id,
            COALESCE(A.bowl_style, 'Unknown') AS bowl_style,
            SUM(COALESCE(B.batter_runs, 0)) AS runs,
            COUNT(*) FILTER (
                WHERE NOT COALESCE(B.is_wide_ball, FALSE)
            ) AS balls_faced
        FROM public.ball_by_ball_data AS B
        LEFT JOIN public.ipl_players AS A
            ON B.bowler = A.player_name
        WHERE B.batter = :player_name
    """

    params = {"player_name": selected_player}

    # Apply team filter only when a specific team is selected
    if selected_team and selected_team != "ALL":
        bowling_query += """
            AND B.team_batting = :team_batting
        """
        params["team_batting"] = selected_team

    # Apply season filter only when a specific season is selected
    if season_id is not None:
        bowling_query += """
            AND B.season_id = :season_id
        """
        params["season_id"] = season_id

    # Apply bowling-style filter only when a specific style is selected
    if selected_style and selected_style != "ALL":
        bowling_query += """
            AND COALESCE(A.bowl_style, 'Unknown') = :bowl_style
        """
        params["bowl_style"] = selected_style

    bowling_query += """
        GROUP BY B.season_id, COALESCE(A.bowl_style, 'Unknown')
        ORDER BY B.season_id, bowl_style
    """

    batter_vs_bowling_df = pd.read_sql(
        text(bowling_query),
        engine,
        params=params
    )

    if batter_vs_bowling_df.empty:
        bowling_fig = px.line(
            title="No data found for the selected filters",
            labels={"season_id": "Season", "strike_rate": "Strike Rate"}
        )
    else:
        batter_vs_bowling_df["strike_rate"] = (
            batter_vs_bowling_df["runs"]
            / batter_vs_bowling_df["balls_faced"].replace(0, pd.NA)
            * 100
        ).fillna(0)

        bowling_fig = px.line(
            batter_vs_bowling_df,
            x="season_id",
            y="strike_rate",
            color="bowl_style",
            markers=True,
            title=f"{selected_player} - Season-wise Strike Rate vs Bowling Type",
            labels={
                "season_id": "Season",
                "strike_rate": "Strike Rate",
                "bowl_style": "Bowling Type",
                "runs": "Runs",
                "balls_faced": "Balls Faced"
            },
            hover_data=[
                "season_id",
                "bowl_style",
                "runs",
                "balls_faced",
                "strike_rate"
            ]
        )

        bowling_fig.update_layout(
            xaxis_title="Season",
            yaxis_title="Strike Rate"
        )

    return (
        kpis,
        apply_chart_typography(runs_fig),
        apply_chart_typography(season_fig),
        apply_chart_typography(bowling_fig)
    )


@app.callback(
    Output("player-kpis", "children"),
    Output("runs-chart", "figure"),
    Output("season-chart", "figure"),
    Output("batter-vs-bowling-type-chart", "figure"),
    Input("player-filter", "value"),
    Input("player-team-filter", "value"),
    Input("player-filter2", "value"),
    Input("bowl-style-filter", "value")
)
def update_player_dashboard(
    selected_player,
    selected_team,
    selected_year,
    selected_style
):
    try:
        return _build_player_dashboard(
            selected_player,
            selected_team,
            selected_year,
            selected_style
        )
    except Exception:
        logging.exception("Player dashboard callback failed")
        return _empty_player_dashboard(
            "Unable to load player statistics. See the server traceback."
        )

# =========================================================
# 10. UPDATE BOWLER DROPDOWN
# =========================================================

@app.callback(
    Output("bowler-filter", "options"),
    Output("bowler-filter", "value"),
    Input("bowling-team-filter", "value")
)
def update_bowlers(selected_team):

    data = bowling_df

    if selected_team != "ALL":
        data = data[data["team_bowling"] == selected_team]

    bowlers = sorted(data["player_name"].dropna().unique())

    options = [
        {"label": bowler, "value": bowler}
        for bowler in bowlers
    ]

    return options, None


# =========================================================
# 11. PLAYER BOWLING DASHBOARD
# =========================================================

@app.callback(
    Output("bowler-kpis", "children"),
    Output("bowler-wicket-chart", "figure"),
    Output("bowler-season-chart", "figure"),
    Input("bowler-filter", "value"),
    Input("bowling-team-filter", "value")
)
def update_bowling_dashboard(selected_bowler, selected_team):

    empty_fig = apply_chart_typography(
        px.bar(title="Select a bowler to view performance")
    )

    if not selected_bowler:
        return (
            html.P("Choose a team and bowler to view statistics."),
            empty_fig,
            empty_fig
        )

    data = bowling_df[
        bowling_df["player_name"] == selected_bowler
    ].copy()

    if selected_team != "ALL":
        data = data[data["team_bowling"] == selected_team]

    if data.empty:
        return html.P("No bowling data found."), empty_fig, empty_fig

    total_wickets = int(data["wickets"].sum())
    total_runs = int(data["runs_conceded"].sum())
    total_balls = int(data["legal_balls"].sum())

    total_overs = total_balls / 6

    economy = (
        total_runs * 6 / total_balls
        if total_balls else 0
    )

    bowling_average = (
        total_runs / total_wickets
        if total_wickets else 0
    )

    kpis = html.Div([
        html.H3(f"Total Wickets: {total_wickets}", className="kpi-value"),
        html.H3(f"Runs Conceded: {total_runs}", className="kpi-value"),
        html.H3(f"Overs Bowled: {total_overs:.1f}", className="kpi-value"),
        html.H3(f"Economy Rate: {economy:.2f}", className="kpi-value"),
        html.H3(f"Bowling Average: {bowling_average:.2f}", className="kpi-value")
    ], className="kpi-values")

    wickets_by_season = (
        data.groupby(
            ["season_id", "team_bowling"],
            as_index=False
        )
        .agg(wickets=("wickets", "sum"))
    )

    wickets_fig = px.bar(
        wickets_by_season,
        x="season_id",
        y="wickets",
        color="team_bowling",
        barmode="group",
        title=f"{selected_bowler} - Wickets by Season",
        labels={
            "season_id": "Season",
            "wickets": "Wickets",
            "team_bowling": "Team"
        }
    )

    season_data = (
        data.groupby("season_id", as_index=False)
        .agg(
            runs_conceded=("runs_conceded", "sum"),
            legal_balls=("legal_balls", "sum"),
            wickets=("wickets", "sum")
        )
    )

    season_data["economy_rate"] = (
        season_data["runs_conceded"] * 6
        / season_data["legal_balls"].replace(0, pd.NA)
    ).fillna(0)
    season_data["bowling_average"] = (
        season_data["runs_conceded"]
        / season_data["wickets"].replace(0, pd.NA)
    ).fillna(0)

    season_fig = px.line(
        season_data,
        x="season_id",
        y=["economy_rate","bowling_average"],
        markers=True,
        title=f"{selected_bowler} - Economy Rate by Season",
        labels={
            "season_id": "Season",
            "economy_rate": "Economy Rate"
        }
    )

    return (
        kpis,
        apply_chart_typography(wickets_fig),
        apply_chart_typography(season_fig)
    )


# =========================================================
# 12. RUN DASHBOARD
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
