//! Python module entry point for jzip

const std = @import("std");
const py = @import("python.zig");
const c = py.c;
const jzip = @import("jzip");

const allocator = std.heap.c_allocator;

const capsule_name: [:0]const u8 = "jzip.Context";

fn jzip_version(_: [*c]c.PyObject, _: [*c]c.PyObject) callconv(.c) [*c]c.PyObject {
    return c.PyUnicode_FromString("0.0.8");
}

fn py_header(_: [*c]c.PyObject, args: [*c]c.PyObject) callconv(.c) [*c]c.PyObject {
    var blob_obj: [*c]c.PyObject = null;
    if (c.PyArg_ParseTuple(args, "O", &blob_obj) == 0) return null;

    var buf = std.mem.zeroes(c.Py_buffer);
    if (c.PyObject_GetBuffer(blob_obj, &buf, c.PyBUF_SIMPLE) < 0) return null;
    defer c.PyBuffer_Release(&buf);

    const blob: [*]const u8 = @ptrCast(buf.buf);
    const blob_len: usize = @intCast(buf.len);

    const hdr = jzip.parseHeader(blob[0..blob_len]) catch {
        py.raiseValue("invalid jzip blob");
        return null;
    };

    const t = c.PyTuple_New(2) orelse return null;
    _ = c.PyTuple_SetItem(t, 0, c.PyLong_FromUnsignedLong(@as(c_ulong, hdr.n)));
    _ = c.PyTuple_SetItem(t, 1, c.PyLong_FromUnsignedLong(@as(c_ulong, hdr.d)));
    return t;
}

fn checkF32Buffer(buf: *c.Py_buffer, writable: bool) bool {
    if (buf.itemsize != @sizeOf(f32)) return false;
    if (buf.format == null) return false;
    const fmt = std.mem.span(buf.format);
    if (fmt.len == 0 or fmt[0] != 'f') return false;
    if (writable and (buf.readonly != 0)) return false;
    if (@intFromPtr(buf.buf) % @alignOf(f32) != 0) return false;
    return true;
}

fn py_compress(_: [*c]c.PyObject, args: [*c]c.PyObject, kwds: [*c]c.PyObject) callconv(.c) [*c]c.PyObject {
    var x_obj: [*c]c.PyObject = null;
    var n_in: c_ulong = 0;
    var d_in: c_ulong = 0;
    var level: c_int = 1;
    var threads_in: c_int = 1;

    const kwlist = [_:null]?[*:0]const u8{ "x", "n", "d", "level", "threads", null };
    if (c.PyArg_ParseTupleAndKeywords(args, kwds, "Okk|ii", @ptrCast(@constCast(&kwlist)), &x_obj, &n_in, &d_in, &level, &threads_in) == 0)
        return null;

    if (n_in > std.math.maxInt(u32) or d_in > std.math.maxInt(u32)) {
        py.raiseValue("n and d must fit in uint32");
        return null;
    }
    const n: u32 = @intCast(n_in);
    const d: u32 = @intCast(d_in);

    if (threads_in < 1 or threads_in > 16) {
        py.raiseValue("threads must be 1-16");
        return null;
    }
    const threads: u8 = @intCast(threads_in);

    var x_buf = std.mem.zeroes(c.Py_buffer);
    if (c.PyObject_GetBuffer(x_obj, &x_buf, c.PyBUF_SIMPLE | c.PyBUF_FORMAT) < 0) return null;
    defer c.PyBuffer_Release(&x_buf);
    if (!checkF32Buffer(&x_buf, false)) {
        py.raiseType("x must be a contiguous float32 buffer");
        return null;
    }

    const x_len_bytes: usize = @intCast(x_buf.len);
    const x_f32_len: usize = x_len_bytes / @sizeOf(f32);
    const expected = @as(usize, n) * @as(usize, d);
    if (x_f32_len != expected) {
        py.raiseValue("x length does not match n*d");
        return null;
    }
    const x_ptr: [*]const f32 = @ptrCast(@alignCast(x_buf.buf));

    const cap = jzip.compressBound(n, d) catch {
        py.raiseValue("invalid dims");
        return null;
    };

    // We cannot rely on PyBytes_Resize under the limited API used for
    // CPython 3.12 header import. Compress into a temp buffer and let
    // PyBytes_FromStringAndSize copy into an exactly-sized bytes object.
    const tmp = allocator.alloc(u8, cap) catch {
        py.raiseRuntime("Out of memory");
        return null;
    };
    defer allocator.free(tmp);

    const gil = c.PyEval_SaveThread();
    const actual = if (threads == 1) blk: {
        break :blk jzip.compressInto(
            allocator,
            null,
            x_ptr[0..x_f32_len],
            n,
            d,
            @as(i32, level),
            tmp,
        ) catch {
            c.PyEval_RestoreThread(gil);
            py.raiseRuntime("compression failed");
            return null;
        };
    } else blk: {
        var ctx: jzip.Context = undefined;
        ctx.init(allocator, threads) catch {
            c.PyEval_RestoreThread(gil);
            py.raiseRuntime("Failed to init context");
            return null;
        };
        defer ctx.deinit();
        break :blk jzip.compressInto(
            allocator,
            &ctx,
            x_ptr[0..x_f32_len],
            n,
            d,
            @as(i32, level),
            tmp,
        ) catch {
            c.PyEval_RestoreThread(gil);
            py.raiseRuntime("compression failed");
            return null;
        };
    };
    c.PyEval_RestoreThread(gil);

    return c.PyBytes_FromStringAndSize(@ptrCast(tmp.ptr), @as(c.Py_ssize_t, @intCast(actual)));
}

