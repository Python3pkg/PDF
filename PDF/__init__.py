import pkg_resources

from pdf import PdfFileReader, PdfFileWriter
from merger import PdfFileMerger

__all__ = ["pdf", "PdfFileMerger"]

__version__ = pkg_resources.require('PDF')[0].version
