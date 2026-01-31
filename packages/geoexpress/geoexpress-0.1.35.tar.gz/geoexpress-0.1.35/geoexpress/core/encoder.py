# from geoexpress.core.base import GeoExpressCommand

# _encoder = GeoExpressCommand("mrsidgeoencoder")


# def encode(input: str, output: str, options: dict = None):
#     args = ["-i", input, "-o", output]

#     if options:
#         for k, v in options.items():
#             flag = f"-{k}"
#             if isinstance(v, bool):
#                 if v:
#                     args.append(flag)
#             else:
#                 args.extend([flag, str(v)])

#     return _encoder.run(args)

# from typing import Optional, Dict
# from geoexpress.core.base import GeoExpressCommand

# _encoder = GeoExpressCommand("mrsidgeoencoder")


# def encode(
#     input: str,
#     output: str,
#     options: Optional[Dict] = None,
#     password: Optional[str] = None
# ) -> str:
#     """
#     Encode raster to MrSID.

#     If password is provided:
#     - Automatically switches output format to MG3
#     - Applies password protection
#     """

#     args = [
#         "-i", input,
#         "-o", output
#     ]

#     if password:
#         args.extend(["-of", "MG3"])
#         args.extend(["-pwd", password])

#     if options:
#         for k, v in options.items():
#             args.extend([f"-{k}", str(v)])

#     return _encoder.run(args)

# from typing import Optional, Dict
# from geoexpress.core.base import GeoExpressCommand

# _encoder = GeoExpressCommand("mrsidgeoencoder")


# def encode(
#     input: str,
#     output: str,
#     options: Optional[Dict] = None,
#     password: Optional[str] = None
# ) -> str:
#     """
#     Encode raster to MrSID.

#     If password is provided:
#     - Automatically switches output format to MG3
#     - Applies password protection
#     """

#     args = [
#         "-i", input,
#         "-o", output
#     ]

#     if password:
#         args.extend(["-of", "MG3"])
#         args.extend(["-pwd", password])

#     if options:
#         for k, v in options.items():
#             flag = f"-{k}"

#             # Boolean flags (lossless, etc.)
#             if isinstance(v, bool):
#                 if v:
#                     args.append(flag)
#                 continue

#             # Key-value options (cr, of, etc.)
#             args.extend([flag, str(v)])

#     return _encoder.run(args)

# geoexpress/core/encoder.py

# geoexpress/core/encoder.py

# from typing import Optional, Dict
# from geoexpress.core.base import GeoExpressCommand
# from geoexpress.core.formats import GEOEXPRESS_FORMATS
# from geoexpress.core.format_detect import detect_format_from_output

# _encoder = GeoExpressCommand("mrsidgeoencoder")


# def encode(
#     input: str,
#     output: str,
#     options: Optional[Dict] = None,
#     format: Optional[str] = None,
#     password: Optional[str] = None,
# ) -> str:

#     args = ["-i", input, "-o", output]

#     # -------------------------------
#     # Output format resolution
#     # Priority:
#     # 1. Password → MG3
#     # 2. Explicit format argument
#     # 3. Auto-detect from output extension
#     # -------------------------------

#     if password:
#         args.extend(["-of", "mg3", "-pwd", password])

#     else:
#         fmt = None

#         if format:
#             fmt = format.lower()

#         else:
#             fmt = detect_format_from_output(output)

#         if fmt:
#             # NO validation here – let GeoExpress decide
#             args.extend(["-of", fmt])

#     # -------------------------------
#     # Encoder options
#     # -------------------------------
#     if options:
#         for k, v in options.items():
#             flag = f"-{k}"

#             if isinstance(v, bool):
#                 if v:
#                     args.append(flag)
#                 continue

#             args.extend([flag, str(v)])

#     return _encoder.run(args)

from typing import Optional, Dict
from geoexpress.core.base import GeoExpressCommand
from geoexpress.core.format_detect import detect_format_from_output

_encoder = GeoExpressCommand("mrsidgeoencoder")


def encode(
    input: str,
    output: str,
    options: Optional[Dict] = None,
    format: Optional[str] = None,
    password: Optional[str] = None,
) -> str:

    args = ["-i", input, "-o", output]

    # ------------------------------------------------
    # Output format resolution priority
    # 1. password → mg3
    # 2. explicit format argument
    # 3. auto-detect from output extension
    # ------------------------------------------------

    if password:
        args.extend(["-of", "mg3", "-pwd", password])

    else:
        fmt = format.lower() if format else detect_format_from_output(output)

        if fmt:
            # NO validation – GeoExpress CLI decides
            args.extend(["-of", fmt])

    # ------------------------------------------------
    # Encoder options
    # ------------------------------------------------
    if options:
        for k, v in options.items():
            flag = f"-{k}"

            if isinstance(v, bool):
                if v:
                    args.append(flag)
                continue

            args.extend([flag, str(v)])

    return _encoder.run(args)
