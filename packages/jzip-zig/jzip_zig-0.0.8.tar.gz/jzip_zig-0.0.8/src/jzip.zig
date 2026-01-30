// Zig implementation is a byte-for-byte compatible port of `jzip.c`.
// Original source: https://github.com/jina-ai/jzip-compressor
// Author: Han Xiao - Elastic
const std = @import("std");
const builtin = @import("builtin");
const native_endian = builtin.cpu.arch.endian();

const c_math = @cImport({
    @cInclude("math.h");
});

pub const magic: u32 = 0x5A494A4A;
pub const version: u32 = 1;
pub const zstd_level_default: i32 = 1;

pub const Options = struct {
    /// Number of threads to use for the spherical transform.
    /// 1 means single-threaded. Values > 16 are clamped to 16.
    threads: u8 = 1,
};

pub const Context = struct {
    allocator: std.mem.Allocator,
    /// Requested thread count (clamped to 1..16).
    threads: u8,

    // Thread pool is only initialized when threads > 1.
    pool: std.Thread.Pool = undefined,
    has_pool: bool = false,

    // Per-worker scratch for cartesian->spherical (threads * d f64 values).
    r2_all: []f64 = &.{},
    r2_threads: usize = 0,
    r2_dim: usize = 0,

    pub fn init(self: *Context, allocator: std.mem.Allocator, threads_req: u8) !void {
        var threads: u8 = threads_req;
        if (threads < 1) threads = 1;
        if (threads > 16) threads = 16;

        self.* = .{
            .allocator = allocator,
            .threads = threads,
            .pool = undefined,
            .has_pool = false,
            .r2_all = &.{},
            .r2_threads = 0,
            .r2_dim = 0,
        };

        if (!builtin.single_threaded and threads > 1) {
            // Pool allocator must be thread-safe.
            try self.pool.init(.{ .allocator = std.heap.page_allocator, .n_jobs = threads - 1 });
            self.has_pool = true;
        }
    }

    pub fn deinit(self: *Context) void {
        if (self.has_pool) self.pool.deinit();
        if (self.r2_all.len != 0) self.allocator.free(self.r2_all);
        self.* = undefined;
    }

    pub fn compressFile(
        self: *Context,
        in_path: []const u8,
        out_path: []const u8,
        n: u32,
        d: u32,
        level: i32,
    ) !void {
        return compressFileImpl(self.allocator, in_path, out_path, n, d, level, .{ .threads = self.threads }, self);
    }

    pub fn decompressFile(self: *Context, in_path: []const u8, out_path: []const u8) !void {
        return decompressFileImpl(self.allocator, in_path, out_path, .{ .threads = self.threads }, self);
    }

    fn ensureR2(self: *Context, threads: usize, dim: usize) !void {
        if (threads <= 1) return;
        if (self.r2_all.len != 0 and self.r2_threads == threads and self.r2_dim == dim) return;
        if (self.r2_all.len != 0) self.allocator.free(self.r2_all);
        self.r2_all = try self.allocator.alloc(f64, threads * dim);
        self.r2_threads = threads;
        self.r2_dim = dim;
    }
};

pub fn compressFileWithContext(
    ctx: *Context,
    in_path: []const u8,
    out_path: []const u8,
    n: u32,
    d: u32,
    level: i32,
) !void {
    return ctx.compressFile(in_path, out_path, n, d, level);
}

pub fn decompressFileWithContext(ctx: *Context, in_path: []const u8, out_path: []const u8) !void {
    return ctx.decompressFile(in_path, out_path);
}

pub const Header = struct {
    magic: u32,
    version: u32,
    n: u32,
    d: u32,
};

pub fn parseHeader(blob: []const u8) !Header {
    if (blob.len < headerSize()) return error.InvalidFile;
    const hdr = headerReadNative(blob[0..headerSize()]);
    if (hdr.magic != magic) return error.InvalidFile;
    if (hdr.version != version) return error.InvalidFile;
    if (hdr.d < 2) return error.InvalidDims;
    return hdr;
}

pub fn compressBound(n: u32, d: u32) !usize {
    if (d < 2) return error.InvalidDims;
    const rows = @as(usize, n);
    const dim = @as(usize, d);
    const out_dim = dim - 1;
    const angles_len = try mulUsize(rows, out_dim);
    const src_size = angles_len * @sizeOf(f32);
    const bound = zstdCompressBound(src_size);
    return headerSize() + bound;
}

