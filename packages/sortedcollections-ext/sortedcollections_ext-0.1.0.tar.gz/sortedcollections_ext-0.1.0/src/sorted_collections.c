#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "btreemodule.h"
#include "sorted_collections.h"

static PyObject *BTreeType = NULL;

typedef struct {
    PyObject_HEAD
    PyObject *tree; /* btree.BTree */
} SortedDictObject;

typedef struct {
    PyObject_HEAD
    PyObject *tree; /* btree.BTree */
} SortedSetObject;

typedef struct {
    PyObject_HEAD
    SortedDictObject *dict;
    int kind; /* 0=keys, 1=values, 2=items */
} SortedDictViewObject;

static PyTypeObject SortedDictType;
static PyTypeObject SortedSetType;
static PyTypeObject SortedDictViewType;

/* Forward declarations for functions called before definition */
static PyObject *SortedDict_update(PyObject *self, PyObject *args, PyObject *kwds);
static PyObject *SortedList_bisect_right(PyObject *self, PyObject *args);

static PyObject *SortedDict_popitem(PyObject *self, PyObject *Py_UNUSED(ignored));
static PyObject *SortedDict_copy(PyObject *self, PyObject *Py_UNUSED(ignored));
static PyObject *SortedDict_bisect(PyObject *self, PyObject *args);
static PyObject *SortedDict_index(PyObject *self, PyObject *args);
static PyObject *SortedDict_islice(PyObject *self, PyObject *args, PyObject *kwds);
static int SortedDict_contains(PyObject *self, PyObject *key);

static PyObject *SortedSet_bisect_left(PyObject *self, PyObject *args);
static PyObject *SortedSet_bisect_right(PyObject *self, PyObject *args);
static PyObject *SortedSet_index(PyObject *self, PyObject *args);
static PyObject *SortedSet_irange(PyObject *self, PyObject *args, PyObject *kwds);
static PyObject *SortedSet_islice(PyObject *self, PyObject *args, PyObject *kwds);
static PyObject *SortedSet_union(PyObject *self, PyObject *args);
static PyObject *SortedSet_difference(PyObject *self, PyObject *args);
static PyObject *SortedSet_intersection(PyObject *self, PyObject *args);
static PyObject *SortedSet_symmetric_difference(PyObject *self, PyObject *args);
static PyObject *SortedSet_or(PyObject *self, PyObject *other);
static PyObject *SortedSet_and(PyObject *self, PyObject *other);
static PyObject *SortedSet_sub(PyObject *self, PyObject *other);
static PyObject *SortedSet_xor(PyObject *self, PyObject *other);
static PyObject *SortedDictView_new(SortedDictObject *dict, int kind);
static PyObject *SortedSet_richcompare(PyObject *self, PyObject *other, int op);

static int
sortedset_richcompare_cached(PyObject *a, PyObject *b, int op,
                             PyTypeObject **cached_type, richcmpfunc *cached_rc)
{
    if (a == b) {
        if (op == Py_EQ) {
            return 1;
        }
        if (op == Py_LT) {
            return 0;
        }
    }

    if (Py_TYPE(a) == Py_TYPE(b)) {
        PyTypeObject *type = Py_TYPE(a);
        if (*cached_type != type) {
            *cached_type = type;
            *cached_rc = type->tp_richcompare;
        }
        if (*cached_rc) {
            PyObject *res = (*cached_rc)(a, b, op);
            if (!res) {
                return -1;
            }
            if (res == Py_NotImplemented) {
                Py_DECREF(res);
                return PyObject_RichCompareBool(a, b, op);
            }
            int truth = PyObject_IsTrue(res);
            Py_DECREF(res);
            return truth;
        }
    }

    return PyObject_RichCompareBool(a, b, op);
}

static int
sortedcollections_ensure_btree(void)
{
    if (!BTreeType) {
        PyObject *btree_module = PyImport_ImportModule("btree");
        if (!btree_module) {
            return -1;
        }
        BTreeType = PyObject_GetAttrString(btree_module, "BTree");
        Py_DECREF(btree_module);
        if (!BTreeType) {
            return -1;
        }
    }
    return 0;
}

/*
 * Common helper for islice operations on SortedDict and SortedSet.
 * Returns a list of keys from the given tree within [start, stop) range.
 */
static PyObject *
_islice_common(PyObject *tree, Py_ssize_t start, Py_ssize_t stop, int reverse)
{
    Py_ssize_t length = PyObject_Length(tree);
    if (length < 0) {
        return NULL;
    }
    if (start < 0) {
        start += length;
    }
    if (stop < 0) {
        stop += length;
    }
    if (start < 0) {
        start = 0;
    }
    if (stop > length) {
        stop = length;
    }
    if (stop < start) {
        stop = start;
    }

    if (reverse) {
        Py_ssize_t r_start = start;
        Py_ssize_t r_stop = stop;
        start = length - r_stop;
        stop = length - r_start;
        if (start < 0) {
            start = 0;
        }
        if (stop > length) {
            stop = length;
        }
        if (stop < start) {
            stop = start;
        }
    }

    Py_ssize_t slicelength = stop - start;
    PyObject *list = PyList_New(slicelength);
    if (!list) {
        return NULL;
    }
    for (Py_ssize_t i = 0; i < slicelength; i++) {
        PyObject *key = PyBTree_GetItemByIndex(tree, start + i, 0);
        if (!key) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, key);  /* Steals reference */
    }
    if (reverse && slicelength > 0) {
        if (PyList_Reverse(list) < 0) {
            Py_DECREF(list);
            return NULL;
        }
    }
    return list;
}

static PyObject *
SortedDictView_iter(PyObject *self_obj)
{
    SortedDictViewObject *view = (SortedDictViewObject *)self_obj;
    const char *method = "keys";
    if (view->kind == 1) {
        method = "values";
    } else if (view->kind == 2) {
        method = "items";
    }
    return PyObject_CallMethod(view->dict->tree, method, NULL);
}

static Py_ssize_t
SortedDictView_len(PyObject *self_obj)
{
    SortedDictViewObject *view = (SortedDictViewObject *)self_obj;
    return PyObject_Length(view->dict->tree);
}

static PyObject *
SortedDictView_getitem(PyObject *self_obj, Py_ssize_t index)
{
    SortedDictViewObject *view = (SortedDictViewObject *)self_obj;
    return PyBTree_GetItemByIndex(view->dict->tree, index, view->kind);
}

static int
SortedDictView_contains(PyObject *self_obj, PyObject *item)
{
    SortedDictViewObject *view = (SortedDictViewObject *)self_obj;
    if (view->kind == 0) {
        return SortedDict_contains((PyObject *)view->dict, item);
    }
    PyObject *iter = SortedDictView_iter(self_obj);
    if (!iter) {
        return -1;
    }
    PyObject *value = NULL;
    while ((value = PyIter_Next(iter))) {
        int eq = PyObject_RichCompareBool(value, item, Py_EQ);
        Py_DECREF(value);
        if (eq < 0) {
            Py_DECREF(iter);
            return -1;
        }
        if (eq) {
            Py_DECREF(iter);
            return 1;
        }
    }
    Py_DECREF(iter);
    if (PyErr_Occurred()) {
        return -1;
    }
    return 0;
}

static void
SortedDictView_dealloc(SortedDictViewObject *view)
{
    Py_XDECREF(view->dict);
    Py_TYPE(view)->tp_free((PyObject *)view);
}

/* Reverse iterator for SortedDictView */
typedef struct {
    PyObject_HEAD
    SortedDictViewObject *view;
    Py_ssize_t index;
} SortedDictViewReverseIterObject;

static PyTypeObject SortedDictViewReverseIterType;

static void
SortedDictViewReverseIter_dealloc(SortedDictViewReverseIterObject *it)
{
    Py_XDECREF(it->view);
    Py_TYPE(it)->tp_free((PyObject *)it);
}

static PyObject *
SortedDictViewReverseIter_iternext(SortedDictViewReverseIterObject *it)
{
    if (it->index < 0) {
        return NULL;
    }
    PyObject *item = PyBTree_GetItemByIndex(it->view->dict->tree, it->index, it->view->kind);
    it->index--;
    return item;
}

