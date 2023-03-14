
First we assume any token could be related to any prior token.

Then the rough-scorer keeps only the most likely coreferents for each token. It computes all pairwise scores and applies the topk operation to them to retain the pairs with the highest scores. It returns the sparse topk-graph.

The fine-scorer takes the sparsified graph and places a weight on each edge indicating how likely two words are to corefer. It returns the weighted version of the topk-graph.

We place the special empty node in the graph and connect it with weight 0 to all other nodes. We will use this node to absorb all tokens that are not part of any cluster.

During training we normalize the edge-weights with softmax in such a way that the sum of edge weights add up to 1 for each node. We use this normalized softmax - graph and the corresponding labels for training.

During inference we compute the argmax graph instead: for each node we keep the largest outgoing edge. This disconnects the graph and we take the resulting connected components as the clusters. Nodes that ended up in the empty cluster are not returned by the component.


![Alt text](https://explosion.ai/static/aa5b6e430b30f2f17df21adea0ea6ea1/d7477/coref-6.png)
![Alt text](https://explosion.ai/static/3a30827384cc5f8a33f6ae64ea407e78/ed64c/coref-7.png)