#ifndef Py_SORTEDCOLLECTIONS_H
#define Py_SORTEDCOLLECTIONS_H
/*
 * sorted_collections.h - Public header for sortedcollections module
 *
 * This header provides forward declarations for the SortedDict and SortedSet
 * types. The actual implementation is internal to sorted_collections.c.
 *
 * Usage:
 *   #include "sorted_collections.h"
 *   // Import the module via PyImport_ImportModule("sortedcollections")
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Module initialization function - the only non-static symbol */
PyMODINIT_FUNC PyInit_sortedcollections(void);

#ifdef __cplusplus
}
#endif
#endif /* !Py_SORTEDCOLLECTIONS_H */
