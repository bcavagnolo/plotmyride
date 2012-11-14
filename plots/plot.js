var pageWidth = 960, pageHeight = 500;

// variables for scatter plots
var margin = {top: 20, right: 20, bottom: 30, left: 60},
    width = pageWidth - margin.left - margin.right,
    height = pageHeight - margin.top - margin.bottom;

// variables for progress meter
var innerR = 150,
    outerR = 200,
    twoPi = 2 * Math.PI,
    formatPercent = d3.format(".0%");
var progress = 0,
    total = 1308573; // Content-Length (file size) & process time

// variables for box plots
var boxMargin = {top: 10, right: 50, bottom: 20, left: 50},
    boxWidth = width / 9 / 2,
    boxHeight = 500 - boxMargin.top - boxMargin.bottom;
var chart = boxChart()
      .whiskers(iqr(10))
      .width(boxWidth)
      .height(boxHeight);

// set the whole chart
var svg = d3.select("#box").append("svg")
         .attr("width", width + margin.left + margin.right)
         .attr("height", height + margin.top + margin.bottom)
      .append("g")
         .attr("class", "whole")
         .attr("transform", "translate(" + pageWidth / 2 + "," + pageHeight / 2 + ")");

$("#box").css("visibility", "hidden");

var pring = d3.select("#progress").append("svg")
   .attr("width", width + margin.left + margin.right)
   .attr("height", height + margin.top + margin.bottom)
   .append("g")
   .attr("class", "whole")
   .attr("transform", "translate(" + pageWidth / 2 + "," + pageHeight / 2 + ")");

d3.select("svg")
  .on("mousemove", function() {
     var zone_num = (event.offsetX-margin.left) / (880/9/2);
     if (zone_num < 0) zone_num = -1;
     else if (zone_num >= 18) zone_num = 18;
     else zone_num = Math.floor(zone_num);
     $("g.box").css("visibility", "hidden");
     $(".num"+zone_num).css("visibility", "visible");
  })
  .on("mouseout", function(){
     $("g.box").css("visibility", "hidden");
  });

// draw progress meter
var arc = d3.svg.arc()
         .startAngle(0)
         .innerRadius(innerR)
         .outerRadius(outerR);
var meter = pring.append("g").attr("class", "progress-meter");
meter.append("path")
      .attr("class", "background")
      .attr("d", arc.endAngle(twoPi));
var foreground = meter.append("path")
      .attr("class", "foreground");
var meterText = meter.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", ".35em");


// set the tooltip element
var tooltip = d3.select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("z-index", "10")
      .style("visibility", "hidden")
      .text("a simple tooltip");


var user_data = [];
var box_data = [];
var username = getURLParameter('username');
var x, y, data;

function parseStrava() {
   // parse the CSV string to float and select user dots
   data.forEach(function(d) {
      d.grade = parseFloat(d.grade);
      d.speed = parseFloat(d.speed)*0.000621371;
      
      var g = d.grade;
      var start_grade = -8, end_grade = 10, diff = 1;
      for (i = 0; i < (end_grade-start_grade)/diff; i++) {
         if (g > i+start_grade && g <= i+start_grade+diff) {
            d.cat = i;
            break;
         }
      }
      var data = box_data[d.cat];
      if (!data) {
         data = box_data[d.cat] = [d.speed];
      } else {
         data.push(d.speed);
      }

      if (d.username == username) {
         user_data.push(d);
      }
   });
}

function preparePlot() {
   // set axis scale variables' ragne
   x = d3.scale.linear().range([0, width]);
   y = d3.scale.linear().range([height, 0]);
   // set axis scale variables' domain using extent() (finding min & max) and nice() (extend the scale domain to nice round numbers)
   x.domain(d3.extent(data, function(d) { return d.grade; })).nice();
   y.domain(d3.extent(data, function(d) { return d.speed; })).nice();
   chart.domain(d3.extent(data, function(d) { return d.speed; }));
   // set axis variables 
   var xAxis = d3.svg.axis().scale(x).orient("bottom").tickFormat(function (d) { return d + " %"});
   var yAxis = d3.svg.axis().scale(y).orient("left").tickFormat(function (d) { return d + " mph"});

   // draw axis and labels
   svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
     .append("text")
      .attr("class", "label")
      .attr("x", width)
      .attr("y", -6)
      .style("text-anchor", "end")
      .text("avg. Grade (%)");
   svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
     .append("text")
      .attr("class", "label")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("avg. Speed (mph)")
}

