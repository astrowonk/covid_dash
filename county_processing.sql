drop table if exists counties;

CREATE TABLE counties (
	date TEXT,
	state TEXT,
	fips BIGINT,
	cases BIGINT,
	deaths BIGINT

);
.mode csv
.import data_cache/temp.csv counties
create index idx_state on counties (state);