pub fn compressInto(
    allocator: std.mem.Allocator,
    ctx: ?*Context,
    x: []const f32,
    n: u32,
    d: u32,
    level: i32,
    dst: []u8,
) !usize {
    if (d < 2) return error.InvalidDims;

    const expected = try mulUsize(@as(usize, n), @as(usize, d));
    if (x.len != expected) return error.InvalidInputSize;

    const rows = @as(usize, n);
    const dim = @as(usize, d);
    const out_dim = dim - 1;
    const angles_len = try mulUsize(rows, out_dim);
    const src_size = angles_len * @sizeOf(f32);

    const bound = zstdCompressBound(src_size);
    const total_cap = headerSize() + bound;
    if (dst.len < total_cap) return error.DstTooSmall;

    const ang = try allocator.alloc(f32, angles_len);
    defer allocator.free(ang);
    const shuffled = try allocator.alloc(u8, src_size);
    defer allocator.free(shuffled);

    if (ctx) |cctx| {
        const threads_eff = effectiveThreads(rows, cctx.threads);
        try cctx.ensureR2(threads_eff, dim);
    }

    try cartesianToSpherical(allocator, ctx, x, ang, n, d, .{ .threads = if (ctx) |cctx| cctx.threads else 1 });
    transposeShuffleAngles(ang, shuffled, rows, out_dim);

    const hdr: Header = .{ .magic = magic, .version = version, .n = n, .d = d };
    headerWriteNative(hdr, dst[0..headerSize()]);

    const csize = try zstdCompress(dst[headerSize() .. headerSize() + bound], shuffled, level);
    return headerSize() + csize;
}

pub fn decompressInto(
    allocator: std.mem.Allocator,
    ctx: ?*Context,
    blob: []const u8,
    out: []f32,
) !void {
    const hdr = try parseHeader(blob);
    const rows = @as(usize, hdr.n);
    const dim = @as(usize, hdr.d);
    const out_dim = dim - 1;

    const expected = try mulUsize(rows, dim);
    if (out.len != expected) return error.InvalidOutputSize;

    const angles_len = try mulUsize(rows, out_dim);
    const ang_size = angles_len * @sizeOf(f32);

    const shuffled = try allocator.alloc(u8, ang_size);
    defer allocator.free(shuffled);
    const ang = try allocator.alloc(f32, angles_len);
    defer allocator.free(ang);

    const payload = blob[headerSize()..];
    const dsize = try zstdDecompress(shuffled, payload);
    if (dsize != ang_size) return error.ZstdError;

    unshuffleUntransposeAngles(shuffled, ang, rows, out_dim);
    try sphericalToCartesian(ctx, ang, out, hdr.n, hdr.d, .{ .threads = if (ctx) |cctx| cctx.threads else 1 });
}

pub fn compressFile(
    allocator: std.mem.Allocator,
    in_path: []const u8,
    out_path: []const u8,
    n: u32,
    d: u32,
    level: i32,
) !void {
    return compressFileWithOptions(allocator, in_path, out_path, n, d, level, .{});
}

pub fn compressFileWithOptions(
    allocator: std.mem.Allocator,
    in_path: []const u8,
    out_path: []const u8,
    n: u32,
    d: u32,
    level: i32,
    options: Options,
) !void {
    return compressFileImpl(allocator, in_path, out_path, n, d, level, options, null);
}

pub fn decompressFile(
    allocator: std.mem.Allocator,
    in_path: []const u8,
    out_path: []const u8,
) !void {
    return decompressFileWithOptions(allocator, in_path, out_path, .{});
}

pub fn decompressFileWithOptions(
    allocator: std.mem.Allocator,
    in_path: []const u8,
    out_path: []const u8,
    options: Options,
) !void {
    return decompressFileImpl(allocator, in_path, out_path, options, null);
}

