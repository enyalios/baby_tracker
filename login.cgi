#!/usr/bin/perl

use strict;
use warnings;
use CGI ":standard";
use CGI::Cookie;
use CGI::Carp qw(fatalsToBrowser);

(my $progname = $0) =~ s,.*/,,;
my ($password, $cookie);
my $message = "";

if(defined param("password")) {
    $password = param("password");
    open my $fh, "<secure/cookie.txt" or die;
    chomp(my $pass_from_file = <$fh>);
    close $fh or die;
    if($password eq $pass_from_file) {
        $cookie = new CGI::Cookie(-name => "baby", -value => $password, -expires => "+3M", -path => "/baby");
        print header(-cookie => $cookie, -location => "/baby");
        exit;
    } else {
        $message = "<br /><span class=\"alert\"><i class=\"fa fa-exclamation-circle\"></i> Bad password.  Please try again.</span><br /><br />";
    }
}

print header(-cookie => $cookie);
print <<EOF;
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="//netdna.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.css" />
        <link rel="stylesheet" type="text/css" href="mystyle.css" />
        <script>
            window.onload = startup;
            function startup() {
                document.forms[0].password.focus();
            }
        </script>
    </head>
    <body>
        <div class="center">
            <img src="img/baby.png" />
            $message
            <form action="$progname" method="POST"><div class="input-group"><span class="input-group-addon"><i class="fa fa-key"></i></span><input type="password" name="password" placeholder="Password"/></div></form>
        </div>
    </body>
</html>
EOF
