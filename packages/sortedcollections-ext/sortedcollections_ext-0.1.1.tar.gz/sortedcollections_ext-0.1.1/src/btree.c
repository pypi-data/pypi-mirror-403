#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <stddef.h>

#define BTREE_MODULE
#include "btreemodule.h"

/* Thread-safety for free-threaded Python (PEP 703, Python 3.13+) */
#ifdef Py_GIL_DISABLED
#include <pythread.h>
static PyMutex btree_freelist_mutex = {0};
#define FREELIST_LOCK() PyMutex_Lock(&btree_freelist_mutex)
#define FREELIST_UNLOCK() PyMutex_Unlock(&btree_freelist_mutex)
#else
#define FREELIST_LOCK() ((void)0)
#define FREELIST_UNLOCK() ((void)0)
#endif

#ifndef BTREE_LEAF_MIN_DEGREE
#define BTREE_LEAF_MIN_DEGREE 64
#endif
#define BTREE_LEAF_MAX_KEYS (2 * BTREE_LEAF_MIN_DEGREE - 1)

#ifndef BTREE_INTERNAL_MIN_DEGREE
#define BTREE_INTERNAL_MIN_DEGREE 64
#endif
#define BTREE_INTERNAL_MAX_KEYS (2 * BTREE_INTERNAL_MIN_DEGREE - 1)
#define BTREE_INTERNAL_MAX_CHILDREN (2 * BTREE_INTERNAL_MIN_DEGREE)

typedef struct BTreeNodeBase {
    int n;
    int leaf;
    Py_ssize_t subtree_size;  /* Total keys in this node + all children */
    struct BTreeNodeBase *next_free;
} BTreeNode;

typedef union {
    int64_t i64;
    double f64;
} BTreePrimKey;

enum {
    BTREE_PRIM_UNKNOWN = -1,
    BTREE_PRIM_NONE = 0,
    BTREE_PRIM_I64 = 1,
    BTREE_PRIM_F64 = 2,
};

typedef struct BTreeLeaf {
    BTreeNode base;
    PyObject *keys[BTREE_LEAF_MAX_KEYS];
    PyObject *values[BTREE_LEAF_MAX_KEYS];
    BTreePrimKey prim_keys[BTREE_LEAF_MAX_KEYS];
    struct BTreeLeaf *next_leaf;
} BTreeLeaf;

typedef struct BTreeInternal {
    BTreeNode base;
    PyObject *keys[BTREE_INTERNAL_MAX_KEYS];
    BTreePrimKey prim_keys[BTREE_INTERNAL_MAX_KEYS];
    struct BTreeNodeBase *children[BTREE_INTERNAL_MAX_CHILDREN];
} BTreeInternal;

typedef struct {
    PyObject_HEAD
    BTreeNode *root;
    Py_ssize_t size;
    PyTypeObject *key_type;
    int prim_kind;
    int busy;
    PyObject *weakreflist;
    PyObject *cache_key;
    BTreeNode **cache_nodes;
    Py_ssize_t cache_depth;
    Py_ssize_t cache_cap;
    uint64_t mod_count;
    uint64_t cache_version;
} BTreeObject;

typedef struct {
    PyObject_HEAD
    BTreeObject *tree;
    int kind; /* 0=keys, 1=values, 2=items */
    BTreeNode *leaf;
    Py_ssize_t leaf_index;
    uint64_t expected_mod_count;
    Py_ssize_t top;
    Py_ssize_t cap;
    BTreeNode **nodes;
    int *index;
} BTreeIterObject;

static PyTypeObject BTreeType;
static PyTypeObject BTreeIterType;

static PyObject *BTree_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static BTreeNode *btree_node_new(int leaf);
static void btree_node_free(BTreeNode *node);
static int btree_prim_from_key(PyObject *key, int *kind, BTreePrimKey *out);
static void btree_cache_clear(BTreeObject *self);
static int btree_cache_ensure(BTreeObject *self, Py_ssize_t depth);
static int btree_cache_select_index(BTreeObject *self, Py_ssize_t index,
                                    PyObject **out_key, PyObject **out_value);

/* Fixed-size freelists for BTreeNode allocations */
#define BTREE_NODE_FREELIST_MAX 1024
static BTreeNode *btree_leaf_freelist = NULL;
static Py_ssize_t btree_leaf_freelist_size = 0;
static BTreeNode *btree_internal_freelist = NULL;
static Py_ssize_t btree_internal_freelist_size = 0;

static int
btree_guard_enter(BTreeObject *self)
{
    if (self->busy) {
        PyErr_SetString(PyExc_RuntimeError, "BTree reentrant access during comparison");
        return -1;
    }
    self->busy = 1;
    return 0;
}

static void
btree_guard_exit(BTreeObject *self)
{
    self->busy = 0;
}

static int
btree_guard_check(BTreeObject *self)
{
    if (self->busy) {
        PyErr_SetString(PyExc_RuntimeError, "BTree reentrant access during comparison");
        return -1;
    }
    return 0;
}

static int
btree_key_is_nan(PyObject *key, int *is_nan)
{
    if (!PyFloat_Check(key)) {
        *is_nan = 0;
        return 0;
    }
    double v = PyFloat_AsDouble(key);
    if (PyErr_Occurred()) {
        return -1;
    }
    *is_nan = isnan(v);
    return 0;
}

static int
btree_check_nan_key(PyObject *key)
{
    int is_nan = 0;
    if (btree_key_is_nan(key, &is_nan) < 0) {
        return -1;
    }
    if (is_nan) {
        PyErr_SetString(PyExc_ValueError, "NaN keys are not supported");
        return -1;
    }
    return 0;
}

static void
btree_cache_clear(BTreeObject *self)
{
    if (self->cache_key) {
        Py_DECREF(self->cache_key);
        self->cache_key = NULL;
    }
    self->cache_depth = 0;
    self->cache_version = 0;
}

static int
btree_cache_ensure(BTreeObject *self, Py_ssize_t depth)
{
    if (depth <= self->cache_cap) {
        return 0;
    }
    Py_ssize_t new_cap = self->cache_cap ? self->cache_cap : 8;
    while (new_cap < depth) {
        new_cap *= 2;
    }
    BTreeNode **new_nodes = PyMem_Realloc(self->cache_nodes, new_cap * sizeof(BTreeNode *));
    if (!new_nodes) {
        PyErr_NoMemory();
        return -1;
    }
    self->cache_nodes = new_nodes;
    self->cache_cap = new_cap;
    return 0;
}

static inline BTreeLeaf *
btree_leaf(BTreeNode *node)
{
    return (BTreeLeaf *)node;
}

static inline BTreeInternal *
btree_internal(BTreeNode *node)
{
    return (BTreeInternal *)node;
}

static inline PyObject **
btree_keys(BTreeNode *node)
{
    return node->leaf ? btree_leaf(node)->keys : btree_internal(node)->keys;
}

static inline PyObject **
btree_values(BTreeNode *node)
{
    return node->leaf ? btree_leaf(node)->values : NULL;
}

static inline BTreeNode **
btree_children(BTreeNode *node)
{
    return node->leaf ? NULL : (BTreeNode **)btree_internal(node)->children;
}

