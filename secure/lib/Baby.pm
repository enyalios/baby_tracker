package Baby;

use strict;
use warnings;
use CGI::Cookie;
 
our $VERSION = '1.00';

use base 'Exporter';

our @EXPORT = qw(check_login);

sub check_login {
    # kick them back to the login page if the correct cookie isnt set
    my $path = $ENV{SCRIPT_NAME};
    $path =~ s{/[^/]*$}{};

    open my $fh, "<secure/cookie.txt" or die;
    chomp(my $pass = <$fh>);
    close $fh or die;
    my %cookies = fetch CGI::Cookie;
    if(!defined $cookies{"baby"} || $cookies{"baby"}->value ne $pass) {
        print "Location: $path/login.cgi\n";
        print "Status: 307\n\n";
        exit;
    }
}

1;