function plotCrowd() {

   // draw dots and bind events for tooltip
   svg.selectAll(".dot")
      .data(data)
     .enter().append("circle")
      .attr("class", "dot")
      .attr("r", 3)
      .attr("cx", function(d) { return x(d.grade); })
      .attr("cy", function(d) { return y(d.speed); })
      .attr("timemin",function(d){
        var time = d.startDate.split("T")[1].split(":");
        h = parseInt(time[0]);
        m = parseInt(time[1]);
        timemin = h*60 + m
        return timemin;
      });
/*
     .on("mouseover", function(d) {
        tooltip.text(d.grade + ", " + d.speed).style("visibility", "visible");
     })
	  .on("mousemove", function(){
	     tooltip.style("top", (event.pageY-15)+"px").style("left",(event.pageX+15)+"px");
	  })
	  .on("mouseout", function(d){
	     tooltip.style("visibility", "hidden");
	  });
*/
}

function drawBoxes() {
   // draw box plots
   var vis = svg.selectAll("svg")
      .data(box_data)
      .enter().append("g")
         .attr("transform", function(d, i) {
            var left = i * (880/9/2);
            return "translate(" + left + ",0)"
         })
         .attr("class", function (d, i) { return "box num" + i;})
         .attr("width", (880/9/2))
         .attr("height", height)
      .call(chart);
   $("g.box").css("visibility", "hidden");
}

function plotUser() {

   // draw user dots and bind events for tooltip
   svg.selectAll(".userDot")
     .data(user_data)
     .enter().append("circle")
      .attr("class", "userDot")
      .attr("r", 3)
      .attr("cx", function(d) { return x(d.grade); })
      .attr("cy", function(d) { return y(d.speed); })
      .attr("timemin",function(d){
        var time = d.startDate.split("T")[1].split(":");
        h = parseInt(time[0]);
        m = parseInt(time[1]);
        timemin = h*60 + m
        return timemin;
      })
      .style("fill", "#E4E542")
     .on("mouseover", function(d) {
        tooltip.text(d.grade.toFixed(2) + " %, " + d.speed.toFixed(2) + " mph").style("visibility", "visible");
     })
	  .on("mousemove", function(){
	     tooltip.style("top", (event.pageY-15)+"px").style("left",(event.pageX+15)+"px");
	  })
	  .on("mouseout", function(d){
	     tooltip.style("visibility", "hidden");
	  });
    
    //Create slider functionality
     $(function(){
      $('#slider').slider({
        orientation: "vertical",
        max: 1440,
        min: 0,
        range: true,
        values: [40, 1400],        
        slide: function(event, ui) {
           lbound = ui.values[0];
           ubound = ui.values[1];
           $('.dot , .userDot').each(function(){
            if($(this).attr("timemin")>lbound && $(this).attr("timemin")<ubound) {
              $(this).attr("visibility","visible");
              }
            else{
              $(this).attr("visibility","hidden");
            } 
          });
        }
      });
    });
}

function done() {
   // finish drawing, remove progress meter and scale back the plots
   $(".progress-meter").remove();
   $(".box text").remove();
   $(".whole").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
   $("#progress").remove();
   $("#box").css("visibility", "visible");
}

var currentWork = 0;
var work = [parseStrava, preparePlot, plotCrowd, drawBoxes, plotUser, done];

function incrementProgress() {
   updateProgress(loadFraction + (1-loadFraction)*currentWork/work.length);
}

function doWork() {
   if (currentWork >= work.length)
      return;
   work[currentWork++]();
   incrementProgress();
   setTimeout(doWork, 5);
}

var loadFraction = 0.0;
function updateProgress(fraction) {
   // when progressing, draw the progress meter.  Let 50% of progress be
   // the load time, and the rest be data processing.
   if (fraction > 1.0) {
      fraction = 1.0;
   }
   var i = d3.interpolate(progress, fraction);
   d3.transition().tween("progress", function() {
      return function(t) {
         progress = i(t);
         foreground.attr("d", arc.endAngle(twoPi * progress));
         meterText.text(formatPercent(progress));
      };
   });
}

// read CSV and draw the plots
d3.csv("strava.csv", function(theData) {
   data = theData;
   setTimeout(doWork, 5);
})
.on("progress", function(e) {
   loadFraction = d3.event.loaded / total * 0.5;
   updateProgress(loadFraction);
});