static int
btree_cache_select_index(BTreeObject *self, Py_ssize_t index, PyObject **out_key, PyObject **out_value)
{
    if (!self->root) {
        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }
    if (index < 0) {
        index += self->size;
    }
    if (index < 0 || index >= self->size) {
        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    btree_cache_clear(self);

    BTreeNode *node = self->root;
    Py_ssize_t depth = 0;
    while (node && !node->leaf) {
        if (btree_cache_ensure(self, depth + 1) < 0) {
            btree_cache_clear(self);
            return -1;
        }
        self->cache_nodes[depth++] = node;

        BTreeNode **children = btree_children(node);
        Py_ssize_t idx = index;
        int child_idx = 0;
        for (; child_idx <= node->n; child_idx++) {
            Py_ssize_t child_size = children[child_idx]->subtree_size;
            if (idx < child_size) {
                break;
            }
            idx -= child_size;
        }
        index = idx;
        node = children[child_idx];
    }

    if (!node) {
        btree_cache_clear(self);
        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }
    if (btree_cache_ensure(self, depth + 1) < 0) {
        btree_cache_clear(self);
        return -1;
    }
    self->cache_nodes[depth++] = node;

    if (index < 0 || index >= node->n) {
        btree_cache_clear(self);
        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject **keys = btree_keys(node);
    PyObject **values = btree_values(node);
    PyObject *key = keys[index];
    PyObject *value = values[index];
    if (!key || !value) {
        btree_cache_clear(self);
        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    *out_key = Py_NewRef(key);
    *out_value = Py_NewRef(value);
    self->cache_key = Py_NewRef(key);
    self->cache_depth = depth;
    self->cache_version = self->mod_count;
    return 0;
}

static inline BTreePrimKey *
btree_prim_keys(BTreeNode *node)
{
    return node->leaf ? btree_leaf(node)->prim_keys : btree_internal(node)->prim_keys;
}

static inline int
btree_max_keys(BTreeNode *node)
{
    return node->leaf ? BTREE_LEAF_MAX_KEYS : BTREE_INTERNAL_MAX_KEYS;
}

static inline int
btree_min_degree(BTreeNode *node)
{
    return node->leaf ? BTREE_LEAF_MIN_DEGREE : BTREE_INTERNAL_MIN_DEGREE;
}

static inline void
btree_node_free_raw(BTreeNode *node)
{
    if (!node) {
        return;
    }
    PyMem_Free(node);
}

static int
btree_keys_append(PyObject ***keys, Py_ssize_t *size, Py_ssize_t *cap, PyObject *key)
{
    if (*size >= *cap) {
        Py_ssize_t new_cap = (*cap == 0) ? 256 : (*cap * 2);
        PyObject **new_keys = PyMem_Realloc(*keys, new_cap * sizeof(PyObject *));
        if (!new_keys) {
            PyErr_NoMemory();
            return -1;
        }
        *keys = new_keys;
        *cap = new_cap;
    }
    (*keys)[(*size)++] = key;
    return 0;
}

static BTreeObject *
btree_build_from_sorted(PyObject **keys, Py_ssize_t n)
{
    BTreeObject *tree = (BTreeObject *)BTree_new(&BTreeType, NULL, NULL);
    if (!tree) {
        return NULL;
    }
    if (n == 0) {
        return tree;
    }

    for (Py_ssize_t i = 0; i < n; i++) {
        if (btree_check_nan_key(keys[i]) < 0) {
            Py_DECREF(tree);
            return NULL;
        }
    }

    tree->key_type = Py_TYPE(keys[0]);
    int prim_kind = tree->prim_kind;

    Py_ssize_t leaf_cap = BTREE_LEAF_MAX_KEYS;
    Py_ssize_t leaf_count = (n + leaf_cap - 1) / leaf_cap;
    BTreeNode **level = (BTreeNode **)PyMem_Malloc(leaf_count * sizeof(BTreeNode *));
    if (!level) {
        PyErr_NoMemory();
        Py_DECREF(tree);
        return NULL;
    }

    Py_ssize_t idx = 0;
    BTreeLeaf *prev_leaf = NULL;
    for (Py_ssize_t i = 0; i < leaf_count; i++) {
        BTreeLeaf *leaf = btree_leaf(btree_node_new(1));
        if (!leaf) {
            for (Py_ssize_t j = 0; j < i; j++) {
                btree_node_free(level[j]);
            }
            PyMem_Free(level);
            Py_DECREF(tree);
            return NULL;
        }
        leaf->base.n = 0;
        leaf->base.subtree_size = 0;
        leaf->next_leaf = NULL;

        Py_ssize_t count = (n - idx > leaf_cap) ? leaf_cap : (n - idx);
        BTreePrimKey *pkeys = leaf->prim_keys;
        for (Py_ssize_t j = 0; j < count; j++) {
            leaf->keys[j] = keys[idx];
            keys[idx] = NULL;
            Py_INCREF(Py_None);
            leaf->values[j] = Py_None;
            if (tree->key_type && Py_TYPE(leaf->keys[j]) != tree->key_type) {
                tree->key_type = NULL;
            }
            if (prim_kind != BTREE_PRIM_NONE) {
                BTreePrimKey prim_key;
                int kind_tmp = BTREE_PRIM_NONE;
                int r = btree_prim_from_key(leaf->keys[j], &kind_tmp, &prim_key);
                if (r < 0) {
                    for (Py_ssize_t k = 0; k <= j; k++) {
                        Py_DECREF(leaf->keys[k]);
                        Py_DECREF(leaf->values[k]);
                    }
                    btree_node_free((BTreeNode *)leaf);
                    PyMem_Free(level);
                    Py_DECREF(tree);
                    return NULL;
                }
                if (prim_kind == BTREE_PRIM_UNKNOWN) {
                    if (r == 1) {
                        prim_kind = kind_tmp;
                        tree->prim_kind = kind_tmp;
                        pkeys[j] = prim_key;
                    } else {
                        prim_kind = BTREE_PRIM_NONE;
                        tree->prim_kind = BTREE_PRIM_NONE;
                    }
                } else if (prim_kind == kind_tmp && r == 1) {
                    pkeys[j] = prim_key;
                } else if (r == 0 || prim_kind != kind_tmp) {
                    prim_kind = BTREE_PRIM_NONE;
                    tree->prim_kind = BTREE_PRIM_NONE;
                }
            }
            idx++;
        }
        leaf->base.n = (int)count;
        leaf->base.subtree_size = count;

        if (prev_leaf) {
            prev_leaf->next_leaf = leaf;
        }
        prev_leaf = leaf;
        level[i] = (BTreeNode *)leaf;
    }

    Py_ssize_t level_count = leaf_count;
    while (level_count > 1) {
        Py_ssize_t child_cap = BTREE_INTERNAL_MAX_CHILDREN;
        Py_ssize_t parent_count = (level_count + child_cap - 1) / child_cap;
        BTreeNode **next_level = (BTreeNode **)PyMem_Malloc(parent_count * sizeof(BTreeNode *));
        if (!next_level) {
            PyErr_NoMemory();
            for (Py_ssize_t i = 0; i < level_count; i++) {
                btree_node_free(level[i]);
            }
            PyMem_Free(level);
            Py_DECREF(tree);
            return NULL;
        }

        Py_ssize_t child_index = 0;
        for (Py_ssize_t i = 0; i < parent_count; i++) {
            BTreeInternal *parent = btree_internal(btree_node_new(0));
            if (!parent) {
                for (Py_ssize_t j = 0; j < i; j++) {
                    btree_node_free(next_level[j]);
                }
                for (Py_ssize_t j = child_index; j < level_count; j++) {
                    btree_node_free(level[j]);
                }
                PyMem_Free(next_level);
                PyMem_Free(level);
                Py_DECREF(tree);
                return NULL;
            }

            Py_ssize_t remaining = level_count - child_index;
            Py_ssize_t num_children = remaining > child_cap ? child_cap : remaining;
            parent->base.n = (int)(num_children - 1);
            parent->base.subtree_size = 0;

            for (Py_ssize_t c = 0; c < num_children; c++) {
                parent->children[c] = level[child_index + c];
                parent->base.subtree_size += level[child_index + c]->subtree_size;
                if (c > 0) {
                    BTreeNode *child = level[child_index + c];
                    PyObject **child_keys = btree_keys(child);
                    Py_INCREF(child_keys[0]);
                    parent->keys[c - 1] = child_keys[0];
                    if (prim_kind != BTREE_PRIM_NONE) {
                        BTreePrimKey *pprim = parent->prim_keys;
                        BTreePrimKey *cprim = btree_prim_keys(child);
                        pprim[c - 1] = cprim[0];
                    }
                }
            }
            child_index += num_children;
            next_level[i] = (BTreeNode *)parent;
        }

        PyMem_Free(level);
        level = next_level;
        level_count = parent_count;
    }

    tree->root = level[0];
    tree->size = n;
    PyMem_Free(level);
    return tree;
}

static BTreeObject *
btree_build_from_sorted_pairs(PyObject **keys, PyObject **values, Py_ssize_t n)
{
    BTreeObject *tree = (BTreeObject *)BTree_new(&BTreeType, NULL, NULL);
    if (!tree) {
        return NULL;
    }
    if (n == 0) {
        return tree;
    }

    for (Py_ssize_t i = 0; i < n; i++) {
        if (btree_check_nan_key(keys[i]) < 0) {
            Py_DECREF(tree);
            return NULL;
        }
    }

    tree->key_type = Py_TYPE(keys[0]);
    int prim_kind = tree->prim_kind;

    Py_ssize_t leaf_cap = BTREE_LEAF_MAX_KEYS;
    Py_ssize_t leaf_count = (n + leaf_cap - 1) / leaf_cap;
    BTreeNode **level = (BTreeNode **)PyMem_Malloc(leaf_count * sizeof(BTreeNode *));
    if (!level) {
        PyErr_NoMemory();
        Py_DECREF(tree);
        return NULL;
    }

    Py_ssize_t idx = 0;
    BTreeLeaf *prev_leaf = NULL;
    for (Py_ssize_t i = 0; i < leaf_count; i++) {
        BTreeLeaf *leaf = btree_leaf(btree_node_new(1));
        if (!leaf) {
            for (Py_ssize_t j = 0; j < i; j++) {
                btree_node_free(level[j]);
            }
            PyMem_Free(level);
            Py_DECREF(tree);
            return NULL;
        }
        leaf->base.n = 0;
        leaf->base.subtree_size = 0;
        leaf->next_leaf = NULL;

        Py_ssize_t count = (n - idx > leaf_cap) ? leaf_cap : (n - idx);
        BTreePrimKey *pkeys = leaf->prim_keys;
        for (Py_ssize_t j = 0; j < count; j++) {
            leaf->keys[j] = keys[idx];
            keys[idx] = NULL;
            leaf->values[j] = values[idx];
            values[idx] = NULL;
            if (tree->key_type && Py_TYPE(leaf->keys[j]) != tree->key_type) {
                tree->key_type = NULL;
            }
            if (prim_kind != BTREE_PRIM_NONE) {
                BTreePrimKey prim_key;
                int kind_tmp = BTREE_PRIM_NONE;
                int r = btree_prim_from_key(leaf->keys[j], &kind_tmp, &prim_key);
                if (r < 0) {
                    for (Py_ssize_t k = 0; k <= j; k++) {
                        Py_DECREF(leaf->keys[k]);
                        Py_DECREF(leaf->values[k]);
                    }
                    btree_node_free((BTreeNode *)leaf);
                    PyMem_Free(level);
                    Py_DECREF(tree);
                    return NULL;
                }
                if (prim_kind == BTREE_PRIM_UNKNOWN) {
                    if (r == 1) {
                        prim_kind = kind_tmp;
                        tree->prim_kind = kind_tmp;
                        pkeys[j] = prim_key;
                    } else {
                        prim_kind = BTREE_PRIM_NONE;
                        tree->prim_kind = BTREE_PRIM_NONE;
                    }
                } else if (prim_kind == kind_tmp && r == 1) {
                    pkeys[j] = prim_key;
                } else if (r == 0 || prim_kind != kind_tmp) {
                    prim_kind = BTREE_PRIM_NONE;
                    tree->prim_kind = BTREE_PRIM_NONE;
                }
            }
            idx++;
        }
        leaf->base.n = (int)count;
        leaf->base.subtree_size = count;

        if (prev_leaf) {
            prev_leaf->next_leaf = leaf;
        }
        prev_leaf = leaf;
        level[i] = (BTreeNode *)leaf;
    }

    Py_ssize_t level_count = leaf_count;
    while (level_count > 1) {
        Py_ssize_t child_cap = BTREE_INTERNAL_MAX_CHILDREN;
        Py_ssize_t parent_count = (level_count + child_cap - 1) / child_cap;
        BTreeNode **next_level = (BTreeNode **)PyMem_Malloc(parent_count * sizeof(BTreeNode *));
        if (!next_level) {
            PyErr_NoMemory();
            for (Py_ssize_t i = 0; i < level_count; i++) {
                btree_node_free(level[i]);
            }
            PyMem_Free(level);
            Py_DECREF(tree);
            return NULL;
        }

        Py_ssize_t child_index = 0;
        for (Py_ssize_t i = 0; i < parent_count; i++) {
            BTreeInternal *parent = btree_internal(btree_node_new(0));
            if (!parent) {
                for (Py_ssize_t j = 0; j < i; j++) {
                    btree_node_free(next_level[j]);
                }
                for (Py_ssize_t j = 0; j < level_count; j++) {
                    btree_node_free(level[j]);
                }
                PyMem_Free(next_level);
                PyMem_Free(level);
                Py_DECREF(tree);
                return NULL;
            }
            parent->base.n = 0;
            parent->base.subtree_size = 0;

            Py_ssize_t num_children = (level_count - child_index > child_cap)
                ? child_cap : (level_count - child_index);
            for (Py_ssize_t c = 0; c < num_children; c++) {
                parent->children[c] = level[child_index + c];
                parent->base.subtree_size += level[child_index + c]->subtree_size;
                if (c > 0) {
                    BTreeNode *child = level[child_index + c];
                    PyObject **child_keys = btree_keys(child);
                    Py_INCREF(child_keys[0]);
                    parent->keys[c - 1] = child_keys[0];
                    if (prim_kind != BTREE_PRIM_NONE) {
                        parent->prim_keys[c - 1] = btree_prim_keys(child)[0];
                    }
                }
            }
            parent->base.n = (int)num_children - 1;
            child_index += num_children;
            next_level[i] = (BTreeNode *)parent;
        }

        PyMem_Free(level);
        level = next_level;
        level_count = parent_count;
    }

    tree->root = level[0];
    tree->size = n;
    PyMem_Free(level);
    return tree;
}

static void *
btree_alloc_simple(size_t size)
{
    void *ptr = PyMem_Malloc(size);
    if (!ptr) {
        PyErr_NoMemory();
        return NULL;
    }
    memset(ptr, 0, size);
    return ptr;
}

static void
btree_recompute_subtree(BTreeNode *node)
{
    if (!node) {
        return;
    }
    if (node->leaf) {
        node->subtree_size = node->n;
        return;
    }
    Py_ssize_t total = 0;
    BTreeNode **children = btree_children(node);
    for (int i = 0; i <= node->n; i++) {
        total += children[i]->subtree_size;
    }
    node->subtree_size = total;
}

static Py_ssize_t
btree_recompute_subtree_full(BTreeNode *node)
{
    if (!node) {
        return 0;
    }
    if (node->leaf) {
        node->subtree_size = node->n;
        return node->subtree_size;
    }
    Py_ssize_t total = 0;
    BTreeNode **children = btree_children(node);
    for (int i = 0; i <= node->n; i++) {
        total += btree_recompute_subtree_full(children[i]);
    }
    node->subtree_size = total;
    return total;
}
static BTreeNode *
btree_node_new(int leaf)
{
    if (leaf) {
        BTreeLeaf *node = NULL;
        FREELIST_LOCK();
        if (btree_leaf_freelist) {
            node = (BTreeLeaf *)btree_leaf_freelist;
            btree_leaf_freelist = btree_leaf_freelist->next_free;
            btree_leaf_freelist_size--;
            FREELIST_UNLOCK();
            memset(node, 0, sizeof(BTreeLeaf));
        } else {
            FREELIST_UNLOCK();
            node = (BTreeLeaf *)btree_alloc_simple(sizeof(BTreeLeaf));
            if (!node) {
                return NULL;
            }
        }
        node->base.n = 0;
        node->base.leaf = 1;
        node->base.subtree_size = 0;
        node->base.next_free = NULL;
        node->next_leaf = NULL;
        return (BTreeNode *)node;
    }

    BTreeInternal *node = NULL;
    FREELIST_LOCK();
    if (btree_internal_freelist) {
        node = (BTreeInternal *)btree_internal_freelist;
        btree_internal_freelist = btree_internal_freelist->next_free;
        btree_internal_freelist_size--;
        FREELIST_UNLOCK();
        memset(node, 0, sizeof(BTreeInternal));
    } else {
        FREELIST_UNLOCK();
        node = (BTreeInternal *)btree_alloc_simple(sizeof(BTreeInternal));
        if (!node) {
            return NULL;
        }
    }
    node->base.n = 0;
    node->base.leaf = 0;
    node->base.subtree_size = 0;
    node->base.next_free = NULL;
    return (BTreeNode *)node;
}

static void
btree_node_free(BTreeNode *node)
{
    if (!node) {
        return;
    }

    if (node->leaf) {
        BTreeLeaf *leaf = btree_leaf(node);
        for (int i = 0; i < node->n; i++) {
            Py_DECREF(leaf->keys[i]);
            Py_DECREF(leaf->values[i]);
        }
        FREELIST_LOCK();
        if (btree_leaf_freelist_size < BTREE_NODE_FREELIST_MAX) {
            memset(leaf, 0, sizeof(BTreeLeaf));
            leaf->base.next_free = btree_leaf_freelist;
            btree_leaf_freelist = (BTreeNode *)leaf;
            btree_leaf_freelist_size++;
            FREELIST_UNLOCK();
        } else {
            FREELIST_UNLOCK();
            PyMem_Free(leaf);
        }
        return;
    }

    BTreeInternal *in = btree_internal(node);
    for (int i = 0; i <= node->n; i++) {
        btree_node_free(in->children[i]);
    }
    for (int i = 0; i < node->n; i++) {
        Py_DECREF(in->keys[i]);
    }

    FREELIST_LOCK();
    if (btree_internal_freelist_size < BTREE_NODE_FREELIST_MAX) {
        memset(in, 0, sizeof(BTreeInternal));
        in->base.next_free = btree_internal_freelist;
        btree_internal_freelist = (BTreeNode *)in;
        btree_internal_freelist_size++;
        FREELIST_UNLOCK();
    } else {
        FREELIST_UNLOCK();
        PyMem_Free(in);
    }
}

static int
btree_traverse_node(BTreeNode *node, visitproc visit, void *arg)
{
    if (!node) {
        return 0;
    }
    if (node->leaf) {
        BTreeLeaf *leaf = btree_leaf(node);
        for (int i = 0; i < node->n; i++) {
            Py_VISIT(leaf->keys[i]);
            Py_VISIT(leaf->values[i]);
        }
        return 0;
    }
    BTreeInternal *in = btree_internal(node);
    for (int i = 0; i < node->n; i++) {
        Py_VISIT(in->keys[i]);
    }
    for (int i = 0; i <= node->n; i++) {
        if (btree_traverse_node(in->children[i], visit, arg) < 0) {
            return -1;
        }
    }
    return 0;
}

static PyObject *
BTreeIter_new(BTreeObject *tree, int kind)
{
    if (btree_guard_check(tree) < 0) {
        return NULL;
    }
    BTreeIterObject *it = PyObject_GC_New(BTreeIterObject, &BTreeIterType);
    if (!it) {
        return NULL;
    }
    it->tree = (BTreeObject *)Py_NewRef((PyObject *)tree);
    it->kind = kind;
    it->leaf = NULL;
    it->leaf_index = 0;
    it->expected_mod_count = tree->mod_count;
    it->top = -1;
    it->cap = 0;
    it->nodes = NULL;
    it->index = NULL;

    if (tree->root) {
        BTreeNode *cur = tree->root;
        while (cur && !cur->leaf) {
            cur = btree_children(cur)[0];
        }
        it->leaf = cur;
        it->leaf_index = 0;
    }
    return (PyObject *)it;
}

static void
BTreeIter_dealloc(BTreeIterObject *it)
{
    PyObject_GC_UnTrack(it);
    Py_XDECREF(it->tree);
    PyMem_Free(it->nodes);
    PyMem_Free(it->index);
    PyObject_GC_Del(it);
}

static int
BTreeIter_traverse(BTreeIterObject *it, visitproc visit, void *arg)
{
    Py_VISIT(it->tree);
    return 0;
}

static int
BTreeIter_clear(BTreeIterObject *it)
{
    Py_CLEAR(it->tree);
    it->leaf = NULL;
    it->leaf_index = 0;
    return 0;
}

static PyObject *
BTreeIter_iternext(BTreeIterObject *it)
{
    if (it->tree && it->expected_mod_count != it->tree->mod_count) {
        PyErr_SetString(PyExc_RuntimeError, "BTree mutated during iteration");
        return NULL;
    }
    while (it->leaf) {
        if (it->leaf_index < it->leaf->n) {
            BTreeLeaf *leaf = btree_leaf(it->leaf);
            PyObject *key = leaf->keys[it->leaf_index];
            PyObject *value = leaf->values[it->leaf_index];
            it->leaf_index += 1;
            if (it->kind == 0) {
                return Py_NewRef(key);
            }
            if (it->kind == 1) {
                return Py_NewRef(value);
            }
            return PyTuple_Pack(2, key, value);
        }
        it->leaf = (BTreeNode *)btree_leaf(it->leaf)->next_leaf;
        it->leaf_index = 0;
    }
    PyErr_SetNone(PyExc_StopIteration);
    return NULL;
}

static int
btree_key_cmp(PyObject *a, PyObject *b)
{
    PyObject *exc_type = NULL;
    PyObject *exc_value = NULL;
    PyObject *exc_tb = NULL;
    PyErr_Fetch(&exc_type, &exc_value, &exc_tb);

    /* 1. Identity Check: Fastest path for identical objects or singletons */
    if (a == b) {
        PyErr_Restore(exc_type, exc_value, exc_tb);
        return 0;
    }

    /* 2. Fast Path: Use direct type comparison if types match.
       This bypasses the overhead of generic rich comparison dispatching. */
    PyTypeObject *tp = Py_TYPE(a);
    if (Py_IS_TYPE(b, tp) && tp->tp_richcompare != NULL) {
        PyObject *res_obj = tp->tp_richcompare(a, b, Py_LT);
        
        if (res_obj == Py_True) {
            Py_DECREF(res_obj);
            PyErr_Restore(exc_type, exc_value, exc_tb);
            return -1;
        }
        if (res_obj == Py_False) {
            Py_DECREF(res_obj);
            // Now check for equality to distinguish between GT and EQ
            res_obj = tp->tp_richcompare(a, b, Py_EQ);
            if (res_obj == Py_True) {
                Py_DECREF(res_obj);
                PyErr_Restore(exc_type, exc_value, exc_tb);
                return 0;
            }
            if (res_obj == Py_False) {
                Py_DECREF(res_obj);
                PyErr_Restore(exc_type, exc_value, exc_tb);
                return 1;
            }
        }
        
        /* Fallback if the direct call returns NULL (error) or NotImplemented */
        if (res_obj == NULL) {
            Py_XDECREF(exc_type);
            Py_XDECREF(exc_value);
            Py_XDECREF(exc_tb);
            return -2;
        }
        Py_DECREF(res_obj); 
    }

    /* 3. General Path: Fallback for different types or complex objects */
    int lt = PyObject_RichCompareBool(a, b, Py_LT);
    if (lt < 0) {
        Py_XDECREF(exc_type);
        Py_XDECREF(exc_value);
        Py_XDECREF(exc_tb);
        return -2; // Error sentinel
    }
    if (lt) {
        PyErr_Restore(exc_type, exc_value, exc_tb);
        return -1;
    }

    int eq = PyObject_RichCompareBool(a, b, Py_EQ);
    if (eq < 0) {
        Py_XDECREF(exc_type);
        Py_XDECREF(exc_value);
        Py_XDECREF(exc_tb);
        return -2;
    }
    if (eq) {
        PyErr_Restore(exc_type, exc_value, exc_tb);
        return 0;
    }

    PyErr_Restore(exc_type, exc_value, exc_tb);
    return 1; // Implicitly Greater Than
}

static int
btree_select_index(BTreeNode *node, Py_ssize_t index, PyObject **key, PyObject **value)
{
    while (node) {
        if (node->leaf) {
            if (index < 0 || index >= node->n) {
                break;
            }
            PyObject **keys = btree_keys(node);
            PyObject **values = btree_values(node);
            *key = keys[index];
            *value = values[index];
            return 0;
        }
        BTreeNode **children = btree_children(node);
        for (int i = 0; i <= node->n; i++) {
            Py_ssize_t child_size = children[i]->subtree_size;
            if (index < child_size) {
                node = children[i];
                goto next_node;
            }
            index -= child_size;
        }
        break;
    next_node:
        ;
    }
    PyErr_SetString(PyExc_IndexError, "index out of range");
    return -1;
}

static int
btree_cmp_i64(int64_t a, int64_t b)
{
    if (a < b) {
        return -1;
    }
    if (a > b) {
        return 1;
    }
    return 0;
}

static int
btree_cmp_f64(double a, double b)
{
    int nan_a = isnan(a);
    int nan_b = isnan(b);
    if (nan_a || nan_b) {
        if (nan_a && nan_b) {
            return 0;
        }
        return nan_a ? 1 : -1;
    }
    if (a < b) {
        return -1;
    }
    if (a > b) {
        return 1;
    }
    return 0;
}

static int
btree_prim_from_key(PyObject *key, int *kind, BTreePrimKey *out)
{
    if (Py_IS_TYPE(key, &PyBool_Type)) {
        *kind = BTREE_PRIM_I64;
        out->i64 = (key == Py_True) ? 1 : 0;
        return 1;
    }
    if (PyLong_CheckExact(key)) {
        int overflow = 0;
        long long v = PyLong_AsLongLongAndOverflow(key, &overflow);
        if (overflow == 0) {
            *kind = BTREE_PRIM_I64;
            out->i64 = (int64_t)v;
            return 1;
        }
        if (PyErr_Occurred()) {
            return -1;
        }
        return 0;
    }
    if (PyFloat_CheckExact(key)) {
        if (isnan(PyFloat_AS_DOUBLE(key))) {
            PyErr_SetString(PyExc_ValueError, "NaN keys are not supported");
            return -1;
        }
        *kind = BTREE_PRIM_F64;
        out->f64 = PyFloat_AS_DOUBLE(key);
        return 1;
    }
    return 0;
}

static int
btree_key_cmp_fast(PyObject *a, PyObject *b, PyTypeObject *tp)
{
    if (tp == &PyBool_Type) {
        if (a == b) {
            return 0;
        }
        return (a == Py_False) ? -1 : 1;
    }

    if (tp == &PyLong_Type && PyLong_CheckExact(a) && PyLong_CheckExact(b)) {
        int overflow_a = 0;
        int overflow_b = 0;
        long long va = PyLong_AsLongLongAndOverflow(a, &overflow_a);
        long long vb = PyLong_AsLongLongAndOverflow(b, &overflow_b);
        if (overflow_a == 0 && overflow_b == 0) {
            return btree_cmp_i64((int64_t)va, (int64_t)vb);
        }
        if (PyErr_Occurred()) {
            return -2;
        }
        return 2;
    }

    if (tp == &PyFloat_Type && PyFloat_CheckExact(a) && PyFloat_CheckExact(b)) {
        double va = PyFloat_AS_DOUBLE(a);
        double vb = PyFloat_AS_DOUBLE(b);
        if (isnan(va) || isnan(vb)) {
            PyErr_SetString(PyExc_ValueError, "NaN keys are not supported");
            return -2;
        }
        return btree_cmp_f64(va, vb);
    }

    if (tp == &PyUnicode_Type && PyUnicode_CheckExact(a) && PyUnicode_CheckExact(b)) {
        int cmp = PyUnicode_Compare(a, b);
        if (cmp < 0) {
            if (PyErr_Occurred()) {
                return -2;
            }
            return -1;
        }
        if (cmp > 0) {
            return 1;
        }
        return 0;
    }

    if (tp == &PyBytes_Type && PyBytes_CheckExact(a) && PyBytes_CheckExact(b)) {
        char *sa = NULL;
        char *sb = NULL;
        Py_ssize_t la = 0;
        Py_ssize_t lb = 0;
        if (PyBytes_AsStringAndSize(a, &sa, &la) < 0) {
            return -2;
        }
        if (PyBytes_AsStringAndSize(b, &sb, &lb) < 0) {
            return -2;
        }
        Py_ssize_t min_len = (la < lb) ? la : lb;
        int cmp = (min_len > 0) ? memcmp(sa, sb, (size_t)min_len) : 0;
        if (cmp < 0) {
            return -1;
        }
        if (cmp > 0) {
            return 1;
        }
        if (la < lb) {
            return -1;
        }
        if (la > lb) {
            return 1;
        }
        return 0;
    }

    PyObject *res_obj = tp->tp_richcompare(a, b, Py_LT);
    if (res_obj == Py_True) {
        Py_DECREF(res_obj);
        return -1;
    }
    if (res_obj == Py_False) {
        Py_DECREF(res_obj);
        res_obj = tp->tp_richcompare(a, b, Py_EQ);
        if (res_obj == Py_True) {
            Py_DECREF(res_obj);
            return 0;
        }
        if (res_obj == Py_False) {
            Py_DECREF(res_obj);
            return 1;
        }
    }
    if (res_obj == NULL) {
        return -2;
    }
    if (res_obj == Py_NotImplemented) {
        Py_DECREF(res_obj);
        return 2;
    }
    Py_DECREF(res_obj);
    return 2;
}

static int
btree_find_index_i64(BTreeNode *node, int64_t key, int *found)
{
    BTreePrimKey *pkeys = btree_prim_keys(node);
    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp = btree_cmp_i64(pkeys[mid].i64, key);
        if (cmp < 0) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    *found = (lo < node->n && btree_cmp_i64(pkeys[lo].i64, key) == 0);
    return lo;
}

static int
btree_find_child_i64(BTreeNode *node, int64_t key)
{
    BTreePrimKey *pkeys = btree_prim_keys(node);
    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp = btree_cmp_i64(pkeys[mid].i64, key);
        if (cmp > 0) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return lo;
}

static int
btree_find_index_f64(BTreeNode *node, double key, int *found)
{
    BTreePrimKey *pkeys = btree_prim_keys(node);
    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp = btree_cmp_f64(pkeys[mid].f64, key);
        if (cmp < 0) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    *found = (lo < node->n && btree_cmp_f64(pkeys[lo].f64, key) == 0);
    return lo;
}

static int
btree_find_child_f64(BTreeNode *node, double key)
{
    BTreePrimKey *pkeys = btree_prim_keys(node);
    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp = btree_cmp_f64(pkeys[mid].f64, key);
        if (cmp > 0) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return lo;
}

static int
btree_find_index_typed(BTreeNode *node, PyObject *key, int *found, PyTypeObject *tp, int use_fast)
{
    PyObject **keys = btree_keys(node);

    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp;
        if (use_fast) {
            cmp = btree_key_cmp_fast(keys[mid], key, tp);
            if (cmp == 2) {
                use_fast = 0;
                cmp = btree_key_cmp(keys[mid], key);
            }
        } else {
            cmp = btree_key_cmp(keys[mid], key);
        }
        if (cmp == -2) {
            return -1;
        }
        if (cmp < 0) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }

    if (lo < node->n) {
        int eq;
        if (use_fast) {
            eq = btree_key_cmp_fast(keys[lo], key, tp);
            if (eq == 2) {
                eq = btree_key_cmp(keys[lo], key);
            }
        } else {
            eq = btree_key_cmp(keys[lo], key);
        }
        if (eq == -2) {
            return -1;
        }
        *found = (eq == 0);
    } else {
        *found = 0;
    }
    return lo;
}

static int
btree_find_child_typed(BTreeNode *node, PyObject *key, PyTypeObject *tp, int use_fast)
{
    PyObject **keys = btree_keys(node);
    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp;
        if (use_fast) {
            cmp = btree_key_cmp_fast(keys[mid], key, tp);
            if (cmp == 2) {
                use_fast = 0;
                cmp = btree_key_cmp(keys[mid], key);
            }
        } else {
            cmp = btree_key_cmp(keys[mid], key);
        }
        if (cmp == -2) {
            return -1;
        }
        if (cmp > 0) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return lo;
}

static int
btree_find_index(BTreeNode *node, PyObject *key, int *found)
{
    PyTypeObject *tp = NULL;
    int use_fast = 0;
    PyObject **keys = btree_keys(node);
    if (node->n > 0 && Py_TYPE(key) == Py_TYPE(keys[0])) {
        tp = Py_TYPE(key);
        use_fast = (tp->tp_richcompare != NULL);
    }

    /* Binary search: find leftmost index where keys[idx] >= key */
    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp;
        if (use_fast) {
            cmp = btree_key_cmp_fast(keys[mid], key, tp);
            if (cmp == 2) {
                use_fast = 0;
                cmp = btree_key_cmp(keys[mid], key);
            }
        } else {
            cmp = btree_key_cmp(keys[mid], key);
        }
        if (cmp == -2) {
            return -1;
        }
        if (cmp < 0) {
            /* keys[mid] < key */
            lo = mid + 1;
        } else {
            /* keys[mid] >= key */
            hi = mid;
        }
    }

    /* lo is now the insertion point; check if we found an exact match */
    if (lo < node->n) {
        int eq;
        if (use_fast) {
            eq = btree_key_cmp_fast(keys[lo], key, tp);
            if (eq == 2) {
                eq = btree_key_cmp(keys[lo], key);
            }
        } else {
            eq = btree_key_cmp(keys[lo], key);
        }
        if (eq == -2) {
            return -1;
        }
        *found = (eq == 0);
    } else {
        *found = 0;
    }
    return lo;
}

static int
btree_find_child(BTreeNode *node, PyObject *key)
{
    PyTypeObject *tp = NULL;
    int use_fast = 0;
    PyObject **keys = btree_keys(node);
    if (node->n > 0 && Py_TYPE(key) == Py_TYPE(keys[0])) {
        tp = Py_TYPE(key);
        use_fast = (tp->tp_richcompare != NULL);
    }

    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp;
        if (use_fast) {
            cmp = btree_key_cmp_fast(keys[mid], key, tp);
            if (cmp == 2) {
                use_fast = 0;
                cmp = btree_key_cmp(keys[mid], key);
            }
        } else {
            cmp = btree_key_cmp(keys[mid], key);
        }
        if (cmp == -2) {
            return -1;
        }
        if (cmp > 0) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return lo;
}

static int
btree_split_child(BTreeNode *parent, int idx, int prim_kind)
{
    BTreeNode **pchildren = btree_children(parent);
    BTreeNode *full = pchildren[idx];
    BTreeNode *right = btree_node_new(full->leaf);
    if (!right) {
        return -1;
    }

    if (full->leaf) {
        /* Leaf split: keep all keys in leaves; copy separator to parent. */
        int left_n = BTREE_LEAF_MIN_DEGREE;
        int right_n = full->n - left_n;
        right->n = right_n;
        BTreeLeaf *full_leaf = btree_leaf(full);
        BTreeLeaf *right_leaf = btree_leaf(right);
        for (int j = 0; j < right_n; j++) {
            right_leaf->keys[j] = full_leaf->keys[j + left_n];
            right_leaf->values[j] = full_leaf->values[j + left_n];
            if (prim_kind != BTREE_PRIM_NONE) {
                right_leaf->prim_keys[j] = full_leaf->prim_keys[j + left_n];
            }
            full_leaf->keys[j + left_n] = NULL;
            full_leaf->values[j + left_n] = NULL;
        }
        full->n = left_n;

        right_leaf->next_leaf = full_leaf->next_leaf;
        full_leaf->next_leaf = right_leaf;

        /* Shift parent children to make room for the new right node */
        for (int j = parent->n; j >= idx + 1; j--) {
            pchildren[j + 1] = pchildren[j];
        }
        pchildren[idx + 1] = right;

        /* Shift parent keys and insert separator (copy from right->keys[0]) */
        PyObject **pkeys = btree_keys(parent);
        BTreePrimKey *pprim = btree_internal(parent)->prim_keys;
        for (int j = parent->n - 1; j >= idx; j--) {
            pkeys[j + 1] = pkeys[j];
            if (prim_kind != BTREE_PRIM_NONE) {
                pprim[j + 1] = pprim[j];
            }
        }
        Py_INCREF(right_leaf->keys[0]);
        pkeys[idx] = right_leaf->keys[0];
        if (prim_kind != BTREE_PRIM_NONE) {
            pprim[idx] = right_leaf->prim_keys[0];
        }

        parent->n += 1;
        btree_recompute_subtree(full);
        btree_recompute_subtree(right);
        btree_recompute_subtree(parent);
        return 0;
    }

    /* Internal node split: move median key up, split children. */
    right->n = BTREE_INTERNAL_MIN_DEGREE - 1;
    BTreeInternal *full_in = btree_internal(full);
    BTreeInternal *right_in = btree_internal(right);
    for (int j = 0; j < BTREE_INTERNAL_MIN_DEGREE - 1; j++) {
        right_in->keys[j] = full_in->keys[j + BTREE_INTERNAL_MIN_DEGREE];
        if (prim_kind != BTREE_PRIM_NONE) {
            right_in->prim_keys[j] = full_in->prim_keys[j + BTREE_INTERNAL_MIN_DEGREE];
        }
        full_in->keys[j + BTREE_INTERNAL_MIN_DEGREE] = NULL;
    }

    for (int j = 0; j < BTREE_INTERNAL_MIN_DEGREE; j++) {
        right_in->children[j] = full_in->children[j + BTREE_INTERNAL_MIN_DEGREE];
        full_in->children[j + BTREE_INTERNAL_MIN_DEGREE] = NULL;
    }

    full->n = BTREE_INTERNAL_MIN_DEGREE - 1;

    for (int j = parent->n; j >= idx + 1; j--) {
        pchildren[j + 1] = pchildren[j];
    }
    pchildren[idx + 1] = right;

    PyObject **pkeys = btree_keys(parent);
    BTreePrimKey *pprim = btree_internal(parent)->prim_keys;
    for (int j = parent->n - 1; j >= idx; j--) {
        pkeys[j + 1] = pkeys[j];
        if (prim_kind != BTREE_PRIM_NONE) {
            pprim[j + 1] = pprim[j];
        }
    }
    pkeys[idx] = full_in->keys[BTREE_INTERNAL_MIN_DEGREE - 1];
    if (prim_kind != BTREE_PRIM_NONE) {
        pprim[idx] = full_in->prim_keys[BTREE_INTERNAL_MIN_DEGREE - 1];
    }
    full_in->keys[BTREE_INTERNAL_MIN_DEGREE - 1] = NULL;

    parent->n += 1;
    btree_recompute_subtree(full);
    btree_recompute_subtree(right);
    btree_recompute_subtree(parent);

    return 0;
}

static int
btree_insert_nonfull(BTreeNode *node, PyObject *key, PyObject *value, int *inserted,
                     PyTypeObject *tp, int use_fast, int prim_kind, const BTreePrimKey *prim_key)
{
    BTreeNode **stack = NULL;
    Py_ssize_t stack_size = 0;
    Py_ssize_t stack_cap = 0;

    while (!node->leaf) {
        if (stack_size == stack_cap) {
            Py_ssize_t new_cap = (stack_cap == 0) ? 16 : stack_cap * 2;
            BTreeNode **new_stack = PyMem_Realloc(stack, new_cap * sizeof(BTreeNode *));
            if (!new_stack) {
                PyMem_Free(stack);
                PyErr_NoMemory();
                return -1;
            }
            stack = new_stack;
            stack_cap = new_cap;
        }
        stack[stack_size++] = node;

        int idx;
        if (prim_kind == BTREE_PRIM_I64 && prim_key) {
            idx = btree_find_child_i64(node, prim_key->i64);
        } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
            idx = btree_find_child_f64(node, prim_key->f64);
        } else {
            idx = btree_find_child_typed(node, key, tp, use_fast);
        }
        if (idx < 0) {
            PyMem_Free(stack);
            return -1;
        }

        BTreeNode **children = btree_children(node);
        if (children[idx]->n == btree_max_keys(children[idx])) {
            if (btree_split_child(node, idx, prim_kind) < 0) {
                PyMem_Free(stack);
                return -1;
            }
            PyObject **keys = btree_keys(node);
            int cmp;
            if (prim_kind == BTREE_PRIM_I64 && prim_key) {
                cmp = btree_cmp_i64(btree_prim_keys(node)[idx].i64, prim_key->i64);
            } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
                cmp = btree_cmp_f64(btree_prim_keys(node)[idx].f64, prim_key->f64);
            } else if (use_fast) {
                cmp = btree_key_cmp_fast(keys[idx], key, tp);
                if (cmp == 2) {
                    cmp = btree_key_cmp(keys[idx], key);
                }
            } else {
                cmp = btree_key_cmp(keys[idx], key);
            }
            if (cmp == -2) {
                PyMem_Free(stack);
                return -1;
            }
            if (cmp <= 0) {
                idx++;
            }
        }

        node = children[idx];
    }

    int found = 0;
    int idx;
    if (prim_kind == BTREE_PRIM_I64 && prim_key) {
        idx = btree_find_index_i64(node, prim_key->i64, &found);
    } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
        idx = btree_find_index_f64(node, prim_key->f64, &found);
    } else {
        idx = btree_find_index_typed(node, key, &found, tp, use_fast);
    }
    if (idx < 0) {
        PyMem_Free(stack);
        return -1;
    }

    if (found) {
        /* Key exists: update value only. subtree_size remains the same. */
        Py_INCREF(value);
        PyObject **values = btree_values(node);
        Py_DECREF(values[idx]);
        values[idx] = value;
        *inserted = 0;
        PyMem_Free(stack);
        return 0;
    }

    /* Shift and insert new key/value */
    PyObject **keys = btree_keys(node);
    PyObject **values = btree_values(node);
    BTreePrimKey *pkeys = btree_prim_keys(node);
    if (node->n > idx) {
        size_t count = (size_t)(node->n - idx);
        memmove(&keys[idx + 1], &keys[idx], count * sizeof(PyObject *));
        memmove(&values[idx + 1], &values[idx], count * sizeof(PyObject *));
        if (prim_kind != BTREE_PRIM_NONE) {
            memmove(&pkeys[idx + 1], &pkeys[idx], count * sizeof(BTreePrimKey));
        }
    }

    Py_INCREF(key);
    Py_INCREF(value);
    keys[idx] = key;
    values[idx] = value;
    if (prim_kind != BTREE_PRIM_NONE && prim_key) {
        pkeys[idx] = *prim_key;
    }

    /* RANKED UPDATE: Increment local and subtree counts */
    node->n += 1;
    node->subtree_size = node->n;
    *inserted = 1;

    for (Py_ssize_t i = 0; i < stack_size; i++) {
        stack[i]->subtree_size += 1;
    }

    PyMem_Free(stack);
    return 0;
}

