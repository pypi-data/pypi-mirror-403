"""
metaflow-pyinstrument: Profile Metaflow steps with pyinstrument HTML cards.
"""

import os

METAFLOW_PACKAGE_POLICY = "include"
# Ensure this module is included in Metaflow's code package

from metaflow import user_step_decorator, StepMutator

__all__ = ["pyinstrument_card"]


@user_step_decorator
def _pyinstrument_profile(step_name, flow, inputs=None, attributes=None):
    """
    Profiles step execution with pyinstrument.
    Sets flow.html (or custom attribute) to the profiler's HTML output.
    """
    try:
        from pyinstrument import Profiler
    except ImportError as e:
        raise ImportError(
            "pyinstrument is required for @pyinstrument_card. "
            "Add @pypi_base(packages={'pyinstrument': ''}) to your flow class."
        ) from e

    attr = attributes or {}
    html_attribute = attr.get("html_attribute", "html")
    interval = attr.get("interval", 0.001)

    profiler = Profiler(interval=interval)
    profiler.start()

    yield  # User's step code executes here

    profiler.stop()
    setattr(flow, html_attribute, profiler.output_html())
    print(f"[pyinstrument_card] Profiling complete for step '{step_name}'")


class pyinstrument_card(StepMutator):
    """
    Profile step execution with pyinstrument and render results as an HTML card.

    This StepMutator wraps your step with pyinstrument profiling and outputs
    an interactive HTML flame graph as a Metaflow card.

    Parameters
    ----------
    card_id : str, default "pyinstrument"
        Unique identifier for the card.
    html_attribute : str, default "html"
        Artifact name for the HTML output.
    interval : float, default 0.001
        Sampling interval in seconds. Use smaller values (e.g., 0.0001)
        for short-running code.

    Requirements
    ------------
    - @pypi_base(packages={'pyinstrument': ''}) on your flow class
    - pip install metaflow-card-html

    Example
    -------
    >>> @pypi_base(packages={'pyinstrument': ''})
    ... class MyFlow(FlowSpec):
    ...     # ... other step decorators ...
    ...     @pyinstrument_card
    ...     @step
    ...     def train(self):
    ...         # code to profile
    ...         self.next(self.end)
    """

    def init(self, *args, **kwargs):
        self.card_id = kwargs.get("card_id", "pyinstrument")
        self.html_attribute = kwargs.get("html_attribute", "html")
        self.interval = kwargs.get("interval", 0.001)

    def mutate(self, mutable_step):
        mutable_step.add_decorator(
            "card",
            deco_kwargs={
                "type": "html",
                "id": self.card_id,
                "options": {"attribute": self.html_attribute},
            },
        )
        mutable_step.add_decorator(
            _pyinstrument_profile,
            deco_kwargs={
                "html_attribute": self.html_attribute,
                "interval": self.interval,
            },
            duplicates=mutable_step.ERROR,
        )
