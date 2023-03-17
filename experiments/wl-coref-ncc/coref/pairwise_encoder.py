""" Describes PairwiseEncodes, that transforms pairwise features, such as
distance between the mentions into feature embeddings
"""
import torch

from coref.config import Config
from coref.const import Doc


class PairwiseEncoder(torch.nn.Module):
    """ A Pytorch module to obtain feature embeddings for pairwise features

    Usage:
        encoder = PairwiseEncoder(config)
        pairwise_features = encoder(pair_indices, doc)
    """
    def __init__(self, config: Config):
        super().__init__()
        emb_size = config.embedding_size
        # each position corresponds to a bucket:
        #   [(0, 2), (2, 3), (3, 4), (4, 5), (5, 8),
        #    (8, 16), (16, 32), (32, 64), (64, float("inf"))]
        self.distance_emb = torch.nn.Embedding(9, emb_size)
        self.dropout = torch.nn.Dropout(config.dropout_rate)
        self.shape = emb_size  # distance

    @property
    def device(self) -> torch.device:
        return next(self.distance_emb.parameters()).device

    def forward(self,  # type: ignore  # pylint: disable=arguments-differ  #35566 in pytorch
                top_indices: torch.Tensor,
                doc: Doc) -> torch.Tensor:
        word_ids = torch.arange(0, len(doc["cased_words"]), device=self.device)
        # bucketing the distance (see __init__())
        distance = (word_ids.unsqueeze(1) - word_ids[top_indices]
                    ).clamp_min_(min=1)
        log_distance = distance.to(torch.float).log2().floor_()
        log_distance = log_distance.clamp_max_(max=6).to(torch.long)
        distance = torch.where(distance < 5, distance - 1, log_distance + 2)
        distance = self.distance_emb(distance)

        return self.dropout(distance)