static PyTypeObject SortedDictViewReverseIterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sortedcollections._SortedDictViewReverseIter",
    .tp_basicsize = sizeof(SortedDictViewReverseIterObject),
    .tp_dealloc = (destructor)SortedDictViewReverseIter_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_iter = PyObject_SelfIter,
    .tp_iternext = (iternextfunc)SortedDictViewReverseIter_iternext,
};

static PyObject *
SortedDictView_reversed(PyObject *self_obj)
{
    SortedDictViewObject *view = (SortedDictViewObject *)self_obj;
    SortedDictViewReverseIterObject *it = PyObject_New(SortedDictViewReverseIterObject, 
                                                        &SortedDictViewReverseIterType);
    if (!it) {
        return NULL;
    }
    it->view = (SortedDictViewObject *)Py_NewRef(self_obj);
    it->index = PyObject_Length(view->dict->tree) - 1;
    return (PyObject *)it;
}

static PyMethodDef SortedDictView_methods[] = {
    {"__reversed__", (PyCFunction)SortedDictView_reversed, METH_NOARGS, "Return a reverse iterator."},
    {NULL, NULL, 0, NULL}
};

static PySequenceMethods SortedDictView_as_sequence = {
    .sq_length = SortedDictView_len,
    .sq_item = SortedDictView_getitem,
    .sq_contains = SortedDictView_contains,
};

static PyTypeObject SortedDictViewType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sortedcollections._SortedDictView",
    .tp_basicsize = sizeof(SortedDictViewObject),
    .tp_dealloc = (destructor)SortedDictView_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_iter = SortedDictView_iter,
    .tp_as_sequence = &SortedDictView_as_sequence,
    .tp_methods = SortedDictView_methods,
};

static PyObject *
SortedDictView_new(SortedDictObject *dict, int kind)
{
    SortedDictViewObject *view = PyObject_New(SortedDictViewObject, &SortedDictViewType);
    if (!view) {
        return NULL;
    }
    view->dict = (SortedDictObject *)Py_NewRef((PyObject *)dict);
    view->kind = kind;
    return (PyObject *)view;
}
static PyObject *
SortedDict_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    SortedDictObject *self = (SortedDictObject *)type->tp_alloc(type, 0);
    if (!self) {
        return NULL;
    }
    self->tree = NULL;
    return (PyObject *)self;
}

static int
SortedDict_init(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    PyObject *iterable = NULL;
    PyObject *btree_obj = NULL;
    PyObject *update_args = NULL;
    PyObject *update_result = NULL;

    if (!PyArg_UnpackTuple(args, "SortedDict", 0, 1, &iterable)) {
        return -1;
    }

    if (sortedcollections_ensure_btree() < 0) {
        return -1;
    }

    btree_obj = PyObject_CallObject(BTreeType, NULL);
    if (!btree_obj) {
        return -1;
    }

    Py_XDECREF(self->tree);
    self->tree = btree_obj;

    if (iterable) {
        update_args = PyTuple_Pack(1, iterable);
        if (!update_args) {
            return -1;
        }
        update_result = SortedDict_update(self_obj, update_args, NULL);
        Py_DECREF(update_args);
        if (!update_result) {
            return -1;
        }
        Py_DECREF(update_result);
    }

    if (kwds && PyDict_Size(kwds) > 0) {
        update_args = PyTuple_New(0);
        if (!update_args) {
            return -1;
        }
        update_result = SortedDict_update(self_obj, update_args, kwds);
        Py_DECREF(update_args);
        if (!update_result) {
            return -1;
        }
        Py_DECREF(update_result);
    }

    return 0;
}

static void
SortedDict_dealloc(SortedDictObject *self)
{
    Py_XDECREF(self->tree);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
SortedSet_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    SortedSetObject *self = (SortedSetObject *)type->tp_alloc(type, 0);
    if (!self) {
        return NULL;
    }
    self->tree = NULL;
    return (PyObject *)self;
}

static int
SortedSet_init(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *iterable = NULL;
    PyObject *btree_obj = NULL;

    if (kwds && PyDict_Size(kwds) > 0) {
        PyErr_SetString(PyExc_TypeError, "SortedSet does not accept keyword arguments");
        return -1;
    }

    if (!PyArg_UnpackTuple(args, "SortedSet", 0, 1, &iterable)) {
        return -1;
    }

    if (sortedcollections_ensure_btree() < 0) {
        return -1;
    }

    btree_obj = PyObject_CallObject(BTreeType, NULL);
    if (!btree_obj) {
        return -1;
    }

    Py_XDECREF(self->tree);
    self->tree = btree_obj;

    if (iterable) {
        if (Py_EnterRecursiveCall(" in SortedSet_init")) {
            return -1;
        }
        PyObject *iter = PyObject_GetIter(iterable);
        if (!iter) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        PyObject *item = NULL;
        while ((item = PyIter_Next(iter))) {
            if (PyBTree_Insert(self->tree, item, Py_None) < 0) {
                Py_DECREF(item);
                Py_DECREF(iter);
                Py_LeaveRecursiveCall();
                return -1;
            }
            Py_DECREF(item);
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        Py_LeaveRecursiveCall();
    }

    return 0;
}

static void
SortedSet_dealloc(SortedSetObject *self)
{
    Py_XDECREF(self->tree);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
SortedDict_getitem(PyObject *self_obj, PyObject *key)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    return PyBTree_Search(self->tree, key);
}

static int
SortedDict_contains(PyObject *self_obj, PyObject *key)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    PyObject *value = PyBTree_Search(self->tree, key);
    if (value) {
        Py_DECREF(value);
        return 1;
    }
    if (PyErr_ExceptionMatches(PyExc_KeyError)) {
        PyErr_Clear();
        return 0;
    }
    return -1;
}

static int
SortedDict_setitem(PyObject *self_obj, PyObject *key, PyObject *value)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    if (!value) {
        return PyBTree_Delete(self->tree, key);
    }
    return PyBTree_Insert(self->tree, key, value);
}

static int
SortedDict_delitem(PyObject *self_obj, PyObject *key)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    return PyBTree_Delete(self->tree, key);
}

static Py_ssize_t
SortedDict_len(PyObject *self_obj)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    return PyObject_Length(self->tree);
}

static PyObject *
SortedDict_setdefault(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"key", "default", NULL};
    PyObject *key = NULL;
    PyObject *default_value = Py_None;
    SortedDictObject *self = (SortedDictObject *)self_obj;
    PyObject *value = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist, &key, &default_value)) {
        return NULL;
    }

    value = PyBTree_Search(self->tree, key);
    if (value) {
        return value;
    }
    if (!PyErr_ExceptionMatches(PyExc_KeyError)) {
        return NULL;
    }
    PyErr_Clear();

    if (PyBTree_Insert(self->tree, key, default_value) < 0) {
        return NULL;
    }

    return Py_NewRef(default_value);
}

static int
SortedDict_update_from_iterable(SortedDictObject *self, PyObject *iterable)
{
    if (Py_EnterRecursiveCall(" in SortedDict_update_from_iterable")) {
        return -1;
    }
    PyObject *iter = PyObject_GetIter(iterable);
    if (!iter) {
        Py_LeaveRecursiveCall();
        return -1;
    }

    PyObject *item = NULL;
    while ((item = PyIter_Next(iter))) {
        PyObject *fast = PySequence_Fast(item, "update sequence element is not a 2-item sequence");
        if (!fast) {
            Py_DECREF(item);
            Py_DECREF(iter);
            Py_LeaveRecursiveCall();
            return -1;
        }
        if (PySequence_Fast_GET_SIZE(fast) != 2) {
            Py_DECREF(item);
            Py_DECREF(iter);
            Py_DECREF(fast);
            PyErr_SetString(PyExc_ValueError, "update sequence element has length != 2");
            Py_LeaveRecursiveCall();
            return -1;
        }
        PyObject *key = PySequence_Fast_GET_ITEM(fast, 0);
        PyObject *value = PySequence_Fast_GET_ITEM(fast, 1);
        if (PyBTree_Insert(self->tree, key, value) < 0) {
            Py_DECREF(item);
            Py_DECREF(iter);
            Py_DECREF(fast);
            Py_LeaveRecursiveCall();
            return -1;
        }
        Py_DECREF(item);
        Py_DECREF(fast);
    }

    Py_DECREF(iter);
    if (PyErr_Occurred()) {
        Py_LeaveRecursiveCall();
        return -1;
    }
    Py_LeaveRecursiveCall();
    return 0;
}

