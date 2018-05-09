#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use JSON;
use CGI::Carp qw(fatalsToBrowser);
use FindBin '$Bin';
use lib "$Bin/secure/lib";
use Baby;

check_login();

my $dbh = DBI->connect("dbi:SQLite:dbname=secure/baby.db","","");
my $tree = $dbh->selectall_hashref("SELECT id, type, MAX(start) AS start, end, data FROM baby GROUP BY type", "type");

print <<EOF;
Content-Type: text/html

<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
        <title>Baby!</title>
        <link rel="stylesheet" type="text/css" href="//netdna.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.css" />
        <link rel="stylesheet" type="text/css" href="mystyle.css" />
        <script>
            var dict = {};
            var last_updated = parseInt(new Date() / 1000);
            var fold_visible = 0;
EOF
printf "            dict = JSON.parse('%s');\n", encode_json $tree;
print <<EOF;

            function toggle() {
                var boob = document.getElementById('label').innerHTML;
                if(boob == "right") {
                    boob = "left";
                } else if (boob == "left") {
                    boob = "right";
                } else {
                    // currently saving
                    return;
                }
                set_boob(boob);
                document.getElementById('label').innerHTML = "saving";
                var xmlhttp = new XMLHttpRequest();
                xmlhttp.onreadystatechange = function() {
                    if(xmlhttp.readyState == 4) {
                        dict[boob] = JSON.parse(xmlhttp.responseText);
                        set_boob(boob);
                    }
                }
                xmlhttp.open("POST", "update.cgi", true);
                xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
                xmlhttp.send("type=" + boob);
            }

            function set_boob(boob) {
                if(boob == "left") {
                    document.getElementById('label').innerHTML = "left";
                    document.getElementById('label').style.float = "right";
                    document.getElementById('slider').className = "slider slider-left";
                    document.getElementById('rbutton').style.display = "none";
                    document.getElementById('lbutton').style.display = "block";
                } else if (boob == "right") {
                    document.getElementById('label').innerHTML = "right";
                    document.getElementById('label').style.float = "left";
                    document.getElementById('slider').className = "slider slider-right";
                    document.getElementById('rbutton').style.display = "block";
                    document.getElementById('lbutton').style.display = "none";
                }
            }

            function update(type, data) {
                var xmlhttp = new XMLHttpRequest();
                xmlhttp.onreadystatechange = function() {
                    if(xmlhttp.readyState == 4) {
                        document.getElementById(type + "_img").src="img/"+type+".png";
                        dict[type] = JSON.parse(xmlhttp.responseText);
                        refresh();
                    }
                }
                xmlhttp.open("POST", "update.cgi", true);
                xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
                if(data == 'undefined') {
                    xmlhttp.send("type=" + type);
                } else {
                    xmlhttp.send("type=" + type + "&data=" + data);
                }
                document.getElementById(type + "_img").src="img/spin.gif";
            }

            function format_time(time, unit) {
                //return get_hours(time) + ":" + get_minutes(time) + ":" + get_seconds(time);
                if(unit == "m") {
                    return "<div class='timetext' style='right:110px;'>minutes</div>" + 
                    "<div class='timetext' style='right:10px;'>seconds</div>" + 
                    get_minutes(time) + ":" + get_seconds(time);
                    } else {
                    return "<div class='timetext' style='right:110px;'>hours</div>" + 
                    "<div class='timetext' style='right:10px;'>minutes</div>" + 
                    get_hours(time) + ":" + get_minutes(time);
                }
            }

            function get_hours(time) {
                var hour = parseInt(time/3600);
                //if(hour < 10) { hour = "0" + hour; }
                if(hour == 0) { hour = ""; }
                if(time > 86400) { hour = "24"; }
                return hour;
            }

            function get_minutes(time) {
                var min = parseInt(time/60)%60;
                if(min < 10) { min = "0" + min; }
                if(time > 86400) { min = "00"; }
                return min;
            }

            function get_seconds(time) {
                var sec;
                sec = time%60;
                if(sec < 10) { sec = "0" + sec; }
                if(time > 86400) { sec = "00"; }
                return sec;
            }

            function refresh() {
                var epoch = parseInt(new Date() / 1000);
                if(epoch - last_updated >= 60) {
                    last_updated = epoch;
                    server_side_refresh();
                }
                var change = { 1:"Wet", 2:"Dirty", 3:"W+D" };
                document.getElementById("change").innerHTML = format_time(epoch - dict.change.start);
                document.getElementById("change_status").innerHTML = "Last:<br />" + change[dict.change.data];
                document.getElementById("feed").innerHTML = format_time(epoch - dict.feed.start);
                //document.getElementById("other").innerHTML = format_time(epoch - dict.other.start);
                document.getElementById("pump").innerHTML = format_time(epoch - dict.pump.start);
                document.getElementById("drug").innerHTML = format_time(epoch - dict.drug.start);
                document.getElementById("other").innerHTML = format_time(epoch - dict.other.start);
                if(dict.timer == null) {
                    document.getElementById("timer").innerHTML = format_time(0, "m");
                } else if(dict.timer.end) {
                    document.getElementById("timer").innerHTML = format_time(dict.timer.end - dict.timer.start, "m");
                } else if(dict.timer.start) {
                    document.getElementById("timer").innerHTML = format_time(epoch - dict.timer.start, "m");
                }
                if(document.getElementById("label").innerHTML != "saving") {
                    if(dict.right.start < dict.left.start) {
                        set_boob("left");
                    } else {
                        set_boob("right");
                    }
                }
                if(dict.sleep.end >= dict.sleep.start) {
                    document.getElementById("sleep_status").innerHTML = "Awake";
                    document.getElementById("sleep").innerHTML = format_time(epoch - dict.sleep.end);
                } else {
                    document.getElementById("sleep_status").innerHTML = "Sleeping";
                    document.getElementById("sleep").innerHTML = format_time(epoch - dict.sleep.start);
                }
                print_time();
            }

            function server_side_refresh() {
                var xmlhttp = new XMLHttpRequest();
                xmlhttp.onreadystatechange = function() {
                    if(xmlhttp.readyState == 4) {
                        dict = JSON.parse(xmlhttp.responseText);
                        refresh();
                    }
                }
                xmlhttp.open("GET", "helper.cgi", true);
                xmlhttp.send(null);
            }

            function play(i) {
                var sounds = ["Rockabye Baby", "White Noise"];
                var media = document.getElementById("audio" + i);
                var button = document.getElementById("audiobutton" + i);
                if(!media.paused) {
                    // if the selected audio is playing, pause it
                    if(i == 1) {
                        // if its the white noise track, stop the backup as well
                        document.getElementById("audio2").pause();
                    }
                    media.pause();
                    button.innerHTML = "<i class=\\"fa fa-fw fa-play\\"></i> " + sounds[i];
                } else { 
                    // otherwise, play the selected one
                    if(i == 1) {
                        // if its the white noise track, play both to cover up the skipping when it loops
                        document.getElementById("audio1").currentTime = 5;
                        document.getElementById("audio2").currentTime = 15;
                        document.getElementById("audio1").play();
                        document.getElementById("audio2").play();
                    } else {
                        media.play();
                    }
                    button.innerHTML = "<i class=\\"fa fa-fw fa-pause\\"></i> " + sounds[i];
                }
            }

            function toggle_fold() {
                document.getElementById("drug_row").classList.toggle("hidden-row");
                document.getElementById("other_row").classList.toggle("hidden-row");
                document.getElementById("timer_row").classList.toggle("hidden-row");
                document.getElementById("timer_btn_row").classList.toggle("hidden-row");
                if(fold_visible) {
                    document.getElementById("toggle_fold_link").innerHTML = "<i class=\\"fa fa-lg fa-chevron-down\\">";
                } else {
                    document.getElementById("toggle_fold_link").innerHTML = "<i class=\\"fa fa-lg fa-chevron-up\\">";
                    setTimeout(function() { window.scrollBy(0,500,"smooth"); }, 300);
                }
                fold_visible = (fold_visible+1)%2;
            }

            function toggle_dropdown(event) {
                if(document.getElementById("sound_menu").style.display == "none") {
                    document.getElementById("sound_menu").style.display = "inline-block";
                } else {
                    document.getElementById("sound_menu").style.display = "none";
                }
                event.preventDefault();
            }

            function close_dropdown(event) {
                if(!event.defaultPrevented)
                    document.getElementById("sound_menu").style.display = "none";
            }

            function toggle_clock() {
                var doc = window.document;
                //var docEl = doc.documentElement;
                var docEl = document.getElementById("overlay");
                var mobile = navigator.userAgent.match(/mobile/i)

                if(docEl.style.display != "block") {
                    if(mobile) {
                        var requestFullScreen = docEl.requestFullscreen || docEl.mozRequestFullScreen || docEl.webkitRequestFullScreen || docEl.msRequestFullscreen;
                        requestFullScreen.call(docEl);
                    }
                    docEl.style.display = "block";
                } else {
                    if(mobile) {
                        var cancelFullScreen = doc.exitFullscreen || doc.mozCancelFullScreen || doc.webkitExitFullscreen || doc.msExitFullscreen;
                        cancelFullScreen.call(doc);
                    }
                    docEl.style.display = "none";
                }
            }

            function print_time() {
                var d = new Date();
                var sep = ":";
                if(d.getMilliseconds() >= 500) sep = " ";
                document.getElementById("overlay").innerHTML = "<pre>" + pad(d.getHours(), " ") + sep + pad(d.getMinutes(), "0") + sep + pad(d.getSeconds(), "0") + "</pre>";
            }

            function pad(x, char) {
                if(x < 10) {
                    return "" + char + x
                } else {
                    return x;
                }
            }


            function init() {
                // make the client update every half second
                setInterval(refresh, 500);
                refresh();
                window.addEventListener("click", close_dropdown);
            }

            window.onload = init;
        </script>
    </head>
    <body>
        <div class="overlay" id="overlay" onclick="toggle_clock()"><pre><pre></div>
        <div class="tab-bar">
            <a class="tab tab-active">Summary</a>
            <a class="tab" href="history.cgi">History</a>
            <a class="tab" href="bulk.cgi">Bulk</a>
        </div>
        <table>