fn compressFileImpl(
    allocator: std.mem.Allocator,
    in_path: []const u8,
    out_path: []const u8,
    n: u32,
    d: u32,
    level: i32,
    options: Options,
    ctx: ?*Context,
) !void {
    var stdout_buf: [4096]u8 = undefined;
    var stdout_file_writer = std.fs.File.stdout().writer(&stdout_buf);
    defer stdout_file_writer.interface.flush() catch {};

    var stderr_buf: [1024]u8 = undefined;
    var stderr_file_writer = std.fs.File.stderr().writer(&stderr_buf);
    defer stderr_file_writer.interface.flush() catch {};

    if (d < 2) return error.InvalidDims;

    const data = try readFloats(allocator, in_path);
    defer allocator.free(data);

    const expected = try mulUsize(@as(usize, n), @as(usize, d));
    if (data.len != expected) {
        try stderr_file_writer.interface.print(
            "error: expected {d} floats, got {d}\n",
            .{ expected, data.len },
        );
        return error.InvalidInputSize;
    }

    const rows = @as(usize, n);
    const dim = @as(usize, d);
    const out_dim = dim - 1;
    const angles_len = try mulUsize(rows, out_dim);

    const ang = try allocator.alloc(f32, angles_len);
    defer allocator.free(ang);
    const shuffled = try allocator.alloc(u8, angles_len * @sizeOf(f32));
    defer allocator.free(shuffled);

    // Prepare thread pool scratch before timing starts.
    if (ctx) |cctx| {
        const threads_eff = effectiveThreads(rows, cctx.threads);
        try cctx.ensureR2(threads_eff, dim);
    }

    var timer = try std.time.Timer.start();
    const t0 = timer.read();
    try cartesianToSpherical(allocator, ctx, data, ang, n, d, options);
    const t1 = timer.read();
    transposeShuffleAngles(ang, shuffled, rows, out_dim);
    const t2 = timer.read();

    const src_size = angles_len * @sizeOf(f32);
    const bound = zstdCompressBound(src_size);
    const compressed = try allocator.alloc(u8, headerSize() + bound);
    defer allocator.free(compressed);

    const hdr: Header = .{ .magic = magic, .version = version, .n = n, .d = d };
    headerWriteNative(hdr, compressed[0..headerSize()]);

    const csize = zstdCompress(
        compressed[headerSize() .. headerSize() + bound],
        shuffled[0..src_size],
        level,
    ) catch {
        try stderr_file_writer.interface.print("error: compression failed\n", .{});
        return error.ZstdError;
    };
    const t3 = timer.read();

    const final_size = headerSize() + csize;
    try writeFile(out_path, compressed[0..final_size]);

    const orig_bytes = expected * @sizeOf(f32);
    const ratio = @as(f64, @floatFromInt(orig_bytes)) / @as(f64, @floatFromInt(final_size));

    const spherical_ms = nsToMs(t1 - t0);
    const transpose_shuffle_ms = nsToMs(t2 - t1);
    const zstd_ms = nsToMs(t3 - t2);
    const total_ms = nsToMs(t3 - t0);
    const orig_mb = @as(f64, @floatFromInt(orig_bytes)) / 1e6;

    try stdout_file_writer.interface.print("{s}: {d} -> {d} bytes ({d:.2}x)\n", .{ out_path, orig_bytes, final_size, ratio });
    try stdout_file_writer.interface.print("  spherical: {d:.1} ms ({d:.1} MB/s)\n", .{ spherical_ms, orig_mb / (spherical_ms / 1000.0) });
    try stdout_file_writer.interface.print("  transpose+shuffle: {d:.1} ms\n", .{transpose_shuffle_ms});
    try stdout_file_writer.interface.print("  zstd: {d:.1} ms\n", .{zstd_ms});
    try stdout_file_writer.interface.print("  total encode: {d:.1} ms ({d:.1} MB/s)\n", .{ total_ms, orig_mb / (total_ms / 1000.0) });
}

