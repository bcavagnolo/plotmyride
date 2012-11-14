var athletes = [];

$(function () {
  // Fake a dynamic back end by grabbing the whole list of athletes.
  d3.csv("athletes.csv", function(data) {
    data.forEach(function(d) {
      athletes.push(d.username);
    });
  });

  $("#login").submit(function (e) {
    pw = $('#pw').val();
	$('#pw').val("");
    username = $('#uname').val().trim();
    if (!username) {
      $('#message').text("Please enter a username!");
      return false;
    }
    if (!pw) {
      $('#message').text("Please enter your password!");
      return false;
    }
    if (athletes.indexOf(username) == -1) {
      $('#message').text("Invalid username!");
      return false;
    }
  });
});
