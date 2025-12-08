async function parseSchema(viewdiv) {
  let url = viewdiv.attributes["schema-url"].textContent;
  let resp = await fetch(url);
  let schema = await resp.json();
  return schema;
}

function parseInlineSchema(viewdiv) {
  let inline = JSON.parse(viewdiv.textContent);

  let baseSchema = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  };

  let schema = Object.assign({}, baseSchema, inline);
  return schema;
}

window.onload = function() {
  let viewDivs = document.querySelectorAll("vegachart");

  for (let index = 0; index < viewDivs.length; index++) {
    if ("schema-url" in viewDivs[index].attributes) {
      parseSchema(viewDivs[index]).then(schema => vegaEmbed(viewDivs[index], schema, { "actions": false }));
    } else {
      let schema = parseInlineSchema(viewDivs[index]);
      vegaEmbed(viewDivs[index], schema, { "actions": false });
    }
  }
};