fn decompressFileImpl(
    allocator: std.mem.Allocator,
    in_path: []const u8,
    out_path: []const u8,
    options: Options,
    ctx: ?*Context,
) !void {
    var stdout_buf: [4096]u8 = undefined;
    var stdout_file_writer = std.fs.File.stdout().writer(&stdout_buf);
    defer stdout_file_writer.interface.flush() catch {};

    var stderr_buf: [1024]u8 = undefined;
    var stderr_file_writer = std.fs.File.stderr().writer(&stderr_buf);
    defer stderr_file_writer.interface.flush() catch {};

    const blob = try readFileAlloc(allocator, in_path);
    defer allocator.free(blob);
    if (blob.len < headerSize()) return error.InvalidFile;

    const hdr = headerReadNative(blob[0..headerSize()]);
    if (hdr.magic != magic) {
        try stderr_file_writer.interface.print("error: invalid file\n", .{});
        return error.InvalidFile;
    }
    if (hdr.d < 2) return error.InvalidDims;

    const rows = @as(usize, hdr.n);
    const dim = @as(usize, hdr.d);
    const out_dim = dim - 1;
    const angles_len = try mulUsize(rows, out_dim);
    const ang_size = angles_len * @sizeOf(f32);

    const shuffled = try allocator.alloc(u8, ang_size);
    defer allocator.free(shuffled);
    const ang = try allocator.alloc(f32, angles_len);
    defer allocator.free(ang);

    var timer = try std.time.Timer.start();
    const t0 = timer.read();

    const payload = blob[headerSize()..];
    const dsize = zstdDecompress(shuffled, payload) catch {
        try stderr_file_writer.interface.print("error: decompression failed\n", .{});
        return error.ZstdError;
    };
    if (dsize != ang_size) {
        try stderr_file_writer.interface.print("error: decompression size mismatch\n", .{});
        return error.ZstdError;
    }
    const t1 = timer.read();

    unshuffleUntransposeAngles(shuffled, ang, rows, out_dim);
    const t2 = timer.read();

    const out_len = try mulUsize(rows, dim);
    const x = try allocator.alloc(f32, out_len);
    defer allocator.free(x);
    try sphericalToCartesian(ctx, ang, x, hdr.n, hdr.d, options);
    const t3 = timer.read();

    try writeFile(out_path, std.mem.sliceAsBytes(x));

    const orig_bytes = out_len * @sizeOf(f32);
    try stdout_file_writer.interface.print("{s}: {d} x {d} floats\n", .{ out_path, hdr.n, hdr.d });
    try stdout_file_writer.interface.print("  zstd decompress: {d:.1} ms\n", .{nsToMs(t1 - t0)});
    try stdout_file_writer.interface.print("  unshuffle+transpose: {d:.1} ms\n", .{nsToMs(t2 - t1)});
    const spherical_ms = nsToMs(t3 - t2);
    const total_ms = nsToMs(t3 - t0);
    const orig_mb = @as(f64, @floatFromInt(orig_bytes)) / 1e6;
    try stdout_file_writer.interface.print("  spherical->cartesian: {d:.1} ms ({d:.1} MB/s)\n", .{ spherical_ms, orig_mb / (spherical_ms / 1000.0) });
    try stdout_file_writer.interface.print("  total decode: {d:.1} ms ({d:.1} MB/s)\n", .{ total_ms, orig_mb / (total_ms / 1000.0) });
}

fn headerSize() usize {
    return 16;
}

fn headerWriteNative(h: Header, out: []u8) void {
    std.debug.assert(out.len >= headerSize());
    std.mem.writeInt(u32, out[0..4], h.magic, native_endian);
    std.mem.writeInt(u32, out[4..8], h.version, native_endian);
    std.mem.writeInt(u32, out[8..12], h.n, native_endian);
    std.mem.writeInt(u32, out[12..16], h.d, native_endian);
}

fn headerReadNative(in: []const u8) Header {
    std.debug.assert(in.len >= headerSize());
    return .{
        .magic = std.mem.readInt(u32, in[0..4], native_endian),
        .version = std.mem.readInt(u32, in[4..8], native_endian),
        .n = std.mem.readInt(u32, in[8..12], native_endian),
        .d = std.mem.readInt(u32, in[12..16], native_endian),
    };
}

fn readFloats(allocator: std.mem.Allocator, path: []const u8) ![]f32 {
    const file = try std.fs.cwd().openFile(path, .{});
    defer file.close();

    const size = try file.getEndPos();
    if (size % @as(u64, @sizeOf(f32)) != 0) return error.InvalidInputSize;

    const count = @as(usize, @intCast(size / @as(u64, @sizeOf(f32))));
    const data = try allocator.alloc(f32, count);
    errdefer allocator.free(data);

    const bytes = std.mem.sliceAsBytes(data);
    var tmp: [4096]u8 = undefined;
    var r = file.reader(&tmp);
    r.interface.readSliceAll(bytes) catch |err| switch (err) {
        error.EndOfStream => return error.UnexpectedEof,
        error.ReadFailed => return error.ReadFailed,
    };
    return data;
}

