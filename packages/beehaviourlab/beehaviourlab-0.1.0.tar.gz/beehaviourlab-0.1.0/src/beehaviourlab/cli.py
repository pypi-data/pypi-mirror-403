import click

from .tracking import (
    batch_process,
    extract_flow_info,
    fix_ids,
    process_video,
    tracking_video_visualiser,
    yolo_predict_to_file,
)


@click.group()
def bee() -> None:
    """BEEhaviourLab command line interface."""


@bee.group()
def track() -> None:
    """Tracking-related commands."""


track.add_command(process_video.main, name="run-pipeline")
track.add_command(batch_process.main, name="batch-process")
track.add_command(yolo_predict_to_file.main, name="run-yolo")
track.add_command(fix_ids.main, name="fix-ids")
track.add_command(extract_flow_info.main, name="extract-flow")
track.add_command(tracking_video_visualiser.main, name="visualise-tracking")


if __name__ == "__main__":
    bee()
