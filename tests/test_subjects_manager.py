from click.testing import CliRunner

from connecticity.managers.subjects.query_subjects import main


def test_main():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["/home/groot/Projects/PhD/connectomeplasticity/data/subjects/raw"],
    )
    assert result.output.startswith("Found")
