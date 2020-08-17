from unittest import mock, TestCase

from .. import unbound_ssh


####### Mocks and other helpers #######


class response:
    "web request body content and or JSON nominally decoded from body"

    def __init__(self, *, content_val="", json_val=None):
        self.content = content_val
        self._json = json_val

    def json(self):
        if self._json is None:
            raise ValueError("No json here")
        return self._json


class MockObj:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)


def patch_subprocess_run(returncode, **kwargs):
    return mock.patch("subprocess.run", return_value=MockObj(returncode=returncode, **kwargs))


####### TESTS #######


class TestLib(TestCase):

    # __init__ requires & accepts args, fails on missing

    def test01_init_requires_ssh_des(self):
        with self.assertRaises(TypeError):
            unbound_ssh.UnboundSsh()  # pylint: disable=E1125

    def test02_init_okay(self):
        self.assertTrue(unbound_ssh.UnboundSsh(ssh_des="nobody@nowhere.man"))

    def test03_init_with_alias_okay(self):
        self.assertTrue(unbound_ssh.UnboundSsh(ssh_des="nobody@nowhere.man", alias="example.com"))

    # local function unbound_command rejects invalid command

    def test13_unbound_command_bad_cmd_fails(self):
        with self.assertRaises(ValueError):
            unbound_ssh.unbound_command("bad", "fqdn", "acme_challenge")

    # end to end tests (up to calling out to ssh, of course)

    def test21_create_delete_dns_record_okay(self):
        "test create and delete with the ssh callout mocked"

        provider = unbound_ssh.UnboundSsh(ssh_des="nobody@nowhere.man")
        with patch_subprocess_run(0) as sub_run_mock:
            provider.create_dns_record("example.com", "a1b2c3d4e5f6g7h8i9j0")
            provider.delete_dns_record("example.com", "a1b2c3d4e5f6g7h8i9j0")
            self.assertTrue(sub_run_mock.call_count == 2)

    def test22_create_dns_record_fail(self):
        "only runs through create since the fail point is in the method both call"

        provider = unbound_ssh.UnboundSsh(ssh_des="nobody@nowhere.man")
        with patch_subprocess_run(42, args=None) as sub_run_mock:
            with self.assertRaises(RuntimeError):
                provider.create_dns_record("example.com", "a1b2c3d4e5f6g7h8i9j0")
            self.assertTrue(sub_run_mock.call_count == 1)
