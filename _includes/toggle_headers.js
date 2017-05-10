function unhide(headerID) {
  var header, item;
  header = document.getElementById(headerID);
  var hid_header1, hid_header2, hid_header3;
  var hid_item1, hid_item2, hid_item3;

  // Get items according to header
  if (headerID == "image_header") {
      hid_header1 = document.getElementById("library_header");
      hid_header2 = document.getElementById("thumbnail_header");
      hid_header3 = document.getElementById("manipulate_header");
      item = document.getElementById("toggle_image");
      hid_item1 = document.getElementById("toggle_library");
      hid_item2 = document.getElementById("toggle_thumbnail");
      hid_item3 = document.getElementById("toggle_manipulate");
  }
  else if (headerID == "library_header") {
      hid_header1 = document.getElementById("image_header");
      hid_header2 = document.getElementById("thumbnail_header");
      hid_header3 = document.getElementById("manipulate_header");
      item = document.getElementById("toggle_library");
      hid_item1 = document.getElementById("toggle_image");
      hid_item2 = document.getElementById("toggle_thumbnail");
      hid_item3 = document.getElementById("toggle_manipulate");
  }
  else if (headerID == "thumbnail_header") {
      hid_header1 = document.getElementById("image_header");
      hid_header2 = document.getElementById("library_header");
      hid_header3 = document.getElementById("manipulate_header");
      item = document.getElementById("toggle_thumbnail");
      hid_item1 = document.getElementById("toggle_image");
      hid_item2 = document.getElementById("toggle_library");
      hid_item3 = document.getElementById("toggle_manipulate");
  }
  else if (headerID == "manipulate_header") {
      hid_header1 = document.getElementById("image_header");
      hid_header2 = document.getElementById("library_header");
      hid_header3 = document.getElementById("thumbnail_header");
      item = document.getElementById("toggle_manipulate");
      hid_item1 = document.getElementById("toggle_image");
      hid_item2 = document.getElementById("toggle_library");
      hid_item3 = document.getElementById("toggle_thumbnail");
  }
  // Hide images
  item.className = "unhidden";
  hid_item1.className = "hidden";
  hid_item2.className = "hidden";
  hid_item3.className = "hidden";
  // Set header class
  header.className = "unhidden_header";
  hid_header1.className = "hidden_header"
  hid_header2.className = "hidden_header"
  hid_header3.className = "hidden_header"
}
