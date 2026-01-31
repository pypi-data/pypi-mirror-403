import argparse
from datetime import datetime
import os
from pathlib import Path
from m3cli.docs.commons import create_logger
from m3cli.docs.commons.commands_table import add_table_md
from m3cli.docs.cli_to_md import generate_documentation
from m3cli.docs.commons.m3_preprocessor import style_headers, merge_mds
from m3cli.docs.md_to_docx import convert_md_to_docx
from m3cli.docs.commons.title_page_docx import add_page_to_docx
from m3cli.docs.commons.last_page import add_cli_last_page
from m3cli.docs.commons.page_numbers import (
    add_page_numbers,
    get_available_formats,
    get_available_alignments,
)
from m3cli.docs.commons.page_header import add_page_header

_LOG = create_logger()


def generate_docx(
        tool_name: str,
        commands_def_path: str,
        result_docx_path: str | None = None,
        changelog_url: str | None = None,
        changelog_path: str | None = None,
        cli_version: str | None = None,
        no_last_page: bool = False,
        no_page_numbers: bool = False,
        page_number_format: str = 'simple',
        page_number_align: str = 'right',
        page_number_custom: str | None = None,
        header_text: str | None = None,
        header_align: str = 'center',
        no_header_skip_first: bool = False,
) -> None:
    tmp_md_path = os.path.join(result_docx_path, f'{tool_name}.md')
    _LOG.debug(f"Temporary markdown path set: {tmp_md_path}")
    generate_documentation(
        tool_name,
        commands_def_path,
        result_docx_path,
    )
    result_docx_file = \
        os.path.join(result_docx_path, f'{tool_name}_reference_guide.docx')
    _LOG.debug(f"Result DOCX path set: {result_docx_file}")

    style_headers(tmp_md_path, tmp_md_path)
    if not add_table_md(tmp_md_path, tmp_md_path):
        _LOG.warning("Failed to parse the MD file or no commands found.")

    merge_mds(
        [os.path.join(Path(__file__).parent, "commons/m3_intro.md"),
         tmp_md_path],
        tmp_md_path,
        delimiter='\n \n\n',
    )

    current_date = datetime.now()
    current_month_year = current_date.strftime('%B %Y')

    try:
        convert_md_to_docx(md_file=tmp_md_path, docx_file=result_docx_file)
        _LOG.info(
            f"Markdown converted to DOCX successfully at: {result_docx_file}"
        )
    except Exception as e:
        _LOG.error(f"Failed to convert markdown to DOCX: {e}")
        raise

    try:
        add_page_to_docx(
            docx_path=result_docx_file,
            title_text='M3 CLI Tool\nReference Guide',
            secondary_title_text='M3CLI-02',
            date_text=current_month_year,
            version_text='Version 1.0',
        )
    except Exception as e:
        _LOG.error(f"Failed to add title page to DOCX: {e}")
        raise

    # Add last page with changelog and version info
    if not no_last_page:
        _LOG.info("Adding last page with version history...")
        try:
            add_cli_last_page(
                docx_path=result_docx_file,
                cli_name=tool_name,
                cli_version=cli_version,
                changelog_url=changelog_url,
                changelog_path=changelog_path,
                auto_detect_version=True,
            )
            _LOG.info("Last page added successfully")
        except Exception as e:
            _LOG.error(f"Failed to add last page: {e}")
            raise

    # Add page header if specified
    if header_text:
        _LOG.info(
            f"Adding page header (text: '{header_text}', "
            f"align: {header_align}, skip_first: {not no_header_skip_first})..."
        )
        try:
            add_page_header(
                docx_path=result_docx_file,
                header_text=header_text,
                skip_first_page=not no_header_skip_first,
                alignment=header_align,
            )
            _LOG.info("Page header added successfully")
        except Exception as e:
            _LOG.error(f"Failed to add page header: {e}")
            raise

    # Add page numbers (skip title page)
    if not no_page_numbers:
        _LOG.info(
            f"Adding page numbers (format: {page_number_format}, "
            f"align: {page_number_align})..."
        )
        try:
            add_page_numbers(
                docx_path=result_docx_file,
                skip_first_page=True,
                alignment=page_number_align,
                page_number_format=page_number_format,
                custom_format=page_number_custom,
            )
            _LOG.info("Page numbers added successfully")
        except Exception as e:
            _LOG.error(f"Failed to add page numbers: {e}")
            raise


