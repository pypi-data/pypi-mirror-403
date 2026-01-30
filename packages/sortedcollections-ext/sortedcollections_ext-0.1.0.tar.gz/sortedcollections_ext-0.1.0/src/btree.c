#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>
#include <stdint.h>

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

#define BTREE_LEAF_MIN_DEGREE 64
#define BTREE_LEAF_MAX_KEYS (2 * BTREE_LEAF_MIN_DEGREE - 1)

#define BTREE_INTERNAL_MIN_DEGREE 64
#define BTREE_INTERNAL_MAX_KEYS (2 * BTREE_INTERNAL_MIN_DEGREE - 1)
#define BTREE_INTERNAL_MAX_CHILDREN (2 * BTREE_INTERNAL_MIN_DEGREE)

typedef struct BTreeNodeBase {
    int n;
    int leaf;
    Py_ssize_t subtree_size;  /* Total keys in this node + all children */
    struct BTreeNodeBase *next_free;
} BTreeNode;

typedef struct BTreeLeaf {
    BTreeNode base;
    PyObject *keys[BTREE_LEAF_MAX_KEYS];
    PyObject *values[BTREE_LEAF_MAX_KEYS];
    struct BTreeLeaf *next_leaf;
} BTreeLeaf;

typedef struct BTreeInternal {
    BTreeNode base;
    PyObject *keys[BTREE_INTERNAL_MAX_KEYS];
    struct BTreeNodeBase *children[BTREE_INTERNAL_MAX_CHILDREN];
} BTreeInternal;

typedef struct {
    PyObject_HEAD
    BTreeNode *root;
    Py_ssize_t size;
} BTreeObject;