static PyObject *
btree_search(BTreeNode *node, PyObject *key, PyTypeObject *tp, int use_fast,
             int prim_kind, const BTreePrimKey *prim_key)
{
    /* Security Procedure: Protect the C stack from deep recursion */
    if (Py_EnterRecursiveCall(" in btree_search")) {
        return NULL;
    }

    PyObject **keys = btree_keys(node);

    if (node->leaf) {
        int lo = 0, hi = node->n;
        while (lo < hi) {
            int mid = (lo + hi) / 2;
            int cmp;
            if (prim_kind == BTREE_PRIM_I64 && prim_key) {
                cmp = btree_cmp_i64(btree_prim_keys(node)[mid].i64, prim_key->i64);
            } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
                cmp = btree_cmp_f64(btree_prim_keys(node)[mid].f64, prim_key->f64);
            } else if (use_fast) {
                cmp = btree_key_cmp_fast(keys[mid], key, tp);
                if (cmp == 2) {
                    cmp = btree_key_cmp(keys[mid], key);
                }
            } else {
                cmp = btree_key_cmp(keys[mid], key);
            }
            if (cmp == -2) {
                Py_LeaveRecursiveCall();
                return NULL;
            }
            if (cmp == 0) {
                Py_LeaveRecursiveCall();
                PyObject **values = btree_values(node);
                return Py_NewRef(values[mid]);
            }
            if (cmp > 0) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        PyErr_SetObject(PyExc_KeyError, key);
        Py_LeaveRecursiveCall();
        return NULL;
    }

    int lo = 0, hi = node->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int cmp;
        if (prim_kind == BTREE_PRIM_I64 && prim_key) {
            cmp = btree_cmp_i64(btree_prim_keys(node)[mid].i64, prim_key->i64);
        } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
            cmp = btree_cmp_f64(btree_prim_keys(node)[mid].f64, prim_key->f64);
        } else if (use_fast) {
            cmp = btree_key_cmp_fast(keys[mid], key, tp);
            if (cmp == 2) {
                cmp = btree_key_cmp(keys[mid], key);
            }
        } else {
            cmp = btree_key_cmp(keys[mid], key);
        }
        if (cmp == -2) {
            Py_LeaveRecursiveCall();
            return NULL;
        }
        if (cmp > 0) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }

    BTreeNode **children = btree_children(node);
    PyObject *result = btree_search(children[lo], key, tp, use_fast, prim_kind, prim_key);
    Py_LeaveRecursiveCall();
    return result;
}

