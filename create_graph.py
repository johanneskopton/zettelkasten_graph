import re
import os
import json
import jinja2

# where to find the zettelkasten markdown files
# (currently works only if files are in single directory)
zettelkasten_path = "/home/johannes/Dokumente/zettel/zettelkasten"

# filename pattern for zettelkasten zettel
filename_regex = r'ZTL\S.*\.md'

# pattern for zettel IDs (for in links and filenames)
id_regex = r'(ZTL\d{14})'

# only use the first n links in each document
nth_link_limit = 100

# exclude zettel of the categories in this list
exclude_list = ["person", "beispielzettel"]

# template for display ("nodes" or "words")
template = "nodes"


def create_graph(
    path,
    filename_regex,
    id_regex,
    nth_link_limit=100,
    exclude_list=[],
):
    result_dict = {
        "nodes": [],
        "links": [],
    }
    excluded_ids = []
    link_dict = {}
    for zettel_filename in os.listdir(path):
        if not re.match(filename_regex, zettel_filename):
            continue
        zettel_path = os.path.join(path, zettel_filename)
        with open(zettel_path, "r") as zettel_file:
            zettel_content = zettel_file.read()
        title = re.search(r'^\#\s(.+)[\r\n]', zettel_content).groups()[0]
        category_re = re.search(r'\#([a-zA-ZäöüßÄÖÜ]+)\s', zettel_content)
        if category_re:
            category = category_re.groups()[0]
        else:
            category = "None"
        zettel_id = re.search(id_regex, zettel_filename).groups()[0]
        if category.lower() in exclude_list:
            excluded_ids.append(zettel_id)
            continue
        result_dict["nodes"].append({
            "id": zettel_id,
            "name": title,
            "val": 3,
            "group": category
        })
        links = re.findall(r"\[\[" + id_regex + r"\]\]", zettel_content)
        link_dict[zettel_id] = links
    for zettel_id in link_dict.keys():
        links = link_dict[zettel_id]
        for i, link_id in enumerate(links):
            if i >= nth_link_limit:
                break
            if link_id in excluded_ids:
                continue
            result_dict["links"].append({
                "source": zettel_id,
                "target": link_id
            })
    return json.dumps(result_dict, indent=True)


def hydrate_js(graph, template="nodes"):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))
    template = env.get_template("{}.html".format(template))
    dist_path = "dist/index.html"
    with open(dist_path, "w") as dist_file:
        dist_file.write(template.render(graph_data=graph))


graph = create_graph(zettelkasten_path, filename_regex, id_regex,
                     nth_link_limit, exclude_list)
hydrate_js(graph, template)
