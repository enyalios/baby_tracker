#!/usr/bin/perl

use strict;
use warnings;
use CGI ":cgi";
use CGI::Cookie;
use DBI;
use JSON;
use FindBin '$Bin';
use lib "$Bin/secure/lib";
use Baby;

check_login();

print "Content-Type: text/html\n\n";
unless(request_method() eq "POST") {
    print "Bad request method.\n";
    exit;
}

my $type = param("type");
my $data = param("data");
$data = undef if $data eq "undefined";
my $time = time();
my $complete = 0;

my $dbh = DBI->connect("dbi:SQLite:dbname=secure/baby.db","","") or die;
if($type eq "sleep") {
    my $tree = $dbh->selectall_hashref("SELECT id, type, MAX(start) AS start, end, data FROM baby WHERE type = ?", "type", {}, $type);
    if(!defined $tree->{$type}->{end}) {
        my $end = $time;
        # if the duration would be less than 10 seconds, set the end
        # equal to the start show it displays differently is the history
        $end = $tree->{$type}->{start} if $time - $tree->{$type}->{start} <= 10;
        my $sth = $dbh->prepare("UPDATE baby SET end = ? where id = ?");
        my $rv = $sth->execute($end, $tree->{$type}->{id});
        $complete = 1;
    }
}

if($type eq "timer") {
    my $tree = $dbh->selectall_hashref("SELECT id, type, MAX(start) AS start, end, data FROM baby WHERE type = ?", "type", {}, $type);
    if($data eq "start") {
        if(defined $tree->{$type}->{end}) {
            # only do something if we are currently paused
            my $diff = $tree->{$type}->{end} - $tree->{$type}->{start};
            $dbh->do("UPDATE baby SET start = ?, end = null where type = ?", {}, $time - $diff, $type);
        }
    } elsif($data eq "pause") {
        # only do something if we are currently NOT paused
        $dbh->do("UPDATE baby SET end = ? where type = ?", {}, $time, $type) unless $tree->{$type}->{end};
    } elsif($data eq "reset") {
        my $end = undef;
        $end = $time if defined $tree->{$type}->{end};
        $dbh->do("UPDATE baby SET start = ?, end = ? where type = ?", {}, $time, $end, $type);
    } else {
        die "shouldnt get here";
    }
    $complete = 1;
}

unless($complete) {
    my $sth = $dbh->prepare("INSERT INTO baby (type, start, data) VALUES (?, ?, ?)");
    my $rv = $sth->execute($type, $time, $data);
}
my $tree = $dbh->selectall_hashref("SELECT id, type, MAX(start) AS start, end, data FROM baby WHERE type = ?", "type", {}, $type);
$dbh->disconnect();
print encode_json $tree->{$type};
