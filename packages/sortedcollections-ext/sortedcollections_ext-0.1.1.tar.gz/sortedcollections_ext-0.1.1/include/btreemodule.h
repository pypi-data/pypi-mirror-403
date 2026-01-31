#ifndef Py_BTREEMODULE_H
#define Py_BTREEMODULE_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 1. Define function indices in the API pointer array [2] */
#define PyBTree_Insert_NUM 0
#define PyBTree_Delete_NUM 1
#define PyBTree_Search_NUM 2
#define PyBTree_BisectLeft_NUM 3
#define PyBTree_BisectRight_NUM 4
#define PyBTree_IRange_NUM 5
#define PyBTree_GetItemByIndex_NUM 6
#define PyBTree_IterNew_NUM 7
#define PyBTree_IterNext_NUM 8
#define PyBTree_MergeUnion_NUM 9
#define PyBTree_MergeIntersection_NUM 10
#define PyBTree_MergeDifference_NUM 11
#define PyBTree_Copy_NUM 12
#define PyBTree_Increment_NUM 13
#define PyBTree_BuildFromSortedPairs_NUM 14
#define PyBTree_PopItemByIndex_NUM 15
#define PyBTree_API_pointers 16

/* 2. Define return types and signatures for the B-tree C logic [2] */
#define PyBTree_Insert_RETURN int
#define PyBTree_Insert_PROTO (PyObject *tree, PyObject *key, PyObject *val)

#define PyBTree_Delete_RETURN int
#define PyBTree_Delete_PROTO (PyObject *tree, PyObject *key)

#define PyBTree_Search_RETURN PyObject*
#define PyBTree_Search_PROTO (PyObject *tree, PyObject *key)

#define PyBTree_BisectLeft_RETURN Py_ssize_t
#define PyBTree_BisectLeft_PROTO (PyObject *tree, PyObject *key)

#define PyBTree_BisectRight_RETURN Py_ssize_t
#define PyBTree_BisectRight_PROTO (PyObject *tree, PyObject *key)

#define PyBTree_IRange_RETURN PyObject*
#define PyBTree_IRange_PROTO (PyObject *tree, PyObject *min, PyObject *max, PyObject *inclusive)

#define PyBTree_GetItemByIndex_RETURN PyObject*
#define PyBTree_GetItemByIndex_PROTO (PyObject *tree, Py_ssize_t index, int kind)

#define PyBTree_IterNew_RETURN PyObject*
#define PyBTree_IterNew_PROTO (PyObject *tree, int kind)

#define PyBTree_IterNext_RETURN PyObject*
#define PyBTree_IterNext_PROTO (PyObject *iter)

#define PyBTree_MergeUnion_RETURN PyObject*
#define PyBTree_MergeUnion_PROTO (PyObject *tree_a, PyObject *tree_b)

#define PyBTree_MergeIntersection_RETURN PyObject*
#define PyBTree_MergeIntersection_PROTO (PyObject *tree_a, PyObject *tree_b)

#define PyBTree_MergeDifference_RETURN PyObject*
#define PyBTree_MergeDifference_PROTO (PyObject *tree_a, PyObject *tree_b)

#define PyBTree_Copy_RETURN PyObject*
#define PyBTree_Copy_PROTO (PyObject *tree)

#define PyBTree_Increment_RETURN PyObject*
#define PyBTree_Increment_PROTO (PyObject *tree, PyObject *key, PyObject *delta, PyObject *default_value)

#define PyBTree_BuildFromSortedPairs_RETURN PyObject*
#define PyBTree_BuildFromSortedPairs_PROTO (PyObject **keys, PyObject **values, Py_ssize_t n)

#define PyBTree_PopItemByIndex_RETURN PyObject*
#define PyBTree_PopItemByIndex_PROTO (PyObject *tree, Py_ssize_t index)

