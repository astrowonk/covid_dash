drop table if exists counties;

CREATE TABLE counties (
	date TEXT,
	fips TEXT,
	cases BIGINT,
	deaths FLOAT,
	state TEXT
);
.mode csv
.import data_cache/temp.csv counties
create index idx_state on counties (state);
