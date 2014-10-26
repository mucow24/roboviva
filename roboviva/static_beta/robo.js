function doViva() {
  var value = document.getElementById("routebox").value;
  var url = "routes/" + value;
  window.open(url, "_blank");
}

function onKey(evt) {
  var routebox = document.getElementById("routebox");

  // For compatibility; 'evt' will work on Safari and Chrome, 'window.event' on
  // Firefox (gross)
  var e = evt || window.event;
  var charCode = e.which || e.keyCode;

  // Go on 'Enter'
  if (charCode == 13 && routebox.value != "") {
    doViva();
  }

  // Toggle button state based on input:
  var button = document.getElementById("viva_button");
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
  if (!(charCode == 8 || charCode == 46) &&
      (charCode < 48 || charCode > 57)) {
    return false;
  }
  return true;
}

