import stouputils as stp
from beet.core.utils import JsonDict as JsonDict

def validate_config(pmc_config: dict[str, str]) -> str:
    """ Validate PlanetMinecraft configuration

\tArgs:
\t\tpmc_config (dict[str, str]): Configuration for the PlanetMinecraft project
\tReturns:
\t\tstr: Project url on PlanetMinecraft
\t"""
def convert_markdown_to_bbcode(markdown: str, verbose: bool = True) -> str:
    """ Convert markdown to bbcode for PlanetMinecraft

\tArgs:
\t\tmarkdown (str): Markdown text
\t\tverbose (bool): If True, print the conversion comparison

\tReturns:
\t\tstr: BBcode text

\tExamples:
\t\t>>> markdown_text = '''
\t\t... [![Discord](https://img.shields.io/discord/1216400498488377467?label=Discord&logo=discord)](https://discord.gg/anxzu6rA9F)
\t\t... ![Discord](https://img.shields.io/discord/1216400498488377467?label=Discord&logo=discord)
\t\t... ## Changelog
\t\t...
\t\t... ### Build System
\t\t... - 🚀 Bump version to v1.2.3 ([2111fd2](https://github.com/Stoupy51/LifeSteal/commit/2111fd2f390b80a3aab77a4e7bcbb24b93845e5a))
\t\t...
\t\t...
\t\t...
\t\t... ### Features
\t\t... - ✨ Added new configuration for dropping heart (non pvp) ([cde8749](https://github.com/Stoupy51/LifeSteal/commit/cde8749aa9e447302481f50b9887a0b3a846c7fe))
\t\t...
\t\t... - 🔧 Another feature with multiple newlines before
\t\t...
\t\t... **Full Changelog**: https://github.com/Stoupy51/LifeSteal/compare/v1.2.2...v1.2.3
\t\t... '''
\t\t>>> bbcode = convert_markdown_to_bbcode(markdown_text, verbose=False)
\t\t>>> print(bbcode.strip())
\t\t[url=https://discord.gg/anxzu6rA9F][img]https://img.shields.io/discord/1216400498488377467?label=Discord&logo=discord[/img][/url]
\t\t[img]https://img.shields.io/discord/1216400498488377467?label=Discord&logo=discord[/img]
\t\t[h2]Changelog[/h2][h4]Build System[/h4][list]
\t\t[*]🚀 Bump version to v1.2.3 ([url=https://github.com/Stoupy51/LifeSteal/commit/2111fd2f390b80a3aab77a4e7bcbb24b93845e5a]2111fd2[/url])[/*]
\t\t[/list][h4]Features[/h4][list]
\t\t[*]✨ Added new configuration for dropping heart (non pvp) ([url=https://github.com/Stoupy51/LifeSteal/commit/cde8749aa9e447302481f50b9887a0b3a846c7fe]cde8749[/url])[/*]
\t\t[*]🔧 Another feature with multiple newlines before[/*]
\t\t[/list]
\t\t[b]Full Changelog[/b]: [url]https://github.com/Stoupy51/LifeSteal/compare/v1.2.2...v1.2.3[/url]
\t"""
def upload_version(project_url: str, changelog: str) -> None:
    """ Upload new version by opening the project url with the browser

\tArgs:
\t\tproject_url\t\t(str):\tUrl of the project on PlanetMinecraft to open
\t\tchangelog\t\t(str):\tChangelog text
\t"""
@stp.handle_error
def upload_to_pmc(pmc_config: JsonDict, changelog: str = '') -> None:
    """ Upload the project to PlanetMinecraft using the configuration

\tDisclaimer:
\t\tThere is no API for PlanetMinecraft, so everything is done manually.
\tArgs:
\t\tpmc_config\t\t(dict):\t\tConfiguration for the PlanetMinecraft project
\t\tchangelog\t\t(str):\t\tChangelog text for the release
\t"""
