import sys
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Literal, Optional

from relationalai_gnns.common.exceptions import ValidationError
from relationalai_gnns.common.job_models import PayloadTypes, PydanticConfigType

from .api_request_handler import APIRequestHandler
from .connector import BaseConnector


@dataclass
class ExperimentConfig:
    """
    Configuration class for experiment metadata.

    Attributes:
        database (str): Name of the database associated with the experiment.
        schema (str): Name of the schema within the database.
    """

    database: str
    schema: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TrainerConfig:
    """
    Configuration class for training a GNN model.

    This class stores all hyperparameters required for training, validation,
    and evaluation of a GNN model.

    :param device: Device to perform training, inference, and feature extraction.
        One of "cuda" or "cpu".
    :type device: str

    :param n_epochs: Number of training epochs. An epoch corresponds to
        a full pass over the training data.
    :type n_epochs: int

    :param max_iters: Maximum number of batch iterations per epoch.
        If None, all batches are processed. If set to a value lower than the
        total number of batches, each epoch will process only a subset.
        Default: None
    :type max_iters: Optional[int]

    :param train_batch_size: Batch size for training. Default: 128
    :type train_batch_size: int

    :param val_batch_size: Batch size for validation. Default: 128
    :type val_batch_size: int

    :param eval_every: Frequency (in epochs) to evaluate on the validation set.
        Default: 1
    :type eval_every: int

    :param patience: Number of epochs with no improvement after which
        training will be stopped early. Default: 5
    :type patience: int

    :param label_smoothing: Whether to apply label smoothing.
        Applicable to node classification tasks. Default: False
    :type label_smoothing: bool

    :param label_smoothing_alpha: Smoothing parameter alpha ∈ (0, 1).
        Default: 0.1
    :type label_smoothing_alpha: float

    :param id_awareness: Whether to use ID-awareness embeddings.
        See: https://github.com/RelationalAI/gnn-learning-engine/blob/main/src/modeling/model.py#L15
        Default: False
    :type id_awareness: bool

    :param use_temporal_encoder: Whether to use a temporal encoding model.
        Default: True
    :type use_temporal_encoder: bool

    :param shallow_embeddings_list: List of non-task table names
        for which to add learnable shallow embeddings.
        Default: []
    :type shallow_embeddings_list: List[str]

    :param clamp_min: Minimum output value for regression tasks. Default: 0
    :type clamp_min: int

    :param clamp_max: Maximum output value for regression tasks. Default: 100
    :type clamp_max: int

    :param seed: Random seed for reproducibility. Default: None
    :type seed: int

    :param lr: Learning rate. Default: 0.001
    :type lr: float

    :param T_max: Maximum number of iterations to apply cosine annealing scheduler.
        If set to None then it defaults to the total number of epochs. Default: None
    :type T_max: int

    :param eta_min: Minimum learning rate for cosine annealing scheduler. Default: 1e-8
    :type eta_min: int

    :param fanouts: List of neighbors to sample per GNN layer.
        For example, [128, 64] samples 128 neighbors at 1st hop and 64 at 2nd.
        Default: [128, 64]
    :type fanouts: Optional[List[int]]

    :param temporal_strategy: Strategy for temporal neighbor sampling.
        "uniform" ignores time; "last" picks most recent. Default: "uniform"
    :type temporal_strategy: Literal["uniform", "last"]

    :param num_negative: Number of negative samples to draw per source node
            in a btach. Valid only for classic_link_prediction problems. Default: 10
    :type num_negative: Optional[int]

    :param negative_sampling_strategy: Negative sampling strategy to use. Either
            "random" or "degree_based". When set to random, negative samples
            are sampled randomly from the destination nodes. When set to degree_based,
            negative samples are sampled proportionally to the destination node degree
            (thus popular items will have a higher chance to be sampled).
            Valid only for classic_link_prediction problems. Default: "random"
    :type negative_sampling_strategy: Optional[str]

    :param text_embedder: Text embedding model for text-based features.
        Default: "model2vec-potion-base-4M"
    :type text_embedder: Literal["model2vec-potion-base-4M", "bert-base-distill"]

    :param channels: Number of hidden channels used across GNN, encoders,
        and prediction heads. Default: 128
    :type channels: Optional[int]

    :param gnn_layers: Number of GNN layers. If None, set to len(fanouts).
        Default: None
    :type gnn_layers: Optional[int]

    :param conv_aggregation: Aggregation method for convolution operations.
        Default: "mean"
    :type conv_aggregation: Literal["mean", "max", "sum"]

    :param hetero_conv_aggregation: Aggregation method across different edge types
        in a heterogeneous graph. Default: "sum"
    :type hetero_conv_aggregation: Literal["mean", "max", "sum"]

    :param gnn_norm: Normalization strategy for GNN layers.
        Default: "layer_norm"
    :type gnn_norm: Literal["batch_norm", "layer_norm", "instance_norm"]

    :param head_layers: Number of MLP layers in the prediction head.
        Default: 1
    :type head_layers: Optional[int]

    :param head_norm: Normalization strategy for the MLP prediction head.
        Default: "batch_norm"
    :type head_norm: Literal["batch_norm", "layer_norm"]
    """

    connector: BaseConnector
    device: str
    n_epochs: int
    experiment_config: ExperimentConfig
    max_iters: int = field(default=sys.maxsize)
    train_batch_size: int = field(default=128)
    val_batch_size: int = field(default=128)
    eval_every: int = field(default=1)
    patience: int = field(default=5)
    label_smoothing: bool = field(default=False)
    label_smoothing_alpha: float = field(default=0.1)
    id_awareness: bool = field(default=False)
    use_temporal_encoder: bool = field(default=True)
    shallow_embeddings_list: List[str] = field(default_factory=list)
    clamp_min: int = field(default=0)
    clamp_max: int = field(default=100)
    seed: int = field(default=None)
    lr: float = field(default=0.001)
    T_max: int = field(default=None)
    eta_min: float = field(default=1e-8)
    fanouts: List[int] = field(default_factory=lambda: [128, 64])
    temporal_strategy: Literal["uniform", "last"] = field(default="uniform")
    num_negative: int = field(default=10)
    negative_sampling_strategy: Literal["random", "degree_based"] = field(default="random")
    text_embedder: Literal["model2vec-potion-base-4M", "bert-base-distill"] = field(default="bert-base-distill")
    channels: int = field(default=128)
    gnn_layers: Optional[int] = None
    conv_aggregation: Literal["mean", "max", "sum"] = field(default="mean")
    hetero_conv_aggregation: Literal["mean", "max", "sum"] = field(default="sum")
    gnn_norm: Literal["batch_norm", "layer_norm", "instance_norm"] = field(default="layer_norm")
    head_layers: int = field(default=1)
    head_norm: Literal["batch_norm", "layer_norm"] = field(default="batch_norm")

    def __post_init__(self):
        """Post-initialization validation and defaults."""
        # If gnn_layers is not set, default to length of fanouts
        if self.gnn_layers is None:
            self.gnn_layers = len(self.fanouts)

        # Validate device setting
        device_list = ["cuda", "cpu"]
        if self.device not in device_list:
            raise ValueError(f"Invalid device '{self.device}'. Choose from {device_list}.")

        # Initalize API Handler
        self.api_handler = APIRequestHandler(self.connector)

        # Validate configuration after initialization
        self.validate()

    def to_dict(self) -> Dict:
        """Return a dict representation of the dataclass that is compatible with the ModelConfig pydantic model for the
        GNN RLE."""
        # set T_max if None to the number of epochs
        if self.T_max is None:
            self.T_max = self.n_epochs

        model_config_dict = {
            "training_parameters": {
                "n_epochs": self.n_epochs,
                "max_iters": self.max_iters,
                "train_batch_size": self.train_batch_size,
                "val_batch_size": self.val_batch_size,
                "eval_every": self.eval_every,
                "patience": self.patience,
                "label_smoothing": self.label_smoothing,
                "label_smoothing_alpha": self.label_smoothing_alpha,
                "id_awareness": self.id_awareness,
                "use_temporal_encoder": self.use_temporal_encoder,
                "num_negative": self.num_negative,
                "negative_sampling_strategy": self.negative_sampling_strategy,
                "seed": self.seed,
                "device": self.device,
                "shallow_embeddings_list": self.shallow_embeddings_list,
            },
            "experiment": self.experiment_config.to_dict(),
            "optimizer": {"name": "adam", "parameters": {"lr": self.lr, "weight_decay": 0.0001}},
            "scheduler": {"name": "cosine", "parameters": {"T_max": self.T_max, "eta_min": self.eta_min}},
            "sampler": {
                "name": "pyg_neighbor_sampling",
                "parameters": {"fanouts": self.fanouts, "temporal_strategy": self.temporal_strategy, "num_workers": 0},
            },
            "feature_extractor": {
                "name": "torch_frame",
                "parameters": {
                    "materialize": False,  # hard-coded to false
                    "text_embedder": {"name": self.text_embedder, "device": self.device},
                },
            },
            "feature_encoder": {
                "name": "hetero_encoder",
                "parameters": {
                    "channels": self.channels,
                    "num_layers": 2,
                    "stype_encoders": {
                        "categorical": {"encoder_name": "TF_EmbeddingEncoder"},
                        "numerical": {"encoder_name": "TF_LinearEncoder"},
                        "multicategorical": {"encoder_name": "TF_MultiCategoricalEmbeddingEncoder"},
                        "embedding": {"encoder_name": "TF_LinearEmbeddingEncoder"},
                        "timestamp": {"encoder_name": "TF_TimestampEncoder"},
                    },
                },
            },
            "temporal_encoder": {
                "name": "temporal_encoder",
                "parameters": {"channels": self.channels, "encoding_type": "Positional"},
            },
            "gnn": {
                "name": "hetero_graph_sage",
                "parameters": {
                    "channels": self.channels,
                    "num_layers": self.gnn_layers,
                    "conv_aggregation": self.conv_aggregation,
                    "hetero_conv_aggregation": self.hetero_conv_aggregation,
                    "skip_connection": False,
                    "skip_connection_before_norm": False,
                    "normalize": False,
                    "norm": self.gnn_norm,
                },
            },
            "head": {
                "name": "MLP",
                "parameters": {
                    "num_layers": self.head_layers,
                    "in_channels": self.channels,
                    "hidden_channels": self.channels,
                    "norm": self.head_norm,
                },
            },
        }

        return model_config_dict

    def validate(self):
        """Validate the configuration."""
        config_dict = self.to_dict()
        payload = {
            "payload_type": PayloadTypes.VALIDATE_CONFIG,
            "config": config_dict,
            "type": PydanticConfigType.MODEL_CONFIG,
        }
        try:
            self.api_handler.make_request(payload)
            return True
        except Exception as e:
            raise ValidationError(e)
