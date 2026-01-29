# -*- coding: utf-8 -*-


def get_video_extensions() -> set:
    res = {".mp4", ".m4v", ".mkv", ".mk3d", ".mka", ".webm", ".avi", ".mov", ".wmv", ".wma", ".asf", ".ts", ".m2ts",
           ".flv",
           ".3gp", ".3g2", ".rm", ".rmvb", ".divx", ".mxf", ".gxf", ".nut", ".psp", ".mpg"}
    return res


def get_audio_extensions() -> set:
    res = {".mp3", ".wav", ".aac", ".flac", ".ogg", ".oga", ".amr"}
    return res


def get_image_extensions() -> set:
    res = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp", ".svg", ".heif", ".hei", ".ico",
           ".ppm", ".pgm", ".pbm", ".pnm",
           ".pcx", ".dds", ".tga", ".icb", ".vda", ".vst", ".exr", ".jp2", ".j2k", ".pgf", ".xbm"}
    return res