static int
SortedDict_update_from_mapping(SortedDictObject *self, PyObject *mapping)
{
    PyObject *items = PyMapping_Items(mapping);
    if (!items) {
        return -1;
    }
    int result = SortedDict_update_from_iterable(self, items);
    Py_DECREF(items);
    return result;
}

static PyObject *
SortedDict_update(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    Py_ssize_t nargs = PyTuple_GET_SIZE(args);

    if (nargs > 1) {
        PyErr_SetString(PyExc_TypeError, "update expected at most 1 positional argument");
        return NULL;
    }

    if (nargs == 1) {
        PyObject *arg = PyTuple_GET_ITEM(args, 0);
        int is_mapping = 0;
        /* Check if arg has an 'items' attribute to determine if it's a mapping.
         * Using PyObject_GetAttr avoids the double lookup of HasAttrString. */
        if (PyMapping_Check(arg)) {
            PyObject *items_attr = PyObject_GetAttrString(arg, "items");
            if (items_attr) {
                is_mapping = 1;
                Py_DECREF(items_attr);
            } else {
                /* No 'items' attribute - treat as iterable, clear the AttributeError */
                if (PyErr_ExceptionMatches(PyExc_AttributeError)) {
                    PyErr_Clear();
                } else {
                    return NULL;  /* Propagate other errors */
                }
            }
        }
        if (is_mapping) {
            if (SortedDict_update_from_mapping(self, arg) < 0) {
                return NULL;
            }
        } else {
            if (SortedDict_update_from_iterable(self, arg) < 0) {
                return NULL;
            }
        }
    }

    if (kwds && PyDict_Size(kwds) > 0) {
        PyObject *key = NULL;
        PyObject *value = NULL;
        Py_ssize_t pos = 0;
        while (PyDict_Next(kwds, &pos, &key, &value)) {
            if (PyBTree_Insert(self->tree, key, value) < 0) {
                return NULL;
            }
        }
    }

    Py_RETURN_NONE;
}

static PyObject *
SortedDict_pop(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"key", "default", NULL};
    PyObject *key = NULL;
    PyObject *default_value = NULL;
    SortedDictObject *self = (SortedDictObject *)self_obj;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist, &key, &default_value)) {
        return NULL;
    }

    PyObject *value = PyBTree_Search(self->tree, key);
    if (!value) {
        if (!PyErr_ExceptionMatches(PyExc_KeyError)) {
            return NULL;
        }
        PyErr_Clear();
        if (default_value) {
            return Py_NewRef(default_value);
        }
        PyErr_SetObject(PyExc_KeyError, key);
        return NULL;
    }

    if (PyBTree_Delete(self->tree, key) < 0) {
        Py_DECREF(value);
        return NULL;
    }

    return value;
}

static PyObject *
SortedDict_get(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"key", "default", NULL};
    PyObject *key = NULL;
    PyObject *default_value = Py_None;
    SortedDictObject *self = (SortedDictObject *)self_obj;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|O", kwlist, &key, &default_value)) {
        return NULL;
    }

    PyObject *value = PyBTree_Search(self->tree, key);
    if (value) {
        return value;
    }

    if (!PyErr_ExceptionMatches(PyExc_KeyError)) {
        return NULL;
    }
    PyErr_Clear();
    return Py_NewRef(default_value);
}

static PyObject *
SortedDict_clear(PyObject *self_obj, PyObject *Py_UNUSED(ignored))
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    PyObject *result = PyObject_CallMethod(self->tree, "clear", NULL);
    if (!result) {
        return NULL;
    }
    Py_DECREF(result);
    Py_RETURN_NONE;
}

static PyObject *
SortedDict_peekitem(PyObject *self_obj, PyObject *args)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    Py_ssize_t index = 0;
    Py_ssize_t size = 0;

    if (!PyArg_ParseTuple(args, "|n", &index)) {
        return NULL;
    }

    size = PyObject_Length(self->tree);
    if (size < 0) {
        return NULL;
    }
    if (size == 0) {
        PyErr_SetString(PyExc_KeyError, "peek from empty SortedDict");
        return NULL;
    }

    if (index < 0) {
        index += size;
    }
    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "peek index out of range");
        return NULL;
    }

    /* O(log n) access using subtree_size-based indexing */
    PyObject *item = PyBTree_GetItemByIndex(self->tree, index, 2);  /* kind=2 for items */
    return item;  /* Already returns a tuple (key, value) */
}

static PyObject *
SortedDict_keys(PyObject *self_obj, PyObject *Py_UNUSED(ignored))
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    return SortedDictView_new(self, 0);
}

static PyObject *
SortedDict_items(PyObject *self_obj, PyObject *Py_UNUSED(ignored))
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    return SortedDictView_new(self, 2);
}

static PyObject *
SortedDict_values(PyObject *self_obj, PyObject *Py_UNUSED(ignored))
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    return SortedDictView_new(self, 1);
}

static PyObject *
SortedDict_copy(PyObject *self_obj, PyObject *Py_UNUSED(ignored))
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    
    /* Create new SortedDict and use O(n) tree copy instead of O(n log n) insert */
    SortedDictObject *copy = (SortedDictObject *)SortedDict_new(&SortedDictType, NULL, NULL);
    if (!copy) {
        return NULL;
    }

    if (sortedcollections_ensure_btree() < 0) {
        Py_DECREF(copy);
        return NULL;
    }

    /* Use optimized O(n) tree copy */
    PyObject *new_tree = PyBTree_Copy(self->tree);
    if (!new_tree) {
        Py_DECREF(copy);
        return NULL;
    }

    copy->tree = new_tree;
    return (PyObject *)copy;
}

static PyObject *
SortedDict_popitem(PyObject *self_obj, PyObject *args)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    Py_ssize_t index = -1;
    if (!PyArg_ParseTuple(args, "|n", &index)) {
        return NULL;
    }

    Py_ssize_t size = PyObject_Length(self->tree);
    if (size < 0) {
        return NULL;
    }
    if (size == 0) {
        PyErr_SetString(PyExc_KeyError, "popitem from empty SortedDict");
        return NULL;
    }
    if (index < 0) {
        index += size;
    }
    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "popitem index out of range");
        return NULL;
    }

    /* O(log n) access using subtree_size-based indexing */
    PyObject *key = PyBTree_GetItemByIndex(self->tree, index, 0);  /* kind=0 for key */
    if (!key) {
        return NULL;
    }

    PyObject *value = PyBTree_GetItemByIndex(self->tree, index, 1);  /* kind=1 for value */
    if (!value) {
        Py_DECREF(key);
        return NULL;
    }

    if (SortedDict_delitem(self_obj, key) < 0) {
        Py_DECREF(key);
        Py_DECREF(value);
        return NULL;
    }

    PyObject *item = PyTuple_Pack(2, key, value);
    Py_DECREF(key);
    Py_DECREF(value);
    return item;
}

static PyObject *
SortedDict_fromkeys(PyObject *cls, PyObject *args)
{
    PyObject *iterable = NULL;
    PyObject *value = Py_None;

    if (!PyArg_ParseTuple(args, "O|O", &iterable, &value)) {
        return NULL;
    }

    PyObject *obj = PyObject_CallObject(cls, NULL);
    if (!obj) {
        return NULL;
    }

    PyObject *iter = PyObject_GetIter(iterable);
    if (!iter) {
        Py_DECREF(obj);
        return NULL;
    }

    PyObject *item = NULL;
    while ((item = PyIter_Next(iter))) {
        if (PyBTree_Insert(((SortedDictObject *)obj)->tree, item, value) < 0) {
            Py_DECREF(item);
            Py_DECREF(iter);
            Py_DECREF(obj);
            return NULL;
        }
        Py_DECREF(item);
    }
    Py_DECREF(iter);

    if (PyErr_Occurred()) {
        Py_DECREF(obj);
        return NULL;
    }

    return obj;
}

