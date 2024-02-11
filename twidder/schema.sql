create table if not exists user (
    email text primary key,
    password text NOT NULL, 
    firstname text NOT NULL, 
    lastname text NOT NULL,
    gender text NOT NULL, 
    city text NOT NULL,
    country text NOT NULL,
  	image blob
);

create table if not exists post (
    id integer primary key AUTOINCREMENT,
  	author text not NULL,
  	user text NOT NULL,
  	content text NOT NULL,
  	created datetime NOT NULL,
  	edited datetime,
  	foreign key(author) references user(email),
  	foreign key(user) references user(email)
);