fn py_decompress_into(_: [*c]c.PyObject, args: [*c]c.PyObject, kwds: [*c]c.PyObject) callconv(.c) [*c]c.PyObject {
    var blob_obj: [*c]c.PyObject = null;
    var out_obj: [*c]c.PyObject = null;
    var threads_in: c_int = 1;

    const kwlist = [_:null]?[*:0]const u8{ "blob", "out", "threads", null };
    if (c.PyArg_ParseTupleAndKeywords(args, kwds, "OO|i", @ptrCast(@constCast(&kwlist)), &blob_obj, &out_obj, &threads_in) == 0)
        return null;

    if (threads_in < 1 or threads_in > 16) {
        py.raiseValue("threads must be 1-16");
        return null;
    }
    const threads: u8 = @intCast(threads_in);

    var blob_buf = std.mem.zeroes(c.Py_buffer);
    if (c.PyObject_GetBuffer(blob_obj, &blob_buf, c.PyBUF_SIMPLE) < 0) return null;
    defer c.PyBuffer_Release(&blob_buf);
    const blob_ptr: [*]const u8 = @ptrCast(blob_buf.buf);
    const blob_len: usize = @intCast(blob_buf.len);

    var out_buf = std.mem.zeroes(c.Py_buffer);
    if (c.PyObject_GetBuffer(out_obj, &out_buf, c.PyBUF_WRITABLE | c.PyBUF_FORMAT) < 0) return null;
    defer c.PyBuffer_Release(&out_buf);
    if (!checkF32Buffer(&out_buf, true)) {
        py.raiseType("out must be a writable contiguous float32 buffer");
        return null;
    }
    const out_ptr: [*]f32 = @ptrCast(@alignCast(out_buf.buf));
    const out_f32_len: usize = @as(usize, @intCast(out_buf.len)) / @sizeOf(f32);

    const gil = c.PyEval_SaveThread();
    if (threads == 1) {
        jzip.decompressInto(allocator, null, blob_ptr[0..blob_len], out_ptr[0..out_f32_len]) catch {
            c.PyEval_RestoreThread(gil);
            py.raiseRuntime("decompression failed");
            return null;
        };
    } else {
        var ctx: jzip.Context = undefined;
        ctx.init(allocator, threads) catch {
            c.PyEval_RestoreThread(gil);
            py.raiseRuntime("Failed to init context");
            return null;
        };
        defer ctx.deinit();
        jzip.decompressInto(allocator, &ctx, blob_ptr[0..blob_len], out_ptr[0..out_f32_len]) catch {
            c.PyEval_RestoreThread(gil);
            py.raiseRuntime("decompression failed");
            return null;
        };
    }
    c.PyEval_RestoreThread(gil);
    return py.none();
}

fn ctx_capsule_destructor(capsule: [*c]c.PyObject) callconv(.c) void {
    // Destructors must not raise.
    const raw = c.PyCapsule_GetPointer(capsule, capsule_name.ptr);
    if (raw == null) {
        c.PyErr_Clear();
        return;
    }
    const ctx: *jzip.Context = @ptrCast(@alignCast(raw));
    ctx.deinit();
    allocator.destroy(ctx);
}