static void
btree_merge(BTreeNode *node, int idx, int prim_kind);

static int
btree_remove(BTreeNode *node, PyObject *key, Py_ssize_t *size, int prim_kind,
             PyTypeObject *tp, int use_fast, const BTreePrimKey *prim_key,
             int *min_changed, PyObject **new_min, BTreePrimKey *new_prim);

static void
btree_remove_from_leaf(BTreeNode *node, int idx, int prim_kind)
{
    PyObject **keys = btree_keys(node);
    PyObject **values = btree_values(node);
    BTreePrimKey *pkeys = btree_prim_keys(node);
    Py_DECREF(keys[idx]);
    Py_DECREF(values[idx]);
    for (int i = idx + 1; i < node->n; i++) {
        keys[i - 1] = keys[i];
        values[i - 1] = values[i];
        if (prim_kind != BTREE_PRIM_NONE) {
            pkeys[i - 1] = pkeys[i];
        }
    }
    node->n -= 1;
}

static void
btree_borrow_from_prev(BTreeNode *node, int idx, int prim_kind)
{
    BTreeNode **children = btree_children(node);
    BTreeNode *child = children[idx];
    BTreeNode *sibling = children[idx - 1];

    if (child->leaf) {
        PyObject **ckeys = btree_keys(child);
        PyObject **cvalues = btree_values(child);
        BTreePrimKey *cprim = btree_prim_keys(child);
        PyObject **skeys = btree_keys(sibling);
        PyObject **svalues = btree_values(sibling);
        BTreePrimKey *sprim = btree_prim_keys(sibling);
        for (int i = child->n - 1; i >= 0; i--) {
            ckeys[i + 1] = ckeys[i];
            cvalues[i + 1] = cvalues[i];
            if (prim_kind != BTREE_PRIM_NONE) {
                cprim[i + 1] = cprim[i];
            }
        }
        ckeys[0] = skeys[sibling->n - 1];
        cvalues[0] = svalues[sibling->n - 1];
        if (prim_kind != BTREE_PRIM_NONE) {
            cprim[0] = sprim[sibling->n - 1];
        }
        skeys[sibling->n - 1] = NULL;
        svalues[sibling->n - 1] = NULL;
        sibling->n -= 1;
        child->n += 1;

        PyObject **pkeys = btree_keys(node);
        BTreePrimKey *pprim = btree_internal(node)->prim_keys;
        Py_DECREF(pkeys[idx - 1]);
        Py_INCREF(ckeys[0]);
        pkeys[idx - 1] = ckeys[0];
        if (prim_kind != BTREE_PRIM_NONE) {
            pprim[idx - 1] = cprim[0];
        }
        btree_recompute_subtree(sibling);
        btree_recompute_subtree(child);
        btree_recompute_subtree(node);
        return;
    }

    PyObject **ckeys = btree_keys(child);
    PyObject **skeys = btree_keys(sibling);
    BTreePrimKey *cprim = btree_prim_keys(child);
    BTreePrimKey *sprim = btree_prim_keys(sibling);
    for (int i = child->n - 1; i >= 0; i--) {
        ckeys[i + 1] = ckeys[i];
        if (prim_kind != BTREE_PRIM_NONE) {
            cprim[i + 1] = cprim[i];
        }
    }
    BTreeNode **cchildren = btree_children(child);
    BTreeNode **schildren = btree_children(sibling);
    for (int i = child->n; i >= 0; i--) {
        cchildren[i + 1] = cchildren[i];
    }

    PyObject **pkeys = btree_keys(node);
    BTreePrimKey *pprim = btree_internal(node)->prim_keys;
    ckeys[0] = pkeys[idx - 1];
    if (prim_kind != BTREE_PRIM_NONE) {
        cprim[0] = pprim[idx - 1];
    }
    cchildren[0] = schildren[sibling->n];

    pkeys[idx - 1] = skeys[sibling->n - 1];
    if (prim_kind != BTREE_PRIM_NONE) {
        pprim[idx - 1] = sprim[sibling->n - 1];
    }
    skeys[sibling->n - 1] = NULL;

    sibling->n -= 1;
    child->n += 1;
    btree_recompute_subtree(sibling);
    btree_recompute_subtree(child);
    btree_recompute_subtree(node);
}

static void
btree_borrow_from_next(BTreeNode *node, int idx, int prim_kind)
{
    BTreeNode **children = btree_children(node);
    BTreeNode *child = children[idx];
    BTreeNode *sibling = children[idx + 1];

    if (child->leaf) {
        PyObject **ckeys = btree_keys(child);
        PyObject **cvalues = btree_values(child);
        BTreePrimKey *cprim = btree_prim_keys(child);
        PyObject **skeys = btree_keys(sibling);
        PyObject **svalues = btree_values(sibling);
        BTreePrimKey *sprim = btree_prim_keys(sibling);
        ckeys[child->n] = skeys[0];
        cvalues[child->n] = svalues[0];
        if (prim_kind != BTREE_PRIM_NONE) {
            cprim[child->n] = sprim[0];
        }
        for (int i = 1; i < sibling->n; i++) {
            skeys[i - 1] = skeys[i];
            svalues[i - 1] = svalues[i];
            if (prim_kind != BTREE_PRIM_NONE) {
                sprim[i - 1] = sprim[i];
            }
        }
        skeys[sibling->n - 1] = NULL;
        svalues[sibling->n - 1] = NULL;
        sibling->n -= 1;
        child->n += 1;

        PyObject **pkeys = btree_keys(node);
        BTreePrimKey *pprim = btree_internal(node)->prim_keys;
        Py_DECREF(pkeys[idx]);
        Py_INCREF(skeys[0]);
        pkeys[idx] = skeys[0];
        if (prim_kind != BTREE_PRIM_NONE) {
            pprim[idx] = sprim[0];
        }
        btree_recompute_subtree(sibling);
        btree_recompute_subtree(child);
        btree_recompute_subtree(node);
        return;
    }

    PyObject **ckeys = btree_keys(child);
    PyObject **skeys = btree_keys(sibling);
    BTreePrimKey *cprim = btree_prim_keys(child);
    BTreePrimKey *sprim = btree_prim_keys(sibling);
    BTreeNode **cchildren = btree_children(child);
    BTreeNode **schildren = btree_children(sibling);
    PyObject **pkeys = btree_keys(node);
    BTreePrimKey *pprim = btree_internal(node)->prim_keys;
    ckeys[child->n] = pkeys[idx];
    if (prim_kind != BTREE_PRIM_NONE) {
        cprim[child->n] = pprim[idx];
    }
    cchildren[child->n + 1] = schildren[0];

    pkeys[idx] = skeys[0];
    if (prim_kind != BTREE_PRIM_NONE) {
        pprim[idx] = sprim[0];
    }

    for (int i = 1; i < sibling->n; i++) {
        skeys[i - 1] = skeys[i];
        if (prim_kind != BTREE_PRIM_NONE) {
            sprim[i - 1] = sprim[i];
        }
    }
    for (int i = 1; i <= sibling->n; i++) {
        schildren[i - 1] = schildren[i];
    }
    skeys[sibling->n - 1] = NULL;

    sibling->n -= 1;
    child->n += 1;
    btree_recompute_subtree(sibling);
    btree_recompute_subtree(child);
    btree_recompute_subtree(node);
}

