"""Example Products feature configuration."""

from dataclasses import dataclass, field


@dataclass
class ExampleProductsFeatureConfig:
    """Configuration for the example_products feature.

    Attributes:
        name: The feature name (used for routing prefix).
        verbose_name: Human-readable name for the feature.
        description: Description of the feature's functionality.
        prefix: URL prefix for the feature's routes.
        tags: OpenAPI tags for the feature's routes.
    """

    name: str = "example_products"
    verbose_name: str = "Example Products"
    description: str = "Example product catalog management"
    prefix: str = "/products"
    tags: list[str] = field(default_factory=lambda: ["products"])


feature_config = ExampleProductsFeatureConfig()
