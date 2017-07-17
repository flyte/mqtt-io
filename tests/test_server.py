import uuid

import mock
import pytest
from pip.status_codes import SUCCESS

from pi_mqtt_gpio import server


@mock.patch("pkg_resources.WorkingSet")
def test_imr_no_attribute(mock_ws):
    """
    Should not bother looking up what's installed when there's no requirements.
    """
    module = object()
    server.install_missing_requirements(module)
    mock_ws.assert_not_called()


@mock.patch("pkg_resources.WorkingSet")
def test_imr_blank_list(mock_ws):
    """
    Should not bother looking up what's installed when there's no requirements.
    """
    module = mock.Mock()
    module.REQUIREMENTS = []
    server.install_missing_requirements(module)
    mock_ws.assert_not_called()


@mock.patch("pkg_resources.WorkingSet.find", return_value=None)
@mock.patch("pip.commands.install.InstallCommand.main", return_value=SUCCESS)
def test_imr_has_requirements(mock_pip, mock_find):
    """
    Should install all missing args.
    """
    module = mock.Mock()
    module.REQUIREMENTS = ["testreq1", "testreq2==1.2.3"]
    server.install_missing_requirements(module)
    args, _ = mock_pip.call_args
    assert args == (["testreq1", "testreq2==1.2.3"],)


@mock.patch("pkg_resources.WorkingSet.find", return_value=None)
def test_imr_bad_pkg_fails(mock_find):
    """
    Should raise exception when pkg installation fails.
    """
    module = mock.Mock()
    module.REQUIREMENTS = [str(uuid.uuid4())]
    with pytest.raises(server.CannotInstallModuleRequirements):
        server.install_missing_requirements(module)


def test_onfts_no_set():
    """
    Should raise a ValueError when there's no /set at the end of the topic.
    """
    with pytest.raises(ValueError):
        server.output_name_from_topic(
            "myprefix/output/myoutputname", "myprefix", "set")


def test_onfts_returns_output_name():
    """
    Should return the proper output name.
    """
    output_name = "myoutputname"
    ret = server.output_name_from_topic(
        "myprefix/output/%s/%s" % (output_name, server.SET_TOPIC),
        "myprefix",
        "set"
    )
    assert ret == output_name
