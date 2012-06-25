// simple JS file to experiment with mousing over a server

var canvas;
var ctx;
var servers = {};

mouse_over_setup = function() {
    canvas = document.getElementById("main");
    ctx = canvas.getContext("2d");
    canvas.addEventListener("mousemove", on_canvas_mouseover, false);

    x = canvas.width/2;
    y = canvas.height/2;
    r = 50;

    // draw server(s)
    servers["a"] = { "x" : x, "y" : y, "r" : r, "on" : false};

    primary(x, y, r);
};


on_canvas_mouseover = function(e) {
    var x = e.clientX;
    var y = e.clientY;

    // check if mouse was over server
    for (server in servers) {

	// calculate distance from click
	diffX = x - servers[server]["x"];
	diffY = y - servers[server]["y"];
	distance = Math.sqrt(Math.pow(diffX,2) + Math.pow(diffY,2)) - 5;
	// is it within radius?
	if (distance <= servers[server]["r"]) {
	    // check if that server is set to "true" for mouseover
	    if (servers[server]["on"] == false) {
		// make a shadow under server, and a sound
		document.getElementById("mouse_over_sound").innerHTML = "<embed src='click.wav' hidden=true autostart=true loop=false>";
		servers[server]["on"] = true;
		// draw the drop shadow
		ctx.beginPath();
		ctx.arc(servers[server]["x"], servers[server]["y"], servers[server]["r"], 0, 360, false);
		ctx.strokeStyle = "red";
		ctx.fillStyle = "rgba(10, 10, 10, 1)";
		ctx.lineWidth = 10;
		ctx.shadowColor = "black";
		ctx.shadowBlur = servers[server]["r"] + 50;
		ctx.fill();
		ctx.shadowBlur = 0;
		primary(servers[server]["x"], servers[server]["y"], servers[server]["r"])
	    }
	}
	servers[server]["on"] = false;
    }
};