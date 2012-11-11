var pageWidth = 960, pageHeight = 500;

// variables for scatter plots
var margin = {top: 20, right: 20, bottom: 30, left: 60},
    width = pageWidth - margin.left - margin.right,
    height = pageHeight - margin.top - margin.bottom,
    formatTooltip = d3.format(".2");

// variables for progress meter
var innerR = 150,
    outerR = 200,
    twoPi = 2 * Math.PI,
    formatPercent = d3.format(".0%");
var progress = 0,
    total = 1308573; // Content-Length (file size) & process time

// variables for box plots
var boxMargin = {top: 10, right: 50, bottom: 20, left: 50},
    boxWidth = 120 - boxMargin.left - boxMargin.right,
    boxHeight = 500 - boxMargin.top - boxMargin.bottom;
var chart = boxChart()
      .whiskers(iqr(1.5))
      .width(boxWidth)
      .height(boxHeight);

// set the whole chart
var svg = d3.select("body").append("svg")
         .attr("width", width + margin.left + margin.right)
         .attr("height", height + margin.top + margin.bottom)
      .append("g")
         .attr("class", "whole")
         .attr("transform", "translate(" + pageWidth / 2 + "," + pageHeight / 2 + ")");
//  .on("mousemove", function() {
//   console.log(event);
//  });

// draw progress meter
var arc = d3.svg.arc()
         .startAngle(0)
         .innerRadius(innerR)
         .outerRadius(outerR);
var meter = svg.append("g").attr("class", "progress-meter");
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
      .style("position", "absolute")
      .style("z-index", "10")
      .style("visibility", "hidden")
      .text("a simple tooltip");

// read CSV and draw the plots
d3.csv("strava.csv", function(data) {
   var user_data = [];
   var box_data = [];
   // parse the CSV string to float and select user dots
   data.forEach(function(d) {
      d.grade = parseFloat(d.grade);
      d.speed = parseFloat(d.speed);
      
      // TODO: should automatically calculate
      var g = d.grade;
      if (g > -8 && g <= -6) {
         d.cat = 0;
      } else if (g > -6 && g <= -4) {
         d.cat = 1;
      } else if (g > -4 && g <= -2) {
         d.cat = 2;
      } else if (g > -2 && g <= 0) {
         d.cat = 3;
      } else if (g > 0 && g <= 2) {
         d.cat = 4;
      } else if (g > 2 && g <= 4) {
         d.cat = 5;
      } else if (g > 4 && g <= 6) {
         d.cat = 6;
      } else if (g > 6 && g <= 8) {
         d.cat = 7;
      } else if (g > 8 && g <= 10) {
         d.cat = 8;
      }

      var data = box_data[d.cat];
      if (!data) {
         data = box_data[d.cat] = [d.speed];
      } else {
         data.push(d.speed);
      }

      // TODO: get the athlete_id
      if (d.athlete_id == "228156") {
         user_data.push(d);
      }
   });
   
   // set axis scale variables' ragne
   var x = d3.scale.linear().range([0, width]);
   var y = d3.scale.linear().range([height, 0]);
   // set axis scale variables' domain using extent() (finding min & max) and nice() (extend the scale domain to nice round numbers)
   x.domain(d3.extent(data, function(d) { return d.grade; })).nice();
   y.domain(d3.extent(data, function(d) { return d.speed; })).nice();
   chart.domain(d3.extent(data, function(d) { return d.speed; }));
   // set axis variables 
   var xAxis = d3.svg.axis().scale(x).orient("bottom");
   var yAxis = d3.svg.axis().scale(y).orient("left");

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
      .text("avg. Grade");
   svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
     .append("text")
      .attr("class", "label")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("avg. Speed")
   var n_xblocks = $("g.x").children("g").length - 1;

   // draw dots and bind events for tooltip
   svg.selectAll(".dot")
      .data(data)
     .enter().append("circle")
      .attr("class", "dot")
      .attr("r", 3)
      .attr("cx", function(d) { return x(d.grade); })
      .attr("cy", function(d) { return y(d.speed); })
     .on("mouseover", function(d) {
        tooltip.text(d.grade + ", " + d.speed).style("visibility", "visible");
        $(this).attr("style", "fill: green");
        $("rect.box", ".num" + d.cat).attr("style", "fill: orange");
     })
	  .on("mousemove", function(){
	     tooltip.style("top", (event.pageY-15)+"px").style("left",(event.pageX+15)+"px");
	  })
	  .on("mouseout", function(d){
	     $(this).attr("style", "fill: none");
	     tooltip.style("visibility", "hidden");
	     $("rect.box", ".num" + d.cat).attr("style", "fill: #fff");
	  });

    // draw user dots and bind events for tooltip
   svg.selectAll(".userDot")
     .data(user_data)
     .enter().append("circle")
      .attr("class", "userDot")
      .attr("r", 3)
      .attr("cx", function(d) { return x(d.grade); })
      .attr("cy", function(d) { return y(d.speed); })
      .style("fill", "orange")
     .on("mouseover", function(d) {
        tooltip.text(d.grade + ", " + d.speed).style("visibility", "visible");
        $(this).attr("style", "fill: red");
        $("rect.box", ".num"+d.cat).attr("style", "fill: orange");
     })
	  .on("mousemove", function(){
	     tooltip.style("top", (event.pageY-15)+"px").style("left",(event.pageX+15)+"px");
	  })
	  .on("mouseout", function(d){
	     tooltip.style("visibility", "hidden");
	     $(this).attr("style", "fill: orange");
	     $("rect.box", ".num"+d.cat).attr("style", "fill: #fff");
	  });

   // draw box plots
   var vis = d3.select("#box").selectAll("svg")
      .data(box_data)
      .enter().append("svg")
         .attr("class", function (d, i) { return "box num" + i;})
         .attr("width", boxWidth + boxMargin.left + boxMargin.right)
         .attr("height", boxHeight + boxMargin.bottom + boxMargin.top)
      .append("g")
         .attr("transform", "translate(" + boxMargin.left + "," + boxMargin.top + ")")
      .call(chart);

   // finish drawing, remove progress meter and scale back the plots
   $(".progress-meter").remove();
   $(".whole").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
})
.on("progress", function(e) {
   // when progressing, draw the progress meter
   var i = d3.interpolate(progress, d3.event.loaded / total);
   d3.transition().tween("progress", function() {
      return function(t) {
         progress = i(t);
         foreground.attr("d", arc.endAngle(twoPi * progress));
         meterText.text(formatPercent(progress));
      };
   });
});
