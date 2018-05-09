#!/usr/bin/perl

use strict;
use warnings;
use CGI ":cgi";
use DBI;
use Time::Piece;
use HTML::Entities;
use CGI::Carp qw(fatalsToBrowser);
use FindBin '$Bin';
use lib "$Bin/secure/lib";
use Baby;

(my $progname = $0) =~ s!.*/!!;
check_login();

my %trans = (
    "dirty" => "Changed dirty diaper",
    "wet"   => "Changed wet diaper",
    "feed"  => "Fed baby",
    "sleep" => "Slept / Woke up",
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

my $event = param("event");
my $action = param("action") || "";
my $dbh = DBI->connect("dbi:SQLite:dbname=secure/baby.db","","") or die;

if($action eq "") {
    my $row = $dbh->selectrow_hashref("SELECT type, start, end, comment, data FROM baby WHERE id = ?", {}, $event);
    my $start = localtime($row->{start})->cdate;
    my $end = localtime($row->{end})->cdate;
    $end = "" unless defined $row->{end};
    my $comment = $row->{comment} // "";
    $comment = encode_entities $comment;
    $comment =~ s/ /&nbsp;/g;
    $comment =~ s/&nbsp;((&nbsp;)*)/ $1/g;
    $comment =~ s/^ /&nbsp;/mg;
    $comment =~ s/\n/<br \/>/g;
    my $event_string = $row->{type};
    if($event_string eq "change") {
        $event_string = "Changed $change{$row->{data}} diaper";
    } else {
        $event_string = $trans{$event_string};
    }
    &print_header();
    my $end_row = "";
    $end_row = "\n<tr><td class=\"edit-header\">End</td><td>$end</td></tr>" if $row->{type} eq "sleep";
    print <<EOF;
<table>
<tr><td class="edit-header">Event</td><td>$event_string</td></tr>
<tr><td class="edit-header">Start</td><td>$start</td></tr>$end_row
<tr><td class="edit-header">Comment</td></tr>
<tr><td colspan="2"><div class="edit-comment">$comment</div></td></tr>
</table>
<br />
<div class="container">
<span><a href="?event=$event&action=edit" class="btn"><i class="fa fa-pencil"></i> Edit</a></span>
<span><a href="?event=$event&action=delete" class="btn pull-right"><i class="fa fa-trash-o"></i> Delete</a></span>
</div>
EOF
} elsif($action eq "edit") {
    my $row = $dbh->selectrow_hashref("SELECT type, start, end, comment, data FROM baby WHERE id = ?", {}, $event);
    my $start = localtime($row->{start});
    my $end = localtime($row->{end});
    my $start_timestamp = $start->date . " " . $start->time;
    my $end_timestamp = $end->date . " " . $end->time;
    $end_timestamp = "" unless defined $row->{end};
    my $comment = defined $row->{comment} ? $row->{comment} : "";
    my $type = $row->{type};
    &print_header();
    my $event_string = $row->{type};
    if($event_string eq "change") {
        $event_string = "Changed $change{$row->{data}} diaper";
    } else {
        $event_string = $trans{$event_string};
    }
    my $start_field_name = $row->{type} eq "sleep"?"Start":"Time";
    print <<EOF;
<form action="$progname" method="POST">
<input type="hidden" name="event" value="$event" />
<input type="hidden" name="type" value="$type" />
<input type="hidden" name="action" value="save" />
<table>
<tr><td class="edit-header">Event</td><td>$event_string</td></tr>
<tr><td class="edit-header">$start_field_name</td><tr>
EOF
    print_buttons("start", 1);
    print "<tr><td colspan=\"2\"><input class=\"timestamp\" type=\"text\" name=\"start\" value=\"$start_timestamp\" /></td></tr>\n";
    print_buttons("start", -1);
    if($row->{type} eq "sleep") {
        # display the end time field only if its a sleep event
        print "<tr><td class=\"edit-header\">End</td><tr>\n";
        print_buttons("end", 1);
        print "<tr><td colspan=\"2\"><input class=\"timestamp\" type=\"text\" name=\"end\" value=\"$end_timestamp\" /></td></tr>\n";
        print_buttons("end", -1);
    }
    print <<EOF;
<tr><td class="edit-header">Comment</td><tr>
<tr><td colspan="2"><textarea name="comment" rows="7">$comment</textarea></td></tr>
</table>
<button type="submit" name="submit"/><i class="fa fa-save"></i> Save</button>
</form>
<br />
EOF
} elsif($action eq "save") {
    my $type = param("type") || "";
    my $start_timestring = param("start") || "";
    my $end_timestring = param("end") || "";
    my $comment = param("comment") || "";
    my $start_epoch = localtime->strptime($start_timestring, "%Y-%m-%d %T")->epoch;
    my $end_epoch = localtime->strptime($end_timestring, "%Y-%m-%d %T")->epoch;
    $end_epoch = undef if $end_timestring eq "";
    if($type eq "sleep") {
        $dbh->do("UPDATE baby SET start = ?, end = ?, comment = ? WHERE id = ?", {}, $start_epoch, $end_epoch, $comment, $event);
    } else {
        $dbh->do("UPDATE baby SET start = ?, comment = ? WHERE id = ?", {}, $start_epoch, $comment, $event);
    }
    print "Location: $progname?event=$event\n\n";
} elsif($action eq "delete") {
    $dbh->do("DELETE FROM baby WHERE id = ?", {}, $event);
    print "Location: history.cgi\n\n";
}
$dbh->disconnect();
&print_footer();

sub print_header {
    print <<EOF;
Content-type: text/html

<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
        <link rel="stylesheet" type="text/css" href="//netdna.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.css" />
        <link rel="stylesheet" type="text/css" href="mystyle.css" />
        <script>
            function zeropad(x) {
                if(x < 10) {
                    return "0" + x;
                } else {
                    return x
                }
            }
            function inc(field, component, addend) {
                var regex = /^\\d+-\\d+-\\d+ \\d+:\\d+:\\d+\$/;
                if(!regex.exec(document.forms[0].elements[field].value)) return;
                var max = {
                    "year"  : 4000,
                    "month" : 12,
                    "day"   : 31,
                    "hour"  : 23,
                    "minute": 59,
                    "second": 59,
                    };
                var min = {
                    "year"  : 0,
                    "month" : 1,
                    "day"   : 1,
                    "hour"  : 0,
                    "minute": 0,
                    "second": 0,
                    };
                var parts = document.forms[0].elements[field].value.split(/[-: ]/);
                var time = {
                    "year":   parseInt(parts[0]),
                    "month":  parseInt(parts[1]),
                    "day":    parseInt(parts[2]),
                    "hour":   parseInt(parts[3]),
                    "minute": parseInt(parts[4]),
                    "second": parseInt(parts[5]),
                    };
                time[component] = (time[component] + addend);
                if(time[component] > max[component]) {
                    time[component] = min[component];
                }
                if(time[component] < min[component]) {
                    time[component] = max[component];
                }
                document.forms[0].elements[field].value = time.year + "-"
                    + zeropad(time.month) + "-"
                    + zeropad(time.day) + " "
                    + zeropad(time.hour) + ":"
                    + zeropad(time.minute) + ":"
                    + zeropad(time.second);
            }
        </script>
    </head>
    <body>
        <div class="tab-bar">
            <a class="tab" href="index.cgi">Summary</a>
            <a class="tab" href="history.cgi">History</a>
            <a class="tab tab-active">Edit</a>
            <a class="tab" href="bulk.cgi">Bulk</a>
        </div>
EOF
}

sub print_footer {
    print "</body></html>\n";
}

sub print_buttons {
    my $field = $_[0];
    my $addend = $_[1];
    my $icon = $addend == 1 ? "up" : "down";
    my $up_or_down_class = $addend == 1 ? "ts-btn-up" : "ts-btn-down";
    print "<tr><td colspan=\"2\">\n";
    for(qw"year month day hour minute second") {
        my $year_class = $_ eq "year" ? " ts-btn-year" : "";
        print "<a class=\"ts-btn $up_or_down_class$year_class\" onclick=\"inc('$field', '$_', $addend)\"><i class=\"fa fa-angle-double-$icon\"></i></a>\n";
    }
    print "</td></tr>\n";
}