static PyObject *
SortedDict_repr(PyObject *self_obj)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    PyObject *iter = PyObject_CallMethod(self->tree, "items", NULL);
    if (!iter) {
        return NULL;
    }
    PyObject *items = PySequence_List(iter);
    Py_DECREF(iter);
    if (!items) {
        return NULL;
    }
    PyObject *repr = PyUnicode_FromFormat("SortedDict(%R)", items);
    Py_DECREF(items);
    return repr;
}

static PyObject *
SortedDict_iter(PyObject *self_obj)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    return PyObject_CallMethod(self->tree, "keys", NULL);
}

static PyObject *
SortedDict_bisect(PyObject *self_obj, PyObject *args)
{
    return SortedList_bisect_right(self_obj, args);
}

static PyObject *
SortedDict_index(PyObject *self_obj, PyObject *args)
{
    PyObject *key = NULL;
    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }
    PyObject *idx = PyObject_CallMethod(((SortedDictObject *)self_obj)->tree, "bisect_left", "O", key);
    if (!idx) {
        return NULL;
    }
    PyObject *value = PyBTree_Search(((SortedDictObject *)self_obj)->tree, key);
    if (!value) {
        Py_DECREF(idx);
        if (PyErr_ExceptionMatches(PyExc_KeyError)) {
            PyErr_Clear();
            PyErr_SetString(PyExc_ValueError, "key not in SortedDict");
        }
        return NULL;
    }
    Py_DECREF(value);
    return idx;
}

static PyObject *
SortedDict_islice(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"start", "stop", "reverse", NULL};
    Py_ssize_t start = 0;
    Py_ssize_t stop = PY_SSIZE_T_MAX;
    int reverse = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|nnp", kwlist, &start, &stop, &reverse)) {
        return NULL;
    }

    return _islice_common(((SortedDictObject *)self_obj)->tree, start, stop, reverse);
}
static PyObject *
SortedList_bisect_left(PyObject *self_obj, PyObject *args)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    PyObject *key = NULL;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    Py_ssize_t idx = PyBTree_BisectLeft(self->tree, key);
    if (idx < 0 && PyErr_Occurred()) {
        return NULL;
    }
    return PyLong_FromSsize_t(idx);
}

static PyObject *
SortedList_bisect_right(PyObject *self_obj, PyObject *args)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    PyObject *key = NULL;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    Py_ssize_t idx = PyBTree_BisectRight(self->tree, key);
    if (idx < 0 && PyErr_Occurred()) {
        return NULL;
    }
    return PyLong_FromSsize_t(idx);
}

static PyObject *
SortedList_irange(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    SortedDictObject *self = (SortedDictObject *)self_obj;
    static char *kwlist[] = {"min", "max", "inclusive", "reverse", NULL};
    PyObject *min = Py_None;
    PyObject *max = Py_None;
    PyObject *inclusive = Py_None;
    int reverse = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOp", kwlist, &min, &max, &inclusive, &reverse)) {
        return NULL;
    }

    PyObject *list = PyBTree_IRange(self->tree, min, max, inclusive);
    if (!list) {
        return NULL;
    }
    if (reverse) {
        if (PyList_Reverse(list) < 0) {
            Py_DECREF(list);
            return NULL;
        }
    }
    return list;
}

static PyObject *
SortedSet_add(PyObject *self_obj, PyObject *key)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    if (PyBTree_Insert(self->tree, key, Py_None) < 0) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *
sortedset_key_at(SortedSetObject *self, Py_ssize_t index)
{
    return PyBTree_GetItemByIndex(self->tree, index, 0);
}

static PyObject *
SortedSet_remove(PyObject *self_obj, PyObject *key)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    if (PyBTree_Delete(self->tree, key) < 0) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *
SortedSet_discard(PyObject *self_obj, PyObject *key)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    if (PyBTree_Delete(self->tree, key) < 0) {
        if (PyErr_ExceptionMatches(PyExc_KeyError)) {
            PyErr_Clear();
            Py_RETURN_NONE;
        }
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *
SortedSet_repr(PyObject *self_obj)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *iter = PyObject_CallMethod(self->tree, "keys", NULL);
    if (!iter) {
        return NULL;
    }
    PyObject *keys_list = PySequence_List(iter);
    Py_DECREF(iter);
    if (!keys_list) {
        return NULL;
    }
    PyObject *repr = PyUnicode_FromFormat("SortedSet(%R)", keys_list);
    Py_DECREF(keys_list);
    return repr;
}

static PyObject *
SortedSet_bisect_left(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *key = NULL;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    Py_ssize_t idx = PyBTree_BisectLeft(self->tree, key);
    if (idx < 0 && PyErr_Occurred()) {
        return NULL;
    }
    return PyLong_FromSsize_t(idx);
}

static PyObject *
SortedSet_bisect_right(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *key = NULL;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    Py_ssize_t idx = PyBTree_BisectRight(self->tree, key);
    if (idx < 0 && PyErr_Occurred()) {
        return NULL;
    }
    return PyLong_FromSsize_t(idx);
}

static PyObject *
SortedSet_index(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *key = NULL;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    PyObject *idx = PyObject_CallMethod(self->tree, "bisect_left", "O", key);
    if (!idx) {
        return NULL;
    }
    PyObject *value = PyBTree_Search(self->tree, key);
    if (!value) {
        Py_DECREF(idx);
        if (PyErr_ExceptionMatches(PyExc_KeyError)) {
            PyErr_Clear();
            PyErr_SetString(PyExc_ValueError, "key not in SortedSet");
        }
        return NULL;
    }
    Py_DECREF(value);
    return idx;
}

static PyObject *
SortedSet_irange(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    static char *kwlist[] = {"min", "max", "inclusive", "reverse", NULL};
    PyObject *min = Py_None;
    PyObject *max = Py_None;
    PyObject *inclusive = Py_None;
    int reverse = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOp", kwlist, &min, &max, &inclusive, &reverse)) {
        return NULL;
    }

    PyObject *list = PyBTree_IRange(self->tree, min, max, inclusive);
    if (!list) {
        return NULL;
    }
    if (reverse) {
        if (PyList_Reverse(list) < 0) {
            Py_DECREF(list);
            return NULL;
        }
    }
    return list;
}

static PyObject *
SortedSet_islice(PyObject *self_obj, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"start", "stop", "reverse", NULL};
    Py_ssize_t start = 0;
    Py_ssize_t stop = PY_SSIZE_T_MAX;
    int reverse = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|nnp", kwlist, &start, &stop, &reverse)) {
        return NULL;
    }

    return _islice_common(((SortedSetObject *)self_obj)->tree, start, stop, reverse);
}

static PyObject *
SortedSet_pop(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    Py_ssize_t index = -1;
    if (!PyArg_ParseTuple(args, "|n", &index)) {
        return NULL;
    }

    PyObject *key = sortedset_key_at(self, index);
    if (!key) {
        return NULL;
    }

    if (PyBTree_Delete(self->tree, key) < 0) {
        Py_DECREF(key);
        return NULL;
    }

    return key;
}

static int
SortedSet_contains(PyObject *self_obj, PyObject *key)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *value = PyBTree_Search(self->tree, key);
    if (value) {
        Py_DECREF(value);
        return 1;
    }
    if (PyErr_ExceptionMatches(PyExc_KeyError)) {
        PyErr_Clear();
        return 0;
    }
    return -1;
}

