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
template = "words"

# depth of subgraphs
depth = 2


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
    return result_dict


def hydrate_js(graph, target, template="words", base_path="../"):
    json_graph = json.dumps(graph, indent=True)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))
    template = env.get_template("{}.html".format(template))
    dist_path = target
    with open(dist_path, "w") as dist_file:
        dist_file.write(
            template.render(
                graph_data=json_graph,
                base_path=base_path,
            ))


def get_local_subgraph(graph, node_id, max_depth):
    """ Return protion of the graph, that is connected to node_id with maximum
    *depth* links.
    """

    def get_connected_nodes(node_id, recursion_depth=0):
        if recursion_depth >= max_depth:
            return set()
        connected_node_ids = {node_id}
        for link in graph["links"]:
            if link["target"] == node_id:
                connected_node_ids.add(link["source"])
            elif link["source"] == node_id:
                connected_node_ids.add(link["target"])
        next_connected_node_ids = set()
        for connected_node_id in connected_node_ids:
            next_connected_node_ids = next_connected_node_ids.union(
                get_connected_nodes(connected_node_id, recursion_depth + 1))
        return connected_node_ids.union(next_connected_node_ids)

    subgraph = {
        "nodes": [],
        "links": [],
    }

    subgraph_nodes = get_connected_nodes(node_id)

    for node in graph["nodes"]:
        if node["id"] in subgraph_nodes:
            subgraph["nodes"].append(node)

    for link in graph["links"]:
        if link["source"] in subgraph_nodes and link[
                "target"] in subgraph_nodes:
            subgraph["links"].append(link)

    return subgraph


def hydrate_subgraphs(graph, depth, template="words"):
    for node in graph["nodes"]:
        node_id = node["id"]
        subgraph = get_local_subgraph(graph, node_id, depth)
        hydrate_js(subgraph, "dist/local_graphs/{}.html".format(node_id),
                   template, "../../")


graph = create_graph(zettelkasten_path, filename_regex, id_regex,
                     nth_link_limit, exclude_list)
hydrate_js(graph, "dist/index.html", template, "../")

hydrate_subgraphs(graph, depth, template)