typedef struct {
    PyObject_HEAD
    BTreeObject *tree;
    int kind; /* 0=keys, 1=values, 2=items */
    BTreeNode *leaf;
    Py_ssize_t leaf_index;
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

/* Fixed-size freelists for BTreeNode allocations */
#define BTREE_NODE_FREELIST_MAX 128
static BTreeNode *btree_leaf_freelist = NULL;
static Py_ssize_t btree_leaf_freelist_size = 0;
static BTreeNode *btree_internal_freelist = NULL;
static Py_ssize_t btree_internal_freelist_size = 0;

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
        for (Py_ssize_t j = 0; j < count; j++) {
            leaf->keys[j] = keys[idx];
            keys[idx] = NULL;
            Py_INCREF(Py_None);
            leaf->values[j] = Py_None;
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

static PyObject *
BTreeIter_new(BTreeObject *tree, int kind)
{
    BTreeIterObject *it = PyObject_New(BTreeIterObject, &BTreeIterType);
    if (!it) {
        return NULL;
    }
    it->tree = (BTreeObject *)Py_NewRef((PyObject *)tree);
    it->kind = kind;
    it->leaf = NULL;
    it->leaf_index = 0;
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
    Py_XDECREF(it->tree);
    PyMem_Free(it->nodes);
    PyMem_Free(it->index);
    PyObject_Free(it);
}

static PyObject *
BTreeIter_iternext(BTreeIterObject *it)
{
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
    /* 1. Identity Check: Fastest path for identical objects or singletons */
    if (a == b) {
        return 0;
    }

    /* 2. Fast Path: Use direct type comparison if types match.
       This bypasses the overhead of generic rich comparison dispatching. */
    PyTypeObject *tp = Py_TYPE(a);
    if (Py_IS_TYPE(b, tp) && tp->tp_richcompare != NULL) {
        PyObject *res_obj = tp->tp_richcompare(a, b, Py_LT);
        
        if (res_obj == Py_True) {
            Py_DECREF(res_obj);
            return -1;
        }
        if (res_obj == Py_False) {
            Py_DECREF(res_obj);
            // Now check for equality to distinguish between GT and EQ
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
        
        /* Fallback if the direct call returns NULL (error) or NotImplemented */
        if (res_obj == NULL) {
            return -2;
        }
        Py_DECREF(res_obj); 
    }

    /* 3. General Path: Fallback for different types or complex objects */
    int lt = PyObject_RichCompareBool(a, b, Py_LT);
    if (lt < 0) {
        return -2; // Error sentinel
    }
    if (lt) {
        return -1;
    }

    int eq = PyObject_RichCompareBool(a, b, Py_EQ);
    if (eq < 0) {
        return -2;
    }
    if (eq) {
        return 0;
    }

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
btree_key_cmp_fast(PyObject *a, PyObject *b, PyTypeObject *tp)
{
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
btree_split_child(BTreeNode *parent, int idx)
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
        for (int j = parent->n - 1; j >= idx; j--) {
            pkeys[j + 1] = pkeys[j];
        }
        Py_INCREF(right_leaf->keys[0]);
        pkeys[idx] = right_leaf->keys[0];

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
    for (int j = parent->n - 1; j >= idx; j--) {
        pkeys[j + 1] = pkeys[j];
    }
    pkeys[idx] = full_in->keys[BTREE_INTERNAL_MIN_DEGREE - 1];
    full_in->keys[BTREE_INTERNAL_MIN_DEGREE - 1] = NULL;

    parent->n += 1;
    btree_recompute_subtree(full);
    btree_recompute_subtree(right);
    btree_recompute_subtree(parent);

    return 0;
}

static int
btree_insert_nonfull(BTreeNode *node, PyObject *key, PyObject *value, int *inserted)
{
    /* Security Procedure: Protect the C stack from deep recursion */
    if (Py_EnterRecursiveCall(" in btree_insert_nonfull")) {
        return -1;
    }

    int i = node->n - 1;

    if (node->leaf) {
        int found = 0;
        int idx = btree_find_index(node, key, &found);
        if (idx < 0) {
            Py_LeaveRecursiveCall();
            return -1;
        }

        if (found) {
            /* Key exists: update value only. subtree_size remains the same. */
            Py_INCREF(value);
            PyObject **values = btree_values(node);
            Py_DECREF(values[idx]);
            values[idx] = value;
            *inserted = 0;
            Py_LeaveRecursiveCall();
            return 0;
        }

        /* Shift and insert new key/value */
        PyObject **keys = btree_keys(node);
        PyObject **values = btree_values(node);
        for (i = node->n - 1; i >= idx; i--) {
            keys[i + 1] = keys[i];
            values[i + 1] = values[i];
        }

        Py_INCREF(key);
        Py_INCREF(value);
        keys[idx] = key;
        values[idx] = value;
        
        /* RANKED UPDATE: Increment local and subtree counts */
        node->n += 1;
        node->subtree_size = node->n;
        *inserted = 1;
        
        Py_LeaveRecursiveCall();
        return 0;
    }

    /* Internal node: find the child to descend into */
    int idx = btree_find_child(node, key);
    if (idx < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }

    /* If child is full, split it */
    BTreeNode **children = btree_children(node);
    if (children[idx]->n == btree_max_keys(children[idx])) {
        if (btree_split_child(node, idx) < 0) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        /* After split, determine which of the two new children to descend into */
        PyObject **keys = btree_keys(node);
        int cmp = btree_key_cmp(keys[idx], key);
        if (cmp == -2) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        if (cmp <= 0) {
            idx++;
        }
    }

    /* Recurse into the non-full child */
    if (btree_insert_nonfull(children[idx], key, value, inserted) < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }

    /* RANKED UPDATE: If a new item was actually inserted, update current subtree_size */
    if (*inserted) {
        btree_recompute_subtree(node);
    }

    Py_LeaveRecursiveCall();
    return 0;
}

static PyObject *
btree_search(BTreeNode *node, PyObject *key)
{
    /* Security Procedure: Protect the C stack from deep recursion */
    if (Py_EnterRecursiveCall(" in btree_search")) {
        return NULL;
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
            return NULL;
        }
        if (cmp > 0) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }

    BTreeNode **children = btree_children(node);
    PyObject *result = btree_search(children[lo], key);
    Py_LeaveRecursiveCall();
    return result;
}

static void
btree_merge(BTreeNode *node, int idx);

static int
btree_remove(BTreeNode *node, PyObject *key, Py_ssize_t *size);

static void
btree_remove_from_leaf(BTreeNode *node, int idx)
{
    PyObject **keys = btree_keys(node);
    PyObject **values = btree_values(node);
    Py_DECREF(keys[idx]);
    Py_DECREF(values[idx]);
    for (int i = idx + 1; i < node->n; i++) {
        keys[i - 1] = keys[i];
        values[i - 1] = values[i];
    }
    node->n -= 1;
}

static void
btree_borrow_from_prev(BTreeNode *node, int idx)
{
    BTreeNode **children = btree_children(node);
    BTreeNode *child = children[idx];
    BTreeNode *sibling = children[idx - 1];

    if (child->leaf) {
        PyObject **ckeys = btree_keys(child);
        PyObject **cvalues = btree_values(child);
        PyObject **skeys = btree_keys(sibling);
        PyObject **svalues = btree_values(sibling);
        for (int i = child->n - 1; i >= 0; i--) {
            ckeys[i + 1] = ckeys[i];
            cvalues[i + 1] = cvalues[i];
        }
        ckeys[0] = skeys[sibling->n - 1];
        cvalues[0] = svalues[sibling->n - 1];
        skeys[sibling->n - 1] = NULL;
        svalues[sibling->n - 1] = NULL;
        sibling->n -= 1;
        child->n += 1;

        PyObject **pkeys = btree_keys(node);
        Py_DECREF(pkeys[idx - 1]);
        Py_INCREF(ckeys[0]);
        pkeys[idx - 1] = ckeys[0];
        btree_recompute_subtree(sibling);
        btree_recompute_subtree(child);
        btree_recompute_subtree(node);
        return;
    }

    PyObject **ckeys = btree_keys(child);
    PyObject **skeys = btree_keys(sibling);
    for (int i = child->n - 1; i >= 0; i--) {
        ckeys[i + 1] = ckeys[i];
    }
    BTreeNode **cchildren = btree_children(child);
    BTreeNode **schildren = btree_children(sibling);
    for (int i = child->n; i >= 0; i--) {
        cchildren[i + 1] = cchildren[i];
    }

    PyObject **pkeys = btree_keys(node);
    ckeys[0] = pkeys[idx - 1];
    cchildren[0] = schildren[sibling->n];

    pkeys[idx - 1] = skeys[sibling->n - 1];
    skeys[sibling->n - 1] = NULL;

    sibling->n -= 1;
    child->n += 1;
    btree_recompute_subtree(sibling);
    btree_recompute_subtree(child);
    btree_recompute_subtree(node);
}

static void
btree_borrow_from_next(BTreeNode *node, int idx)
{
    BTreeNode **children = btree_children(node);
    BTreeNode *child = children[idx];
    BTreeNode *sibling = children[idx + 1];

    if (child->leaf) {
        PyObject **ckeys = btree_keys(child);
        PyObject **cvalues = btree_values(child);
        PyObject **skeys = btree_keys(sibling);
        PyObject **svalues = btree_values(sibling);
        ckeys[child->n] = skeys[0];
        cvalues[child->n] = svalues[0];
        for (int i = 1; i < sibling->n; i++) {
            skeys[i - 1] = skeys[i];
            svalues[i - 1] = svalues[i];
        }
        skeys[sibling->n - 1] = NULL;
        svalues[sibling->n - 1] = NULL;
        sibling->n -= 1;
        child->n += 1;

        PyObject **pkeys = btree_keys(node);
        Py_DECREF(pkeys[idx]);
        Py_INCREF(skeys[0]);
        pkeys[idx] = skeys[0];
        btree_recompute_subtree(sibling);
        btree_recompute_subtree(child);
        btree_recompute_subtree(node);
        return;
    }

    PyObject **ckeys = btree_keys(child);
    PyObject **skeys = btree_keys(sibling);
    BTreeNode **cchildren = btree_children(child);
    BTreeNode **schildren = btree_children(sibling);
    PyObject **pkeys = btree_keys(node);
    ckeys[child->n] = pkeys[idx];
    cchildren[child->n + 1] = schildren[0];

    pkeys[idx] = skeys[0];

    for (int i = 1; i < sibling->n; i++) {
        skeys[i - 1] = skeys[i];
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
btree_merge(BTreeNode *node, int idx)
{
    BTreeNode **children = btree_children(node);
    BTreeNode *child = children[idx];
    BTreeNode *sibling = children[idx + 1];

    if (child->leaf) {
        PyObject **ckeys = btree_keys(child);
        PyObject **cvalues = btree_values(child);
        PyObject **skeys = btree_keys(sibling);
        PyObject **svalues = btree_values(sibling);
        /* Move keys/values from sibling to child - no refcount change needed
         * since we're transferring ownership, not copying */
        for (int i = 0; i < sibling->n; i++) {
            ckeys[child->n + i] = skeys[i];
            cvalues[child->n + i] = svalues[i];
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
        BTreeNode **cchildren = btree_children(child);
        BTreeNode **schildren = btree_children(sibling);
        PyObject **pkeys = btree_keys(node);
        ckeys[BTREE_INTERNAL_MIN_DEGREE - 1] = pkeys[idx];

        for (int i = 0; i < sibling->n; i++) {
            ckeys[i + BTREE_INTERNAL_MIN_DEGREE] = skeys[i];
        }
        for (int i = 0; i <= sibling->n; i++) {
            cchildren[i + BTREE_INTERNAL_MIN_DEGREE] = schildren[i];
        }
        child->n += sibling->n + 1;

        pkeys[idx] = NULL;
    }

    for (int i = idx + 1; i < node->n; i++) {
        btree_keys(node)[i - 1] = btree_keys(node)[i];
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
btree_fill(BTreeNode *node, int idx)
{
    BTreeNode **children = btree_children(node);
    int min_degree = btree_min_degree(children[idx]);
    if (idx != 0 && children[idx - 1]->n >= min_degree) {
        btree_borrow_from_prev(node, idx);
        return 0;
    }

    if (idx != node->n && children[idx + 1]->n >= min_degree) {
        btree_borrow_from_next(node, idx);
        return 0;
    }

    if (idx != node->n) {
        btree_merge(node, idx);
    } else {
        btree_merge(node, idx - 1);
    }

    return 0;
}

static int
btree_remove(BTreeNode *node, PyObject *key, Py_ssize_t *size)
{
    /* Security Procedure: Protect the C stack */
    if (Py_EnterRecursiveCall(" in btree_remove")) {
        return -1;
    }

    if (node->leaf) {
        int found = 0;
        int idx = btree_find_index(node, key, &found);
        if (idx < 0) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        if (!found) {
            PyErr_SetObject(PyExc_KeyError, key);
            Py_LeaveRecursiveCall();
            return -1;
        }
        btree_remove_from_leaf(node, idx);
        node->subtree_size -= 1;
        *size -= 1;
        Py_LeaveRecursiveCall();
        return 0;
    }

    int idx = btree_find_child(node, key);
    if (idx < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }

    BTreeNode **children = btree_children(node);
    if (children[idx]->n < btree_min_degree(children[idx])) {
        if (btree_fill(node, idx) < 0) {
            Py_LeaveRecursiveCall();
            return -1;
        }
        if (idx > node->n) {
            idx--;
        }
    }

    Py_ssize_t old_size = *size;
    if (btree_remove(children[idx], key, size) < 0) {
        Py_LeaveRecursiveCall();
        return -1;
    }
    if (*size < old_size) {
        node->subtree_size -= 1;
    }

    Py_LeaveRecursiveCall();
    return 0;
}

static int
btree_insert_item(BTreeObject *self, PyObject *key, PyObject *value)
{
    int root_split = 0;
    if (!self->root) {
        self->root = btree_node_new(1);
        if (!self->root) {
            return -1;
        }
    }

    if (self->root->n == btree_max_keys(self->root)) {
        BTreeNode *new_root = btree_node_new(0);
        if (!new_root) {
            return -1;
        }
        btree_children(new_root)[0] = self->root;
        if (btree_split_child(new_root, 0) < 0) {
            btree_node_free_raw(new_root);
            return -1;
        }
        btree_recompute_subtree(new_root);
        self->root = new_root;
        root_split = 1;
    }

    int inserted = 0;
    if (btree_insert_nonfull(self->root, key, value, &inserted) < 0) {
        return -1;
    }
    if (inserted) {
        self->size += 1;
    }
    if (root_split) {
        btree_recompute_subtree_full(self->root);
    }
    return 0;
}

static int
btree_delete_item(BTreeObject *self, PyObject *key)
{
    if (!self->root) {
        PyErr_SetObject(PyExc_KeyError, key);
        return -1;
    }

    if (btree_remove(self->root, key, &self->size) < 0) {
        return -1;
    }

    if (self->root->n == 0) {
        BTreeNode *old_root = self->root;
        if (self->root->leaf) {
            self->root = NULL;
            self->size = 0;
        } else {
            self->root = btree_children(self->root)[0];
        }
        btree_node_free_raw(old_root);
    }

    return 0;
}

static PyObject *
btree_search_item(BTreeObject *self, PyObject *key)
{
    if (!self->root) {
        PyErr_SetObject(PyExc_KeyError, key);
        return NULL;
    }
    return btree_search(self->root, key);
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
    return (PyObject *)self;
}

static void
BTree_dealloc(BTreeObject *self)
{
    btree_node_free(self->root);
    Py_TYPE(self)->tp_free((PyObject *)self);
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
    btree_node_free(self->root);
    self->root = NULL;
    self->size = 0;
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

    if (self->root) {
        if (btree_count_lt(self->root, key, &count, 0) < 0) {
            return NULL;
        }
    }

    return PyLong_FromSsize_t(count);
}

static PyObject *
BTree_bisect_right(BTreeObject *self, PyObject *args)
{
    PyObject *key = NULL;
    Py_ssize_t count = 0;

    if (!PyArg_ParseTuple(args, "O", &key)) {
        return NULL;
    }

    if (self->root) {
        if (btree_count_lt(self->root, key, &count, 1) < 0) {
            return NULL;
        }
    }

    return PyLong_FromSsize_t(count);
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

    if (inclusive != Py_None) {
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
    if (self->root) {
        if (btree_collect_range(self->root, list, min, max, include_min, include_max) < 0) {
            Py_DECREF(list);
            return NULL;
        }
    }
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
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_iter = PyObject_SelfIter,
    .tp_iternext = (iternextfunc)BTreeIter_iternext,
};

static PyTypeObject BTreeType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "btree.BTree",
    .tp_basicsize = sizeof(BTreeObject),
    .tp_dealloc = (destructor)BTree_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
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

static PyBTree_BisectLeft_RETURN
PyBTree_BisectLeft(PyObject *tree, PyObject *key)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return -1;
    }
    Py_ssize_t count = 0;
    if (((BTreeObject *)tree)->root) {
        if (btree_count_lt(((BTreeObject *)tree)->root, key, &count, 0) < 0) {
            return -1;
        }
    }
    return count;
}

static PyBTree_BisectRight_RETURN
PyBTree_BisectRight(PyObject *tree, PyObject *key)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return -1;
    }
    Py_ssize_t count = 0;
    if (((BTreeObject *)tree)->root) {
        if (btree_count_lt(((BTreeObject *)tree)->root, key, &count, 1) < 0) {
            return -1;
        }
    }
    return count;
}

static PyBTree_IRange_RETURN
PyBTree_IRange(PyObject *tree, PyObject *min, PyObject *max, PyObject *inclusive)
{
    if (!PyObject_TypeCheck(tree, &BTreeType)) {
        PyErr_SetString(PyExc_TypeError, "expected btree.BTree");
        return NULL;
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
    if (self->root) {
        if (btree_collect_range(self->root, list,
                                min ? min : Py_None,
                                max ? max : Py_None,
                                include_min, include_max) < 0) {
            Py_DECREF(list);
            return NULL;
        }
    }
    return list;
}

static PyBTree_GetItemByIndex_RETURN
PyBTree_GetItemByIndex(PyObject *tree, Py_ssize_t index, int kind)
{
    BTreeObject *self = (BTreeObject *)tree;
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
btree_copy_node(BTreeNode *node)
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
    }
    for (int i = 0; i <= node->n; i++) {
        dst->children[i] = btree_copy_node(src->children[i]);
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

    if (src->root) {
        dst->root = btree_copy_node(src->root);
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

// == SortedDict size=1000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// insert              0.17 us/op           0.54 us/op      3.15x
// get                 0.30 us/op           0.56 us/op      1.90x
// contains            0.20 us/op           0.37 us/op      1.85x
// delete              0.23 us/op           0.68 us/op      3.00x
// bisect              0.20 us/op           0.35 us/op      1.72x
// irange            125.54 us/op         358.97 us/op      2.86x

// == SortedSet size=1000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// add                 0.12 us/op           0.28 us/op      2.22x
// contains            0.21 us/op           0.30 us/op      1.42x
// remove              0.25 us/op           0.52 us/op      2.11x
// union             408.46 us/op         296.68 us/op      0.73x

// == SortedDict mixed size=1000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// mixed               0.28 us/op           0.34 us/op      1.23x

// == SortedSet mixed size=1000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// mixed               0.27 us/op           0.28 us/op      1.05x

// == SortedDict size=10000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// insert              0.17 us/op           0.46 us/op      2.68x
// get                 1.84 us/op           4.59 us/op      2.49x
// contains            1.87 us/op           4.65 us/op      2.48x
// delete              1.93 us/op           5.04 us/op      2.61x
// bisect              1.05 us/op           2.62 us/op      2.49x
// irange           1784.34 us/op        4493.50 us/op      2.52x

// == SortedSet size=10000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// add                 0.18 us/op           0.36 us/op      2.05x
// contains            1.84 us/op           3.77 us/op      2.04x
// remove              1.95 us/op           3.95 us/op      2.03x
// union            4369.97 us/op        3903.59 us/op      0.89x

// == SortedDict mixed size=10000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// mixed               0.41 us/op           0.51 us/op      1.24x

// == SortedSet mixed size=10000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// mixed               0.39 us/op           0.39 us/op      1.00x

// == SortedDict size=100000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// insert              0.25 us/op           0.57 us/op      2.25x
// get                27.06 us/op          57.82 us/op      2.14x
// contains           26.52 us/op          57.59 us/op      2.17x
// delete             27.19 us/op          56.62 us/op      2.08x
// bisect             12.62 us/op          27.89 us/op      2.21x
// irange          25769.89 us/op       53884.78 us/op      2.09x

// == SortedSet size=100000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// add                 0.27 us/op           0.54 us/op      1.99x
// contains           27.47 us/op          49.01 us/op      1.78x
// remove             27.42 us/op          48.14 us/op      1.76x
// union           65039.75 us/op       53807.73 us/op      0.83x

// == SortedDict mixed size=100000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// mixed               0.93 us/op           1.38 us/op      1.48x

// == SortedSet mixed size=100000 ==
// operation      sortedcollections   sortedcontainers     ratio
// ------------   -------------------   ---------------   --------
// mixed               0.92 us/op           1.09 us/op      1.19x
