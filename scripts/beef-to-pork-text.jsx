/*
  Beef -> Pork text swap for the Habanero Lime pork jerky pouch.

  Changes (keeps every font, size, colour and style exactly as it is):
    "What's a beef crisp?"                          -> "What's a pork crisp?"
    "Our beef crisps are thinly sliced premium beef" -> "Our pork crisps are thinly sliced premium pork"

  HOW TO RUN
  1. In Illustrator, click on the habanero lime pork pouch file so it is the active document.
  2. File > Scripts > Other Script...  and choose this file.
  3. Review, then File > Save.

  Any OTHER place that still says "beef" is NOT changed, but it is listed in the
  pop-up at the end so you can decide what to do with it.
*/
#target illustrator

(function () {
    if (app.documents.length == 0) { alert("Open the habanero lime pork pouch file first."); return; }
    var doc = app.activeDocument;
    if (!confirm("Change 'beef' to 'pork' in these two lines of:\n" + doc.name + "\n\n" +
        "  What's a beef crisp?\n  Our beef crisps are thinly sliced premium beef\n\nContinue?")) return;

    // phrases to fix; words may be split by spaces or line breaks
    var phrases = [
        /what['’‘]?s\s+a\s+beef\s+crisp/gi,
        /our\s+beef\s+crisps\s+are\s+thinly\s+sliced\s+premium\s+beef/gi
    ];

    // replace one 4-letter word in place, letter by letter, so formatting is kept
    function swapWord(tf, start, word) {
        var repl = "pork";
        for (var i = 0; i < 4; i++) {
            var ch = word.charAt(i), r = repl.charAt(i);
            tf.characters[start + i].contents = (ch == ch.toUpperCase()) ? r.toUpperCase() : r;
        }
    }

    var changed = 0, done = [], others = [], locked = [];
    for (var f = 0; f < doc.textFrames.length; f++) {
        var tf = doc.textFrames[f], text;
        try { text = tf.contents; } catch (e) { continue; }
        if (!/beef/i.test(text)) continue;

        // positions of every "beef" inside the target phrases
        var hits = {};
        for (var p = 0; p < phrases.length; p++) {
            phrases[p].lastIndex = 0;
            var m;
            while ((m = phrases[p].exec(text)) != null) {
                var seg = m[0], re = /beef/gi, b;
                while ((b = re.exec(seg)) != null) hits[m.index + b.index] = true;
            }
        }
        // apply (characters indexes match contents indexes)
        for (var k in hits) {
            var idx = parseInt(k, 10);
            try { swapWord(tf, idx, text.substr(idx, 4)); changed++; }
            catch (e) { locked.push(text.substr(Math.max(0, idx - 15), 40)); }
        }
        if (changed) done.push(tf.contents.replace(/[\r\n\u0003]+/g, " ").substring(0, 70));

        // report remaining "beef" anywhere else
        var after = tf.contents, re2 = /beef/gi, o;
        while ((o = re2.exec(after)) != null)
            others.push("..." + after.substr(Math.max(0, o.index - 20), 45).replace(/[\r\n\u0003]+/g, " ") + "...");
    }

    var msg = "Changed " + changed + " word(s) from beef to pork.";
    if (changed == 0) msg += "\n\nNo matching lines were found. If the text was converted to outlines, " +
        "it can't be edited as text; retype it with the Type tool instead.";
    if (locked.length) msg += "\n\nCould not edit (locked or hidden layer?):\n" + locked.join("\n");
    if (others.length) msg += "\n\n'Beef' still appears here (not changed):\n" + others.slice(0, 10).join("\n") +
        (others.length > 10 ? "\n(+" + (others.length - 10) + " more)" : "");
    else msg += "\n\nNo other 'beef' text left in this file.";
    alert(msg + "\n\nReview the artwork, then File > Save.");
})();
