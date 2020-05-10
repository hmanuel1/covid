"""
    Queries for Database
"""

COUNTIES_VIEW = ("""
    CREATE VIEW
            counties_view AS
    SELECT
        nytimes_counties.date,
        us_map.name || ', ' || state_map.abbr AS 'county',
        nytimes_counties.cases,
        nytimes_counties.deaths,
        nytimes_counties.case_level AS level
    FROM
            nytimes_counties
    INNER JOIN us_map ON us_map.county_id = nytimes_counties.county_id
    INNER JOIN state_map ON state_map.state_id = nytimes_counties.state_id
""")

COUNTIES_VIEW_TABLE = 'counties_view'

DROP_COUNTIES_VIEW = 'DROP VIEW IF EXISTS counties_view'

STATES_VIEW = ("""
    CREATE VIEW
            states_view AS
    SELECT
        nytimes_states.date,
        state_map.state_id,
        state_map.name AS 'state',
        nytimes_states.cases,
        nytimes_states.deaths
    FROM
            nytimes_states
    INNER JOIN state_map ON state_map.state_id = nytimes_states.state_id
""")

STATES_VIEW_TABLE = 'states_view'

DROP_STATES_VIEW = 'DROP VIEW IF EXISTS states_view'

FLDEM_VIEW = ("""
    CREATE VIEW
        fldem_view AS
    SELECT
        m.date,
        m.day,
        m.male AS 'gender',
        m.age,
        us_map.aland AS 'land_area',
        us_map.awater AS 'water_area',
        us_map.pop AS 'population',
        ROUND(us_map.pop / us_map.aland, 0) AS 'density',
        IFNULL(e.died, 0) AS 'died'
    FROM
        fldem_cases m
    INNER JOIN us_map ON us_map.county_id = m.county_id
    LEFT JOIN
        (
            SELECT DISTINCT
                fldem_cases.case_id,
                fldem_cases.rowid/fldem_cases.rowid as 'died'
            FROM
                fldem_cases
            INNER JOIN fldem_deaths ON
                fldem_deaths.county_id = fldem_cases.county_id AND
                fldem_deaths.age = fldem_cases.age AND
                fldem_deaths.date = fldem_cases.date AND
                fldem_deaths.male = fldem_cases.male AND
                fldem_deaths.resident = fldem_cases.resident AND
                fldem_deaths.traveled = fldem_cases.traveled AND
                fldem_deaths.place = fldem_cases.place
        ) e ON m.case_id = e.case_id
""")

FLDEM_VIEW_TABLE = 'fldem_view'

DROP_FLDEM_VIEW = 'DROP VIEW IF EXISTS fldem_view'

CREATE_OPTIONS_TABLE = ("""
    CREATE TABLE options AS
    SELECT
        state_id AS 'id',
        name AS 'state'
    FROM state_map
""")

INSERT_USA_OPTION = ("""
    INSERT INTO
        options (rowid, id, state)
    VALUES
        (0, '00', 'USA')
""")

DROP_OPTIONS_TABLE = 'DROP TABLE IF EXISTS options'

OPTIONS_TABLE = 'options'

US_MAP_VIEW = ("""
    CREATE VIEW
        us_map_view AS
    SELECT
        us_map.county_id,
        state_map.state_id,
        us_map.name || ', ' || state_map.abbr AS 'name',
        us_map.geometry,
        us_map.pop,
        nytimes_counties.cases AS 'c',
        nytimes_counties.deaths AS 'd',
        nytimes_counties.case_level AS 'm',
        nytimes_counties.day
    FROM
        us_map
    LEFT JOIN state_map ON state_map.state_id = us_map.state_id
    LEFT JOIN nytimes_counties ON
        nytimes_counties.county_id = us_map.county_id AND
        nytimes_counties.day < 15
""")