EOF
&print_timer_row("change", 1, 0);
print <<EOF;
            <tr>
                <td colspan="3" style="text-align:center;" class="btn-group">
                    <a class="btn btn-fw" href="javascript:update('change', 1)">Wet</a>
                    <a class="btn btn-fw" href="javascript:update('change', 2)">Dirty</a>
                    <a class="btn btn-fw" href="javascript:update('change', 3)">W+D</a>
                </td>
            </tr>
EOF
&print_timer_row("feed", 0, 0);
print <<EOF;
        <tr><td colspan="3">
        <div id="slider_block" style="display:block;"><span class="small">Next feeding on the</span>
        <div style="display:inline-block;">
            <a href="javascript:toggle()">
                <div class='slider' id="slider">
                    <div class='slider-btn' id="lbutton" style='float:left;display:none;'></div>
                    <div class='slider-label' id="label" style='float:left;'></div>
                    <div class='slider-btn' id="rbutton" style='float:right;display:none'></div>
                </div>
            </a>
        </div>
        <span class="small">breast.</span></div>
        </td></tr>
EOF
&print_timer_row("sleep", 0, 0);
&print_timer_row("pump", 0, 0);
&print_timer_row("timer", 1, 1);
print <<EOF;
            <tr id="timer_btn_row" class="hidden-row">
                <td colspan="3" style="text-align:center;">
                    <div class="btn-group">
                        <a class="btn btn-fw" href="javascript:update('timer', 'start')"><i class="fa fa-play"></i></a>
                        <a class="btn btn-fw" href="javascript:update('timer', 'pause')"><i class="fa fa-pause"></i></a>
                        <a class="btn btn-fw" href="javascript:update('timer', 'reset')"><i class="fa fa-refresh"></i></a>
                    </div>
                </td>
            </tr>