fn readFileAlloc(allocator: std.mem.Allocator, path: []const u8) ![]u8 {
    const file = try std.fs.cwd().openFile(path, .{});
    defer file.close();
    const size64 = try file.getEndPos();
    const size = try castUsize(size64);
    const buf = try allocator.alloc(u8, size);
    errdefer allocator.free(buf);
    var tmp: [4096]u8 = undefined;
    var r = file.reader(&tmp);
    r.interface.readSliceAll(buf) catch |err| switch (err) {
        error.EndOfStream => return error.UnexpectedEof,
        error.ReadFailed => return error.ReadFailed,
    };
    return buf;
}

fn writeFile(path: []const u8, data: []const u8) !void {
    const file = try std.fs.cwd().createFile(path, .{ .truncate = true });
    defer file.close();
    var tmp: [4096]u8 = undefined;
    var w = file.writer(&tmp);
    try w.interface.writeAll(data);
    try w.interface.flush();
}

fn cartesianToSpherical(
    allocator: std.mem.Allocator,
    ctx: ?*Context,
    x: []const f32,
    ang: []f32,
    n: u32,
    d: u32,
    options: Options,
) !void {
    const rows = @as(usize, n);
    const dim = @as(usize, d);
    const threads_req: u8 = if (ctx) |cctx| cctx.threads else options.threads;
    const threads = effectiveThreads(rows, threads_req);
    if (threads <= 1) {
        const r2 = try allocator.alloc(f64, dim);
        defer allocator.free(r2);
        cartesianToSphericalRange(x, ang, 0, rows, dim, r2);
        return;
    }

    var pool_ptr: *std.Thread.Pool = undefined;
    var local_pool: std.Thread.Pool = undefined;
    var use_local_pool = false;

    var r2_all: []f64 = undefined;
    var free_r2_all = false;

    if (ctx) |cctx| {
        // Caller should have prepared scratch; fall back to allocating if not.
        if (cctx.has_pool and cctx.r2_all.len >= threads * dim) {
            pool_ptr = &cctx.pool;
            r2_all = cctx.r2_all[0 .. threads * dim];
        } else {
            r2_all = try allocator.alloc(f64, threads * dim);
            free_r2_all = true;
            use_local_pool = true;
        }
    } else {
        r2_all = try allocator.alloc(f64, threads * dim);
        free_r2_all = true;
        use_local_pool = true;
    }
    defer if (free_r2_all) allocator.free(r2_all);

    if (use_local_pool) {
        try local_pool.init(.{ .allocator = std.heap.page_allocator, .n_jobs = threads - 1 });
        defer local_pool.deinit();
        pool_ptr = &local_pool;
    }

    var wg: std.Thread.WaitGroup = .{};
    defer wg.wait();

    const chunk = (rows + threads - 1) / threads;

    // Main thread processes chunk 0.
    const main_end: usize = @min(rows, chunk);
    cartesianToSphericalRange(x, ang, 0, main_end, dim, r2_all[0..dim]);

    // Remaining chunks run on the pool.
    for (1..threads) |t| {
        const start = t * chunk;
        const end = @min(rows, start + chunk);
        if (start >= end) break;
        const r2 = r2_all[t * dim ..][0..dim];
        pool_ptr.spawnWg(&wg, cartesianToSphericalRange, .{ x, ang, start, end, dim, r2 });
    }
}

fn cartesianToSphericalRange(
    x: []const f32,
    ang: []f32,
    row_start: usize,
    row_end: usize,
    dim: usize,
    r2: []f64,
) void {
    const out_dim = dim - 1;
    for (row_start..row_end) |row| {
        const v = x[row * dim ..][0..dim];
        const a = ang[row * out_dim ..][0..out_dim];

        r2[dim - 1] = @as(f64, v[dim - 1]) * @as(f64, v[dim - 1]);
        var i: usize = dim - 1;
        while (i > 0) {
            i -= 1;
            const vi = @as(f64, v[i]);
            r2[i] = r2[i + 1] + vi * vi;
        }

        if (dim > 2) {
            for (0..dim - 2) |j| {
                const r = std.math.sqrt(r2[j]);
                var val = @as(f64, v[j]) / r;
                if (val > 1.0) val = 1.0;
                if (val < -1.0) val = -1.0;
                // Use system libm for performance.
                a[j] = @floatCast(c_math.acos(val));
            }
        }
        a[dim - 2] = @floatCast(std.math.atan2(@as(f64, v[dim - 1]), @as(f64, v[dim - 2])));
    }
}

