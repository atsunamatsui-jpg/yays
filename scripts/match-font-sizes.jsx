/*
  Match font sizes: YaysPorkPouch 11-4-26 (habanero lime)  <-  YaysPouchPrint 8-11-25

  HOW TO RUN
  1. Open BOTH files in Adobe Illustrator.
  2. File > Scripts > Other Script...  and choose this file.
  3. Confirm the two file names in the dialog and click OK.
  4. Review the result, then File > Save (or Save As to keep the original).

  WHAT IT DOES
  For every text object in the pork pouch it looks for the matching text in the
  reference pouch and copies the reference's font size (and fixed leading):
    - Same words   -> sizes copied character by character (keeps mixed sizes).
    - Different words but same spot on the artboard (e.g. flavour name)
                   -> sizes copied paragraph by paragraph.
  Anything it cannot match is left untouched and listed in the report, which
  is also saved to your Desktop as "font-size-match-report.txt".
  Text that has been converted to outlines cannot be resized by this script.
*/
#target illustrator

(function () {
    if (app.documents.length < 2) {
        alert("Please open BOTH pouch files in Illustrator first:\n- YaysPorkPouch 11-4-26 (habanero lime)\n- YaysPouchPrint-8-11-25");
        return;
    }

    // ---------- find the two documents ----------
    function findDoc(tests) {
        for (var i = 0; i < app.documents.length; i++) {
            var n = app.documents[i].name.toLowerCase();
            var ok = true;
            for (var t = 0; t < tests.length; t++) if (n.indexOf(tests[t]) < 0) { ok = false; break; }
            if (ok) return app.documents[i];
        }
        return null;
    }
    var target = findDoc(["11-4-26"]) || findDoc(["pork"]);
    var ref = findDoc(["8-11-25"]);

    var names = [];
    for (var d = 0; d < app.documents.length; d++) names.push(app.documents[d].name);

    // Let the user confirm / pick
    var dlg = new Window("dialog", "Match font sizes");
    dlg.alignChildren = "fill";
    dlg.add("statictext", undefined, "Copy font sizes FROM (reference):");
    var refList = dlg.add("dropdownlist", undefined, names);
    dlg.add("statictext", undefined, "Apply font sizes TO (pork pouch):");
    var tgtList = dlg.add("dropdownlist", undefined, names);
    refList.selection = ref ? indexOf(names, ref.name) : 0;
    tgtList.selection = target ? indexOf(names, target.name) : (names.length > 1 ? 1 : 0);
    var cb = dlg.add("checkbox", undefined, "Also match fixed leading (line spacing)");
    cb.value = true;
    var btns = dlg.add("group"); btns.alignment = "right";
    btns.add("button", undefined, "Cancel", { name: "cancel" });
    btns.add("button", undefined, "OK", { name: "ok" });
    if (dlg.show() != 1) return;
    ref = app.documents[refList.selection.index];
    target = app.documents[tgtList.selection.index];
    var doLeading = cb.value;
    if (ref == target) { alert("Please choose two different documents."); return; }

    function indexOf(arr, v) { for (var i = 0; i < arr.length; i++) if (arr[i] == v) return i; return 0; }

    // ---------- helpers ----------
    function norm(s) {
        return String(s).replace(/[\r\n\u0003\t]+/g, " ").replace(/\s+/g, " ")
            .replace(/^\s+|\s+$/g, "").toLowerCase();
    }
    function artboardOf(doc, b) {          // b = geometricBounds [l,t,r,b]
        var cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
        for (var i = 0; i < doc.artboards.length; i++) {
            var r = doc.artboards[i].artboardRect;   // [l,t,r,b]
            if (cx >= r[0] && cx <= r[2] && cy <= r[1] && cy >= r[3]) return i;
        }
        return 0;
    }
    function info(doc, tf) {
        var b = tf.geometricBounds, ai = artboardOf(doc, b), r = doc.artboards[ai].artboardRect;
        var w = r[2] - r[0], h = r[1] - r[3];
        return {
            tf: tf, text: norm(tf.contents), ab: ai,
            cx: (((b[0] + b[2]) / 2) - r[0]) / w,     // relative position on artboard 0..1
            cy: (r[1] - ((b[1] + b[3]) / 2)) / h
        };
    }
    function collect(doc) {
        var out = [];
        for (var i = 0; i < doc.textFrames.length; i++) {
            try { if (norm(doc.textFrames[i].contents) != "") out.push(info(doc, doc.textFrames[i])); } catch (e) {}
        }
        return out;
    }
    function label(s) { s = s.length > 40 ? s.substring(0, 40) + "..." : s; return "\"" + s + "\""; }
    function sizeOf(chars) { try { return Math.round(chars.characterAttributes.size * 100) / 100; } catch (e) { return "?"; } }

    function copyAttrs(src, dst) {
        dst.characterAttributes.size = src.characterAttributes.size;
        if (doLeading) {
            if (src.characterAttributes.autoLeading) dst.characterAttributes.autoLeading = true;
            else { dst.characterAttributes.autoLeading = false; dst.characterAttributes.leading = src.characterAttributes.leading; }
        }
    }

    // ---------- match ----------
    var R = collect(ref), T = collect(target);
    var used = {}, report = [], changed = 0, skipped = [];

    // 1) identical text
    for (var t = 0; t < T.length; t++) {
        for (var r = 0; r < R.length; r++) {
            if (used[r]) continue;
            if (T[t].text == R[r].text) { T[t].match = r; T[t].how = "same text"; used[r] = true; break; }
        }
    }
    // 2) same position on the same artboard (different words, e.g. flavour name)
    for (var t2 = 0; t2 < T.length; t2++) {
        if (T[t2].match != undefined) continue;
        var best = -1, bestD = 0.06;          // within ~6% of the artboard
        for (var r2 = 0; r2 < R.length; r2++) {
            if (used[r2] || R[r2].ab != T[t2].ab) continue;
            var dd = Math.sqrt(Math.pow(R[r2].cx - T[t2].cx, 2) + Math.pow(R[r2].cy - T[t2].cy, 2));
            if (dd < bestD) { bestD = dd; best = r2; }
        }
        if (best >= 0) { T[t2].match = best; T[t2].how = "same position"; used[best] = true; }
    }

    // ---------- apply ----------
    for (var k = 0; k < T.length; k++) {
        var tg = T[k];
        if (tg.match == undefined) { skipped.push(label(tg.text) + "  (no match found, " + sizeOf(tg.tf.textRange) + " pt kept)"); continue; }
        var src = R[tg.match].tf, dst = tg.tf, before = sizeOf(dst.textRange);
        try {
            if (tg.how == "same text" && src.characters.length == dst.characters.length) {
                for (var c = 0; c < dst.characters.length; c++) copyAttrs(src.characters[c], dst.characters[c]);
            } else {
                var sp = src.paragraphs, dp = dst.paragraphs;
                for (var p = 0; p < dp.length; p++) {
                    if (dp[p].characters.length == 0) continue;
                    var s = sp[Math.min(p, sp.length - 1)];
                    var sc = s.characters.length ? s.characters[0] : src.characters[0];
                    copyAttrs(sc, dp[p]);
                }
            }
            var after = sizeOf(dst.textRange);
            if (String(before) != String(after)) changed++;
            report.push(label(tg.text) + ":  " + before + " pt -> " + after + " pt  (" + tg.how + ")");
        } catch (e) {
            skipped.push(label(tg.text) + "  (could not edit: locked or hidden layer?)");
        }
    }

    // ---------- report ----------
    var txt = "Font sizes copied from: " + ref.name + "\nApplied to: " + target.name + "\n\n" +
        "MATCHED (" + report.length + ", " + changed + " changed size)\n" + report.join("\n") +
        "\n\nNOT CHANGED (" + skipped.length + ")\n" + (skipped.length ? skipped.join("\n") : "(none)") +
        "\n\nNote: sizes shown are the first character of each text object." +
        "\nText converted to outlines is not text any more and cannot be resized by this script.";
    try {
        var f = new File(Folder.desktop + "/font-size-match-report.txt");
        f.encoding = "UTF-8"; f.open("w"); f.write(txt); f.close();
    } catch (e) {}
    app.activeDocument = target;
    alert("Done. " + report.length + " text objects matched (" + changed + " resized), " + skipped.length +
        " left unchanged.\n\nFull report saved to your Desktop:\nfont-size-match-report.txt\n\nReview the pouch, then save. Use Edit > Undo repeatedly if you want to revert.");
})();
