"""Phonexia grapheme to phoneme conversion client.

This module provides a grapheme to phoneme conversion client.
This client can be used to communicate with the grapheme to phoneme conversion server.
"""

import json
import logging
from enum import Enum
from typing import Annotated, Optional, TextIO

import grpc
import typer
from google.protobuf.json_format import MessageToDict
from phonexia.grpc.technologies.grapheme_to_phoneme_conversion.v1.grapheme_to_phoneme_conversion_pb2 import (
    ConvertRequest,
    ConvertResponse,
    ListAllowedGraphemesRequest,
    Pronunciation,
)
from phonexia.grpc.technologies.grapheme_to_phoneme_conversion.v1.grapheme_to_phoneme_conversion_pb2_grpc import (
    GraphemeToPhonemeConversionStub,
)


class Format(str, Enum):
    """Output format options."""

    JSON = "json"
    TEXT = "text"


def read_words_file(file: TextIO) -> list[str]:
    """Read words from input file (one word per line)."""
    words = []
    for line in file:
        word = line.strip()
        if word:  # Skip empty lines
            words.append(word)
    return words


def write_result(
    response: ConvertResponse,
    output_file: TextIO,
    out_format: Format,
    show_source: bool,
) -> None:
    """Write conversion result to output file."""
    if out_format == Format.JSON:
        json.dump(
            MessageToDict(
                message=response,
                always_print_fields_with_no_presence=True,
                preserving_proto_field_name=True,
            ),
            output_file,
            indent=2,
            ensure_ascii=False,
        )
    else:
        # Text format: one line per word with all pronunciations
        for word_pronunciation in response.word_pronunciations:
            pronunciations_text = []
            for pron in word_pronunciation.pronunciations:
                if show_source:
                    source_name = Pronunciation.PronunciationSource.Name(pron.pronunciation_source)
                    pronunciations_text.append(
                        f"{word_pronunciation.word} -> {pron.pronunciation} [{source_name}]"
                    )
                else:
                    pronunciations_text.append(f"{word_pronunciation.word} -> {pron.pronunciation}")
            output_file.write(" | ".join(pronunciations_text) + "\n")


def convert_impl(
    channel: grpc.Channel,
    file: TextIO,
    output: TextIO,
    out_format: Format,
    show_source: bool,
    metadata: Optional[list[tuple[str, str]]],
) -> None:
    """Perform grapheme to phoneme conversion using the gRPC service."""
    logging.info(f"Converting words from '{file.name}'")
    stub = GraphemeToPhonemeConversionStub(channel)

    words = read_words_file(file)
    if not words:
        logging.warning("No words to convert")
        return

    logging.debug(f"Converting {len(words)} words")

    request = ConvertRequest(words=words)
    response: ConvertResponse = stub.Convert(request, metadata=metadata)

    write_result(response, output, out_format, show_source)
    logging.info(f"Conversion completed: {len(response.word_pronunciations)} results")


def list_graphemes_impl(
    channel: grpc.Channel,
    output: TextIO,
    out_format: Format,
    metadata: Optional[list[tuple[str, str]]],
) -> None:
    """List allowed graphemes for the model."""
    logging.info("Listing allowed graphemes")
    stub = GraphemeToPhonemeConversionStub(channel)

    request = ListAllowedGraphemesRequest()
    response = stub.ListAllowedGraphemes(request, metadata=metadata)

    if out_format == Format.JSON:
        json.dump(
            MessageToDict(
                message=response,
                always_print_fields_with_no_presence=True,
                preserving_proto_field_name=True,
            ),
            output,
            indent=2,
            ensure_ascii=False,
        )
    else:
        output.write("\n".join(response.graphemes))

    logging.info(f"Listed {len(response.graphemes)} allowed graphemes")