/*
 * btree_merge: Merges sibling at children[idx+1] into children[idx].
 *
 * Reference ownership notes:
 * - For leaf nodes: keys/values are MOVED (not copied) from sibling to child.
 *   The sibling's slots become invalid, so we use btree_node_free_raw() which
 *   only frees memory without decrementing references. The parent separator
 *   key IS decremented since it's no longer needed.
 * - For internal nodes: sibling's keys/children are moved, and the parent's
 *   separator key is moved down (not copied). No reference count changes needed
 *   for moved pointers.
 */
static void
btree_merge(BTreeNode *node, int idx, int prim_kind)
{
    BTreeNode **children = btree_children(node);
    BTreeNode *child = children[idx];
    BTreeNode *sibling = children[idx + 1];

    if (child->leaf) {
        PyObject **ckeys = btree_keys(child);
        PyObject **cvalues = btree_values(child);
        BTreePrimKey *cprim = btree_prim_keys(child);
        PyObject **skeys = btree_keys(sibling);
        PyObject **svalues = btree_values(sibling);
        BTreePrimKey *sprim = btree_prim_keys(sibling);
        /* Move keys/values from sibling to child - no refcount change needed
         * since we're transferring ownership, not copying */
        for (int i = 0; i < sibling->n; i++) {
            ckeys[child->n + i] = skeys[i];
            cvalues[child->n + i] = svalues[i];
            if (prim_kind != BTREE_PRIM_NONE) {
                cprim[child->n + i] = sprim[i];
            }
        }
        child->n += sibling->n;
        btree_leaf(child)->next_leaf = btree_leaf(sibling)->next_leaf;

        /* The parent separator key is no longer needed - decref it */
        PyObject **pkeys = btree_keys(node);
        Py_DECREF(pkeys[idx]);
        pkeys[idx] = NULL;
    } else {
        PyObject **ckeys = btree_keys(child);
        PyObject **skeys = btree_keys(sibling);
        BTreePrimKey *cprim = btree_prim_keys(child);
        BTreePrimKey *sprim = btree_prim_keys(sibling);
        BTreeNode **cchildren = btree_children(child);
        BTreeNode **schildren = btree_children(sibling);
        PyObject **pkeys = btree_keys(node);
        BTreePrimKey *pprim = btree_internal(node)->prim_keys;
        ckeys[BTREE_INTERNAL_MIN_DEGREE - 1] = pkeys[idx];
        if (prim_kind != BTREE_PRIM_NONE) {
            cprim[BTREE_INTERNAL_MIN_DEGREE - 1] = pprim[idx];
        }

        for (int i = 0; i < sibling->n; i++) {
            ckeys[i + BTREE_INTERNAL_MIN_DEGREE] = skeys[i];
            if (prim_kind != BTREE_PRIM_NONE) {
                cprim[i + BTREE_INTERNAL_MIN_DEGREE] = sprim[i];
            }
        }
        for (int i = 0; i <= sibling->n; i++) {
            cchildren[i + BTREE_INTERNAL_MIN_DEGREE] = schildren[i];
        }
        child->n += sibling->n + 1;

        pkeys[idx] = NULL;
    }

    for (int i = idx + 1; i < node->n; i++) {
        btree_keys(node)[i - 1] = btree_keys(node)[i];
        if (prim_kind != BTREE_PRIM_NONE) {
            btree_internal(node)->prim_keys[i - 1] = btree_internal(node)->prim_keys[i];
        }
    }
    for (int i = idx + 2; i <= node->n; i++) {
        children[i - 1] = children[i];
    }

    node->n -= 1;
    btree_node_free_raw(sibling);
    btree_recompute_subtree(child);
    btree_recompute_subtree(node);
}

static int
btree_fill(BTreeNode *node, int idx, int prim_kind)
{
    BTreeNode **children = btree_children(node);
    int min_degree = btree_min_degree(children[idx]);
    if (idx != 0 && children[idx - 1]->n >= min_degree) {
        btree_borrow_from_prev(node, idx, prim_kind);
        return 0;
    }

    if (idx != node->n && children[idx + 1]->n >= min_degree) {
        btree_borrow_from_next(node, idx, prim_kind);
        return 0;
    }

    if (idx != node->n) {
        btree_merge(node, idx, prim_kind);
    } else {
        btree_merge(node, idx - 1, prim_kind);
    }

    return 0;
}

static int
btree_remove(BTreeNode *node, PyObject *key, Py_ssize_t *size, int prim_kind,
             PyTypeObject *tp, int use_fast, const BTreePrimKey *prim_key,
             int *min_changed, PyObject **new_min, BTreePrimKey *new_prim)
{
    /* Security Procedure: Protect the C stack */
    if (Py_EnterRecursiveCall(" in btree_remove")) {
        return -1;
    }

    if (min_changed) {
        *min_changed = 0;
    }
    if (new_min) {
        *new_min = NULL;
    }

    if (node->leaf) {
        int found = 0;
        int idx;
        if (prim_kind == BTREE_PRIM_I64 && prim_key) {
            idx = btree_find_index_i64(node, prim_key->i64, &found);
        } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
            idx = btree_find_index_f64(node, prim_key->f64, &found);
        } else {
            idx = btree_find_index_typed(node, key, &found, tp, use_fast);
        }
        if (idx < 0) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        if (!found) {
            PyErr_SetObject(PyExc_KeyError, key);
            Py_LeaveRecursiveCall();
            return -1;
        }
        int was_first = (idx == 0);
        btree_remove_from_leaf(node, idx, prim_kind);
        node->subtree_size -= 1;
        *size -= 1;
        if (was_first && node->n > 0 && min_changed && new_min) {
            PyObject **keys = btree_keys(node);
            *min_changed = 1;
            *new_min = keys[0];
            if (prim_kind != BTREE_PRIM_NONE && new_prim) {
                *new_prim = btree_prim_keys(node)[0];
            }
        }
        Py_LeaveRecursiveCall();
        return 0;
    }

    int idx;
    if (prim_kind == BTREE_PRIM_I64 && prim_key) {
        idx = btree_find_child_i64(node, prim_key->i64);
    } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
        idx = btree_find_child_f64(node, prim_key->f64);
    } else {
        idx = btree_find_child_typed(node, key, tp, use_fast);
    }
    if (idx < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }

    BTreeNode **children = btree_children(node);
    if (children[idx]->n < btree_min_degree(children[idx])) {
        if (btree_fill(node, idx, prim_kind) < 0) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        if (idx > node->n) {
            idx--;
        }
    }

    Py_ssize_t old_size = *size;
    int child_min_changed = 0;
    PyObject *child_new_min = NULL;
    BTreePrimKey child_new_prim;
    if (btree_remove(children[idx], key, size, prim_kind,
                     tp, use_fast, prim_key,
                     &child_min_changed, &child_new_min, &child_new_prim) < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }
    if (*size < old_size) {
        node->subtree_size -= 1;
    }
    if (child_min_changed && child_new_min) {
        if (idx > 0) {
            PyObject **pkeys = btree_keys(node);
            Py_DECREF(pkeys[idx - 1]);
            Py_INCREF(child_new_min);
            pkeys[idx - 1] = child_new_min;
            if (prim_kind != BTREE_PRIM_NONE) {
                btree_internal(node)->prim_keys[idx - 1] = child_new_prim;
            }
        } else if (min_changed && new_min) {
            *min_changed = 1;
            *new_min = child_new_min;
            if (prim_kind != BTREE_PRIM_NONE && new_prim) {
                *new_prim = child_new_prim;
            }
        }
    }

    Py_LeaveRecursiveCall();
    return 0;
}

static int
btree_remove_cached_path(BTreeObject *self, PyObject *key)
{
    if (!self->root || !self->cache_key || self->cache_key != key) {
        return 1;
    }
    if (self->cache_version != self->mod_count || self->cache_depth <= 0) {
        return 1;
    }

    if (self->cache_nodes[0] != self->root) {
        return 1;
    }

    for (Py_ssize_t level = 0; level < self->cache_depth - 1; level++) {
        BTreeNode *node = self->cache_nodes[level];
        if (node->leaf) {
            return 1;
        }
        BTreeNode *child = self->cache_nodes[level + 1];
        BTreeNode **children = btree_children(node);
        int idx = -1;
        for (int i = 0; i <= node->n; i++) {
            if (children[i] == child) {
                idx = i;
                break;
            }
        }
        if (idx < 0) {
            return 1;
        }

        if (children[idx]->n < btree_min_degree(children[idx])) {
            if (btree_fill(node, idx, self->prim_kind) < 0) {
                return -1;
            }
            if (idx > node->n) {
                idx--;
            }
        }

        children = btree_children(node);
        if (idx < 0 || idx > node->n) {
            return 1;
        }
        if (children[idx] != child) {
            idx = -1;
            for (int i = 0; i <= node->n; i++) {
                if (children[i] == child) {
                    idx = i;
                    break;
                }
            }
            if (idx < 0) {
                return 1;
            }
        }
    }

    BTreeNode *leaf = self->cache_nodes[self->cache_depth - 1];
    if (!leaf || !leaf->leaf) {
        return 1;
    }

    int prim_kind = self->prim_kind;
    BTreePrimKey prim_key;
    const BTreePrimKey *prim_ptr = NULL;
    if (prim_kind == BTREE_PRIM_I64 || prim_kind == BTREE_PRIM_F64) {
        int kind_tmp = BTREE_PRIM_NONE;
        int r = btree_prim_from_key(key, &kind_tmp, &prim_key);
        if (r < 0) {
            return -1;
        }
        if (r == 1 && kind_tmp == prim_kind) {
            prim_ptr = &prim_key;
        } else {
            prim_kind = BTREE_PRIM_NONE;
        }
    }

    int found = 0;
    int idx;
    if (prim_kind == BTREE_PRIM_I64 && prim_ptr) {
        idx = btree_find_index_i64(leaf, prim_ptr->i64, &found);
    } else if (prim_kind == BTREE_PRIM_F64 && prim_ptr) {
        idx = btree_find_index_f64(leaf, prim_ptr->f64, &found);
    } else {
        PyTypeObject *tp = Py_TYPE(key);
        int use_fast = (self->key_type == tp && tp->tp_richcompare != NULL);
        idx = btree_find_index_typed(leaf, key, &found, tp, use_fast);
    }
    if (idx < 0) {
        return -1;
    }
    if (!found) {
        PyErr_SetObject(PyExc_KeyError, key);
        return -1;
    }

    int was_first = (idx == 0);
    btree_remove_from_leaf(leaf, idx, self->prim_kind);
    leaf->subtree_size -= 1;
    self->size -= 1;

    for (Py_ssize_t level = 0; level < self->cache_depth - 1; level++) {
        self->cache_nodes[level]->subtree_size -= 1;
    }

    if (was_first && leaf->n > 0) {
        PyObject *new_min = btree_keys(leaf)[0];
        BTreePrimKey new_prim;
        if (self->prim_kind != BTREE_PRIM_NONE) {
            new_prim = btree_prim_keys(leaf)[0];
        }
        for (Py_ssize_t level = self->cache_depth - 2; level >= 0; level--) {
            BTreeNode *parent = self->cache_nodes[level];
            BTreeNode **children = btree_children(parent);
            int child_idx = -1;
            for (int i = 0; i <= parent->n; i++) {
                if (children[i] == (level + 1 == self->cache_depth - 1 ? leaf : self->cache_nodes[level + 1])) {
                    child_idx = i;
                    break;
                }
            }
            if (child_idx < 0) {
                break;
            }
            if (child_idx > 0) {
                PyObject **pkeys = btree_keys(parent);
                Py_DECREF(pkeys[child_idx - 1]);
                Py_INCREF(new_min);
                pkeys[child_idx - 1] = new_min;
                if (self->prim_kind != BTREE_PRIM_NONE) {
                    btree_internal(parent)->prim_keys[child_idx - 1] = new_prim;
                }
                break;
            }
            /* child_idx == 0: propagate to higher parent */
        }
    }

    return 0;
}

static int
btree_insert_item(BTreeObject *self, PyObject *key, PyObject *value)
{
    if (btree_check_nan_key(key) < 0) {
        return -1;
    }
    if (btree_guard_enter(self) < 0) {
        return -1;
    }
    int rc = -1;
    if (!self->root) {
        self->root = btree_node_new(1);
        if (!self->root) {
            goto out;
        }
    }

    if (self->root->n == btree_max_keys(self->root)) {
        BTreeNode *new_root = btree_node_new(0);
        if (!new_root) {
            goto out;
        }
        btree_children(new_root)[0] = self->root;
        if (btree_split_child(new_root, 0, self->prim_kind) < 0) {
            btree_node_free_raw(new_root);
            goto out;
        }
        btree_recompute_subtree(new_root);
        self->root = new_root;
    }

    PyTypeObject *tp = Py_TYPE(key);
    if (self->size == 0) {
        self->key_type = tp;
    } else if (self->key_type && self->key_type != tp) {
        self->key_type = NULL;
    }
    int use_fast = (self->key_type == tp && tp->tp_richcompare != NULL);

    int prim_kind = self->prim_kind;
    BTreePrimKey prim_key;
    const BTreePrimKey *prim_ptr = NULL;
    if (prim_kind != BTREE_PRIM_NONE) {
        int kind_tmp = BTREE_PRIM_NONE;
        int r = btree_prim_from_key(key, &kind_tmp, &prim_key);
        if (r < 0) {
            goto out;
        }
        if (prim_kind == BTREE_PRIM_UNKNOWN) {
            if (r == 1) {
                prim_kind = kind_tmp;
                self->prim_kind = kind_tmp;
                prim_ptr = &prim_key;
            } else {
                prim_kind = BTREE_PRIM_NONE;
                self->prim_kind = BTREE_PRIM_NONE;
            }
        } else if (r == 1 && kind_tmp == prim_kind) {
            prim_ptr = &prim_key;
        } else {
            prim_kind = BTREE_PRIM_NONE;
            self->prim_kind = BTREE_PRIM_NONE;
        }
    }

    int inserted = 0;
    if (btree_insert_nonfull(self->root, key, value, &inserted, tp, use_fast,
                             prim_kind, prim_ptr) < 0) {
        goto out;
    }
    if (inserted) {
        self->size += 1;
    }
    btree_cache_clear(self);
    self->mod_count += 1;
    rc = 0;
out:
    btree_guard_exit(self);
    return rc;
}

