from typing import List, Optional

from pydantic.v1 import BaseModel


class XaiParams(BaseModel):
    """Configuration parameters for explainability (XAI) analysis in Fiddler models.

    XaiParams defines the configuration for explainability analysis, including
    custom explanation methods and default explanation strategies. These parameters
    control how feature importance, SHAP values, and other explainability metrics
    are computed for your model.

    This configuration is essential for models that require custom explanation
    logic or when you want to override the default explanation methods provided
    by Fiddler's built-in explainability features.

    Attributes:
        custom_explain_methods: List of user-defined explanation method names
        default_explain_method: Default explanation method to use when none is specified

    Examples:
        Creating XAI parameters with custom methods:

        xai_params = XaiParams(
            custom_explain_methods=["custom_shap", "custom_lime", "domain_specific"],
            default_explain_method="custom_shap"
        )

        Creating XAI parameters with only default method:

        simple_xai_params = XaiParams(
            default_explain_method="integrated_gradients"
        )

        Creating XAI parameters for multiple explanation strategies:

        multi_xai_params = XaiParams(
            custom_explain_methods=[
                "business_rule_explainer",
                "feature_interaction_explainer",
                "counterfactual_explainer"
            ],
            default_explain_method="business_rule_explainer"
        )

        Creating empty XAI parameters (use Fiddler defaults):

        default_xai_params = XaiParams()
    """
    custom_explain_methods: List[str] = []
    """User-defined explain_custom method of the model object defined in package.py"""

    default_explain_method: Optional[str] = None
    """Default explanation method"""