static PyObject *
SortedSet_union(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    
    /* Start with a copy of self's tree */
    PyObject *result_tree = PyBTree_Copy(self->tree);
    if (!result_tree) {
        return NULL;
    }

    /* Iteratively merge each argument */
    for (Py_ssize_t i = 0; i < nargs; i++) {
        PyObject *arg = PyTuple_GET_ITEM(args, i);
        
        if (PyObject_TypeCheck(arg, &SortedSetType)) {
            /* Fast path: merge two sorted trees */
            SortedSetObject *other = (SortedSetObject *)arg;
            PyObject *merged = PyBTree_MergeUnion(result_tree, other->tree);
            Py_DECREF(result_tree);
            if (!merged) {
                return NULL;
            }
            result_tree = merged;
        } else {
            /* Slow path: insert items one by one */
            if (Py_EnterRecursiveCall(" in SortedSet_union")) {
                Py_DECREF(result_tree);
                return NULL;
            }
            PyObject *iter = PyObject_GetIter(arg);
            if (!iter) {
                Py_LeaveRecursiveCall();
                Py_DECREF(result_tree);
                return NULL;
            }
            PyObject *item = NULL;
            while ((item = PyIter_Next(iter))) {
                if (PyBTree_Insert(result_tree, item, Py_None) < 0) {
                    Py_DECREF(item);
                    Py_DECREF(iter);
                    Py_LeaveRecursiveCall();
                    Py_DECREF(result_tree);
                    return NULL;
                }
                Py_DECREF(item);
            }
            Py_DECREF(iter);
            Py_LeaveRecursiveCall();
            if (PyErr_Occurred()) {
                Py_DECREF(result_tree);
                return NULL;
            }
        }
    }

    /* Create result SortedSet and assign the tree */
    PyObject *result = PyObject_CallObject((PyObject *)&SortedSetType, NULL);
    if (!result) {
        Py_DECREF(result_tree);
        return NULL;
    }
    Py_DECREF(((SortedSetObject *)result)->tree);
    ((SortedSetObject *)result)->tree = result_tree;
    return result;
}

