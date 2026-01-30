const std = @import("std");
const jzip = @import("jzip");

pub fn main() !void {
    var stderr_buf: [4096]u8 = undefined;
    var stderr_file_writer = std.fs.File.stderr().writer(&stderr_buf);
    defer stderr_file_writer.interface.flush() catch {};

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer {
        const status = gpa.deinit();
        if (status == .leak) @panic("memory leak detected");
    }
    const allocator = gpa.allocator();

    var args = std.process.args();
    _ = args.next(); // argv[0]

    var threads: u8 = 1;

    var cmd = args.next() orelse {
        try usage(&stderr_file_writer.interface);
        return error.InvalidArgs;
    };
    if (std.mem.eql(u8, cmd, "-t") or std.mem.eql(u8, cmd, "--threads")) {
        const threads_str = args.next() orelse return failUsage(&stderr_file_writer.interface);
        threads = try std.fmt.parseInt(u8, threads_str, 10);
        if (threads < 1 or threads > 16) {
            try stderr_file_writer.interface.print("error: threads must be 1-16\n", .{});
            return error.InvalidArgs;
        }
        cmd = args.next() orelse return failUsage(&stderr_file_writer.interface);
    }

    if (std.mem.eql(u8, cmd, "-c")) {
        const in_path = args.next() orelse return failUsage(&stderr_file_writer.interface);
        const out_path = args.next() orelse return failUsage(&stderr_file_writer.interface);
        const n_str = args.next() orelse return failUsage(&stderr_file_writer.interface);
        const d_str = args.next() orelse return failUsage(&stderr_file_writer.interface);
        const level_str = args.next();
        if (args.next() != null) return failUsage(&stderr_file_writer.interface);

        const n = try parseU32(n_str);
        const d = try parseU32(d_str);
        const level: i32 = if (level_str) |s| blk: {
            const tmp = try std.fmt.parseInt(i32, s, 10);
            break :blk tmp;
        } else jzip.zstd_level_default;

        if (level < 1 or level > 22) {
            try stderr_file_writer.interface.print("error: level must be 1-22\n", .{});
            return error.InvalidArgs;
        }
        if (threads == 1) {
            try jzip.compressFileWithOptions(allocator, in_path, out_path, n, d, level, .{ .threads = 1 });
        } else {
            var ctx: jzip.Context = undefined;
            try ctx.init(allocator, threads);
            defer ctx.deinit();
            try ctx.compressFile(in_path, out_path, n, d, level);
        }
        return;
    }

    if (std.mem.eql(u8, cmd, "-d")) {
        const in_path = args.next() orelse return failUsage(&stderr_file_writer.interface);
        const out_path = args.next() orelse return failUsage(&stderr_file_writer.interface);
        if (args.next() != null) return failUsage(&stderr_file_writer.interface);
        if (threads == 1) {
            try jzip.decompressFileWithOptions(allocator, in_path, out_path, .{ .threads = 1 });
        } else {
            var ctx: jzip.Context = undefined;
            try ctx.init(allocator, threads);
            defer ctx.deinit();
            try ctx.decompressFile(in_path, out_path);
        }
        return;
    }

    return failUsage(&stderr_file_writer.interface);
}

fn failUsage(stderr: *std.Io.Writer) !void {
    try usage(stderr);
    return error.InvalidArgs;
}

fn usage(w: *std.Io.Writer) !void {
    try w.print("usage: jzip [-t THREADS] -c INPUT OUTPUT N D [LEVEL]\n", .{});
    try w.print("       jzip [-t THREADS] -d INPUT OUTPUT\n", .{});
    try w.print("       THREADS: 1-16 (default: 1)\n", .{});
    try w.print("       LEVEL: zstd compression level 1-22 (default: {d})\n", .{jzip.zstd_level_default});
}

fn parseU32(s: []const u8) !u32 {
    const v = try std.fmt.parseInt(u32, s, 10);
    return v;
}