static int
btree_increment_nonfull(BTreeNode *node, PyObject *key, PyObject *delta, PyObject *default_value,
                        int *inserted, PyObject **out_value, PyTypeObject *tp, int use_fast,
                        int prim_kind, const BTreePrimKey *prim_key)
{
    if (Py_EnterRecursiveCall(" in btree_increment_nonfull")) {
        return -1;
    }

    if (node->leaf) {
        int found = 0;
        int idx;
        if (prim_kind == BTREE_PRIM_I64 && prim_key) {
            idx = btree_find_index_i64(node, prim_key->i64, &found);
        } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
            idx = btree_find_index_f64(node, prim_key->f64, &found);
        } else {
            idx = btree_find_index_typed(node, key, &found, tp, use_fast);
        }
        if (idx < 0) {
            Py_LeaveRecursiveCall();
            return -1;
        }

        PyObject **values = btree_values(node);
        PyObject *new_value = NULL;
        if (found) {
            new_value = PyNumber_Add(values[idx], delta);
            if (!new_value) {
                Py_LeaveRecursiveCall();
                return -1;
            }
            Py_DECREF(values[idx]);
            values[idx] = new_value;
            Py_INCREF(new_value);
            *out_value = new_value;
            *inserted = 0;
            Py_LeaveRecursiveCall();
            return 0;
        }

        new_value = PyNumber_Add(default_value, delta);
        if (!new_value) {
            Py_LeaveRecursiveCall();
            return -1;
        }

        PyObject **keys = btree_keys(node);
        BTreePrimKey *pkeys = btree_prim_keys(node);
        if (node->n > idx) {
            size_t count = (size_t)(node->n - idx);
            memmove(&keys[idx + 1], &keys[idx], count * sizeof(PyObject *));
            memmove(&values[idx + 1], &values[idx], count * sizeof(PyObject *));
            if (prim_kind != BTREE_PRIM_NONE) {
                memmove(&pkeys[idx + 1], &pkeys[idx], count * sizeof(BTreePrimKey));
            }
        }

        Py_INCREF(key);
        Py_INCREF(new_value);
        keys[idx] = key;
        values[idx] = new_value;
        if (prim_kind != BTREE_PRIM_NONE && prim_key) {
            pkeys[idx] = *prim_key;
        }
        node->n += 1;
        node->subtree_size = node->n;
        *inserted = 1;
        *out_value = new_value;
        Py_LeaveRecursiveCall();
        return 0;
    }

    int idx;
    if (prim_kind == BTREE_PRIM_I64 && prim_key) {
        idx = btree_find_child_i64(node, prim_key->i64);
    } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
        idx = btree_find_child_f64(node, prim_key->f64);
    } else {
        idx = btree_find_child_typed(node, key, tp, use_fast);
    }
    if (idx < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }

    BTreeNode **children = btree_children(node);
    if (children[idx]->n == btree_max_keys(children[idx])) {
        if (btree_split_child(node, idx, prim_kind) < 0) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        PyObject **keys = btree_keys(node);
        int cmp;
        if (prim_kind == BTREE_PRIM_I64 && prim_key) {
            cmp = btree_cmp_i64(btree_prim_keys(node)[idx].i64, prim_key->i64);
        } else if (prim_kind == BTREE_PRIM_F64 && prim_key) {
            cmp = btree_cmp_f64(btree_prim_keys(node)[idx].f64, prim_key->f64);
        } else if (use_fast) {
            cmp = btree_key_cmp_fast(keys[idx], key, tp);
            if (cmp == 2) {
                cmp = btree_key_cmp(keys[idx], key);
            }
        } else {
            cmp = btree_key_cmp(keys[idx], key);
        }
        if (cmp == -2) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        if (cmp <= 0) {
            idx++;
        }
    }

    if (btree_increment_nonfull(children[idx], key, delta, default_value, inserted, out_value,
                                tp, use_fast, prim_kind, prim_key) < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }

    if (*inserted) {
        node->subtree_size += 1;
    }

    Py_LeaveRecursiveCall();
    return 0;
}

static PyObject *
btree_increment_item(BTreeObject *self, PyObject *key, PyObject *delta, PyObject *default_value)
{
    if (btree_check_nan_key(key) < 0) {
        return NULL;
    }
    if (btree_guard_enter(self) < 0) {
        return NULL;
    }
    PyObject *result = NULL;
    if (!self->root) {
        self->root = btree_node_new(1);
        if (!self->root) {
            goto out;
        }
    }

    if (self->root->n == btree_max_keys(self->root)) {
        BTreeNode *new_root = btree_node_new(0);
        if (!new_root) {
            goto out;
        }
        btree_children(new_root)[0] = self->root;
        if (btree_split_child(new_root, 0, self->prim_kind) < 0) {
            btree_node_free_raw(new_root);
            goto out;
        }
        btree_recompute_subtree(new_root);
        self->root = new_root;
    }

    PyTypeObject *tp = Py_TYPE(key);
    if (self->size == 0) {
        self->key_type = tp;
    } else if (self->key_type && self->key_type != tp) {
        self->key_type = NULL;
    }
    int use_fast = (self->key_type == tp && tp->tp_richcompare != NULL);

    int prim_kind = self->prim_kind;
    BTreePrimKey prim_key;
    const BTreePrimKey *prim_ptr = NULL;
    if (prim_kind != BTREE_PRIM_NONE) {
        int kind_tmp = BTREE_PRIM_NONE;
        int r = btree_prim_from_key(key, &kind_tmp, &prim_key);
        if (r < 0) {
            goto out;
        }
        if (prim_kind == BTREE_PRIM_UNKNOWN) {
            if (r == 1) {
                prim_kind = kind_tmp;
                self->prim_kind = kind_tmp;
                prim_ptr = &prim_key;
            } else {
                prim_kind = BTREE_PRIM_NONE;
                self->prim_kind = BTREE_PRIM_NONE;
            }
        } else if (r == 1 && kind_tmp == prim_kind) {
            prim_ptr = &prim_key;
        } else {
            prim_kind = BTREE_PRIM_NONE;
            self->prim_kind = BTREE_PRIM_NONE;
        }
    }

    int inserted = 0;
    PyObject *out_value = NULL;
    if (btree_increment_nonfull(self->root, key, delta, default_value, &inserted, &out_value,
                                tp, use_fast, prim_kind, prim_ptr) < 0) {
        goto out;
    }
    if (inserted) {
        self->size += 1;
    }
    btree_cache_clear(self);
    self->mod_count += 1;
    result = out_value;
out:
    btree_guard_exit(self);
    return result;
}

static int
btree_delete_item(BTreeObject *self, PyObject *key)
{
    if (btree_check_nan_key(key) < 0) {
        return -1;
    }
    if (btree_guard_enter(self) < 0) {
        return -1;
    }
    if (!self->root) {
        PyErr_SetObject(PyExc_KeyError, key);
        btree_guard_exit(self);
        return -1;
    }

    int res = btree_remove_cached_path(self, key);
    if (res == 1) {
        PyTypeObject *tp = Py_TYPE(key);
        int use_fast = (self->key_type == tp && tp->tp_richcompare != NULL);
        int prim_kind = self->prim_kind;
        BTreePrimKey prim_key;
        const BTreePrimKey *prim_ptr = NULL;
        if (prim_kind == BTREE_PRIM_I64 || prim_kind == BTREE_PRIM_F64) {
            int kind_tmp = BTREE_PRIM_NONE;
            int r = btree_prim_from_key(key, &kind_tmp, &prim_key);
            if (r < 0) {
                btree_guard_exit(self);
                return -1;
            }
            if (r == 1 && kind_tmp == prim_kind) {
                prim_ptr = &prim_key;
            } else {
                prim_kind = BTREE_PRIM_NONE;
            }
        }

        int min_changed = 0;
        PyObject *new_min = NULL;
        BTreePrimKey new_prim;
        res = btree_remove(self->root, key, &self->size, prim_kind,
                           tp, use_fast, prim_ptr,
                           &min_changed, &new_min, &new_prim);
    }
    if (res < 0) {
        btree_guard_exit(self);
        return -1;
    }

    if (self->root->n == 0) {
        BTreeNode *old_root = self->root;
        if (self->root->leaf) {
            self->root = NULL;
            self->size = 0;
            self->key_type = NULL;
            self->prim_kind = BTREE_PRIM_UNKNOWN;
        } else {
            self->root = btree_children(self->root)[0];
        }
        btree_node_free_raw(old_root);
    }

    btree_cache_clear(self);
    self->mod_count += 1;
    btree_guard_exit(self);
    return 0;
}

