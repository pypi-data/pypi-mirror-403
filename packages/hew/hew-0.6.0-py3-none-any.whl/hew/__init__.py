import argparse
import datetime
import json
import logging
import magic
import os
import shutil
import threading
import warnings

from concurrent.futures import ThreadPoolExecutor
from contextlib import chdir
from functools import partial
from git import Commit, Repo, TagReference
from packaging.version import parse
from pathlib import Path
from typing import Callable, List, Optional, NamedTuple, Union

# We're aware of version compatability warnings, but they shouldn't
# be a problem:
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        import pandoc
        from pandoc.types import BulletList, Data, Header, Meta, MetaBool, Pandoc, Str
        pandoc_available = shutil.which("pandoc") is not None
    except Exception:
        # We handle this at the application level
        pandoc_available = False

try:
    import frontmatter
    frontmatter_available = True
except Exception:
    # We handle this at the application level
    frontmatter_available = False


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


COMPILE_ACTION = "compile"
CHANGELOG_ACTION = "changelog"
ACTION_DEFAULT = COMPILE_ACTION

class ChangelogError(Exception):
    def __init__(self, message: str, path: Path):
        super().__init__(message)
        self.message = message
        self.path = path


class FakeCommit(NamedTuple):
    committed_date: int


class FakeTag(NamedTuple):
    name: str
    commit: FakeCommit


class Change(NamedTuple):
    """A lightweight structure to pass around changelogs that's less
    brittle than a plain dict:

    """

    tag: TagReference | FakeTag
    component: Optional[str]
    category: str
    document: object
    notify: bool


