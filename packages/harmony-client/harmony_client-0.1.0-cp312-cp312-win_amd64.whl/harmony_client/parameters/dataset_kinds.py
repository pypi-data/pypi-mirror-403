from harmony_client.runtime.dto.DatasetSampleFormats import (
    DatasetMetricSample,
    DatasetPreferenceSample,
    DatasetPromptSample,
    DatasetSample,
    DtoBaseModel,
)


class DatasetKind:
    def __init__(
        self,
        kind: str,
        formats: list[type[DtoBaseModel]] = [
            DatasetPreferenceSample,
            DatasetMetricSample,
            DatasetSample,
            DatasetPromptSample,
        ],
    ):
        self.kind = kind
        self.formats = formats

    def parse(self, line: dict):
        for f in self.formats:
            try:
                return f.model_validate(line)
            except Exception:
                pass


class Prompt(DatasetKind):
    def __init__(self):
        super().__init__("prompts", [DatasetPromptSample])


class Preference(DatasetKind):
    def __init__(self):
        super().__init__("preference", [DatasetPreferenceSample])


class Completion(DatasetKind):
    def __init__(self):
        super().__init__("completions", [DatasetSample])


class Metric(DatasetKind):
    def __init__(self):
        super().__init__("feedbacks", [DatasetMetricSample])
