// simple JS file to experiment with mousing over a server

var canvas;
var ctx;
var server_layer;

mouse_over_setup = function() {
    canvas = document.getElementById("background_layer");
    server_layer = canvas.getContext("2d");

    canvas2 = document.getElementById("shadow_layer");
    shadows = canvas2.getContext("2d");
    canvas2.addEventListener("mousemove", on_canvas_mouseover, false);

    message = document.getElementById("message_layer");
    message_layer = message.getContext("2d");


    x = canvas.width/2;
    y = canvas.height/2;
    r = 25;

    // draw server(s)
    var randomnumber;
    var xval, yval;/*
    for(var i = 0; i < 10; i++) {
		randomnumber = Math.floor(Math.random()*5);
		xval = Math.floor(Math.random()*800);
		yval = Math.floor(Math.random()*600);

		if(randomnumber === 0) {
			servers[i] = { "x" : xval, "y" : yval, "r" : r, "on" : false, "type" : "primary"};
			primary(xval, yval, r, server_layer);
		}
		else if (randomnumber == 1) {
			servers[i] = { "x" : xval, "y" : yval, "r" : r, "on" : false, "type" : "secondary"};
			secondary(xval, yval, r, server_layer);
		}
		else if (randomnumber == 2) {
			servers[i] = { "x" : xval, "y" : yval, "r" : r, "on" : false, "type" : "arbiter"};
			arbiter(xval, yval, r, server_layer);
		}
		else if (randomnumber == 3) {
			servers[i] = { "x" : xval, "y" : yval, "r" : 10, "on" : false, "type" : "user"};
			user(xval, yval, 10, server_layer);
		}
		else if (randomnumber == 4) {
			servers[i] = { "x" : xval, "y" : yval, "r" : r, "on" : false, "type" : "down"};
			down(xval, yval, r, server_layer);
		}
    }*/
};


on_canvas_mouseover = function(e) {
    var x = e.clientX;
    var y = e.clientY;

    // check if mouse was over server
    for (server in servers) {

		// calculate distance from click
		diffX = x - servers[server]["x"];
		diffY = y - servers[server]["y"];
		distance = Math.sqrt(Math.pow(diffX,2) + Math.pow(diffY,2));
		console.log("Distance is: %d, Xcenter: %d, Ycenter: %d, Xactual: %d, Yactual: %d", distance, servers[server]["x"], servers[server]["y"], x, y);
		// is it within radius?
		if (distance <= servers[server]["r"]) {
			// check if that server is set to "true" for mouseover
			if (!servers[server]["on"]) {
			// make a shadow under server, and a sound
			document.getElementById("mouse_over_sound").innerHTML = "<embed src='click.wav' hidden=true autostart=true loop=false>";
			servers[server]["on"] = true;
			// draw the drop shadow
			shadows.beginPath();
			shadows.arc(servers[server]["x"], servers[server]["y"], servers[server]["r"], 0, 360, false);
			shadows.strokeStyle = "red";
			shadows.fillStyle = "rgba(10, 10, 10, 1)";
			shadows.lineWidth = 10;
			shadows.shadowColor = "black";
			shadows.shadowBlur = servers[server]["r"] + 50;
			shadows.fill();
			shadows.shadowBlur = 0;
			//canvas.width = canvas.width;
			most_foreground.fillStyle = "black";
			most_foreground.rect(x, y, 100, 100);
			//most_foreground.fill();


			/*
			if(servers[server]["type"] == "primary")
				primary(servers[server]["x"], servers[server]["y"], servers[server]["r"], most_foreground);
			else if(servers[server]["type"] == "arbiter")
				arbiter(servers[server]["x"], servers[server]["y"], servers[server]["r"], most_foreground);
			else if(servers[server]["type"] == "user")
				user(servers[server]["x"], servers[server]["y"], servers[server]["r"], most_foreground);
			else if(servers[server]["type"] == "secondary")
				secondary(servers[server]["x"], servers[server]["y"], servers[server]["r"], most_foreground);
			else if(servers[server]["type"] == "down")
				down(servers[server]["type"], servers[server]["y"], servers[server]["r"], most_foreground);
			*/
		}
	}
		/*else {
			if(servers[server]["on"]){
				canvas3.width = canvas3.width;
				canvas2.width = canvas2.width;
				message.width = message.width;
				servers[server]["on"] = false;
			}
		}*/
	}
};
