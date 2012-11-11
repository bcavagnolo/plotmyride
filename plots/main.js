function getURLParameter(name) {
  str = RegExp(name + '=' + '(.+?)(&|$)').exec(location.search);
  if (str==null)
    return null;
  return decodeURI(str[1]);
}

$(function() {
  username = getURLParameter('username');
  $('#username').html("Welcome, " + username);
});
