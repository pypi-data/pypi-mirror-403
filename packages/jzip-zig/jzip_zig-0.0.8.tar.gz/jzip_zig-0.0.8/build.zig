const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const zstd_include_dir = b.option([]const u8, "zstd-include", "Path to zstd headers (directory containing zstd.h)");
    const zstd_lib_dir = b.option([]const u8, "zstd-lib", "Path to zstd library directory");

    const jzip_mod = b.addModule("jzip", .{
        .root_source_file = b.path("src/jzip.zig"),
        .target = target,
    });
    // Needed for @cImport("zstd.h") inside src/jzip.zig.
    // Keep this on the module so all importers inherit it.
    jzip_mod.addIncludePath(b.path("third_party/zstd/lib"));

    const exe = b.addExecutable(.{
        .name = "jzip",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "jzip", .module = jzip_mod },
            },
        }),
    });
    linkZstd(b, exe, target, zstd_include_dir, zstd_lib_dir);
    b.installArtifact(exe);

    const lib = b.addLibrary(.{
        .name = "jzip",
        .linkage = .static,
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/lib.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "jzip", .module = jzip_mod },
            },
        }),
    });
    linkZstd(b, lib, target, zstd_include_dir, zstd_lib_dir);
    b.installArtifact(lib);

    const run_exe = b.addRunArtifact(exe);
    run_exe.step.dependOn(b.getInstallStep());
    if (b.args) |args| run_exe.addArgs(args);
    const run_step = b.step("run", "Run jzip");
    run_step.dependOn(&run_exe.step);

    const unit_tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/jzip.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    linkZstd(b, unit_tests, target, zstd_include_dir, zstd_lib_dir);
    const run_tests = b.addRunArtifact(unit_tests);
    const test_step = b.step("test", "Run unit tests");
    test_step.dependOn(&run_tests.step);

    // Python bindings (CPython extension module)
    const python_step = b.step("python-bindings", "Build Python native bindings");

    const python_mod = b.createModule(.{
        .target = target,
        .optimize = optimize,
        .root_source_file = b.path("bindings/python/src/main.zig"),
    });
    python_mod.addImport("jzip", jzip_mod);
    python_mod.link_libc = true;

    // Make our stub CPython internal headers visible before Python's include dir.
    python_mod.addIncludePath(b.path("bindings/python/include"));

    const python_include = b.option([]const u8, "python-include", "Python include path (python -c \"import sysconfig; print(sysconfig.get_path('include'))\")");
    _ = b.option([]const u8, "python-lib", "(unused) Python library name (not needed for extension modules)");
    _ = b.option([]const u8, "python-lib-path", "(unused) Python library search path");

    if (python_include) |inc| {
        python_mod.addIncludePath(.{ .cwd_relative = inc });
    }

    const is_macos = target.result.os.tag == .macos;

    const python_lib = b.addLibrary(.{
        .linkage = .dynamic,
        .name = "_jzip",
        .root_module = python_mod,
    });
    // Build vendored zstd into the extension so wheels are self-contained.
    linkVendoredZstd(b, python_lib);
    // Still need libc + (on non-Darwin) libm for trig.
    python_lib.linkLibC();
    if (!is_macos) {
        python_lib.linkSystemLibrary("m");
    }
    // Extension modules typically do not link to libpython; symbols resolve at load time.
    // On macOS and Linux, explicitly allow undefined Python symbols.
    if (is_macos or target.result.os.tag == .linux) {
        python_lib.linker_allow_shlib_undefined = true;
    }

    const python_install = b.addInstallArtifact(python_lib, .{
        .dest_dir = .{ .override = .{ .custom = "bindings/python/jzip" } },
    });
    python_step.dependOn(&python_install.step);
}

fn linkVendoredZstd(b: *std.Build, step: *std.Build.Step.Compile) void {
    // Compile zstd sources directly into the extension.
    // This avoids runtime dependencies on libzstd.{so,dylib} in wheels.
    step.addIncludePath(b.path("third_party/zstd/lib"));

    const flags = b.dupeStrings(&.{
        "-std=c99",
        "-O3",
        "-DNDEBUG",
        "-DXXH_NAMESPACE=ZSTD_",
        "-DZSTD_DISABLE_ASM",
        "-DZSTD_LEGACY_SUPPORT=0",
    });

    const files = collectZstdCoreSources(b) catch |err|
        std.debug.panic("failed to collect zstd sources: {s}", .{@errorName(err)});
    step.root_module.addCSourceFiles(.{
        .root = b.path("third_party/zstd/lib"),
        .files = files,
        .flags = flags,
        .language = .c,
    });
}

fn collectZstdCoreSources(b: *std.Build) ![]const []const u8 {
    var list: std.ArrayList([]const u8) = .empty;
    errdefer list.deinit(b.allocator);

    try collectCFilesInDir(b, &list, "third_party/zstd/lib/common", "common");
    try collectCFilesInDir(b, &list, "third_party/zstd/lib/compress", "compress");
    try collectCFilesInDir(b, &list, "third_party/zstd/lib/decompress", "decompress");

    return list.toOwnedSlice(b.allocator);
}

fn collectCFilesInDir(
    b: *std.Build,
    list: *std.ArrayList([]const u8),
    dir_path: []const u8,
    rel_prefix: []const u8,
) !void {
    var dir = try std.fs.cwd().openDir(dir_path, .{ .iterate = true });
    defer dir.close();

    var it = dir.iterate();
    while (try it.next()) |e| {
        if (e.kind != .file) continue;
        if (!std.mem.endsWith(u8, e.name, ".c")) continue;
        // Relative to third_party/zstd/lib
        const rel = b.fmt("{s}/{s}", .{ rel_prefix, e.name });
        try list.append(b.allocator, rel);
    }
}

fn linkZstd(
    b: *std.Build,
    step: *std.Build.Step.Compile,
    target: std.Build.ResolvedTarget,
    zstd_include_dir: ?[]const u8,
    zstd_lib_dir: ?[]const u8,
) void {
    step.linkLibC();
    step.linkSystemLibrary("zstd");

    if (target.result.os.tag != .macos and target.result.os.tag != .ios and target.result.os.tag != .tvos and target.result.os.tag != .watchos) {
        // Needed on many non-Darwin targets when using sin/cos/atan2.
        step.linkSystemLibrary("m");
    }

    if (zstd_include_dir) |p| step.addIncludePath(.{ .cwd_relative = p });
    if (zstd_lib_dir) |p| step.addLibraryPath(.{ .cwd_relative = p });

    // Common Homebrew/MacPorts locations.
    if (target.result.os.tag == .macos) {
        addIncludeAndLibIfExists(step, b, "/opt/homebrew/include", "/opt/homebrew/lib");
        addIncludeAndLibIfExists(step, b, "/usr/local/include", "/usr/local/lib");
    }
}

fn addIncludeAndLibIfExists(step: *std.Build.Step.Compile, b: *std.Build, include_dir: []const u8, lib_dir: []const u8) void {
    _ = b;
    if (dirExistsAbsolute(include_dir)) step.addIncludePath(.{ .cwd_relative = include_dir });
    if (dirExistsAbsolute(lib_dir)) step.addLibraryPath(.{ .cwd_relative = lib_dir });
}

fn dirExistsAbsolute(path: []const u8) bool {
    var dir = std.fs.openDirAbsolute(path, .{}) catch return false;
    dir.close();
    return true;
}