fn sphericalToCartesian(ctx: ?*Context, ang: []const f32, x: []f32, n: u32, d: u32, options: Options) !void {
    const rows = @as(usize, n);
    const dim = @as(usize, d);
    const threads_req: u8 = if (ctx) |cctx| cctx.threads else options.threads;
    const threads = effectiveThreads(rows, threads_req);
    if (threads <= 1) {
        sphericalToCartesianRange(ang, x, 0, rows, dim);
        return;
    }

    var pool_ptr: *std.Thread.Pool = undefined;
    var local_pool: std.Thread.Pool = undefined;
    var use_local_pool = false;

    if (ctx) |cctx| {
        if (cctx.has_pool) {
            pool_ptr = &cctx.pool;
        } else {
            use_local_pool = true;
        }
    } else {
        use_local_pool = true;
    }

    if (use_local_pool) {
        try local_pool.init(.{ .allocator = std.heap.page_allocator, .n_jobs = threads - 1 });
        defer local_pool.deinit();
        pool_ptr = &local_pool;
    }

    var wg: std.Thread.WaitGroup = .{};
    defer wg.wait();

    const chunk = (rows + threads - 1) / threads;

    // Main thread processes chunk 0.
    const main_end: usize = @min(rows, chunk);
    sphericalToCartesianRange(ang, x, 0, main_end, dim);

    // Remaining chunks run on the pool.
    for (1..threads) |t| {
        const start = t * chunk;
        const end = @min(rows, start + chunk);
        if (start >= end) break;
        pool_ptr.spawnWg(&wg, sphericalToCartesianRange, .{ ang, x, start, end, dim });
    }
}

fn sphericalToCartesianRange(ang: []const f32, x: []f32, row_start: usize, row_end: usize, dim: usize) void {
    const in_dim = dim - 1;
    for (row_start..row_end) |row| {
        const a = ang[row * in_dim ..][0..in_dim];
        const v = x[row * dim ..][0..dim];

        var s: f64 = 1.0;
        if (dim > 2) {
            for (0..dim - 2) |i| {
                const angle = @as(f64, a[i]);
                v[i] = @floatCast(s * std.math.cos(angle));
                s *= std.math.sin(angle);
            }
        }
        const last_angle = @as(f64, a[dim - 2]);
        v[dim - 2] = @floatCast(s * std.math.cos(last_angle));
        v[dim - 1] = @floatCast(s * std.math.sin(last_angle));
    }
}

fn effectiveThreads(rows: usize, threads_req: u8) usize {
    if (builtin.single_threaded) return 1;
    var t: usize = threads_req;
    if (t < 1) t = 1;
    if (t > 16) t = 16;
    if (t > rows) t = rows;
    return t;
}

inline fn shuffleStoreU32(dst: []u8, n_floats: usize, k: usize, bits: u32) void {
    std.debug.assert(k < n_floats);
    std.debug.assert(dst.len >= n_floats * 4);
    if (comptime native_endian == .little) {
        dst[k] = @truncate(bits);
        dst[n_floats + k] = @truncate(bits >> 8);
        dst[n_floats * 2 + k] = @truncate(bits >> 16);
        dst[n_floats * 3 + k] = @truncate(bits >> 24);
    } else {
        dst[k] = @truncate(bits >> 24);
        dst[n_floats + k] = @truncate(bits >> 16);
        dst[n_floats * 2 + k] = @truncate(bits >> 8);
        dst[n_floats * 3 + k] = @truncate(bits);
    }
}

