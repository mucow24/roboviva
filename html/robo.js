function doViva() {
  value = document.getElementById("routebox").value;
  url = "http://ugcs.caltech.edu/~mucow/cgi-bin/roboviva.py?routeid=" + value;
  window.open(url, "_blank");
}

function onKey(event) {
  routebox = document.getElementById("routebox");

  // Go on 'Enter'
  if (event.keyCode == 13 && routebox.value != "") {
    doViva();
  } 

  // Toggle button state based on input: 
  button = document.getElementById("viva_button");
  if (routebox.value == "") {
    button.setAttribute("class", "viva_button_disabled");
    button.onclick = "";
    button.innerHTML = "Enter Route #";
  } else {
    button.setAttribute("class", "viva_button_enabled");
    button.innerHTML = "¡Viva!";
    button.onclick   = doViva;
  }

  // Reject inputs that aren't numeric, but allow backspace/delete:
  if (!(event.keyCode == 8 || event.keyCode == 46) && 
      (event.keyCode < 48 || event.keyCode > 57)) {
    return false;
  }
  return true;
}