class LogLevel(str, Enum):
    """Log levels."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


def _parse_metadata_callback(
    ctx: typer.Context, metadata_list: Optional[list[str]]
) -> list[tuple[str, str]]:
    """Parse metadata from command line arguments."""
    if ctx.resilient_parsing or metadata_list is None:
        return []

    params = []
    for item in metadata_list:
        t = tuple(item.split("=", 1))
        if len(t) != 2:
            raise typer.BadParameter(f"Metadata must be in format 'KEY=VALUE': {item}")
        params.append(t)
    return params


app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)


def handle_grpc_error(e: grpc.RpcError) -> None:
    """Handle gRPC errors with appropriate logging."""
    logging.error(f"gRPC call failed with status code: {e.code()}")
    logging.error(f"Error details: {e.details()}")

    if e.code() == grpc.StatusCode.UNAVAILABLE:
        logging.error("Service is unavailable.")
    elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
        logging.error("Invalid arguments were provided to the RPC.")
    elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
        logging.error("The RPC deadline was exceeded.")
    else:
        logging.error(f"An unexpected error occurred: {e.code()} - {e.details()}")


@app.command()
def convert(
    ctx: typer.Context,
    file: Annotated[
        typer.FileText,
        typer.Argument(
            help="Input file containing words to convert (one word per line). "
            "Words may contain multiple sub-words separated by '+' (e.g., 'hello+world'). "
            "If omitted, reads from standard input.",
            lazy=False,
        ),
    ] = "-",
    output: Annotated[
        typer.FileTextWrite,
        typer.Option(
            "-o",
            "--output",
            help="Output file path. If omitted, prints to stdout.",
            lazy=False,
        ),
    ] = "-",
    out_format: Annotated[
        Format,
        typer.Option(
            "-f",
            "--out-format",
            help="Output format (json, text). Text format shows pronunciations separated by '|'.",
        ),
    ] = Format.TEXT,
    show_source: Annotated[
        bool,
        typer.Option(
            "--show-source",
            help="Include pronunciation source in text output (DICTIONARY, GENERATED, or PARTLY_GENERATED).",
        ),
    ] = False,
) -> None:
    """Convert graphemes to phonemes for words in the input file."""

    try:
        logging.info(f"Connecting to {ctx.obj['host']}")
        with (
            grpc.insecure_channel(target=ctx.obj["host"])
            if ctx.obj["plaintext"]
            else grpc.secure_channel(
                target=ctx.obj["host"], credentials=grpc.ssl_channel_credentials()
            )
        ) as channel:
            convert_impl(
                channel=channel,
                file=file,
                output=output,
                out_format=out_format,
                show_source=show_source,
                metadata=ctx.obj["metadata"],
            )

    except grpc.RpcError as e:
        handle_grpc_error(e)
        raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except ValueError as e:
        logging.error(f"Invalid input: {e}")  # noqa: TRY400
        raise typer.Exit(1) from None
    except Exception:
        logging.exception("Unknown error")
        raise typer.Exit(1) from None


@app.command()
def list_graphemes(
    ctx: typer.Context,
    output: Annotated[
        typer.FileTextWrite,
        typer.Option(
            "-o",
            "--output",
            help="Output file path. If omitted, prints to stdout.",
            lazy=False,
        ),
    ] = "-",
    out_format: Annotated[
        Format,
        typer.Option(
            "-f",
            "--out-format",
            help="Output format (json, text).",
        ),
    ] = Format.TEXT,
) -> None:
    """List all allowed graphemes for the conversion model."""

    try:
        logging.info(f"Connecting to {ctx.obj['host']}")
        with (
            grpc.insecure_channel(target=ctx.obj["host"])
            if ctx.obj["plaintext"]
            else grpc.secure_channel(
                target=ctx.obj["host"], credentials=grpc.ssl_channel_credentials()
            )
        ) as channel:
            list_graphemes_impl(
                channel=channel,
                output=output,
                out_format=out_format,
                metadata=ctx.obj["metadata"],
            )

    except grpc.RpcError as e:
        handle_grpc_error(e)
        raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except Exception:
        logging.exception("Unknown error")
        raise typer.Exit(1) from None


@app.callback()
def cli(
    ctx: typer.Context,
    host: Annotated[
        str,
        typer.Option("--host", "-H", help="Server address (host:port)."),
    ] = "localhost:8080",
    log_level: Annotated[
        LogLevel, typer.Option("--log-level", "-l", help="Logging level.")
    ] = LogLevel.ERROR,
    metadata: Annotated[
        list[str],
        typer.Option(
            "--metadata",
            metavar="key=value",
            help="Custom client metadata.",
            show_default=False,
            callback=_parse_metadata_callback,
        ),
    ] = [],
    plaintext: Annotated[
        bool,
        typer.Option(
            "--plaintext", help="Use plain-text HTTP/2 when connecting to server (no TLS)."
        ),
    ] = False,
) -> None:
    """Grapheme To Phoneme Convertor gRPC client."""

    ctx.obj = {
        "host": host,
        "metadata": metadata,
        "log_level": log_level,
        "plaintext": plaintext,
    }

    logging.basicConfig(
        level=log_level.value.upper(),
        format="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


if __name__ == "__main__":
    app()