# Get available options for help text
available_formats = get_available_formats()
available_alignments = get_available_alignments()

format_help = 'Page number format. Options: ' + ', '.join(
    [f"'{k}' ({v})" for k, v in available_formats.items()]
)
align_help = 'Page number alignment. Options: ' + ', '.join(
    available_alignments)

parser = argparse.ArgumentParser(
    description='Generate M3 CLI Reference Guide in DOCX format',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=f"""
        Page Number Format Examples:
          simple        -> 1, 2, 3...
          page_x        -> Page 1, Page 2...
          page_x_of_y   -> Page 1 of 10, Page 2 of 10...
          x_of_y        -> 1 of 10, 2 of 10...
          dash          -> - 1 -, - 2 -...
          dash_total    -> - 1 of 10 -, - 2 of 10 -...
        
        Custom format uses {{page}} and {{total}} placeholders:
          --page-number-custom "[ {{page}} / {{total}} ]"  -> [ 1 / 10 ]

        Page Header Examples:
          --header-text "M3 CLI – Reference Guide"
          --header-text "M3 CLI – Reference Guide" --header-align right
          --header-text "M3 CLI – Reference Guide" --no-header-skip-first
    """,
)
parser.add_argument(
    '-name', '--tool_name', type=str, required=True,
    help='The name of the tool for which the doc will be generated'
)
parser.add_argument(
    '-cmd_path', '--commands_def_path', type=str, required=True,
    help='The path to the file "commands_def.json"'
)
parser.add_argument(
    '-res_path', '--result_docx_path', type=str,
    help='The path to the result file DOCX file'
)
parser.add_argument(
    '--changelog-url', type=str, dest='changelog_url',
    help='URL to the changelog (e.g., GitHub CHANGELOG.md URL)'
)
parser.add_argument(
    '--changelog-path', type=str, dest='changelog_path',
    help='Local path to the changelog file'
)
parser.add_argument(
    '--cli-version', type=str, dest='cli_version',
    help='CLI version string (auto-detected if not provided)'
)
parser.add_argument(
    '--no-last-page', action='store_true', dest='no_last_page',
    help='Skip adding the last page with version history'
)
parser.add_argument(
    '--no-page-numbers', action='store_true', dest='no_page_numbers',
    help='Skip adding page numbers'
)
parser.add_argument(
    '--page-number-format', type=str, dest='page_number_format',
    default='simple', choices=list(available_formats.keys()),
    help=format_help
)
parser.add_argument(
    '--page-number-align', type=str, dest='page_number_align',
    default='right', choices=available_alignments,
    help=align_help
)
parser.add_argument(
    '--page-number-custom', type=str, dest='page_number_custom',
    help='Custom page number format using {page} and {total} placeholders (overrides --page-number-format)'
)
# Page header arguments
parser.add_argument(
    '--header-text', type=str, dest='header_text',
    help='Text for page header (e.g., "M3 CLI – Reference Guide")'
)
parser.add_argument(
    '--header-align', type=str, dest='header_align',
    default='center', choices=['left', 'center', 'right'],
    help='Header text alignment (default: center)'
)
parser.add_argument(
    '--no-header-skip-first', action='store_true', dest='no_header_skip_first',
    help='Include header on first page (default: skip first page)'
)


def main():
    try:
        generate_docx(**vars(parser.parse_args()))
    except Exception as e:
        _LOG.exception(e)


if __name__ == '__main__':
    main()
