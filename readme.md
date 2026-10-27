# IPL Player Analysis Dashboard

An interactive IPL analytics dashboard built using Python, Dash, Plotly, and PostgreSQL to explore player performance, team statistics, season-wise trends, and batter performance against different bowling styles.

## Overview

The IPL Player Analysis Dashboard transforms match-level and ball-by-ball cricket data into interactive visualizations. It helps users explore player statistics, compare performances across seasons, and understand batting patterns against different bowling styles.

## Features

- **Player Performance Analysis:** Analyze batting performance using runs, balls faced, fours, sixes, and strike rate.
- **Team-wise Analysis:** Explore player and team statistics using interactive filters.
- **Season-wise Trends:** Compare player performance across different IPL seasons.
- **Batter vs. Bowling Style:** Analyze how batters perform against different bowling styles.
- **Interactive Visualizations:** Explore statistics through Plotly charts and a Dash web interface.
- **KPI Cards:** Display key performance metrics for quick analysis.
- **Dynamic Filtering:** Filter dashboard results by player, team, and season.

## Tech Stack

- **Programming Language:** Python
- **Dashboard Framework:** Dash
- **Visualization:** Plotly
- **Database:** PostgreSQL
- **Database Connectivity:** SQLAlchemy
- **Data Analysis:** Pandas
- **Query Language:** SQL

## Dataset

The project uses IPL match and ball-by-ball datasets covering seasons through 2025.

The data supports analysis of:

- Match details and participating teams
- Batting and bowling statistics
- Runs scored and balls faced
- Boundaries, including fours and sixes
- Player performance across seasons
- Batter performance against bowling styles

*Note: The accuracy of each analysis depends on data quality, available fields, and the metric's calculation logic.*

## Project Structure

```text
IPL-Player-Analysis/
├── app.py                 # Dash application entry point
├── requirements.txt       # Project dependencies
├── .env                   # Database configuration (not committed)
├── data/                  # Dataset files, if stored locally
└── README.md              # Project documentation
```

*Adjust the file structure above to match your actual repository.*

## Installation and Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd IPL-Player-Analysis
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install dash plotly pandas sqlalchemy psycopg2-binary python-dotenv
```

Alternatively, install the dependencies from your requirements file:

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database and configure the connection details using environment variables in your `.env` file.

Example:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ipl_database
DB_USER=your_username
DB_PASSWORD=your_password
```

Ensure that your application reads these variables and constructs the database connection correctly. Never commit real database credentials to GitHub.

### 5. Run the dashboard

```bash
python app.py
```

Open the local URL displayed in your terminal, typically:

```text
http://127.0.0.1:8050/
```

## Analytical Approach

1. **Data Preparation:** Load and clean match and ball-by-ball datasets.
2. **Database Management:** Store structured cricket data in PostgreSQL.
3. **SQL Aggregation:** Calculate player-level statistics using filtering, grouping, and aggregate functions.
4. **Data Visualization:** Build interactive charts using Plotly.
5. **Dashboard Integration:** Connect the charts and KPI cards to interactive filters through Dash callbacks.

## Key Analytical Considerations

- Strike rate should be interpreted alongside balls faced and sample size.
- Season-level comparisons should use consistent filtering and aggregation.
- Wicket calculations should account for dismissal types that do not count as bowler-credited wickets.
- Batter-versus-bowling-style comparisons depend on the completeness and consistency of bowling-style data.

## Future Enhancements

- Venue-based player performance analysis
- Batter-versus-bowler matchup analysis
- Player form analysis using recent matches
- Playing XI integration
- Venue-aware player performance predictions

## Learning Outcomes

- Writing SQL queries for analytical workloads
- Connecting Python applications to PostgreSQL
- Developing interactive dashboards with Dash and Plotly
- Implementing data-driven filtering and aggregation
- Interpreting cricket performance metrics and identifying analytical limitations

## Author

**Pratham Nema**

B.Tech Computer Science Student

