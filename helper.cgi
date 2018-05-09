#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use JSON;
use FindBin '$Bin';
use lib "$Bin/secure/lib";
use Baby;

check_login();

print "Content-Type: text/html\n\n";

my $dbh = DBI->connect("dbi:SQLite:dbname=secure/baby.db","","") or die;
my $tree = $dbh->selectall_hashref("SELECT id, type, MAX(start) AS start, end, data FROM baby GROUP BY type", "type");
$dbh->disconnect();
print encode_json $tree;