inline fn shuffleLoadU32(src: []const u8, n_floats: usize, k: usize) u32 {
    std.debug.assert(k < n_floats);
    std.debug.assert(src.len >= n_floats * 4);
    if (comptime native_endian == .little) {
        return (@as(u32, src[k])) |
            (@as(u32, src[n_floats + k]) << 8) |
            (@as(u32, src[n_floats * 2 + k]) << 16) |
            (@as(u32, src[n_floats * 3 + k]) << 24);
    } else {
        return (@as(u32, src[k]) << 24) |
            (@as(u32, src[n_floats + k]) << 16) |
            (@as(u32, src[n_floats * 2 + k]) << 8) |
            (@as(u32, src[n_floats * 3 + k]));
    }
}

// Equivalent to: transpose(ang -> ang_t) then byteShuffle(ang_t_bytes -> shuffled)
fn transposeShuffleAngles(ang: []const f32, shuffled: []u8, rows: usize, out_dim: usize) void {
    const n_floats = rows * out_dim;
    std.debug.assert(ang.len >= n_floats);
    std.debug.assert(shuffled.len >= n_floats * 4);

    const tile_rows: usize = 256;
    const tile_cols: usize = 16;
    var tile: [tile_rows * tile_cols]u32 = undefined;

    var row0: usize = 0;
    while (row0 < rows) : (row0 += tile_rows) {
        const r_end = @min(rows, row0 + tile_rows);
        const r_len = r_end - row0;

        var col0: usize = 0;
        while (col0 < out_dim) : (col0 += tile_cols) {
            const c_end = @min(out_dim, col0 + tile_cols);
            const c_len = c_end - col0;

            // Read tile in row-major order (contiguous reads from ang).
            for (0..r_len) |r| {
                const src = ang[(row0 + r) * out_dim + col0 ..][0..c_len];
                for (0..c_len) |cc| {
                    tile[r * tile_cols + cc] = @bitCast(src[cc]);
                }
            }

            // Write transposed tile into shuffled planes (contiguous writes per column).
            for (0..c_len) |cc| {
                const base = (col0 + cc) * rows + row0;
                for (0..r_len) |r| {
                    const bits = tile[r * tile_cols + cc];
                    shuffleStoreU32(shuffled, n_floats, base + r, bits);
                }
            }
        }
    }
}

// Equivalent to: byteUnshuffle(shuffled -> ang_t_bytes) then transpose(ang_t -> ang)
fn unshuffleUntransposeAngles(shuffled: []const u8, ang: []f32, rows: usize, out_dim: usize) void {
    const n_floats = rows * out_dim;
    std.debug.assert(shuffled.len >= n_floats * 4);
    std.debug.assert(ang.len >= n_floats);

    const tile_rows: usize = 256;
    const tile_cols: usize = 16;
    var tile: [tile_rows * tile_cols]u32 = undefined;

    var row0: usize = 0;
    while (row0 < rows) : (row0 += tile_rows) {
        const r_end = @min(rows, row0 + tile_rows);
        const r_len = r_end - row0;

        var col0: usize = 0;
        while (col0 < out_dim) : (col0 += tile_cols) {
            const c_end = @min(out_dim, col0 + tile_cols);
            const c_len = c_end - col0;

            // Read transposed tile from shuffled planes (contiguous reads per column).
            for (0..c_len) |cc| {
                const base = (col0 + cc) * rows + row0;
                for (0..r_len) |r| {
                    tile[r * tile_cols + cc] = shuffleLoadU32(shuffled, n_floats, base + r);
                }
            }

            // Write tile back in row-major order (contiguous writes to ang).
            for (0..r_len) |r| {
                const dst = ang[(row0 + r) * out_dim + col0 ..][0..c_len];
                for (0..c_len) |cc| {
                    dst[cc] = @bitCast(tile[r * tile_cols + cc]);
                }
            }
        }
    }
}

fn transpose(src: []const f32, dst: []f32, rows_u32: u32, cols_u32: u32) void {
    const rows = @as(usize, rows_u32);
    const cols = @as(usize, cols_u32);
    for (0..rows) |i| {
        for (0..cols) |j| {
            dst[j * rows + i] = src[i * cols + j];
        }
    }
}

fn byteShuffle(src_bytes: []const u8, dst: []u8, n_floats: usize) void {
    std.debug.assert(src_bytes.len >= n_floats * 4);
    std.debug.assert(dst.len >= n_floats * 4);
    for (0..n_floats) |i| {
        dst[i] = src_bytes[i * 4];
        dst[n_floats + i] = src_bytes[i * 4 + 1];
        dst[n_floats * 2 + i] = src_bytes[i * 4 + 2];
        dst[n_floats * 3 + i] = src_bytes[i * 4 + 3];
    }
}

