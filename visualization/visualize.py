import functools
import math

from adapters import (
    allen_data_adapter,
    corenlp_data_adapter,
    huggingface_data_adapter,
    stanford_data_adapter,
)
from IPython.display import HTML, display

HIGHLIGHT_COLORS = [
    "blue",
    "green",
    "pink",
    "orange",
    "purple",
    "teal",
    "tan",
    "red",
    "cobalt",
    "brown",
    "slate",
    "fuchsia",
    "gray",
]


def get_highlight_color(index):
    if index < len(HIGHLIGHT_COLORS):
        return HIGHLIGHT_COLORS[index]
    else:
        calcindex = index - (
            len(HIGHLIGHT_COLORS) * math.floor(index / len(HIGHLIGHT_COLORS))
        )
        calcindex = calcindex % len(HIGHLIGHT_COLORS)
        return HIGHLIGHT_COLORS[calcindex]


# Transofrms tokens and clusters into a tree representation
def transform_to_tree(tokens, clusters):
    def contains(span, index):
        return index >= span[0] and index <= span[1]

    inside_clusters = [{"cluster": -1, "contents": [], "end": -1}]

    for i, token in enumerate(tokens):
        # Find all the new clusters we are entering at the current index
        new_clusters = []
        for j, cluster in enumerate(clusters):
            # Make sure we're not already in this cluster
            if j not in [c["cluster"] for c in inside_clusters]:
                for span in cluster:
                    if i in span:
                        new_clusters.append({"end": span[1], "cluster": j})

        # Enter each new cluster, starting with the leftmost
        new_clusters = sorted(
            new_clusters, key=functools.cmp_to_key(lambda a, b: b["end"] - a["end"])
        )
        for new_cluster in new_clusters:
            # Descend into the new cluster
            inside_clusters.append(
                {
                    "cluster": new_cluster["cluster"],
                    "contents": [],
                    "end": new_cluster["end"],
                }
            )

        # Add the current token into the current cluster
        inside_clusters[-1]["contents"].append(token)

        # Exit each cluster we're at the end of
        while len(inside_clusters) > 0 and inside_clusters[-1]["end"] == i:
            top_cluster = inside_clusters[-1]
            inside_clusters.pop()
            inside_clusters[-1]["contents"].append(top_cluster)

    return inside_clusters[0]["contents"]


# This is the function that calls itself when we recurse over the span tree.
def gen_elem(token, idx, depth):
    if isinstance(token, dict) or isinstance(token, list):
        return '<span key={} class="highlight {}" depth={} id={} onmouseover="handleHighlightMouseOver(this)" \
                onmouseout="handleHighlightMouseOut(this)" labelPosition="left">\
                <span class="highlight__label"><strong>{}</strong></span>\
                <span class="highlight__content">{}</span></span>'.format(
            idx,
            get_highlight_color(token["cluster"]),
            depth,
            token["cluster"],
            token["cluster"],
            " ".join(span_wrapper(token["contents"], depth + 1)),
        )
    else:
        return "<span>{} </span>".format(token)


# Wraps the tree representation into spans indicating cluster-wise depth
def span_wrapper(tree, depth):
    return [gen_elem(token, idx, depth) for idx, token in enumerate(tree)]


def unify_data_format(fn):
    def unified_data(data, **kwargs):
        if kwargs.get("stanford", False):
            tokens, clusters = stanford_data_adapter(data)
        if kwargs.get("corenlp", False):
            tokens, clusters = corenlp_data_adapter(data)
        if kwargs.get("allen", False):
            tokens, clusters = allen_data_adapter(data)
        if kwargs.get("huggingface", False):
            tokens, clusters = huggingface_data_adapter(data)
        if kwargs.get("proref", False):
            tokens, clusters = labelled_pronoun(data)

        return fn(tokens, clusters, **kwargs)

    return unified_data


# Either return the html string or rander in a jupyter notebook output
# Function signature based on displacy render functionality
@unify_data_format
def render(
    tokens,
    clusters,
    style="coref",
    stanford=False,
    corenlp=False,
    allen=False,
    huggingface=False,
    proref=False,
    jupyter=True,
):

    # print("tokens:", tokens)
    # print("clust:", clusters)
    html = to_html(tokens, clusters)

    if jupyter:
        display(HTML(html))
    else:
        return html


def tokens_and_clusters(tokens, clusters):
    html = to_html(tokens, clusters)
    display(HTML(html))


def labelled_pronoun(row):
    txt = row.text

    # map char indices to token indices
    tokens = txt.split(" ")
    start_a = len(txt[: row.a_offset].split(" ")) - 1
    start_b = len(txt[: row.b_offset].split(" ")) - 1

    clusters = [
        [[start_a, start_a + len(row.a.split(" ")) - 1]],
        [[start_b, start_b + len(row.b.split(" ")) - 1]],
    ]

    # add pronoun token to the labelled cluster
    start_p = len(txt[: row.pronoun_offset].split(" ")) - 1
    if row.a_coref:
        clusters[0].append([start_p, start_p + len(row.pronoun.split(" ")) - 1])
    elif row.b_coref:
        clusters[1].append([start_p, start_p + len(row.pronoun.split(" ")) - 1])
    else:
        clusters.append([[start_p, start_p + len(row.pronoun.split(" ")) - 1]])

    return tokens, clusters


def to_html(tokens, clusters):
    tree = transform_to_tree(tokens, clusters)
    html = "".join(span_wrapper(tree, 0))
    html = '<div id="highlight-container" style="padding: 16px;">{}</div>'.format(html)
    return html
