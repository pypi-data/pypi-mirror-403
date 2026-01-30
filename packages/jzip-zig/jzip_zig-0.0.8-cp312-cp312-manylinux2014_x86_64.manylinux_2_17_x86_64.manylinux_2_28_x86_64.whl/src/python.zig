//! Python C API helpers for Zig

pub const c = @cImport({
    @cDefine("PY_SSIZE_T_CLEAN", {});
    @cInclude("jzip_python.h");
});

const std = @import("std");

/// Manual PyModuleDef since C macro doesn't translate
pub const PyModuleDef_Base = extern struct {
    ob_base: c.PyObject,
    m_init: ?*const fn () callconv(.c) ?*c.PyObject,
    m_index: c.Py_ssize_t,
    m_copy: ?*c.PyObject,
};

pub const PyModuleDef = extern struct {
    m_base: PyModuleDef_Base,
    m_name: ?[*:0]const u8,
    m_doc: ?[*:0]const u8,
    m_size: c.Py_ssize_t,
    m_methods: ?[*]c.PyMethodDef,
    m_slots: ?*c.PyModuleDef_Slot,
    m_traverse: ?*const fn (?*c.PyObject, c.visitproc, ?*anyopaque) callconv(.c) c_int,
    m_clear: ?*const fn (?*c.PyObject) callconv(.c) c_int,
    m_free: ?*const fn (?*anyopaque) callconv(.c) void,
};

pub fn makeBaseObject() c.PyObject {
    return std.mem.zeroes(c.PyObject);
}

pub fn moduleCreate(def: *PyModuleDef) ?*c.PyObject {
    return c.PyModule_Create(@as(*c.PyModuleDef, @ptrCast(def)));
}

pub fn none() *c.PyObject {
    // Equivalent to Py_RETURN_NONE (macro).
    return c.Py_BuildValue("");
}

pub fn raiseValue(msg: [:0]const u8) void {
    c.PyErr_SetString(c.PyExc_ValueError, msg.ptr);
}

pub fn raiseType(msg: [:0]const u8) void {
    c.PyErr_SetString(c.PyExc_TypeError, msg.ptr);
}

pub fn raiseRuntime(msg: [:0]const u8) void {
    c.PyErr_SetString(c.PyExc_RuntimeError, msg.ptr);
}
