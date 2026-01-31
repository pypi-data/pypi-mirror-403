// Wrap in anonymous function to avoid global pollution.
// TODO: Convert to ESM.
(() => {
    const tagmap = get_tagmap();
    if (tagmap) {
        insert_html(tagmap);
    }

    function get_tagmap() {
        const $first_cell = $(".jp-Cell").first();
        var frontmatter;
        try {
            frontmatter = JSON.parse($first_cell.text());
        } catch (error) {
            console.log("No JSON frontmatter in first cell; No further processing.", error);
            return;
        }
        const tagmap = frontmatter?.tagmap;
        if (tagmap) {
            $first_cell.remove();
        }
        return tagmap;
    }

    function show_only(tags) {
        const prefix = "celltag_";
        // Substring match is slightly too general, but unlikely to matter.
        // The DOM for markdown and code cells is different.
        $(`.jp-Cell[class*="${prefix}"]`).hide();
        $(`.jp-Cell:has([class*="${prefix}"])`).hide();
        tags.forEach((tag) => {
            const tag_css = `.${prefix}${tag}`;
            $(`.jp-Cell${tag_css}`).show();
            $(`.jp-Cell:has(${tag_css})`).show()
        });
    }

    function insert_html(tagmap) {
        const $select = $("<select>");
        const delim = "|";
        Object.entries(tagmap).forEach(([label, tags]) => {
            $select.append($("<option>", {value: tags.join(delim)}).text(label));
        });

        // HTML skeleton is just copy-paste from notebook source:
        // Looks ok, but the semantics aren't correct.
        $("main").prepend(`
            <div class="jp-Cell jp-MarkdownCell jp-Notebook-cell">
                <div class="jp-Cell-inputWrapper">
                    <div class="jp-Collapser jp-InputCollapser jp-Cell-inputCollapser">
                    </div>
                    <div class="jp-InputArea jp-Cell-inputArea"><div class="jp-InputPrompt jp-InputArea-prompt">
                        Show:
                    </div>
                    <div class="jp-RenderedHTMLCommon jp-RenderedMarkdown jp-MarkdownOutput" data-mime-type="text/markdown">
                        <select>${$select.html()}</select>
                    </div>
                </div>
            </div>
        `);

        const default_tags = Object.values(tagmap)[0];
        show_only(default_tags);

        $("select").on("change", (event) => {
            const tags = event.target.value.split(delim);
            show_only(tags);
        })
    }
})();