#ifdef BTREE_MODULE
/* This section is used when compiling the btree backend itself [2] */
static PyBTree_Insert_RETURN PyBTree_Insert PyBTree_Insert_PROTO;
static PyBTree_Delete_RETURN PyBTree_Delete PyBTree_Delete_PROTO;
static PyBTree_Search_RETURN PyBTree_Search PyBTree_Search_PROTO;
static PyBTree_BisectLeft_RETURN PyBTree_BisectLeft PyBTree_BisectLeft_PROTO;
static PyBTree_BisectRight_RETURN PyBTree_BisectRight PyBTree_BisectRight_PROTO;
static PyBTree_IRange_RETURN PyBTree_IRange PyBTree_IRange_PROTO;
static PyBTree_GetItemByIndex_RETURN PyBTree_GetItemByIndex PyBTree_GetItemByIndex_PROTO;
static PyBTree_IterNew_RETURN PyBTree_IterNew PyBTree_IterNew_PROTO;
static PyBTree_IterNext_RETURN PyBTree_IterNext PyBTree_IterNext_PROTO;
static PyBTree_MergeUnion_RETURN PyBTree_MergeUnion PyBTree_MergeUnion_PROTO;
static PyBTree_MergeIntersection_RETURN PyBTree_MergeIntersection PyBTree_MergeIntersection_PROTO;
static PyBTree_MergeDifference_RETURN PyBTree_MergeDifference PyBTree_MergeDifference_PROTO;
static PyBTree_Copy_RETURN PyBTree_Copy PyBTree_Copy_PROTO;
static PyBTree_Increment_RETURN PyBTree_Increment PyBTree_Increment_PROTO;
static PyBTree_BuildFromSortedPairs_RETURN PyBTree_BuildFromSortedPairs PyBTree_BuildFromSortedPairs_PROTO;
static PyBTree_PopItemByIndex_RETURN PyBTree_PopItemByIndex PyBTree_PopItemByIndex_PROTO;

#else
/* This section is used by the SortedDict/SortedSet modules to call the B-tree [2] */
static void **PyBTree_API;

#define PyBTree_Insert \
 (*(PyBTree_Insert_RETURN (*)PyBTree_Insert_PROTO) PyBTree_API[PyBTree_Insert_NUM])

#define PyBTree_Delete \
 (*(PyBTree_Delete_RETURN (*)PyBTree_Delete_PROTO) PyBTree_API[PyBTree_Delete_NUM])

#define PyBTree_Search \
 (*(PyBTree_Search_RETURN (*)PyBTree_Search_PROTO) PyBTree_API[PyBTree_Search_NUM])

#define PyBTree_BisectLeft \
 (*(PyBTree_BisectLeft_RETURN (*)PyBTree_BisectLeft_PROTO) PyBTree_API[PyBTree_BisectLeft_NUM])

#define PyBTree_BisectRight \
 (*(PyBTree_BisectRight_RETURN (*)PyBTree_BisectRight_PROTO) PyBTree_API[PyBTree_BisectRight_NUM])

#define PyBTree_IRange \
 (*(PyBTree_IRange_RETURN (*)PyBTree_IRange_PROTO) PyBTree_API[PyBTree_IRange_NUM])

#define PyBTree_GetItemByIndex \
 (*(PyBTree_GetItemByIndex_RETURN (*)PyBTree_GetItemByIndex_PROTO) PyBTree_API[PyBTree_GetItemByIndex_NUM])

#define PyBTree_IterNew \
 (*(PyBTree_IterNew_RETURN (*)PyBTree_IterNew_PROTO) PyBTree_API[PyBTree_IterNew_NUM])

#define PyBTree_IterNext \
 (*(PyBTree_IterNext_RETURN (*)PyBTree_IterNext_PROTO) PyBTree_API[PyBTree_IterNext_NUM])

#define PyBTree_MergeUnion \
 (*(PyBTree_MergeUnion_RETURN (*)PyBTree_MergeUnion_PROTO) PyBTree_API[PyBTree_MergeUnion_NUM])

#define PyBTree_MergeIntersection \
 (*(PyBTree_MergeIntersection_RETURN (*)PyBTree_MergeIntersection_PROTO) PyBTree_API[PyBTree_MergeIntersection_NUM])

#define PyBTree_MergeDifference \
 (*(PyBTree_MergeDifference_RETURN (*)PyBTree_MergeDifference_PROTO) PyBTree_API[PyBTree_MergeDifference_NUM])

#define PyBTree_Copy \
 (*(PyBTree_Copy_RETURN (*)PyBTree_Copy_PROTO) PyBTree_API[PyBTree_Copy_NUM])

#define PyBTree_Increment \
 (*(PyBTree_Increment_RETURN (*)PyBTree_Increment_PROTO) PyBTree_API[PyBTree_Increment_NUM])

#define PyBTree_BuildFromSortedPairs \
 (*(PyBTree_BuildFromSortedPairs_RETURN (*)PyBTree_BuildFromSortedPairs_PROTO) PyBTree_API[PyBTree_BuildFromSortedPairs_NUM])

#define PyBTree_PopItemByIndex \
 (*(PyBTree_PopItemByIndex_RETURN (*)PyBTree_PopItemByIndex_PROTO) PyBTree_API[PyBTree_PopItemByIndex_NUM])

/* Idiomatic macro to import the C API via a Capsule [2, 3] */
static int import_btree(void) {
    PyBTree_API = (void **)PyCapsule_Import("btree._C_API", 0);
    return (PyBTree_API != NULL) ? 0 : -1;
}
#endif

#ifdef __cplusplus
}
#endif
#endif /* !Py_BTREEMODULE_H */
