
#ifndef LEGATE_EXPORT_H
#define LEGATE_EXPORT_H

#ifdef LEGATE_STATIC_DEFINE
#  define LEGATE_EXPORT
#  define LEGATE_NO_EXPORT
#else
#  ifndef LEGATE_EXPORT
#    ifdef legate_EXPORTS
        /* We are building this library */
#      define LEGATE_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define LEGATE_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef LEGATE_NO_EXPORT
#    define LEGATE_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef LEGATE_DEPRECATED
#  define LEGATE_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef LEGATE_DEPRECATED_EXPORT
#  define LEGATE_DEPRECATED_EXPORT LEGATE_EXPORT LEGATE_DEPRECATED
#endif

#ifndef LEGATE_DEPRECATED_NO_EXPORT
#  define LEGATE_DEPRECATED_NO_EXPORT LEGATE_NO_EXPORT LEGATE_DEPRECATED
#endif

/* NOLINTNEXTLINE(readability-avoid-unconditional-preprocessor-if) */
#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef LEGATE_NO_DEPRECATED
#    define LEGATE_NO_DEPRECATED
#  endif
#endif
// For symbols that are only exported because they are used by the python bindings, not
// because they otherwise need to be. If references to them are removed in the Python
// bindings, these symbols should also be fixed up to be un-exported again.
#define LEGATE_PYTHON_EXPORT LEGATE_EXPORT

#endif /* LEGATE_EXPORT_H */