fn py_ctx_new(_: [*c]c.PyObject, args: [*c]c.PyObject, kwds: [*c]c.PyObject) callconv(.c) [*c]c.PyObject {
    var threads_in: c_int = 1;
    const kwlist = [_:null]?[*:0]const u8{ "threads", null };
    if (c.PyArg_ParseTupleAndKeywords(args, kwds, "|i", @ptrCast(@constCast(&kwlist)), &threads_in) == 0) return null;
    if (threads_in < 1 or threads_in > 16) {
        py.raiseValue("threads must be 1-16");
        return null;
    }

    const ptr = allocator.create(jzip.Context) catch {
        py.raiseRuntime("Out of memory");
        return null;
    };
    errdefer allocator.destroy(ptr);
    ptr.init(allocator, @intCast(threads_in)) catch {
        py.raiseRuntime("Failed to init context");
        return null;
    };

    return c.PyCapsule_New(ptr, capsule_name.ptr, @ptrCast(&ctx_capsule_destructor));
}

fn getCtxFromCapsule(obj: [*c]c.PyObject) ?*jzip.Context {
    const raw = c.PyCapsule_GetPointer(obj, capsule_name.ptr);
    if (raw == null) return null;
    return @ptrCast(@alignCast(raw));
}

fn py_ctx_compress(_: [*c]c.PyObject, args: [*c]c.PyObject, kwds: [*c]c.PyObject) callconv(.c) [*c]c.PyObject {
    var cap_obj: [*c]c.PyObject = null;
    var x_obj: [*c]c.PyObject = null;
    var n_in: c_ulong = 0;
    var d_in: c_ulong = 0;
    var level: c_int = 1;

    const kwlist = [_:null]?[*:0]const u8{ "ctx", "x", "n", "d", "level", null };
    if (c.PyArg_ParseTupleAndKeywords(args, kwds, "OOkk|i", @ptrCast(@constCast(&kwlist)), &cap_obj, &x_obj, &n_in, &d_in, &level) == 0)
        return null;

    const ctx = getCtxFromCapsule(cap_obj) orelse {
        py.raiseType("invalid context");
        return null;
    };

    if (n_in > std.math.maxInt(u32) or d_in > std.math.maxInt(u32)) {
        py.raiseValue("n and d must fit in uint32");
        return null;
    }
    const n: u32 = @intCast(n_in);
    const d: u32 = @intCast(d_in);

    var x_buf = std.mem.zeroes(c.Py_buffer);
    if (c.PyObject_GetBuffer(x_obj, &x_buf, c.PyBUF_SIMPLE | c.PyBUF_FORMAT) < 0) return null;
    defer c.PyBuffer_Release(&x_buf);
    if (!checkF32Buffer(&x_buf, false)) {
        py.raiseType("x must be a contiguous float32 buffer");
        return null;
    }

    const x_len_bytes: usize = @intCast(x_buf.len);
    const x_f32_len: usize = x_len_bytes / @sizeOf(f32);
    const expected = @as(usize, n) * @as(usize, d);
    if (x_f32_len != expected) {
        py.raiseValue("x length does not match n*d");
        return null;
    }
    const x_ptr: [*]const f32 = @ptrCast(@alignCast(x_buf.buf));

    const cap = jzip.compressBound(n, d) catch {
        py.raiseValue("invalid dims");
        return null;
    };

    const tmp = allocator.alloc(u8, cap) catch {
        py.raiseRuntime("Out of memory");
        return null;
    };
    defer allocator.free(tmp);

    const gil = c.PyEval_SaveThread();
    const actual = jzip.compressInto(allocator, ctx, x_ptr[0..x_f32_len], n, d, @as(i32, level), tmp) catch {
        c.PyEval_RestoreThread(gil);
        py.raiseRuntime("compression failed");
        return null;
    };
    c.PyEval_RestoreThread(gil);

    return c.PyBytes_FromStringAndSize(@ptrCast(tmp.ptr), @as(c.Py_ssize_t, @intCast(actual)));
}

