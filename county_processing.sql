drop table if exists counties;
CREATE TEMPORARY TABLE counties (
	date TEXT,
	state TEXT,
	fips INTEGER,
	cases INTEGER,
	deaths INTEGER
);
.mode csv
.import data_cache/temp.csv "temp.counties"



--create index temp.idx_state on counties(state);
--now make better table
drop table if exists county_enhanced;

CREATE TABLE county_enhanced (
	date TEXT,
	state TEXT,
	cases INTEGER,
	deaths INTEGER,
	population INTEGER
);


insert into county_enhanced
select c.date,
	c.state,
	c.cases,
	c.deaths,
	p.population
from "temp.counties" c
	left join county_population p on c.fips = p.fips;
CREATE INDEX idx_state_enhanced ON county_enhanced (state);
drop table if exists "temp.counties";
