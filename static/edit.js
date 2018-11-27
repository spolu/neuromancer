var get_position = () => {
  var sel = document.getSelection();
  var path = [];
  var anchor = sel.anchorNode
  var current = anchor
  while (current != $('#content')[0] && current != null) {
    path.unshift(current)
    current = current.parentNode
  }

  if (current == null || path.length == 0) {
    return null;
  }

  var line = -1;
  for (var i = 0; i < $('#content')[0].childNodes.length; i ++) {
    if ($('#content')[0].childNodes[i] == path[0]) {
      line = i
    }
  }

  var col = sel.focusOffset
  var text = path[path.length-1].data || ""

  return {
    line: line,
    col: col,
    text: text,
    path: path,
    anchor: anchor
  }
}

var last = [0, 0];
var prediction = "";

var show_prediction = (prediction) => {
  hide_prediction()
  p = get_position()
  console.log("FOOBAR")
  console.log($(p.anchor))
  $(p.anchor).replaceWith(p.text+'<span class="prediction">FOO</span>')
}

var hide_prediction = () => {
  $('#content .prediction').remove()
}

(() => {
  $('#content').on('keydown', (evt) => {
    var p = get_position();

    // Handle space.
    if (evt.keyCode == 32 && evt.shiftKey) {
      prefix = p.text.substr(0, p.col);

      $.get("/predict/" + prefix, (data) => {
        prediction = data['prediction']

        path = p.path
        node = path[path.length-1]

        node.data += prediction + " "

        var range = document.createRange();
        var sel = window.getSelection();
        range.setStart(node, p.col + prediction.length + 1);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
      });

      prediction = ""

      return false;
    }
  })

  //   $('#content').on('keyup', (evt) => {
  //     var p = get_position();
  // 
  //     // Handle shift key up.
  //     if (evt.keyCode == 16) {
  //       return true
  //     }
  // 
  //     // Handle space.
  //     if (evt.keyCode == 32) {
  //       prediction = ""
  //       // $('#prediction').text("")
  //       return true
  //     }
  // 
  //     if (p != null) {
  //       // refresh(position, 0)
  // 
  //       prefix = p.text.substr(0, p.col);
  //       console.log(last + ' -> ' + [p.line, p.col] + ' ' + prefix);
  //       $.get("/predict/" + prefix, (data) => {
  //         prediction = data['prediction']
  //         // show_prediction(prediction)
  //       });
  // 
  //       last = [p.line, p.col];
  //     } else {
  //       // hide_prediction()
  //       last = [0, 0];
  //     }
  //   })
})()