fn byteUnshuffle(src: []const u8, dst_bytes: []u8, n_floats: usize) void {
    std.debug.assert(src.len >= n_floats * 4);
    std.debug.assert(dst_bytes.len >= n_floats * 4);
    for (0..n_floats) |i| {
        dst_bytes[i * 4] = src[i];
        dst_bytes[i * 4 + 1] = src[n_floats + i];
        dst_bytes[i * 4 + 2] = src[n_floats * 2 + i];
        dst_bytes[i * 4 + 3] = src[n_floats * 3 + i];
    }
}

fn nsToMs(ns: u64) f64 {
    return @as(f64, @floatFromInt(ns)) / 1e6;
}

fn castUsize(v: u64) !usize {
    if (v > std.math.maxInt(usize)) return error.Overflow;
    return @as(usize, @intCast(v));
}

fn mulUsize(a: usize, b: usize) !usize {
    const r = @mulWithOverflow(a, b);
    if (r[1] != 0) return error.Overflow;
    return r[0];
}

// ---- zstd bindings ----

const c = @cImport({
    @cInclude("zstd.h");
});

fn zstdCompressBound(src_size: usize) usize {
    return c.ZSTD_compressBound(src_size);
}

fn zstdCompress(dst: []u8, src: []const u8, level: i32) !usize {
    const res = c.ZSTD_compress(
        @ptrCast(dst.ptr),
        dst.len,
        @ptrCast(src.ptr),
        src.len,
        @as(c_int, @intCast(level)),
    );
    if (c.ZSTD_isError(res) != 0) return error.ZstdError;
    return @as(usize, @intCast(res));
}

fn zstdDecompress(dst: []u8, src: []const u8) !usize {
    const res = c.ZSTD_decompress(
        @ptrCast(dst.ptr),
        dst.len,
        @ptrCast(src.ptr),
        src.len,
    );
    if (c.ZSTD_isError(res) != 0) return error.ZstdError;
    return @as(usize, @intCast(res));
}

test "byte shuffle roundtrip" {
    var data: [8]u32 = .{ 0x01020304, 0x05060708, 0x11121314, 0x15161718, 0x21222324, 0x25262728, 0x31323334, 0x35363738 };
    const bytes = std.mem.sliceAsBytes(data[0..]);
    var shuffled: [32]u8 = undefined;
    var restored: [32]u8 = undefined;
    byteShuffle(bytes, shuffled[0..], data.len);
    byteUnshuffle(shuffled[0..], restored[0..], data.len);
    try std.testing.expectEqualSlices(u8, bytes, restored[0..]);
}

test "transpose+shuffle fusion matches reference" {
    const rows: usize = 7;
    const out_dim: usize = 5;
    const n_floats = rows * out_dim;

    var ang: [n_floats]f32 = undefined;
    for (0..n_floats) |i| {
        // Deterministic bit patterns (avoid NaN payload traps).
        const bits: u32 = 0x3f000000 +% (@as(u32, @truncate(i)) *% 2654435761);
        ang[i] = @bitCast(bits);
    }

    var ang_t: [n_floats]f32 = undefined;
    transpose(ang[0..], ang_t[0..], @as(u32, @intCast(rows)), @as(u32, @intCast(out_dim)));

    var shuffled_ref: [n_floats * 4]u8 = undefined;
    byteShuffle(std.mem.sliceAsBytes(ang_t[0..]), shuffled_ref[0..], n_floats);

    var shuffled_new: [n_floats * 4]u8 = undefined;
    transposeShuffleAngles(ang[0..], shuffled_new[0..], rows, out_dim);
    try std.testing.expectEqualSlices(u8, shuffled_ref[0..], shuffled_new[0..]);

    // Inverse fusion matches reference reconstruction.
    var ang_back_new: [n_floats]f32 = undefined;
    unshuffleUntransposeAngles(shuffled_ref[0..], ang_back_new[0..], rows, out_dim);
    try std.testing.expectEqualSlices(u8, std.mem.sliceAsBytes(ang[0..]), std.mem.sliceAsBytes(ang_back_new[0..]));
}
