drop table if exists players;
create table players (
  id integer primary key autoincrement,
  name text not null unique,
  population integer not null,
  country text not null unique
);

drop table if exists players_cards;
create table players_cards (
    id integer primary key autoincrement,
    card_id integer not null,
    player_id integer not null
);

drop table if exists moves;
create table moves (
    id integer primary key autoincrement,
    card_id integer not null,
    target_id integer,
    round integer not null
);

drop table if exists round;
create table round (
    id integer primary key autoincrement,
    foo text
);