static PyObject *
btree_popitem_by_index(BTreeObject *self, Py_ssize_t index)
{
    if (btree_guard_check(self) < 0) {
        return NULL;
    }
    PyObject *key = NULL;
    PyObject *value = NULL;
    if (btree_cache_select_index(self, index, &key, &value) < 0) {
        return NULL;
    }

    if (btree_delete_item(self, key) < 0) {
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
btree_search_item(BTreeObject *self, PyObject *key)
{
    if (btree_check_nan_key(key) < 0) {
        return NULL;
    }
    if (btree_guard_enter(self) < 0) {
        return NULL;
    }
    if (!self->root) {
        btree_cache_clear(self);
        PyErr_SetObject(PyExc_KeyError, key);
        btree_guard_exit(self);
        return NULL;
    }
    PyTypeObject *tp = Py_TYPE(key);
    int use_fast = (self->key_type == tp && tp->tp_richcompare != NULL);

    int prim_kind = self->prim_kind;
    BTreePrimKey prim_key;
    const BTreePrimKey *prim_ptr = NULL;
    if (prim_kind == BTREE_PRIM_I64 || prim_kind == BTREE_PRIM_F64) {
        int kind_tmp = BTREE_PRIM_NONE;
        int r = btree_prim_from_key(key, &kind_tmp, &prim_key);
        if (r < 0) {
            btree_cache_clear(self);
            btree_guard_exit(self);
            return NULL;
        }
        if (r == 1 && kind_tmp == prim_kind) {
            prim_ptr = &prim_key;
        } else {
            prim_kind = BTREE_PRIM_NONE;
        }
    }

    BTreeNode *node = self->root;
    Py_ssize_t depth = 0;
    while (node && !node->leaf) {
        if (btree_cache_ensure(self, depth + 1) < 0) {
            btree_cache_clear(self);
            return NULL;
        }
        self->cache_nodes[depth++] = node;

        int idx;
        if (prim_kind == BTREE_PRIM_I64 && prim_ptr) {
            idx = btree_find_child_i64(node, prim_ptr->i64);
        } else if (prim_kind == BTREE_PRIM_F64 && prim_ptr) {
            idx = btree_find_child_f64(node, prim_ptr->f64);
        } else {
            idx = btree_find_child_typed(node, key, tp, use_fast);
        }
        if (idx < 0) {
            btree_cache_clear(self);
            btree_guard_exit(self);
            return NULL;
        }
        node = btree_children(node)[idx];
    }

    if (!node) {
        btree_cache_clear(self);
        PyErr_SetObject(PyExc_KeyError, key);
        btree_guard_exit(self);
        return NULL;
    }

    if (btree_cache_ensure(self, depth + 1) < 0) {
        btree_cache_clear(self);
        btree_guard_exit(self);
        return NULL;
    }
    self->cache_nodes[depth++] = node;

    int found = 0;
    int idx;
    if (prim_kind == BTREE_PRIM_I64 && prim_ptr) {
        idx = btree_find_index_i64(node, prim_ptr->i64, &found);
    } else if (prim_kind == BTREE_PRIM_F64 && prim_ptr) {
        idx = btree_find_index_f64(node, prim_ptr->f64, &found);
    } else {
        idx = btree_find_index_typed(node, key, &found, tp, use_fast);
    }
    if (idx < 0) {
        btree_cache_clear(self);
        btree_guard_exit(self);
        return NULL;
    }
    if (!found) {
        btree_cache_clear(self);
        PyErr_SetObject(PyExc_KeyError, key);
        btree_guard_exit(self);
        return NULL;
    }

    PyObject **values = btree_values(node);
    PyObject *result = Py_NewRef(values[idx]);

    btree_cache_clear(self);
    self->cache_key = Py_NewRef(key);
    self->cache_depth = depth;
    self->cache_version = self->mod_count;
    btree_guard_exit(self);
    return result;
}

static int
btree_collect_keys(BTreeNode *node, PyObject *list)
{
    if (node->leaf) {
        PyObject **keys = btree_keys(node);
        for (int i = 0; i < node->n; i++) {
            if (PyList_Append(list, keys[i]) < 0) {
                return -1;
            }
        }
        return 0;
    }
    BTreeNode **children = btree_children(node);
    for (int i = 0; i <= node->n; i++) {
        if (btree_collect_keys(children[i], list) < 0) {
            return -1;
        }
    }
    return 0;
}

static int
btree_collect_values(BTreeNode *node, PyObject *list)
{
    if (node->leaf) {
        PyObject **values = btree_values(node);
        for (int i = 0; i < node->n; i++) {
            if (PyList_Append(list, values[i]) < 0) {
                return -1;
            }
        }
        return 0;
    }
    BTreeNode **children = btree_children(node);
    for (int i = 0; i <= node->n; i++) {
        if (btree_collect_values(children[i], list) < 0) {
            return -1;
        }
    }
    return 0;
}

static int
btree_collect_items(BTreeNode *node, PyObject *list)
{
    if (node->leaf) {
        PyObject **keys = btree_keys(node);
        PyObject **values = btree_values(node);
        for (int i = 0; i < node->n; i++) {
            PyObject *pair = PyTuple_Pack(2, keys[i], values[i]);
            if (!pair) {
                return -1;
            }
            int rc = PyList_Append(list, pair);
            Py_DECREF(pair);
            if (rc < 0) {
                return -1;
            }
        }
        return 0;
    }
    BTreeNode **children = btree_children(node);
    for (int i = 0; i <= node->n; i++) {
        if (btree_collect_items(children[i], list) < 0) {
            return -1;
        }
    }
    return 0;
}

static int
btree_count_lt(BTreeNode *node, PyObject *key, Py_ssize_t *count, int inclusive)
{
    if (Py_EnterRecursiveCall(" in btree_count_lt")) {
        return -1;
    }

    PyTypeObject *tp = NULL;
    int use_fast = 0;
    PyObject **keys = btree_keys(node);
    if (node->n > 0 && Py_TYPE(key) == Py_TYPE(keys[0])) {
        tp = Py_TYPE(key);
        use_fast = (tp->tp_richcompare != NULL);
    }

    if (node->leaf) {
        int lo = 0, hi = node->n;
        int mid, cmp;
        while (lo < hi) {
            mid = (lo + hi) / 2;
            if (use_fast) {
                cmp = btree_key_cmp_fast(keys[mid], key, tp);
                if (cmp == 2) {
                    use_fast = 0;
                    cmp = btree_key_cmp(keys[mid], key);
                }
            } else {
                cmp = btree_key_cmp(keys[mid], key);
            }
            if (cmp == -2) {
                Py_LeaveRecursiveCall();
                return -1;
            }
            if (cmp > 0 || (cmp == 0 && !inclusive)) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        *count += lo;
        Py_LeaveRecursiveCall();
        return 0;
    }

    int idx = btree_find_child(node, key);
    if (idx < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }
    BTreeNode **children = btree_children(node);
    for (int i = 0; i < idx; i++) {
        *count += children[i]->subtree_size;
    }
    if (btree_count_lt(children[idx], key, count, inclusive) < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }

    Py_LeaveRecursiveCall();
    return 0;
}

static int
btree_collect_range(BTreeNode *node, PyObject *list, PyObject *min,
                    PyObject *max, int include_min, int include_max)
{
    if (node->leaf) {
        PyObject **keys = btree_keys(node);
        for (int i = 0; i < node->n; i++) {
            int cmp_min = 1;
            int cmp_max = -1;
            if (min != Py_None) {
                cmp_min = btree_key_cmp(keys[i], min);
                if (cmp_min == -2) {
                    return -1;
                }
            }
            if (max != Py_None) {
                cmp_max = btree_key_cmp(keys[i], max);
                if (cmp_max == -2) {
                    return -1;
                }
            }
            int ok_min = (min == Py_None) || (cmp_min > 0) || (cmp_min == 0 && include_min);
            int ok_max = (max == Py_None) || (cmp_max < 0) || (cmp_max == 0 && include_max);
            if (ok_min && ok_max) {
                if (PyList_Append(list, keys[i]) < 0) {
                    return -1;
                }
            }
            /* Early exit if we've passed the max */
            if (max != Py_None) {
                if (cmp_max > 0 || (cmp_max == 0 && !include_max)) {
                    return 0;
                }
            }
        }
        return 0;
    }

    /* Internal node: use subtree pruning */
    PyObject **keys = btree_keys(node);
    BTreeNode **children = btree_children(node);
    
    /* Find start child - skip children that are entirely below min */
    int start_child = 0;
    if (min != Py_None) {
        for (int i = 0; i < node->n; i++) {
            int cmp = btree_key_cmp(keys[i], min);
            if (cmp == -2) {
                return -1;
            }
            /* If key[i] < min, we can skip child[i] entirely (it's all below min) */
            if (cmp < 0 || (cmp == 0 && !include_min)) {
                start_child = i + 1;
            } else {
                break;
            }
        }
    }
    
    /* Find end child - stop at children that are entirely above max */
    int end_child = node->n;
    if (max != Py_None) {
        for (int i = node->n - 1; i >= 0; i--) {
            int cmp = btree_key_cmp(keys[i], max);
            if (cmp == -2) {
                return -1;
            }
            /* If key[i] > max, we can skip child[i+1] and beyond */
            if (cmp > 0 || (cmp == 0 && !include_max)) {
                end_child = i;
            } else {
                break;
            }
        }
    }
    
    /* Now recurse only into children that could have values in range */
    for (int i = start_child; i <= end_child; i++) {
        if (btree_collect_range(children[i], list, min, max, include_min, include_max) < 0) {
            return -1;
        }
    }
    return 0;
}

static PyObject *
BTree_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    BTreeObject *self = (BTreeObject *)type->tp_alloc(type, 0);
    if (!self) {
        return NULL;
    }
    self->root = NULL;
    self->size = 0;
    self->key_type = NULL;
    self->prim_kind = BTREE_PRIM_UNKNOWN;
    self->busy = 0;
    self->weakreflist = NULL;
    self->cache_key = NULL;
    self->cache_nodes = NULL;
    self->cache_depth = 0;
    self->cache_cap = 0;
    self->mod_count = 0;
    self->cache_version = 0;
    return (PyObject *)self;
}

static void
BTree_dealloc(BTreeObject *self)
{
    PyObject_GC_UnTrack(self);
    if (self->weakreflist) {
        PyObject_ClearWeakRefs((PyObject *)self);
    }
    btree_node_free(self->root);
    btree_cache_clear(self);
    PyMem_Free(self->cache_nodes);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static int
BTree_traverse(BTreeObject *self, visitproc visit, void *arg)
{
    if (btree_traverse_node(self->root, visit, arg) < 0) {
        return -1;
    }
    Py_VISIT(self->cache_key);
    return 0;
}

static int
BTree_clear_refs(BTreeObject *self)
{
    btree_node_free(self->root);
    self->root = NULL;
    self->size = 0;
    self->key_type = NULL;
    self->prim_kind = BTREE_PRIM_UNKNOWN;
    self->busy = 0;
    btree_cache_clear(self);
    return 0;
}

static Py_ssize_t
BTree_len(BTreeObject *self)
{
    return self->size;
}

static PyObject *
BTree_insert(BTreeObject *self, PyObject *args)
{
    PyObject *key = NULL;
    PyObject *value = Py_None;

    if (!PyArg_ParseTuple(args, "O|O", &key, &value)) {
        return NULL;
    }

    if (btree_insert_item(self, key, value) < 0) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *
BTree_delete(BTreeObject *self, PyObject *args)
{
    PyObject *key = NULL;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    if (btree_delete_item(self, key) < 0) {
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *
BTree_search(BTreeObject *self, PyObject *args)
{
    PyObject *key = NULL;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    return btree_search_item(self, key);
}

static PyObject *
BTree_clear(BTreeObject *self, PyObject *Py_UNUSED(ignored))
{
    if (btree_guard_enter(self) < 0) {
        return NULL;
    }
    if (BTree_clear_refs(self) < 0) {
        btree_guard_exit(self);
        return NULL;
    }
    self->mod_count += 1;
    btree_guard_exit(self);
    Py_RETURN_NONE;
}

static PyObject *
BTree_keys(BTreeObject *self, PyObject *Py_UNUSED(ignored))
{
    return BTreeIter_new(self, 0);
}

static PyObject *
BTree_values(BTreeObject *self, PyObject *Py_UNUSED(ignored))
{
    return BTreeIter_new(self, 1);
}

static PyObject *
BTree_items(BTreeObject *self, PyObject *Py_UNUSED(ignored))
{
    return BTreeIter_new(self, 2);
}

static PyObject *
BTree_bisect_left(BTreeObject *self, PyObject *args)
{
    PyObject *key = NULL;
    Py_ssize_t count = 0;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    if (btree_check_nan_key(key) < 0) {
        return NULL;
    }
    if (btree_guard_enter(self) < 0) {
        return NULL;
    }

    if (self->root) {
        if (btree_count_lt(self->root, key, &count, 0) < 0) {
            btree_guard_exit(self);
            return NULL;
        }
    }

    PyObject *result = PyLong_FromSsize_t(count);
    btree_guard_exit(self);
    return result;
}

static PyObject *
BTree_bisect_right(BTreeObject *self, PyObject *args)
{
    PyObject *key = NULL;
    Py_ssize_t count = 0;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    if (btree_check_nan_key(key) < 0) {
        return NULL;
    }
    if (btree_guard_enter(self) < 0) {
        return NULL;
    }

    if (self->root) {
        if (btree_count_lt(self->root, key, &count, 1) < 0) {
            btree_guard_exit(self);
            return NULL;
        }
    }

    PyObject *result = PyLong_FromSsize_t(count);
    btree_guard_exit(self);
    return result;
}

static PyObject *
BTree_irange(BTreeObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"min", "max", "inclusive", NULL};
    PyObject *min = Py_None;
    PyObject *max = Py_None;
    PyObject *inclusive = Py_None;
    int include_min = 1;
    int include_max = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOO", kwlist, &min, &max, &inclusive)) {
        return NULL;
    }

    if (min != Py_None) {
        if (btree_check_nan_key(min) < 0) {
            return NULL;
        }
    }
    if (max != Py_None) {
        if (btree_check_nan_key(max) < 0) {
            return NULL;
        }
    }
    if (btree_guard_enter(self) < 0) {
        return NULL;
    }

    if (inclusive != Py_None) {
        PyObject *seq = PySequence_Fast(inclusive, "inclusive must be a 2-item sequence");
        if (!seq) {
            btree_guard_exit(self);
            return NULL;
        }
        if (PySequence_Fast_GET_SIZE(seq) != 2) {
            Py_DECREF(seq);
            PyErr_SetString(PyExc_ValueError, "inclusive must be length 2");
            btree_guard_exit(self);
            return NULL;
        }
        include_min = PyObject_IsTrue(PySequence_Fast_GET_ITEM(seq, 0));
        include_max = PyObject_IsTrue(PySequence_Fast_GET_ITEM(seq, 1));
        Py_DECREF(seq);
        if (include_min < 0 || include_max < 0) {
            btree_guard_exit(self);
            return NULL;
        }
    }

    PyObject *list = PyList_New(0);
    if (!list) {
        btree_guard_exit(self);
        return NULL;
    }
    if (self->root) {
        if (btree_collect_range(self->root, list, min, max, include_min, include_max) < 0) {
            Py_DECREF(list);
            btree_guard_exit(self);
            return NULL;
        }
    }
    btree_guard_exit(self);
    return list;
}

static PyMethodDef BTree_methods[] = {
    {"insert", (PyCFunction)BTree_insert, METH_VARARGS, NULL},
    {"delete", (PyCFunction)BTree_delete, METH_VARARGS, NULL},
    {"search", (PyCFunction)BTree_search, METH_VARARGS, NULL},
    {"clear", (PyCFunction)BTree_clear, METH_NOARGS, NULL},
    {"keys", (PyCFunction)BTree_keys, METH_NOARGS, NULL},
    {"values", (PyCFunction)BTree_values, METH_NOARGS, NULL},
    {"items", (PyCFunction)BTree_items, METH_NOARGS, NULL},
    {"bisect_left", (PyCFunction)BTree_bisect_left, METH_VARARGS, NULL},
    {"bisect_right", (PyCFunction)BTree_bisect_right, METH_VARARGS, NULL},
    {"irange", (PyCFunction)BTree_irange, METH_VARARGS | METH_KEYWORDS, NULL},
    {NULL, NULL, 0, NULL}
};

static PySequenceMethods BTree_as_sequence = {
    .sq_length = (lenfunc)BTree_len,
};

static PyTypeObject BTreeIterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "btree._BTreeIter",
    .tp_basicsize = sizeof(BTreeIterObject),
    .tp_dealloc = (destructor)BTreeIter_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
    .tp_traverse = (traverseproc)BTreeIter_traverse,
    .tp_clear = (inquiry)BTreeIter_clear,
    .tp_iter = PyObject_SelfIter,
    .tp_iternext = (iternextfunc)BTreeIter_iternext,
};

static PyTypeObject BTreeType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "btree.BTree",
    .tp_basicsize = sizeof(BTreeObject),
    .tp_dealloc = (destructor)BTree_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
    .tp_traverse = (traverseproc)BTree_traverse,
    .tp_clear = (inquiry)BTree_clear_refs,
    .tp_weaklistoffset = offsetof(BTreeObject, weakreflist),
    .tp_new = BTree_new,
    .tp_methods = BTree_methods,
    .tp_as_sequence = &BTree_as_sequence,
};

static PyBTree_Insert_RETURN
PyBTree_Insert(PyObject *tree, PyObject *key, PyObject *val)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return -1;
    }

    return btree_insert_item((BTreeObject *)tree, key, val);
}

static PyBTree_Delete_RETURN
PyBTree_Delete(PyObject *tree, PyObject *key)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return -1;
    }

    return btree_delete_item((BTreeObject *)tree, key);
}

static PyBTree_Search_RETURN
PyBTree_Search(PyObject *tree, PyObject *key)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return NULL;
    }

    return btree_search_item((BTreeObject *)tree, key);
}

static PyBTree_Increment_RETURN
PyBTree_Increment(PyObject *tree, PyObject *key, PyObject *delta, PyObject *default_value)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return NULL;
    }
    return btree_increment_item((BTreeObject *)tree, key, delta, default_value);
}

static PyBTree_BisectLeft_RETURN
PyBTree_BisectLeft(PyObject *tree, PyObject *key)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return -1;
    }
    if (btree_check_nan_key(key) < 0) {
        return -1;
    }
    BTreeObject *self = (BTreeObject *)tree;
    if (btree_guard_enter(self) < 0) {
        return -1;
    }
    Py_ssize_t count = 0;
    if (self->root) {
        if (btree_count_lt(self->root, key, &count, 0) < 0) {
            btree_guard_exit(self);
            return -1;
        }
    }
    btree_guard_exit(self);
    return count;
}

static PyBTree_BisectRight_RETURN
PyBTree_BisectRight(PyObject *tree, PyObject *key)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return -1;
    }
    if (btree_check_nan_key(key) < 0) {
        return -1;
    }
    BTreeObject *self = (BTreeObject *)tree;
    if (btree_guard_enter(self) < 0) {
        return -1;
    }
    Py_ssize_t count = 0;
    if (self->root) {
        if (btree_count_lt(self->root, key, &count, 1) < 0) {
            btree_guard_exit(self);
            return -1;
        }
    }
    btree_guard_exit(self);
    return count;
}

static PyBTree_IRange_RETURN
PyBTree_IRange(PyObject *tree, PyObject *min, PyObject *max, PyObject *inclusive)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return NULL;
    }
    if (min && min != Py_None) {
        if (btree_check_nan_key(min) < 0) {
            return NULL;
        }
    }
    if (max && max != Py_None) {
        if (btree_check_nan_key(max) < 0) {
            return NULL;
        }
    }

    int include_min = 1;
    int include_max = 1;
    if (inclusive && inclusive != Py_None) {
        PyObject *seq = PySequence_Fast(inclusive, "inclusive must be a 2-item sequence");
        if (!seq) {
            return NULL;
        }
        if (PySequence_Fast_GET_SIZE(seq) != 2) {
            Py_DECREF(seq);
            PyErr_SetString(PyExc_ValueError, "inclusive must be length 2");
            return NULL;
        }
        include_min = PyObject_IsTrue(PySequence_Fast_GET_ITEM(seq, 0));
        include_max = PyObject_IsTrue(PySequence_Fast_GET_ITEM(seq, 1));
        Py_DECREF(seq);
        if (include_min < 0 || include_max < 0) {
            return NULL;
        }
    }

    PyObject *list = PyList_New(0);
    if (!list) {
        return NULL;
    }
    BTreeObject *self = (BTreeObject *)tree;
    if (btree_guard_enter(self) < 0) {
        Py_DECREF(list);
        return NULL;
    }
    if (self->root) {
        if (btree_collect_range(self->root, list,
                                min ? min : Py_None,
                                max ? max : Py_None,
                                include_min, include_max) < 0) {
            Py_DECREF(list);
            btree_guard_exit(self);
            return NULL;
        }
    }
    btree_guard_exit(self);
    return list;
}

static PyBTree_GetItemByIndex_RETURN
PyBTree_GetItemByIndex(PyObject *tree, Py_ssize_t index, int kind)
{
    BTreeObject *self = (BTreeObject *)tree;
    if (btree_guard_check(self) < 0) {
        return NULL;
    }
    if (!self->root) {
        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }
    if (index < 0) {
        index += self->size;
    }
    if (index < 0 || index >= self->size) {
        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }
    PyObject *key = NULL;
    PyObject *value = NULL;
    if (btree_select_index(self->root, index, &key, &value) < 0) {
        return NULL;
    }
    if (kind == 0) {
        return Py_NewRef(key);
    }
    if (kind == 1) {
        return Py_NewRef(value);
    }
    return PyTuple_Pack(2, key, value);
}

static PyBTree_IterNew_RETURN
PyBTree_IterNew(PyObject *tree, int kind)
{
    return BTreeIter_new((BTreeObject *)tree, kind);
}

static PyBTree_IterNext_RETURN
PyBTree_IterNext(PyObject *iter)
{
    PyObject *item = BTreeIter_iternext((BTreeIterObject *)iter);
    if (!item && PyErr_ExceptionMatches(PyExc_StopIteration)) {
        PyErr_Clear();
    }
    return item;
}

