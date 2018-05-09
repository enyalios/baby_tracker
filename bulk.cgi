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

my %lookup = (
    #key      #type     #data  #description
    "w"  => [ "change", 1,     "Changed wet diaper"   ],
    "d"  => [ "change", 2,     "Changed dirty diaper" ],
    "bm" => [ "change", 2,     "Changed dirty diaper" ],
    "wd" => [ "change", 3,     "Changed w+d diaper"   ],
    "dw" => [ "change", 3,     "Changed w+d diaper"   ],
    "f"  => [ "feed",   undef, "Fed"                  ],
    "s"  => [ "sleep",  undef, "Slept from"           ],
);

sub start_html {
    print <<EOF;
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="//netdna.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.css" />
        <link rel="stylesheet" type="text/css" href="mystyle.css" />
    </head>
    <body>
        <div class="tab-bar">
            <a class="tab" href="index.cgi">Summary</a>
            <a class="tab" href="history.cgi">History</a>
            <a class="tab tab-active">Bulk</a>
        </div>
        <br />
EOF
}

sub end_html {
    print "    </body>\n</html>\n";
}

sub parse_line {
    my ($line, $date) = (@_);

    # get the type
    my $type = lc get_field($line);
    return { error => "Couldn't get the type field" } unless defined $type;
    return { error => "Couldn't look up the type '$type'" } unless defined $lookup{$type};
    my $data = $lookup{$type}[1];
    my $desc = $lookup{$type}[2];
    $type = $lookup{$type}[0];

    # get the start time
    my $start_string = get_field($line);
    return { error => "Mising start time" } unless defined $start_string;
    my $start = parse_time($start_string, $date);
    return { error => "Couldn't parse start time '$start_string'" }
        unless defined $start;

    # get the end time if it's type 'sleep'
    my $end = undef;
    if($type eq "sleep") {
        my $end_string= get_field($line);
        return { error => "Missing end time" } unless defined $end_string;
        $end = parse_time($end_string, $date);
        return { error => "Couldn't parse end time '$end_string'" }
            unless defined $end;
    }

    # strip extra whitespace off the comment field
    $line =~ s/^\s*//;
    $line =~ s/\s*$//;
    my $comment = undef;
    $comment = $line unless $line eq "";

    return {
        type    => $type,
        start   => $start,
        end     => $end,
        data    => $data,
        comment => $comment,
        desc    => $desc
    };
}

sub get_field {
    if($_[0] =~ s/^\s*(\S+)//) {
        return $1;
    } else {
        return undef;
    }
}

sub parse_time {
    my ($time_string, $today_str) = (@_);
    return undef unless defined $time_string;

    return undef unless $time_string =~ /^(\d?\d):?(\d\d)(:(\d\d))?$/;
    my ($hour, $minute, $second) = ($1, $2, $4);
    $second = "00" unless defined $second;
    # assume small hours are pm since bulk data is usually for daycare hours
    $hour += 12 if $hour < 7;
    my $datetime_string = $today_str . " $hour:$minute:$second";
    return new Time::Piece->strptime($datetime_string, "%Y-%m-%d %H:%M:%S");
}

sub process_line {
    my $data  = $_[0];
    my $input = $_[1];
    my $sth   = $_[2];

    # print the error message and bail if there was a parse error
    if(defined $data->{error}) {
        $input =~ s/\r?\n?$//;
        print "<div style=\"display:inline-block;\" class=\"alert\"><i class=\"fa fa-exclamation-circle\"></i> ", $data->{error}, " for line '", encode_entities($input), "'.</div>\n";
        return;
    }

    my $comment = "";
    $comment = " (" . encode_entities($data->{comment}) . ")" if defined $data->{comment};
    if($data->{type} eq "sleep") {
        printf "<div>%s from %s to %s%s.</div>\n",
            $data->{desc},
            $data->{start}->strftime("%k:%M"),
            $data->{end}->strftime("%k:%M"),
            $comment;
    } else {
        printf "<div>%s at %s%s.</div>\n",
            $data->{desc},
            $data->{start}->strftime("%k:%M"),
            $comment;
    }

    my $end = $data->{end};
    $end = $end->epoch if defined $end;

    # actually update the database
    $sth->execute($data->{type}, $data->{start}->epoch, $end, $data->{data}, $data->{comment})
        or print "DB Error: $sth->errstr";
}


check_login();

print "Content-type: text/html\n\n";
if(request_method() ne "POST") {
    # not a POST request, print the input form
    start_html();
    my $date = localtime->ymd;
    print <<EOF;
        List events that should be added one per line.<br />
        The format of each line is:
        <pre>&lt;code&gt; &lt;start_time&gt; &lt;end_time&gt; &lt;comment&gt;</pre>
        End time should be left off unless its a sleep event.<br />
        The comment field is optional.<br />
        The codes are:
        <ul>
        <li>s for sleep</li>
        <li>f for feed</li>
        <li>w for wet diaper</li>
        <li>d for dirty diaper</li>
        <li>wd for w&amp;d diaper</li>
        </ul>
        <form method="POST">
            Date: <input style="width:80px;" type="text" name="date" value="$date"><br />
            <textarea name="bulk" rows="10"></textarea><br />
            <button type="submit"><i class="fa fa-save"></i> Bulk Import</button>
        </form>
EOF
    end_html();
} else {
    # if they did a POST
    start_html();
    my $bulk = param("bulk") // "";
    my $date = param("date") // localtime->ymd;
    my $dbh = DBI->connect("dbi:SQLite:dbname=secure/baby.db","","") or die;
    my $sth = $dbh->prepare("INSERT INTO baby (type, start, end, data, comment) VALUES (?, ?, ?, ?, ?)");
    for my $line (split /\n/, $bulk) {
        next if $line =~ /^\s*$/; # skip blank lines
        my $data = parse_line($line, $date);
        process_line($data, $line, $sth);
    }
    $dbh->disconnect();
    end_html();
}
