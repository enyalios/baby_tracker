Baby Tracker
============

A website for tracking things about your baby.

Installing
----------

1. Move this whole directory into somewhere served by a CGI executing web server.
2. Set up the database by running `cat secure/schema.txt | sqlite3 secure/baby.db`
3. Set a password by running `echo s3cr1t_p4ssw0rd > secure/cookie.txt`
4. Make sure that the web server user can write to the db file and the directory its in.
