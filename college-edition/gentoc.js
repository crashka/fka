/**
 * Generate sinple table of contents for specified section type, insert
 * before first section referenced.  The TOC format is as follows (with
 * id and class names parameterized for easier styling):
 *
 * <div id="toc_id">
 *   <p class="title_cl">Title Text</p>
 *   <ul class="list_cl"></ul>
 * </div>
 *
 * @param {string} title    title text for toc
 * @param {string} toc_id   id for container <div>
 * @param {string} title_cl class name for title <p>
 * @param {string} list_cl  class name for toc <ul>
 * @param {string} sect     element tag for content sections (must have id)
 */
function gentoc(title, toc_id, title_cl, list_cl, sect) {
  var $toc = $("<div id='" + toc_id + "'></div>")
  $toc.append("<p class='" + title_cl + "'>" + title + "</p>")
  $toc.append("<ul class='" + list_cl + "'></ul>")
  $(sect).first().before($toc)
    
  var list = '.' + list_cl
  $(list).empty();
  $(sect).each(function() {
    var li = "<li><a href='#" + $(this).attr('id') + "'>" +
        $(this).text() + "</a></li>";
    $(list).append(li);
  });
}
