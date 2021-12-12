from click.testing import CliRunner

from connectome_plasticity_project.managers.query_subjects import main


def test_main():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["/home/groot/Projects/PhD/connectomeplasticity/data/subjects/raw"],
    )
    assert result.output.startswith("Found")