US_MAP_PIVOT_VIEW = ("""
    CREATE VIEW
        us_map_pivot_view AS
    SELECT
        name,
        state_id,
        geometry,
        pop,
        day,
        IFNULL(SUM(CASE WHEN day = 0 THEN c END), 0) as c,
        IFNULL(SUM(CASE WHEN day = 0 THEN d END), 0) as d,
        IFNULL(SUM(CASE WHEN day = 0 THEN m END), 0) as m,
        IFNULL(SUM(CASE WHEN day = 0 THEN IFNULL(c, 0) END), 0) as c0,
        IFNULL(SUM(CASE WHEN day = 0 THEN IFNULL(d, 0) END), 0) as d0,
        IFNULL(SUM(CASE WHEN day = 0 THEN IFNULL(m, 0) END), 0) as m0,
        IFNULL(SUM(CASE WHEN day = 1 THEN IFNULL(c, 0) END), 0) as c1,
        IFNULL(SUM(CASE WHEN day = 1 THEN IFNULL(d, 0) END), 0) as d1,
        IFNULL(SUM(CASE WHEN day = 1 THEN IFNULL(m, 0) END), 0) as m1,
        IFNULL(SUM(CASE WHEN day = 2 THEN IFNULL(c, 0) END), 0) as c2,
        IFNULL(SUM(CASE WHEN day = 2 THEN IFNULL(d, 0) END), 0) as d2,
        IFNULL(SUM(CASE WHEN day = 2 THEN IFNULL(m, 0) END), 0) as m2,
        IFNULL(SUM(CASE WHEN day = 3 THEN IFNULL(c, 0) END), 0) as c3,
        IFNULL(SUM(CASE WHEN day = 3 THEN IFNULL(d, 0) END), 0) as d3,
        IFNULL(SUM(CASE WHEN day = 3 THEN IFNULL(m, 0) END), 0) as m3,
        IFNULL(SUM(CASE WHEN day = 4 THEN IFNULL(c, 0) END), 0) as c4,
        IFNULL(SUM(CASE WHEN day = 4 THEN IFNULL(d, 0) END), 0) as d4,
        IFNULL(SUM(CASE WHEN day = 4 THEN IFNULL(m, 0) END), 0) as m4,
        IFNULL(SUM(CASE WHEN day = 5 THEN IFNULL(c, 0) END), 0) as c5,
        IFNULL(SUM(CASE WHEN day = 5 THEN IFNULL(d, 0) END), 0) as d5,
        IFNULL(SUM(CASE WHEN day = 5 THEN IFNULL(m, 0) END), 0) as m5,
        IFNULL(SUM(CASE WHEN day = 6 THEN IFNULL(c, 0) END), 0) as c6,
        IFNULL(SUM(CASE WHEN day = 6 THEN IFNULL(d, 0) END), 0) as d6,
        IFNULL(SUM(CASE WHEN day = 6 THEN IFNULL(m, 0) END), 0) as m6,
        IFNULL(SUM(CASE WHEN day = 7 THEN IFNULL(c, 0) END), 0) as c7,
        IFNULL(SUM(CASE WHEN day = 7 THEN IFNULL(d, 0) END), 0) as d7,
        IFNULL(SUM(CASE WHEN day = 7 THEN IFNULL(m, 0) END), 0) as m7,
        IFNULL(SUM(CASE WHEN day = 8 THEN IFNULL(c, 0) END), 0) as c8,
        IFNULL(SUM(CASE WHEN day = 8 THEN IFNULL(d, 0) END), 0) as d8,
        IFNULL(SUM(CASE WHEN day = 8 THEN IFNULL(m, 0) END), 0) as m8,
        IFNULL(SUM(CASE WHEN day = 9 THEN IFNULL(c, 0) END), 0) as c9,
        IFNULL(SUM(CASE WHEN day = 9 THEN IFNULL(d, 0) END), 0) as d9,
        IFNULL(SUM(CASE WHEN day = 9 THEN IFNULL(m, 0) END), 0) as m9,
        IFNULL(SUM(CASE WHEN day = 10 THEN IFNULL(c, 0) END), 0) as c10,
        IFNULL(SUM(CASE WHEN day = 10 THEN IFNULL(d, 0) END), 0) as d10,
        IFNULL(SUM(CASE WHEN day = 10 THEN IFNULL(m, 0) END), 0) as m10,
        IFNULL(SUM(CASE WHEN day = 11 THEN IFNULL(c, 0) END), 0) as c11,
        IFNULL(SUM(CASE WHEN day = 11 THEN IFNULL(d, 0) END), 0) as d11,
        IFNULL(SUM(CASE WHEN day = 11 THEN IFNULL(m, 0) END), 0) as m11,
        IFNULL(SUM(CASE WHEN day = 12 THEN IFNULL(c, 0) END), 0) as c12,
        IFNULL(SUM(CASE WHEN day = 12 THEN IFNULL(d, 0) END), 0) as d12,
        IFNULL(SUM(CASE WHEN day = 12 THEN IFNULL(m, 0) END), 0) as m12,
        IFNULL(SUM(CASE WHEN day = 13 THEN IFNULL(c, 0) END), 0) as c13,
        IFNULL(SUM(CASE WHEN day = 13 THEN IFNULL(d, 0) END), 0) as d13,
        IFNULL(SUM(CASE WHEN day = 13 THEN IFNULL(m, 0) END), 0) as m13,
        IFNULL(SUM(CASE WHEN day = 14 THEN IFNULL(c, 0) END), 0) as c14,
        IFNULL(SUM(CASE WHEN day = 14 THEN IFNULL(d, 0) END), 0) as d14,
        IFNULL(SUM(CASE WHEN day = 14 THEN IFNULL(m, 0) END), 0) as m14
    FROM us_map_view
    GROUP BY county_id
""")

US_MAP_PIVOT_VIEW_TABLE = 'us_map_pivot_view'

DROP_US_MAP_PIVOT_VIEW = 'DROP VIEW IF EXISTS us_map_pivot_view'

VACUUM = 'VACUUM'

REINDEX = 'REINDEX'
