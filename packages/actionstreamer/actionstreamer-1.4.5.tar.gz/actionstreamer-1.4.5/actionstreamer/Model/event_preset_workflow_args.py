import json
from typing import List, Iterable, Any, Optional
from .event_args import EventArgs
from .workflow_preset import WorkflowPreset


class EventPresetWorkflowArgs(EventArgs):
    workflow_presets: List[WorkflowPreset]  # type hint only (no default list!)

    extra_fields: dict[str, Any]

    def __init__(self, workflow_presets: Optional[Iterable[WorkflowPreset]] = None, **kwargs: Any):
        # Always create a new list for each instance (safe)
        self.workflow_presets = list(workflow_presets) if workflow_presets else []

        # Store unknown fields like your other classes
        self.extra_fields = kwargs
        if kwargs:
            print(f"Extra fields: {kwargs}")

    def add(self, preset: WorkflowPreset):
        self.workflow_presets.append(preset)

    def to_dict(self):
        # Convert each WorkflowPreset to dict
        return [preset.to_dict() for preset in self.workflow_presets]

    def to_json(self):
        return json.dumps(self.to_dict())