def serialize_changelog(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()

    if isinstance(obj, Path):
        return obj.name

    # In some cases a user may not define an output format in which
    # case we need to define the behavior when we hit a pandoc
    # document.
    if pandoc_available and isinstance(obj, Data):
        return json.loads(pandoc.write(obj, format="json"))

    raise TypeError("Type %s not serializable" % type(obj))


class Hewer:
    """Class for running `hew` across a repository to collect
    changelogs into structured data.

    Attributes:

    project_root (Path): Path to the root of the repository with
    tracked changelogs.

    repo (Repository): GitPython Repository for the project_root.

    prerelease (bool): Whether to consider compilation operatiosn to
    occur in a prerelease environment.

    component_map (dict): Map of component names to alternative
    strings. This permits, for example, to remap a discovered
    component named something like "backend_api_service" to "server" or
    "API".

    skip_predicates (Callable): Collection of functions that will be
    given a `Change` type and dictate whether or not it should be
    excluded from matching a given tag.

    unreleased_tag_name (str): What tag name to file changes
    under that as yet still have no containing tag.

    changelog_dir_name (str): Name that will be considered the
    authoritative parent directory for considered changelogs.

    """

    def __init__(
            self,
            project_root: Path,
            prerelease: bool,
            component_map: dict[str, str],
            skip_predicates: list[Callable[[Change], bool]],
            unreleased_tag_name: str = "unreleased",
            changelog_dir_name: str = "changelogs.d"
    ) -> None:
        self.project_root = project_root.absolute()
        self.repo = Repo(self.project_root)
        self.prerelease = prerelease
        self.component_map = component_map
        self.skip_predicates = skip_predicates
        self.unreleased_tag_name = unreleased_tag_name
        self.changelog_dir_name = changelog_dir_name

        self._git_lock = threading.Lock()

    def find_commit(self, item: str, commit: Commit) -> List[Commit]:
        """Given a path name, our repo, and a candidate commit, return a
        list of commits that we should consider based up whether that
        commit has introduced the `item` in its commit diff. Recursive in
        the case that we encounter a _renamed_ file and need to follow its
        parents to find the commit that originally introduced the item.
        """
        for parent in commit.parents:
            for diff in parent.diff(commit):
                # If this commit included the filename we’re interested
                # in,
                if item.endswith(diff.b_path):
                    # and it was added in this commit,
                    if diff.new_file:
                        # Then we want to include it as a candidate.
                        return [commit]
                    # Otherwise, if this commit _renamed_ the file, then
                    # backtrack to the old filename to continue searching
                    # history.
                    elif diff.renamed:
                        r = []
                        for parent_commit in self.repo.iter_commits(
                            "--all", paths=diff.a_path
                        ):
                            r.extend(
                                self.find_commit(
                                    str(Path(diff.a_path)), parent_commit
                                )
                            )

                        # If we found _no parents_ that added the renamed
                        # file, then the only possibility is that it was
                        # squashed or otherwise scrubbed from history, so
                        # we can only infer that the commit in question -
                        # and not any parents - is the birth of the
                        # changelog.
                        return r or [commit]

        # Otherwise, we didn’t find any commits that introduced or
        # birthed the queried file..
        return []

    def process_changelog_item(
        self,
        item: Path,
        changelog: dict,
        component: Optional[str] = None,
        category: Optional[str] = None,
        strict: bool = False,
    ) -> Union[Change, None]:
        """Within the given repo and tag collection, determine if item
        fits in the changelog. An optional component and category may be
        passed here and used as defaults if they don't appear in the
        document metadata (which is usually considered the normal case)

        Returns a `Change` on success or `None` if the changelog item
        either isn't within the tag timeline or is missing crucial
        fields.

        """
        meta = {}
        if pandoc_available:
            meta_block, document = pandoc.read(
                file=str(item.absolute()), options=["--standalone"]
            )
            meta = meta_block[0]
        elif frontmatter_available:
            meta, document = frontmatter.parse(item.read_text())
        else:
            document = item.read_text()

        # Defaults
        change_tag = None
        notify = False

        def extract(value):
            if pandoc_available:
                if isinstance(value, MetaBool):
                    return value._args[0]
                else:
                    return pandoc.write(value).strip()
            else:
                return value

        # Honor specific metadata keys
        for k, raw_value in meta.items():
            match k:
                case "category":
                    category = extract(raw_value)
                case "component":
                    component = extract(raw_value)
                case "version":
                    version = extract(raw_value)
                    if version in changelog:
                        change_tag = changelog.get(version)
                    else:
                        raise ChangelogError(f"'{version}' not in changelog", item)
                case "notify":
                    notify = extract(raw_value)
                case "draft":
                    if extract(raw_value):
                        # This change is marked as a draft and should be
                        # skipped.
                        return None
                case _:
                    if strict:
                        raise ChangelogError(
                            f"Unexpected changelog metadata: {k}", item
                        )

        # If the source document didn’t specify a version,
        # derive it from git itself.
        #
        # This is the central "magic" part that hew provides; implicit
        # discovery of the right tag based on git ancestry.
        if not change_tag:
            # Find _all_ commits that affected this changelog item's
            # _current_ filename:
            all_commits = self.repo.iter_commits("--all", paths=item)
            # Prepare a new list with only the commits we're interested
            # in:
            commits = []

            # Populate the list of commits by those that actually
            # introduced the file that we're processing:
            for commit in all_commits:
                with self._git_lock:
                    if candidate_commits := self.find_commit(str(item), commit):
                        commits.extend(candidate_commits)

            # After assembling commit candidates, we now need to
            # accumulate tags that include those that commits.
            candidates = []

            # If there are commits associated with this file, try and find
            # the tag that it falls within. Crucial that we order the
            # commits by their committed date to ensure that we pluck
            # the commit that first introduced the changelog so that
            # version attribution is correct.
            with self._git_lock:
                for commit in sorted(commits, key=lambda c: c.committed_date):
                    # Rely on the builtin `tag --contains` to find our
                    # most recent containing tag:
                        for tag in self.repo.git.tag(
                            "--sort",
                            "taggerdate",
                            "--contains",
                            str(commit),
                        ).split("\n"):
                            # The found tag needs to match our naming scheme and
                            # also defined in the changelog dictionary - once we
                            # find the first one (sorted by date), we can break
                            # for this `commit` (but continue to check the other
                            # commits before sorting their final dates)
                            if (
                                self.valid_tag(
                                    tag,
                                    Change(
                                        FakeTag(tag, FakeCommit(0)),
                                        component,
                                        category,
                                        document,
                                        notify,
                                    ),
                                )
                                and tag in changelog
                            ):
                                candidates.append(changelog[tag])
                                # We've found a tag that works with this
                                # commit, but check other commits as well for
                                # potential other ancestries.
                                break

                # If we can find the earliest tag, use that as our change tag.
                if latest_tag := next(
                    iter(sorted(candidates, key=lambda x: x.commit.committed_date)),
                    None,
                ):
                    change_tag = latest_tag

        if not change_tag and self.prerelease:
            # Without any commits, it means that this file isn’t
            # within git history yet - but if we're in prerelease
            # mode, that's fine, give it the unreleased tag name.
            change_tag = FakeTag(self.unreleased_tag_name, FakeCommit(0))


        if change_tag and category:
            return Change(change_tag, component, category, document, notify)
        else:
            message = " ".join(
                [
                    "Missing required fields for changelog item",
                    f"{item.name}:",
                    f"change_tag:{change_tag}",
                    f"category:{category}.",
                ]
            )
            if strict:
                raise ChangelogError(message, item)
            else:
                logger.warn(message)
                return None


    def valid_tag(
        self,
        tag_name: str,
        change: Optional[Change] = None,
    ) -> bool:
        """Predicate to determine whether a given tag string should be
        included in the changelog.

        """
        # Some skip criteria includes a potential component name. If
        # we're querying just whether a tag is valid but do not have a
        # concrete change to consult, fake one that we can test.
        if not change:
            change = Change(
                FakeTag(tag_name, FakeCommit(0)),
                None,
                "",
                None,
                False
            )

        # The packaging.version parse function will raise on malformed
        # tags.
        try:
            return bool(
                tag_name
                and (tag := parse(tag_name))
                and not (not self.prerelease and tag.is_prerelease)
                and not any([predicate(change) for predicate in self.skip_predicates])
            )
        except Exception:
            return False


    def tags(
        self,
        reverse: bool = False,
    ) -> list[Union[FakeTag, TagReference]]:
        """Collect all tags that match the given predicates for the
        repository.

        """
        return sorted(
            # Note the check for t.tag here, which indicates an annotated
            # tag. Otherwise we run into lightweight tag annoyances.
            [
                tag
                for tag in self.repo.tags
                if self.valid_tag(tag.name)
                and tag.tag
            ],
            key=lambda t: t.commit.committed_date,
            reverse=reverse,
        )



    def compile(
        self,
        include_paths: bool = False,
        strict: bool = False,
        fmts: List[str] = [],
    ) -> list[dict]:
        """Given optional desired Pandoc output formats and other options,
        return a list of the form:

        >>> [
        >>>   {
        >>>     "version": "<tag>",
        >>>     "date": "<ISO8661 date>",
        >>>     "changes": {
        >>>       "<component>": {
        >>>         "<kind>": [
        >>>           {
        >>>             "meta": { ... },
        >>>             ( "content": <Pandoc types>
        >>>             | { "format": "<rendered format>", ... }
        >>>             )
        >>>           }, ...
        >>>         ]
        >>>       }, ...
        >>>     }
        >>>   }, ...
        >>> ]

        `include_paths` will append the `Path` value associated with the
        changelog content to the changelog's `meta` dictionary.

        `strict` when set will bail out parsing changelogs if unexpected or
        unrecognized document metadata is encountered.

        `fmts` may be passed a list of trings, in which case the
        changelog entry will be rendered by passing the given format
        as an output format to Pandoc, or

        Excluding any members from the `fmts` list will return the
        changelog as richer Python types (datetime objects, Pandoc
        types). Using `fmts` makes the return value suitable for
        serialization into formats like JSON or YAML.

        Each changelog item can either define a field manually or let it
        be inferred by the full path to the file. Markdown YAML front matter
        is the simplest example of using document metadata to change these
        fields.

        - An individual changelog entry will be associated with nearest
        tag created following the commit where the changelog file was
        created. This may be overridden via the `version` field.

        - The component for a change - for example, "frontend" or "backend" -
        will be derived from the name of the directory containing the
        changelog directory. This may be overridden via the `component`
        field.

        - The kind for the change, such as "fix" or "feature", will be
        derived from the name of the directory that a changelog file is
        an immediate child of - for example,
        `frontend/${changelog_dir}/fixes/example.md` will be associated
        with `fixes`. This may be overridden via the `category` field.

        - The optional `notify` field signals to downstream consumers that
        the indicated change should be highlighted and brought to user
        attention. This is up to those downstream consumers to
        implement.

        """

        # GitPython behaves a little strangely when you call into `git`
        # CLI outside of the repository working directory, so we handle
        # that here for it:
        with chdir(self.project_root):
            return self._compile(include_paths, strict, fmts)

    def _compile(
        self,
        include_paths: bool,
        strict: bool,
        fmts: List[str],
    ) -> list[dict]:
        """
        Inner compilation function; wrapped by a chdir to ensure that
        GitPython behaves itself
        """

        # Accumulate all the candidate tags found in the repository:
        tags = self.tags()

        # In pre-release scenarios, we often want to include a
        # headline for changes that have been written but not included
        # in any releases yet.
        if self.prerelease:
            tags.append(FakeTag(self.unreleased_tag_name, FakeCommit(0)))

        # Short-circuit an empty log:
        if len(tags) == 0:
            return []

        # Our main return value - we leverage defaultdict to avoid a lot
        # of "not in" predicate noise later.
        changelog = {t: {} for t in tags}
        errors: list[str] = []

        # We'll run concurrently, collect the results here:
        results = []

        parent: str
        files: list[str]
        # I've run experiments on this and although it improves
        # performance slightly, it is not ideal.
        #
        # GitPython isn't threadsafe: 
        with ThreadPoolExecutor() as executor:
            # Deeply traverse the repository:
            for parent, _, files in os.walk(self.project_root):
                # We’re permissive about structure as long as the file lives
                # somewhere underneath a changelog directory.
                if self.changelog_dir_name in (
                    [Path(p).name for p in Path(parent).parents] + [Path(parent).name]
                ):
                    # Iterate through each file - we don’t care about the
                    # second element of the walk() tuple because walk() will
                    # eventually take us there anyway.
                    change: Path
                    for change in [Path(parent) / f for f in files]:
                        # Avoid unexpected types.
                        if not change.is_file():
                            continue

                        # Run this test, otherwise we may run into very
                        # annoying parsing behavior against files like
                        # images.
                        if "text" not in magic.from_file(change):
                            continue

                        component, kind = None, None

                        # If we’re within a changelog dir but the parent is not
                        # the actual changelog dir, use that as the category.
                        if Path(parent).name != self.changelog_dir_name:
                            kind = (
                                # Clean up the filename if it has some
                                # filename safeguards around it.
                                Path(parent).name.replace("-", " ").replace("_", " ")
                            )

                        # Find the containing changelog dir, and...
                        for change_dir in [
                            x
                            for x in (list(Path(parent).parents) + [Path(parent)])
                            if x.name == self.changelog_dir_name
                        ]:
                            # ...if its containing directory isn’t the given root,
                            if change_dir.parent != self.project_root:
                                # Use that as the component name with optional
                                # overriding via the component map.
                                component = self.component_map.get(
                                    change_dir.parent.name, change_dir.parent.name
                                )

                        results.append(executor.submit(
                            self.process_changelog_item,
                            change,
                            {t.name: t for t in changelog.keys()},
                            component,
                            kind,
                            strict,
                        ))
                        if len(results) % 100 == 0:
                            logger.debug(f"queued {len(results)} changelogs...")

            # conclusion of repository walk()
            result_count = len(results)
            logger.info(f"collected {result_count} changelogs for processing")

            progress = {int(result_count * 0.25), int(result_count * 0.5), int(result_count * 0.75), result_count}

            for index, future in enumerate(results, 1):
                if index in progress:
                    logger.debug(f"handled {index} changelogs...")
                try:
                    item = future.result()
                except ChangelogError as ch:
                    errors.append(f"{ch.path.name}: {ch.message}")
                    continue

                # A None indicates a non-strict failure
                if item:
                    # Catch the unexpected case wherein a tag wasn’t
                    # actually found in git history (for example, a bad
                    # `version` field)
                    entry = {
                        "meta": {}
                        # If desired, include the notify value as
                        # part of the entry’s meta dictionary:
                            | (
                                {"notify": item.notify}
                                if item.notify
                                else {}
                            )
                            # Some callers need to know about what the
                            # source path for the changelog is, so
                            # honor that parameter here:
                            | ({"path": change} if include_paths else {}),
                            # Add the raw Pandoc structure if no
                            # formats have been specified
                            "content": (
                                item.document
                                if not pandoc_available or not fmts
                                else {
                                        # Otherwise, create a nested
                                        # dictionary of format labels and
                                        # their rendered forms:
                                    f: pandoc.write(item.document, format=f)
                                    for f in fmts
                                }
                            ),
                    }
                    if item.component:
                        if item.component not in changelog[item.tag]:
                            changelog[item.tag][item.component] = {}
                        elif not isinstance(changelog[item.tag][item.component], dict):
                            raise ValueError(
                                f"encountered changelog {change} with a "
                                f"component ({item.component}) in a changelog "
                                "without components. "
                                "Please either remove the component of "
                                f"{change} or write a changelog comprised of components."
                            )

                        if item.category not in changelog[item.tag][item.component]:
                            changelog[item.tag][item.component][item.category] = []

                        changelog[item.tag][item.component][item.category].append(entry)
                    else:
                        if item.category not in changelog[item.tag]:
                            changelog[item.tag][item.category] = []
                        elif not isinstance(changelog[item.tag][item.category], list):
                            raise ValueError(
                                f"encountered changelog {change} without a "
                                "component in a changelog with components "
                                f"(found `{item}`). Please either designate "
                                "the component of {change} or write a changelog "
                                "without components."
                            )
                        changelog[item.tag][item.category].append(entry)


        if strict and errors:
            raise ValueError(
                "Encountered malformed changelogs:\n" + "\n".join(errors)
            )
        else:
            # With an assembled changelog, we now need to return it in
            # ordered form.
            #
            # Re-use the `tags` we collected previously that are already
            # sorted by _commit date order_ and pull out the changes
            # associated with those tags from the changelog dictionary.
            return list(
                [
                    {
                        "version": version.name,
                        "changes": changelog[version],
                    }
                    | (
                        # If there’s a date for this tag, return it as a
                        # full Python object when we aren’t formatting
                        # changelogs, otherwise, dump it as an
                        # ISO-formatted string.
                        {"date": ts}
                        if hasattr(version, "tag")
                        and version.tag is not None
                        and (
                            ts := datetime.datetime.fromtimestamp(
                                version.tag.tagged_date, datetime.timezone.utc
                            )
                        )
                        else {}
                    )
                    for version in tags
                ]
            )

def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "A tool to compile repository changelogs into release "
            "notes and other forms of documentation."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "action",
        help=f"What action to take. Defaults to [{ACTION_DEFAULT}]",
        choices=[COMPILE_ACTION, CHANGELOG_ACTION],
        nargs="?",
        default=ACTION_DEFAULT,
    )
    parser.add_argument(
        dest="project_root",
        default=os.environ.get("PWD"),
        help="Path to target repository.",
    )
    parser.add_argument(
        "-p",
        "--prerelease",
        dest="prerelease",
        action="store_true",
        help="Whether to include pre-release tags",
    )
    parser.add_argument(
        "-m",
        "--component-map",
        metavar="DIRECTORY_NAME=STRING",
        nargs="*",
        dest="component_map",
        default=[],
        help="List component directory names mapped to alternative strings",
    )
    parser.add_argument(
        "--skip",
        metavar="[tag=value][,][component=value]",
        nargs="*",
        dest="skip",
        default=[],
        help="Conditions for which tags or changes may be skipped",
    )
    # Todo: maybe handle skip predicates a fancy way?
    parser.add_argument(
        "-u",
        "--unreleased-name",
        dest="unreleased_name",
        default="unreleased",
        help="Name to give to unreleased changelogs without a tag.",
    )
    parser.add_argument(
        "-c",
        "--changelog-directory",
        dest="changelog_dir_name",
        default="changelogs.d",
        help="Directory name that contains targeted changelogs.",
    )

    # Options specific to the compile call
    parser.add_argument(
        "-i",
        "--include-paths",
        dest="include_paths",
        action="store_true",
        help="Whether to include changelog origin paths in parsed results",
    )
    parser.add_argument(
        "-s",
        "--strict",
        dest="strict",
        action="store_true",
        help="Bail out and fail for invalid changelogs with missing metadata.",
    )
    if pandoc_available:
        parser.add_argument(
            "-f",
            "--formats",
            nargs="*",
            dest="formats",
            default=[],
            help="List of optional formats to transform parsed markup into.",
        )

    # Options relevant only to how the CLI behaves
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Whether to print debug-level output",
    )
    parser.add_argument(
        "--pretty",
        dest="pretty",
        action="store_true",
        help="Whether to print JSON output in human-readable format",
    )

    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARN)

    if args.action == "changelog" and not args.formats:
        default_format = "markdown_github"
        logger.warn(f"no changelog format specified, using `{default_format}`")
        args.formats.append(default_format)

    def skip_predicate(criterion, change):
        """Run a check for a CLI skip against a change candidate or
        tag:

        """
        match criterion.partition("="):
            case ("tag", _, value):
                return change.tag.name == value
            case ("component", _, value):
                return change.component == value
            case _:
                return  False

    def skip_predicates(criteria, change):
        """Accept a CLI skip string and check whether it satisfies
        all of its predicates.

        """
        return all(
            skip_predicate(criterion, change)
            for criterion in criteria.split(",")
        )

    cli = Hewer(
        Path(args.project_root),
        args.prerelease,
        # Re-form our CLI arguments into a viable component
        # mapping (that is, a dict[str, str])
        {
            cs[0]: cs[1]
            for c in args.component_map
            if (cs := c.split("=")) and len(cs) == 2
        },
        # Re-form the simple CLI form of skip criteria to the
        # internal representation of a list of callables:
        [
            partial(skip_predicates, skip)
            for skip in args.skip
        ],
        args.unreleased_name,
        args.changelog_dir_name,
    )
    changelog = cli.compile(
        args.include_paths,
        args.strict,
        args.formats if hasattr(args, "formats") and not args.action == "changelog" else []
    )

    match args.action:
        case a if a == COMPILE_ACTION:
            print(json.dumps(
                changelog,
                default=serialize_changelog,
                indent=4 if args.pretty else None,
            ))
        case a if a == CHANGELOG_ACTION:
            document = [Header(1, ("", [], []), [Str("Release Notes")])]
            for release in reversed(changelog):
                document.append(Header(2, ("", [], []), [Str(release['version'])]))
                for nested, items in release['changes'].items():
                    document.append(Header(3, ("", [], []), [Str(nested)]))
                    if isinstance(items, list):
                        # We're not component-based
                        document.append(BulletList([i['content'] for i in items]))
                    else:
                        # Recurse once more
                        for category, changes in items.items():
                            document.append(Header(4, ("", [], []), [Str(category)]))
                            document.append(BulletList([c['content'] for c in changes]))

            for fmt in args.formats:
                print(pandoc.write(Pandoc(Meta({}), document), format=fmt))
