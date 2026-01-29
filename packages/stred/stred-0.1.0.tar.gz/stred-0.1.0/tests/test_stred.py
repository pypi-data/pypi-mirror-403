from click.testing import CliRunner
from stred.cli import main as stred_main


def invoke_cli(args: list[str], lines: list[str]):
    runner = CliRunner()
    result = runner.invoke(stred_main, args=args, input="\n".join(lines))
    assert result.exit_code == 0
    return result.output.splitlines()


def test_search_without_replacement_prints_output_unaltered():
    assert invoke_cli(
        ["FOO"],
        ["This is a FOO line", "This is not a match"],
    ) == ["This is a FOO line", "This is not a match"]


def test_filter_stream():
    assert invoke_cli(
        ["-g", "FOO"],
        ["This is a FOO line", "This is not a match"],
    ) == ["This is a FOO line"]


def test_filter_stream_case_insensitive():
    assert invoke_cli(
        ["-g", "-i", "FOO"],
        ["This is a FOO line", "This is a foo line"],
    ) == ["This is a FOO line", "This is a foo line"]


def test_filter_stream_only_matches():
    text = ["This is a FOO line", "This is a BAR BAZ line"]
    args = ["-g", "-o", r"(FOO|BAR|BAZ)"]
    output = ["FOO", "BAR", "BAZ"]
    assert invoke_cli(args, text) == output


def test_single_replacement():
    assert invoke_cli(
        ["FOO", "BAR"],
        ["This is a FOO line", "This is not a match"],
    ) == ["This is a BAR line", "This is not a match"]


def test_single_replacement_and_filter():
    assert invoke_cli(
        ["-g", "FOO", "BAR"],
        ["This is a FOO line", "This is not a match"],
    ) == ["This is a BAR line"]


def test_multi_replacement():
    assert invoke_cli(
        ["FOO", "BAR"],
        ["Hello FOO and FOO or FOO"],
    ) == ["Hello BAR and BAR or BAR"]


def test_output_only_matching():
    assert invoke_cli(
        [r"FOO\{(?P<flag>.*?)\}", r"Flag: \g<flag>", "--only-matching"],
        [
            "Hello FOO{flag1} and FOO{flag2}",
            "This is FOO{flag3}!",
            "This is not a match",
            "More noise",
            "FOO{flag4} at the end",
        ],
    ) == ["Flag: flag1", "Flag: flag2", "Flag: flag3", "Flag: flag4"]


def test_simple_replacement_jinja():
    assert invoke_cli(
        ["(?P<name>FOO)", "[{{ name }}]", "--jinja"],
        ["This is a FOO line", "This is not a match"],
    ) == ["This is a [FOO] line", "This is not a match"]


def test_simple_replacement_and_filter_jinja():
    assert invoke_cli(
        ["(?P<name>FOO)", "[{{ name }}]", "--jinja", "-g"],
        ["This is a FOO line", "This is not a match"],
    ) == ["This is a [FOO] line"]


def test_replacement_with_numeric_groups():
    text = [
        "This is http://host1/path1 an example http://host2/path2",
        "Last one: http://host3/path3",
    ]
    args = [r"http://([^/]+)/([^ ]*)", r"[h=\g<1>;p=\g<2>]", "-o"]
    output = ["[h=host1;p=path1]", "[h=host2;p=path2]", "[h=host3;p=path3]"]
    assert invoke_cli(args, text) == output


def test_replacement_with_named_groups():
    text = [
        "This is http://host1/path1 an example http://host2/path2",
        "Last one: http://host3/path3",
    ]
    args = [
        r"http://(?P<host>[^/]+)/(?P<path>[^ ]*)",
        r"[h=\g<host>;p=\g<path>]",
        "--only-matching",
    ]
    output = ["[h=host1;p=path1]", "[h=host2;p=path2]", "[h=host3;p=path3]"]
    assert invoke_cli(args, text) == output


def test_replacement_with_named_groups_jinja():
    text = [
        "This is http://host1/path1 an example http://host2/path2",
        "Last one: http://host3/path3",
    ]
    args = [
        r"http://(?P<host>[^/]+)/(?P<path>[^ ]*)",
        r"[h={{ host }};p={{ path }}]",
        "--only-matching",
        "--jinja",
    ]
    output = ["[h=host1;p=path1]", "[h=host2;p=path2]", "[h=host3;p=path3]"]
    assert invoke_cli(args, text) == output


def test_construct_urls_with_jinja():
    text = [
        "Hello there, visit http://example.com/some/path or http://example.com/other?id=123",
        "Another good one is http://example.com?foo=1&bar=2",
    ]
    args = [
        r"(?P<url>http://[^ '\"]+)",
        r"http://tracking.example.com?url={{ url | urlencode }}",
        "--only-matching",
        "--jinja",
    ]
    output = [
        "http://tracking.example.com?url=http%3A//example.com/some/path",
        "http://tracking.example.com?url=http%3A//example.com/other%3Fid%3D123",
        "http://tracking.example.com?url=http%3A//example.com%3Ffoo%3D1%26bar%3D2",
    ]
    assert invoke_cli(args, text) == output