static PyObject *
SortedSet_difference(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *result = PyObject_CallObject((PyObject *)&SortedSetType, NULL);
    if (!result) {
        return NULL;
    }

    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    if (nargs == 1 && PyObject_TypeCheck(PyTuple_GET_ITEM(args, 0), &SortedSetType)) {
        SortedSetObject *other = (SortedSetObject *)PyTuple_GET_ITEM(args, 0);
        PyObject *merged = PyBTree_MergeDifference(self->tree, other->tree);
        if (!merged) {
            Py_DECREF(result);
            return NULL;
        }
        Py_DECREF(((SortedSetObject *)result)->tree);
        ((SortedSetObject *)result)->tree = merged;
        return result;
    }

    PyObject *other_set = PySet_New(NULL);
    if (!other_set) {
        Py_DECREF(result);
        return NULL;
    }
    for (Py_ssize_t i = 0; i < nargs; i++) {
        if (Py_EnterRecursiveCall(" in SortedSet_difference")) {
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        PyObject *iterable = PyTuple_GET_ITEM(args, i);
        PyObject *iter = PyObject_GetIter(iterable);
        if (!iter) {
            Py_LeaveRecursiveCall();
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        PyObject *item = NULL;
        while ((item = PyIter_Next(iter))) {
            if (PySet_Add(other_set, item) < 0) {
                Py_DECREF(item);
                Py_DECREF(iter);
                Py_LeaveRecursiveCall();
                Py_DECREF(other_set);
                Py_DECREF(result);
                return NULL;
            }
            Py_DECREF(item);
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) {
            Py_LeaveRecursiveCall();
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        Py_LeaveRecursiveCall();
    }

    PyObject *iter_keys = PyObject_CallMethod(self->tree, "keys", NULL);
    if (!iter_keys) {
        Py_DECREF(other_set);
        Py_DECREF(result);
        return NULL;
    }
    PyObject *key = NULL;
    while ((key = PyIter_Next(iter_keys))) {
        int contains = PySet_Contains(other_set, key);
        if (contains < 0) {
            Py_DECREF(key);
            Py_DECREF(iter_keys);
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        if (!contains) {
            if (PyBTree_Insert(((SortedSetObject *)result)->tree, key, Py_None) < 0) {
                Py_DECREF(key);
                Py_DECREF(iter_keys);
                Py_DECREF(other_set);
                Py_DECREF(result);
                return NULL;
            }
        }
        Py_DECREF(key);
    }
    Py_DECREF(iter_keys);
    if (PyErr_Occurred()) {
        Py_DECREF(other_set);
        Py_DECREF(result);
        return NULL;
    }
    Py_DECREF(other_set);
    return result;
}

static PyObject *
SortedSet_intersection(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *result = PyObject_CallObject((PyObject *)&SortedSetType, NULL);
    if (!result) {
        return NULL;
    }

    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    if (nargs == 1 && PyObject_TypeCheck(PyTuple_GET_ITEM(args, 0), &SortedSetType)) {
        SortedSetObject *other = (SortedSetObject *)PyTuple_GET_ITEM(args, 0);
        PyObject *merged = PyBTree_MergeIntersection(self->tree, other->tree);
        if (!merged) {
            Py_DECREF(result);
            return NULL;
        }
        Py_DECREF(((SortedSetObject *)result)->tree);
        ((SortedSetObject *)result)->tree = merged;
        return result;
    }

    PyObject *other_set = PySet_New(NULL);
    if (!other_set) {
        Py_DECREF(result);
        return NULL;
    }
    for (Py_ssize_t i = 0; i < nargs; i++) {
        if (Py_EnterRecursiveCall(" in SortedSet_intersection")) {
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        PyObject *iterable = PyTuple_GET_ITEM(args, i);
        PyObject *iter = PyObject_GetIter(iterable);
        if (!iter) {
            Py_LeaveRecursiveCall();
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        PyObject *item = NULL;
        while ((item = PyIter_Next(iter))) {
            if (PySet_Add(other_set, item) < 0) {
                Py_DECREF(item);
                Py_DECREF(iter);
                Py_LeaveRecursiveCall();
                Py_DECREF(other_set);
                Py_DECREF(result);
                return NULL;
            }
            Py_DECREF(item);
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) {
            Py_LeaveRecursiveCall();
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        Py_LeaveRecursiveCall();
    }

    PyObject *iter_keys = PyObject_CallMethod(self->tree, "keys", NULL);
    if (!iter_keys) {
        Py_DECREF(other_set);
        Py_DECREF(result);
        return NULL;
    }
    PyObject *key = NULL;
    while ((key = PyIter_Next(iter_keys))) {
        int contains = PySet_Contains(other_set, key);
        if (contains < 0) {
            Py_DECREF(key);
            Py_DECREF(iter_keys);
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        if (contains) {
            if (PyBTree_Insert(((SortedSetObject *)result)->tree, key, Py_None) < 0) {
                Py_DECREF(key);
                Py_DECREF(iter_keys);
                Py_DECREF(other_set);
                Py_DECREF(result);
                return NULL;
            }
        }
        Py_DECREF(key);
    }
    Py_DECREF(iter_keys);
    if (PyErr_Occurred()) {
        Py_DECREF(other_set);
        Py_DECREF(result);
        return NULL;
    }
    Py_DECREF(other_set);
    return result;
}

static PyObject *
SortedSet_symmetric_difference(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *result = PyObject_CallObject((PyObject *)&SortedSetType, NULL);
    if (!result) {
        return NULL;
    }

    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    if (nargs == 1 && PyObject_TypeCheck(PyTuple_GET_ITEM(args, 0), &SortedSetType)) {
        SortedSetObject *other = (SortedSetObject *)PyTuple_GET_ITEM(args, 0);
        PyTypeObject *cached_type = NULL;
        richcmpfunc cached_rc = NULL;
        PyObject *iter_a = PyBTree_IterNew(self->tree, 0);
        PyObject *iter_b = PyBTree_IterNew(other->tree, 0);
        if (!iter_a || !iter_b) {
            Py_XDECREF(iter_a);
            Py_XDECREF(iter_b);
            Py_DECREF(result);
            return NULL;
        }
        PyObject *a = PyBTree_IterNext(iter_a);
        PyObject *b = PyBTree_IterNext(iter_b);
        while (a || b) {
            if (!b) {
                if (PyBTree_Insert(((SortedSetObject *)result)->tree, a, Py_None) < 0) {
                    Py_DECREF(a);
                    Py_DECREF(iter_a);
                    Py_DECREF(iter_b);
                    Py_DECREF(result);
                    return NULL;
                }
                Py_DECREF(a);
                a = PyBTree_IterNext(iter_a);
                continue;
            }
            if (!a) {
                if (PyBTree_Insert(((SortedSetObject *)result)->tree, b, Py_None) < 0) {
                    Py_DECREF(b);
                    Py_DECREF(iter_a);
                    Py_DECREF(iter_b);
                    Py_DECREF(result);
                    return NULL;
                }
                Py_DECREF(b);
                b = PyBTree_IterNext(iter_b);
                continue;
            }
            int lt = sortedset_richcompare_cached(a, b, Py_LT, &cached_type, &cached_rc);
            if (lt < 0) {
                Py_DECREF(a);
                Py_DECREF(b);
                Py_DECREF(iter_a);
                Py_DECREF(iter_b);
                Py_DECREF(result);
                return NULL;
            }
            if (lt) {
                if (PyBTree_Insert(((SortedSetObject *)result)->tree, a, Py_None) < 0) {
                    Py_DECREF(a);
                    Py_DECREF(b);
                    Py_DECREF(iter_a);
                    Py_DECREF(iter_b);
                    Py_DECREF(result);
                    return NULL;
                }
                Py_DECREF(a);
                a = PyBTree_IterNext(iter_a);
            } else {
                int eq = sortedset_richcompare_cached(a, b, Py_EQ, &cached_type, &cached_rc);
                if (eq < 0) {
                    Py_DECREF(a);
                    Py_DECREF(b);
                    Py_DECREF(iter_a);
                    Py_DECREF(iter_b);
                    Py_DECREF(result);
                    return NULL;
                }
                if (eq) {
                    Py_DECREF(a);
                    Py_DECREF(b);
                    a = PyBTree_IterNext(iter_a);
                    b = PyBTree_IterNext(iter_b);
                } else {
                    if (PyBTree_Insert(((SortedSetObject *)result)->tree, b, Py_None) < 0) {
                        Py_DECREF(a);
                        Py_DECREF(b);
                        Py_DECREF(iter_a);
                        Py_DECREF(iter_b);
                        Py_DECREF(result);
                        return NULL;
                    }
                    Py_DECREF(b);
                    b = PyBTree_IterNext(iter_b);
                }
            }
        }
        Py_DECREF(iter_a);
        Py_DECREF(iter_b);
        if (PyErr_Occurred()) {
            Py_DECREF(result);
            return NULL;
        }
        return result;
    }

    PyObject *other_set = PySet_New(NULL);
    if (!other_set) {
        Py_DECREF(result);
        return NULL;
    }

    for (Py_ssize_t i = 0; i < nargs; i++) {
        if (Py_EnterRecursiveCall(" in SortedSet_symmetric_difference")) {
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        PyObject *iterable = PyTuple_GET_ITEM(args, i);
        PyObject *iter = PyObject_GetIter(iterable);
        if (!iter) {
            Py_LeaveRecursiveCall();
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        PyObject *item = NULL;
        while ((item = PyIter_Next(iter))) {
            if (PySet_Add(other_set, item) < 0) {
                Py_DECREF(item);
                Py_DECREF(iter);
                Py_LeaveRecursiveCall();
                Py_DECREF(other_set);
                Py_DECREF(result);
                return NULL;
            }
            Py_DECREF(item);
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) {
            Py_LeaveRecursiveCall();
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        Py_LeaveRecursiveCall();
    }

    PyObject *iter_keys = PyObject_CallMethod(self->tree, "keys", NULL);
    if (!iter_keys) {
        Py_DECREF(other_set);
        Py_DECREF(result);
        return NULL;
    }
    PyObject *key = NULL;
    while ((key = PyIter_Next(iter_keys))) {
        int contains = PySet_Contains(other_set, key);
        if (contains < 0) {
            Py_DECREF(key);
            Py_DECREF(iter_keys);
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        if (!contains) {
            if (PyBTree_Insert(((SortedSetObject *)result)->tree, key, Py_None) < 0) {
                Py_DECREF(key);
                Py_DECREF(iter_keys);
                Py_DECREF(other_set);
                Py_DECREF(result);
                return NULL;
            }
        }
        Py_DECREF(key);
    }
    Py_DECREF(iter_keys);
    if (PyErr_Occurred()) {
        Py_DECREF(other_set);
        Py_DECREF(result);
        return NULL;
    }
    PyObject *other_iter = PyObject_GetIter(other_set);
    if (!other_iter) {
        Py_DECREF(other_set);
        Py_DECREF(result);
        return NULL;
    }
    while ((key = PyIter_Next(other_iter))) {
        int contains = PySequence_Contains((PyObject *)self, key);
        if (contains < 0) {
            Py_DECREF(key);
            Py_DECREF(other_iter);
            Py_DECREF(other_set);
            Py_DECREF(result);
            return NULL;
        }
        if (!contains) {
            if (PyBTree_Insert(((SortedSetObject *)result)->tree, key, Py_None) < 0) {
                Py_DECREF(key);
                Py_DECREF(other_iter);
                Py_DECREF(other_set);
                Py_DECREF(result);
                return NULL;
            }
        }
        Py_DECREF(key);
    }
    Py_DECREF(other_iter);
    if (PyErr_Occurred()) {
        Py_DECREF(other_set);
        Py_DECREF(result);
        return NULL;
    }
    Py_DECREF(other_set);
    return result;
}

static int
SortedSet_update_internal(SortedSetObject *self, PyObject *args, int op)
{
    PyObject *result = NULL;
    switch (op) {
        case 0:
            result = SortedSet_union((PyObject *)self, args);
            break;
        case 1:
            result = SortedSet_difference((PyObject *)self, args);
            break;
        case 2:
            result = SortedSet_intersection((PyObject *)self, args);
            break;
        case 3:
            result = SortedSet_symmetric_difference((PyObject *)self, args);
            break;
        default:
            PyErr_SetString(PyExc_ValueError, "invalid update op");
            return -1;
    }
    if (!result) {
        return -1;
    }
    PyObject *new_tree = PyObject_CallObject(BTreeType, NULL);
    if (!new_tree) {
        Py_DECREF(result);
        return -1;
    }
    PyObject *iter = PyObject_CallMethod(((SortedSetObject *)result)->tree, "keys", NULL);
    if (!iter) {
        Py_DECREF(result);
        Py_DECREF(new_tree);
        return -1;
    }
    PyObject *key = NULL;
    while ((key = PyIter_Next(iter))) {
        if (PyBTree_Insert(new_tree, key, Py_None) < 0) {
            Py_DECREF(key);
            Py_DECREF(iter);
            Py_DECREF(result);
            Py_DECREF(new_tree);
            return -1;
        }
        Py_DECREF(key);
    }
    Py_DECREF(iter);
    if (PyErr_Occurred()) {
        Py_DECREF(result);
        Py_DECREF(new_tree);
        return -1;
    }
    Py_DECREF(result);

    Py_DECREF(self->tree);
    self->tree = new_tree;
    return 0;
}

static PyObject *
SortedSet_update(PyObject *self_obj, PyObject *args)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    for (Py_ssize_t i = 0; i < nargs; i++) {
        if (Py_EnterRecursiveCall(" in SortedSet_update")) {
            return NULL;
        }
        PyObject *iterable = PyTuple_GET_ITEM(args, i);
        PyObject *iter = PyObject_GetIter(iterable);
        if (!iter) {
            Py_LeaveRecursiveCall();
            return NULL;
        }
        PyObject *item = NULL;
        while ((item = PyIter_Next(iter))) {
            if (PyBTree_Insert(self->tree, item, Py_None) < 0) {
                Py_DECREF(item);
                Py_DECREF(iter);
                Py_LeaveRecursiveCall();
                return NULL;
            }
            Py_DECREF(item);
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) {
            Py_LeaveRecursiveCall();
            return NULL;
        }
        Py_LeaveRecursiveCall();
    }
    Py_RETURN_NONE;
}

static PyObject *
SortedSet_difference_update(PyObject *self_obj, PyObject *args)
{
    if (SortedSet_update_internal((SortedSetObject *)self_obj, args, 1) < 0) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *
SortedSet_intersection_update(PyObject *self_obj, PyObject *args)
{
    if (SortedSet_update_internal((SortedSetObject *)self_obj, args, 2) < 0) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *
SortedSet_symmetric_difference_update(PyObject *self_obj, PyObject *args)
{
    if (SortedSet_update_internal((SortedSetObject *)self_obj, args, 3) < 0) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *
SortedSet_richcompare(PyObject *self_obj, PyObject *other_obj, int op)
{
    PyObject *self_set = PySet_New(NULL);
    if (!self_set) {
        return NULL;
    }
    PyObject *iter_keys = PyObject_CallMethod(((SortedSetObject *)self_obj)->tree, "keys", NULL);
    if (!iter_keys) {
        Py_DECREF(self_set);
        return NULL;
    }
    PyObject *key = NULL;
    while ((key = PyIter_Next(iter_keys))) {
        if (PySet_Add(self_set, key) < 0) {
            Py_DECREF(key);
            Py_DECREF(iter_keys);
            Py_DECREF(self_set);
            return NULL;
        }
        Py_DECREF(key);
    }
    Py_DECREF(iter_keys);
    if (PyErr_Occurred()) {
        Py_DECREF(self_set);
        return NULL;
    }

    PyObject *other_set = NULL;
    if (PyObject_TypeCheck(other_obj, &SortedSetType)) {
        other_set = PySet_New(NULL);
        if (!other_set) {
            Py_DECREF(self_set);
            return NULL;
        }
        PyObject *other_iter = PyObject_CallMethod(((SortedSetObject *)other_obj)->tree, "keys", NULL);
        if (!other_iter) {
            Py_DECREF(other_set);
            Py_DECREF(self_set);
            return NULL;
        }
        while ((key = PyIter_Next(other_iter))) {
            if (PySet_Add(other_set, key) < 0) {
                Py_DECREF(key);
                Py_DECREF(other_iter);
                Py_DECREF(other_set);
                Py_DECREF(self_set);
                return NULL;
            }
            Py_DECREF(key);
        }
        Py_DECREF(other_iter);
        if (PyErr_Occurred()) {
            Py_DECREF(other_set);
            Py_DECREF(self_set);
            return NULL;
        }
    } else if (PyAnySet_Check(other_obj)) {
        other_set = Py_NewRef(other_obj);
    } else {
        Py_DECREF(self_set);
        Py_RETURN_NOTIMPLEMENTED;
    }

    PyObject *result = PyObject_RichCompare(self_set, other_set, op);
    Py_DECREF(self_set);
    Py_DECREF(other_set);
    return result;
}

static PyObject *
SortedSet_iter(PyObject *self_obj)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *keys = PyObject_CallMethod(self->tree, "keys", NULL);
    if (!keys) {
        return NULL;
    }
    PyObject *iter = PyObject_GetIter(keys);
    Py_DECREF(keys);
    return iter;
}

static PyObject *
SortedSet_subscript(PyObject *self_obj, PyObject *item)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    PyObject *result = NULL;
    if (PySlice_Check(item)) {
        Py_ssize_t length = PyObject_Length(self->tree);
        if (length < 0) {
            return NULL;
        }
        Py_ssize_t start, stop, step, slicelength;
        if (PySlice_GetIndicesEx(item, length, &start, &stop, &step, &slicelength) < 0) {
            return NULL;
        }
        result = PyList_New(0);
        if (!result) {
            return NULL;
        }
        if (slicelength > 0) {
            for (Py_ssize_t i = 0; i < slicelength; i++) {
                Py_ssize_t idx = start + i * step;
                PyObject *key = PyBTree_GetItemByIndex(self->tree, idx, 0);
                if (!key) {
                    Py_DECREF(result);
                    return NULL;
                }
                if (PyList_Append(result, key) < 0) {
                    Py_DECREF(key);
                    Py_DECREF(result);
                    return NULL;
                }
                Py_DECREF(key);
            }
        }
    } else {
        Py_ssize_t index = PyLong_AsSsize_t(item);
        if (index == -1 && PyErr_Occurred()) {
            return NULL;
        }
        result = sortedset_key_at(self, index);
    }
    return result;
}

static int
SortedSet_ass_subscript(PyObject *self_obj, PyObject *item, PyObject *value)
{
    SortedSetObject *self = (SortedSetObject *)self_obj;
    if (value != NULL) {
        PyErr_SetString(PyExc_NotImplementedError, "SortedSet does not support item assignment");
        return -1;
    }

    if (PySlice_Check(item)) {
        Py_ssize_t length = PyObject_Length(self->tree);
        if (length < 0) {
            return -1;
        }
        Py_ssize_t start, stop, step, slicelength;
        if (PySlice_GetIndicesEx(item, length, &start, &stop, &step, &slicelength) < 0) {
            return -1;
        }
        PyObject *to_delete = PyList_New(0);
        if (!to_delete) {
            return -1;
        }
        if (slicelength > 0) {
            for (Py_ssize_t i = 0; i < slicelength; i++) {
                Py_ssize_t idx = start + i * step;
                PyObject *key = PyBTree_GetItemByIndex(self->tree, idx, 0);
                if (!key) {
                    Py_DECREF(to_delete);
                    return -1;
                }
                if (PyList_Append(to_delete, key) < 0) {
                    Py_DECREF(key);
                    Py_DECREF(to_delete);
                    return -1;
                }
                Py_DECREF(key);
            }
        }
        Py_ssize_t size = PyList_GET_SIZE(to_delete);
        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject *key = PyList_GET_ITEM(to_delete, i);
            if (PyBTree_Delete(self->tree, key) < 0) {
                Py_DECREF(to_delete);
                if (PyErr_ExceptionMatches(PyExc_KeyError)) {
                    PyErr_Clear();
                    continue;
                }
                return -1;
            }
        }
        Py_DECREF(to_delete);
        return 0;
    }

    Py_ssize_t index = PyLong_AsSsize_t(item);
    if (index == -1 && PyErr_Occurred()) {
        return -1;
    }
    PyObject *key = sortedset_key_at(self, index);
    if (!key) {
        return -1;
    }
    int rc = PyBTree_Delete(self->tree, key);
    Py_DECREF(key);
    if (rc < 0) {
        return -1;
    }
    return 0;
}

static PyObject *
SortedSet_or(PyObject *self_obj, PyObject *other)
{
    PyObject *args = PyTuple_Pack(1, other);
    if (!args) {
        return NULL;
    }
    PyObject *res = SortedSet_union(self_obj, args);
    Py_DECREF(args);
    return res;
}

static PyObject *
SortedSet_and(PyObject *self_obj, PyObject *other)
{
    PyObject *args = PyTuple_Pack(1, other);
    if (!args) {
        return NULL;
    }
    PyObject *res = SortedSet_intersection(self_obj, args);
    Py_DECREF(args);
    return res;
}

static PyObject *
SortedSet_sub(PyObject *self_obj, PyObject *other)
{
    PyObject *args = PyTuple_Pack(1, other);
    if (!args) {
        return NULL;
    }
    PyObject *res = SortedSet_difference(self_obj, args);
    Py_DECREF(args);
    return res;
}

static PyObject *
SortedSet_xor(PyObject *self_obj, PyObject *other)
{
    PyObject *args = PyTuple_Pack(1, other);
    if (!args) {
        return NULL;
    }
    PyObject *res = SortedSet_symmetric_difference(self_obj, args);
    Py_DECREF(args);
    return res;
}

static PyMappingMethods SortedDict_as_mapping = {
    .mp_length = SortedDict_len,
    .mp_subscript = SortedDict_getitem,
    .mp_ass_subscript = SortedDict_setitem,
};

static PySequenceMethods SortedDict_as_sequence = {
    .sq_contains = SortedDict_contains,
};

static PyMethodDef SortedDict_methods[] = {
    {"setdefault", (PyCFunction)SortedDict_setdefault, METH_VARARGS | METH_KEYWORDS,
     "D.setdefault(key[, default]) -> D[key] if key in D, else default (also setting it)."},
    {"update", (PyCFunction)SortedDict_update, METH_VARARGS | METH_KEYWORDS,
     "D.update([E, ]**F) -> None. Update D from dict/iterable E and F."},
    {"pop", (PyCFunction)SortedDict_pop, METH_VARARGS | METH_KEYWORDS,
     "D.pop(key[, default]) -> v. Remove key and return value, or default if not found."},
    {"popitem", (PyCFunction)SortedDict_popitem, METH_VARARGS,
     "D.popitem([index]) -> (k, v). Remove and return (key, value) at index (default last)."},
    {"get", (PyCFunction)SortedDict_get, METH_VARARGS | METH_KEYWORDS,
     "D.get(key[, default]) -> D[key] if key in D, else default (None)."},
    {"copy", (PyCFunction)SortedDict_copy, METH_NOARGS,
     "D.copy() -> a shallow copy of D."},
    {"clear", (PyCFunction)SortedDict_clear, METH_NOARGS,
     "D.clear() -> None. Remove all items from D."},
    {"peekitem", (PyCFunction)SortedDict_peekitem, METH_VARARGS,
     "D.peekitem([index]) -> (k, v). Return (key, value) at index without removing."},
    {"keys", (PyCFunction)SortedDict_keys, METH_NOARGS,
     "D.keys() -> a set-like object providing a view on D's keys."},
    {"items", (PyCFunction)SortedDict_items, METH_NOARGS,
     "D.items() -> a set-like object providing a view on D's items."},
    {"values", (PyCFunction)SortedDict_values, METH_NOARGS,
     "D.values() -> an object providing a view on D's values."},
    {"fromkeys", (PyCFunction)SortedDict_fromkeys, METH_CLASS | METH_VARARGS,
     "Create a new SortedDict with keys from iterable and values set to value."},
    {"bisect", (PyCFunction)SortedDict_bisect, METH_VARARGS,
     "D.bisect(key) -> index. Return insertion point for key (same as bisect_right)."},
    {"index", (PyCFunction)SortedDict_index, METH_VARARGS,
     "D.index(key) -> index. Return index of key. Raises ValueError if not found."},
    {"islice", (PyCFunction)SortedDict_islice, METH_VARARGS | METH_KEYWORDS,
     "D.islice([start[, stop[, reverse]]]) -> list of keys in slice range."},
    {"bisect_left", (PyCFunction)SortedList_bisect_left, METH_VARARGS,
     "D.bisect_left(key) -> index. Return leftmost insertion point for key."},
    {"bisect_right", (PyCFunction)SortedList_bisect_right, METH_VARARGS,
     "D.bisect_right(key) -> index. Return rightmost insertion point for key."},
    {"irange", (PyCFunction)SortedList_irange, METH_VARARGS | METH_KEYWORDS,
     "D.irange([min[, max[, inclusive[, reverse]]]]) -> list of keys in range."},
    {NULL, NULL, 0, NULL}
};

static PySequenceMethods SortedSet_as_sequence = {
    .sq_contains = SortedSet_contains,
    .sq_length = SortedDict_len,
};

static PyMappingMethods SortedSet_as_mapping = {
    .mp_length = SortedDict_len,
    .mp_subscript = SortedSet_subscript,
    .mp_ass_subscript = (objobjargproc)SortedSet_ass_subscript,
};

static PyNumberMethods SortedSet_as_number = {
    .nb_or = (binaryfunc)SortedSet_or,
    .nb_and = (binaryfunc)SortedSet_and,
    .nb_subtract = (binaryfunc)SortedSet_sub,
    .nb_xor = (binaryfunc)SortedSet_xor,
};

static PyMethodDef SortedSet_methods[] = {
    {"add", (PyCFunction)SortedSet_add, METH_O,
     "S.add(elem) -> None. Add element elem to the set."},
    {"remove", (PyCFunction)SortedSet_remove, METH_O,
     "S.remove(elem) -> None. Remove element elem. Raises KeyError if not found."},
    {"discard", (PyCFunction)SortedSet_discard, METH_O,
     "S.discard(elem) -> None. Remove element elem if present."},
    {"pop", (PyCFunction)SortedSet_pop, METH_VARARGS,
     "S.pop([index]) -> elem. Remove and return element at index (default last)."},
    {"union", (PyCFunction)SortedSet_union, METH_VARARGS,
     "S.union(*others) -> SortedSet. Return union of sets."},
    {"difference", (PyCFunction)SortedSet_difference, METH_VARARGS,
     "S.difference(*others) -> SortedSet. Return difference of sets."},
    {"intersection", (PyCFunction)SortedSet_intersection, METH_VARARGS,
     "S.intersection(*others) -> SortedSet. Return intersection of sets."},
    {"symmetric_difference", (PyCFunction)SortedSet_symmetric_difference, METH_VARARGS,
     "S.symmetric_difference(other) -> SortedSet. Return symmetric difference."},
    {"update", (PyCFunction)SortedSet_update, METH_VARARGS,
     "S.update(*others) -> None. Update set with union of itself and others."},
    {"difference_update", (PyCFunction)SortedSet_difference_update, METH_VARARGS,
     "S.difference_update(*others) -> None. Update set with difference."},
    {"intersection_update", (PyCFunction)SortedSet_intersection_update, METH_VARARGS,
     "S.intersection_update(*others) -> None. Update set with intersection."},
    {"symmetric_difference_update", (PyCFunction)SortedSet_symmetric_difference_update, METH_VARARGS,
     "S.symmetric_difference_update(other) -> None. Update with symmetric difference."},
    {"bisect_left", (PyCFunction)SortedSet_bisect_left, METH_VARARGS,
     "S.bisect_left(value) -> index. Return leftmost insertion point for value."},
    {"bisect_right", (PyCFunction)SortedSet_bisect_right, METH_VARARGS,
     "S.bisect_right(value) -> index. Return rightmost insertion point for value."},
    {"index", (PyCFunction)SortedSet_index, METH_VARARGS,
     "S.index(value) -> index. Return index of value. Raises ValueError if not found."},
    {"irange", (PyCFunction)SortedSet_irange, METH_VARARGS | METH_KEYWORDS,
     "S.irange([min[, max[, inclusive[, reverse]]]]) -> list of values in range."},
    {"islice", (PyCFunction)SortedSet_islice, METH_VARARGS | METH_KEYWORDS,
     "S.islice([start[, stop[, reverse]]]) -> list of values in slice range."},
    {NULL, NULL, 0, NULL}
};

static PyTypeObject SortedDictType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sortedcollections.SortedDict",
    .tp_basicsize = sizeof(SortedDictObject),
    .tp_dealloc = (destructor)SortedDict_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = SortedDict_new,
    .tp_init = SortedDict_init,
    .tp_as_mapping = &SortedDict_as_mapping,
    .tp_as_sequence = &SortedDict_as_sequence,
    .tp_methods = SortedDict_methods,
    .tp_repr = SortedDict_repr,
    .tp_iter = SortedDict_iter,
};

static PyTypeObject SortedSetType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "sortedcollections.SortedSet",
    .tp_basicsize = sizeof(SortedSetObject),
    .tp_dealloc = (destructor)SortedSet_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = SortedSet_new,
    .tp_init = SortedSet_init,
    .tp_as_sequence = &SortedSet_as_sequence,
    .tp_as_mapping = &SortedSet_as_mapping,
    .tp_as_number = &SortedSet_as_number,
    .tp_methods = SortedSet_methods,
    .tp_repr = SortedSet_repr,
    .tp_iter = SortedSet_iter,
    .tp_richcompare = SortedSet_richcompare,
};

static PyMethodDef sortedcollections_module_methods[] = {
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef sortedcollections_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "sortedcollections",
    .m_doc = "Sorted dictionary and set collections backed by a B-tree.",
    .m_size = -1,
    .m_methods = sortedcollections_module_methods,
};

PyMODINIT_FUNC
PyInit_sortedcollections(void)
{
    if (import_btree() < 0) {
        return NULL;
    }

    if (PyType_Ready(&SortedDictViewReverseIterType) < 0) {
        return NULL;
    }
    if (PyType_Ready(&SortedDictViewType) < 0) {
        return NULL;
    }
    if (PyType_Ready(&SortedDictType) < 0) {
        return NULL;
    }
    if (PyType_Ready(&SortedSetType) < 0) {
        return NULL;
    }

    PyObject *m = PyModule_Create(&sortedcollections_module);
    if (!m) {
        return NULL;
    }

    if (PyModule_AddObjectRef(m, "SortedDict", (PyObject *)&SortedDictType) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    if (PyModule_AddObjectRef(m, "SortedSet", (PyObject *)&SortedSetType) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