EOF
&print_timer_row("drug", 0, 1);
&print_timer_row("other", 0, 1);
print <<EOF;
        </table>
        <br />
        <audio id="audio0" src="audio/rockabyebaby.mp3" loop preload="none"></audio> 
        <audio id="audio1" src="audio/white_noise.short.ogg" loop preload="none"></audio> 
        <audio id="audio2" src="audio/white_noise.short.ogg" loop preload="none"></audio> 
        <div class="bottom-bar">
            <a id="toggle_fold_link" href="javascript:toggle_fold()"><i class="fa fa-lg fa-chevron-down"></i></a>
            <a href="javascript:toggle_clock()"><i class="fa fa-lg fa-clock-o"></i></a>
            <a href="http://nibbler.enyalios.net/monitor/"><i class="fa fa-lg fa-video-camera"></i></a>
            <a onclick="toggle_dropdown(event)" href="javascript:void(0)"><i class="fa fa-lg fa-volume-up"></i></a>
        </div>
        <ul class="dropdown-menu" id="sound_menu" style="display:none;">
            <li><a href="javascript:play(0)" id="audiobutton0"><i class="fa fa-fw fa-play"></i> Rockabye Baby</a></li>
            <li><a href="javascript:play(1)" id="audiobutton1"><i class="fa fa-fw fa-play"></i> White Noise</a></li>
        </ul>
    </body>
</html>
EOF

sub print_timer_row {
    my ($type, $nolink, $hidden) = @_;
    my $url = $nolink?"":" href=\"javascript:update('$type')\"";
    my $display = $hidden?" class=\"hidden-row\"":"";
    print <<EOF;
            <tr id="${type}_row"$display>
                <td><div class="icon"><a$url>
                <!--<div class="superscript">$type</div>-->
                <img src="img/$type.png" id="${type}_img" /></a></div></td>
                <td><div id="$type" class="time"></div></td>
                <td><div id="${type}_status" class="status"></div></td>
            </tr>
EOF
}

=cut

TODO

use superscript or subscript to show which fields are days/hours/minutes
add the ability to filter by event type in the history
track time since last bath (use days/hours instead of hours/minutes)
make the edit.cgi page only do work on POST requests
handle feeding with more granularity
stop the edit page from changing nulls to empty strings and clean them all up in the db
clean up how times are displayed (dont display minutes when they are 0 for mm:ss times)
style input fields so they look nice on all browsers
store the amount pumped in the data field
make the summary boxes on the history page togglable
make the history summary boxes count sleeps that span midnight correctly
