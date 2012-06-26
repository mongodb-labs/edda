// test 2: draw basic servers

var canvas;


serverSetup = function() {
    canvas = document.getElementById("background_layer");
    var ctx = canvas.getContext("2d");
    ctx.beginPath();
    ctx.rect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#4E3629";
    ctx.fill();

};


generate_coords = function(count, names) {

    var r = 50;
    var w = canvas.width;
    var h = canvas.height;

    switch(count) {
    case 0:
    break;
    case 1:
	// one centered server
	servers[names[0]] = { "x" : w/2, "y" : h/2, "r" : r, "on" : false, "type" : "primary" };
	break;
    case 2:
	// two servers, one on either side
	servers[names[0]] = {"x" : w/3, "y" : h/2, "r" : r, "on" : false, "type" : "primary"};
	servers[names[1]] = {"x" : (0.66)*w, "y" : h/2, "r" : r, "on" : false, "type" : "primary"};
	break;
    case 3:
	// three servers in a triangle
	servers[names[0]] = {"x" : w/2, "y" : h/3, "r" : r, "on" : false, "type" : "primary"};
	servers[names[1]] = {"x" : w/3, "y" : (0.66)*h, "r" : r, "on" : false, "type" : "primary"};
	servers[names[2]] = {"x" : (0.66)*w, "y" : (0.66)*h, "r" : r, "on" : false, "type" : "primary"};
	break;
    case 4:
	// four servers in a square
	servers[names[0]] = {"x" : w/3, "y" : h/3, "r" : r, "on" : false, "type" : "primary"};
	servers[names[1]] = {"x" : w/3, "y" : (0.66)*h, "r" : r, "on" : false, "type" : "primary"};
	servers[names[2]] = {"x" : (0.66)*w, "y" : (0.66)*h, "r" : r, "on" : false, "type" : "primary"};
	servers[names[3]] = {"x" : (0.66)*w, "y" : h/3, "r" : r, "on" : false, "type" : "primary"};
	break;
    case 5:
	// five servers in a pentagon
	break;
    case 6:
	// six servers in a wheel
	break;
    case 7:
	// seven servers in a wheel
	break;
    }
};


primary = function(x, y, r, ctx) {
    // draw a primary server with radius r centered at (x, y)
     // draw a green circle with a yellow stroke
    circle(x, y, r, "#24B314", "#F0E92F", 18, ctx);
    // add the crown
    crown(x, (y - 0.22*r), 0.6*r, 0.5*r, ctx);
};

down = function(x, y, r, ctx) {
    // draw a down server
    ctx.globalAlpha = 0.4; // 40% opacity
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 360, false);
    ctx.lineWidth = 9;
    ctx.strokeStyle = "#9A9A9A";
    ctx.fillStyle = "#515151";
    ctx.fill();
    ctx.globalAlpha = 1; // full opacity
    //ctx.stroke();

    // generate dotted outline
    var a = 0;
    var b = 0.05;
    while (b <= 2) {
	ctx.beginPath();
	ctx.arc(x, y, r, a*Math.PI, b*Math.PI, false);
	ctx.stroke();
	a += 0.08;
	b += 0.08;
        }
};


arbiter = function(x, y, r, ctx) {
    // draw an arbiter centered at (x, y) with radius r

    // draw bottom white circle
    ctx.beginPath();

    ctx.lineWidth = 5;

    ctx.arc(x, y, r, 0, 360, false);
    ctx.fillStyle = "#BFB1A4";
    ctx.fill();

    // draw stripes
    // right stripe
    ctx.fillStyle = "#33312F";
    ctx.beginPath();
    ctx.arc(x, y, r, -0.4 * Math.PI, -0.25 * Math.PI, false);
    ctx.lineTo(x + r * Math.sin(0.25 * Math.PI), y + r * Math.sin(45));
    ctx.arc(x, y, r, 0.25 * Math.PI, 0.4 * Math.PI, false);
    ctx.lineTo(x + r * Math.cos(0.4 * Math.PI), y - r * Math.sin(0.4 * Math.PI));
    ctx.fill();

    // left stripe
    ctx.beginPath();
    ctx.arc(x, y, r, -0.6 * Math.PI, -0.75 * Math.PI, true);
    ctx.lineTo(x - r * Math.sin(0.25 * Math.PI), y + r * Math.sin(45));
    ctx.arc(x, y, r, -1.25*Math.PI, -1.4*Math.PI, true);
    ctx.lineTo(x - r * Math.cos(0.4 * Math.PI), y - r * Math.sin(0.4*Math.PI));
    ctx.fill();

    // top circle, just for outline
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 360, false);
    ctx.strokeStyle = "#1A1007";
    ctx.stroke();

};

circle = function(x, y, r, fill, stroke, wt, ctx) {
    // draw a circle with given qualities
    ctx.fillStyle = fill;
    ctx.beginPath();
    ctx.arc(x,y, r, 0, 360, false);
    ctx.lineWidth = wt;
    ctx.strokeStyle = stroke;
    ctx.stroke();
    ctx.fill();
};

user = function(x, y, r, ctx) {
    // draw a user circle with radius r centered at (x, y)
    circle(x, y, r, "#93191C", "#AF434B", 5, ctx);
};

secondary = function(x, y, r, ctx) {
    // draw a secondary server with radius r centered at (x, y)
    // draw a green circle with a
    circle(x, y, r, "#24B314", "#196E0F", 18, ctx);
};


crown = function(x, y, w, h, ctx) {
    // draw a crown with center spike at (x, y)
    // with width w and height h
    // fill yellow
    ctx.beginPath();
    ctx.moveTo(x, y);
    // right side
    ctx.lineTo(x + w/5, y + h/2);
    ctx.lineTo(x + (2*w/5), y + h/5);
    ctx.lineTo(x + (3*w/5), y + (0.55)*h);
    ctx.lineTo(x + w, y + h/5);
    ctx.lineTo(x + (2*w/3), y + h);
    // left side
    ctx.lineTo(x - (2*w/3), y + h);
    ctx.lineTo(x - w, y + h/5);
    ctx.lineTo(x - (3*w/5), y + 0.55*h);
    ctx.lineTo(x - (2*w/5), y + h/5);
    ctx.lineTo(x - w/5, y + h/2);
    ctx.lineTo(x, y);
    // set fills and line weights
    ctx.lineWidth = 2; // consider setting dynamically for scaling
    ctx.lineJoin = "miter";
    ctx.stroke();
    ctx.fillStyle = "#F0E92F";
    ctx.fill();
};

