from click.testing import CliRunner
from aiida_gulp.cmndline.potentials import potentials


def test_list_potentials():
    runner = CliRunner()
    result = runner.invoke(potentials, ["list"])
    assert result.exit_code == 0
    assert "lj" in str(result.output)