static PyObject *
btree_iter_next_clear(BTreeIterObject *iter)
{
    PyObject *item = BTreeIter_iternext(iter);
    if (!item && PyErr_ExceptionMatches(PyExc_StopIteration)) {
        PyErr_Clear();
    }
    return item;
}

static PyBTree_MergeUnion_RETURN
PyBTree_MergeUnion(PyObject *tree_a, PyObject *tree_b)
{
    if (!PyObject_TypeCheck(tree_a, &BTreeType) || !PyObject_TypeCheck(tree_b, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected BTree objects");
        return NULL;
    }

    PyObject **keys = NULL;
    Py_ssize_t size = 0;
    Py_ssize_t cap = 0;

    BTreeIterObject *iter_a = (BTreeIterObject *)BTreeIter_new((BTreeObject *)tree_a, 0);
    BTreeIterObject *iter_b = (BTreeIterObject *)BTreeIter_new((BTreeObject *)tree_b, 0);
    if (!iter_a || !iter_b) {
        Py_XDECREF(iter_a);
        Py_XDECREF(iter_b);
        return NULL;
    }

    PyObject *a = btree_iter_next_clear(iter_a);
    PyObject *b = btree_iter_next_clear(iter_b);
    while (a || b) {
        if (!b) {
            if (btree_keys_append(&keys, &size, &cap, a) < 0) {
                Py_DECREF(a);
                Py_DECREF(iter_a);
                Py_DECREF(iter_b);
                goto error;
            }
            a = btree_iter_next_clear(iter_a);
            continue;
        }
        if (!a) {
            if (btree_keys_append(&keys, &size, &cap, b) < 0) {
                Py_DECREF(b);
                Py_DECREF(iter_a);
                Py_DECREF(iter_b);
                goto error;
            }
            b = btree_iter_next_clear(iter_b);
            continue;
        }

        int cmp = btree_key_cmp(a, b);
        if (cmp == -2) {
            Py_DECREF(a);
            Py_DECREF(b);
            Py_DECREF(iter_a);
            Py_DECREF(iter_b);
            goto error;
        }
        if (cmp < 0) {
            if (btree_keys_append(&keys, &size, &cap, a) < 0) {
                Py_DECREF(a);
                Py_DECREF(b);
                Py_DECREF(iter_a);
                Py_DECREF(iter_b);
                goto error;
            }
            a = btree_iter_next_clear(iter_a);
        } else if (cmp == 0) {
            if (btree_keys_append(&keys, &size, &cap, a) < 0) {
                Py_DECREF(a);
                Py_DECREF(b);
                Py_DECREF(iter_a);
                Py_DECREF(iter_b);
                goto error;
            }
            Py_DECREF(b);
            a = btree_iter_next_clear(iter_a);
            b = btree_iter_next_clear(iter_b);
        } else {
            if (btree_keys_append(&keys, &size, &cap, b) < 0) {
                Py_DECREF(a);
                Py_DECREF(b);
                Py_DECREF(iter_a);
                Py_DECREF(iter_b);
                goto error;
            }
            b = btree_iter_next_clear(iter_b);
        }
    }

    Py_DECREF(iter_a);
    Py_DECREF(iter_b);
    if (PyErr_Occurred()) {
        goto error;
    }

    BTreeObject *result = btree_build_from_sorted(keys, size);
    for (Py_ssize_t i = 0; i < size; i++) {
        Py_XDECREF(keys[i]);
    }
    PyMem_Free(keys);
    return (PyObject *)result;

error:
    if (keys) {
        for (Py_ssize_t i = 0; i < size; i++) {
            Py_XDECREF(keys[i]);
        }
        PyMem_Free(keys);
    }
    return NULL;
}

static PyBTree_MergeIntersection_RETURN
PyBTree_MergeIntersection(PyObject *tree_a, PyObject *tree_b)
{
    if (!PyObject_TypeCheck(tree_a, &BTreeType) || !PyObject_TypeCheck(tree_b, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected BTree objects");
        return NULL;
    }

    PyObject **keys = NULL;
    Py_ssize_t size = 0;
    Py_ssize_t cap = 0;
    BTreeIterObject *iter_a = (BTreeIterObject *)BTreeIter_new((BTreeObject *)tree_a, 0);
    BTreeIterObject *iter_b = (BTreeIterObject *)BTreeIter_new((BTreeObject *)tree_b, 0);
    if (!iter_a || !iter_b) {
        Py_XDECREF(iter_a);
        Py_XDECREF(iter_b);
        return NULL;
    }

    PyObject *a = btree_iter_next_clear(iter_a);
    PyObject *b = btree_iter_next_clear(iter_b);
    while (a && b) {
        int cmp = btree_key_cmp(a, b);
        if (cmp == -2) {
            Py_DECREF(a);
            Py_DECREF(b);
            Py_DECREF(iter_a);
            Py_DECREF(iter_b);
            goto error_intersection;
        }
        if (cmp < 0) {
            Py_DECREF(a);
            a = btree_iter_next_clear(iter_a);
            continue;
        }
        if (cmp > 0) {
            Py_DECREF(b);
            b = btree_iter_next_clear(iter_b);
            continue;
        }
        if (btree_keys_append(&keys, &size, &cap, a) < 0) {
            Py_DECREF(a);
            Py_DECREF(b);
            Py_DECREF(iter_a);
            Py_DECREF(iter_b);
            goto error_intersection;
        }
        Py_DECREF(a);
        Py_DECREF(b);
        a = btree_iter_next_clear(iter_a);
        b = btree_iter_next_clear(iter_b);
    }

    Py_XDECREF(a);
    Py_XDECREF(b);
    Py_DECREF(iter_a);
    Py_DECREF(iter_b);
    if (PyErr_Occurred()) {
        goto error_intersection;
    }

    BTreeObject *result = btree_build_from_sorted(keys, size);
    for (Py_ssize_t i = 0; i < size; i++) {
        Py_XDECREF(keys[i]);
    }
    PyMem_Free(keys);
    return (PyObject *)result;

error_intersection:
    if (keys) {
        for (Py_ssize_t i = 0; i < size; i++) {
            Py_XDECREF(keys[i]);
        }
        PyMem_Free(keys);
    }
    return NULL;
}

static PyBTree_MergeDifference_RETURN
PyBTree_MergeDifference(PyObject *tree_a, PyObject *tree_b)
{
    if (!PyObject_TypeCheck(tree_a, &BTreeType) || !PyObject_TypeCheck(tree_b, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected BTree objects");
        return NULL;
    }

    PyObject **keys = NULL;
    Py_ssize_t size = 0;
    Py_ssize_t cap = 0;
    BTreeIterObject *iter_a = (BTreeIterObject *)BTreeIter_new((BTreeObject *)tree_a, 0);
    BTreeIterObject *iter_b = (BTreeIterObject *)BTreeIter_new((BTreeObject *)tree_b, 0);
    if (!iter_a || !iter_b) {
        Py_XDECREF(iter_a);
        Py_XDECREF(iter_b);
        return NULL;
    }

    PyObject *a = btree_iter_next_clear(iter_a);
    PyObject *b = btree_iter_next_clear(iter_b);
    while (a) {
        if (!b) {
            if (btree_keys_append(&keys, &size, &cap, a) < 0) {
                Py_DECREF(a);
                Py_DECREF(iter_a);
                Py_DECREF(iter_b);
                goto error_difference;
            }
            a = btree_iter_next_clear(iter_a);
            continue;
        }
        int cmp = btree_key_cmp(a, b);
        if (cmp == -2) {
            Py_DECREF(a);
            Py_DECREF(b);
            Py_DECREF(iter_a);
            Py_DECREF(iter_b);
            goto error_difference;
        }
        if (cmp < 0) {
            if (btree_keys_append(&keys, &size, &cap, a) < 0) {
                Py_DECREF(a);
                Py_DECREF(b);
                Py_DECREF(iter_a);
                Py_DECREF(iter_b);
                goto error_difference;
            }
            a = btree_iter_next_clear(iter_a);
        } else if (cmp == 0) {
            Py_DECREF(a);
            Py_DECREF(b);
            a = btree_iter_next_clear(iter_a);
            b = btree_iter_next_clear(iter_b);
        } else {
            Py_DECREF(b);
            b = btree_iter_next_clear(iter_b);
        }
    }

    Py_XDECREF(b);
    Py_DECREF(iter_a);
    Py_DECREF(iter_b);
    if (PyErr_Occurred()) {
        goto error_difference;
    }

    BTreeObject *result = btree_build_from_sorted(keys, size);
    for (Py_ssize_t i = 0; i < size; i++) {
        Py_XDECREF(keys[i]);
    }
    PyMem_Free(keys);
    return (PyObject *)result;

error_difference:
    if (keys) {
        for (Py_ssize_t i = 0; i < size; i++) {
            Py_XDECREF(keys[i]);
        }
        PyMem_Free(keys);
    }
    return NULL;
}

/*
 * PyBTree_Copy: Create a deep copy of a BTree in O(n) time.
 * This uses btree_build_from_sorted internally since the source is already sorted.
 */
static BTreeNode *
btree_copy_node(BTreeNode *node, int prim_kind)
{
    if (!node) {
        return NULL;
    }

    if (node->leaf) {
        BTreeLeaf *src = btree_leaf(node);
        BTreeLeaf *dst = btree_leaf(btree_node_new(1));
        if (!dst) {
            return NULL;
        }
        dst->base.n = node->n;
        dst->base.subtree_size = node->subtree_size;
        for (int i = 0; i < node->n; i++) {
            dst->keys[i] = Py_NewRef(src->keys[i]);
            dst->values[i] = Py_NewRef(src->values[i]);
            if (prim_kind != BTREE_PRIM_NONE) {
                dst->prim_keys[i] = src->prim_keys[i];
            }
        }
        dst->next_leaf = NULL;  /* Will be fixed up after full copy */
        return (BTreeNode *)dst;
    }

    BTreeInternal *src = btree_internal(node);
    BTreeInternal *dst = btree_internal(btree_node_new(0));
    if (!dst) {
        return NULL;
    }
    dst->base.n = node->n;
    dst->base.subtree_size = node->subtree_size;
    for (int i = 0; i < node->n; i++) {
        dst->keys[i] = Py_NewRef(src->keys[i]);
        if (prim_kind != BTREE_PRIM_NONE) {
            dst->prim_keys[i] = src->prim_keys[i];
        }
    }
    for (int i = 0; i <= node->n; i++) {
        dst->children[i] = btree_copy_node(src->children[i], prim_kind);
        if (!dst->children[i]) {
            /* Cleanup on failure */
            for (int j = 0; j < i; j++) {
                btree_node_free(dst->children[j]);
            }
            for (int j = 0; j < node->n; j++) {
                Py_DECREF(dst->keys[j]);
            }
            btree_node_free_raw((BTreeNode *)dst);
            return NULL;
        }
    }
    return (BTreeNode *)dst;
}

/* Fix leaf linked list after copying */
static void
btree_fixup_leaf_links(BTreeNode *node, BTreeLeaf **prev_leaf)
{
    if (!node) {
        return;
    }
    if (node->leaf) {
        BTreeLeaf *leaf = btree_leaf(node);
        if (*prev_leaf) {
            (*prev_leaf)->next_leaf = leaf;
        }
        *prev_leaf = leaf;
        return;
    }
    BTreeInternal *internal = btree_internal(node);
    for (int i = 0; i <= node->n; i++) {
        btree_fixup_leaf_links(internal->children[i], prev_leaf);
    }
}

static PyBTree_Copy_RETURN
PyBTree_Copy(PyObject *tree)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return NULL;
    }

    BTreeObject *src = (BTreeObject *)tree;
    BTreeObject *dst = (BTreeObject *)BTree_new(&BTreeType, NULL, NULL);
    if (!dst) {
        return NULL;
    }
    dst->key_type = src->key_type;
    dst->prim_kind = src->prim_kind;

    if (src->root) {
        dst->root = btree_copy_node(src->root, src->prim_kind);
        if (!dst->root) {
            Py_DECREF(dst);
            return NULL;
        }
        /* Fix up leaf linked list */
        BTreeLeaf *prev_leaf = NULL;
        btree_fixup_leaf_links(dst->root, &prev_leaf);
    }
    dst->size = src->size;

    return (PyObject *)dst;
}

static PyBTree_BuildFromSortedPairs_RETURN
PyBTree_BuildFromSortedPairs(PyObject **keys, PyObject **values, Py_ssize_t n)
{
    if (n < 0) {
        PyErr_SetString(PyExc_ValueError, "n must be >= 0");
        return NULL;
    }
    return (PyObject *)btree_build_from_sorted_pairs(keys, values, n);
}

static PyBTree_PopItemByIndex_RETURN
PyBTree_PopItemByIndex(PyObject *tree, Py_ssize_t index)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return NULL;
    }
    return btree_popitem_by_index((BTreeObject *)tree, index);
}

static PyMethodDef btree_module_methods[] = {
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef btree_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "btree",
    .m_doc = "B-tree data structure for sorted collections.",
    .m_size = -1,
    .m_methods = btree_module_methods,
};

PyMODINIT_FUNC
PyInit_btree(void)
{
    PyObject *m = NULL;
    PyObject *api_capsule = NULL;
    static void *api[PyBTree_API_pointers];

    if (PyType_Ready(&BTreeIterType) < 0) {
        return NULL;
    }

    if (PyType_Ready(&BTreeType) < 0) {
        return NULL;
    }

    m = PyModule_Create(&btree_module);
    if (!m) {
        return NULL;
    }

    if (PyModule_AddObjectRef(m, "BTree", (PyObject *)&BTreeType) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    api[PyBTree_Insert_NUM] = PyBTree_Insert;
    api[PyBTree_Delete_NUM] = PyBTree_Delete;
    api[PyBTree_Search_NUM] = PyBTree_Search;
    api[PyBTree_BisectLeft_NUM] = PyBTree_BisectLeft;
    api[PyBTree_BisectRight_NUM] = PyBTree_BisectRight;
    api[PyBTree_IRange_NUM] = PyBTree_IRange;
    api[PyBTree_GetItemByIndex_NUM] = PyBTree_GetItemByIndex;
    api[PyBTree_IterNew_NUM] = PyBTree_IterNew;
    api[PyBTree_IterNext_NUM] = PyBTree_IterNext;
    api[PyBTree_MergeUnion_NUM] = PyBTree_MergeUnion;
    api[PyBTree_MergeIntersection_NUM] = PyBTree_MergeIntersection;
    api[PyBTree_MergeDifference_NUM] = PyBTree_MergeDifference;
    api[PyBTree_Copy_NUM] = PyBTree_Copy;
    api[PyBTree_Increment_NUM] = PyBTree_Increment;
    api[PyBTree_BuildFromSortedPairs_NUM] = PyBTree_BuildFromSortedPairs;
    api[PyBTree_PopItemByIndex_NUM] = PyBTree_PopItemByIndex;

    api_capsule = PyCapsule_New((void *)api, "btree._C_API", NULL);
    if (!api_capsule) {
        Py_DECREF(m);
        return NULL;
    }
    if (PyModule_AddObject(m, "_C_API", api_capsule) < 0) {
        Py_DECREF(api_capsule);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