fn py_ctx_decompress_into(_: [*c]c.PyObject, args: [*c]c.PyObject, kwds: [*c]c.PyObject) callconv(.c) [*c]c.PyObject {
    var cap_obj: [*c]c.PyObject = null;
    var blob_obj: [*c]c.PyObject = null;
    var out_obj: [*c]c.PyObject = null;

    const kwlist = [_:null]?[*:0]const u8{ "ctx", "blob", "out", null };
    if (c.PyArg_ParseTupleAndKeywords(args, kwds, "OOO", @ptrCast(@constCast(&kwlist)), &cap_obj, &blob_obj, &out_obj) == 0)
        return null;

    const ctx = getCtxFromCapsule(cap_obj) orelse {
        py.raiseType("invalid context");
        return null;
    };

    var blob_buf = std.mem.zeroes(c.Py_buffer);
    if (c.PyObject_GetBuffer(blob_obj, &blob_buf, c.PyBUF_SIMPLE) < 0) return null;
    defer c.PyBuffer_Release(&blob_buf);
    const blob_ptr: [*]const u8 = @ptrCast(blob_buf.buf);
    const blob_len: usize = @intCast(blob_buf.len);

    var out_buf = std.mem.zeroes(c.Py_buffer);
    if (c.PyObject_GetBuffer(out_obj, &out_buf, c.PyBUF_WRITABLE | c.PyBUF_FORMAT) < 0) return null;
    defer c.PyBuffer_Release(&out_buf);
    if (!checkF32Buffer(&out_buf, true)) {
        py.raiseType("out must be a writable contiguous float32 buffer");
        return null;
    }
    const out_ptr: [*]f32 = @ptrCast(@alignCast(out_buf.buf));
    const out_f32_len: usize = @as(usize, @intCast(out_buf.len)) / @sizeOf(f32);

    const gil = c.PyEval_SaveThread();
    jzip.decompressInto(allocator, ctx, blob_ptr[0..blob_len], out_ptr[0..out_f32_len]) catch {
        c.PyEval_RestoreThread(gil);
        py.raiseRuntime("decompression failed");
        return null;
    };
    c.PyEval_RestoreThread(gil);
    return py.none();
}

var module_methods = [_]c.PyMethodDef{
    .{ .ml_name = "version", .ml_meth = @ptrCast(&jzip_version), .ml_flags = c.METH_NOARGS, .ml_doc = "Return version" },
    .{ .ml_name = "header", .ml_meth = @ptrCast(&py_header), .ml_flags = c.METH_VARARGS, .ml_doc = "header(blob) -> (n, d)" },
    .{ .ml_name = "compress", .ml_meth = @ptrCast(&py_compress), .ml_flags = c.METH_VARARGS | c.METH_KEYWORDS, .ml_doc = "compress(x, n, d, level=1, threads=1) -> bytes" },
    .{ .ml_name = "decompress_into", .ml_meth = @ptrCast(&py_decompress_into), .ml_flags = c.METH_VARARGS | c.METH_KEYWORDS, .ml_doc = "decompress_into(blob, out, threads=1) -> None" },
    .{ .ml_name = "ctx_new", .ml_meth = @ptrCast(&py_ctx_new), .ml_flags = c.METH_VARARGS | c.METH_KEYWORDS, .ml_doc = "ctx_new(threads=1) -> capsule" },
    .{ .ml_name = "ctx_compress", .ml_meth = @ptrCast(&py_ctx_compress), .ml_flags = c.METH_VARARGS | c.METH_KEYWORDS, .ml_doc = "ctx_compress(ctx, x, n, d, level=1) -> bytes" },
    .{ .ml_name = "ctx_decompress_into", .ml_meth = @ptrCast(&py_ctx_decompress_into), .ml_flags = c.METH_VARARGS | c.METH_KEYWORDS, .ml_doc = "ctx_decompress_into(ctx, blob, out) -> None" },
    .{ .ml_name = null, .ml_meth = null, .ml_flags = 0, .ml_doc = null },
};

var module_def = py.PyModuleDef{
    .m_base = .{ .ob_base = py.makeBaseObject(), .m_init = null, .m_index = 0, .m_copy = null },
    .m_name = "_jzip",
    .m_doc = "Near-lossless embedding compression",
    .m_size = -1,
    .m_methods = &module_methods,
    .m_slots = null,
    .m_traverse = null,
    .m_clear = null,
    .m_free = null,
};

pub export fn PyInit__jzip() ?*c.PyObject {
    return py.moduleCreate(&module_def);
}
