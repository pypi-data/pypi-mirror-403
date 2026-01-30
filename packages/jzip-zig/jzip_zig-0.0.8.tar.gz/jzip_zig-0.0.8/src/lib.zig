const jzip = @import("jzip.zig");

pub const Header = jzip.Header;
pub const Options = jzip.Options;
pub const Context = jzip.Context;
pub const magic = jzip.magic;
pub const version = jzip.version;
pub const zstd_level_default = jzip.zstd_level_default;

pub const compressFile = jzip.compressFile;
pub const compressFileWithContext = jzip.compressFileWithContext;
pub const compressFileWithOptions = jzip.compressFileWithOptions;
pub const decompressFile = jzip.decompressFile;
pub const decompressFileWithContext = jzip.decompressFileWithContext;
pub const decompressFileWithOptions = jzip.decompressFileWithOptions;

pub const parseHeader = jzip.parseHeader;
pub const compressBound = jzip.compressBound;
pub const compressInto = jzip.compressInto;
pub const decompressInto = jzip.decompressInto;
