import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from wafer_core.rollouts.dtypes import Endpoint, EvalConfig, Message, Metric, Score
from wafer_core.rollouts.evaluation import evaluate
from wafer_core.rollouts.training.types import Sample, Status


def _dataset(n: int) -> Iterator[dict]:
    for i in range(n):
        yield {"i": i}


@pytest.mark.trio
async def test_interrupt_uses_streamed_samples_for_partial_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_dir = tmp_path / "out"
    (output_dir / "samples").mkdir(parents=True, exist_ok=True)

    # Simulate samples that were already streamed to disk even though the eval loop
    # is about to be interrupted before returning in-memory results.
    for i in range(2):
        s = Sample(
            id=f"sample_{i:04d}",
            status=Status.COMPLETED,
            metadata={"status": "success"},
            score=Score(metrics=(Metric("ok", 1.0, weight=1.0),)),
        )
        (output_dir / "samples" / f"{s.id}.json").write_text(json.dumps(s.to_dict(), indent=2))

    async def _interrupting_batch(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("wafer_core.rollouts.evaluation._evaluate_batch", _interrupting_batch)

    def _no_upload(_path: Path) -> None:
        return None

    monkeypatch.setattr(
        "wafer_core.rollouts.upload.upload_results_to_supabase", _no_upload, raising=False
    )

    config = EvalConfig(
        endpoint=Endpoint(provider="openai", model="dummy", api_base="", api_key="dummy"),
        score_fn=lambda _sample: Score(metrics=(Metric("ok", 1.0, weight=1.0),)),
        prepare_messages=lambda _row: [Message(role="user", content="hi")],
        max_samples=2,
        max_concurrent=2,
        output_dir=output_dir,
        eval_name="interrupt_test",
        verbose=False,
        show_progress=False,
    )

    with pytest.raises(SystemExit) as ex:
        await evaluate(_dataset(2), config)
    assert ex.value.code == 130

    report = json.loads((output_dir / "report.json").read_text())
    assert report["interrupted"] is True
    assert report["completed_samples"] == 2
    assert set(report["sample_ids"]) == {"sample_0000", "sample_0001"}
