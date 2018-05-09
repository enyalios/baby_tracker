#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use Time::Piece;
use CGI ":cgi";
use HTML::Entities;
use CGI::Carp qw(fatalsToBrowser);
use FindBin '$Bin';
use lib "$Bin/secure/lib";
use Baby;

check_login();

my %trans = (
    "dirty" => "Changed dirty diaper",
    "wet"   => "Changed wet diaper",
    "feed"  => "Fed baby",
    "sleep" => "Slept",
    "other" => "Other event",
    "left"  => "Next feeding on the left breast",
    "right" => "Next feeding on the right breast",
    "pump"  => "Breast pumped",
    "drug"  => "Took medicine",
);

my %change = (
    1 => "wet",
    2 => "dirty",
    3 => "wet & dirty",
);

sub print_summary {
    my $arg = $_[0];
    return unless keys %$arg;
    print "<div class=\"summary\">";
    print "Fed ", $arg->{feed}, " times<br />\n" if defined $arg->{feed};
    if(defined $arg->{sleep}) {
        print "Slept ", $arg->{sleep}, " times ";
        print "(", int($arg->{sleeptime} / 60 / 60), "h ", int($arg->{sleeptime} / 60 % 60), "m)<br />\n";
    }
    if(defined $arg->{change1} || defined $arg->{change2} || defined $arg->{change3}) {
        $arg->{"change$_"} ||= 0 for 1..3;
        print "Changed ", $arg->{change1} + $arg->{change2} + $arg->{change3}, " Diapers ";
        print "(";
        print join ", ",
        $arg->{change1} ? "$arg->{change1}W" : (),
        $arg->{change2} ? "$arg->{change2}D" : (),
        $arg->{change3} ? "$arg->{change3}W+D" : ();
        print ")<br />\n";
    }
    print "</div>";
}

my $show = param("show") || "";
my $last_week = localtime(localtime->epoch - 6*24*60*60);
my $history_start = localtime->strptime($last_week->ymd . " 00:00:00", "%Y-%m-%d %T")->epoch;
my $toggle_link = "<a class=\"pull-right\" href=\"?show=all\">Show All</a>";
if($show eq "all") {
    $history_start = 0;
    $toggle_link = "<a class=\"pull-right\" href=\"?show=recent\">Show Recent</a>";
}

print "Content-type: text/html\n\n";
my $dbh = DBI->connect("dbi:SQLite:dbname=secure/baby.db","","") or die;
my $rows = $dbh->selectall_arrayref("SELECT id, type, start, end, comment, data FROM baby WHERE start >= ? ORDER BY start DESC", {}, $history_start);
$dbh->disconnect();
print <<EOF;
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="mystyle.css" />
    </head>
    <body>
        <div class="container">$toggle_link</div>
        <div class="tab-bar">
            <a class="tab" href="index.cgi">Summary</a>
            <a class="tab tab-active">History</a>
            <a class="tab" href="bulk.cgi">Bulk</a>
        </div>
        <br />
EOF
my $date = "";
my %summary = ();
for(@$rows) {
    my $start = localtime($_->[2]);
    my $end = localtime($_->[3]);
    my $start_timestamp = $start->strftime("%H:%M");
    my $end_timestamp = $end->strftime("%H:%M");
    $end_timestamp = "" unless defined $_->[3];
    my $comment = encode_entities $_->[4] // "";
    if($start->date ne $date) {
        # start of a new day
        print_summary(\%summary);
        %summary = ();
        print "<div class=\"date\">", $start->strftime("%a %b %e, %Y"), "</div>\n";
    }
    $date = $start->date;
    my $class = $_->[1];
    next if $_->[1] eq "timer";
    if($_->[1] eq "sleep") {
        $summary{$_->[1]}++;
        $summary{sleeptime} += $end - $start;
        if($start == $end) {
            # this is an old sleep / wake up where we didnt track the start and end
            printf "<div class=\"item\"><a class=\"history-item history-$class\" href=\"edit.cgi?event=%s\">%s Slept / Woke up</a></div>\n", $_->[0], $start_timestamp;
        } elsif($end_timestamp eq "") {
            # this is for when baby is currently asleep and there in no end time
            printf "<div class=\"item\"><a class=\"history-item history-$class\" href=\"edit.cgi?event=%s\">%s Went to sleep</a></div>\n", $_->[0], $start_timestamp;
        } else {
            # this is a complete sleep / wake up event
            printf "<div class=\"item\"><a class=\"history-item history-$class\" href=\"edit.cgi?event=%s\">%s - %s %s</a></div>\n", $_->[0], $start_timestamp, $end_timestamp, $trans{$_->[1]};
        }
    } else {
       my $key = $_->[1];
       $key .= $_->[5] if defined $_->[5];
       $summary{$key}++;
        my $event = $_->[1];
        if($event eq "change") {
            $event = "Changed $change{$_->[5]} diaper";
            $class = $class . $_->[5];
        } else {
            $event = $trans{$event};
        }
        printf "<div class=\"item\"><a class=\"history-item history-$class\" href=\"edit.cgi?event=%s\">%s %s</a></div>\n", $_->[0], $start_timestamp, $event;
    }
    print "<div class=\"history-comment\">$comment</div>\n" if $comment ne "";
}
print_summary(\%summary);
print "</body></html>\n";

=cut
left boob dark blue
right boob light blue
formula red
wet+dirty green
dirty blue
wet yellow
